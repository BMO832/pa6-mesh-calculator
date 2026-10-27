"""Shared, unrounded rows for UI, charts and CSV."""
import csv
import io
from dataclasses import asdict
from v5.sources import PW_LABEL

DEPTH='혼합층 두께 [cm]'
SAND='전체 잔존량 기준 모래 총부하량 [mg/kg dry sand]'


def stats_row(x):
    return {PW_LABEL:x['selected'],'최고 일별 환산농도 [mg/L]':x['peak'],
            '최고 발생일 [day]':x['peak_day'],'일별 산술평균 환산농도 [mg/L]':x['average']}


def report(m):
    out={k:[] for k in ('summary','layers','comparison','rates','mass_time','pw_time','sand_curve','pw_curve','bars','export')}
    p=m['physical']; d=p['design']
    conditions={**asdict(d),'평가일 [day]':m['days'],'온도 [°C]':30,'평면면적 [m²]':p['area'],
                '전체 소재 표면적 [m²]':p['surface'],'PA6 질량 [kg]':p['mass'],
                '매몰률':m['burial'],'건조 용적밀도 [kg/m³]':m['rho_b'],'입자밀도 [kg/m³]':m['rho_s'],
                '공극률':m['volume']['porosity'],'선택 혼합 깊이 [cm]':m['depth'],
                '표층 깊이 [cm]':m['surface'],'참고 깊이1 [cm]':m['average'],'참고 깊이2 [cm]':m['maximum'],
                '외삽 여부':m['extrapolated'],
                '모델 설명':'매몰부 배분 후 날짜 말 투입·1차 분해·전량 용존·균일 혼합; 모래 총부하 지표는 별도 V4 시나리오'}
    for c in m['chemicals']:
        name=c['name']; r=c['current']; x=c['selected']; chem=c['chemical']
        base={'물질':name,'정량 구분':'반정량' if chem.semiquantitative else '카프로락탐',
              '반감기 [day]':str(c['half']) if c['half'] is not None else '분해 미반영',
              '반감기 구분':'가상 민감도' if chem.semiquantitative and c['half'] else '참고 시나리오',
              'eta':c['eta'],'f_pw':c['allocation'],'Ce [%]':chem.ce,'a':chem.a,'k [day⁻¹]':chem.k,'lambda [day⁻¹]':c['decay'],
              '총 누적 용출량 [mg]':r['cumulative_mg'],'전체 환경 잔존량 [mg]':r['remaining_mg'],
              '매몰부 배분 누적 유입량 [mg]':r['pw_in'],'공극수 구획 잔존량 [mg]':r['pw_remaining']}
        out['summary'].append({**base,'누적 용출률 [%]':r['rate_percent'],'소재 면적당 용출량 [mg/m²-PA6]':c['q_pa6'],
                               '평면면적당 용출량 [mg/m²]':c['q_plan'],'공극수 부피 [L]':x['water'],
                               **stats_row(x),SAND:x['sand'].concentration_mg_kg})
        for layer in c['layers']:
            row={**base,'시나리오':f"표층 {layer['depth']:g} cm까지 완전혼합 시나리오",DEPTH:layer['depth'],
                 '포화도':m['saturation'],'모래 부피 [m³]':layer['sand_volume'],
                 '건조 모래 질량 [kg]':layer['sand'].mass_kg,'공극 부피 [m³]':layer['pore_volume'],
                 '공극수 부피 [L]':layer['water'],**stats_row(layer),SAND:layer['sand'].concentration_mg_kg,
                 '굴 깊이 기준 잠재적 공극수 접촉농도 [mg/L]':layer['selected'],
                 '상태':'계산 불가: 공극수 없음' if layer['water']==0 else '가정 시나리오'}
            out['layers'].append(row); out['export'].append({**conditions,'표 구분':'깊이 비교',**row})
        for x in c['comparison']:
            row={**base,'시나리오':x['scenario'],'포화도':x['saturation'],DEPTH:m['depth'],
                 '공극수 부피 [L]':x['water'],**stats_row(x)}
            if x['scenario']=='분해 미반영':
                row.update({'반감기 [day]':'분해 미반영','반감기 구분':'분해 미반영','lambda [day⁻¹]':0.,
                            '공극수 구획 잔존량 [mg]':c['current']['pw_in'],
                            '전체 환경 잔존량 [mg]':c['current']['cumulative_mg']})
            out['comparison'].append(row); out['export'].append({**conditions,'표 구분':'노출조건 비교',**row})
        for r in c['records']:
            out['rates'].append(dict(x=r['day'],y=r['rate_percent'],series=name,note='65-92일 외삽' if r['day']>64 else '1-64일 실험 범위'))
            for key,label in [('cumulative_mg','전체 누적'),('remaining_mg','전체 잔존'),('pw_in','공극수 배분 누적'),('pw_remaining','공극수 잔존')]:
                out['mass_time'].append(dict(x=r['day'],y=r[key],series=name+' · '+label,note='날짜 말 투입'))
            if c['selected']['water']>0:
                out['pw_time'].append(dict(x=r['day'],y=r['pw_remaining']/c['selected']['water'],series=name,note='전량 용존 환산값'))
        for layer in c['curve']:
            note=f"0-{layer['depth']:g} cm층 평균, 독립 시나리오"
            out['sand_curve'].append(dict(x=layer['depth'],y=layer['sand'].concentration_mg_kg,series=name,note=note))
            if layer['selected'] is not None:
                out['pw_curve'].append(dict(x=layer['depth'],y=layer['selected'],series=name,note=note))
        for h in sorted(set((m['surface'],m['depth'],m['average'],m['maximum']))):
            layer=next(x for x in c['layers'] if x['depth']==h)
            out['bars'].append(dict(chemical=name,layer=f'0-{h:g} cm층',value=layer['sand'].concentration_mg_kg))
    return out


def export_csv(rows):
    if not rows: return b''
    fields=list(dict.fromkeys(key for row in rows for key in row))
    f=io.StringIO(newline=''); writer=csv.DictWriter(f,fieldnames=fields)
    writer.writeheader(); writer.writerows(rows)
    return f.getvalue().encode('utf-8-sig')
