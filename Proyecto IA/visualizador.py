# visualizador_arbol.py
import tkinter as tk
from tkinter import ttk
import threading

# ---------- Utilidades para medir el árbol ----------
def _altura(nodo):
    if nodo is None:
        return 0
    return 1 + max(_altura(nodo.izquierda), _altura(nodo.derecha))

def _contar_nodos(nodo):
    if nodo is None:
        return 0
    return 1 + _contar_nodos(nodo.izquierda) + _contar_nodos(nodo.derecha)

# In-order para posicionar por columnas (x) y niveles (y)
def _asignar_posiciones_inorder(nodo, nivel, dx, dy, margen_x, margen_y, col_ref, posiciones):
    if nodo is None:
        return
    _asignar_posiciones_inorder(nodo.izquierda, nivel + 1, dx, dy, margen_x, margen_y, col_ref, posiciones)
    x = margen_x + col_ref[0] * dx
    y = margen_y + nivel * dy
    posiciones[nodo] = (x, y)
    col_ref[0] += 1
    _asignar_posiciones_inorder(nodo.derecha, nivel + 1, dx, dy, margen_x, margen_y, col_ref, posiciones)

def _formatear_etiqueta(nodo):
    # Mostrar palabra(s) y valor: si es lista, mostramos primeras 2…
    if isinstance(nodo.palabra, list):
        if len(nodo.palabra) <= 2:
            palabras = ", ".join(nodo.palabra)
        else:
            palabras = ", ".join(nodo.palabra[:2]) + "…"
    else:
        palabras = str(nodo.palabra)
    # antes: return f"{palabras}\n{nodo.valor}"
    return f"{palabras}\n{nodo.suma_ascii}"


# ---------- Ventana con Canvas y barras de desplazamiento ----------
def _crear_canvas_scrollable(root, width, height):
    frame = ttk.Frame(root)
    frame.pack(fill="both", expand=True)

    hscroll = ttk.Scrollbar(frame, orient="horizontal")
    vscroll = ttk.Scrollbar(frame, orient="vertical")
    canvas = tk.Canvas(
        frame,
        bg="#0b1020",
        scrollregion=(0, 0, width, height),
        xscrollcommand=hscroll.set,
        yscrollcommand=vscroll.set,
        highlightthickness=0
    )
    hscroll.config(command=canvas.xview)
    vscroll.config(command=canvas.yview)

    canvas.grid(row=0, column=0, sticky="nsew")
    vscroll.grid(row=0, column=1, sticky="ns")
    hscroll.grid(row=1, column=0, sticky="ew")
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)
    return canvas

# ---------- Dibujo ----------
def _dibujar_arista(canvas, x1, y1, x2, y2):
    canvas.create_line(x1, y1, x2, y2, width=2, fill="#a0b4ff")

def _dibujar_nodo(canvas, x, y, etiqueta):
    rx, ry = 38, 24  # radio x/y del óvalo
    canvas.create_oval(x - rx, y - ry, x + rx, y + ry, fill="#233a7a", outline="#cce1ff", width=2)
    canvas.create_text(x, y, text=etiqueta, font=("Arial", 10, "bold"), fill="#ffffff", justify="center")

def _dibujar_arbol(canvas, raiz, posiciones):
    # Primero aristas
    for nodo, (x, y) in posiciones.items():
        if nodo.izquierda:
            xi, yi = posiciones[nodo.izquierda]
            _dibujar_arista(canvas, x, y + 22, xi, yi - 22)
        if nodo.derecha:
            xd, yd = posiciones[nodo.derecha]
            _dibujar_arista(canvas, x, y + 22, xd, yd - 22)
    # Luego nodos
    for nodo, (x, y) in posiciones.items():
        _dibujar_nodo(canvas, x, y, _formatear_etiqueta(nodo))

