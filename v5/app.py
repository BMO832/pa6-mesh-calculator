"""V5 replacement; existing V1-V4 entrypoints remain unchanged."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import streamlit as st
from v5.engine import Design, STRAW, MEASURED, SQUARE, ROTATED, PRESETS, CHEMICALS, HALF_LIVES, build_model, design_comparison
from v5.preview import design_preview
from v5.panel import show_panel
from v5.reporting import report, export_csv, SAND
from v5.sources import PW_LABEL, PW_NOTE, BURROW_NOTE, HALF_NOTE, HYPOTHETICAL, LIMITS, PNEC_NOTE, SOURCES, explain


def apply_preset():
    name=st.session_state['preset']
    if name in PRESETS:
        s,n,h=PRESETS[name]
        st.session_state.update(structure=STRAW,dw=3.,df=1.2,spacing=s,n=n,h=h,path=1.6,crimp=1.05,rib_period=5)
    elif name=='R1': st.session_state.update(structure=SQUARE,dw=3.,spacing=12.)
    elif name=='R2': st.session_state['structure']=MEASURED


def apply_width():
    if st.session_state['width_preset']!='직접 입력': st.session_state['width']=float(st.session_state['width_preset'])


def apply_saturation():
    if st.session_state['sat_preset']!='직접 입력': st.session_state['sat']=float(st.session_state['sat_preset'].rstrip('%'))


def number(label,key,value,**kwargs):
    if key not in st.session_state: st.session_state[key]=value
    return st.number_input(label,key=key,**kwargs)


def chart(rows,title,xtitle,ytitle,log=False):
    st.subheader(title)
    if not rows:
        st.info('계산 불가: 공극수 없음'); return
    if log and any(r['y']<=0 for r in rows):
        st.caption('0 값은 로그축에 표시할 수 없어 선형축을 사용합니다.'); log=False
    st.vega_lite_chart(spec={'data':{'values':rows},'mark':{'type':'line'},'encoding':{
        'x':{'field':'x','type':'quantitative','title':xtitle},
        'y':{'field':'y','type':'quantitative','title':ytitle,'scale':{'type':'log' if log else 'linear'}},
        'color':{'field':'series','type':'nominal','title':'물질·시나리오'},
        'tooltip':[{'field':'series'},{'field':'x'},{'field':'y','format':'.6g'},{'field':'note'}]}},width='stretch')


st.set_page_config(page_title='PA6 Mesh Calculator V5',layout='wide')
st.markdown('''<style>
[data-testid="stLatex"] {overflow-x:auto; max-width:100%;}
[data-testid="stLatex"] .katex-display {overflow-x:auto; overflow-y:hidden; padding:.4rem 0;}
@media(max-width:850px){[data-testid="stHorizontalBlock"]{flex-direction:column;}[data-testid="stColumn"]{width:100%;flex:1 1 100%;min-width:0;}}
</style>''',unsafe_allow_html=True)
st.title('PA6 Mesh Calculator V5')
st.caption('물리 구조·공극수 노출 통합 | 전량 용존 환산 시나리오 | V5 보완 지시문 반영판')
left,right=st.columns([1.1,.9],gap='large')
with left:
    st.header('설계 조건')
    st.selectbox('시료 프리셋',['C0','A1','A2','A3','A4','R1','R2'],key='preset',on_change=apply_preset)
    st.caption('프리셋은 시작 설계값입니다. 아래 값을 바꾸면 현재 사용자 조건으로 계산합니다.')
    structure=st.selectbox('직조 구조',[STRAW,SQUARE,ROTATED,MEASURED],key='structure')
    length=number('이동로 길이 L [m]','length',10.,format='%.4f')
    st.selectbox('너비 프리셋 [m]',['1.5','1.525','1.65','1.7','직접 입력'],key='width_preset',on_change=apply_width)
    width=number('이동로 너비 W [m]','width',1.5,format='%.4f')
    st.caption('1.5 m는 팀 비교값. 1.525 m는 미국 ABA 해변 접근로 유효폭 참고값이며 적용 여부는 별도 검토입니다.')
    kw=dict(structure=structure,length=length,width=width)
    if structure==MEASURED:
        st.info('R2는 시판 매트의 해당 크기 시료 실측값을 입력합니다. 미입력값을 추정하지 않습니다.')
        for key,label in [('measured_mass','실측 총질량 [kg]'),('measured_area','실측 전체 소재 표면적 [m²]'),
                          ('measured_thickness','실측 유효 두께 [mm]'),('measured_cross','실측 진행 직각 틈 [mm]'),('measured_long','실측 진행 방향 틈 [mm]')]:
            kw[key]=number(label,key,0.,min_value=0.)
        kw['measured_pa6']=st.checkbox('R2 시료가 PA6이며 입력 질량 전체에 PA6 용출식을 적용할 수 있음을 확인',key='measured_pa6')
    else:
        kw['dw']=number('날줄/기존 격자 직경 d_w [mm]','dw',3.,format='%.4f')
        kw['spacing']=number('날줄/격자 중심 간격 s [mm]','spacing',12.,format='%.4f',help='회전 격자는 인접 평행선 사이 수직 거리입니다.')
        if structure==STRAW:
            kw['df']=number('씨줄 직경 d_f [mm]','df',1.2,format='%.4f')
            kw['n']=number('씨줄 밀도 N [회/10cm]','n',20.,format='%.4f')
            kw['h']=number('요철 높이 h [mm]','h',1.,min_value=0.,format='%.4f')
            kw['rib_period']=number('리브 주기 [회당 1회]','rib_period',5,min_value=1,step=1)
            kw['path']=number('씨줄 경로계수 k','path',1.6,min_value=1.)
            kw['crimp']=number('날줄 굴곡계수 c_w','crimp',1.05,min_value=1.,format='%.4f')
    kw['rho']=number('PA6 대표 밀도 [kg/m³]','rho',1130.)
    kw['recovery']=number('원료 회수율 [%]','recovery',60.,min_value=.1,max_value=100.)/100
    kw['core']=number('심지관 외경 [m]','core',.15,format='%.4f')
    st.caption('경로계수·굴곡계수·리브 형상·회수율은 팀 가정으로 시료 실측 후 보정합니다.')
    st.header('화학물질 및 환경 조건')
    names=st.multiselect('화학물질',list(CHEMICALS),default=['Caprolactam'],key='chemicals')
    days=st.slider('수중 접촉을 가정한 평가 기간 [day]',1,92,7,key='days')
    st.caption('92일은 7-9월 설치를 고려한 시나리오입니다. 실제 해변 설치일수와 수중 접촉일수는 같지 않습니다.')
    if days>64: st.warning('65-92일은 Bridson 경험식의 외삽 범위입니다. 실제 환경의 최대 용출량을 뜻하지 않습니다.')
    burial=number('매몰부 표면적 비율 [%]','burial',50.,min_value=0.,max_value=100.)/100
    halves={}; etas={}
    for name in names:
        oligomer=CHEMICALS[name].semiquantitative
        options=['분해 미반영']+[('가상 ' if oligomer else '참고 ')+f'{h:g}일' for h in HALF_LIVES[1:]]
        selected=st.selectbox(name+' 반감기',options,index=0 if oligomer else 2,key='half_'+name)
        halves[name]=HALF_LIVES[options.index(selected)]
        etas[name]=number(name+' 공극수 이동·유지율 eta [%]','eta_'+name,100.,min_value=0.,max_value=100.)/100
        if oligomer:
            st.caption('올리고머 용출 자료는 반정량이며 실제 용존량으로 확정하지 않습니다.')
            if halves[name] is not None: st.warning(HYPOTHETICAL)
        else: st.caption(HALF_NOTE)
    density=number('건조 모래 용적밀도 ρb [kg/m³]','density',1500.,help='공극 포함 전체 부피당 건조 질량입니다. 방아머리 실측값이 아닌 가정값입니다.')
    particle=number('모래 입자밀도 ρs [kg/m³]','particle',2650.)
    st.selectbox('수분 포화도 시나리오',['25%','50%','100%','직접 입력'],index=1,key='sat_preset',on_change=apply_saturation)
    saturation=number('수분 포화도 S_w [%]','sat',50.,min_value=0.,max_value=100.,format='%.4f')/100
    depth=number('선택 혼합 깊이 [cm]','depth',10.,min_value=.1,max_value=130.,step=.1)
    surface=number('표층 시나리오 두께 [cm]','surface',1.,min_value=.1,max_value=5.,step=.1)
    average=number('굴 깊이 참고 시나리오 1 [cm] (출처 확인 필요)','average',14.4,min_value=.1,max_value=130.,step=.1)
    maximum=number('굴 깊이 참고 시나리오 2 [cm] (출처 확인 필요)','maximum',37.6,min_value=.1,max_value=130.,step=.1)
    st.caption('14.4·37.6 cm의 대상종·원문·대표값 산정 방식은 확인 필요. 평균 생활 깊이나 실제 오염 도달 깊이로 확정하지 않습니다.')
    try:
        model=build_model(Design(**kw),names,days,halves,etas,burial,density,particle,saturation,depth,surface,average,maximum)
    except (ValueError,OverflowError,ZeroDivisionError) as exc:
        st.error(str(exc))
        with right: st.info('유효한 입력을 지정하면 계산 과정이 표시됩니다.')
        st.stop()
    p=model['physical']; data=report(model)
    st.subheader('물리 설계 결과')
    for label,value,unit in [('매트 평면면적',p['area'],'m²'),('전체 소재 표면적',p['surface'],'m²'),
                             ('매몰부 추정 표면적 (공극수 접촉 가능 영역)',p['buried'],'m²'),('총질량',p['mass'],'kg')]:
        st.metric(label,f'{value:,.6f} {unit}')
    if p['length'] is not None: st.metric('전체 필라멘트 길이',f"{p['length']:,.6f} m")
    st.caption(f"보조: 비매몰 면적 {p['unburied']:.6f} m². 매몰부는 실제 수분 접촉 면적의 실측값이 아닙니다.")
    physical_row={'진행 직각 틈 [mm]':p['cross'],'진행 방향 틈 [mm]':p['long'],
                  '기본 두께 [mm]':p['t_base']*1000,'리브 두께 [mm]':p['t_rib']*1000,
                  '기본 두께 롤 지름 [cm]':p['roll_base']*100,'리브 두께 롤 지름 [cm]':p['roll_rib']*100,
                  '회수율 가정 원료 소요량 [kg]':p['waste']}
    st.dataframe([physical_row],hide_index=True)
    if structure==ROTATED: st.caption(f"평행 원사 사이 수직 틈: {p['normal_gap']:g} mm. 진행방향 개구 치수와는 다릅니다.")
    st.markdown(design_preview(p),unsafe_allow_html=True)
    st.caption('2D 개념도: 일부 중심선만 표시합니다. 짚신형은 파랑 날줄·회색 일반 씨줄·주황 리브이며 실제 굴곡이나 원사 직경을 축척 재현하지 않습니다. R2는 외곽만 표시합니다.')
    st.subheader('R1·C0 및 시료 설계 비교')
    comparisons=design_comparison(length,width,kw['rho'],kw['recovery'],kw['core'])
    comparisons['현재 입력']=p
    st.dataframe([{'설계':name,'질량 [kg]':x['mass'],'표면적 [m²]':x['surface'],
                   '직각 틈 [mm]':x['cross'],'진행 틈 [mm]':x['long'],'기본 두께 [mm]':x['t_base']*1000,
                   '리브 두께 [mm]':x['t_rib']*1000,'롤 지름(리브) [cm]':x['roll_rib']*100,'원료 [kg]':x['waste']}
                  for name,x in comparisons.items()],hide_index=True)
    st.caption('같은 L·W·밀도·회수율·심지 외경에서 표준 프리셋을 비교합니다. 10 mm(진행 직각), 6.5 mm(진행 방향)는 팀 내부 목표이며 법적 기준이 아닙니다. ABA 13 mm는 구 통과 기준으로 단순 틈 계산만으로 적합성을 판단하지 않습니다.')
    if not model['chemicals']:
        st.info('R2 재질이 확인되지 않아 PA6 화학 모델을 적용하지 않았습니다. PA6 확인 후 계산할 수 있습니다.')
    else:
        st.subheader('누적 용출·잔존량 및 농도')
        st.write(PW_NOTE)
        if saturation==0: st.warning('계산 불가: 공극수 없음. mg/L·최고·평균·PNEC 비율을 산출하지 않습니다.')
        elif saturation<.05: st.warning('수분이 매우 적은 가정입니다. 용해도 제한 없이 전량을 나누므로 환산농도가 과도하게 커질 수 있습니다.')
        st.caption('포화도 25·50·100%는 실측 이전의 대안 시나리오입니다. 100%가 건조 조상대의 일반 조건이라는 의미가 아닙니다.')
        for c in model['chemicals']:
            x=c['selected']
            st.metric(c['name']+' · 선택일 '+PW_LABEL,'계산 불가: 공극수 없음' if x['selected'] is None else f"{x['selected']:,.6f}")
            if x['selected'] is not None:
                st.caption(f"기간 최고 {x['peak']:,.6f} mg/L ({x['peak_day']}일째) · 일별 산술평균 {x['average']:,.6f} mg/L")
        st.dataframe(data['summary'],hide_index=True,column_order=['물질',PW_LABEL,'최고 일별 환산농도 [mg/L]',
            '최고 발생일 [day]','일별 산술평균 환산농도 [mg/L]','총 누적 용출량 [mg]',
            '매몰부 배분 누적 유입량 [mg]','공극수 구획 잔존량 [mg]','공극수 부피 [L]',SAND,
            '전체 환경 잔존량 [mg]','누적 용출률 [%]','소재 면적당 용출량 [mg/m²-PA6]','평면면적당 용출량 [mg/m²]'])
        st.caption('mg/kg dry sand는 V4와 동일하게 전체 환경 잔존량을 모래 질량으로 나눈 독립 부하량입니다. 공극수로 배분된 질량을 쓰는 mg/L와 합산하거나 같은 노출지표로 취급하지 않습니다.')
        st.subheader('깊이별 완전혼합 시나리오')
        st.dataframe(data['layers'],hide_index=True,column_order=['물질','시나리오',PW_LABEL,
            '굴 깊이 기준 잠재적 공극수 접촉농도 [mg/L]','공극수 부피 [L]',SAND,'건조 모래 질량 [kg]',
            '모래 부피 [m³]','공극 부피 [m³]','혼합층 두께 [cm]','상태'])
        st.write('굴 깊이 기준 잠재적 공극수 접촉농도')
        st.caption(BURROW_NOTE)
        st.subheader('25·50·100% 포화도 및 반감기 비교')
        st.dataframe(data['comparison'],hide_index=True,column_order=['물질','시나리오','포화도',PW_LABEL,
            '최고 일별 환산농도 [mg/L]','최고 발생일 [day]','일별 산술평균 환산농도 [mg/L]',
            '공극수 부피 [L]','반감기 [day]','반감기 구분'])
        st.caption('같은 구조·물질·깊이·배분율에 대한 독립 대안입니다. 선택일·1일부터 선택일까지 최고(최초 발생일)·일별 산술평균을 비교합니다. 산술평균은 연속시간 시간가중 노출량이나 체내흡수량이 아닙니다.')
        st.subheader('카프로락탐 OECD 수환경 PNEC 참고 비교')
        cap=next((c for c in model['chemicals'] if c['name']=='Caprolactam'),None)
        if cap:
            st.dataframe([{'지표':label,'환산농도 [mg/L]':cap['selected'][key],'PNEC [mg/L]':.13,'참고 비교 비율':cap['ratios'][key]}
                          for key,label in [('selected','선택일'),('peak','기간 최고'),('average','기간 산술평균')]],hide_index=True)
        else: st.info('카프로락탐을 선택하면 참고 비교를 표시합니다. 올리고머에는 적용하지 않습니다.')
        st.caption(PNEC_NOTE)
        explain('oecd')
        chart(data['rates'],'1-92일 누적 용출률 (65일 이후 외삽)','접촉일 [day]','누적 용출률 [%]')
        chart(data['mass_time'],'누적 용출량·환경 잔존량','접촉일 [day]','물질량 [mg]')
        chart(data['pw_time'],'일별 공극수 환산농도 (65일 이후 외삽)','접촉일 [day]',PW_LABEL)
        log=st.checkbox('깊이별 농도 그래프 y축 로그 표시',key='log')
        chart(data['sand_curve'],'가정한 혼합층 두께에 따른 모래 총부하량','표면부터 혼합층 두께 [cm]',SAND,log)
        chart(data['pw_curve'],'가정한 혼합층 두께에 따른 공극수 환산농도','표면부터 혼합층 두께 [cm]',PW_LABEL,log)
        st.caption('같은 물질량을 더 두꺼운 층에 나누어 평균값이 낮아지는 독립 시나리오입니다. 실제로 깊이에 따라 이 곡선의 농도분포가 형성된다는 뜻이 아닙니다.')
        st.subheader('물질별 모래층 평균 부하량 비교')
        st.vega_lite_chart(spec={'data':{'values':data['bars']},'mark':'bar','encoding':{
            'x':{'field':'chemical','type':'nominal','title':'물질'},'xOffset':{'field':'layer'},
            'y':{'field':'value','type':'quantitative','title':SAND},'color':{'field':'layer'},
            'tooltip':[{'field':'chemical'},{'field':'layer'},{'field':'value','format':'.6g'}]}},width='stretch')
        st.download_button('조건·깊이·노출 비교 CSV 다운로드',export_csv(data['export']),file_name='pa6_v5_scenarios.csv',mime='text/csv')
    with st.expander('모델 경계·가정·출처 확인 상태'):
        st.write(LIMITS)
        for key in SOURCES: explain(key)
with right:
    show_panel(model)
