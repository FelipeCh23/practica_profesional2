from math import cos, sin, radians, sqrt

# --- núcleo geométrico (sin series/delays) ---
def _pt_geom(x, y, *, is_void=False, note=""):
    return {"x": x, "y": y, "is_void": bool(is_void), "note": note}

def _xform(x, y, *, center=(0,0), scale_x=1.0, scale_y=1.0, rot_deg=0.0):
    cx, cy = center
    x, y = x*scale_x, y*scale_y
    if rot_deg:
        a = radians(rot_deg); ca, sa = cos(a), sin(a)
        x, y = x*ca - y*sa, x*sa + y*ca
    return cx + x, cy + y

# SARROIS
def cuele_sarrois_geom(center=(0,0), d=0.15,
                       scale_x=1.0, scale_y=1.0, rot_deg=0.0,
                       offset_rows=None, offset_cols=None, offset_xy=None):
    """
    Geometría: 3×3 con vacío central.
    Offsets:
      - offset_rows: [Δy_fila_sup, Δy_fila_med, Δy_fila_inf]
      - offset_cols: [Δx_izq, Δx_centro, Δx_der]
      - offset_xy: {(f,c): (dx,dy)} con f∈{0..2} (sup..inf), c∈{0..2} (izq..der)
    """
    if offset_rows is None: offset_rows = [0.0, 0.0, 0.0]
    if offset_cols is None: offset_cols = [0.0, 0.0, 0.0]
    if offset_xy   is None: offset_xy   = {}

    xs = [-d, 0.0, +d]
    ys = [+d, 0.0, -d]
    mask = [
        [(False,"sarrios"), (False,"sarrios"), (False,"sarrios")],   # fila sup
        [(False,"sarrios"), (True,"alivio"),  (False,"sarrios")],    # fila med
        [(False,"sarrios"), (False,"sarrios"),(False,"sarrios")],    # fila inf
    ]

    holes=[]
    for f,yb in enumerate(ys):
        for c,xb in enumerate(xs):
            is_void = mask[f][c][0]
            note    = mask[f][c][1]
            dx,dy   = offset_xy.get((f,c),(0.0,0.0))
            x = xb + offset_cols[c] + dx
            y = yb + offset_rows[f] + dy
            X,Y = _xform(x, y, center=center, scale_x=scale_x, scale_y=scale_y, rot_deg=rot_deg)
            holes.append(_pt_geom(X, Y, is_void=is_void, note=note))
    return holes


def cuele_cuatro_secciones_geom(center=(0.0, 0.0), D=0.20, D2=0.20,
                                k2=1.5, k3=1.5, k4=1.5, add_mids_S4=True,
                                scale_x=1.0, scale_y=1.0, rot_deg=0.0):
    """
    Geometría únicamente; aplica regla R1 ≤ 1.7·D2.
    """
    # burdens
    B1 = 1.5*D; B2 = k2*B1; B3 = k3*B2; B4 = k4*B3
    # apotemas acumuladas
    A1 = B1; A2 = B1+B2; A3 = B1+B2+B3; A4 = B1+B2+B3+B4
    # restricción
    R1 = A1*sqrt(2)
    if R1 > 1.7*D2:
        s = (1.7*D2)/R1
        A1*=s; A2*=s; A3*=s; A4*=s; R1 = A1*sqrt(2)

    holes=[]
    # vacío central
    X,Y = _xform(0.0, 0.0, center=center, scale_x=scale_x, scale_y=scale_y, rot_deg=rot_deg)
    holes.append(_pt_geom(X,Y,is_void=True, note="alivio"))

    # S1 ejes @R1
    for (x,y) in [( R1,0),(0,R1),(-R1,0),(0,-R1)]:
        X,Y = _xform(x,y, center=center, scale_x=scale_x, scale_y=scale_y, rot_deg=rot_deg)
        holes.append(_pt_geom(X,Y, note="S1"))
    # S2 diagonales @A2
    for (x,y) in [( A2, A2),( A2,-A2),(-A2,-A2),(-A2, A2)]:
        X,Y = _xform(x,y, center=center, scale_x=scale_x, scale_y=scale_y, rot_deg=rot_deg)
        holes.append(_pt_geom(X,Y, note="S2"))
    # S3 ejes @R3
    R3 = A3*sqrt(2)
    for (x,y) in [( R3,0),(0,R3),(-R3,0),(0,-R3)]:
        X,Y = _xform(x,y, center=center, scale_x=scale_x, scale_y=scale_y, rot_deg=rot_deg)
        holes.append(_pt_geom(X,Y, note="S3"))
    # S4 diagonales (+ medias)
    s4 = [( A4, A4),( A4,-A4),(-A4,-A4),(-A4, A4)]
    if add_mids_S4:
        s4 += [(A4,0),(0,A4),(-A4,0),(0,-A4)]
    for (x,y) in s4:
        X,Y = _xform(x,y, center=center, scale_x=scale_x, scale_y=scale_y, rot_deg=rot_deg)
        holes.append(_pt_geom(X,Y, note="S4"))
    return holes


  
