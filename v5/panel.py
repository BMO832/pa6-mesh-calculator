import streamlit as st
from v5.engine import STRAW, MEASURED, PNEC
from v5.sources import explain, PW_NOTE, BURROW_NOTE, HALF_NOTE, HYPOTHETICAL, PNEC_NOTE


def show_panel(m):
    p=m['physical']; d=p['design']; day=m['days']
    st.header('실시간 계산 원리·출처')
    st.caption('결과표·그래프와 같은 계산 객체를 참조합니다. A 문헌식 / B 기본 수학 / C 자체 유도 / D 팀 가정. 표시만 반올림합니다.')
    with st.expander('① 직조 구조·표면적·질량·롤',expanded=True):
        st.write(d.structure)
        st.latex(rf'L={d.length:g}\,m,\quad W={d.width:g}\,m,\quad A=LW={p["area"]:.6f}\,m^2')
        explain('geometry')
        if d.structure==STRAW:
            st.latex(rf'n_w=\lfloor W/s_m\rfloor+1=\lfloor {d.width:g}/{d.spacing/1000:g}\rfloor+1={p["nw"]}')
            st.latex(rf'n_{{all}}=\operatorname{{round}}(10NL)=\operatorname{{round}}(10\times{d.n:g}\times{d.length:g})={p["nall"]}')
            st.latex(rf'n_{{rib}}=\lfloor {p["nall"]}/{d.rib_period}\rfloor={p["nrib"]},\quad n_{{regular}}={p["nall"]}-{p["nrib"]}={p["nregular"]}')
            st.caption('N: 10 cm당 씨줄 회수. round는 정확한 절반에서 짝수 정수로 반올림. 리브는 기존 씨줄을 대체합니다.')
            explain('weave','team')
            st.latex(rf'T_w=n_wLc_w={p["nw"]}\times{d.length:g}\times{d.crimp:g}={p["tw"]:.6f}\,m')
            st.latex(rf'T_{{regular}}=n_{{regular}}Wk={p["nregular"]}\times{d.width:g}\times{d.path:g}={p["tf"]:.6f}\,m')
            st.latex(rf'T_{{rib}}=n_{{rib}}Wk={p["nrib"]}\times{d.width:g}\times{d.path:g}={p["tr"]:.6f}\,m')
            st.latex(rf'd_{{rib}}=(d_f+h)/1000=({d.df:g}+{d.h:g})/1000={p["dr"]:g}\,m')
            st.caption('위 k는 씨줄 경로계수(무차원); 화학 용출계수 k_i(day⁻¹)와 다릅니다. 직경 입력 mm를 m로 변환합니다.')
            explain('weave','team')
        elif d.structure!=MEASURED:
            if p['counts']:
                nx,ny=p['counts']
                st.latex(rf'N_x=\lfloor {d.width:g}/{d.spacing/1000:g}\rfloor+1={nx},\quad N_y=\lfloor {d.length:g}/{d.spacing/1000:g}\rfloor+1={ny}')
                st.latex(rf'T=N_xL+N_yW={nx}\times{d.length:g}+{ny}\times{d.width:g}={p["length"]:.6f}\,m')
                explain('grid')
            else:
                st.latex(r'(-x+y)/\sqrt2=ns,\quad(x+y)/\sqrt2=ns')
                st.latex(rf'T=\sum\ell_{{clip}}={p["length"]:.6f}\,m')
                st.caption(f'원점 (0,0), 경계 [0,{d.length:g}]×[0,{d.width:g}] m, 수직간격 {d.spacing/1000:g} m. 각 축의 허용 매개변수 구간을 교차합니다. 점 접촉은 길이 0으로 제외합니다.')
                explain('clip')
        if p['parts']:
            st.dataframe(p['parts'],hide_index=True)
            st.latex(r'A_{total}=\pi\sum_j d_jT_j,\quad m=\rho\frac{\pi}{4}\sum_j d_j^2T_j')
            area_terms='+'.join(f'{x["diameter"]:g}\\times{x["length"]:.6f}' for x in p['parts'])
            mass_terms='+'.join(f'({x["diameter"]:g})^2\\times{x["length"]:.6f}' for x in p['parts'])
            st.latex(rf'A_{{total}}=\pi({area_terms})={p["surface"]:.6f}\,m^2')
            st.latex(rf'm={d.rho:g}\frac{{\pi}}{{4}}({mass_terms})={p["mass"]:.6f}\,kg')
            st.caption('각 j는 원형 원사군입니다. 끝단·교차 접촉면·겹침 미보정. ρ 단위 kg/m³, d·T 단위 m.')
            explain('geometry','density')
        else:
            st.latex(rf'm_{{input}}={p["mass"]:.6f}\,kg,\quad A_{{input}}={p["surface"]:.6f}\,m^2')
            st.caption('사용자 실측 입력값으로 직접 사용. 시료·측정 방법 및 PA6 재질은 사용자가 확인해야 합니다. 출처: 사용자 입력, 문헌값 아님.')
        if d.structure==STRAW:
            st.latex(rf'g_{{cross}}=s-d_w={d.spacing:g}-{d.dw:g}={p["cross"]:g}\,mm')
            st.latex(rf'g_{{long}}=100/N-d_f=100/{d.n:g}-{d.df:g}={p["long"]:g}\,mm')
            st.latex(rf't_{{base}}=d_w+2d_f={d.dw:g}+2\times{d.df:g}={p["t_base"]*1000:g}\,mm')
            st.latex(rf't_{{rib}}=t_{{base}}+h={p["t_base"]*1000:g}+{d.h:g}={p["t_rib"]*1000:g}\,mm')
            explain('weave','team')
        elif d.structure!=MEASURED:
            st.latex(rf'g_{{normal}}=s-d={d.spacing:g}-{d.dw:g}={p["normal_gap"]:g}\,mm,\quad t=2d={p["t_base"]*1000:g}\,mm')
            st.caption('회전 격자의 g_normal은 원사 사이 수직 틈으로 진행방향 틈과 동일하지 않습니다. t=2d는 롤 비교를 위한 층 두께 가정입니다.')
            explain('grid','team')
        st.latex(r'D=\sqrt{D_{core}^2+4Lt/\pi}')
        for k in ('base','rib'):
            st.latex(rf'D_{{{k}}}=\sqrt{{{d.core:g}^2+4\times{d.length:g}\times{p["t_"+k]:g}/\pi}}={p["roll_"+k]:.6f}\,m')
        explain('roll')
        st.latex(rf'm_{{waste}}=m/y={p["mass"]:.6f}/{d.recovery:g}={p["waste"]:.6f}\,kg')
        st.caption('y: 재활용 원료 회수율(무차원). R2에서는 동일 회수율을 가정한 재료 소요 환산일 뿐 실제 시판제품 제조 정보가 아닙니다.')
        explain('team','aba')
    with st.expander('② 매몰부 추정 표면적',expanded=True):
        st.latex(rf'A_{{bur}}=A_{{total}}f_{{bur}}={p["surface"]:.6f}\times{m["burial"]:g}={p["buried"]:.6f}\,m^2')
        st.latex(rf'A_{{unbur}}=A_{{total}}(1-f_{{bur}})={p["unburied"]:.6f}\,m^2')
        st.caption('f_bur: 매몰 표면 비율. 공극수 접촉 가능 영역이며 실제 젖은 면적 또는 지속 침수를 뜻하지 않습니다.')
        explain('team','geometry')
    with st.expander('③ 물질별 누적 용출률·용출량',expanded=True):
        for c in m['chemicals']:
            chem=c['chemical']; r=c['current']
            st.write(c['name']+(' · 반정량' if chem.semiquantitative else ''))
            st.latex(rf'r({day})={chem.ce}[1-{chem.a}e^{{-{chem.k}\times{day}}}]={r["rate_percent"]:.6f}\%')
            st.latex(rf'M=m_{{PA6}}(r/100)10^6={p["mass"]:.6f}({r["rate_percent"]:.6f}/100)10^6={r["cumulative_mg"]:.6f}\,mg')
            st.latex(rf'q_{{PA6}}=M/A_{{total}}={c["q_pa6"]:.6f}\,mg/m^2,\quad q_{{plan}}=M/(LW)={c["q_plan"]:.6f}\,mg/m^2')
        st.caption('Ce·r: PA6 질량 대비 %, a: 무차원, k_i: 용출속도(day⁻¹), t: 수중 접촉 시나리오 일수. 30°C 고정. 전체 질량에는 매몰률 미적용.')
        explain('bridson','geometry')
    with st.expander('④ 매몰부 공극수 배분',expanded=True):
        for c in m['chemicals']:
            st.write(c['name'])
            st.latex(rf'f_{{pw}}=f_{{bur}}\eta={m["burial"]:g}\times{c["eta"]:g}={c["allocation"]:g}')
            st.latex(rf'M_{{pw,in}}=M f_{{pw}}={c["current"]["cumulative_mg"]:.6f}\times{c["allocation"]:g}={c["current"]["pw_in"]:.6f}\,mg')
        st.caption('eta: 매몰부 유래 용출량의 공극수 이동·유지 비율. 매몰 표면 비율을 전체 질량 기준 용출량에 한 번 배분하는 가정이며, 매몰부 실측 용출률이 아닙니다.')
        explain('team')
    with st.expander('⑤ 일별 투입·반감기·잔존량',expanded=True):
        st.latex(r'\lambda=\ln2/H,\quad \Delta M(j)=M(j)-M(j-1),\quad \Delta M_{pw}=f_{pw}\Delta M')
        st.latex(r'R_{pw}(t)=\sum_{j=1}^t\Delta M_{pw}(j)e^{-\lambda(t-j)}')
        st.caption('H: 환경 반감기(day), λ: 환경 분해속도(day⁻¹), 용출속도 k_i와 별개. 날짜 말 투입. 양의 초기 절편을 첫날 M(1)에 포함, 수지용 M(0)=0.')
        for c in m['chemicals']:
            st.write(c['name'])
            if c['half'] is None: st.latex(r'\lambda=0,\quad R_{pw}=M_{pw,in}')
            else: st.latex(rf'\lambda=\ln2/{c["half"]:g}={c["decay"]:.8f}\,day^{{-1}}')
            st.latex(rf'R_{{pw}}({day})={c["current"]["pw_remaining"]:.6f}\,mg')
            if c['chemical'].semiquantitative and c['half'] is not None: st.warning(HYPOTHETICAL)
            st.dataframe([{'투입일':x['day'],'전체 신규 [mg]':x['total_increment'],'공극수 신규 [mg]':x['pw_increment'],
                           '감쇠 일수':x['age'],'공극수 잔존 기여 [mg]':x['remaining']} for x in c['contributions']],hide_index=True)
        st.caption(HALF_NOTE)
        explain('decay','kubo','team')
    with st.expander('⑥ 모래 공극률',expanded=True):
        st.latex(rf'n=1-\rho_b/\rho_s=1-{m["rho_b"]:g}/{m["rho_s"]:g}={m["volume"]["porosity"]:.6f}')
        st.caption('ρb: 건조 모래 질량/전체 부피, ρs: 입자 밀도(kg/m³). n은 무차원 공극 부피 비율로 포화도와 다릅니다.')
        explain('soil','team')
    with st.expander('⑦ 포화도·공극수 부피',expanded=True):
        st.latex(rf'z={m["depth"]:g}/100={m["depth"]/100:g}\,m')
        st.latex(rf'V_{{pore}}=Az n={p["area"]:g}\times{m["depth"]/100:g}\times{m["volume"]["porosity"]:.6f}={m["volume"]["pore_volume"]:.6f}\,m^3')
        st.latex(rf'V_{{water}}=V_{{pore}}S_w10^3={m["volume"]["pore_volume"]:.6f}\times{m["saturation"]:g}\times1000={m["volume"]["water"]:.6f}\,L')
        st.caption('S_w: 공극 중 물이 차지하는 비율. 25·50·100%는 가정이며 건조 조상대의 대표 포화도 아님. 0%면 mg/L 계산 차단. 적은 물에 전량 배분하면 값이 과도하게 커질 수 있습니다.')
        explain('geometry','soil','team')
    with st.expander('⑧ 공극수 환산농도·최고·평균·모래 부하',expanded=True):
        st.write(PW_NOTE)
        st.latex(r'C_{peak}=\max_{1\le j\le t}C_{pw}(j),\quad C_{avg}=\frac1t\sum_{j=1}^t C_{pw}(j)')
        for c in m['chemicals']:
            x=c['selected']; r=c['current']; st.write(c['name'])
            if x['water']==0: st.info('계산 불가: 공극수 없음')
            else:
                st.latex(rf'C_{{pw}}({day})={r["pw_remaining"]:.6f}/{x["water"]:.6f}={x["selected"]:.6f}\,mg/L')
                st.latex(rf'C_{{peak}}={x["peak"]:.6f}\,mg/L\ (day\ {x["peak_day"]}),\quad C_{{avg}}={x["average"]:.6f}\,mg/L')
            st.latex(rf'm_{{sand}}=\rho_bAz={m["rho_b"]:g}\times{p["area"]:g}\times{m["depth"]/100:g}={x["sand"].mass_kg:.6f}\,kg')
            st.latex(rf'C_{{sand,V4}}=R_{{total}}/m_{{sand}}={r["remaining_mg"]:.6f}/{x["sand"].mass_kg:.6f}={x["sand"].concentration_mg_kg:.6f}\,mg/kg')
        st.caption('최고일 동률이면 최초일. 산술평균은 날짜 말 값의 평균이며 연속시간 시간가중 노출량이나 체내흡수량이 아닙니다. mg/kg는 전체 잔존량을 쓰는 V4 대안 시나리오로 공극수 지표와 합산하지 않습니다.')
        explain('geometry','team','anzg','epa')
    with st.expander('⑨ 굴 깊이 기준 잠재적 공극수 접촉농도',expanded=True):
        st.latex(r'C_{burrow,proxy}(z,t)=C_{pw}(z,t)')
        for c in m['chemicals']:
            st.write(c['name'])
            for h in sorted(set((m['surface'],m['depth'],m['average'],m['maximum']))):
                x=next(x for x in c['layers'] if x['depth']==h)
                st.caption(f'표층 {h:g} cm까지 완전혼합 시나리오')
                if x['water']==0: st.write('계산 불가: 공극수 없음')
                else: st.latex(rf'C_{{proxy}}={c["current"]["pw_remaining"]:.6f}/{x["water"]:.6f}={x["selected"]:.6f}\,mg/L')
        st.write(BURROW_NOTE)
        st.caption('달랑게류·긴꼬리도약옆새우류 검토용. 14.4·37.6 cm의 해당 생물종·원문·대표값 산정은 출처 확인 필요. 깊이별 부피가 다른 독립 시나리오이며 굴 내부 물의 유입이나 수직 농도분포를 계산하지 않습니다.')
        explain('team','crab','amphipod')
    with st.expander('⑩ OECD 수환경 PNEC 참고 비교',expanded=True):
        st.latex(r'PNEC_{aqua}=130/1000=0.13\,mg/L')
        for c in m['chemicals']:
            if c['ratios'] is not None:
                for key,label in [('selected','선택일'),('peak','기간 최고'),('average','기간 산술평균')]:
                    st.caption(label)
                    if c['ratios'][key] is None: st.write('계산 불가: 공극수 없음')
                    else: st.latex(rf'Comparison\ ratio={c["selected"][key]:.6f}/{PNEC}={c["ratios"][key]:.6f}')
        st.write(PNEC_NOTE)
        explain('oecd','team')
