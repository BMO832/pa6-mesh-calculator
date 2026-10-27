"""Physical design and independent sand/porewater scenarios; SI units internally."""
from dataclasses import dataclass, replace
from decimal import Decimal, ROUND_HALF_EVEN
import math
from v5.mesh_engine import MeshInput, calculate, square_counts, SQUARE, ROTATED
from v5.chemistry import CHEMICALS, HALF_LIVES, history, rate
from v5.sand import calculate_sand, REFERENCE_DEPTHS

STRAW = '짚신형 v2'
MEASURED = 'R2 시판 매트 (실측 입력)'
PRESETS = {'C0':(12.,20.,1.), 'A1':(10.,16.,.8), 'A2':(10.,25.,2.),
           'A3':(14.,16.,2.), 'A4':(14.,25.,.8)}
PNEC = .13


def positive(*values):
    if any(not math.isfinite(v) or v <= 0 for v in values):
        raise ValueError('길이·직경·밀도·계수는 유한한 양수여야 합니다.')


def fraction(value):
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError('매몰·이동·포화 비율은 0-100% 범위의 유한한 값이어야 합니다.')


@dataclass(frozen=True)
class Design:
    structure: str = STRAW
    length: float = 10.
    width: float = 1.5
    dw: float = 3.  # mm
    spacing: float = 12.  # mm
    df: float = 1.2  # mm
    n: float = 20.  # picks per 10 cm
    h: float = 1.  # mm
    rib_period: int = 5
    path: float = 1.6
    crimp: float = 1.05
    rho: float = 1130.
    recovery: float = .6
    core: float = .15  # core OUTER diameter, m
    measured_mass: float = 0.
    measured_area: float = 0.
    measured_thickness: float = 0.  # mm
    measured_cross: float = 0.  # mm
    measured_long: float = 0.  # mm
    measured_pa6: bool = False


def physical(d):
    positive(d.length,d.width,d.rho,d.recovery,d.core)
    if d.recovery > 1: raise ValueError('회수율은 0% 초과 100% 이하여야 합니다.')
    p={'design':d,'area':d.length*d.width,'counts':None,'parts':[]}
    if d.structure == MEASURED:
        positive(d.measured_mass,d.measured_area,d.measured_thickness)
        if any(not math.isfinite(x) or x<0 for x in (d.measured_cross,d.measured_long)):
            raise ValueError('실측 틈은 0 이상의 유한한 값이어야 합니다.')
        p.update(mass=d.measured_mass,surface=d.measured_area,length=None,
                 cross=d.measured_cross,long=d.measured_long,
                 t_base=d.measured_thickness/1000,t_rib=d.measured_thickness/1000)
    elif d.structure in (SQUARE,ROTATED):
        mesh=MeshInput(d.length,d.width,d.dw,d.spacing)
        g=calculate(mesh,d.structure)
        p.update(mesh=mesh,length=g.filament_length_m,surface=g.total_surface_m2,
                 mass=d.rho*(math.pi*mesh.diameter_m**2/4)*g.filament_length_m,
                 counts=square_counts(mesh) if d.structure==SQUARE else None,
                 cross=d.spacing-d.dw if d.structure==SQUARE else None,
                 long=d.spacing-d.dw if d.structure==SQUARE else None,
                 normal_gap=d.spacing-d.dw,t_base=2*mesh.diameter_m,t_rib=2*mesh.diameter_m)
        p['parts']=[dict(name='전체 필라멘트',diameter=mesh.diameter_m,length=p['length'])]
    elif d.structure == STRAW:
        positive(d.dw,d.spacing,d.df,d.n,d.path,d.crimp)
        if not math.isfinite(d.h) or d.h<0: raise ValueError('요철 높이는 0 이상이어야 합니다.')
        if not isinstance(d.rib_period,int) or d.rib_period<1: raise ValueError('리브 주기는 1 이상의 정수여야 합니다.')
        if d.path<1 or d.crimp<1: raise ValueError('경로·굴곡계수는 1 이상이어야 합니다.')
        if d.spacing<=d.dw or 100/d.n<=d.df: raise ValueError('날줄 간격과 씨줄 피치는 각 직경보다 커야 합니다.')
        nw=square_counts(MeshInput(d.length,d.width,d.dw,d.spacing))[0]
        # Python round convention: half-to-even, with decimal multiplication to avoid binary ties.
        nall=int((Decimal('10')*Decimal(str(d.n))*Decimal(str(d.length))).quantize(Decimal('1'),rounding=ROUND_HALF_EVEN))
        if nall<1: raise ValueError('입력 길이에서 씨줄이 1회 이상이어야 합니다.')
        nrib=nall//d.rib_period; nregular=nall-nrib
        tw=nw*d.length*d.crimp; tf=nregular*d.width*d.path; tr=nrib*d.width*d.path
        dr=(d.df+d.h)/1000
        parts=[dict(name='날줄',count=nw,diameter=d.dw/1000,length=tw),
               dict(name='일반 씨줄',count=nregular,diameter=d.df/1000,length=tf),
               dict(name='리브 씨줄',count=nrib,diameter=dr,length=tr)]
        p.update(nw=nw,nall=nall,nrib=nrib,nregular=nregular,tw=tw,tf=tf,tr=tr,dr=dr,parts=parts,
                 length=tw+tf+tr,surface=math.pi*sum(x['diameter']*x['length'] for x in parts),
                 mass=d.rho*math.pi/4*sum(x['diameter']**2*x['length'] for x in parts),
                 cross=d.spacing-d.dw,long=100/d.n-d.df,
                 t_base=(d.dw+2*d.df)/1000,t_rib=(d.dw+2*d.df+d.h)/1000)
    else: raise ValueError('지원하지 않는 구조입니다.')
    p.update(roll_base=math.sqrt(d.core**2+4*d.length*p['t_base']/math.pi),
             roll_rib=math.sqrt(d.core**2+4*d.length*p['t_rib']/math.pi),waste=p['mass']/d.recovery)
    positive(*(p[k] for k in ('area','mass','surface','t_base','t_rib','roll_base','roll_rib','waste')))
    return p


