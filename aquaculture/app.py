"""Run: python -m streamlit run aquaculture/app.py"""
from pathlib import Path
import sys
import json
import csv
import io
import math
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import streamlit as st
from aquaculture.model import Design, evaluate, preview_svg, SQUARE, ROTATED

st.set_page_config(page_title="양식장 그물 설계", page_icon="🌊", layout="wide")
st.markdown('''<style>
.block-container{max-width:1260px;padding-top:2.4rem;padding-bottom:3rem}
[data-testid="stMetric"]{background:white;border:1px solid #dce9eb;border-radius:14px;padding:16px}
[data-testid="stMetricValue"]{font-size:1.8rem}
</style>''', unsafe_allow_html=True)
st.caption("AQUACULTURE · MESH DESIGN / v1.0")
st.title("양식장 그물 설계 계산기")
st.write("실의 굵기와 간격을 바꾸며 **조류가 붙을 표면적**과 **수면을 가리는 면적**을 함께 비교하세요.")
st.info("수직 입사광·평평한 단층 그물의 기하학 계산입니다. 실제 광학 차광률·수온 감소·산소 생산량을 예측하지 않습니다.")

with st.sidebar:
    st.header("그물 조건")
    structure = st.selectbox("직조 구조", (SQUARE, ROTATED))
    length = st.number_input("가두리 길이 (m)", 0.1, 100.0, 5.0, 0.5)
    width = st.number_input("가두리 너비 (m)", 0.1, 100.0, 5.0, 0.5)
    diameter = st.number_input("실 직경 (mm)", 0.01, 100.0, 2.0, 0.1, format="%.3f")
    spacing = st.number_input("실 중심 간격 (mm)", 0.02, 1000.0, 20.0, 0.5,
        help="실 사이의 빈 간격이 아닙니다. 회전 격자도 평행한 실 사이 수직 거리입니다.", format="%.3f")
    deployment = st.slider("수면 전개율 (%)", 0, 100, 100, 5,
        help="길이 방향으로 펼친 비율. 미전개 부분은 가두리 밖에 보관하며 수면을 가리지 않는 것으로 가정합니다.")
    st.subheader("부착·배양 보정")
    inaccessible = st.slider("접촉·고정부 등 부착 불가율 (%)", 0, 100, 0, 5,
        help="실 원주 표면적 중 부착에 쓸 수 없는 비율을 직접 가정합니다. 측정값이 없으면 미보정 0%로 비교하세요.")
    cultivation = st.slider("부착 가능 면적 중 배양 사용률 (%)", 0, 100, 100, 5)
    light = st.slider("배양 면적 중 광 이용 가능 비율 (%)", 0, 100, 100, 5,
        help="뒷면·겹침·그늘을 고려하는 사용자 가정입니다. 자동으로 계산된 광합성 유효율이 아닙니다.")
    biofilm = st.number_input("실 한쪽의 생물막 두께 (mm)", 0.0, 50.0, 0.0, 0.01,
        help="직경에 두께의 두 배를 더해 투영 가림만 계산합니다. 조류 무게나 성장량으로 환산하지 않습니다.", format="%.3f")

d = Design(length, width, diameter, spacing, structure, deployment, inaccessible, cultivation, light, biofilm)
try:
    r = evaluate(d)
except ValueError as e:
    st.error(str(e))
    st.stop()

cols = st.columns(3)
cols[0].metric("부착 가능 표면적", f"{r['부착 가능 표면적 (m²)']:,.3f} m²")
cols[1].metric("수면 투영 차광면적", f"{r['수면 투영 차광면적 (m²)']:,.3f} m²")
cols[2].metric("수면 전체 기준 가림률", f"{r['수면 전체 기준 가림률 (%)']:,.1f} %")
st.caption("부착 면적은 실의 원주를 따라 잰 면적, 차광면적은 위에서 내려다봤을 때 가리는 수면 면적입니다. 서로 더하지 않습니다.")
if deployment == 0:
    st.warning("전부 회수한 상태입니다. 설치 중인 부착 면적과 수면 차광면적은 0입니다. 제작할 그물 전체의 실 길이는 아래에서 확인할 수 있습니다.")
