import threading
import customtkinter as ctk
from database.connection import obtener_productos

_BATCH = 30  # Productos renderizados por frame de animación


class ProductosTab:
    """Manages the Productos inventory tab content."""

    def __init__(self, parent_frame, controller):
        """
        Args:
            parent_frame: The CTkFrame where this tab's content is placed.
            controller:   The VendedorWindow instance (provides .rol, callbacks).
        """
        self.controller = controller
        self.todos_productos = []
        self._last_query = None  # Evita re-renders innecesarios al filtrar

        # ── Top bar ────────────────────────────────────────────────────────────
        top_bar = ctk.CTkFrame(parent_frame, fg_color="transparent")
        top_bar.pack(fill="x", padx=40, pady=(0, 20))

        ctk.CTkLabel(
            top_bar, text="Inventario de Productos",
            font=("Arial", 18, "bold"), text_color="#aaaaaa"
        ).pack(side="left")

        ctk.CTkButton(
            top_bar, text="↻ Actualizar",
            font=("Arial", 12, "bold"),
            fg_color="#1e1e1e", hover_color="#333333", text_color="#1DB954",
            width=100, command=self.cargar
        ).pack(side="right")

        self.entry_buscar = ctk.CTkEntry(
            top_bar, placeholder_text="Buscar nombre o ref...", width=200
        )
        self.entry_buscar.pack(side="right", padx=(0, 10))
        self.entry_buscar.bind("<KeyRelease>", self.filtrar)

        # ── Scrollable product list ────────────────────────────────────────────
        self.scroll = ctk.CTkScrollableFrame(
            parent_frame, fg_color="#0a0a0a", corner_radius=10
        )
        self.scroll.pack(fill="both", expand=True, padx=40, pady=(0, 20))

        # Carga asíncrona al construir el tab
        self.cargar()

    # ── Public API ─────────────────────────────────────────────────────────────

    def cargar(self):
        """Fetch products from DB asynchronously, then re-render."""
        self._limpiar()
        ctk.CTkLabel(
            self.scroll, text="Cargando productos...", text_color="#888888",
            font=("Arial", 14)
        ).pack(pady=30)

        def _fetch():
            try:
                data = obtener_productos(self.controller.rol)
                self.scroll.after(0, lambda d=data: self._on_loaded(d))
            except Exception as e:
                self.scroll.after(0, lambda err=str(e): self._on_error(err))

        threading.Thread(target=_fetch, daemon=True).start()

    def filtrar(self, event=None):
        query = self.entry_buscar.get().strip().lower()
        if query == self._last_query:
            return  # Sin cambio real: evitar re-render
        self._last_query = query

        filtrados = self.todos_productos if not query else [
            p for p in self.todos_productos
            if query in p['nombre'].lower() or query in p['referencia'].lower()
        ]
        self._render_batch(filtrados)

    # ── Private helpers ────────────────────────────────────────────────────────

    def _on_loaded(self, data):
        self.todos_productos = data
        # Actualizar caché del controller para que VentasTab lo reutilice
        self.controller.todos_productos = data
        self._last_query = None
        self.filtrar()

    def _on_error(self, msg):
        self._limpiar()
        ctk.CTkLabel(
            self.scroll, text=f"Error cargando productos:\n{msg}",
            text_color="#ff4d4d"
        ).pack(pady=20)

    def _limpiar(self):
        for w in self.scroll.winfo_children():
            w.destroy()

    def _render_batch(self, productos):
        """Render products in batches to keep the UI responsive."""
        self._limpiar()

        if not productos:
            ctk.CTkLabel(
                self.scroll, text="No se encontraron productos.",
                text_color="#888888"
            ).pack(pady=20)
            return

        rol = self.controller.rol

        # Contenedor de tabla compartido entre lotes
        table = ctk.CTkFrame(self.scroll, fg_color="transparent")
        table.pack(fill="x", expand=True)

        # Pesos de columnas
        table.grid_columnconfigure(0, weight=1)
        table.grid_columnconfigure(1, weight=2)
        table.grid_columnconfigure(2, weight=1)
        table.grid_columnconfigure(3, weight=1)
        if rol == 1:
            table.grid_columnconfigure(4, weight=1)

        # Encabezados
        hc = "#1e1e1e"
        for col_idx, text in enumerate(["Referencia", "Producto", "Precio Venta", "Stock (Bodega)"]):
            ctk.CTkLabel(
                table, text=text,
                font=("Arial", 14, "bold"), text_color="#1DB954",
                fg_color=hc, anchor="w", padx=10, pady=10
            ).grid(row=0, column=col_idx, sticky="nsew")
        if rol == 1:
            ctk.CTkLabel(
                table, text="Acciones",
                font=("Arial", 14, "bold"), text_color="#1DB954",
                fg_color=hc, anchor="w", padx=10, pady=10
            ).grid(row=0, column=4, sticky="nsew")

        # Renderizar el primer lote inmediatamente
        self._render_rows(table, productos, rol, 0)

    def _render_rows(self, table, productos, rol, start_idx):
        """Render one batch of rows, then schedule the next batch via after()."""
        end_idx = min(start_idx + _BATCH, len(productos))

        for idx in range(start_idx, end_idx):
            prod = productos[idx]
            row_idx = idx + 1  # fila 0 es el encabezado
            rc = "#121212" if idx % 2 == 0 else "#0a0a0a"

            ctk.CTkLabel(table, text=prod['referencia'], text_color="#cccccc",
                         fg_color=rc, anchor="w", padx=10, pady=8
                         ).grid(row=row_idx, column=0, sticky="nsew")
            ctk.CTkLabel(table, text=prod['nombre'], text_color="#ffffff",
                         fg_color=rc, anchor="w", padx=10, pady=8
                         ).grid(row=row_idx, column=1, sticky="nsew")
            ctk.CTkLabel(table, text=f"${prod['precio_venta']:,.2f}", text_color="#cccccc",
                         fg_color=rc, anchor="w", padx=10, pady=8
                         ).grid(row=row_idx, column=2, sticky="nsew")

            stock = prod['bodega']
            sc = "#cccccc" if stock > 0 else "#ff4d4d"
            ctk.CTkLabel(table, text=str(stock) if stock > 0 else "Agotado",
                         text_color=sc, fg_color=rc, anchor="w", padx=10, pady=8
                         ).grid(row=row_idx, column=3, sticky="nsew")

            if rol == 1:
                af = ctk.CTkFrame(table, fg_color=rc, corner_radius=0)
                af.grid(row=row_idx, column=4, sticky="nsew")
                ctk.CTkButton(
                    af, text="✏ Editar Valor",
                    font=("Arial", 11, "bold"), width=95, height=24,
                    fg_color="#1e1e1e", hover_color="#2b2b2b", text_color="#1DB954",
                    command=lambda p=prod: self.controller._abrir_actualizar_precio_producto(p)
                ).pack(padx=10, pady=5, anchor="w")

        # Si quedan más productos, programar el siguiente lote
        if end_idx < len(productos):
            table.after(0, lambda: self._render_rows(table, productos, rol, end_idx))
