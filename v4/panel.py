import streamlit as st
from v4.sources import BRIDSON, FORTMANN, KUBO, HALF_NOTE, HYPOTHETICAL


def show_panel(m):
    d,g = m['data'],m['geometry']
    st.header('실시간 계산 원리 및 문헌')
    st.caption('왼쪽과 동일한 계산 결과 객체를 참조합니다. 입력 변경 시 함께 갱신됩니다.')
    with st.expander('① 표면적 계산',expanded=True):
        st.write(m['structure'])
        if m['counts']:
            nx,ny=m['counts']
            st.latex(r'N_x=\lfloor W/s\rfloor+1,\quad N_y=\lfloor L/s\rfloor+1')
            st.latex(rf'N_x=\lfloor {d.width_m:g}/{d.spacing_m:g}\rfloor+1={nx}')
            st.latex(rf'N_y=\lfloor {d.length_m:g}/{d.spacing_m:g}\rfloor+1={ny}')
            st.latex(rf'T=N_xL+N_yW={nx}\times {d.length_m:g}+{ny}\times {d.width_m:g}={g.filament_length_m:.6f}\ \mathrm{{m}}')
        else:
            st.latex(r'(-x+y)/\sqrt{2}=ns,\quad(x+y)/\sqrt{2}=ns,\quad n\in\mathbb{Z}')
            st.latex(rf'T=\sum\ell_{{\mathrm{{clip}}}}={g.filament_length_m:.6f}\ \mathrm{{m}}')
            st.write(f'원점 (0,0) 고정. 경계 [0,{d.length_m:g}] × [0,{d.width_m:g}] m에서 직선 클리핑, 수직 간격 {d.spacing_m:g} m.')
        st.latex(rf'A_{{\mathrm{{total}}}}=\pi dT=\pi\times {d.diameter_m:g}\times {g.filament_length_m:.6f}={g.total_surface_m2:.6f}\ \mathrm{{m^2}}')
        st.latex(rf'A_{{\mathrm{{exposed}}}}=0.5A_{{\mathrm{{total}}}}={g.exposed_surface_m2:.6f}\ \mathrm{{m^2}}')
        st.latex(rf'A=LW={d.length_m:g}\times {d.width_m:g}={g.planar_area_m2:.6f}\ \mathrm{{m^2}}')
        st.caption('L·W: 매트 치수(m), d: 직경(m), s: 중심 간격(m), T: 전체 길이(m). 출처: 일반 기하학 및 V1 직선 중심선 모델. 끝단·교차부 접촉·굴곡 미보정. 50% 매몰은 프로그램의 이상화 가정.')
    with st.expander('② PA6 질량 계산',expanded=True):
        st.latex(r'm_{\mathrm{PA6}}=\rho\frac{\pi d^2}{4}T')
        st.latex(rf'd={d.diameter_mm:g}/1000={d.diameter_m:g}\ \mathrm{{m}}')
        st.latex(rf'm_{{\mathrm{{PA6}}}}=1130\frac{{\pi({d.diameter_m:g})^2}}{{4}}\times {g.filament_length_m:.6f}={m["mass_kg"]:.6f}\ \mathrm{{kg}}')
        st.caption('출처: 원통 체적×밀도. ρ=1,130 kg/m³는 기존 버전의 초기 가정값이며 이 시료의 실측 밀도가 아닙니다. 매몰률은 적용하지 않습니다.')
    with st.expander('③ 물질별 용출률 계산',expanded=True):
        st.latex(r'r_i(t)=C_{e,i}[1-a_i e^{-k_i t}]')
        st.caption('Ce와 r: PA6 질량 대비 %, a: 무차원, k: 용출곡선 속도계수(day⁻¹), t: 접촉 기간(day). 30°C 고정.')
        for item in m['chemicals']:
            c=item['chemical']; current=item['current']
            st.write(c.name + (' · 반정량' if c.semiquantitative else ''))
            st.latex(rf'r({m["days"]})={c.ce}[1-{c.a}e^{{-{c.k}\times {m["days"]}}}]={current["rate_percent"]:.6f}\%')
        st.markdown('문헌 계수: '+BRIDSON)
    with st.expander('④ 누적 용출량 및 면적 환산',expanded=True):
        st.latex(r'M_i=m_{\mathrm{PA6}}(r_i/100)10^6,\quad q_i=M_i/A_{\mathrm{total}}')
        for item in m['chemicals']:
            c=item['chemical']; r=item['current']
            st.write(c.name)
            st.latex(rf'M={m["mass_kg"]:.6f}\times({r["rate_percent"]:.6f}/100)\times10^6={r["cumulative_mg"]:.6f}\ \mathrm{{mg}}')
            st.latex(rf'q={r["cumulative_mg"]:.6f}/{g.total_surface_m2:.6f}={item["q_pa6"]:.6f}\ \mathrm{{mg/m^2\!\! -PA6}}')
        st.caption('질량→mg 및 % 변환은 일반 단위 환산입니다. 표면적을 다시 곱하거나 50%를 곱하지 않습니다. 표시 숫자는 반올림하지만 엔진은 원래 정밀도로 계산합니다.')
        st.markdown('용출률 출처: '+BRIDSON)
    with st.expander('⑤ 반감기 및 일일 분해 계산',expanded=True):
        st.latex(r'\lambda_i=\ln(2)/H_i,\quad\Delta M_i(j)=M_i(j)-M_i(j-1)')
        st.latex(r'R_i(t)=\sum_{j=1}^{t}\Delta M_i(j)e^{-\lambda_i(t-j)}')
        st.caption('H: 환경 분해 반감기(day), λ: 환경 분해속도(day⁻¹), k: 용출곡선 계수로 서로 다른 값입니다. R: 잔존량(mg).')
        st.write('프로그램 가정: 경험식에는 양의 초기 절편이 있지만 일일 수지에서 M(0)=0. 첫날 투입량은 M(1)이며 매일 말 투입, 이후 1차 분해로 근사합니다.')
        for item in m['chemicals']:
            st.write(item['chemical'].name)
            if item['half_life'] is None:
                st.latex(rf'\lambda=0,\quad R({m["days"]})=M({m["days"]})={item["current"]["remaining_mg"]:.6f}\ \mathrm{{mg}}')
                st.caption('분해 미반영 시나리오')
            else:
                st.latex(rf'\lambda=\ln(2)/{item["half_life"]:g}={item["decay"]:.8f}\ \mathrm{{day^{{-1}}}}')
                st.latex(rf'R({m["days"]})={item["current"]["remaining_mg"]:.6f}\ \mathrm{{mg}}')
                if item['chemical'].semiquantitative: st.warning(HYPOTHETICAL)
                else: st.caption('수중 문헌 관련 참고 반감기 시나리오 — '+HALF_NOTE)
            st.dataframe([{'투입일 j':r['day'],'신규 용출량 [mg]':r['increment_mg'],
                           '감쇠 기간 [day]':r['age_days'],'잔존 기여량 [mg]':r['contribution_mg']}
                          for r in item['contributions']],hide_index=True)
        st.markdown('수중 분해 특성 근거: '+FORTMANN)
        st.caption('감쇠 합산은 일반 1차 분해 수학과 프로그램의 날짜 말 투입 가정입니다. 올리고머 사이의 전환 반응은 없습니다.')
        st.markdown('생분해 가능성 참고: '+KUBO)
        st.caption('선형 PA6 올리고머의 가속 해양 생분해 연구입니다. 고리형 올리고머의 환경 반감기로 사용하지 않습니다.')
    with st.expander('⑥ 모래 혼합층 평균농도',expanded=True):
        st.latex(r'h_{\mathrm m}=h_{\mathrm{cm}}/100,\quad m_{\mathrm{sand}}=\rho_b A h_{\mathrm m},\quad C_i=R_i/m_{\mathrm{sand}}')
        for item in m['chemicals']:
            st.write(item['chemical'].name)
            for key,label in [('surface','표층'),('selected','선택 혼합층'),('average','참고 평균 굴 깊이층'),('maximum','참고 최대 굴 깊이층')]:
                h=m['depth'] if key=='selected' else m[key]
                layer=item['layers'][key]
                st.caption(f'{label}: 0~{h:g} cm층 전체의 평균')
                st.latex(rf'm_{{\mathrm{{sand}}}}={m["density"]:g}\times {g.planar_area_m2:g}\times({h:g}/100)={layer.mass_kg:.6f}\ \mathrm{{kg}}')
                st.latex(rf'C={item["current"]["remaining_mg"]:.6f}/{layer.mass_kg:.6f}={layer.concentration_mg_kg:.6f}\ \mathrm{{mg/kg\ dry\ sand}}')
        st.caption('출처: V3 질량배분식과 일반 질량/질량 정의. 잔존량 전량의 균일 혼합은 프로그램 가정이며 검증된 현장 농도 모델이 아닙니다. ρb는 공극을 포함한 건조 용적밀도입니다.')
