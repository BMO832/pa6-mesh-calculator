"""Five-compound release and end-of-day environmental decay scenarios."""
from dataclasses import dataclass
import math
from v4.mesh_engine import calculate, square_counts, SQUARE
from v4.leaching import calculate_leaching
from v4.sand import calculate_sand, make_rows, REFERENCE_DEPTHS


@dataclass(frozen=True)
class Chemical:
    name: str
    ce: float
    a: float
    k: float
    semiquantitative: bool = True


CHEMICALS = {
    c.name: c for c in (
        Chemical('Caprolactam', .653, .771, .407, False),
        Chemical('PA6 cyclic dimer', .065, .873, .051),
        Chemical('PA6 cyclic trimer', .374, .879, .050),
        Chemical('PA6 cyclic tetramer', .526, .900, .042),
        Chemical('PA6 cyclic pentamer', .221, .939, .026),
    )
}
HALF_LIVES = (None, 5.0, 9.5, 14.0)


def rate(chemical, days):
    if not math.isfinite(days) or not 1 <= days <= 64 or int(days) != days:
        raise ValueError('접촉 기간은 1~64일의 정수여야 합니다.')
    return chemical.ce * (1 - chemical.a * math.exp(-chemical.k * days))


def history(chemical, mass_kg, half_life):
    if not math.isfinite(mass_kg) or mass_kg <= 0:
        raise ValueError('PA6 질량은 유한한 양수여야 합니다.')
    if half_life not in HALF_LIVES:
        raise ValueError('지원하는 반감기는 분해 미반영 또는 5·9.5·14일입니다.')
    decay = 0.0 if half_life is None else math.log(2) / half_life
    records, previous, remaining = [], 0.0, 0.0
    for day in range(1,65):
        r = rate(chemical, day)
        cumulative = mass_kg * (r / 100) * 1_000_000
        increment = cumulative - previous  # Effective M(0)=0, first day includes intercept.
        remaining = cumulative if half_life is None else remaining * math.exp(-decay) + increment
        if not all(math.isfinite(x) for x in (cumulative,increment,remaining)):
            raise ValueError('용출/잔존량이 계산 가능한 수치 범위를 벗어났습니다.')
        if increment < 0 or remaining < 0 or remaining > cumulative * (1+1e-12):
            raise ValueError('용출 및 잔존량의 질량 수지 오류입니다.')
        records.append(dict(day=day, rate_percent=r, cumulative_mg=cumulative,
                            increment_mg=increment, remaining_mg=remaining))
        previous = cumulative
    return decay, records


def build_model(data, structure, names, days, half_lives, density, depth, surface, average, maximum):
    if not names or any(n not in CHEMICALS for n in names):
        raise ValueError('물질을 하나 이상 선택해 주세요.')
    if not .1 <= surface <= 5 or any(not .1 <= h <= 130 for h in (depth,average,maximum)):
        raise ValueError('혼합 깊이 범위를 확인해 주세요.')
    if average > maximum:
        raise ValueError('참고 평균 굴 깊이는 참고 최대 굴 깊이보다 클 수 없습니다.')
    rate(CHEMICALS[names[0]],days)
    geometry = calculate(data,structure)
    mass = calculate_leaching(data.diameter_mm,geometry.filament_length_m,
                              geometry.total_surface_m2,days).mass_kg
    calculate_sand(0,geometry.planar_area_m2,density,depth)
    model = dict(data=data,structure=structure,geometry=geometry,mass_kg=mass,days=days,
                 density=density,depth=depth,surface=surface,average=average,maximum=maximum,
                 counts=square_counts(data) if structure == SQUARE else None,chemicals=[])
    depths = (*REFERENCE_DEPTHS,depth,surface,average,maximum)
    for name in names:
        chemical = CHEMICALS[name]
        half = half_lives[name]
        decay, records = history(chemical,mass,half)
        current = records[days-1]
        remaining = current['remaining_mg']
        table = make_rows(remaining,geometry.planar_area_m2,density,depths,surface,depth)
        curve = make_rows(remaining,geometry.planar_area_m2,density,
                          (*range(1,131),surface,depth,average,maximum),surface,depth)
        layers = {key: calculate_sand(remaining,geometry.planar_area_m2,density,h)
                  for key,h in (('selected',depth),('surface',surface),('average',average),('maximum',maximum))}
        # Each cohort contributes at t after end-of-day addition and subsequent decay.
        contributions = [dict(day=r['day'], increment_mg=r['increment_mg'],
                              age_days=days-r['day'],
                              contribution_mg=r['increment_mg']*math.exp(-decay*(days-r['day'])))
                         for r in records[:days]]
        model['chemicals'].append(dict(chemical=chemical,half_life=half,decay=decay,
            history=records,current=current,table=table,curve=curve,layers=layers,
            contributions=contributions,q_pa6=current['cumulative_mg']/geometry.total_surface_m2,
            q_plan_cumulative=current['cumulative_mg']/geometry.planar_area_m2))
    return model
