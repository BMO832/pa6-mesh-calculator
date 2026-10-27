"""V5 independent geometric/pore-water layer. Reuses v4 chemistry and legacy geometry."""
from dataclasses import dataclass, replace
from math import pi, floor, sqrt, exp, log, isfinite
from v4.mesh_engine import MeshInput, calculate, SQUARE, ROTATED
from v4.model import CHEMICALS  # V4 coefficient provenance preserved

PNEC=0.13
PRESETS={'C0':(12,20,1.0),'A1':(10,16,.8),'A2':(10,25,2.0),'A3':(14,16,2.0),'A4':(14,25,.8)}
WIDTHS=(1.5,1.525,1.65,1.7)
HALF_LIVES=(None,5.,9.5,14.)

@dataclass(frozen=True)
class Design:
    kind:str='C0'
    length:float=10.
    width:float=1.5
    warp_d:float=3.
    spacing:float=12.
    weft_d:float=1.2
    n:float=20.
    rib_h:float=1.
    rib_period:int=5
    k:float=1.6
    cw:float=1.05
    rho:float=1130.
    recovery:float=.60
    core:float=.15
    # R1/R2 common-diameter reference grid inputs
    reference_d:float=3.
    reference_s:float=12.
    reference_structure:str=SQUARE
    # R2 allows direct measured mass/surface override
    measured_mass:float|None=None
    measured_area:float|None=None


def geometry(d:Design):
    nums=(d.length,d.width,d.warp_d,d.spacing,d.weft_d,d.n,d.rib_period,d.k,d.cw,d.rho,d.recovery,d.core,d.reference_d,d.reference_s)
    if any(not isfinite(x) or x<=0 for x in nums) or not isfinite(d.rib_h) or d.rib_h<0 or d.recovery>1:
        raise ValueError('설계값은 유한한 양수, 요철은 0 이상, 회수율은 0-100%여야 합니다.')
    if d.kind in PRESETS or d.kind=='직접 짚신형':
        if d.spacing<=d.warp_d or 100/d.n<=d.weft_d:
            raise ValueError('씨줄·날줄 간격이 직경보다 커야 합니다.')
        sm=d.spacing/1000; dw=d.warp_d/1000; df=d.weft_d/1000; dh=d.rib_h/1000
        nw=floor(d.width/sm)+1
        na=round(10*d.n*d.length)
        nr=na//d.rib_period; nf=na-nr
        tw=nw*d.length*d.cw; tf=nf*d.width*d.k; tr=nr*d.width*d.k
        dr=df+dh
        mass=d.rho*pi/4*(dw**2*tw+df**2*tf+dr**2*tr)
        area=pi*(dw*tw+df*tf+dr*tr)
        base=dw+2*df; rib=base+dh
        total=tw+tf+tr
        gap_cross=d.spacing-d.warp_d; gap_long=100/d.n-d.weft_d
        details=dict(n_w=nw,n_all=na,n_rib=nr,n_regular=nf,T_w=tw,T_regular=tf,T_rib=tr,d_rib_mm=dr*1000)
    else:
        if d.reference_s<=d.reference_d:
            raise ValueError('기존 격자 간격은 직경보다 커야 합니다.')
        g=calculate(MeshInput(d.length,d.width,d.reference_d,d.reference_s),d.reference_structure)
        total=g.filament_length_m; area=g.total_surface_m2
        mass=d.rho*pi/4*(d.reference_d/1000)**2*total
        gap_cross=gap_long=d.reference_s-d.reference_d
        base=rib=d.reference_d/1000
        details={'T':total,'structure':d.reference_structure}
        if d.kind=='R2':
            if d.measured_mass is not None:
                if d.measured_mass<=0 or not isfinite(d.measured_mass): raise ValueError('실측 질량 오류')
                mass=d.measured_mass
            if d.measured_area is not None:
                if d.measured_area<=0 or not isfinite(d.measured_area): raise ValueError('실측 면적 오류')
                area=d.measured_area
    roll_base=sqrt(d.core**2+4*d.length*base/pi)
    roll_rib=sqrt(d.core**2+4*d.length*rib/pi)
    return dict(mass=mass,area=area,total_length=total,gap_cross=gap_cross,gap_long=gap_long,
                thickness_base=base,thickness_rib=rib,roll_base=roll_base,roll_rib=roll_rib,
                waste=mass/d.recovery,details=details,plan=d.length*d.width)


