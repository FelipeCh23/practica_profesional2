# test_cuele_viz.py
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from blast_cuts import (
    # Geometrías
    cuele_sarrois_geom, cuele_sueco_geom, cuele_coromant_geom,
    cuele_cuatro_secciones_geom, cuele_cuna_geom,
    cuele_abanico_geom, cuele_bethune_geom,
    # Apply series
    apply_series_sarrois, apply_series_sueco, apply_series_coromant,
    apply_series_cuatro_secciones, apply_series_cuna,
    apply_series_abanico, apply_series_bethune,
)

def plot_cuele(holes, ax, title, vacio_label="0"):
    ax.set_aspect('equal')
    ax.grid(True, linewidth=0.4, alpha=0.6)
    ax.set_title(title)

    def serie_of(h):
        return h.get("serie", h.get("delay", ""))

    cmap = {0:"C2", 1:"C1", 2:"C3", 3:"C4", 4:"C5", 5:"C6"}
    xs, ys, cs = [], [], []
    for h in holes:
        xs.append(h["x"]); ys.append(h["y"])
        cs.append("k" if h.get("is_void", False) else cmap.get(serie_of(h), "C0"))
    ax.scatter(xs, ys, c=cs, s=60, zorder=2)

    for h in holes:
        lab = vacio_label if h.get("is_void", False) else str(serie_of(h))
        ax.text(h["x"], h["y"], lab, fontsize=8, ha='center', va='bottom')

    if xs and ys:
        pad = 0.2
        ax.set_xlim(min(xs)-pad, max(xs)+pad)
        ax.set_ylim(min(ys)-pad, max(ys)+pad)

def legend_series(fig):
    handles = [
        Line2D([0],[0], marker='o', color='w', label='serie 0', markerfacecolor='C2', markersize=7),
        Line2D([0],[0], marker='o', color='w', label='serie 1', markerfacecolor='C1', markersize=7),
        Line2D([0],[0], marker='o', color='w', label='serie 2', markerfacecolor='C3', markersize=7),
        Line2D([0],[0], marker='o', color='w', label='serie 3', markerfacecolor='C4', markersize=7),
        Line2D([0],[0], marker='o', color='w', label='serie 4', markerfacecolor='C5', markersize=7),
        Line2D([0],[0], marker='o', color='k', label='vacío', markerfacecolor='none', markersize=8),
    ]
    fig.legend(handles=handles, loc='upper center', ncol=6, frameon=False)

fig, axs = plt.subplots(2, 4, figsize=(14, 7))

# ---- Sarrois ----
d_s = 0.15
holes = cuele_sarrois_geom(d=d_s)
apply_series_sarrois(holes, d=d_s)
plot_cuele(holes, axs[0,0], "Sarrois")

# ---- Sueco ----
d_sw = 0.12
holes = cuele_sueco_geom(d=d_sw)
apply_series_sueco(holes, d=d_sw)
plot_cuele(holes, axs[0,1], "Sueco")

# ---- Coromant ----
v, ax_c, ay, skew, spread = 0.06, 0.16, 0.16, 0.05, 1.4
holes = cuele_coromant_geom(v=v, ax=ax_c, ay=ay, skew=skew, spread=spread)
apply_series_coromant(holes, v=v, ax=ax_c, ay=ay, skew=skew)
plot_cuele(holes, axs[0,2], "Coromant")

# ---- Cuatro secciones ----
D, D2 = 0.20, 0.20
k2=k3=k4=1.5
# recomputamos A1..A4 exactamente como en la geometría para el apply:
B1=1.5*D; B2=k2*B1; B3=k3*B2; B4=k4*B3
A1=B1; A2=B1+B2; A3=B1+B2+B3; A4=B1+B2+B3+B4
holes = cuele_cuatro_secciones_geom(D=D, D2=D2, k2=k2, k3=k3, k4=k4, add_mids_S4=True)
apply_series_cuatro_secciones(holes, A1, A2, A3, A4, add_mids_S4=True)
plot_cuele(holes, axs[0,3], "4 secciones")

# ---- Cuña 2x3 ----
d_c = 0.20
holes = cuele_cuna_geom(d=d_c, variante="2x3", sep_cols_factor=2.0)
apply_series_cuna(holes, variante="2x3", d=d_c)
plot_cuele(holes, axs[1,0], "Cuña 2x3")

# ---- Cuña zigzag ----
holes = cuele_cuna_geom(d=d_c, variante="zigzag")
apply_series_cuna(holes, variante="zigzag", d=d_c)
plot_cuele(holes, axs[1,1], "Cuña zigzag")

# ---- Abanico ----
d_a = 0.20
gap12, gap23, gap34 = 0.5, 1.0, 1.0
holes = cuele_abanico_geom(d=d_a, dx_factor=0.5, gap12=gap12, gap23=gap23, gap34=gap34)
apply_series_abanico(holes, d=d_a, y0=0.0, gap12=gap12, gap23=gap23, gap34=gap34)
plot_cuele(holes, axs[1,2], "Abanico")

# ---- Bethune ----
d_b = 0.20
y_levels = (1.6, 1.4, 1.2, 1.0, 0.9)
holes = cuele_bethune_geom(d=d_b, dx_factor=1.2, y_levels=y_levels, invert_y=True, vy_factor=3.5)
apply_series_bethune(holes, d=d_b, y_levels=y_levels, invert_y=True, vy_factor=3.5)
plot_cuele(holes, axs[1,3], "Bethune")

legend_series(fig)
plt.tight_layout(rect=(0,0,1,0.93))
plt.show()
