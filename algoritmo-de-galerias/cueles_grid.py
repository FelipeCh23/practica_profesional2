# cuele_grid_app.py 

# Asistente por pasos para diseñar galería + familias + cueles/contracuele (con borrado por paso) 

 

import math 
import tkinter as tk 
from tkinter import ttk, messagebox 


# --- blast_cuts: patrones de cueles --- 

from blast_cuts import ( 

    cuele_sarrois_geom, cuele_sueco_geom, cuele_coromant_geom, 
    cuele_cuna_geom, cuele_abanico_geom, cuele_bethune_geom, cuele_cuatro_secciones_geom, 
    apply_series_sarrois, apply_series_sueco, apply_series_coromant, 
    apply_series_cuna, apply_series_abanico, apply_series_bethune, 
    apply_series_cuatro_secciones, 
) 

# --- drift_geometry: formas de galería --- 

from drift_geometry import semicircular, d_shaped, rectangular, horseshoe, bezier_tunnel  

# --- drift_layout: familias sobre la galería --- 

from drift_layout import ( 

    place_zapateras, place_cajas, place_corona, 
    place_aux_grid, place_contracuele_hex, place_contracuele_rect 

) 

 

#  Mundo ↔ Pantalla 
SNAP_TOL_M = 0.20 #tolerancia de snap a perforaciones
PX_PER_M = 160.0 

GRID_M   = 0.10 

CANVAS_W = 1000 

CANVAS_H = 700 

ORIGIN_X = CANVAS_W // 2 

ORIGIN_Y = CANVAS_H // 2 

 

def w2c(xm, ym): 

    return ORIGIN_X + xm*PX_PER_M, ORIGIN_Y - ym*PX_PER_M 

 

def c2w(xp, yp): 

    return (xp - ORIGIN_X)/PX_PER_M, (ORIGIN_Y - yp)/PX_PER_M 

 

# -------------------- Modelo -------------------- 

class Scene: 

    def __init__(self): 

        self.holes = []      # dicts: {x,y,is_void,note, _step, _kind, (serie,delay)} 

        self.tunnels = []    # cada túnel es una polilínea [(x,y),...] 

        self.selected_idx = None 

 

    def add_holes(self, hs): 

        self.holes.extend(hs) 

 

    def add_tunnel(self, poly): 

        if poly and len(poly) >= 2: 

            self.tunnels.append(poly) 

            return len(self.tunnels) - 1 

        return None 

 

    def remove_holes_by_step(self, step): 

        self.holes = [h for h in self.holes if h.get("_step") != step] 

 

    def nearest(self, xm, ym, tol_m=0.15): 

        best_i, best_d = None, 1e9 

        for i,h in enumerate(self.holes): 

            d = math.hypot(h["x"]-xm, h["y"]-ym) 

            if d < best_d and d <= tol_m: 

                best_d, best_i = d, i 

        return best_i 

 

# -------------------- Pasos del asistente -------------------- 

SP_GEOM   = 0  # elegir / configurar geometría y click para ubicar 

SP_ZAP    = 1  # zapateras 

SP_CAJAS  = 2  # cajas (por lado, misma cantidad para ambos lados) 

SP_CORONA = 3  # corona 

SP_CUELES = 4  # cueles (click para ubicar) 

SP_CC     = 5  # contracuele (click para ubicar) 

SP_AUX    = 6  # perforaciones auxiliares (grilla interna) 

STEPS_MAX = SP_AUX 

 

# -------------------- App -------------------- 