if structure == ROTATED:
    st.warning("회전형 표면적은 경계에서 자른 실 길이로 계산합니다. 가림률은 반복 격자 근사로, 작은 그물·큰 간격에서 경계 오차가 커집니다. 회전만으로 반복 격자의 평균 가림률이 증가하지는 않습니다.")
if diameter + 2 * biofilm >= spacing:
    st.warning("생물막 포함 실 굵기가 중심 간격 이상입니다. 막힘 가능성을 검토하세요. 이 앱은 유속·유체 저항을 계산하지 않습니다.")

t1, t2, t3 = st.tabs(["면적과 직조", "목표 가림률과 비교", "계산 근거·저장"])
with t1:
    left, right = st.columns([1, 1.25])
    with left:
        st.subheader("직조 확대 보기")
        st.markdown(preview_svg(d), unsafe_allow_html=True)
        st.caption("중심 간격 10칸을 확대한 구조도입니다. 실제 직경 비율을 반영하며, 가두리 전체 그림은 아닙니다.")
    with right:
        st.subheader("실 표면에서 배양 면적까지")
        st.table([
            {"단계": "① 전개 구간 실 원주 표면적", "면적 (m²)": round(r['전개 구간 실 표면적 (m²)'], 4)},
            {"단계": "② 접촉·고정부 손실 제외 → 부착 가능", "면적 (m²)": round(r['부착 가능 표면적 (m²)'], 4)},
            {"단계": "③ 배양 사용률 적용", "면적 (m²)": round(r['배양 면적으로 선택한 표면적 (m²)'], 4)},
            {"단계": "④ 광 이용 비율 적용 (사용자 가정)", "면적 (m²)": round(r['광 이용 가능 표면적 가정 (m²)'], 4)},
        ])
        st.caption("실 원주 전체를 합산하므로 앞·뒷면을 다시 두 배 하지 않습니다. 생물막 외측 표면 증가·실 굴곡·매듭은 반영하지 않습니다.")
    st.subheader("차광과 개구")
    c = st.columns(3)
    c[0].metric("빈 그물 가림률 · 전개 구간", f"{r['빈 그물 가림률 (%)']:.1f}%")
    c[1].metric("생물막 포함 가림률 · 전개 구간", f"{r['생물막 포함 가림률 (%)']:.1f}%")
    c[2].metric("생물막 포함 개구율", f"{r['기하학적 개구율 (%)']:.1f}%")
    st.write(f"그물을 펼친 수면은 **{r['전개한 그물 평면면적 (m²)']:.3f}m²**, "
             f"제작할 전체 실 길이는 **{r['전체 제작 실 길이 (m)']:,.2f}m**입니다.")
    st.caption("수면 전개율은 가리는 범위, 가림률은 그 범위 안에서 실이 차지하는 비율입니다. 실측 PAR 감소율이나 복사열 차단율과 같지 않습니다.")

