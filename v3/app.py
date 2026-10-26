"""Streamlit UI: run with python -m streamlit run app.py."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import streamlit as st
from v3.leaching_ui import show_leaching
from v3.sand_ui import show_sand
from v3.mesh_engine import MeshInput, STRUCTURES, calculate, segments


def preview_svg(data, structure):
    scale = 640 / max(data.length_m, data.width_m)
    w, h = data.length_m * scale, data.width_m * scale
    lines = []
    for (x1, y1), (x2, y2) in segments(data, structure, preview_limit=400):
        lines.append(f'<line x1="{x1*scale}" y1="{h-y1*scale}" x2="{x2*scale}" y2="{h-y2*scale}"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-8 -8 {w+16} {h+16}" '
            'width="100%" role="img" aria-label="선택한 격자 중심선 미리보기">'
            f'<rect width="{w}" height="{h}" fill="#f1f5f9" stroke="#475569"/>'
            '<g stroke="#0891b2" stroke-width="1" vector-effect="non-scaling-stroke">'
            + ''.join(lines) + '</g></svg>')


st.set_page_config(page_title="PA6 Mesh Surface Area Calculator V3", layout="centered")
st.title("PA6 Mesh Surface Area Calculator V3")
st.caption("V3 · PA6 단일 원형 모노필라멘트 · 매몰률 50% 고정")
with st.form("mesh_inputs"):
    structure = st.selectbox("직조 구조", STRUCTURES)
    length = st.number_input("이동로 길이 L (m)", value=10.0, format="%.4f")
    width = st.number_input("이동로 너비 W (m)", value=1.0, format="%.4f")
    diameter = st.number_input("필라멘트 직경 d (mm)", value=2.0, format="%.4f")
    spacing = st.number_input("필라멘트 중심 간격 s (mm)", value=20.0, format="%.4f",
                              help="회전 격자는 인접 평행 필라멘트 사이의 수직 거리입니다.")
    submitted = st.form_submit_button("계산")

if submitted:
    st.session_state.pop('mesh_result', None)
    try:
        checked = MeshInput(length, width, diameter, spacing)
        checked_result = calculate(checked, structure)
        st.session_state['mesh_result'] = (checked, structure, checked_result)
    except (ValueError, OverflowError) as exc:
        st.error(str(exc))

if 'mesh_result' in st.session_state:
    try:
        data, structure, result = st.session_state['mesh_result']
        # Geometry result is retained when the period slider reruns the app.
        st.subheader("계산 결과")
        for label, value, unit in (
            ("이동로 평면면적", result.planar_area_m2, "m²"),
            ("전체 필라멘트 길이", result.filament_length_m, "m"),
            ("매몰 전 기하학적 표면적", result.total_surface_m2, "m²"),
            ("50% 매몰 후 비매몰 표면적", result.exposed_surface_m2, "m²"),
        ):
            st.metric(label, f"{value:,.4f} {unit}")
        st.subheader("2D 미리보기")
        st.markdown(preview_svg(data, structure), unsafe_allow_html=True)
        st.caption("가로축 L · 세로축 W · 좌측 하단 (0,0). 조밀한 격자는 일부 중심선만 표시하며 계산에는 모든 선분을 포함합니다. 선 굵기는 실제 직경과 무관합니다.")
        days, prediction = show_leaching(data, result)
        show_sand(data, result, days, prediction, structure)
    except (ValueError, OverflowError) as exc:
        st.error(str(exc))

st.info("직선 중심선 기준의 1차 기하학 근사입니다. 끝단, 교차부 중복·접촉면과 실의 굴곡을 보정하지 않습니다. 50% 매몰은 전체 표면적의 절반을 가린다는 이상화된 가정입니다.")
