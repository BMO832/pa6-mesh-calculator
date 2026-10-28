"""Geometry, not an optical or thermal performance model. SI units internally."""
from dataclasses import dataclass, asdict
import math
from .mesh_geometry import MeshInput, SQUARE, ROTATED, calculate, square_counts, segments


@dataclass(frozen=True)
class Design:
    length_m: float = 5.0
    width_m: float = 5.0
    diameter_mm: float = 2.0
    spacing_mm: float = 20.0
    structure: str = SQUARE
    deployment_pct: float = 100.0
    inaccessible_pct: float = 0.0
    cultivation_pct: float = 100.0
    light_usable_pct: float = 100.0
    biofilm_mm: float = 0.0

    def validate(self):
        MeshInput(self.length_m, self.width_m, self.diameter_mm, self.spacing_mm)
        if self.structure not in (SQUARE, ROTATED):
            raise ValueError("지원하지 않는 직조 구조입니다.")
        for name in ('deployment_pct', 'inaccessible_pct', 'cultivation_pct', 'light_usable_pct'):
            v = getattr(self, name)
            if not math.isfinite(v) or not 0 <= v <= 100:
                raise ValueError("비율은 0~100% 범위여야 합니다.")
        if not math.isfinite(self.biofilm_mm) or self.biofilm_mm < 0:
            raise ValueError("생물막 두께는 0 이상이어야 합니다.")


def band_coverage(span_m, pitch_m, diameter_m, count):
    """Union of strips centred at k*pitch, k=0..count-1, clipped to span."""
    r = diameter_m / 2
    n = count - 1
    if n == 0:
        return min(span_m, r)
    if diameter_m >= pitch_m:
        return min(span_m, n * pitch_m + r)
    remainder = max(0.0, span_m - n * pitch_m)
    return min(span_m, r + (n - 1) * diameter_m + min(diameter_m, r + remainder))


def shade_fraction(mesh, structure, diameter_m):
    if structure == SQUARE:
        ny, nx = square_counts(mesh)
        x = band_coverage(mesh.length_m, mesh.spacing_m, diameter_m, nx)
        y = band_coverage(mesh.width_m, mesh.spacing_m, diameter_m, ny)
        return 1 - (1 - x / mesh.length_m) * (1 - y / mesh.width_m)
    # Rotating an infinite square lattice preserves its area fraction.
    # For a finite rectangle this is explicitly a periodic-cell approximation.
    return 1 - max(0.0, 1 - diameter_m / mesh.spacing_m) ** 2


def evaluate(d):
    d.validate()
    full = MeshInput(d.length_m, d.width_m, d.diameter_mm, d.spacing_mm)
    full_result = calculate(full, d.structure)
    fraction = d.deployment_pct / 100
    active_length = d.length_m * fraction
    active = MeshInput(active_length, d.width_m, d.diameter_mm, d.spacing_mm) if fraction else None
    result = calculate(active, d.structure) if active else None
    footprint = active_length * d.width_m
    surface = result.total_surface_m2 if result else 0.0
    available = surface * (1 - d.inaccessible_pct / 100)
    cultivated = available * d.cultivation_pct / 100
    light_usable = cultivated * d.light_usable_pct / 100
    bare_ratio = shade_fraction(active, d.structure, d.diameter_mm / 1000) if active else 0.0
    effective_d = (d.diameter_mm + 2 * d.biofilm_mm) / 1000
    grown_ratio = shade_fraction(active, d.structure, effective_d) if active else 0.0
    area = full_result.planar_area_m2
    shaded = footprint * grown_ratio
    return {
        '가두리 수면면적 (m²)': area,
        '전개한 그물 평면면적 (m²)': footprint,
        '전체 제작 실 길이 (m)': full_result.filament_length_m,
        '전개 구간 실 길이 (m)': result.filament_length_m if result else 0.0,
        '전체 제작 실 표면적 (m²)': full_result.total_surface_m2,
        '전개 구간 실 표면적 (m²)': surface,
        '부착 가능 표면적 (m²)': available,
        '배양 면적으로 선택한 표면적 (m²)': cultivated,
        '광 이용 가능 표면적 가정 (m²)': light_usable,
        '빈 그물 가림률 (%)': bare_ratio * 100,
        '생물막 포함 가림률 (%)': grown_ratio * 100,
        '기하학적 개구율 (%)': (1 - grown_ratio) * 100,
        '수면 투영 차광면적 (m²)': shaded,
        '수면 전체 기준 가림률 (%)': shaded / area * 100,
        '빛이 통과하거나 미전개한 수면면적 (m²)': area - shaded,
        '생물막 포함 실 직경 (mm)': effective_d * 1000,
        '생물막 포함 빈 간격 (mm)': max(0.0, d.spacing_mm - effective_d * 1000),
    }


def preview_svg(d):
    """A 10-pitch detail, not a decimated full-net picture."""
    pitch = d.spacing_mm / 1000
    span = pitch * 10
    detail = MeshInput(span, span, d.diameter_mm, d.spacing_mm)
    stroke = (d.diameter_mm + 2 * d.biofilm_mm) / 1000
    lines = []
    for p, q in segments(detail, d.structure):
        lines.append(f'<line x1="{p[0]}" y1="{p[1]}" x2="{q[0]}" y2="{q[1]}"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {span} {span}" '
            f'width="100%" height="320"><defs><clipPath id="net"><rect width="{span}" height="{span}"/>'
            f'</clipPath></defs><rect width="{span}" height="{span}" fill="#e9f6f7"/>'
            f'<g clip-path="url(#net)" stroke="#197d85" stroke-width="{stroke}" stroke-linecap="butt">'
            + ''.join(lines) + '</g></svg>')
