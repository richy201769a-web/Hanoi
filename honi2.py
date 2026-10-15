"""
Torre de Hanoi GRÁFICA en Python (tkinter) usando pilas (stacks).

Cada varilla es una pila (lista de Python):
    append() -> push | pop() -> pop | [-1] -> peek

Se permiten de 1 a 64 discos. Si escribes más de 64 sale un mensaje de error.
"""

import colorsys
import time
import tkinter as tk
from tkinter import ttk, messagebox

# ---------- Configuración ----------
MAX_DISCOS = 67                  # límite permitido
AVISO_DISCOS = 20                # a partir de aquí se avisa que tardará muchísimo
ANCHO, ALTO = 760, 400
Y_BASE = 350                     # donde se apoyan los discos
ALTO_TORRE = 270                 # altura de las varillas
X_VARILLAS = {"A": 140, "B": 380, "C": 620}
FONDO = "#12141c"
COLOR_MADERA = "#8d6e63"


def generar_movimientos(n, origen, auxiliar, destino):
    """Genera (yield) cada movimiento de la solución recursiva, uno por uno."""
    if n == 0:
        return
    yield from generar_movimientos(n - 1, origen, destino, auxiliar)
    yield (origen, destino)
    yield from generar_movimientos(n - 1, auxiliar, origen, destino)


def color_disco(numero, total):
    """Cada disco recibe un color distinto (arcoíris)."""
    r, g, b = colorsys.hsv_to_rgb(numero / (total + 1), 0.65, 0.95)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