#  SUECO
def cuele_sueco_geom(center=(0.0, 0.0), d=0.12,
                     scale_x=1.0, scale_y=1.0, rot_deg=0.0,
                     offset_rows=None, offset_cols=None, offset_xy=None):
    """
    Patrón (f=0..4 top→bottom; c=0..2 left→center→right):
      f0: [●, V, ●]
      f1: [ , ●,  ]
      f2: [●, V, ●]
      f3: [ , ●,  ]
      f4: [●, V, ●]
    """
    if offset_rows is None: offset_rows = [0.0]*5
    if offset_cols is None: offset_cols = [0.0]*3
    if offset_xy   is None: offset_xy   = {}

    xs = [-d, 0.0, +d]
    ys = [+2*d, +1*d, 0.0, -1*d, -2*d]
    # (is_void, place)
    mask = [
        [(False,"sueco"), (True,"alivio"), (False,"sueco")],
        [(None,""),       (False,"sueco"), (None,"")      ],
        [(False,"sueco"), (True,"alivio"), (False,"sueco")],
        [(None,""),       (False,"sueco"), (None,"")      ],
        [(False,"sueco"), (True,"alivio"), (False,"sueco")],
    ]

    holes=[]
    for f,yb in enumerate(ys):
        for c,xb in enumerate(xs):
            cell = mask[f][c]
            if cell[0] is None:
                continue  # no hay perforación en este slot
            is_void = cell[0]; note = cell[1]
            dx,dy   = offset_xy.get((f,c),(0.0,0.0))
            x = xb + offset_cols[c] + dx
            y = yb + offset_rows[f] + dy
            X,Y = _xform(x, y, center=center, scale_x=scale_x, scale_y=scale_y, rot_deg=rot_deg)
            holes.append(_pt_geom(X, Y, is_void=is_void, note=note))
    return holes




#  COROMANT 
def cuele_coromant_geom(center=(0.0, 0.0),
                        v=0.06, ax=0.16, ay=0.16,
                        skew=0.05, spread=1.4,
                        scale_x=1.0, scale_y=1.0, rot_deg=0.0,
                        offset_xy=None):
    """
    Vacíos pegados: (0, ±v).
    Col IZQ (x≈-ax): y=+ay (3), y=0 (1 más abierto), y=-ay (4).
    Col DER (x≈+ax): y=+ay+skew (5), y=0 (0 más abierto), y=-ay-skew (2).
    """
    if offset_xy is None: offset_xy = {}

    pts = [
        # vacíos
        ((0.0, +v), True,  "alivio"),
        ((0.0, -v), True,  "alivio"),
        # izquierda
        ((-ax,       +ay), False, "coro L"),
        ((-spread*ax, 0.0), False, "coro 1 abierto"),
        ((-ax,       -ay), False, "coro L"),
        # derecha
        ((+ax, +ay+skew),  False, "coro R"),
        ((+spread*ax, 0.0),False, "coro 0 abierto"),
        ((+ax, -ay-skew),  False, "coro R"),
    ]
    holes=[]
    for i,(p,isv,note) in enumerate(pts):
        dx,dy = offset_xy.get(i,(0.0,0.0))
        x,y   = p[0]+dx, p[1]+dy
        X,Y   = _xform(x, y, center=center, scale_x=scale_x, scale_y=scale_y, rot_deg=rot_deg)
        holes.append(_pt_geom(X, Y, is_void=isv, note=note))
    return holes



# CUELE CUÑA 

