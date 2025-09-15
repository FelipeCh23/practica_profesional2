# drift_layout.py
# Colocadores de perforaciones sobre la geometría de la galería

from math import cos, sin, pi
import math

# ---------- helpers geométricos básicos ----------

def _pt(x, y, note="", is_void=False):
    return {"x": x, "y": y, "is_void": bool(is_void), "note": note}

def _bbox(poly):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return min(xs), max(xs), min(ys), max(ys)

def _interp(a, b, t):
    return (a[0] + t*(b[0]-a[0]), a[1] + t*(b[1]-a[1]))

def _segments_mask_by_coord(poly, which="base", eps=0.02):
    """
    Devuelve índices de segmentos colineados con:
      - "base"     → y ≈ ymin
      - "techo"    → y ≈ ymax
      - "lado_izq" → x ≈ xmin
      - "lado_der" → x ≈ xmax
    eps es tolerancia relativa al alto/ancho.
    """
    xmin,xmax,ymin,ymax = _bbox(poly)
    dx = max(xmax - xmin, 1e-6)
    dy = max(ymax - ymin, 1e-6)

    idxs = []
    for i in range(len(poly)-1):
        x1,y1 = poly[i]; x2,y2 = poly[i+1]
        if which == "base":
            if abs(y1 - ymin) <= eps*dy and abs(y2 - ymin) <= eps*dy:
                idxs.append(i)
        elif which == "techo":
            if abs(y1 - ymax) <= eps*dy and abs(y2 - ymax) <= eps*dy:
                idxs.append(i)
        elif which == "lado_izq":
            if abs(x1 - xmin) <= eps*dx and abs(x2 - xmin) <= eps*dx:
                idxs.append(i)
        elif which == "lado_der":
            if abs(x1 - xmax) <= eps*dx and abs(x2 - xmax) <= eps*dx:
                idxs.append(i)
    return idxs

def _sample_on_segment_equidistant(a, b, n):
    """n puntos sin tocar los vértices del segmento."""
    if n <= 0:
        return []
    return [_interp(a,b,(i+1)/(n+1)) for i in range(n)]

# ---------- helpers para arco superior (corona) ----------

def _interpolate_cross(p1, p2, y_cut):
    """Intersección lineal del segmento p1->p2 con la horizontal y=y_cut."""
    (x1,y1), (x2,y2) = p1, p2
    if y2 == y1:
        return (x1, y_cut)
    t = (y_cut - y1) / (y2 - y1)
    return (x1 + t*(x2-x1), y_cut)

def _sample_on_open_poly(poly, n):
    """Equi-espaciado sobre polilínea *abierta*."""
    import bisect
    if n <= 0 or len(poly) < 2:
        return []
    # acumuladas
    d = [0.0]
    for i in range(len(poly)-1):
        x1,y1=poly[i]; x2,y2=poly[i+1]
        d.append(d[-1] + math.hypot(x2-x1,y2-y1))
    L = d[-1] if d[-1] > 0 else 1.0

    def point_at(s):
        if s <= 0: return poly[0]
        if s >= L: return poly[-1]
        i = max(0, min(len(poly)-2, bisect.bisect_right(d, s)-1))
        ds = s - d[i]
        x1,y1=poly[i]; x2,y2=poly[i+1]
        seg = d[i+1]-d[i]
        t = 0 if seg==0 else ds/seg
        return (x1 + t*(x2-x1), y1 + t*(y2-y1))

    if n == 1:
        return [point_at(L/2)]
    step = L/(n-1)
    return [point_at(k*step) for k in range(n)]

def _find_wall_tops(poly):
    """
    Intenta encontrar los *tops* de paredes verticales (izq/der).
    Devuelve (p_top_izq, p_top_der) o (None, None) si no hay paredes explícitas.
    """
    idxs_L = _segments_mask_by_coord(poly, "lado_izq")
    idxs_R = _segments_mask_by_coord(poly, "lado_der")
    pL = pR = None

    def top_from_segments(idxs):
        if not idxs:
            return None
        # toma el endpoint con mayor y entre todos esos segmentos
        best = None
        best_y = -1e18
        for i in idxs:
            for p in (poly[i], poly[i+1]):
                if p[1] > best_y:
                    best = p
                    best_y = p[1]
        return best

    pL = top_from_segments(idxs_L)
    pR = top_from_segments(idxs_R)
    return pL, pR

