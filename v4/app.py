"""Independent V4 entrypoint: streamlit run v4/app.py."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import streamlit as st
from v4.mesh_engine import MeshInput, STRUCTURES
from v4.model import CHEMICALS, HALF_LIVES, build_model
from v4.preview import preview_svg
from v4.panel import show_panel
from v4.sand import csv_bytes, DEPTH, CONCENTRATION, RANGE
from v4.sources import LIMITS, HALF_NOTE, HYPOTHETICAL, BRIDSON, FORTMANN, KUBO


def line_chart(rows,x,y,x_title,y_title,log=False):
    st.vega_lite_chart(spec={
        'data':{'values':rows},'mark':{'type':'line','point':True},
        'encoding':{
            'x':{'field':x,'type':'quantitative','title':x_title},
            'y':{'field':y,'type':'quantitative','title':y_title,'scale':{'type':'log' if log else 'linear'}},
            'color':{'field':'series','type':'nominal','title':'물질 / 계산 구분'},
            'tooltip':[{'field':'series','type':'nominal'},{'field':x,'type':'quantitative'},
                       {'field':y,'type':'quantitative','format':'.6g'},{'field':'note','type':'nominal','title':'설명'}],
        }},width='stretch')


st.set_page_config(page_title='PA6 Mesh Calculator V4',layout='wide')
st.markdown('''<style>
[data-testid="stLatex"] {overflow-x:auto; max-width:100%;}
[data-testid="stLatex"] .katex-display {overflow-x:auto; overflow-y:hidden; padding: .4rem 0;}
</style>''', unsafe_allow_html=True)
st.title('PA6 Mesh Calculator V4')
st.caption('30°C · 5종 물질 · 누적 용출 / 환경 잔존량 구분 · 참고 시나리오')
left,right=st.columns([1.1,.9],gap='large')
with left:
    st.header('PA6 계산기')
    structure=st.selectbox('직조 구조',STRUCTURES,key='structure')
    length=st.number_input('이동로 길이 L (m)',value=10.0,format='%.4f',key='length')
    width=st.number_input('이동로 너비 W (m)',value=1.0,format='%.4f',key='width')
    diameter=st.number_input('필라멘트 직경 d (mm)',value=2.0,format='%.4f',key='diameter')
    spacing=st.number_input('필라멘트 중심 간격 s (mm)',value=20.0,format='%.4f',key='spacing',help='회전형은 인접 평행선 사이 수직 거리')
    names=st.multiselect('화학물질 선택 및 비교',list(CHEMICALS),default=['Caprolactam'],key='chemicals')
    days=st.slider('접촉 기간 (day)',1,64,7,key='days')
    halves={}
    for name in names:
        oligomer=CHEMICALS[name].semiquantitative
        labels=['분해 미반영', *[(('가상 반감기 ' if oligomer else '참고 반감기 ')+f'{h:g}일') for h in HALF_LIVES[1:]]]
        label=st.selectbox(f'{name} — 환경 분해 반감기',labels,index=0 if oligomer else 2,key='half_'+name)
        halves[name]=HALF_LIVES[labels.index(label)]
        if oligomer:
            st.caption('원 연구의 올리고머 용출 결과는 반정량값입니다.')
            if halves[name] is not None: st.warning(HYPOTHETICAL)
        else: st.caption(HALF_NOTE)
    st.subheader('모래 혼합층 설정')
    density=st.number_input('건조 모래 용적밀도 ρb [kg/m³]',value=1500.0,step=10.0,key='density',
        help='입자 자체의 밀도가 아니라 공극을 포함한 모래층의 건조 질량/전체 부피. 1500 kg/m³는 예시 가정값이며 방아머리 실측값이 아닙니다.')
    depth=st.number_input('선택 혼합 깊이 h [cm]',min_value=.1,max_value=130.0,value=10.0,step=.1,key='depth')
    surface=st.number_input('표층 두께 hs [cm]',min_value=.1,max_value=5.0,value=1.0,step=.1,key='surface')
    average=st.number_input('참고 평균 굴 깊이 [cm]',min_value=.1,max_value=130.0,value=14.4,step=.1,key='average')
    maximum=st.number_input('참고 최대 굴 깊이 [cm]',min_value=.1,max_value=130.0,value=37.6,step=.1,key='maximum')
    st.caption('14.4·37.6 cm는 사용자 제공 굴 깊이 참고값입니다. 평균/최대 구분을 포함한 원문 근거는 저장소에서 확인하지 못했습니다. 실제 생활 깊이·오염 도달 깊이로 해석하지 않습니다.')
    try:
        model=build_model(MeshInput(length,width,diameter,spacing),structure,names,days,halves,density,depth,surface,average,maximum)
    except (ValueError,OverflowError) as exc:
        st.error(str(exc))
        with right: st.info('유효한 입력을 지정하면 현재 조건의 수식과 결과가 표시됩니다.')
        st.stop()
    g=model['geometry']
    st.subheader('표면적 및 PA6 질량')
    for label,value,unit in [('이동로 평면면적',g.planar_area_m2,'m²'),('전체 필라멘트 길이',g.filament_length_m,'m'),
                             ('매몰 전 기하학적 표면적',g.total_surface_m2,'m²'),('50% 매몰 후 비매몰 표면적',g.exposed_surface_m2,'m²'),
                             ('PA6 전체 질량',model['mass_kg'],'kg')]:
        st.metric(label,f'{value:,.6f} {unit}')
    st.markdown(preview_svg(model['data'],structure),unsafe_allow_html=True)
    st.caption('가로 L·세로 W, 원점은 좌측 하단. 조밀한 격자는 일부 중심선만 표시하며 계산에는 전체 포함. 선 굵기는 실제 직경과 무관합니다.')
    st.subheader('물질별 30°C 용출 및 잔존량')
    summary=[]
    csv_rows=[]
    time_rows=[]; rate_rows=[]; depth_rows=[]; compare_rows=[]
    for item in model['chemicals']:
        name=item['chemical'].name; cur=item['current']
        summary.append({'물질':name,'정량 구분':'반정량' if item['chemical'].semiquantitative else '카프로락탐',
            '누적 용출률 [%]':cur['rate_percent'],'누적 용출량 [mg]':cur['cumulative_mg'],
            '환경 잔존량 [mg]':cur['remaining_mg'],'소재 표면적당 누적 용출량 [mg/m²-PA6]':item['q_pa6'],
            '평면면적당 누적 용출량 [mg/m²]':item['q_plan_cumulative'],
            '평면면적당 잔존량 [mg/m²]':item['layers']['selected'].q_plan_mg_m2,
            f'표층 0~{surface:g} cm 평균 [mg/kg]':item['layers']['surface'].concentration_mg_kg,
            f'선택 0~{depth:g} cm 평균 [mg/kg]':item['layers']['selected'].concentration_mg_kg,
            f'참고 평균 굴 0~{average:g} cm 평균 [mg/kg]':item['layers']['average'].concentration_mg_kg,
            f'참고 최대 굴 0~{maximum:g} cm 평균 [mg/kg]':item['layers']['maximum'].concentration_mg_kg})
        for row in item['table']:
            csv_rows.append({'물질':name,'정량 구분':'반정량' if item['chemical'].semiquantitative else '카프로락탐',
                '반감기 [day]':f"{item['half_life']:g}" if item['half_life'] else '분해 미반영',
                '반감기 구분':'가상 민감도 분석' if item['chemical'].semiquantitative and item['half_life'] else '참고 시나리오',
                '누적 용출량 [mg]':cur['cumulative_mg'],'환경 잔존량 [mg]':cur['remaining_mg'],**row})
        for row in item['history']:
            rate_rows.append(dict(day=row['day'],value=row['rate_percent'],series=name,note='PA6 질량 대비 누적 용출률'))
            for key,label in [('cumulative_mg','누적 용출'),('remaining_mg','환경 잔존')]:
                time_rows.append(dict(day=row['day'],value=row[key],series=name+' · '+label,note='날짜 말 투입 근사'))
        for row in item['curve']:
            depth_rows.append(dict(depth=row[DEPTH],value=row[CONCENTRATION],series=name,note=f'0~{row[DEPTH]:g} cm층 평균'))
        for key,label,h in [('surface','표층',surface),('selected','선택',depth),('average','참고 평균 굴',average),('maximum','참고 최대 굴',maximum)]:
            compare_rows.append(dict(chemical=name,layer=f'{label} 0~{h:g} cm',value=item['layers'][key].concentration_mg_kg))
    st.dataframe(summary,hide_index=True)
    st.caption('소재 표면적당 용출량은 M/A_total, 평면면적당 용출량은 M/A입니다. 모래 농도는 R/(ρb·A·h)로 계산합니다.')
    st.subheader('1~64일 누적 용출률')
    line_chart(rate_rows,'day','value','접촉 기간 [day]','누적 용출률 [%]')
    st.subheader('시간별 누적 용출량·환경 잔존량')
    line_chart(time_rows,'day','value','접촉 기간 [day]','물질량 [mg]')
    st.subheader('모래 혼합층 평균농도 — 독립 대안 시나리오')
    st.info('분해 후 잔존량 전량이 매트 아래 해당 모래층 전체에 균일하게 배분된다는 가정입니다. 특정 깊이 지점의 농도나 생물 체내농도가 아닙니다.')
    st.dataframe(csv_rows,hide_index=True)
    st.subheader('가정한 혼합층 두께에 따른 평균농도')
    log=st.checkbox('농도 y축 로그 표시',value=False,key='log')
    if log and any(r['value']<=0 for r in depth_rows):
        st.caption('0 농도는 로그축에 표시할 수 없어 선형축을 사용합니다.'); log=False
    line_chart(depth_rows,'depth','value','표면부터의 혼합층 두께 [cm]','혼합층 평균농도 [mg/kg dry sand]',log)
    st.caption('같은 잔존량을 더 두꺼운 모래층에 균일 배분할수록 평균농도가 낮아집니다. 실제 깊이별 농도가 이 곡선을 따라 감소한다는 뜻은 아닙니다.')
    st.subheader('물질별 혼합층 농도 비교')
    st.vega_lite_chart(spec={'data':{'values':compare_rows},'mark':'bar','encoding':{
        'x':{'field':'chemical','type':'nominal','title':'물질'},'xOffset':{'field':'layer'},
        'y':{'field':'value','type':'quantitative','title':'평균농도 [mg/kg dry sand]'},
        'color':{'field':'layer','title':'독립 혼합층 시나리오'},
        'tooltip':[{'field':'chemical'},{'field':'layer'},{'field':'value','format':'.6g'}]}},width='stretch')
    st.download_button('조건 및 깊이 비교표 CSV 다운로드',csv_bytes(csv_rows,{
        '접촉 기간 [day]':days,'온도 [°C]':30,'매트 길이 [m]':length,'매트 너비 [m]':width,
        '매트 평면면적 [m²]':g.planar_area_m2,'모래 용적밀도 [kg/m³]':density,
        '직조 구조':structure,'직경 [mm]':diameter,'간격 [mm]':spacing,
        '선택 혼합 깊이 [cm]':depth,'표층 두께 [cm]':surface,'참고 평균 굴 깊이 [cm]':average,'참고 최대 굴 깊이 [cm]':maximum}),
        file_name='pa6_v4_scenarios.csv',mime='text/csv')
    with st.expander('모델 가정·불확실성 및 출처 목록'):
        st.write(LIMITS)
        st.markdown(BRIDSON); st.markdown(FORTMANN); st.markdown(KUBO)
        st.write(HALF_NOTE)
        st.caption('ρ=1130 kg/m³, ρb=1500 kg/m³와 균일 혼합·날짜 말 투입은 프로그램의 가정입니다. 130 cm는 사용자 제공 뿌리 깊이 참고값으로 원문 출처 미확인, 계산 탐색 상한으로만 사용합니다.')
with right:
    show_panel(model)
