"""Five-compound release and end-of-day environmental decay scenarios."""
from dataclasses import dataclass
import math





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
    if not math.isfinite(days) or not 1 <= days <= 92 or int(days) != days:
        raise ValueError('접촉 기간은 1-92일의 정수여야 합니다.')
    return chemical.ce * (1 - chemical.a * math.exp(-chemical.k * days))


def history(chemical, mass_kg, half_life):
    if not math.isfinite(mass_kg) or mass_kg <= 0:
        raise ValueError('PA6 질량은 유한한 양수여야 합니다.')
    if half_life not in HALF_LIVES:
        raise ValueError('지원하는 반감기는 분해 미반영 또는 5·9.5·14일입니다.')
    decay = 0.0 if half_life is None else math.log(2) / half_life
    records, previous, remaining = [], 0.0, 0.0
    for day in range(1,93):
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


