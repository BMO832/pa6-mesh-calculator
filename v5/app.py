"""Run from repository root: python -m streamlit run v5/app.py"""
import sys, math, csv, io
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import streamlit as st
from v5.engine import Design, geometry, exposures, pore_volume, solid_loading, PRESETS, HALF_LIVES, PNEC
from v4.model import CHEMICALS
from v4.mesh_engine import SQUARE, ROTATED

st.set_page_config(page_title='PA6 Mesh Calculator V5',layout='wide')
st.markdown('''<style>[data-testid="stLatex"]{overflow-x:auto;max-width:100%}@media(max-width:850px){[data-testid="stHorizontalBlock"]{flex-direction:column}[data-testid="stColumn"]{min-width:0;width:100%}}</style>''',unsafe_allow_html=True)
st.title('PA6 Mesh Calculator V5')
st.caption('물리 구조 · 공극수 노출 환산 · 출처/가정 분리 · 30°C · 1-92일 | 실측 노출농도 또는 안전성 판정이 아닙니다.')

SOURCES={
 'ABA':('미국 Access Board, ABA Chapter 10', 'https://www.access-board.gov/aba/chapter/ch10/','해변 접근로 유효폭 1525 mm 및 개구부 구 통과 13 mm 제한(해당 적용 요건 검토 필요)'),
 'PA6':('NETZSCH, PA6 자료','https://analyzing-testing.netzsch.com/ko/polrimeo-netzsch-com/engineering-thermoplastics/pa6-polyamide-6','PA6의 일반 물성. 재생 원사 밀도 1130 kg/m³는 팀 가정'),
 'Bridson':('Bridson et al. (2023), Table 4','https://doi.org/10.1016/j.envadv.2023.100359','30°C 수중 PA6 미세플라스틱 용출 경험식/계수, 올리고머 반정량'),
 'Fortmann':('Fortmann & Rosenberg (1984)','https://doi.org/10.1016/0045-6535(84)90008-0','카프로락탐 수중 환경 거동 참고. 5-14일을 직접 확인한 실측 반감기로 사용하지 않음'),
 'OECD':('OECD SIDS, epsilon-Caprolactam','https://hpvchemicals.oecd.org/ui/handler.axd?id=C1609721-9FDF-4D5F-8F15-FB4F50710C72','수환경 PNEC 참고 비교(0.13 mg/L, EC50 130 mg/L / 평가계수 1000)'),
 'Soil':('Kansas State University, Soil Density','https://kstatelibraries.pressbooks.pub/soilslabmanual/chapter/soil-density/','용적밀도와 입자밀도를 구분한 공극률 관계식'),
 'ANZG':('ANZG Sediment Toxicant Guidelines','https://www.waterquality.gov.au/anz-guidelines/guideline-values/derive/field-effects/method-toxicants-sediments','퇴적물 노출평가의 일반적 맥락. 본 환산농도 식을 직접 제시하지 않음'),
 'Peirce':('Peirce (1937), The Geometry of Cloth Structure','https://doi.org/10.1080/19447023708658809','직물의 굴곡에 대한 참고. 팀 고유 직조 공식과 계수의 출처는 아님'),
 'Clip':('J. Imaging (2022), 선분 클리핑 참고','https://doi.org/10.3390/jimaging8100286','직선-영역 교차 관련 참고. V4 코드를 Liang-Barsky 구현이라고 주장하지 않음'),
 'Roll':('Rollspec, Roll Diameter Guide','https://rollspec.com/guides/roll-diameter-length/','롤의 원환 면적 기반 기하학적 계산 참고'),
 'Burrow1':('저서생물 굴 참고 1 (종별 자료 확인 필요)','https://pmc.ncbi.nlm.nih.gov/articles/PMC6494038/','14.4 cm 및 37.6 cm 값의 정확한 귀속·집계 방식 미확인'),
 'Burrow2':('저서생물 굴 참고 2 (종별 자료 확인 필요)','https://doi.org/10.1163/193724097X00107','굴 깊이 직접 실측값으로 검증하지 않음'),
}

def cite(key):
    name,url,scope=SOURCES[key]
    st.caption(f'출처/참고: {name} — {scope}')
    st.markdown(f'[원문 링크]({url})')

def info(kind,desc,calibration=False):
    st.caption(f'수식 구분: {kind} | 출처/조건: {desc}'+(' | 시료 실측 보정 필요' if calibration else ''))