def porosity(bulk,particle):
    if not all(isfinite(x) and x>0 for x in (bulk,particle)) or bulk>=particle:
        raise ValueError('용적밀도와 입자밀도는 양수이며 용적밀도가 입자밀도보다 작아야 합니다.')
    return 1-bulk/particle


def pore_volume(plan,depth_cm,bulk,particle,saturation):
    if not isfinite(saturation) or not 0<=saturation<=1 or not isfinite(depth_cm) or depth_cm<=0 or plan<=0:
        raise ValueError('포화도는 0-100%, 깊이와 면적은 양수여야 합니다.')
    return plan*(depth_cm/100)*porosity(bulk,particle)*saturation*1000


def exposures(mass_kg,chemical_name,days,buried,eta,half,plan,depth,bulk,particle,saturation):
    """Daily end-of-day mass balance. Unlike V4 this uses 92 days; V4 coefficients unchanged."""
    if chemical_name not in CHEMICALS or not isinstance(days,int) or not 1<=days<=92:
        raise ValueError('화학물질 또는 평가기간 오류')
    if half not in HALF_LIVES or not all(isfinite(v) and 0<=v<=1 for v in (buried,eta)):
        raise ValueError('매몰률·배분율·반감기 오류')
    if not isfinite(mass_kg) or mass_kg<=0: raise ValueError('질량 오류')
    c=CHEMICALS[chemical_name]
    volume=pore_volume(plan,depth,bulk,particle,saturation)
    lam=log(2)/half if half else 0.
    prev=0.; remaining=0.; total_increment=0.; rows=[]
    for day in range(1,days+1):
        r=c.ce*(1-c.a*exp(-c.k*day))
        cumulative=mass_kg*(r/100)*1_000_000
        increment=cumulative-prev
        if increment<-1e-9: raise ArithmeticError('음의 용출량')
        total_increment+=increment
        inflow=increment*buried*eta
        remaining=remaining*exp(-lam)+inflow
        concentration=remaining/volume if volume>0 else None
        rows.append(dict(day=day,rate=r,total_mg=cumulative,increment_mg=increment,
                         allocated_mg=cumulative*buried*eta,remaining_mg=remaining,volume_l=volume,
                         concentration=concentration))
        prev=cumulative
    assert abs(total_increment-rows[-1]['total_mg'])<1e-7
    assert all(q['remaining_mg']>=-1e-8 and q['remaining_mg']<=q['allocated_mg']+1e-8 for q in rows)
    valid=[q['concentration'] for q in rows if q['concentration'] is not None]
    peak=max(valid) if valid else None
    avg=sum(valid)/len(valid) if valid else None
    peak_day=1+next(i for i,q in enumerate(rows) if q['concentration']==peak) if valid else None
    return dict(rows=rows,current=rows[-1],peak=peak,average=avg,peak_day=peak_day,volume_l=volume,
                porosity=porosity(bulk,particle),pnec_ratios={key:(value/PNEC if value is not None else None)
                       for key,value in [('current',rows[-1]['concentration']),('peak',peak),('average',avg)]})


def solid_loading(remaining_mg,plan,depth_cm,bulk):
    """V4 sand concentration is total environmental load in dry sand, independent of pore-water fraction."""
    if depth_cm<=0 or plan<=0 or bulk<=0: raise ValueError('모래 계산 입력 오류')
    return remaining_mg/(plan*depth_cm/100*bulk)