def cuele_cuna_geom(center=(0.0, 0.0), d=0.20,
                    variante="2x3", sep_cols_factor=2.0,
                    scale_x=1.0, scale_y=1.0, rot_deg=0.0,
                    offset_rows=None, offset_cols=None, offset_xy=None):
    """
    '2x3': 2 columnas × 3 filas (pasos: ≈2d y d).
    'zigzag': 4 columnas × 5 filas en patrón alternante.
    """
    if variante=="2x3":
        if offset_rows is None: offset_rows=[0.0]*3
        if offset_cols is None: offset_cols=[0.0]*2
        if offset_xy   is None: offset_xy  ={}
        dx = sep_cols_factor * d / 2.0
        xs = [-dx, +dx]; ys = [+d, 0.0, -d]
        holes=[]
        for f,yb in enumerate(ys):
            for c,xb in enumerate(xs):
                dxp,dyp = offset_xy.get((f,c),(0.0,0.0))
                x = xb + offset_cols[c] + dxp
                y = yb + offset_rows[f] + dyp
                X,Y = _xform(x,y, center=center, scale_x=scale_x, scale_y=scale_y, rot_deg=rot_deg)
                holes.append(_pt_geom(X,Y, note="cuña 2x3"))
        return holes

    elif variante=="zigzag":
        if offset_rows is None: offset_rows=[0.0]*5
        if offset_cols is None: offset_cols=[0.0]*4
        if offset_xy   is None: offset_xy  ={}
        xs = [-1.5*d, -0.5*d, +0.5*d, +1.5*d]
        ys = [+2*d, +1*d, 0.0, -1*d, -2*d]
        mask = [
            [1,0,0,1],
            [0,1,1,0],
            [1,0,0,1],
            [0,1,1,0],
            [1,0,0,1],
        ]
        holes=[]
        for f,yb in enumerate(ys):
            for c,xb in enumerate(xs):
                if not mask[f][c]: continue
                dxp,dyp = offset_xy.get((f,c),(0.0,0.0))
                x = xb + offset_cols[c] + dxp
                y = yb + offset_rows[f] + dyp
                X,Y = _xform(x,y, center=center, scale_x=scale_x, scale_y=scale_y, rot_deg=rot_deg)
                holes.append(_pt_geom(X,Y, note="cuña zigzag"))
        return holes
    else:
        raise ValueError("variante debe ser '2x3' o 'zigzag'")




# CUELE ABANICO (manual)
def cuele_abanico_geom(center=(0.0, 0.0), d=0.20,
                       dx_factor=0.5, gap12=0.5, gap23=1.0, gap34=1.0,
                       scale_x=1.0, scale_y=1.0, rot_deg=0.0,
                       offset_rows=None, offset_cols=None, offset_xy=None):
    if offset_rows is None: offset_rows=[0.0]*4
    if offset_cols is None: offset_cols=[0.0]*5
    if offset_xy   is None: offset_xy  ={}
    dx = dx_factor * d
    xs = [-2*dx, -dx, 0.0, +dx, +2*dx]
    y1 = 0.0
    y2 = y1 - gap12*d
    y3 = y2 - gap23*d
    y4 = y3 - gap34*d
    rows = [y1,y2,y3,y4]
    layout = {
        0: [1,3],     # F1: col 2,4
        1: [0,2,4],   # F2: col 1,3,5
        2: [0,2,4],   # F3: col 1,3,5
        3: [1,3],     # F4: col 2,4
    }
    holes=[]
    for f,cols in layout.items():
        yb = rows[f] + offset_rows[f]
        for c in cols:
            xb = xs[c] + offset_cols[c]
            dxp,dyp = offset_xy.get((f,c),(0.0,0.0))
            X,Y = _xform(xb+dxp, yb+dyp, center=center, scale_x=scale_x, scale_y=scale_y, rot_deg=rot_deg)
            holes.append(_pt_geom(X,Y, note="abanico"))
    return holes



#Cuele Bethune
def cuele_bethune_geom(center=(0.0, 0.0), d=0.20,
                       dx_factor=1.2,
                       y_levels=(1.6, 1.4, 1.2, 1.0, 0.9),
                       invert_y=True, vy_factor=3.5,
                       scale_x=1.0, scale_y=1.0, rot_deg=0.0,
                       offset_rows=None, offset_cols=None, offset_xy=None):
    if offset_rows is None: offset_rows=[0.0]*5
    if offset_cols is None: offset_cols=[0.0]*7
    if offset_xy   is None: offset_xy  ={}

    dx   = dx_factor * d
    cols = [-3*dx,-2*dx,-dx,0.0,+dx,+2*dx,+3*dx]
    sgn  = -1.0 if invert_y else +1.0
    base = [sgn*vy_factor*m*d for m in y_levels]  # 5 filas
    layout = { 0:[3], 1:[1,5], 2:[3], 3:[0,6], 4:[2,4] }

    holes=[]
    for f, cs in layout.items():
        yb = base[f] + offset_rows[f]
        for c in cs:
            xb = cols[c] + offset_cols[c]
            dxp,dyp = offset_xy.get((f,c),(0.0,0.0))
            X,Y = _xform(xb+dxp, yb+dyp, center=center, scale_x=scale_x, scale_y=scale_y, rot_deg=rot_deg)
            holes.append(_pt_geom(X,Y, note="bethune"))
    return holes

