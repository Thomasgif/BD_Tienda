import customtkinter as ctk
from database.connection import obtener_proveedores_completos, obtener_compras_sin_envio_por_proveedor


class ProveedoresTab:
    """Manages the Proveedores tab: list panel + detail panel."""

    def __init__(self, parent_frame, controller):
        self.controller = controller
        self._proveedores_data = []

        # ── Top bar ────────────────────────────────────────────────────────────
        top_bar = ctk.CTkFrame(parent_frame, fg_color="transparent")
        top_bar.pack(fill="x", padx=40, pady=(0, 16))

        ctk.CTkLabel(
            top_bar, text="Proveedores",
            font=("Arial", 18, "bold"), text_color="#aaaaaa"
        ).pack(side="left")

        ctk.CTkButton(
            top_bar, text="↻ Actualizar",
            font=("Arial", 12, "bold"),
            fg_color="#1e1e1e", hover_color="#333333",
            text_color="#1DB954", width=110,
            command=self.cargar
        ).pack(side="right")

        if controller.rol == 1:
            ctk.CTkButton(
                top_bar, text="+ Nuevo Proveedor",
                font=("Arial", 13, "bold"),
                fg_color="#1DB954", hover_color="#179643",
                text_color="#000000", width=155,
                command=self._abrir_nuevo_proveedor
            ).pack(side="right", padx=(0, 10))

        # ── Two-column layout ──────────────────────────────────────────────────
        main = ctk.CTkFrame(parent_frame, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=40, pady=(0, 20))

        # Left panel — list
        left = ctk.CTkFrame(main, fg_color="#0a0a0a", corner_radius=15, width=280)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)

        ctk.CTkLabel(
            left, text="Lista de Proveedores",
            font=("Arial", 14, "bold"), text_color="#666666"
        ).pack(padx=16, pady=(14, 8), anchor="w")

        self.scroll = ctk.CTkScrollableFrame(
            left, fg_color="#0a0a0a", corner_radius=0
        )
        self.scroll.pack(fill="both", expand=True, padx=6, pady=(0, 10))

        # Right panel — detail
        self.right = ctk.CTkFrame(main, fg_color="#0a0a0a", corner_radius=15)
        self.right.pack(side="right", fill="both", expand=True, padx=(10, 0))

        ctk.CTkLabel(
            self.right,
            text="Selecciona un proveedor para ver\nsus compras pendientes de envío.",
            font=("Arial", 15), text_color="#444444"
        ).pack(expand=True)

        self.cargar()

    # ── Public API ─────────────────────────────────────────────────────────────

    def cargar(self):
        try:
            self._proveedores_data = obtener_proveedores_completos(self.controller.rol)
        except Exception as e:
            self._proveedores_data = []
            print(f"Error al cargar proveedores: {e}")
        self._render_lista(self._proveedores_data)

    # ── Rendering ──────────────────────────────────────────────────────────────

    def _render_lista(self, proveedores):
        for w in self.scroll.winfo_children():
            w.destroy()

        if not proveedores:
            ctk.CTkLabel(
                self.scroll, text="No hay proveedores registrados.",
                text_color="#555555"
            ).pack(pady=20)
            return

        for idx, p in enumerate(proveedores):
            bg = "#161616" if idx % 2 == 0 else "#111111"
            row = ctk.CTkFrame(self.scroll, fg_color=bg, corner_radius=8)
            row.pack(fill="x", pady=3, padx=4)
            row.grid_columnconfigure(0, weight=1)

            ctk.CTkButton(
                row,
                text=f"  {p['nombre']}  —  NIT: {p.get('nit') or 'N/A'}",
                font=("Arial", 13),
                fg_color="transparent", hover_color="#1e2b1e",
                text_color="#ffffff", anchor="w", height=38,
                command=lambda prov=p: self._mostrar_detalle(prov)
            ).grid(row=0, column=0, sticky="ew", padx=(4, 0), pady=4)

            if self.controller.rol == 1:
                ctk.CTkButton(
                    row, text="✏", width=34, height=34,
                    font=("Arial", 14),
                    fg_color="#1e2b1e", hover_color="#2d472d", text_color="#1DB954",
                    command=lambda prov=p: self._editar_proveedor(prov)
                ).grid(row=0, column=1, padx=(4, 8), pady=4)

    def _mostrar_detalle(self, proveedor):
        for w in self.right.winfo_children():
            w.destroy()

        # Info section
        info = ctk.CTkFrame(self.right, fg_color="transparent")
        info.pack(fill="x", padx=20, pady=(20, 8))

        name_row = ctk.CTkFrame(info, fg_color="transparent")
        name_row.pack(fill="x")

        ctk.CTkLabel(
            name_row, text=proveedor.get('nombre', ''),
            font=("Arial", 22, "bold"), text_color="#ffffff"
        ).pack(side="left", anchor="w")

        if self.controller.rol == 1:
            ctk.CTkButton(
                name_row, text="+ Nueva Compra",
                font=("Arial", 13, "bold"),
                fg_color="#1DB954", hover_color="#179643",
                text_color="#000000", height=34,
                command=lambda: self._abrir_nueva_compra(proveedor)
            ).pack(side="right")

        for label, key in [("NIT", "nit"), ("Teléfono", "telefono"),
                           ("Correo", "correo"), ("Dirección", "direccion")]:
            ctk.CTkLabel(
                info, text=f"{label}: {proveedor.get(key) or 'N/A'}",
                font=("Arial", 13), text_color="#888888"
            ).pack(anchor="w", pady=1)

        ctk.CTkFrame(self.right, height=1, fg_color="#2a2a2a").pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            self.right,
            text="Compras Pendientes (sin envío asignado)",
            font=("Arial", 15, "bold"), text_color="#1DB954"
        ).pack(anchor="w", padx=20, pady=(0, 8))

        scroll_compras = ctk.CTkScrollableFrame(
            self.right, fg_color="#080808", corner_radius=10
        )
        scroll_compras.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        try:
            compras = obtener_compras_sin_envio_por_proveedor(
                proveedor['idProveedor'], self.controller.rol
            )

            if not compras:
                ctk.CTkLabel(
                    scroll_compras,
                    text="Sin compras pendientes para este proveedor.",
                    text_color="#555555"
                ).pack(pady=24)
            else:
                for idx, c in enumerate(compras):
                    bg = "#181818" if idx % 2 == 0 else "#111111"
                    card = ctk.CTkFrame(scroll_compras, fg_color=bg, corner_radius=10)
                    card.pack(fill="x", pady=5)

                    fecha = c.get('fechacompra', 'N/A')
                    if hasattr(fecha, 'strftime'):
                        fecha = fecha.strftime('%Y-%m-%d %H:%M')
                    total = float(c.get('total_productos', 0))
                    unidades = int(c.get('total_unidades', 0))

                    hdr_row = ctk.CTkFrame(card, fg_color="transparent")
                    hdr_row.pack(fill="x", padx=12, pady=(10, 4))

                    ctk.CTkLabel(
                        hdr_row, text=f"Compra #{c.get('idCompra', 'N/A')}",
                        font=("Arial", 14, "bold"), text_color="#ffffff"
                    ).pack(side="left")
                    ctk.CTkLabel(
                        hdr_row, text=str(fecha),
                        font=("Arial", 12), text_color="#777777"
                    ).pack(side="right")

                    for prod in c.get('detalle', []):
                        ctk.CTkLabel(
                            card,
                            text=f"  • {prod['nombre']}  ({prod['referencia']})   ×{prod['cantidad']}   ${float(prod.get('subtotal', 0)):,.2f}",
                            font=("Arial", 12), text_color="#aaaaaa", anchor="w"
                        ).pack(fill="x", padx=16, pady=1)

                    ctk.CTkLabel(
                        card,
                        text=f"  {unidades} unidades — Total estimado: ${total:,.2f}",
                        font=("Arial", 13, "bold"), text_color="#1DB954", anchor="w"
                    ).pack(fill="x", padx=12, pady=(6, 10))

        except Exception as e:
            ctk.CTkLabel(
                scroll_compras, text=f"Error al cargar compras: {e}",
                text_color="#ff4d4d"
            ).pack(pady=20)

    # ── Navigation helpers ─────────────────────────────────────────────────────

    def _abrir_nuevo_proveedor(self):
        from gui.nuevo_proveedor import NuevoProveedorWindow
        NuevoProveedorWindow(self.controller, rol=self.controller.rol, on_success=self.cargar)

    def _editar_proveedor(self, proveedor):
        from gui.nuevo_proveedor import NuevoProveedorWindow
        NuevoProveedorWindow(self.controller, proveedor_datos=proveedor, rol=self.controller.rol, on_success=self.cargar)

    def _abrir_nueva_compra(self, proveedor):
        from gui.nueva_compra import NuevaCompraWindow
        NuevaCompraWindow(
            self.controller,
            proveedor=proveedor,
            id_empleado=self.controller.id_empleado,
            rol=self.controller.rol,
            on_success=lambda: self._mostrar_detalle(proveedor)
        )