def _slice_poly_between_points(poly, pA, pB):
    """
    Devuelve una sub-polilínea (abierta) del contorno que va de pA a pB
    siguiendo el orden del polígono (sentido de la lista).
    Requiere que pA y pB existan como vértices exactos.
    """
    try:
        iA = poly.index(pA)
        iB = poly.index(pB)
    except ValueError:
        return []

    if iA <= iB:
        sub = poly[iA:iB+1]
    else:
        # wrap-around
        sub = poly[iA:] + poly[:iB+1]
    # asegurar abierta (sin duplicar cierre)
    if len(sub) >= 2 and sub[0] == sub[-1]:
        sub = sub[:-1]
    return sub

# ---------- Colocadores en contorno ----------

def place_zapateras(tunnel_poly, n, note="zapatera"):
    """
    Equidistantes sobre la BASE (segmentos con y≈ymin).
    Soporta bases compuestas por varios segmentos.
    """
    idxs = _segments_mask_by_coord(tunnel_poly, "base")
    if not idxs or n <= 0:
        return []
    segs  = [(i, tunnel_poly[i], tunnel_poly[i+1]) for i in idxs]
    lens  = [math.hypot(b[0]-a[0], b[1]-a[1]) for _,a,b in segs]
    Ltot  = sum(lens) if sum(lens) > 0 else 1.0
    targets = [ (j+0.5)/n * Ltot for j in range(n) ]

    pts=[]; acc=0.0; k=0
    for ln, (i,a,b) in zip(lens, segs):
        while k < n and targets[k] <= acc + ln:
            t = (targets[k] - acc)/ln if ln>0 else 0.5
            pts.append(_interp(a,b,t))
            k += 1
        acc += ln
    return [_pt(x,y, note=note) for (x,y) in pts]

def place_corona(tunnel_poly, n, note="corona"):
    """
    Equidistantes a lo largo del TECHO *solamente entre los vértices donde las paredes
    se unen con el techo* (no se pasa más allá).
    Estrategia:
      A) Si hay paredes verticales → usar sus *tops* exactos como extremos.
      B) Si no hay paredes verticales (p.ej. Bezier) → limitar por umbral de altura:
         toma puntos por encima de y_cut (≈ 2/3 de altura), el más a la izquierda y el más a la derecha,
         y usa ese tramo para muestrear.
    """
    if n <= 0:
        return []

    # A) Intento con paredes verticales
    pL, pR = _find_wall_tops(tunnel_poly)
    if pL and pR and pL != pR:
        arc = _slice_poly_between_points(tunnel_poly, pL, pR)
        if len(arc) >= 2:
            samples = _sample_on_open_poly(arc, n)
            return [_pt(x,y, note=note) for (x,y) in samples]

    # B) Fallback robusto por umbral (para curvas sin paredes explícitas)
    xmin,xmax,ymin,ymax = _bbox(tunnel_poly)
    y_cut = ymin + 0.66*(ymax - ymin)

    # puntos por encima del umbral
    above = [(i,p) for i,p in enumerate(tunnel_poly) if p[1] >= y_cut]
    if len(above) < 2:
        # si el umbral fue muy alto, baja a 0.5
        y_cut = ymin + 0.5*(ymax - ymin)
        above = [(i,p) for i,p in enumerate(tunnel_poly) if p[1] >= y_cut]
        if len(above) < 2:
            # último recurso: usar “techo” horizontal si existe (rectangular)
            idxs = _segments_mask_by_coord(tunnel_poly, "techo")
            if not idxs:
                return []
            segs  = [(i, tunnel_poly[i], tunnel_poly[i+1]) for i in idxs]
            lens  = [math.hypot(b[0]-a[0], b[1]-a[1]) for _,a,b in segs]
            Ltot  = sum(lens) if sum(lens) > 0 else 1.0
            targets = [ (j)/(n-1) * Ltot for j in range(n) ] if n>1 else [0.5*Ltot]
            pts=[]; acc=0.0; k=0
            for ln, (i,a,b) in zip(lens, segs):
                while k < n and targets[k] <= acc + ln:
                    t = (targets[k] - acc)/ln if ln>0 else 0.5
                    pts.append(_interp(a,b,t))
                    k += 1
                acc += ln
            return [_pt(x,y, note=note) for (x,y) in pts]

    # elegir extremos por x dentro de la “zona alta”
    left_idx, left_p  = min(above, key=lambda t: t[1][0])
    right_idx, right_p= max(above, key=lambda t: t[1][0])

    # construir sub-polilínea en orden del contorno
    if left_idx <= right_idx:
        arc = tunnel_poly[left_idx:right_idx+1]
    else:
        arc = tunnel_poly[left_idx:] + tunnel_poly[:right_idx+1]

    # limpiar posibles cierres
    if len(arc) >= 2 and arc[0] == arc[-1]:
        arc = arc[:-1]

    samples = _sample_on_open_poly(arc, n)
    return [_pt(x,y, note=note) for (x,y) in samples]

