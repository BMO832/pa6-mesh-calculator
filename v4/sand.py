"""Pure mass-allocation scenarios. Mass input is mg, never g."""
from dataclasses import dataclass
import csv
import io
import math

MODEL = "분해 후 잔존량 전량 잔류·균일 혼합 가정"
RANGE = "혼합층 범위"
DEPTH = "혼합층 두께 [cm]"
VOLUME = "모래 부피 [m³]"
MASS = "건조 모래 질량 [kg]"
CONCENTRATION = "평균농도 [mg/kg dry sand]"
REFERENCE_DEPTHS = (5, 10, 14.4, 20, 30, 37.6, 50, 100, 130)


@dataclass(frozen=True)
class SandResult:
    q_plan_mg_m2: float
    volume_m3: float
    mass_kg: float
    concentration_mg_kg: float


def calculate_sand(total_mg, area_m2, density_kg_m3, depth_cm):
    """Compute layer mean, not a point concentration or biological exposure."""
    if any(not math.isfinite(x) for x in (total_mg, area_m2, density_kg_m3, depth_cm)):
        raise ValueError("모든 입력은 유한한 수여야 합니다.")
    if total_mg < 0 or min(area_m2, density_kg_m3, depth_cm) <= 0:
        raise ValueError("용출량은 0 이상, 면적·용적밀도·깊이는 0보다 커야 합니다.")
    volume = area_m2 * (depth_cm / 100)
    mass = density_kg_m3 * volume
    if not math.isfinite(mass) or not math.isfinite(volume) or mass <= 0 or volume <= 0:
        raise ValueError("모래층 부피·질량이 계산 가능한 수치 범위를 벗어났습니다.")
    q = total_mg / area_m2
    concentration = total_mg / mass
    if not math.isfinite(q) or not math.isfinite(concentration):
        raise ValueError("농도가 계산 가능한 수치 범위를 벗어났습니다.")
    return SandResult(q, volume, mass, concentration)


def make_rows(total_mg, area_m2, density, depths, surface_cm, selected_cm):
    rows = []
    for h in sorted(set(depths)):
        result = calculate_sand(total_mg, area_m2, density, h)
        labels = []
        if h == surface_cm: labels.append("표층")
        if h == selected_cm: labels.append("선택")
        layer = f"0~{h:g} cm층" + (f" ({', '.join(labels)})" if labels else "")
        rows.append({RANGE: layer, DEPTH: h, VOLUME: result.volume_m3,
                     MASS: result.mass_kg, CONCENTRATION: result.concentration_mg_kg})
    return rows


def scenario_rows(total_mg, area_m2, density, selected_cm, surface_cm):
    if not .1 <= selected_cm <= 130 or not .1 <= surface_cm <= 5:
        raise ValueError("선택 혼합 깊이는 0.1~130 cm, 표층 두께는 0.1~5 cm입니다.")
    table = make_rows(total_mg, area_m2, density,
                      (*REFERENCE_DEPTHS, selected_cm, surface_cm), surface_cm, selected_cm)
    curve = make_rows(total_mg, area_m2, density,
                      (*range(1, 131), selected_cm, surface_cm), surface_cm, selected_cm)
    return table, curve


def chart_spec(rows, logarithmic=False):
    # Log cannot represent zero: use linear for all-zero scenarios.
    use_log = logarithmic and all(row[CONCENTRATION] > 0 for row in rows)
    return {
        "data": {"values": [{"depth_cm": r[DEPTH], "concentration": r[CONCENTRATION],
                              "layer": f"0~{r[DEPTH]:g} cm층 평균"} for r in rows]},
        "mark": {"type": "line", "point": True},
        "encoding": {
            "x": {"field": "depth_cm", "type": "quantitative", "title": "표면부터의 혼합층 두께 [cm]"},
            "y": {"field": "concentration", "type": "quantitative",
                  "title": "혼합층 평균농도 [mg/kg dry sand]",
                  "scale": {"type": "log" if use_log else "linear"}},
            "tooltip": [
                {"field": "layer", "type": "nominal", "title": "혼합층"},
                {"field": "depth_cm", "type": "quantitative", "title": DEPTH},
                {"field": "concentration", "type": "quantitative", "title": CONCENTRATION, "format": ".6g"},
            ],
        },
    }


def csv_bytes(rows, conditions):
    buffer = io.StringIO(newline="")
    records = [{**conditions, **row, "모델 설명": MODEL} for row in rows]
    writer = csv.DictWriter(buffer, fieldnames=list(records[0]))
    writer.writeheader()
    writer.writerows(records)
    return buffer.getvalue().encode("utf-8-sig")
