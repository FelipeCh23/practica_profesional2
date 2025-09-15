# drift_layout.py
#
# COLOCACIÓN DE PERFORACIONES SOBRE UNA GALERÍA (TÚNEL)
# -----------------------------------------------------
# Este módulo toma una polilínea que representa el contorno de una galería
# (cerrada o abierta) y genera arreglos de perforaciones:
#   - Zapateras: a lo largo de la base (y ≈ ymin)
#   - Cajas: a lo largo de los laterales izquierdo y derecho (x ≈ xmin/xmax)
#   - Corona: a lo largo del arco superior, entre las cabezas de pared
#   - Auxiliares: rejilla interna recortada al contorno (robusto)
#   - Contracuele: figura alrededor de un centro (hexágono/rectángulo)
#
# Todas las funciones devuelven una lista de dicts con llaves:
#   {"x": float, "y": float, "is_void": bool, "note": str}


from math import cos, sin, pi


# ======================================================================
# UTILIDADES BÁSICAS
# ======================================================================

def _pt(x, y, note="", is_void=False):
    """
    Crea un punto/“perforación” con metadatos mínimos.

    Parámetros:
        x (float): coordenada X en “mundo”.
        y (float): coordenada Y en “mundo”.
        note (str): etiqueta breve, p.ej. 'zapatera', 'caja', etc.
        is_void (bool): marca especial si se requiere.

    Retorna:
        dict: {"x": x, "y": y, "is_void": ..., "note": note}
    """
    return {"x": x, "y": y, "is_void": bool(is_void), "note": note}


def _bbox(poly):
    """
    Bounding box de una polilínea.

    Parámetros:
        poly (list[tuple]): [(x,y), ...] abierta o cerrada.

    Retorna:
        tuple: (xmin, xmax, ymin, ymax)
    """
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return min(xs), max(xs), min(ys), max(ys)


def _interp(a, b, t):
    """
    Interpolación lineal entre dos puntos.

    Parámetros:
        a (tuple): (x1,y1)
        b (tuple): (x2,y2)
        t (float): 0..1

    Retorna:
        tuple: (x,y) en el segmento ab
    """
    return (a[0] + t*(b[0]-a[0]), a[1] + t*(b[1]-a[1]))


def _poly_length(poly):
    """
    Longitud total de una polilínea (suma de segmentos contiguos).

    Parámetros:
        poly (list[tuple]): [(x,y), ...]

    Retorna:
        float: longitud
    """
    import math
    L = 0.0
    for i in range(len(poly)-1):
        x1,y1 = poly[i]
        x2,y2 = poly[i+1]
        L += math.hypot(x2-x1, y2-y1)
    return L


# ======================================================================
# DETECCIÓN DE SEGMENTOS CON BASE/TECHO/LADOS
# ======================================================================

def _segments_mask_by_coord(poly, which="base", eps=0.02):
    """
    Devuelve índices de segmentos alineados con una banda del bounding box.

    Parámetros:
        poly (list[tuple]): polilínea [(x,y), ...] abierta o cerrada.
        which (str): "base" (y≈ymin), "techo" (y≈ymax),
                      "lado_izq" (x≈xmin), "lado_der" (x≈xmax)
        eps (float): tolerancia relativa (por defecto 2%)

    Retorna:
        list[int]: índices i tales que el segmento (poly[i]→poly[i+1]) está en esa banda.
    """
    xmin,xmax,ymin,ymax = _bbox(poly)
    dx = max(xmax - xmin, 1e-6)
    dy = max(ymax - ymin, 1e-6)

    idxs = []
    for i in range(len(poly)-1):
        x1,y1 = poly[i]
        x2,y2 = poly[i+1]
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
    """
    n puntos equidistantes en un segmento SIN tocar vértices.

    Parámetros:
        a (tuple): (x1,y1)
        b (tuple): (x2,y2)
        n (int): cantidad

    Retorna:
        list[tuple]: [(x,y), ...]
    """
    if n <= 0:
        return []
    return [_interp(a,b,(i+1)/(n+1)) for i in range(n)]


# ======================================================================
# REPARTO EQUITATIVO SOBRE UN CONJUNTO DE SEGMENTOS
# ======================================================================

