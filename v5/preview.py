from v5.mesh_engine import segments
import math

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


def design_preview(p):
    from v5.engine import STRAW, MEASURED
    d=p['design']
    if d.structure not in (STRAW,MEASURED): return preview_svg(p['mesh'],d.structure)
    scale=640/max(d.length,d.width); w=d.length*scale; h=d.width*scale
    lines=[]
    if d.structure==STRAW:
        for i in range(0,p['nw'],max(1,math.ceil(p['nw']/80))):
            y=min(h,i*d.spacing/1000*scale)
            lines.append(f'<line x1="0" y1="{y}" x2="{w}" y2="{y}" stroke="#0891b2"/>')
        picks=set(range(0,p['nall'],max(1,math.ceil(p['nall']/180))))|{0,min(1,p['nall']-1),min(d.rib_period-1,p['nall']-1)}
        for j in sorted(picks):
            x=(j+.5)/p['nall']*w; rib=(j+1)%d.rib_period==0
            color='#d97706' if rib else '#64748b'; thickness=2.5 if rib else 1
            lines.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{h}" stroke="{color}" stroke-width="{thickness}"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-8 -8 {w+16} {h+16}" width="100%" role="img" aria-label="직조 구조 개념도">'
            f'<rect width="{w}" height="{h}" fill="#f1f5f9" stroke="#475569"/>'+''.join(lines)+'</svg>')


