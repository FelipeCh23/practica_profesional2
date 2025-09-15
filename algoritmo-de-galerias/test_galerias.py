import matplotlib.pyplot as plt
from matplotlib.widgets import RadioButtons
from drift_geometry import rectangular, semicircular, d_shaped, horseshoe, bezier_tunnel


# Parámetros iniciales

centro = None
current_geometry = "Rectangular"

params = {
    "Rectangular": {"width": 4, "height": 3},
    "Semicircular": {"radius": 2, "n_points": 30},
    "D-Shaped": {"width": 10, "height": 10, "n_points": 30},
    "Horseshoe": {"width": 4, "height": 3, "n_curve": 10},
    "Bezier": {"width": 6, "wall_height": 2, "curve_height": 3, "n_points": 30}
}


# Configurar figura y menú

fig, ax = plt.subplots(figsize=(7,7))
plt.subplots_adjust(left=0.25)
ax.set_xlim(-10, 10)
ax.set_ylim(-10, 10)
ax.set_aspect('equal')
ax.grid(True)
ax.set_title("Galerías de Minería Subterránea")

# Radio buttons para geometría
ax_radio = plt.axes([0.05, 0.3, 0.15, 0.3], facecolor='lightgoldenrodyellow')
radio = RadioButtons(ax_radio, ("Rectangular","Semicircular","D-Shaped","Horseshoe","Bezier"))

def dibujar():
    ax.cla()
    ax.set_xlim(-10, 10)
    ax.set_ylim(-10, 10)
    ax.set_aspect('equal')
    ax.grid(True)
    ax.set_title(current_geometry)
    if centro:
        ax.plot(centro[0], centro[1], 'rx', markersize=12)
        # Elegir geometría
        if current_geometry == "Rectangular":
            verts = rectangular(centro[0], centro[1], **params["Rectangular"])
        elif current_geometry == "Semicircular":
            verts = semicircular(centro[0], centro[1], **params["Semicircular"])
        elif current_geometry == "D-Shaped":
            verts = d_shaped(centro[0], centro[1], **params["D-Shaped"])
        elif current_geometry == "Horseshoe":
            verts = horseshoe(centro[0], centro[1], **params["Horseshoe"])
        elif current_geometry == "Bezier":
            verts = bezier_tunnel(centro[0], centro[1], **params["Bezier"])
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

def geometria_seleccionada(label):
    global current_geometry
    current_geometry = label
    dibujar()

fig.canvas.mpl_connect('button_press_event', onclick)
radio.on_clicked(geometria_seleccionada)

plt.show()