# ========= Helpers comunes de rotulado =========
def _near(a, b, tol=1e-6):
    return abs(a - b) <= tol


# ========= Cuatro secciones =========
def apply_series_cuatro_secciones(holes, A1, A2, A3, A4, add_mids_S4=True, tol=1e-6):
    """
    Asigna:
      S1 -> serie 0 (vértices ~ R1 = A1*sqrt(2) en ejes)
      S2 -> serie 1 (vértices ~ A2 en diagonales)
      S3 -> serie 2 (vértices ~ R3 = A3*sqrt(2) en ejes)
      S4 -> serie 3 (vértices ~ A4 en diagonales (+ medias de lado si aplica))
      Vacío central -> sin serie a menos que quieras marcar 0 también.
    Nota: requiere conocer A1..A4 usados para generar la geometría (o recomputarlos).
    """
    from math import sqrt
    R1 = A1*sqrt(2.0)
    R3 = A3*sqrt(2.0)
    for h in holes:
        x, y = h["x"], h["y"]
        rax = abs(x); ray = abs(y)
        # vacío: no tocar (o setear serie=0 si te gusta que se vea como “0”)
        if h.get("is_void", False):
            continue

        # candidatos S1: sobre ejes a distancia R1
        if (_near(rax, R1, tol) and _near(y, 0.0, tol)) or (_near(ray, R1, tol) and _near(x, 0.0, tol)):
            h["serie"] = 0

        # candidatos S3: sobre ejes a distancia R3
        elif (_near(rax, R3, tol) and _near(y, 0.0, tol)) or (_near(ray, R3, tol) and _near(x, 0.0, tol)):
            h["serie"] = 2

        # candidatos S2: diagonales con |x|==|y|≈A2
        elif _near(abs(abs(x) - abs(y)), 0.0, tol) and _near(abs(x), A2, tol):
            h["serie"] = 1

        # candidatos S4: diagonales ≈A4 o medias de lado (|x|≈A4, y≈0) o (x≈0,|y|≈A4)
        elif _near(abs(abs(x) - abs(y)), 0.0, tol) and _near(abs(x), A4, tol):
            h["serie"] = 3
        elif add_mids_S4 and ((_near(abs(x), A4, tol) and _near(y, 0.0, tol)) or (_near(abs(y), A4, tol) and _near(x, 0.0, tol))):
            h["serie"] = 3

        # delay = serie si se asignó
        if "serie" in h and "delay" not in h:
            h["delay"] = h["serie"]
    return holes


# ========= Cuña =========
def apply_series_cuna(holes, variante="2x3", d=0.20, tol=1e-6):
    """
    Numera por FILA (arriba -> abajo):
      2x3: 3 filas → series 0,1,2
      zigzag: 5 filas → series 0..4
    """
    # detecta filas aproximando contra multiplios de d
    ys = sorted({round(h["y"]/d) for h in holes})  # discretiza por d
    # mapea cada y real a índice de fila ordenada de mayor a menor
    unique_y = sorted({h["y"] for h in holes}, reverse=True)
    row_levels = sorted(list(set(unique_y)), reverse=True)

    # asignar por orden vertical (top→bottom)
    if variante == "2x3":
        # esperamos 3 niveles
        ordered = sorted(row_levels, reverse=True)
        for h in holes:
            y = h["y"]
            # encuentra fila más cercana entre las 3
            idx = min(range(min(3, len(ordered))), key=lambda i: abs(y-ordered[i]))
            h["serie"] = idx
            if "delay" not in h: h["delay"] = h["serie"]
        return holes

    elif variante == "zigzag":
        # esperamos 5 niveles
        ordered = sorted(row_levels, reverse=True)
        for h in holes:
            y = h["y"]
            idx = min(range(min(5, len(ordered))), key=lambda i: abs(y-ordered[i]))
            h["serie"] = idx
            if "delay" not in h: h["delay"] = h["serie"]
        return holes

    else:
        return holes