def _distribute_over_segments(poly, idxs, n):
    """
    Coloca n puntos equiespaciados a lo largo de varios segmentos continuos,
    respetando su longitud total (sin tocar vértices).

    Parámetros:
        poly (list[tuple]): polilínea [(x,y), ...]
        idxs (list[int]): índices de segmentos seleccionados
        n (int): cantidad total de puntos a repartir

    Retorna:
        list[tuple]: [(x,y), ...] puntos sobre la cadena de segmentos
    """
    import math
    if not idxs or n <= 0:
        return []

    segs  = [(poly[i], poly[i+1]) for i in idxs]
    lens  = [math.hypot(b[0]-a[0], b[1]-a[1]) for (a,b) in segs]
    Ltot  = sum(lens)
    if Ltot <= 0:
        return []

    # Posiciones objetivo (centros de franja) en coordenada “longitud”
    targets = [ (j + 0.5) / n * Ltot for j in range(n) ]

    pts = []
    acc = 0.0
    k   = 0
    for ln, (a,b) in zip(lens, segs):
        while k < n and targets[k] <= acc + ln:
            t = (targets[k] - acc)/ln if ln > 1e-12 else 0.5
            pts.append(_interp(a, b, t))
            k += 1
        acc += ln
    return pts


# ======================================================================
# ARCO SUPERIOR ENTRE CABEZAS DE PARED
# ======================================================================

def _interpolate_cross(p1, p2, y_cut):
    """
    Intersección de un segmento con la horizontal y=y_cut.

    Parámetros:
        p1, p2 (tuple): extremos del segmento
        y_cut (float): cota Y

    Retorna:
        tuple: (x, y_cut) intersección lineal
    """
    (x1,y1), (x2,y2) = p1, p2
    if y2 == y1:
        return (x1, y_cut)
    t = (y_cut - y1) / (y2 - y1)
    return (x1 + t*(x2-x1), y_cut)


def _extract_longest_arc_above(poly, y_cut):
    """
    Extrae el arco MÁS LARGO del contorno que queda por ENCIMA de y_cut.
    Si hay cruces, cierra el arco con las intersecciones en y_cut.

    Parámetros:
        poly (list[tuple]): polilínea [(x,y), ...]
        y_cut (float): cota Y de corte superior

    Retorna:
        list[tuple]: polilínea abierta representando el arco superior.
    """
    arcs = []
    cur = []

    for i in range(len(poly)-1):
        p1 = poly[i]
        p2 = poly[i+1]
        y1 = p1[1]; y2 = p2[1]

        p1_above = (y1 >= y_cut)
        p2_above = (y2 >= y_cut)

        if p1_above and not cur:
            cur = [p1]

        if p1_above and p2_above:
            if not cur:
                cur = [p1]
            cur.append(p2)
        elif p1_above and not p2_above:
            cross = _interpolate_cross(p1, p2, y_cut)
            cur.append(cross)
            arcs.append(cur)
            cur = []
        elif (not p1_above) and p2_above:
            cross = _interpolate_cross(p1, p2, y_cut)
            cur = [cross, p2]
        else:
            pass

    if not arcs:
        return []

    def arc_len(a):
        import math
        L = 0.0
        for i in range(len(a)-1):
            x1,y1=a[i]; x2,y2=a[i+1]
            L += math.hypot(x2-x1, y2-y1)
        return L

    arcs.sort(key=arc_len, reverse=True)
    return arcs[0]


def _sample_on_open_poly(poly, n):
    """
    Muestreo equiespaciado sobre una polilínea ABIERTA.

    Parámetros:
        poly (list[tuple]): [(x,y), ...] abierta
        n (int): cantidad de puntos

    Retorna:
        list[tuple]: [(x,y), ...]
    """
    import math, bisect
    if n <= 0 or len(poly) < 2:
        return []
    d = [0.0]
    for i in range(len(poly)-1):
        x1,y1 = poly[i]
        x2,y2 = poly[i+1]
        d.append(d[-1] + math.hypot(x2-x1, y2-y1))
    L = d[-1] if d[-1] > 0 else 1.0

    def point_at(s):
        if s <= 0: return poly[0]
        if s >= L: return poly[-1]
        i = max(0, min(len(poly)-2, bisect.bisect_right(d, s)-1))
        ds = s - d[i]
        x1,y1 = poly[i]
        x2,y2 = poly[i+1]
        seg = d[i+1] - d[i]
        t = 0.0 if abs(seg) < 1e-12 else ds/seg
        return (x1 + t*(x2-x1), y1 + t*(y2-y1))

    if n == 1:
        return [point_at(L/2)]
    step = L/(n-1)
    return [point_at(k*step) for k in range(n)]


