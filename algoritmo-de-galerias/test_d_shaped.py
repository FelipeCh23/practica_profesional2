import matplotlib.pyplot as plt
from drift_geometry import d_shaped  # asumimos que la función está bien en drift_geometry.py

def test_d_shaped():
    fig, ax = plt.subplots()
    ax.set_title("Click para colocar el centro de la D-Shaped")
    ax.grid(True)
    ax.set_aspect('equal', 'box')
    ax.set_xlim(-10, 10)
    ax.set_ylim(-5, 10)

    width = 10
    height = 8
    n_points = 30
    poly = None
    centro = None

    def dibujar():
        nonlocal poly
        if centro is None:
            return
        verts = d_shaped(centro[0], centro[1], width, height, n_points)
        xs, ys = zip(*verts)
        if poly:
            poly.remove()
        poly = ax.plot(xs, ys, 'b-')[0]
        ax.plot(centro[0], centro[1], 'rx')  # marca el centro
        fig.canvas.draw()

    def onclick(event):
        nonlocal centro
        if event.inaxes != ax:
            return
        centro = (event.xdata, event.ydata)
        dibujar()

    fig.canvas.mpl_connect('button_press_event', onclick)
    plt.show()

if __name__ == "__main__":
    test_d_shaped()