def pore_volume(area,depth_cm,rho_b,rho_s,saturation):
    positive(area,depth_cm,rho_b,rho_s); fraction(saturation)
    if rho_b>=rho_s: raise ValueError('건조 용적밀도는 모래 입자밀도보다 작아야 합니다.')
    porosity=1-rho_b/rho_s
    sand_volume=area*(depth_cm/100)
    pore=sand_volume*porosity
    water=pore*saturation*1000
    if not all(math.isfinite(v) for v in (sand_volume,pore,water)) or (saturation>0 and water<=0):
        raise ValueError('공극수 부피가 계산 가능한 범위를 벗어났습니다.')
    return dict(porosity=porosity,sand_volume=sand_volume,pore_volume=pore,water=water)


def concentration_stats(records,water,days,key='pw_remaining'):
    if not math.isfinite(water) or water<0: raise ValueError('공극수량은 유한한 0 이상 값이어야 합니다.')
    rate(CHEMICALS['Caprolactam'],days)
    if water==0: return dict(selected=None,peak=None,peak_day=None,average=None)
    values=[r[key]/water for r in records[:days]]
    if len(values)!=days or any(not math.isfinite(x) or x<0 for x in values):
        raise ValueError('유효한 비음수 일별 농도 이력이 필요합니다.')
    peak=max(values)
    return dict(selected=values[-1],peak=peak,peak_day=values.index(peak)+1,average=math.fsum(values)/days)