def metric(label,value,unit='',fmt=',.4f'):
    st.metric(label,(format(value,fmt)+' '+unit) if value is not None else '계산 불가: 공극수 없음')

def st_chart(rows,kind):
    st.line_chart(rows,x='day',y=kind)

left,right=st.columns([1.05,.95],gap='large')
with left:
    st.header('설계 조건')
    kind=st.selectbox('구조 및 시료',('C0','A1','A2','A3','A4','R1','R2','직접 짚신형'))
    wchoice=st.selectbox('너비 프리셋',('1.5 m (팀 비교 기준)','1.525 m (ABA 참고)','1.65 m','1.7 m','직접 입력'))
    wlookup={'1.5 m (팀 비교 기준)':1.5,'1.525 m (ABA 참고)':1.525,'1.65 m':1.65,'1.7 m':1.7}
    length=st.number_input('L [m]',min_value=.001,value=10.,format='%.4f')
    width=st.number_input('W [m]',min_value=.001,value=wlookup.get(wchoice,1.5),format='%.4f') if wchoice=='직접 입력' else wlookup[wchoice]
    ds=Design(kind=kind,length=length,width=width)
    if kind in PRESETS:
        s,n,h=PRESETS[kind]; ds=Design(kind=kind,length=length,width=width,spacing=s,n=n,rib_h=h)
        st.caption(f'시료 {kind}: s={s:g} mm, N={n:g}회/10cm, 리브 h={h:g} mm. 아래에서 수정 가능')
    if kind in PRESETS or kind=='직접 짚신형':
        dw=st.number_input('날줄 직경 [mm]',min_value=.01,value=ds.warp_d)
        spacing=st.number_input('날줄 중심 간격 [mm]',min_value=.01,value=ds.spacing)
        df=st.number_input('씨줄 직경 [mm]',min_value=.01,value=ds.weft_d)
        n=st.number_input('씨줄 밀도 [회/10cm]',min_value=.01,value=ds.n)
        rib_h=st.number_input('리브 요철 높이 [mm]',min_value=0.,value=ds.rib_h)
        period=st.number_input('리브 주기 [회당 1회]',min_value=1,value=5,step=1)
        k=st.number_input('씨줄 경로계수',min_value=.001,value=1.6)
        cw=st.number_input('날줄 굴곡계수',min_value=.001,value=1.05)
        ds=Design(kind=kind,length=length,width=width,warp_d=dw,spacing=spacing,weft_d=df,n=n,
                  rib_h=rib_h,rib_period=period,k=k,cw=cw)
    else:
        st.caption('R1은 V4 직교 격자형, R2는 실측값을 직접 입력하는 시판 매트 비교군입니다.')
        ref_d=st.number_input('필라멘트 직경 [mm]',min_value=.01,value=3.)
        ref_s=st.number_input('필라멘트 중심 간격 [mm]',min_value=.01,value=12.)
        structure=st.selectbox('격자 구조', (SQUARE,ROTATED),index=0,disabled=(kind=='R1'))
        mm=ma=None
        if kind=='R2':
            use_measured=st.checkbox('실측 질량 및 표면적 사용',value=False)
            if use_measured:
                mm=st.number_input('실측 PA6 질량 [kg]',min_value=.00001,value=20.)
                ma=st.number_input('실측 표면적 [m²]',min_value=.00001,value=24.)
        ds=Design(kind=kind,length=length,width=width,reference_d=ref_d,reference_s=ref_s,
                  reference_structure=structure,measured_mass=mm,measured_area=ma)
    rho=st.number_input('PA6 밀도 [kg/m³]',min_value=.001,value=1130.)
    recovery=st.number_input('원료 회수율 [%]',min_value=.01,max_value=100.,value=60.)/100
    core=st.number_input('롤 심지 직경 [m]',min_value=.001,value=.15)
    from dataclasses import replace
    ds=replace(ds,rho=rho,recovery=recovery,core=core)
    try:
        g=geometry(ds)
    except (ValueError,OverflowError) as e:
        st.error(str(e)); st.stop()
    st.subheader('물리 구조 결과')
    a,b=st.columns(2)
    with a:
        metric('PA6 전체 질량',g['mass'],'kg')
        metric('매트 전체 표면적',g['area'],'m²')
        metric('진행 직각 틈',g['gap_cross'],'mm')
    with b:
        metric('전체 필라멘트 길이',g['total_length'],'m')
        metric('필요 폐어망',g['waste'],'kg')
        metric('진행 방향 틈',g['gap_long'],'mm')
    st.caption(f"두께 {g['thickness_base']*1000:.3f}-{g['thickness_rib']*1000:.3f} mm | 롤 지름 {g['roll_base']*100:.2f}-{g['roll_rib']*100:.2f} cm")
    st.caption('내부 목표: 진행 직각 틈 10 mm 이하, 진행 방향 틈 6.5 mm 이하(법적 기준 아님). ABA 개구부 기준 약 13 mm는 구 통과 기준으로 단순 1차원 틈과 동일한 판정이 아닙니다.')
    # Geometric conceptual visualization, never claims 3D physical weave.
    if kind in PRESETS or kind=='직접 짚신형':
        st.markdown('**짚신형 개념 미리보기(실제 리브 단면 또는 실 굴곡 미재현)**')
        horiz=''.join(f'<line x1="0" y1="{i*13}" x2="360" y2="{i*13}" stroke="{("#bc7f33" if i%5==0 else "#748fa6")}" stroke-width="{(5 if i%5==0 else 2)}"/>' for i in range(1,14))
        vert=''.join(f'<line x1="{i*13}" y1="0" x2="{i*13}" y2="185" stroke="#556e88" stroke-width="3"/>' for i in range(1,27))
        st.markdown(f'<svg viewBox="0 0 360 185" style="max-width:100%;background:#edf1f4">{vert}{horiz}</svg>',unsafe_allow_html=True)
    st.divider()
    st.header('화학물질 및 환경 조건')
    chosen=st.multiselect('화학물질',list(CHEMICALS),default=['Caprolactam'])
    days=st.slider('기간 [일]',1,92,7)
    if days>64: st.warning('65-92일은 Bridson의 1-64일 실험 범위를 넘어서는 경험식 외삽 구간입니다.')
    buried=st.slider('매몰부 표면적 비율 [%]',0,100,50)/100
    eta=st.slider('매몰부 유래 공극수 이동·유지 비율 [%]',0,100,100)/100
    metric('매몰부 추정 표면적 (공극수 접촉 가능 영역)',g['area']*buried,'m²')
    st.caption(f"비매몰부 표면적(보조 항목): {g['area']*(1-buried):.4f} m² | 매몰부가 실제로 지속 젖은 면적이라는 뜻은 아닙니다.")
    bulk=st.number_input('모래 건조 용적밀도 [kg/m³]',min_value=.01,value=1500.)
    particle=st.number_input('모래 입자밀도 [kg/m³]',min_value=.01,value=2650.)
    swchoice=st.selectbox('수분 포화도 시나리오',('25%','50%','100%','직접 입력'),index=1)
    sw=st.number_input('직접 포화도 [%]',min_value=0.,max_value=100.,value=50.)/100 if swchoice=='직접 입력' else float(swchoice[:-1])/100
    depth=st.number_input('모래 선택 혼합 깊이 [cm]',min_value=.1,max_value=130.,value=10.)
    halfs={}
    for name in chosen:
        opts=('분해 미반영','5일','9.5일','14일')
        idx=2 if name=='Caprolactam' else 0
        label=st.selectbox(f'{name} — 반감기',opts,index=idx)
        halfs[name]={'분해 미반영':None,'5일':5.,'9.5일':9.5,'14일':14.}[label]
        if name!='Caprolactam' and halfs[name]: st.warning(f'{name}: 직접 검증된 반감기 없음. 카프로락탐 시나리오를 차용한 가상 민감도 분석')
    try:
        if not chosen: raise ValueError('화학물질을 하나 이상 선택하세요.')
        result={name:exposures(g['mass'],name,days,buried,eta,halfs[name],g['plan'],depth,bulk,particle,sw) for name in chosen}
    except (ValueError,OverflowError) as e:
        st.error(str(e)); st.stop()
    st.divider()
    st.header('노출 평가 결과')
    st.caption('전량 용존 가정의 공극수 환산농도 (mg/L): 실제 용존 농도가 아닌 단순 완전혼합 환산값')
    rows=[]; csv_rows=[]; comparison=[]
    for name,r in result.items():
        q=r['current']; rows.append({'물질':name,'누적 총 용출량 [mg]':q['total_mg'],
             '공극수 배분 누적량 [mg]':q['allocated_mg'],'공극수 잔존량 [mg]':q['remaining_mg'],
             '공극수 부피 [L]':q['volume_l'],'선택일 환산농도 [mg/L]':q['concentration'],
             '최고 환산농도 [mg/L]':r['peak'],'최고일':r['peak_day'],
             '산술평균 환산농도 [mg/L]':r['average'],
             '모래층 전체 용출부하 [mg/kg dry sand]':solid_loading(q['total_mg'],g['plan'],depth,bulk)})
        for qd in r['rows']:
            csv_rows.append({'물질':name,**qd,'매몰률':buried,'이동·유지율':eta,'포화도':sw,'혼합 깊이 cm':depth})
        for sat in (.25,.50,1.):
            cases=[('분해 미반영',None)]
            if halfs[name] is not None: cases.append(('선택 반감기',halfs[name]))
            for label,half in cases:
                x=exposures(g['mass'],name,days,buried,eta,half,g['plan'],depth,bulk,particle,sat)
                comparison.append({'물질':name,'포화도':f'{sat*100:g}%','분해 설정':label,
                   '선택일 [mg/L]':x['current']['concentration'],'최고 [mg/L]':x['peak'],
                   '최고일':x['peak_day'],'산술평균 [mg/L]':x['average']})
    st.dataframe(rows,hide_index=True,use_container_width=True)
    st.caption('모래 mg/kg는 V4 전체 소재의 누적 용출량을 모두 모래층에 남긴 독립적 총부하 시나리오입니다. 공극수 구획 잔존량과 더해 물질수지를 계산하지 않습니다.')
    st.subheader('포화도 25%, 50%, 100% 및 분해조건 비교')
    st.dataframe(comparison,hide_index=True,use_container_width=True)
    st.caption('동일한 PA6 구조, 배분율, 혼합 깊이 조건의 독립 시나리오입니다. 선택일·최고·산술평균 환산농도는 체내 흡수량이나 실측 시간가중 노출이 아닙니다.')
    st.subheader('깊이별 잠재적 공극수 접촉농도')
    depths=[('표층 1cm까지 완전혼합 시나리오',1.),('표층 10cm까지 완전혼합 시나리오',10.),
            ('14.4cm까지 완전혼합 시나리오 (문헌 확인 필요)',14.4),
            ('37.6cm까지 완전혼합 시나리오 (문헌 확인 필요)',37.6),
            (f'직접 입력 {depth:g}cm까지 완전혼합 시나리오',depth)]
    layer_rows=[]
    for name in chosen:
        for label,z in depths:
            x=exposures(g['mass'],name,days,buried,eta,halfs[name],g['plan'],z,bulk,particle,sw)
            layer_rows.append({'물질':name,'깊이 시나리오':label,'공극수 부피 [L]':x['volume_l'],
                               '굴 깊이 기준 잠재적 공극수 접촉농도 [mg/L]':x['current']['concentration']})
    st.dataframe(layer_rows,hide_index=True,use_container_width=True)
    st.caption('해당 깊이까지의 공극수가 균일하게 혼합된다는 가정에 따른 참고 농도로 실제 굴 내부의 용존 농도나 개체의 체내 흡수량이 아닙니다. 깊이별 값은 실제 수직 농도분포가 아닙니다. 달랑게류 및 긴꼬리도약옆새우류의 굴 깊이 귀속은 문헌 확인 필요.')
    st.subheader('카프로락탐 OECD PNEC 참고 비율')
    if 'Caprolactam' in result:
        rr=result['Caprolactam']['pnec_ratios']
        st.dataframe([{'구분':k,'OECD 수환경 PNEC [mg/L]':PNEC,'참고 비교 비율':rr[key]} for k,key in
                      [('선택일','current'),('기간 최고','peak'),('기간 산술평균','average')]],hide_index=True)
        st.caption('OECD PNEC는 조상대 달랑게류·긴꼬리도약옆새우류에 직접 검증한 기준이 아닙니다. 1 초과/미만은 생태계 피해 또는 안전 판정이 아닙니다.')
    else: st.info('카프로락탐 선택 시 참고 비교를 표시합니다. 올리고머의 PNEC는 설정하지 않았습니다.')
    st.subheader('시간별 공극수 환산농도')
    chart_rows=[{'day':r['day'],'물질':name,'mg/L':r['concentration']} for name,v in result.items() for r in v['rows']]
    st.line_chart(chart_rows,x='day',y='mg/L',color='물질')
    st.subheader('R1 - C0 기준 구조 비교')
    refs=[]
    for key in ('R1','C0'):
        ref=geometry(Design(kind=key,length=length,width=width))
        refs.append({'구조':key,'질량 [kg]':ref['mass'],'표면적 [m²]':ref['area'],'진행 직각 틈 [mm]':ref['gap_cross'],'진행 방향 틈 [mm]':ref['gap_long']})
    st.dataframe(refs,hide_index=True)
    buff=io.StringIO(); writer=csv.DictWriter(buff,fieldnames=list(csv_rows[0]));writer.writeheader();writer.writerows(csv_rows)
    st.download_button('일별 결과 CSV 다운로드',buff.getvalue().encode('utf-8-sig'),file_name='pa6_v5_daily.csv',mime='text/csv')