class App(tk.Tk): 

    def __init__(self): 

        super().__init__() 

        self.title("Diseño de galerías y cueles - asistente por pasos") 
        self.geometry(f"{CANVAS_W+380}x{CANVAS_H+40}") 

 

        # Estado 

        self.scene = Scene() 
        self.tunnel_poly = []   # polilínea de la galería activa 
        self.geom_index = None  # índice del túnel activo dentro de scene.tunnels 
        self.step = SP_GEOM 
        self.dragging_idx = None 

 

        # flags de finalización por paso 

        self.done_geom = False 
        self.done_zap = False 
        self.done_cajas = False 
        self.done_corona = False 
        self.done_cueles = False 
        self.done_cc = False 
        self.done_aux = False 

 

        # UI 

        self._build_ui() 
        self._render_step_panel() 
        self._update_step_label() 
        self.draw() 

 

    # ---------- helpers tagging ---------- 

    def _tag(self, holes, step, kind): 

        for h in holes: 
            h["_step"] = step 
            h["_kind"] = kind 

        return holes 

 

    # ---------- UI estático ---------- 

    def _build_ui(self): 

        # Canvas 

        self.canvas = tk.Canvas(self, width=CANVAS_W, height=CANVAS_H, bg="white") 

        self.canvas.grid(row=0, column=0, padx=6, pady=6, sticky="nsew") 

        self.grid_columnconfigure(0, weight=1) 

        self.grid_rowconfigure(0,   weight=1) 

 

        # Side (contenedor) 

        self.side = ttk.Frame(self) 

        self.side.grid(row=0, column=1, sticky="ns", padx=6, pady=6) 

 

        # Cabecera del asistente 

        hdr = ttk.Frame(self.side); hdr.pack(fill="x") 

        self.step_label = ttk.Label(hdr, text="") 

        self.step_label.pack(anchor="w") 

 

        # Panel de contenido por paso (lo re-creamos cada vez) 

        self.step_frame = ttk.Frame(self.side) 

        self.step_frame.pack(fill="x", pady=(6,4)) 

 

        # Opciones generales 

        opts = ttk.LabelFrame(self.side, text="Opciones") 

        opts.pack(fill="x", pady=6) 

        self.show_labels = tk.BooleanVar(value=False) 

        ttk.Checkbutton(opts, text="Mostrar series", variable=self.show_labels).pack(anchor="w") 

        self.snap_grid = tk.BooleanVar(value=True) 

        ttk.Checkbutton(opts, text="Ajustar a grilla", variable=self.snap_grid).pack(anchor="w") 

        ttk.Label(self.side, text="Arrastra puntos para ajustarlos manualmente.").pack(anchor="w", pady=(2,8)) 

 

        # Botonera pie 

        foot = ttk.Frame(self.side); foot.pack(fill="x", pady=(6,0)) 

        self.btn_prev = ttk.Button(foot, text="Anterior", command=self.prev_step) 

        self.btn_prev.pack(side="left") 

        self.btn_next = ttk.Button(foot, text="Siguiente", command=self.next_step) 

        self.btn_next.pack(side="right") 

 

        util = ttk.Frame(self.side); util.pack(fill="x", pady=6) 

        ttk.Button(util, text="Borrar todo", command=self.clear_all).pack(side="left") 

        ttk.Button(util, text="Export JSON", command=self.export_json).pack(side="right") 

 

        # Eventos canvas 

        self.canvas.bind("<Button-1>", self.on_click) 
        self.canvas.bind("<B1-Motion>", self.on_drag) 
        self.canvas.bind("<ButtonRelease-1>", self.on_release) 
        self.bind("<Delete>", self._delete_selected) 
        self.bind("<BackSpace>", self._delete_selected)
        self.canvas.bind("<Double-Button-1>", self.on_double_click) 

 

    # ---------- UI dinámico por paso ---------- 

    def _render_step_panel(self): 

        # limpiar 

        for w in self.step_frame.winfo_children(): 

            w.destroy() 

 

        # por defecto, política de botones 

        self.btn_prev.configure(state="normal" if self.step > SP_GEOM else "disabled") 

        self.btn_next.configure(state="disabled")  # se habilita cuando el paso queda “done” 

 

        # ---------- GEOMETRÍA ---------- 

        if self.step == SP_GEOM: 

            frm = ttk.LabelFrame(self.step_frame, text="Geometría de galería") 

            frm.pack(fill="x") 

 

            ttk.Label(frm, text="Tipo").grid(row=0, column=0, sticky="w") 

            self.geom_type = tk.StringVar(value="Semicircular") 

            ttk.Combobox(frm, textvariable=self.geom_type, 

                         values=["Semicircular", "D-shaped", "Rectangular", "Horseshoe", "Bezier"], 

                         state="readonly", width=18).grid(row=0, column=1, sticky="e") 

 

            # parámetros 

            self.geom_w     = tk.DoubleVar(value=3.0)  # ancho o 2*R 

            self.geom_h     = tk.DoubleVar(value=3.0)  # alto / wall height 

            self.geom_r     = tk.DoubleVar(value=1.5)  # radio (semicircular) 

            self.geom_curve = tk.DoubleVar(value=0.8)  # altura curva (Bezier) 

 

            row = 1 

            for label, var in [ 

                ("Ancho / 2R", self.geom_w), 

                ("Alto",        self.geom_h), 

                ("Radio",       self.geom_r), 

                ("Curva (Bezier)", self.geom_curve), 

            ]: 

                ttk.Label(frm, text=label).grid(row=row, column=0, sticky="w") 

                ttk.Entry(frm, textvariable=var, width=10).grid(row=row, column=1, sticky="e") 

                row += 1 

 

            ttk.Label(self.step_frame, text="Haz CLICK en el canvas para ubicar el centro de la galería.").pack(anchor="w", pady=(6,6)) 

            ttk.Button(self.step_frame, text="Borrar este paso", command=lambda: self._clear_step(SP_GEOM)).pack(anchor="w") 

 

            if self.tunnel_poly: 

                self.done_geom = True 

            self.btn_next.configure(state="normal" if self.done_geom else "disabled") 

 

        # ---------- ZAPATERAS ---------- 

        elif self.step == SP_ZAP: 

            frm = ttk.LabelFrame(self.step_frame, text="Zapateras (base)") 

            frm.pack(fill="x") 

            self.n_zap = tk.IntVar(value=6) 

            ttk.Label(frm, text="Nº de perforaciones").grid(row=0, column=0, sticky="w") 

            ttk.Entry(frm, textvariable=self.n_zap, width=10).grid(row=0, column=1, sticky="e") 

 

            bar = ttk.Frame(self.step_frame); bar.pack(fill="x", pady=(6,0)) 

            ttk.Button(bar, text="Agregar", command=self._do_zap).pack(side="left") 

            ttk.Button(bar, text="Borrar este paso", command=lambda: self._clear_step(SP_ZAP)).pack(side="left", padx=6) 

 

            ttk.Label(self.step_frame, text="Se distribuirán equidistantes sobre la base de la galería.").pack(anchor="w", pady=(6,0)) 

            self.btn_next.configure(state="normal" if self.done_zap else "disabled") 

 

        # ---------- CAJAS ---------- 

        elif self.step == SP_CAJAS: 

            frm = ttk.LabelFrame(self.step_frame, text="Cajas (paredes)") 

            frm.pack(fill="x") 

            self.n_caja = tk.IntVar(value=5) 

            ttk.Label(frm, text="Cajas por lado").grid(row=0, column=0, sticky="w") 

            ttk.Entry(frm, textvariable=self.n_caja, width=10).grid(row=0, column=1, sticky="e") 

 

            bar = ttk.Frame(self.step_frame); bar.pack(fill="x", pady=(6,0)) 

            ttk.Button(bar, text="Agregar", command=self._do_cajas).pack(side="left") 

            ttk.Button(bar, text="Borrar este paso", command=lambda: self._clear_step(SP_CAJAS)).pack(side="left", padx=6) 

 

            ttk.Label(self.step_frame, text="Se colocan en ambos lados (mismo número por lado).").pack(anchor="w", pady=(6,0)) 

            self.btn_next.configure(state="normal" if self.done_cajas else "disabled") 

 

        # ---------- CORONA ---------- 

        elif self.step == SP_CORONA: 

            frm = ttk.LabelFrame(self.step_frame, text="Corona (techo)") 

            frm.pack(fill="x") 

            self.n_corona = tk.IntVar(value=8) 

            ttk.Label(frm, text="Nº de perforaciones").grid(row=0, column=0, sticky="w") 

            ttk.Entry(frm, textvariable=self.n_corona, width=10).grid(row=0, column=1, sticky="e") 

 

            bar = ttk.Frame(self.step_frame); bar.pack(fill="x", pady=(6,0)) 

            ttk.Button(bar, text="Agregar", command=self._do_corona).pack(side="left") 

            ttk.Button(bar, text="Borrar este paso", command=lambda: self._clear_step(SP_CORONA)).pack(side="left", padx=6) 

 

            ttk.Label(self.step_frame, text="Se distribuirán equidistantes en el techo.").pack(anchor="w", pady=(6,0)) 

            self.btn_next.configure(state="normal" if self.done_corona else "disabled") 

 

        # ---------- CUELES ---------- 

        elif self.step == SP_CUELES: 

            frm = ttk.LabelFrame(self.step_frame, text="Cueles") 

            frm.pack(fill="x") 

 

            ttk.Label(frm, text="Tipo").grid(row=0, column=0, sticky="w") 

            self.cuele_type = tk.StringVar(value="Sarrois") 

            ttk.Combobox(frm, textvariable=self.cuele_type, 

                         values=["Sarrois","Sueco","Coromant","Cuña 2x3","Cuña zigzag","Abanico","Bethune","Cuatro secciones"], 

                         state="readonly", width=18).grid(row=0, column=1, sticky="e") 

 

            self.d_var  = tk.DoubleVar(value=0.15) 

            self.rot    = tk.DoubleVar(value=0.0) 

            self.sx     = tk.DoubleVar(value=1.0) 

            self.sy     = tk.DoubleVar(value=1.0) 

            self.vy     = tk.DoubleVar(value=3.5) 

 

            row = 1 

            for label, var in [("d (m)", self.d_var), ("rot (°)", self.rot), 

                               ("scale X", self.sx), ("scale Y", self.sy), ("Bethune vy", self.vy)]: 

                ttk.Label(frm, text=label).grid(row=row, column=0, sticky="w") 

                ttk.Entry(frm, textvariable=var, width=10).grid(row=row, column=1, sticky="e") 

                row += 1 

 

            ttk.Label(self.step_frame, text="Haz CLICK en el canvas para insertar un cuele en ese punto.").pack(anchor="w", pady=(6,6)) 

            ttk.Button(self.step_frame, text="Borrar este paso", command=lambda: self._clear_step(SP_CUELES)).pack(anchor="w") 

 

            self.btn_next.configure(state="normal" if self.done_cueles else "disabled") 

 

        # ---------- CONTRACUELE ---------- 

        elif self.step == SP_CC: 

            frm = ttk.LabelFrame(self.step_frame, text="Contracuele") 

            frm.pack(fill="x") 

 

            ttk.Label(frm, text="Figura").grid(row=0, column=0, sticky="w") 

            self.cc_type = tk.StringVar(value="Hexágono") 

            ttk.Combobox(frm, textvariable=self.cc_type, 

                         values=["Hexágono","Rectángulo"], state="readonly", width=18).grid(row=0, column=1, sticky="e") 

 

            self.cc_hex_r  = tk.DoubleVar(value=0.8) 

            self.cc_rect_w = tk.DoubleVar(value=1.6) 

            self.cc_rect_h = tk.DoubleVar(value=1.1) 

            self.cc_rect_n = tk.IntVar(value=2) 

 

            row = 1 

            ttk.Label(frm, text="Hex r").grid(row=row, column=0, sticky="w") 

            ttk.Entry(frm, textvariable=self.cc_hex_r, width=10).grid(row=row, column=1, sticky="e"); row += 1 

            ttk.Label(frm, text="Rect w").grid(row=row, column=0, sticky="w") 

            ttk.Entry(frm, textvariable=self.cc_rect_w, width=10).grid(row=row, column=1, sticky="e"); row += 1 

            ttk.Label(frm, text="Rect h").grid(row=row, column=0, sticky="w") 

            ttk.Entry(frm, textvariable=self.cc_rect_h, width=10).grid(row=row, column=1, sticky="e"); row += 1 

            ttk.Label(frm, text="Rect n/lado").grid(row=row, column=0, sticky="w") 

            ttk.Entry(frm, textvariable=self.cc_rect_n, width=10).grid(row=row, column=1, sticky="e"); row += 1 

 

            ttk.Label(self.step_frame, text="Haz CLICK en el canvas para colocar el contracuele.").pack(anchor="w", pady=(6,6)) 

            ttk.Button(self.step_frame, text="Borrar este paso", command=lambda: self._clear_step(SP_CC)).pack(anchor="w") 

 

            self.btn_next.configure(state="normal" if self.done_cc else "disabled") 

 

        # ---------- AUXILIARES ---------- 

        elif self.step == SP_AUX: 

            frm = ttk.LabelFrame(self.step_frame, text="Perforaciones auxiliares (grilla interna)") 

            frm.pack(fill="x") 

            self.aux_nx = tk.IntVar(value=5) 

            self.aux_ny = tk.IntVar(value=3) 

            ttk.Label(frm, text="nx").grid(row=0, column=0, sticky="w") 

            ttk.Entry(frm, textvariable=self.aux_nx, width=10).grid(row=0, column=1, sticky="e") 

            ttk.Label(frm, text="ny").grid(row=1, column=0, sticky="w") 

            ttk.Entry(frm, textvariable=self.aux_ny, width=10).grid(row=1, column=1, sticky="e") 

 

            bar = ttk.Frame(self.step_frame); bar.pack(fill="x", pady=(6,0)) 

            ttk.Button(bar, text="Agregar", command=self._do_aux).pack(side="left") 

            ttk.Button(bar, text="Borrar este paso", command=lambda: self._clear_step(SP_AUX)).pack(side="left", padx=6) 

 

            ttk.Label(self.step_frame, text="Se distribuyen equidistantes dentro de la galería.").pack(anchor="w", pady=(6,0)) 

            self.btn_next.configure(state="normal" if self.done_aux else "disabled") 

 

    def _update_step_label(self): 

        names = { 

            SP_GEOM:   "Paso 1/7: Geometría", 

            SP_ZAP:    "Paso 2/7: Zapateras", 

            SP_CAJAS:  "Paso 3/7: Cajas", 

            SP_CORONA: "Paso 4/7: Corona", 

            SP_CUELES: "Paso 5/7: Cueles", 

            SP_CC:     "Paso 6/7: Contracuele", 

            SP_AUX:    "Paso 7/7: Auxiliares", 

        } 

        self.step_label.config(text=names[self.step]) 

 

    # ---------- Navegación ---------- 

    def prev_step(self): 

        if self.step > SP_GEOM: 

            self.step -= 1 

            self._render_step_panel() 

            self._update_step_label() 

 

    def next_step(self): 

        # bloqueos por paso 

        if self.step == SP_GEOM and not self.done_geom: 

            messagebox.showwarning("Geometría", "Coloca la geometría con un click en el canvas.") 

            return 

        if self.step == SP_ZAP and not self.done_zap: 

            messagebox.showwarning("Zapateras", "Pulsa 'Agregar' para colocar las zapateras.") 

            return 

        if self.step == SP_CAJAS and not self.done_cajas: 

            messagebox.showwarning("Cajas", "Pulsa 'Agregar' para colocar las cajas.") 

            return 

        if self.step == SP_CORONA and not self.done_corona: 

            messagebox.showwarning("Corona", "Pulsa 'Agregar' para colocar la corona.") 

            return 

        if self.step == SP_CUELES and not self.done_cueles: 

            messagebox.showwarning("Cueles", "Inserta al menos un cuele haciendo click en el canvas.") 

            return 

        if self.step == SP_CC and not self.done_cc: 

            messagebox.showwarning("Contracuele", "Inserta el contracuele haciendo click en el canvas.") 

            return 

        if self.step < STEPS_MAX: 

            self.step += 1 

            self._render_step_panel() 

            self._update_step_label() 

 

    # ---------- Dibujo ---------- 

    def draw(self): 

        self.canvas.delete("all") 

        self._draw_grid() 

        self._draw_tunnels() 

        self._draw_holes() 

 

    def _draw_grid(self): 

        step = GRID_M*PX_PER_M 

        x = ORIGIN_X % step 

        while x < CANVAS_W: 

            self.canvas.create_line(x, 0, x, CANVAS_H, fill="#eee") 

            x += step 

        y = ORIGIN_Y % step 

        while y < CANVAS_H: 

            self.canvas.create_line(0, y, CANVAS_W, y, fill="#eee") 

            y += step 

        self.canvas.create_line(0, ORIGIN_Y, CANVAS_W, ORIGIN_Y, fill="#bbb") 

        self.canvas.create_line(ORIGIN_X, 0, ORIGIN_X, CANVAS_H, fill="#bbb") 

 

    def _draw_tunnels(self): 

        for poly in self.scene.tunnels + ([self.tunnel_poly] if self.tunnel_poly else []): 

            if len(poly) < 2: continue 

            pts = [] 

            for (x,y) in poly: 

                xp, yp = w2c(x,y); pts.extend([xp,yp]) 

            self.canvas.create_line(*pts, fill="#888", width=2) 

 

    def _draw_holes(self): 

        r_px = 5 

        for i,h in enumerate(self.scene.holes): 

            xp, yp = w2c(h["x"], h["y"]) 

            color = "black" if h.get("is_void", False) else "#1f77b4" 

            if "serie" in h: 

                palette = ["#2ca02c","#ff7f0e","#d62728","#9467bd","#8c564b","#e377c2"] 

                color = "black" if h.get("is_void", False) else palette[h["serie"] % len(palette)] 

            self.canvas.create_oval(xp-r_px, yp-r_px, xp+r_px, yp+r_px, fill=color, outline="") 

            if self.show_labels.get() and "serie" in h: 

                self.canvas.create_text(xp, yp-10, text=str(h["serie"]), fill="#444", font=("Arial", 9)) 

            if i == self.scene.selected_idx: 

                self.canvas.create_oval(xp-9, yp-9, xp+9, yp+9, outline="#444") 

 

    # ---------- Interacción ---------- 

    def on_click(self, ev): 

        xm, ym = c2w(ev.x, ev.y) 

 

        # ¿arrastrar un punto existente? 

        idx = self.scene.nearest(xm, ym) 

        if idx is not None and self.step not in (SP_CC,): 
            self.scene.selected_idx = idx 
            self.dragging_idx = idx 
            self.draw() 

            return 

        # snap a grilla 

        if self.snap_grid.get(): 

            xm = round(xm/GRID_M)*GRID_M 

            ym = round(ym/GRID_M)*GRID_M 

        # pasos que requieren click para insertar 

        if self.step == SP_GEOM: 

            gtype = self.geom_type.get() 

            if gtype == "Semicircular": 

                R = float(self.geom_r.get()) 

                self.tunnel_poly = semicircular(xm, ym, radius=R, n_points=48) 

            elif gtype == "D-shaped": 

                w = float(self.geom_w.get()); h = float(self.geom_h.get()) 

                self.tunnel_poly = d_shaped(xm, ym, width=w, height=h, n_points=48) 

            elif gtype == "Rectangular": 

                w = float(self.geom_w.get()); h = float(self.geom_h.get()) 

                self.tunnel_poly = rectangular(xm, ym, width=w, height=h) 

            elif gtype == "Horseshoe": 

                w = float(self.geom_w.get()); h = float(self.geom_h.get()) 

                self.tunnel_poly = horseshoe(xm, ym, width=w, height=h, n_curve=24) 

            elif gtype == "Bezier": 

                w = float(self.geom_w.get()); wall = float(self.geom_h.get()); ch = float(self.geom_curve.get()) 

                self.tunnel_poly = bezier_tunnel(xm, ym, width=w, wall_height=wall, curve_height=ch, n_points=48) 

            # guardar 

            self.geom_index = self.scene.add_tunnel(self.tunnel_poly) 

            self.done_geom = True 

            self.draw() 

            self._render_step_panel() 

            return 

 

        elif self.step == SP_CUELES: 

            holes = self._insert_cuele_at(xm, ym) 

            if holes: 

                self.scene.add_holes(self._tag(holes, SP_CUELES, "cuele")) 

                self.done_cueles = True 

                self.draw() 

                self._render_step_panel() 

            return 

 

        elif self.step == SP_CC: 

            if not self.tunnel_poly: 

                messagebox.showwarning("Geometría", "Primero inserta la geometría (Paso 1).") 

                return 
            
            #Snap opcional al agujero más cercano(ejemplo:centro de cuele)
            idx = self.scene.nearest(xm, ym, tol_m=SNAP_TOL_M)
            if idx is not None:
                xm = self.scene.holes[idx]["x"]
                ym = self.scene.holes[idx]["y"]

            cct = self.cc_type.get()

            if cct == "Hexágono": 

                r = float(self.cc_hex_r.get()) 

                holes = place_contracuele_hex((xm,ym), r=r) 

            else: 

                w = float(self.cc_rect_w.get()); h = float(self.cc_rect_h.get()); m = int(self.cc_rect_n.get()) 

                holes = place_contracuele_rect((xm,ym), w=w, h=h, n_per_side=m) 

            self.scene.add_holes(self._tag(holes, SP_CC, "contracuele")) 

            self.done_cc = True 

            self.draw() 

            self._render_step_panel() 

            return 

  

    def on_drag(self, ev): 

        if self.dragging_idx is None: 

            return 

        xm, ym = c2w(ev.x, ev.y) 

        if self.snap_grid.get(): 

            xm = round(xm/GRID_M)*GRID_M 

            ym = round(ym/GRID_M)*GRID_M 

        self.scene.holes[self.dragging_idx]["x"] = xm 

        self.scene.holes[self.dragging_idx]["y"] = ym 

        self.draw() 

 

    def on_release(self, ev): 

        self.dragging_idx = None 

 

    def _delete_selected(self, ev=None): 

        i = self.scene.selected_idx 

        if i is not None and 0 <= i < len(self.scene.holes): 

            del self.scene.holes[i] 

            self.scene.selected_idx = None 

            self.draw() 

 

    # ---------- Inserciones específicas ---------- 

    def _insert_cuele_at(self, xm, ym): 

        name = self.cuele_type.get() 

        d  = float(self.d_var.get()) 

        sx = float(self.sx.get()) 

        sy = float(self.sy.get()) 

        rot= float(self.rot.get()) 

        vy = float(self.vy.get()) 

 

        if name == "Sarrois": 

            holes = cuele_sarrois_geom(center=(xm,ym), d=d, scale_x=sx, scale_y=sy, rot_deg=rot) 

            apply_series_sarrois(holes, d=d) 

        elif name == "Sueco": 

            holes = cuele_sueco_geom(center=(xm,ym), d=d, scale_x=sx, scale_y=sy, rot_deg=rot) 

            apply_series_sueco(holes, d=d) 

        elif name == "Coromant": 

            v  = 0.5*d; ax = 1.2*d; ay = 1.2*d 

            holes = cuele_coromant_geom(center=(xm,ym), v=v, ax=ax, ay=ay, skew=0.4*d, spread=1.4, 

                                        scale_x=sx, scale_y=sy, rot_deg=rot) 

            apply_series_coromant(holes, v=v, ax=ax, ay=ay, skew=0.4*d) 

        elif name == "Cuña 2x3": 

            holes = cuele_cuna_geom(center=(xm,ym), d=d, variante="2x3", sep_cols_factor=2.0, 

                                    scale_x=sx, scale_y=sy, rot_deg=rot) 

            apply_series_cuna(holes, variante="2x3", d=d) 

        elif name == "Cuña zigzag": 

            holes = cuele_cuna_geom(center=(xm,ym), d=d, variante="zigzag", 

                                    scale_x=sx, scale_y=sy, rot_deg=rot) 

            apply_series_cuna(holes, variante="zigzag", d=d) 

        elif name == "Abanico": 

            holes = cuele_abanico_geom(center=(xm,ym), d=d, dx_factor=0.5, 

                                       scale_x=sx, scale_y=sy, rot_deg=rot) 

            apply_series_abanico(holes, d=d) 

        elif name == "Bethune": 

            holes = cuele_bethune_geom(center=(xm,ym), d=d, dx_factor=1.2, 

                                       y_levels=(1.6,1.4,1.2,1.0,0.9), 

                                       invert_y=True, vy_factor=vy, 

                                       scale_x=sx, scale_y=sy, rot_deg=rot) 

            apply_series_bethune(holes, d=d, y_levels=(1.6,1.4,1.2,1.0,0.9), 

                                 invert_y=True, vy_factor=vy) 

        elif name == "Cuatro secciones": 

            holes = cuele_cuatro_secciones_geom(center=(xm,ym), D=d, D2=d, 

                                                k2=1.5, k3=1.5, k4=1.5, 

                                                add_mids_S4=True, 

                                                scale_x=sx, scale_y=sy, rot_deg=rot) 

            B1=1.5*d; B2=1.5*B1; B3=1.5*B2; B4=1.5*B3 

            A1=B1; A2=B1+B2; A3=B1+B2+B3; A4=B1+B2+B3+B4 

            apply_series_cuatro_secciones(holes, A1,A2,A3,A4, add_mids_S4=True) 

        else: 

            holes = [] 

        return holes 

 

    #  “Agregar” por paso 

    def _do_zap(self): 

        if not self.tunnel_poly: 

            messagebox.showwarning("Geometría", "Primero inserta la geometría (Paso 1).") 

            return 

        n = int(self.n_zap.get()) 

        holes = place_zapateras(self.tunnel_poly, n) 

        self.scene.add_holes(self._tag(holes, SP_ZAP, "zapatera")) 

        self.done_zap = True 

        self.draw() 

        self.btn_next.configure(state="normal") 

 

    def _do_cajas(self): 

        if not self.tunnel_poly: 

            messagebox.showwarning("Geometría", "Primero inserta la geometría (Paso 1).") 

            return 

        n = int(self.n_caja.get()) 

        holes = place_cajas(self.tunnel_poly, n) 

        self.scene.add_holes(self._tag(holes, SP_CAJAS, "caja")) 

        self.done_cajas = True 

        self.draw() 

        self.btn_next.configure(state="normal") 

 

    def _do_corona(self): 

        if not self.tunnel_poly: 

            messagebox.showwarning("Geometría", "Primero inserta la geometría (Paso 1).") 

            return 

        n = int(self.n_corona.get()) 

        holes = place_corona(self.tunnel_poly, n) 

        self.scene.add_holes(self._tag(holes, SP_CORONA, "corona")) 

        self.done_corona = True 

        self.draw() 

        self.btn_next.configure(state="normal") 

 

    def _do_aux(self): 

        if not self.tunnel_poly: 

            messagebox.showwarning("Geometría", "Primero inserta la geometría (Paso 1).") 

            return 

        nx = int(self.aux_nx.get()); ny = int(self.aux_ny.get()) 

        holes = place_aux_grid(self.tunnel_poly, nx, ny) 

        self.scene.add_holes(self._tag(holes, SP_AUX, "aux")) 

        self.done_aux = True 

        self.draw() 

        self.btn_next.configure(state="normal") 

 

    #  Borrado por paso 

    def _clear_step(self, step_to_clear): 

        # Si borras geometría: borra TODO y resetea 

        if step_to_clear == SP_GEOM: 

            self.scene = Scene() 

            self.tunnel_poly = [] 

            self.geom_index = None 

            self.step = SP_GEOM 

            self.done_geom = self.done_zap = self.done_cajas = False 

            self.done_corona = self.done_cueles = self.done_cc = self.done_aux = False 

            self._render_step_panel() 

            self._update_step_label() 

            self.draw() 

            return 

 

        # Borrar sólo los elementos de ese paso 

        self.scene.remove_holes_by_step(step_to_clear) 

 

        # Marcar paso como pendiente nuevamente 

        if step_to_clear == SP_ZAP: 

            self.done_zap = False 

        elif step_to_clear == SP_CAJAS: 

            self.done_cajas = False 

        elif step_to_clear == SP_CORONA: 

            self.done_corona = False 

        elif step_to_clear == SP_CUELES: 

            self.done_cueles = False 

        elif step_to_clear == SP_CC: 

            self.done_cc = False 

        elif step_to_clear == SP_AUX: 

            self.done_aux = False 

 

        # Si requiere que al borrar un paso también borre automáticamente 

        # TODOS los posteriores, descomenta este bloque: 

        """ 

        for st in range(step_to_clear+1, STEPS_MAX+1): 

            self.scene.remove_holes_by_step(st) 

            if st == SP_ZAP: self.done_zap = False 

            if st == SP_CAJAS: self.done_cajas = False 

            if st == SP_CORONA: self.done_corona = False 

            if st == SP_CUELES: self.done_cueles = False 

            if st == SP_CC: self.done_cc = False 

            if st == SP_AUX: self.done_aux = False 

        self.step = step_to_clear 

        """ 

 

        # Redibujar / refrescar panel del paso actual 

        self.draw() 

        self._render_step_panel() 

 

    # Utilidades 

    def clear_all(self): 
        self.scene = Scene() 
        self.tunnel_poly = [] 
        self.geom_index = None 
        self.step = SP_GEOM 
        self.done_geom = self.done_zap = self.done_cajas = False 
        self.done_corona = self.done_cueles = self.done_cc = self.done_aux = False 

        self._render_step_panel() 
        self._update_step_label() 
        self.draw() 

 

    def export_json(self): 

        try: 

            import json 

            data = {"holes": self.scene.holes, "tunnels": self.scene.tunnels} 

            with open("layout_export.json","w", encoding="utf-8") as f: 

                json.dump(data, f, ensure_ascii=False, indent=2) 

            messagebox.showinfo("Export", "Guardado layout_export.json") 

        except Exception as e: 

            messagebox.showerror("Export", str(e)) 
    
    def on_double_click(self, ev): 

        # Doble clic: si estamos en contracuele, usar centro de la perforación cercana 

        if self.step != SP_CC: 
           return 

        xm, ym = c2w(ev.x, ev.y) 
 
        # Encuentra la perforación más cercana para “snap” 

        idx = self.scene.nearest(xm, ym, tol_m=SNAP_TOL_M) 
        if idx is None: 
            # si no hay perforación cerca, no hacemos nada en doble-klik 
            return 

        # Centro exacto de la perforación 

        xm = self.scene.holes[idx]["x"] 

        ym = self.scene.holes[idx]["y"] 

 

        # Coloca contracuele con los parámetros seleccionados 

        cct = self.cc_type.get() 

        if cct == "Hexágono": 
            r = float(self.cc_hex_r.get()) 
            holes = place_contracuele_hex((xm, ym), r=r) 

        else: 
            w = float(self.cc_rect_w.get()); h = float(self.cc_rect_h.get()); m = int(self.cc_rect_n.get()) 
            holes = place_contracuele_rect((xm, ym), w=w, h=h, n_per_side=m) 

 
        self.scene.add_holes(self._tag(holes, SP_CC, "contracuele")) 
        self.done_cc = True 
        self.draw() 
        self._render_step_panel() 
 

if __name__ == "__main__": 

    App().mainloop() 