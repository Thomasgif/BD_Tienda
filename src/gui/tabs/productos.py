import customtkinter as ctk
from database.connection import obtener_productos


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

        # ── Top bar ────────────────────────────────────────────────────────────
        top_bar = ctk.CTkFrame(parent_frame, fg_color="transparent")
        top_bar.pack(fill="x", padx=40, pady=(0, 20))

        ctk.CTkLabel(
            top_bar, text="Inventario de Productos",
            font=("Arial", 18, "bold"), text_color="#aaaaaa"
        ).pack(side="left")

        self.entry_buscar = ctk.CTkEntry(
            top_bar, placeholder_text="Buscar nombre o ref...", width=200
        )
        self.entry_buscar.pack(side="right")
        self.entry_buscar.bind("<KeyRelease>", self.filtrar)

        # ── Scrollable product list ────────────────────────────────────────────
        self.scroll = ctk.CTkScrollableFrame(
            parent_frame, fg_color="#0a0a0a", corner_radius=10
        )
        self.scroll.pack(fill="both", expand=True, padx=40, pady=(0, 20))

        self.cargar()

    # ── Public API ─────────────────────────────────────────────────────────────

    def cargar(self):
        """Fetch products from DB and re-render."""
        try:
            self.todos_productos = obtener_productos(self.controller.rol)
            self.filtrar()
        except Exception as e:
            self._limpiar()
            ctk.CTkLabel(
                self.scroll, text=f"Error cargando productos:\n{e}",
                text_color="#ff4d4d"
            ).pack(pady=20)

    def filtrar(self, event=None):
        query = self.entry_buscar.get().lower()
        filtrados = self.todos_productos if not query else [
            p for p in self.todos_productos
            if query in p['nombre'].lower() or query in p['referencia'].lower()
        ]
        self.render(filtrados)

    # ── Private helpers ────────────────────────────────────────────────────────

    def _limpiar(self):
        for w in self.scroll.winfo_children():
            w.destroy()

    def render(self, productos):
        self._limpiar()
        if not productos:
            ctk.CTkLabel(
                self.scroll, text="No se encontraron productos.",
                text_color="#888888"
            ).pack(pady=20)
            return

        rol = self.controller.rol
        table = ctk.CTkFrame(self.scroll, fg_color="transparent")
        table.pack(fill="x", expand=True)

        # Column weights
        table.grid_columnconfigure(0, weight=1)
        table.grid_columnconfigure(1, weight=2)
        table.grid_columnconfigure(2, weight=1)
        table.grid_columnconfigure(3, weight=1)
        if rol == 1:
            table.grid_columnconfigure(4, weight=1)

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

        for idx, prod in enumerate(productos):
            row_idx = idx + 1
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
