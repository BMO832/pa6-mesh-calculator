import streamlit as st
from v3.sand import (calculate_sand, scenario_rows, chart_spec, csv_bytes,
                     RANGE, DEPTH, VOLUME, MASS, CONCENTRATION)


def show_sand(data, geometry, days, prediction, structure):
    st.subheader("모래 혼합층 평균 카프로락탐 농도")
    st.info("용출 질량 전량이 매트 아래 지정한 모래층에 균일하게 혼합된다는 가정입니다. "
            "표시값은 혼합층 평균농도이며 특정 깊이의 실제 농도나 생물 체내농도가 아닙니다.")
    density = st.number_input("건조 모래 용적밀도 ρb [kg/m³]", value=1500.0, step=10.0,
        help="모래 입자 자체의 밀도가 아니라 공극을 포함한 모래층의 건조 질량/전체 부피입니다. "
             "기본값 1500 kg/m³는 계산 예시용 가정값이며 방아머리 실측값이 아닙니다.")
    depth = st.number_input("선택 혼합 깊이 h [cm]", min_value=.1, max_value=130.0,
                            value=10.0, step=.1, format="%.2f")
    surface = st.number_input("표층 두께 hs [cm]", min_value=.1, max_value=5.0,
                              value=1.0, step=.1, format="%.2f")
    total, area = prediction.total_mg, geometry.planar_area_m2
    try:
        selected = calculate_sand(total, area, density, depth)
        rows, curve = scenario_rows(total, area, density, depth, surface)
    except ValueError as exc:
        st.error(str(exc))
        return
    for label, value, unit in (
        ("선택 기간 총용출량", total, "mg"),
        ("매트 평면면적", area, "m²"),
        ("평면면적당 용출량", selected.q_plan_mg_m2, "mg/m²"),
        ("혼합층 건조 모래 질량", selected.mass_kg, "kg"),
        ("혼합층 평균 카프로락탐 농도", selected.concentration_mg_kg, "mg/kg dry sand"),
    ):
        st.metric(label, f"{value:,.6f} {unit}")
    st.write(f"선택 혼합층 범위: **0~{depth:g} cm층**")
    st.caption("평면면적당 용출량 M/A와 V2의 소재 표면적당 용출량 M/A_total은 서로 다른 값입니다. "
               "매몰률 50%로 총용출량을 다시 줄이지 않습니다.")
    st.subheader("깊이 비교표 — 독립된 대안 시나리오")
    st.dataframe(rows, hide_index=True, column_config={
        DEPTH: st.column_config.NumberColumn(format="%.2f"),
        VOLUME: st.column_config.NumberColumn(format="%.6f"),
        MASS: st.column_config.NumberColumn(format="%.6f"),
        CONCENTRATION: st.column_config.NumberColumn(format="%.6f"),
    })
    st.caption("14.4·37.6 cm는 사용자가 제공한 달랑게 굴 깊이 참고값, 130 cm는 갯방풍 뿌리 깊이 참고값입니다. "
               "저장소에서 원문 출처를 확인하지 못했습니다. 실제 오염 도달 깊이나 생물 평균 생활 깊이를 뜻하지 않습니다. "
               "130 cm는 이번 탐색 범위의 상한입니다.")
    st.subheader("가정한 혼합층 두께에 따른 평균농도")
    logarithmic = st.checkbox("농도 y축 로그 표시", value=False)
    if logarithmic and any(row[CONCENTRATION] <= 0 for row in curve):
        st.caption("0 농도는 로그축에 표시할 수 없어 선형축으로 표시합니다.")
    st.vega_lite_chart(spec=chart_spec(curve, logarithmic), width="stretch")
    st.caption("같은 용출 질량을 더 두꺼운 모래층에 균일 배분할수록 평균농도가 낮아집니다. "
               "실제로 깊어질수록 농도가 이 곡선을 따라 감소한다는 뜻은 아닙니다.")
    conditions = {
        "선택 기간 [day]": days, "온도 [°C]": 30,
        "매트 길이 [m]": data.length_m, "매트 너비 [m]": data.width_m,
        "매트 평면면적 [m²]": area, "총용출량 [mg]": total,
        "평면면적당 용출량 [mg/m²]": selected.q_plan_mg_m2,
        "모래 용적밀도 [kg/m³]": density, "직조 구조": structure,
        "필라멘트 직경 [mm]": data.diameter_mm, "필라멘트 간격 [mm]": data.spacing_mm,
        "선택 혼합 깊이 [cm]": depth, "표층 두께 [cm]": surface,
    }
    st.download_button("깊이 비교표 CSV 다운로드", csv_bytes(rows, conditions),
                       file_name="pa6_v3_sand_scenarios.csv", mime="text/csv")
    with st.expander("모래 농도 수식·단위·가정·한계"):
        st.markdown("""
- M: 선택 기간 총용출량 [mg], A: 길이×너비의 매트 평면면적 [m²]
- ρb: 건조 모래 용적밀도 [kg/m³], h: 혼합층 두께 [cm]
- `h_m = h / 100`, `q_plan = M / A` [mg/m²]
- `V_sand = A × h_m` [m³], `m_sand = ρb × A × h_m` [kg dry sand]
- `C_sand = M / m_sand = q_plan / (ρb × h_m)` [mg/kg dry sand]

M은 이미 mg 단위이므로 g→mg 변환을 다시 하지 않습니다. 평가 면적은 매트 평면면적으로 고정하며
주변 수평 확산 면적을 추가하지 않습니다. 전량 잔류를 가정하며 매몰률 50%를 M에 적용하지 않습니다.
0 cm는 부피가 없으므로 계산하지 않습니다. 예를 들어 30 cm는 표면~30 cm층 전체의 평균이며
30 cm 지점의 실제 농도가 아닙니다. 각 혼합 깊이는 독립된 대안 시나리오이고 지중 농도분포가 아닙니다.

전량 잔류 가정은 손실을 무시하지만, 균일 혼합은 국소적으로 높은 농도를 희석할 수 있습니다.
따라서 이 결과는 **최대 노출농도 또는 안전성을 보장하는 상한이 아닙니다.**
강우·침투·지하수 흐름·확산·흡착·분해·생물흡수는 모델링하지 않습니다.
수중 용출 경험식의 결과를 모래에 배분하는 가정이며 실제 해변에서의 방출량을 검증한 결과가 아닙니다.
경험식의 기간은 실제 해변 설치기간과 자동으로 같지 않습니다.
수중 독성값 mg/L와 모래 농도 mg/kg를 직접 비교할 수 없습니다.
생물 체내농도·흡수량·독성영향·개체수 배분·위해지수·안전/위험 판정은 계산하지 않습니다.
""")
