"""Mass-based 30°C reference scenario; no burial or temperature correction."""
from dataclasses import dataclass
import math

DENSITY_KG_M3 = 1130.0


@dataclass(frozen=True)
class LeachingResult:
    mass_kg: float
    rate_percent: float
    total_mg: float
    per_area_mg_m2: float


def release_rate(days: float) -> float:
    if not math.isfinite(days) or not 1 <= days <= 64:
        raise ValueError("용출 기간은 1~64일이어야 합니다.")
    return 0.653 * (1 - 0.771 * math.exp(-0.407 * days))


def calculate_leaching(diameter_mm: float, length_m: float,
                       total_area_m2: float, days: float) -> LeachingResult:
    if any(not math.isfinite(x) or x <= 0 for x in
           (diameter_mm, length_m, total_area_m2)):
        raise ValueError("직경, 전체 길이, 전체 표면적은 유한한 양수여야 합니다.")
    diameter_m = diameter_mm / 1000
    mass = DENSITY_KG_M3 * (math.pi * diameter_m ** 2 / 4) * length_m
    rate = release_rate(days)
    total = mass * (rate / 100) * 1_000_000
    per_area = total / total_area_m2
    if any(not math.isfinite(x) or x <= 0 for x in (mass, total, per_area)):
        raise ValueError("용출 계산이 표현 가능한 수치 범위를 벗어났습니다.")
    return LeachingResult(mass, rate, total, per_area)