with t2:
    st.subheader("목표 가림률에서 간격 역산")
    target = st.slider("목표 수면 전체 가림률 (%)", 1, 99, 50)
    st.caption("불투명 실·수직 입사광·반복 격자 가정의 역산입니다. 온도 저감 목표가 아닙니다.")
    if deployment == 0 or target > deployment:
        st.warning("목표 가림률이 수면 전개율보다 큽니다. 전개율을 먼저 높여 주세요.")
    else:
        local = target / deployment
        ratio = 1 - math.sqrt(max(0.0, 1 - local))
        needed = (diameter + 2 * biofilm) / ratio
        st.success(f"필요 중심 간격 ≈ {needed:.3f}mm · 현재 실 기준 빈 간격 ≈ {max(0, needed-diameter):.3f}mm")
        st.caption("현재 두께의 생물막을 포함한 역산입니다. 경계가 있는 직교형의 실제 계산 결과와는 소폭 다를 수 있습니다. 별도 차양층은 포함하지 않습니다.")
    st.subheader("같은 직경에서 중심 간격 비교")
    rows = []
    for factor in (0.5, 0.75, 1.0, 1.5, 2.0):
        s = spacing * factor
        if s <= diameter:
            continue
        try:
            z = evaluate(Design(length, width, diameter, s, structure, deployment, inaccessible, cultivation, light, biofilm))
            rows.append({"중심 간격 (mm)": round(s, 3), "부착 가능 (m²)": round(z['부착 가능 표면적 (m²)'], 3),
                         "수면 차광면적 (m²)": round(z['수면 투영 차광면적 (m²)'], 3),
                         "전체 가림률 (%)": round(z['수면 전체 기준 가림률 (%)'], 2)})
        except ValueError:
            pass
    st.dataframe(rows, hide_index=True, width="stretch")
    st.caption("간격을 좁히면 실 표면적과 가림률이 함께 늘지만, 배양량·산소 생산량·구조 강도가 비례해 증가한다는 의미는 아닙니다.")

with t3:
    st.subheader("계산식과 적용 범위")
    st.markdown("""
- **실 표면적** = π × 실 직경 × 그물 안의 실 중심선 총길이. 실 단면은 원형이고 직선으로 간주합니다.
- **부착 가능 표면적** = 전개 구간 실 표면적 × (1 − 부착 불가율).
- **배양·광 이용 면적**은 여기에 각 사용 비율을 순서대로 곱한 사용자 가정입니다.
- **직교형 가림률**은 수면 경계로 자른 실 투영 띠의 합집합 면적입니다. 교차부는 중복 계산하지 않습니다.
- **45° 회전형 가림률** ≈ 1 − max(0, 1 − 유효 직경/중심 간격)². 유효 직경 = 실 직경 + 2 × 생물막 두께.
- **차광면적** = 전개 수면면적 × 전개 구간 가림률. 태양 각도·산란·실의 투명도·흡수·반사는 반영하지 않습니다.
- **전개 모델**은 길이 방향으로 펼치고 나머지는 가두리 밖에 보관합니다. 수면 위에 쌓인 접힘 부분의 그림자는 미포함입니다.
""")
    st.write("부착 불가율·배양 사용률·광 이용 비율의 초기값은 미보정 비교용입니다. 측정한 값이 아닙니다. 이 앱은 온도·산소·폐사 감소량을 자동으로 추정하지 않습니다.")
    st.subheader("전체 입력과 결과")
    st.json({"입력": d.__dict__, "출력": r})
    buf = io.StringIO(newline="")
    writer = csv.writer(buf)
    writer.writerow(["구분", "항목", "값"])
    for key, value in d.__dict__.items():
        writer.writerow(["입력", key, value])
    for key, value in r.items():
        writer.writerow(["결과", key, value])
    writer.writerow(["가정", "차광은 기하학적 투영값이며 실측 광학·열 성능이 아님", ""])
    st.download_button("입력·결과 CSV 저장", buf.getvalue().encode('utf-8-sig'), "mesh_design.csv", "text/csv")
    st.download_button("입력·결과 JSON 저장", json.dumps({"version":"1.0", "inputs":d.__dict__, "results":r,
        "scope":"수직 입사·단층 기하학. 회전형 차광은 반복 격자 근사. 광학·열·산소 모델 아님"}, ensure_ascii=False, indent=2),
        "mesh_design.json", "application/json")
    st.markdown("[기존 앱](https://pa6-mesh-calculator-bmo832.streamlit.app/) · [기존 저장소](https://github.com/BMO832/pa6-mesh-calculator)")
