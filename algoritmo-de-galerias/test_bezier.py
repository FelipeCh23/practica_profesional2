import matplotlib.pyplot as plt
from drift_geometry import bezier_tunnel

# Parámetros de la galería
width = 8
wall_height = 5
curve_height = 2
n_points = 30

centro = None

fig, ax = plt.subplots(figsize=(8,6))
ax.set_xlim(-10, 10)
ax.set_ylim(-5, 10)
ax.set_aspect('equal')
ax.grid(True)
ax.set_title("Bezier Tunnel")

def dibujar():
    ax.cla()
    ax.set_xlim(-10, 10)
    ax.set_ylim(-5, 10)
    ax.set_aspect('equal')
    ax.grid(True)
    ax.set_title("Bezier Tunnel")
    if centro:
        # Marcar el centro
        ax.plot(centro[0], centro[1], 'rx', markersize=12)
        # Obtener vértices de la galería
        verts = bezier_tunnel(centro[0], centro[1], width, wall_height, curve_height, n_points)
        xs, ys = zip(*verts)
        xs = list(xs) + [xs[0]]  # Cerrar figura
        ys = list(ys) + [ys[0]]
        ax.plot(xs, ys, '-o')
    fig.canvas.draw()

def onclick(event):
    global centro
    if event.inaxes == ax:
        centro = (event.xdata, event.ydata)
        dibujar()

fig.canvas.mpl_connect('button_press_event', onclick)
plt.show()
