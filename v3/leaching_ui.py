import streamlit as st
from v3.leaching import calculate_leaching, release_rate


def show_leaching(data, result):
    st.subheader("카프로락탐 용출량 예측 (30°C)")
    days = st.slider("용출 기간 (day)", 1, 64, 7, key="leaching_days")
    prediction = calculate_leaching(data.diameter_mm, result.filament_length_m,
                                   result.total_surface_m2, days)
    for label, value, unit in (
        ("PA6 전체 질량", prediction.mass_kg, "kg"),
        ("선택 기간의 누적 카프로락탐 용출률", prediction.rate_percent, "%"),
        ("총 카프로락탐 용출량", prediction.total_mg, "mg"),
        ("면적당 카프로락탐 용출량", prediction.per_area_mg_m2, "mg/m²"),
    ):
        st.metric(label, f"{value:,.4f} {unit}")
    st.caption("밀도 1,130 kg/m³ 가정 · 온도 30°C 고정 · 면적 환산 분모: 매몰 전 전체 기하학적 표면적")
    st.line_chart({"시간 (day)": list(range(1, 65)),
                   "누적 용출률 (%)": [release_rate(t) for t in range(1, 65)]},
                  x="시간 (day)", y="누적 용출률 (%)")
    with st.expander("수식·변수 및 문헌 보기"):
        st.markdown("""
`m_PA6 = ρ × (π × d² / 4) × T`  
`r(t) = 0.653 × (1 − 0.771 × exp(−0.407 × t))`  
`M(t) = m_PA6 × r(t)/100 × 1,000,000`  
`q(t) = M(t) / A_total`

ρ: 밀도 1,130 kg/m³, d: mm에서 m로 변환한 직경, T: 전체 필라멘트 길이(m),
t: 기간(day), r: 누적 용출률(%), M: 총용출량(mg), A_total: 매몰 전 표면적(m²).

q는 질량 기준 예측값의 면적 환산값이며 실제 면적당 용출 실험값이 아닙니다.
직조 구조·직경에 따른 실제 용출속도 차이는 반영하지 않습니다.
0일에는 양의 절편이 있으므로 1~64일만 제공합니다.

출처: [Bridson et al. (2023), Environmental Advances](https://doi.org/10.1016/j.envadv.2023.100359).
""")
    st.info("이 모델은 30°C 수중 실험에서 얻은 PA6 카프로락탐 용출 경험식을 활용합니다. "
            "원 연구의 시료는 PA6 플라스틱 조각이며 재활용 PA6 모노필라멘트의 직접적인 용출 실험 결과는 아닙니다. "
            "매몰률 50%는 표면적 계산에만 적용하며 용출량을 자동으로 50% 감소시키지 않습니다. "
            "재료 질량에 문헌 용출률을 적용한 참고 시나리오로 실제 해변 용출량을 검증한 결과가 아닙니다. "
            "온도 변화, UV 노출, 실제 침수 조건은 고려하지 않습니다.")

    return days, prediction
