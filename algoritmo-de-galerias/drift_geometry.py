#drift_geometry.py
"""
drift_geometry.py - Geometría de galerías subterráneas
 
Cada función calcula los vértices de una galería referida al punto
(click del usuario) como BASE (piso):
    y_base = center_y
    y_top  = center_y + altura
 
Orden de los vértices (sentido horario):
  izquierda base -> izquierda top -> techo/curva -> derecha top -> derecha base -> (cierre)
"""
 
from math import cos, sin, pi, pow
 
# ---------------- Utilidad ----------------
def _update_center(center_x: float, center_y: float,
                   offset_x: float = 0.0, offset_y: float = 0.0):
    return center_x + offset_x, center_y + offset_y
 
# ---------------- 1) Rectangular ----------------
def rectangular(center_x: float, center_y: float, width: float, height: float):
    """
    Rectángulo con base en y=center_y y techo en y=center_y+height.
    """
    cx, cy = center_x, center_y
    dx = width * 0.5
    yb = cy
    yt = cy + height
 
    left_base  = (cx - dx, yb)
    left_top   = (cx - dx, yt)
    right_top  = (cx + dx, yt)
    right_base = (cx + dx, yb)
 
    verts = [left_base, left_top, right_top, right_base, left_base]  # cerrado
    return verts
 
# ---------------- 2) Semicircular (base plana) ----------------
def semicircular(center_x: float, center_y: float, radius: float,
                 n_points: int = 30, offset_x: float = 0.0, offset_y: float = 0.0):
    """
    Base en y=center_y, arco superior de radio 'radius' hasta y=center_y+radius.
    """
    cx, cy = _update_center(center_x, center_y, offset_x, offset_y)
    r = radius
    yb = cy
    yt = cy + r
 
    left_base  = (cx - r, yb)
    right_base = (cx + r, yb)
 
    verts = [left_base, (cx - r, yt)]  # sube pared izquierda hasta inicio del arco
    # arco de izquierda (pi) a derecha (0)
    for i in range(n_points + 1):
        th = pi - (pi * i / n_points)  # pi -> 0
        x = cx + r * cos(th)
        y = yt + r * sin(th)
        verts.append((x, y))
    verts += [(cx + r, yt), right_base, left_base]  # pared derecha, base, cierre
    return verts
 
# ---------------- 3) D-Shaped ----------------
def d_shaped(center_x: float, center_y: float, width: float, height: float,
             n_points: int = 30, offset_x: float = 0.0, offset_y: float = 0.0):
    """
    Paredes rectas hasta y_top, y semicírculo superior de radio = width/2.
    """
    cx, cy = _update_center(center_x, center_y, offset_x, offset_y)
    r = width * 0.5
    wall_h = max(height - r, 0.0)
    yb = cy
    yt = cy + wall_h
 
    left_base  = (cx - r, yb)
    left_top   = (cx - r, yt)
    right_top  = (cx + r, yt)
    right_base = (cx + r, yb)
 
    verts = [left_base, left_top]
    # arco superior (izq->der)
    for i in range(n_points + 1):
        th = pi - (pi * i / n_points)  # pi -> 0
        x = cx + r * cos(th)
        y = yt + r * sin(th)
        verts.append((x, y))
    verts += [right_top, right_base, left_base]
    return verts
 
# ---------------- 4) Horseshoe (herradura) ----------------
def horseshoe(center_x: float, center_y: float, width: float, height: float,
              n_curve: int = 24, offset_x: float = 0.0, offset_y: float = 0.0):
    """
    Herradura clásica: paredes rectas hasta y_top y semicírculo superior
    de radio = width/2 (NO usa width completo en y, así no “explota” al click).
 
    width: ancho total en la base
    height: altura recta de paredes (hasta el inicio del arco)
    """
    cx, cy = _update_center(center_x, center_y, offset_x, offset_y)
    r = width * 0.5
    yb = cy
    yt = cy + height
 
    left_base  = (cx - r, yb)
    left_top   = (cx - r, yt)
    right_top  = (cx + r, yt)
    right_base = (cx + r, yb)
 
    verts = [left_base, left_top]
    # arco superior (izq->der) centrado en (cx, yt) con radio r
    for i in range(n_curve + 1):
        th = pi - (pi * i / n_curve)  # pi -> 0
        x = cx + r * cos(th)
        y = yt + r * sin(th)
        verts.append((x, y))
    verts += [right_top, right_base, left_base]
    return verts
 
# ---------------- 5) Bezier (techo Bezier + paredes) ----------------
def bezier_tunnel(center_x: float, center_y: float, width: float,
                  wall_height: float, curve_height: float, n_points: int = 30,
                  offset_x: float = 0.0, offset_y: float = 0.0):
    """
    Paredes rectas hasta y_top = center_y + wall_height
    y techo Bezier cúbico de (x0,y_top) a (x3,y_top) con bombeo 'curve_height'.
    """
    cx, cy = _update_center(center_x, center_y, offset_x, offset_y)
    yb = cy
    yt = cy + wall_height
    x0 = cx - width * 0.5
    x3 = cx + width * 0.5
    # controles Bezier (suben curve_height)
    x1, y1 = x0 + width/3.0, yt + curve_height
    x2, y2 = x0 + 2.0*width/3.0, yt + curve_height
 
    left_base  = (x0, yb)
    left_top   = (x0, yt)
    right_top  = (x3, yt)
    right_base = (x3, yb)
 
    verts = [left_base, left_top]
    # curva superior Bezier de izq->der
    for i in range(n_points + 1):
        t = i / n_points
        Bx = (1-t)**3 * x0 + 3*(1-t)**2 * t * x1 + 3*(1-t) * t**2 * x2 + t**3 * x3
        By = (1-t)**3 * yt + 3*(1-t)**2 * t * y1 + 3*(1-t) * t**2 * y2 + t**3 * yt
        verts.append((Bx, By))
    verts += [right_top, right_base, left_base]
    return verts