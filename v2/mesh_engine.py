"""PA6 monofilament geometry; all internal geometry is in metres."""
from dataclasses import dataclass
from decimal import Decimal
import math

SQUARE = "직교 격자형 (Square Grid)"
ROTATED = "회전 격자형 (Rotated Square Grid)"
STRUCTURES = (SQUARE, ROTATED)
MAX_ROTATED_LINES = 200_000
Point = tuple[float, float]
Segment = tuple[Point, Point]


@dataclass(frozen=True)
class MeshInput:
    length_m: float
    width_m: float
    diameter_mm: float
    spacing_mm: float

    def __post_init__(self):
        values = (self.length_m, self.width_m, self.diameter_mm, self.spacing_mm)
        if any(not math.isfinite(v) or v <= 0 for v in values):
            raise ValueError("모든 입력은 유한한 양수여야 합니다.")
        if self.spacing_mm <= self.diameter_mm:
            raise ValueError("중심 간격 s는 직경 d보다 커야 합니다 (s > d).")
        if self.diameter_m == 0 or self.spacing_m == 0:
            raise ValueError("단위 변환 후 표현할 수 없는 작은 입력입니다.")

    @property
    def diameter_m(self):
        return self.diameter_mm / 1000.0

    @property
    def spacing_m(self):
        return self.spacing_mm / 1000.0


@dataclass(frozen=True)
class Result:
    planar_area_m2: float
    filament_length_m: float
    total_surface_m2: float
    exposed_surface_m2: float


def square_counts(data: MeshInput) -> tuple[int, int]:
    # Decimal avoids dropping a boundary filament for inputs such as .3 / .1.
    sn, sd = Decimal(str(data.spacing_mm)).as_integer_ratio()
    def count(value):
        n, d = Decimal(str(value)).as_integer_ratio()
        return (n * sd * 1000) // (d * sn) + 1
    return count(data.width_m), count(data.length_m)


def clip_line(normal: Point, offset: float, length: float, width: float) -> Segment | None:
    """Clip n·(x,y)=offset, with unit normal n, to [0,L] × [0,W].

    Closed boundaries are included; point-only corner touches are omitted.
    """
    nx, ny = normal
    px, py = nx * offset, ny * offset
    tx, ty = -ny, nx
    lo, hi = -math.inf, math.inf
    for p, t, bound in ((px, tx, length), (py, ty, width)):
        if t == 0:
            if not 0 <= p <= bound:
                return None
        else:
            a, b = -p / t, (bound - p) / t
            lo, hi = max(lo, min(a, b)), min(hi, max(a, b))
    if hi <= lo:
        return None
    # Clamp only floating point boundary overshoots.
    def point(t):
        return (min(length, max(0.0, px + t * tx)),
                min(width, max(0.0, py + t * ty)))
    return point(lo), point(hi)


def rotated_families(data: MeshInput):
    a = math.sqrt(0.5)
    families = []
    for normal in ((-a, a), (a, a)):
        nx, ny = normal
        projections = (0.0, nx * data.length_m, ny * data.width_m,
                       nx * data.length_m + ny * data.width_m)
        low, high = min(projections) / data.spacing_m, max(projections) / data.spacing_m
        if not math.isfinite(low) or not math.isfinite(high):
            raise ValueError("입력 범위가 너무 큽니다.")
        # One candidate beyond each edge ensures rounded corner cases are clipped.
        families.append((normal, range(math.floor(low), math.ceil(high) + 1)))
    if sum(len(indices) for _, indices in families) > MAX_ROTATED_LINES:
        raise ValueError("회전 격자 계산 한도(후보 직선 200,000개)를 초과했습니다. 간격을 늘리거나 크기를 줄여 주세요.")
    return families


def segments(data: MeshInput, structure: str, preview_limit: int | None = None):
    """Yield all calculation segments, or evenly sampled preview segments."""
    if structure == SQUARE:
        nx, ny = square_counts(data)
        step = max(1, math.ceil((nx + ny) / preview_limit)) if preview_limit else 1
        for i in range(0, nx, step):
            y = min(data.width_m, i * data.spacing_m)
            yield (0.0, y), (data.length_m, y)
        for i in range(0, ny, step):
            x = min(data.length_m, i * data.spacing_m)
            yield (x, 0.0), (x, data.width_m)
    elif structure == ROTATED:
        families = rotated_families(data)
        count = sum(len(indices) for _, indices in families)
        step = max(1, math.ceil(count / preview_limit)) if preview_limit else 1
        for normal, indices in families:
            for k in indices[::step]:
                segment = clip_line(normal, k * data.spacing_m, data.length_m, data.width_m)
                if segment is not None:
                    yield segment
    else:
        raise ValueError("지원하지 않는 직조 구조입니다.")


def calculate(data: MeshInput, structure: str) -> Result:
    if structure == SQUARE:
        nx, ny = square_counts(data)
        total_length = nx * data.length_m + ny * data.width_m
    elif structure == ROTATED:
        total_length = math.fsum(math.dist(p, q) for p, q in segments(data, structure))
    else:
        raise ValueError("지원하지 않는 직조 구조입니다.")
    total_surface = math.pi * data.diameter_m * total_length
    values = (data.length_m * data.width_m, total_length, total_surface, total_surface * 0.5)
    if not all(math.isfinite(v) and v > 0 for v in values):
        raise ValueError("계산 결과가 표현 가능한 수치 범위를 벗어났습니다.")
    return Result(*values)