# ========= Abanico =========
def apply_series_abanico(holes, d=0.20, y0=0.0, gap12=0.5, gap23=1.0, gap34=1.0, tol=1e-6):
    """
    F1 (y = y0)           -> serie 0
    F2 (y = y0 - gap12*d) -> serie 1
    F3 (y = y0 - gap12*d - gap23*d) -> serie 2
    F4 (y = y0 - gap12*d - gap23*d - gap34*d) -> serie 3
    """
    y1 = y0
    y2 = y1 - gap12*d
    y3 = y2 - gap23*d
    y4 = y3 - gap34*d
    for h in holes:
        y = h["y"]
        if   _near(y, y1, tol): h["serie"] = 0
        elif _near(y, y2, tol): h["serie"] = 1
        elif _near(y, y3, tol): h["serie"] = 2
        elif _near(y, y4, tol): h["serie"] = 3
        if "serie" in h and "delay" not in h:
            h["delay"] = h["serie"]
    return holes


# ========= Bethune =========
def apply_series_bethune(holes, d=0.20, y_levels=(1.6,1.4,1.2,1.0,0.9), invert_y=True, vy_factor=3.5, tol=1e-6, center_y=0.0):
    """
    Series por fila:
      F1 -> 0, F2 -> 1, F3 -> 2, F4 -> 3, F5 -> 4
    Usar los mismos parámetros que en la geometría para que calce.
    """
    sgn = -1.0 if invert_y else +1.0
    ys = [center_y + sgn*vy_factor*m*d for m in y_levels]  # F1..F5
    for h in holes:
        y = h["y"]
        # elige el nivel más cercano (0..4)
        k = min(range(len(ys)), key=lambda i: abs(y-ys[i]))
        h["serie"] = k
        if "delay" not in h:
            h["delay"] = h["serie"]
    return holes


def apply_series_sarrois(holes, d, tol=1e-6):
    def near(a,b): return abs(a-b) <= tol
    for h in holes:
        x,y = h["x"], h["y"]
        if   near(y, +d): h["serie"]= 1 if near(x, 0.0) else 2
        elif near(y, 0.0): h["serie"]= 0
        elif near(y, -d): h["serie"]= 2 if near(x, 0.0) else 1
        if "serie" in h and "delay" not in h: h["delay"]=h["serie"]
    return holes
def apply_series_sueco(holes, d, tol=1e-6):
    def near(a,b): return abs(a-b) <= tol
    for h in holes:
        x,y = h["x"], h["y"]
        if   near(y, +2*d): h["serie"]= 0 if h.get("is_void",False) else 1
        elif near(y, +1*d): h["serie"]= 0
        elif near(y, 0.0 ): h["serie"]= 0 if h.get("is_void",False) else 1
        elif near(y, -1*d): h["serie"]= 0
        elif near(y, -2*d): h["serie"]= 0 if h.get("is_void",False) else 1
        if "serie" in h and "delay" not in h: h["delay"]=h["serie"]
    return holes

def apply_series_coromant(holes, v, ax, ay, skew=0.0, tol=1e-6):
    def near(a,b): return abs(a-b) <= tol
    for h in holes:
        x,y = h["x"], h["y"]
        # vacíos
        if near(x,0.0) and (near(y,+v) or near(y,-v)):
            h["serie"]=0
        # izquierda
        elif near(x,-ax) and near(y,+ay):   h["serie"]=3
        elif near(x,-ax) and near(y,-ay):   h["serie"]=4
        elif x < -ax and near(y,0.0):       h["serie"]=1  # abierto a la izquierda
        # derecha
        elif near(x,+ax) and near(y,+ay+skew): h["serie"]=5
        elif near(x,+ax) and near(y,-ay-skew): h["serie"]=2
        elif x > +ax and near(y,0.0):         h["serie"]=0  # abierto a la derecha
        if "serie" in h and "delay" not in h: h["delay"]=h["serie"]
    return holes


def transform(holes, dx=0.0, dy=0.0):
    """Aplica un desplazamiento plano a todos los collares."""
    out = []
    for h in holes:
        h2 = dict(h)
        h2["x"] += dx
        h2["y"] += dy
        out.append(h2)
    return out