# ---------- Zoom helpers ----------
def _configurar_zoom(canvas, root):
    """
    Agrega soporte de zoom con Ctrl + rueda del mouse.
    - Windows/macOS: <Control-MouseWheel> con event.delta (+/-120).
    - Linux (X11): <Control-Button-4> (acerca), <Control-Button-5> (aleja).
    El zoom se hace alrededor de la posición del puntero del mouse.
    """

    # Parámetros de zoom
    zoom_min = 0.25
    zoom_max = 3.5
    zoom_step_in = 1.1   # factor al acercar
    zoom_step_out = 1/zoom_step_in
    # Estado del zoom actual (escala acumulada)
    state = {"scale": 1.0}

    def _zoom(canvas, factor, event):
        # Limitar zoom total
        new_scale = state["scale"] * factor
        if new_scale < zoom_min or new_scale > zoom_max:
            return

        # Coordenadas del mouse en el sistema del canvas
        x = canvas.canvasx(event.x)
        y = canvas.canvasy(event.y)

        # Escalar todo alrededor del puntero
        canvas.scale("all", x, y, factor, factor)

        # Actualizar bbox/scrollregion
        bbox = canvas.bbox("all")
        if bbox:
            canvas.configure(scrollregion=bbox)

        # Ajustar vista para mantener el punto del puntero “anclado”
        # Convertimos a fracciones del scrollregion:
        # (esto da una experiencia más estable al hacer zoom)
        vx = (x - canvas.xview()[0] * (bbox[2] - bbox[0])) / (bbox[2] - bbox[0])
        vy = (y - canvas.yview()[0] * (bbox[3] - bbox[1])) / (bbox[3] - bbox[1])
        # No movemos explicitamente, tk se encarga bastante bien al escalar sobre el puntero.

        state["scale"] = new_scale

    # Windows / macOS
    def _on_mousewheel(event):
        if event.state & 0x0004:  # Control presionado (más robusto que solo binding)
            if event.delta > 0:
                _zoom(canvas, zoom_step_in, event)
            elif event.delta < 0:
                _zoom(canvas, zoom_step_out, event)

    # Linux (rueda como botones 4/5)
    def _on_button4(event):
        # Ctrl + rueda arriba → acercar
        if event.state & 0x0004:
            _zoom(canvas, zoom_step_in, event)

    def _on_button5(event):
        # Ctrl + rueda abajo → alejar
        if event.state & 0x0004:
            _zoom(canvas, zoom_step_out, event)

    # Bindings
    root.bind("<Control-MouseWheel>", _on_mousewheel)  # Win/macOS
    canvas.bind("<Control-Button-4>", _on_button4)     # Linux
    canvas.bind("<Control-Button-5>", _on_button5)     # Linux

    # (Opcional) Cursor de mano cuando Ctrl está presionado (feedback visual)
    def _ctrl_down(_):
        canvas.config(cursor="hand2")
    def _ctrl_up(_):
        canvas.config(cursor="")
    root.bind("<Control_L>", _ctrl_down)
    root.bind("<KeyRelease-Control_L>", _ctrl_up)
    root.bind("<Control_R>", _ctrl_down)
    root.bind("<KeyRelease-Control_R>", _ctrl_up)

# ---------- API pública ----------
def mostrar_arbol(arbol, titulo="Árbol BST (visualización)"):
    """
    Abre una ventana y dibuja el árbol en un Canvas con scroll y zoom (Ctrl + rueda).
    arbol: instancia de ArbolBinario (con atributo 'raiz').
    """
    if arbol is None or arbol.raiz is None:
        print("⚠️ No hay árbol para visualizar.")
        return

    # Parámetros de layout
    altura = _altura(arbol.raiz)
    dx = 110   # separación horizontal entre columnas
    dy = 100   # separación vertical entre niveles
    margen_x = 60
    margen_y = 50

    # Calcular posiciones por in-order (x por columna, y por nivel)
    posiciones = {}
    _asignar_posiciones_inorder(arbol.raiz, 0, dx, dy, margen_x, margen_y, [0], posiciones)

    # Tamaño base del canvas según posiciones
    max_x = max((pos[0] for pos in posiciones.values()), default=0)
    width = max(900, int(max_x + margen_x + dx))
    height = max(600, int(margen_y + (altura + 1) * dy))

    root = tk.Tk()
    root.title(titulo)
    root.geometry("1000x700")

    canvas = _crear_canvas_scrollable(root, width, height)
    _dibujar_arbol(canvas, arbol.raiz, posiciones)

    # Ajustar scrollregion exacto al contenido
    bbox = canvas.bbox("all")
    if bbox:
        canvas.configure(scrollregion=bbox)

    # Configurar zoom con Ctrl + rueda
    _configurar_zoom(canvas, root)

    # Centrar vista al inicio (opcional)
    canvas.xview_moveto(0.0)
    canvas.yview_moveto(0.0)

    root.mainloop()

def mostrar_arbol_async(arbol, titulo="Árbol BST (visualización)"):
    """
    Abre la ventana Tk en un hilo separado para que no bloquee el programa principal.
    Nota: Todas las llamadas a Tk deben ocurrir dentro de este hilo.
    """
    hilo = threading.Thread(target=mostrar_arbol, args=(arbol, titulo), daemon=True)
    hilo.start()
    
    
    
    
    
    