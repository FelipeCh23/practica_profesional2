"""
test2_semicircular.py - Test interactivo de galería semicircular
"""

import matplotlib.pyplot as plt
from drift_geometry import semicircular, _update_center

# Parámetros de la galería
radius = 8  # metros

# Variables globales
centro = None
fig, ax = plt.subplots(figsize=(6,6))
ax.set_title("Click para colocar el centro de la galería semicircular")
ax.set_xlim(-10, 10)
ax.set_ylim(-10, 10)
ax.grid(True)
linea = None
cruz = None

def dibujar():
    global linea, cruz
    if centro is None:
        return
    # Calcular vértices
    verts = semicircular(centro[0], centro[1], radius)
    
    # Dibujar polígono
    if linea is not None:
        linea.remove()
    x_vals = [v[0] for v in verts]
    y_vals = [v[1] for v in verts]
    linea, = ax.plot(x_vals, y_vals, 'b-', linewidth=2)

    # Dibujar centro como cruz
    if cruz is not None:
        cruz.remove()
    cruz, = ax.plot(centro[0], centro[1], 'rx', markersize=10, markeredgewidth=2)

    plt.draw()

def onclick(event):
    global centro
    if event.inaxes != ax:
        return
    centro = (event.xdata, event.ydata)
    dibujar()

cid = fig.canvas.mpl_connect('button_press_event', onclick)
plt.show()