def place_cajas(tunnel_poly, n_per_side, note="caja"):
    """
    Equidistantes en lados IZQ y DER, sin tocar vértices.
    Funciona para paredes verticales (rectangular, D, horseshoe).
    """
    if n_per_side <= 0:
        return []
    pts=[]
    for side in ("lado_izq","lado_der"):
        idxs = _segments_mask_by_coord(tunnel_poly, side)
        for i in idxs:
            a = tunnel_poly[i]; b = tunnel_poly[i+1]
            pts += [_pt(x,y, note=note) for (x,y) in _sample_on_segment_equidistant(a,b, n_per_side)]
    return pts

# ---------- Familias interiores (rejilla) ----------

def _inside_convex(poly, x, y):
    """Test simple para polígonos convexos (o suavemente curvos)."""
    ok = None
    for i in range(len(poly)-1):
        x1,y1 = poly[i]; x2,y2 = poly[i+1]
        vx,vy = x2-x1, y2-y1
        wx,wy = x-x1,  y-y1
        cross = vx*wy - vy*wx
        s = 1 if cross >= 0 else -1
        if ok is None:
            ok = s
        elif s != ok:
            return False
    return True

def place_aux_grid(tunnel_poly, nx, ny, note="aux"):
    xmin,xmax,ymin,ymax = _bbox(tunnel_poly)
    if nx<=0 or ny<=0:
        return []
    xs = [xmin + (xmax-xmin)*(i+1)/(nx+1) for i in range(nx)]
    ys = [ymin + (ymax-ymin)*(j+1)/(ny+1) for j in range(ny)]
    out=[]
    for y in ys:
        for x in xs:
            if _inside_convex(tunnel_poly, x, y):
                out.append(_pt(x,y, note=note))
    return out

# ---------- Contracueles ----------

def place_contracuele_hex(center, r=0.8, note="contracuele"):
    cx, cy = center
    pts=[]
    for k in range(6):
        th = pi/6 + k*pi/3  # rotado un poco
        x = cx + r*cos(th)
        y = cy + r*sin(th)
        pts.append(_pt(x,y, note=note))
    return pts

def place_contracuele_rect(center, w=1.4, h=1.0, n_per_side=2, note="contracuele"):
    cx, cy = center
    x1, x2 = cx - w/2, cx + w/2
    y1, y2 = cy - h/2, cy + h/2
    out=[]
    # base
    out += [_pt(*_interp((x1,y1),(x2,y1),(i+1)/(n_per_side+1)), note=note) for i in range(n_per_side)]
    # techo
    out += [_pt(*_interp((x1,y2),(x2,y2),(i+1)/(n_per_side+1)), note=note) for i in range(n_per_side)]
    # izq
    out += [_pt(*_interp((x1,y1),(x1,y2),(i+1)/(n_per_side+1)), note=note) for i in range(n_per_side)]
    # der
    out += [_pt(*_interp((x2,y1),(x2,y2),(i+1)/(n_per_side+1)), note=note) for i in range(n_per_side)]
    return out