def chemical_scenario(name,mass,days,half,burial,eta,area,rho_b,rho_s,saturation,depths):
    fraction(burial); fraction(eta)
    if name not in CHEMICALS: raise ValueError('지원하지 않는 물질입니다.')
    rate(CHEMICALS[name],days)
    decay,records=history(CHEMICALS[name],mass,half)
    allocation=burial*eta; remaining=0.
    for r in records:
        incoming=r['cumulative_mg']*allocation
        increment=r['increment_mg']*allocation
        remaining=incoming if half is None else remaining*math.exp(-decay)+increment
        r.update(pw_in=incoming,pw_increment=increment,pw_remaining=remaining)
        if not 0<=remaining<=incoming*(1+1e-12): raise ValueError('공극수 질량 수지 오류입니다.')
    current=records[days-1]
    layers=[]
    for depth in sorted(set(depths)):
        if not .1<=depth<=130: raise ValueError('혼합 깊이는 0.1-130 cm이어야 합니다.')
        vol=pore_volume(area,depth,rho_b,rho_s,saturation)
        stats=concentration_stats(records,vol['water'],days)
        sand=calculate_sand(current['remaining_mg'],area,rho_b,depth)
        layers.append(dict(depth=depth,**vol,**stats,sand=sand))
    contributions=[dict(day=r['day'],total_increment=r['increment_mg'],pw_increment=r['pw_increment'],
                        age=days-r['day'],remaining=r['pw_increment']*math.exp(-decay*(days-r['day'])))
                   for r in records[:days]]
    return dict(name=name,chemical=CHEMICALS[name],half=half,decay=decay,allocation=allocation,
                eta=eta,records=records,current=current,layers=layers,contributions=contributions)


def build_model(design,names,days,halves,etas,burial,rho_b,rho_s,saturation,depth,surface=1.,average=14.4,maximum=37.6):
    p=physical(design); fraction(burial)
    if not names or any(n not in CHEMICALS for n in names): raise ValueError('물질을 하나 이상 선택해 주세요.')
    if not .1<=surface<=5: raise ValueError('표층 두께는 0.1-5 cm이어야 합니다.')
    depths=(*REFERENCE_DEPTHS,1.,depth,surface,average,maximum)
    if any(not math.isfinite(x) or not .1<=x<=130 for x in depths): raise ValueError('깊이는 0.1-130 cm이어야 합니다.')
    rate(CHEMICALS[names[0]],days)
    volume=pore_volume(p['area'],depth,rho_b,rho_s,saturation)
    p.update(buried=p['surface']*burial,unburied=p['surface']*(1-burial))
    m=dict(physical=p,days=days,burial=burial,rho_b=rho_b,rho_s=rho_s,saturation=saturation,
           depth=depth,surface=surface,average=average,maximum=maximum,volume=volume,chemicals=[],extrapolated=days>64)
    # A commercial comparator must not silently be treated as PA6.
    if design.structure==MEASURED and not design.measured_pa6: return m
    for name in names:
        c=chemical_scenario(name,p['mass'],days,halves[name],burial,etas[name],p['area'],rho_b,rho_s,saturation,depths)
        c['selected']=next(x for x in c['layers'] if x['depth']==depth)
        c['curve']=chemical_scenario(name,p['mass'],days,halves[name],burial,etas[name],p['area'],rho_b,rho_s,saturation,
                                    (*range(1,131),depth,surface,average,maximum))['layers']
        c['q_pa6']=c['current']['cumulative_mg']/p['surface']
        c['q_plan']=c['current']['cumulative_mg']/p['area']
        c['comparison']=[]
        for sat in (.25,.5,1.):
            volume_l=pore_volume(p['area'],depth,rho_b,rho_s,sat)['water']
            for key,label in [('pw_remaining','선택 반감기'),('pw_in','분해 미반영')]:
                stats=concentration_stats(c['records'],volume_l,days,key)
                c['comparison'].append(dict(saturation=sat,scenario=label,water=volume_l,**stats))
        c['ratios']={key:(c['selected'][key]/PNEC if c['selected'][key] is not None else None)
                     for key in ('selected','peak','average')} if name=='Caprolactam' else None
        m['chemicals'].append(c)
    return m


def design_comparison(length,width,rho=1130.,recovery=.6,core=.15):
    base=Design(length=length,width=width,rho=rho,recovery=recovery,core=core)
    return {'R1':physical(replace(base,structure=SQUARE)),
            **{name:physical(replace(base,spacing=s,n=n,h=h)) for name,(s,n,h) in PRESETS.items()}}