def _wall_top_y(poly):
    """
    Estima la cota Y de la cabeza de muro (parte superior de las paredes).
    Busca segmentos verticales cerca de x≈xmin y x≈xmax y toma el máximo Y
    de cada lado; retorna el mínimo de ambos (para quedar entre paredes).

    Parámetros:
        poly (list[tuple]): contorno de galería

    Retorna:
        float: y_cut recomendado para el arco de corona.
    """
    xmin,xmax,ymin,ymax = _bbox(poly)
    left_idxs  = _segments_mask_by_coord(poly, "lado_izq")
    right_idxs = _segments_mask_by_coord(poly, "lado_der")

    def max_y_on_segments(idxs):
        ys=[]
        for i in idxs:
            ys.append(poly[i][1])
            ys.append(poly[i+1][1])
        return max(ys) if ys else None

    yl = max_y_on_segments(left_idxs)
    yr = max_y_on_segments(right_idxs)

    if yl is not None and yr is not None:
        return min(yl, yr)  # segura: entre las cabezas
    # Fallback suave (por ejemplo en semicircular sin paredes):
    return ymax - 0.02*(ymax - ymin)


# ======================================================================
# COLOCADORES EN CONTORNO
# ======================================================================

def place_zapateras(tunnel_poly, n, note="zapatera"):
    """
    Coloca n perforaciones equidistantes sobre la BASE (y≈ymin).

    Parámetros:
        tunnel_poly (list[tuple]): contorno de la galería
        n (int): cantidad total a colocar
        note (str): etiqueta

    Retorna:
        list[dict]: perforaciones en base
    """
    idxs = _segments_mask_by_coord(tunnel_poly, "base")
    pts = _distribute_over_segments(tunnel_poly, idxs, n)
    return [_pt(x,y, note=note) for (x,y) in pts]


def place_cajas(tunnel_poly, n_per_side, note="caja"):
    """
    Coloca perforaciones en ambos LADOS (izq y der), sin tocar vértices.

    Parámetros:
        tunnel_poly (list[tuple]): contorno de la galería
        n_per_side (int): cantidad por lado (misma para izq y der)
        note (str): etiqueta

    Retorna:
        list[dict]: perforaciones en paredes
    """
    pts=[]
    for side in ("lado_izq","lado_der"):
        idxs = _segments_mask_by_coord(tunnel_poly, side)
        for i in idxs:
            a = tunnel_poly[i]
            b = tunnel_poly[i+1]
            pts += _sample_on_segment_equidistant(a, b, n_per_side)
    return [_pt(x,y, note=note) for (x,y) in pts]


def place_corona(tunnel_poly, n, note="corona"):
    """
    Coloca n perforaciones equidistantes a lo largo del ARCO SUPERIOR,
    limitado entre las cabezas de las paredes (sin “pasarse”).

    Estrategia:
      1) Estima y_cut en la altura de cabeza de paredes (o ~ymax si no hay).
      2) Extrae el arco más largo por encima de y_cut.
      3) Muestra n puntos equidistantes sobre ese arco.
      4) Si no se logra (caso raro), cae a segmentos “techo” (y≈ymax).

    Parámetros:
        tunnel_poly (list[tuple]): contorno de la galería
        n (int): cantidad total
        note (str): etiqueta

    Retorna:
        list[dict]: perforaciones en corona
    """
    if n <= 0:
        return []
    y_cut = _wall_top_y(tunnel_poly)
    arc = _extract_longest_arc_above(tunnel_poly, y_cut)
    if len(arc) >= 2:
        pts = _sample_on_open_poly(arc, n)
        return [_pt(x,y, note=note) for (x,y) in pts]

    # Fallback: usar “techo” plano si lo hay
    idxs = _segments_mask_by_coord(tunnel_poly, "techo")
    pts = _distribute_over_segments(tunnel_poly, idxs, n)
    return [_pt(x,y, note=note) for (x,y) in pts]


