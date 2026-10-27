from v4.mesh_engine import segments

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