with right:
    st.header('실시간 계산 원리·출처')
    with st.expander('1. 직조 구조별 길이·질량·표면적',expanded=True):
        if kind in PRESETS or kind=='직접 짚신형':
            st.latex(r'n_w=\lfloor W/s\rfloor+1,\quad n_{all}=\mathrm{round}(10NL)')
            st.latex(r'n_{rib}=\lfloor n_{all}/p\rfloor,\quad n_{regular}=n_{all}-n_{rib}')
            st.latex(r'T_w=n_wLc_w,\quad T_f=n_{regular}Wk,\quad T_r=n_{rib}Wk')
            st.latex(r'd_r=d_f+h,\quad g_{cross}=s-d_w,\quad g_{long}=100/N-d_f')
            st.latex(r'm=\rho\pi(d_w^2T_w+d_f^2T_f+d_r^2T_r)/4')
            st.latex(r'A=\pi(d_wT_w+d_fT_f+d_rT_r)')
            st.write('대입값/계산 결과:',g['details'])
            info('C 자체 유도 + D 팀 설계 가정',f'날줄 {ds.warp_d:g} mm, 씨줄 {ds.weft_d:g} mm, s={ds.spacing:g} mm, N={ds.n:g}, k={ds.k:g}, cw={ds.cw:g}; 리브는 일반 씨줄을 대체',True)
            cite('Peirce')
        else:
            st.latex(r'N_x=\lfloor W/s\rfloor+1,\quad N_y=\lfloor L/s\rfloor+1')
            st.latex(r'T=N_xL+N_yW,\quad A=\pi dT,\quad m=\rho\pi d^2T/4')
            st.write('실제 계산 구조:',g['details'])
            info('B 기본 기하학 + C 자체 직선 배치/클리핑','R1 직교, R2 지정 직교·회전 구조. 교점 계산에 V4 자체 클리핑 구현 사용',True)
            cite('Clip')
        st.latex(r'D_{roll}=\sqrt{D_{core}^2+4Lt/\pi},\quad m_{waste}=m/recovery')
        st.write(f"PA6 {g['mass']:.6f} kg · 표면적 {g['area']:.6f} m² · 롤 {g['roll_base']:.4f}-{g['roll_rib']:.4f} m · 폐어망 {g['waste']:.6f} kg")
        info('B 롤 기하 + D 회수율·두께 가정',f'심지={core:g} m, 회수율={recovery:.2%}, 유효두께·공극 및 압축 미반영',True)
        cite('Roll');cite('PA6');cite('ABA')
    with st.expander('2. 매몰부 추정 표면적'):
        st.latex(r'A_{bur}=f_{bur}A_{total},\quad A_{unbur}=(1-f_{bur})A_{total}')
        st.write(f"{buried:.4f} × {g['area']:.6f} = {g['area']*buried:.6f} m²")
        info('D 팀 시나리오 가정','매몰은 공극수 접촉 가능 면적의 기하학적 대용값; 실제 습윤면적 아님',True)
    with st.expander('3. PA6 질량 기반 누적 용출곡선'):
        st.latex(r'r_i(t)=C_{e,i}(1-a_i e^{-k_i t}),\quad M_i(t)=m_{PA6}r_i(t)10^4\ (mg)')
        for name,r in result.items():
            c=CHEMICALS[name]
            st.write(f'{name}: Ce={c.ce}, a={c.a}, k={c.k} day⁻¹; {days}일 {r["current"]["rate"]:.8f}% → {r["current"]["total_mg"]:.6f} mg')
        info('A 문헌 경험식 + B 단위변환','30°C, 1-64일 자료. 65-92일 외삽; 재활용 모노필라멘트 실측 아님',True)
        cite('Bridson')
    with st.expander('4. 공극수 배분 및 5. 반감기'):
        st.latex(r'f_{pw}=f_{bur}\eta_i,\quad\Delta M_{pw,i}(j)=f_{pw}\Delta M_i(j)')
        st.latex(r'\lambda_i=\ln2/H_i,\quad R_{pw,i}(t)=R_{pw,i}(t-1)e^{-\lambda_i}+\Delta M_{pw,i}(t)')
        st.write(f'공극수 배분계수 = {buried:.4f} × {eta:.4f} = {buried*eta:.6f} (중복 적용 없음)')
        for name,r in result.items():
            st.write(f'{name}: 전체 누적 {r["current"]["total_mg"]:.6f} mg, 공극수 배분 {r["current"]["allocated_mg"]:.6f} mg, 잔존 {r["current"]["remaining_mg"]:.6f} mg; H={halfs[name]} 일')
        info('B 1차 반응속도론 + D 날짜 말 신규투입·배분 가정','V4 양의 절편이 있지만 M(0)=0으로 두고 첫날 M(1) 전체를 투입. H=5/9.5/14일은 시나리오값',True)
        cite('Fortmann')
    with st.expander('6. 모래 공극률 및 7. 포화 공극수량'):
        st.latex(r'\phi=1-\rho_b/\rho_s,\quad V_{water}=LW(z/100)\phi S_w\times1000\ L')
        z=result[chosen[0]]
        st.write(f'1 - {bulk:g}/{particle:g} = {z["porosity"]:.8f}')
        st.write(f'{g["plan"]:.6f} × {depth:g}/100 × {z["porosity"]:.8f} × {sw:.4f} × 1000 = {z["volume_l"]:.6f} L')
        info('B 밀도·부피 관계 + D 균일 포화도','용적밀도·입자밀도·수분 포화도는 실측 이전의 설정값',True)
        cite('Soil')
    with st.expander('8. 전량 용존 가정 공극수 환산농도'):
        st.latex(r'C_{pw,i}(z,t)=R_{pw,i}(t)/V_{water}(z)')
        for name,r in result.items():
            st.write(f'{name}: {r["current"]["remaining_mg"]:.6f} mg / {r["volume_l"]:.6f} L = '+
                     (f'{r["current"]["concentration"]:.8f} mg/L' if r['current']['concentration'] is not None else '계산 불가: 공극수 없음'))
            st.write(f'기간 최고 {r["peak"]} mg/L ({r["peak_day"]}일), 일별 산술평균 {r["average"]} mg/L')
        info('D 연구팀 단순 완전혼합 환산식','매몰부 유래 용출물이 해당 혼합층 공극수에 모두 용존·균일 혼합되며 흡착·실제 용해도·물질 이동 및 유실 미반영',True)
        cite('ANZG')
    with st.expander('9. 굴 깊이 기준 잠재적 공극수 접촉농도'):
        st.latex(r'C_{burrow,proxy}(z,t)=C_{pw}(z,t)')
        st.write('선택한 각 깊이 0-z cm 층에 같은 유입량이 균일하게 혼합되는 독립 대안 시나리오입니다. 실제 굴 내 수량, 수리학적 연결, 개체 흡수량을 뜻하지 않습니다.')
        info('D 생물 노출 대리지표','14.4 cm / 37.6 cm의 해당 생물·정확한 원문 및 대표값 산정 방식 확인 필요',True)
        cite('Burrow1');cite('Burrow2')
    with st.expander('10. OECD PNEC 참고 비교'):
        st.latex(r'Ratio=C_{pw,caprolactam}/0.13')
        if 'Caprolactam' in result:
            for k,v in result['Caprolactam']['pnec_ratios'].items(): st.write(f'{k}: {v if v is not None else "계산 불가: 공극수 없음"}')
        st.write('수환경 녹조류 EC50=130 mg/L에 평가계수 1000을 적용한 PNEC=0.13 mg/L. 조상대 저서생물의 직접 독성기준 아님; 안전성 자동 판정 안 함.')
        info('A OECD 수환경 PNEC + D 팀 참고비율','노출조건·염분·생물종·시간 차이를 평가하지 않음')
        cite('OECD')
    st.caption('자료 구분: A 문헌 기반, B 기본 수학/기하학, C 자체 유도, D 팀 설계·가정. 실측값으로 표시된 수치는 사용자가 직접 입력한 R2 항목뿐입니다.')