class AppHanoi:
    def __init__(self, ventana):
        """Crea la ventana, los controles y deja la torre lista."""
        self.ventana = ventana
        ventana.title("Torre de Hanoi - con pilas")
        ventana.configure(bg=FONDO)
        ventana.resizable(False, False)

        self.num_discos = 4          # último valor válido
        self.generador = None
        self.corriendo = False
        self.id_after = None         # para poder cancelar la animación

        self.canvas = tk.Canvas(ventana, width=ANCHO, height=ALTO,
                                bg=FONDO, highlightthickness=0)
        self.canvas.pack(padx=10, pady=(10, 0))

        self.crear_controles()
        self.reiniciar()

    def crear_controles(self):
        """Botones, selector de discos y velocidad."""
        barra = tk.Frame(self.ventana, bg=FONDO)
        barra.pack(pady=8)

        tk.Label(barra, text=f"Discos (1-{MAX_DISCOS}):", bg=FONDO, fg="white").grid(row=0, column=0)
        self.var_discos = tk.StringVar(value=str(self.num_discos))
        caja = tk.Spinbox(barra, from_=1, to=MAX_DISCOS, width=5,
                          textvariable=self.var_discos, command=self.cambiar_discos)
        caja.grid(row=0, column=1, padx=6)
        caja.bind("<Return>", self.cambiar_discos)     # al escribir y dar Enter
        caja.bind("<FocusOut>", self.cambiar_discos)   # o al salir de la caja

        tk.Label(barra, text="Velocidad:", bg=FONDO, fg="white").grid(row=0, column=2)
        self.var_velocidad = tk.IntVar(value=300)      # milisegundos entre movimientos
        ttk.Scale(barra, from_=900, to=5, variable=self.var_velocidad,
                  length=140).grid(row=0, column=3, padx=6)

        ttk.Button(barra, text="▶ Resolver", command=self.resolver).grid(row=0, column=4, padx=4)
        ttk.Button(barra, text="↺ Reiniciar", command=self.reiniciar).grid(row=0, column=5, padx=4)
        ttk.Button(barra, text="⏱ Medir tiempos", command=self.medir_tiempos).grid(row=0, column=6, padx=4)

        self.texto_info = tk.StringVar()
        tk.Label(self.ventana, textvariable=self.texto_info, bg=FONDO, fg="#80deea",
                 font=("Consolas", 11), justify="left", height=4).pack(pady=(0, 10))

    def leer_num_discos(self):
        """Lee la caja de discos y valida: entero entre 1 y 64 (si no, muestra mensaje)."""
        try:
            n = int(self.var_discos.get().strip())
        except ValueError:
            self.var_discos.set(str(self.num_discos))
            messagebox.showwarning("Dato inválido",
                                   f"Escribe un número entero entre 1 y {MAX_DISCOS}.")
            return self.num_discos

        if n > MAX_DISCOS:
            self.var_discos.set(str(MAX_DISCOS))
            messagebox.showwarning("Demasiados discos",
                                   f"No se permiten más de {MAX_DISCOS} discos.")
            return MAX_DISCOS
        if n < 1:
            self.var_discos.set("1")
            messagebox.showwarning("Dato inválido", "Debe haber al menos 1 disco.")
            return 1
        return n

    def cambiar_discos(self, evento=None):
        """Reinicia la torre solo si el número de discos realmente cambió."""
        if self.leer_num_discos() != self.num_discos:
            self.reiniciar()

    def reiniciar(self):
        """Detiene la animación y vuelve a poner todos los discos en A."""
        self.corriendo = False
        if self.id_after is not None:
            self.ventana.after_cancel(self.id_after)
            self.id_after = None
        self.generador = None

        n = self.leer_num_discos()
        self.num_discos = n
        self.varillas = {"A": list(range(n, 0, -1)), "B": [], "C": []}
        self.movimientos = 0
        self.actualizar_info()
        self.dibujar()

    def actualizar_info(self, extra=""):
        """Muestra el contador de movimientos (y un aviso si son muchos discos)."""
        total = 2 ** self.num_discos - 1
        texto = f"Movimientos: {self.movimientos:,} / {total:,}{extra}"
        if self.num_discos > AVISO_DISCOS:
            texto += ("\n⚠ Muchos discos: la animación tardará muchísimo."
                      "\n   Usa ↺ Reiniciar para detenerla.")
        self.texto_info.set(texto)

    def dibujar(self):
        """Redibuja base, varillas y los discos de cada pila."""
        c = self.canvas
        n = self.num_discos
        alto_disco = min(24, (ALTO_TORRE - 10) / n)   # se encogen si hay muchos

        c.delete("all")
        c.create_rectangle(20, Y_BASE, ANCHO - 20, Y_BASE + 14,
                           fill=COLOR_MADERA, outline="")
        for nombre, x in X_VARILLAS.items():
            c.create_rectangle(x - 5, Y_BASE - ALTO_TORRE, x + 5, Y_BASE,
                               fill="#bcaaa4", outline="")
            c.create_text(x, Y_BASE + 32, text=nombre, fill="white",
                          font=("Arial", 16, "bold"))
            for nivel, disco in enumerate(self.varillas[nombre]):
                mitad = (30 + disco * 150 / n) / 2
                y_abajo = Y_BASE - nivel * alto_disco
                c.create_rectangle(x - mitad, y_abajo - alto_disco, x + mitad, y_abajo,
                                   fill=color_disco(disco, n),
                                   outline="#ffffff" if alto_disco >= 8 else "")
                if alto_disco >= 14:                  # el número solo si cabe
                    c.create_text(x, y_abajo - alto_disco / 2, text=str(disco),
                                  fill="#222", font=("Arial", 9, "bold"))

    def mover_disco(self, origen, destino):
        """pop() del origen y push() en el destino."""
        disco = self.varillas[origen].pop()
        self.varillas[destino].append(disco)
        self.movimientos += 1

    def resolver(self):
        """Inicia la animación de la solución."""
        if self.corriendo:
            return
        self.cambiar_discos()                 # por si escribió un número sin dar Enter
        if self.movimientos > 0:
            self.reiniciar()
        self.corriendo = True
        self.generador = generar_movimientos(self.num_discos, "A", "B", "C")
        self.paso()

    def paso(self):
        """Hace UN movimiento, redibuja y se programa a sí mismo para el siguiente."""
        if not self.corriendo:
            return
        try:
            origen, destino = next(self.generador)
        except StopIteration:
            self.corriendo = False
            self.actualizar_info("  ¡Resuelto!")
            return
        self.mover_disco(origen, destino)
        self.dibujar()
        self.actualizar_info(f"   ({origen} → {destino})")
        self.id_after = self.ventana.after(int(self.var_velocidad.get()), self.paso)

    def medir_tiempos(self):
        """Mide el tiempo real (sin dibujar nada) para varios números de discos."""
        self.reiniciar()
        lineas = []
        for n in (5, 10, 15, 20):
            pilas = {"A": list(range(n, 0, -1)), "B": [], "C": []}
            inicio = time.perf_counter()
            for origen, destino in generar_movimientos(n, "A", "B", "C"):
                pilas[destino].append(pilas[origen].pop())
            segundos = time.perf_counter() - inicio
            lineas.append(f"{n:>2} discos | {2 ** n - 1:>9,} movs | {segundos:.4f} s")
        self.texto_info.set("\n".join(lineas))


if __name__ == "__main__":
    raiz = tk.Tk()
    AppHanoi(raiz)
    raiz.mainloop()