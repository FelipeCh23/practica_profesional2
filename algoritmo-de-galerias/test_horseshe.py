import matplotlib.pyplot as plt
from drift_geometry import horseshoe

width = 8
height = 10
n_points = 60  # cantidad de puntos para suavizar la curva

centro = None

fig, ax = plt.subplots(figsize=(6,6))
ax.set_xlim(-10, 10)
ax.set_ylim(-10, 10)
ax.set_aspect('equal')
ax.grid(True)
ax.set_title("Horseshoe")

def dibujar():
    ax.cla()
    ax.set_xlim(-10, 10)
    ax.set_ylim(-10, 10)
    ax.set_aspect('equal')
    ax.grid(True)
    ax.set_title("Horseshoe")
    if centro:
        ax.plot(centro[0], centro[1], 'rx', markersize=12)
        verts = horseshoe(centro[0], centro[1], width, height, n_curve=n_points)
        xs, ys = zip(*verts)
        xs = list(xs) + [xs[0]]
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
