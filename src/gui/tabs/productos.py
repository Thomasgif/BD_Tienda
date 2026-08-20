import threading
import customtkinter as ctk
from database.connection import obtener_productos

_BATCH = 30  # Productos renderizados por lote


class ProductosTab:
    """Manages the Productos inventory tab content."""

    def __init__(self, parent_frame, controller):
        """
        Args:
            parent_frame: The CTkFrame where this tab's content is placed.
            controller:   The VendedorWindow instance (provides .rol, callbacks).
        """
        self.controller = controller
        self.todos_productos = getattr(self.controller, 'todos_productos', []) or []
        self._last_query = None
        self._render_token = 0
        self._after_id = None
        self._is_loading = False

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
            width=100, command=lambda: self.cargar(force=True)
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

        # Si ya existen productos en caché, renderizarlos inmediatamente
        if self.todos_productos:
            self._render_batch(self.todos_productos)
        else:
            self.cargar()

    def on_show(self):
        """Called whenever the user switches back to this tab."""
        cached = getattr(self.controller, 'todos_productos', [])
        if cached:
            if not self.todos_productos or len(cached) != len(self.todos_productos):
                self.todos_productos = cached
                self._last_query = None
                self.filtrar()
        elif not self.todos_productos and not self._is_loading:
            self.cargar()
        self.scroll.update_idletasks()

    # ── Public API ─────────────────────────────────────────────────────────────

    def cargar(self, force=False):
        """Fetch products from DB asynchronously, then re-render."""
        if self._is_loading:
            return
        self._is_loading = True

        self._cancel_pending_render()

        if not self.todos_productos or force:
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
            return
        self._last_query = query

        filtrados = self.todos_productos if not query else [
            p for p in self.todos_productos
            if query in str(p.get('nombre', '')).lower() or query in str(p.get('referencia', '')).lower()
        ]
        self._render_batch(filtrados)

    # ── Private helpers ────────────────────────────────────────────────────────

    def _on_loaded(self, data):
        self._is_loading = False
        self.todos_productos = data
        self.controller.todos_productos = data
        self._last_query = None
        self.filtrar()

    def _on_error(self, msg):
        self._is_loading = False
        self._cancel_pending_render()
        self._limpiar()
        ctk.CTkLabel(
            self.scroll, text=f"Error cargando productos:\n{msg}",
            text_color="#ff4d4d"
        ).pack(pady=20)

    def _cancel_pending_render(self):
        self._render_token += 1
        if self._after_id:
            try:
                self.scroll.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _limpiar(self):
        self._cancel_pending_render()
        for w in self.scroll.winfo_children():
            w.destroy()

    def _render_batch(self, productos):
        """Render products in batches to keep UI responsive without ghosting."""
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

        token = self._render_token
        self._render_rows(table, productos, rol, 0, token)

    def _render_rows(self, table, productos, rol, start_idx, token):
        if token != self._render_token:
            return

        end_idx = min(start_idx + _BATCH, len(productos))

        for idx in range(start_idx, end_idx):
            if token != self._render_token:
                return

            prod = productos[idx]
            row_idx = idx + 1
            rc = "#121212" if idx % 2 == 0 else "#0a0a0a"

            ctk.CTkLabel(table, text=str(prod.get('referencia', '')), text_color="#cccccc",
                         fg_color=rc, anchor="w", padx=10, pady=8
                         ).grid(row=row_idx, column=0, sticky="nsew")
            ctk.CTkLabel(table, text=str(prod.get('nombre', '')), text_color="#ffffff",
                         fg_color=rc, anchor="w", padx=10, pady=8
                         ).grid(row=row_idx, column=1, sticky="nsew")
            ctk.CTkLabel(table, text=f"${float(prod.get('precio_venta', 0) or 0):,.2f}", text_color="#cccccc",
                         fg_color=rc, anchor="w", padx=10, pady=8
                         ).grid(row=row_idx, column=2, sticky="nsew")

            stock = int(prod.get('bodega', 0) or 0)
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

        if end_idx < len(productos) and token == self._render_token:
            self._after_id = self.scroll.after(
                10, lambda: self._render_rows(table, productos, rol, end_idx, token)
            )