# ======================================================================
# FAMILIAS INTERIORES (REJILLA ROBUSTA)
# ======================================================================

def _point_in_polygon(poly, x, y):
    """
    Test Ray Casting: True si (x,y) está dentro del polígono.
    Acepta polilínea abierta o cerrada; internamente la cierra.

    Parámetros:
        poly (list[tuple]): contorno abierto/cerrado
        x, y (float): punto de prueba

    Retorna:
        bool: True si está dentro
    """
    if not poly or len(poly) < 3:
        return False
    # cerrar si es necesario
    if poly[0] != poly[-1]:
        p = poly + [poly[0]]
    else:
        p = poly

    inside = False
    j = len(p) - 1
    for i in range(len(p)):
        xi, yi = p[i]
        xj, yj = p[j]
        intersects = ((yi > y) != (yj > y)) and \
                     (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi)
        if intersects:
            inside = not inside
        j = i
    return inside


def place_aux_grid(tunnel_poly, nx, ny, note="aux"):
    """
    Rejilla interna nx×ny recortada al contorno de la galería.
    No asume convexidad y tolera contornos abiertos/cerrados.

    Parámetros:
        tunnel_poly (list[tuple]): contorno de la galería
        nx (int): columnas internas (sin contar bordes)
        ny (int): filas internas (sin contar bordes)
        note (str): etiqueta

    Retorna:
        list[dict]: perforaciones de la rejilla
    """
    xmin,xmax,ymin,ymax = _bbox(tunnel_poly)
    if nx <= 0 or ny <= 0:
        return []

    xs = [xmin + (xmax-xmin)*(i+1)/(nx+1) for i in range(nx)]
    ys = [ymin + (ymax-ymin)*(j+1)/(ny+1) for j in range(ny)]

    out=[]
    for y in ys:
        for x in xs:
            if _point_in_polygon(tunnel_poly, x, y):
                out.append(_pt(x, y, note=note))
    return out


# ======================================================================
# CONTRACUELES
# ======================================================================

def place_contracuele_hex(center, r=0.8, note="contracuele"):
    """
    Hexágono regular (6 puntos) alrededor de un centro.

    Parámetros:
        center (tuple): (cx,cy) centro del contracuele
        r (float): radio
        note (str): etiqueta

    Retorna:
        list[dict]: perforaciones del contracuele
    """
    cx, cy = center
    pts=[]
    for k in range(6):
        th = pi/6 + k*pi/3  # rotado suave
        x = cx + r*cos(th)
        y = cy + r*sin(th)
        pts.append(_pt(x, y, note=note))
    return pts


def place_contracuele_rect(center, w=1.4, h=1.0, n_per_side=2, note="contracuele"):
    """
    Rectángulo con n_per_side perforaciones equidistantes en cada lado,
    sin tocar vértices.

    Parámetros:
        center (tuple): (cx,cy) centro
        w (float): ancho total
        h (float): alto total
        n_per_side (int): puntos por lado
        note (str): etiqueta

    Retorna:
        list[dict]: perforaciones del contracuele
    """
    cx, cy = center
    x1, x2 = cx - w/2, cx + w/2
    y1, y2 = cy - h/2, cy + h/2
    out = []
    # base
    out += [_pt(*_interp((x1,y1),(x2,y1),(i+1)/(n_per_side+1)), note=note) for i in range(n_per_side)]
    # techo
    out += [_pt(*_interp((x1,y2),(x2,y2),(i+1)/(n_per_side+1)), note=note) for i in range(n_per_side)]
    # lado izq
    out += [_pt(*_interp((x1,y1),(x1,y2),(i+1)/(n_per_side+1)), note=note) for i in range(n_per_side)]
    # lado der
    out += [_pt(*_interp((x2,y1),(x2,y2),(i+1)/(n_per_side+1)), note=note) for i in range(n_per_side)]
    return out