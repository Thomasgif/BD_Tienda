import threading
import customtkinter as ctk
from database.connection import obtener_clientes, obtener_deudas_cliente, pago_total_venta


class ClientesTab:
    """Manages the Clientes tab: list, search, debt accordion, pay/cancel modals."""

    def __init__(self, parent_frame, controller):
        self.controller = controller
        self.todos_clientes = []
        self.clientes_expandidos = set()

        # ── Top bar ────────────────────────────────────────────────────────────
        top_bar = ctk.CTkFrame(parent_frame, fg_color="transparent")
        top_bar.pack(fill="x", padx=40, pady=(0, 20))

        ctk.CTkLabel(
            top_bar, text="Lista de Clientes Registrados",
            font=("Arial", 18, "bold"), text_color="#aaaaaa"
        ).pack(side="left")

        ctk.CTkButton(
            top_bar, text="↻ Actualizar",
            font=("Arial", 12, "bold"),
            fg_color="#1e1e1e", hover_color="#333333", text_color="#1DB954",
            width=100, command=self.cargar
        ).pack(side="right")

        ctk.CTkButton(
            top_bar, text="+ Nuevo Cliente",
            font=("Arial", 14, "bold"),
            fg_color="#1DB954", hover_color="#179643", text_color="black",
            command=self._abrir_nuevo_cliente
        ).pack(side="right", padx=(0, 10))

        self.entry_buscar = ctk.CTkEntry(
            top_bar, placeholder_text="Buscar nombre o doc...", width=200
        )
        self.entry_buscar.pack(side="right", padx=(0, 10))
        self.entry_buscar.bind("<KeyRelease>", self.filtrar)

        # ── Scrollable list ────────────────────────────────────────────────────
        self.scroll = ctk.CTkScrollableFrame(
            parent_frame, fg_color="#0a0a0a", corner_radius=10
        )
        self.scroll.pack(fill="both", expand=True, padx=40, pady=(0, 20))

        # Carga asíncrona al construir el tab
        self.cargar()

    # ── Public API ─────────────────────────────────────────────────────────────

    def cargar(self):
        """Fetch clients from DB asynchronously, then re-render."""
        self._limpiar()
        ctk.CTkLabel(
            self.scroll, text="Cargando clientes...", text_color="#888888",
            font=("Arial", 14)
        ).pack(pady=30)

        def _fetch():
            try:
                data = obtener_clientes(self.controller.rol)
                self.scroll.after(0, lambda d=data: self._on_loaded(d))
            except Exception as e:
                self.scroll.after(0, lambda err=str(e): self._on_error(err))

        threading.Thread(target=_fetch, daemon=True).start()

    def _on_loaded(self, data):
        self.todos_clientes = data
        # Sync back to controller so VentasTab combos stay up to date
        self.controller.todos_clientes = data
        self.filtrar()

    def _on_error(self, msg):
        self._limpiar()
        ctk.CTkLabel(
            self.scroll, text=f"Error cargando clientes:\n{msg}",
            text_color="#ff4d4d"
        ).pack(pady=20)

    def on_show(self):
        cached = getattr(self.controller, 'todos_clientes', [])
        if cached:
            if not self.todos_clientes or len(cached) != len(self.todos_clientes):
                self.todos_clientes = cached
                self.filtrar()
        self.scroll.update_idletasks()



    def filtrar(self, event=None):
        query = self.entry_buscar.get().lower()
        filtrados = self.todos_clientes if not query else [
            c for c in self.todos_clientes
            if query in c['nombre'].lower()
            or query in c['apellidos'].lower()
            or query in str(c['documento']).lower()
        ]
        self.render(filtrados)

    # ── Rendering ──────────────────────────────────────────────────────────────

    def _limpiar(self):
        for w in self.scroll.winfo_children():
            w.destroy()

    def render(self, clientes):
        self._limpiar()
        if not clientes:
            ctk.CTkLabel(
                self.scroll, text="No se encontraron clientes.",
                text_color="#888888"
            ).pack(pady=20)
            return

        table = ctk.CTkFrame(self.scroll, fg_color="transparent")
        table.pack(fill="x", expand=True)
        for i, w in enumerate([1, 2, 1, 2, 2]):
            table.grid_columnconfigure(i, weight=w)

        hc = "#1e1e1e"
        for col_idx, text in enumerate(["Documento", "Nombre y Apellido", "Teléfono", "Correo", "Acciones"]):
            ctk.CTkLabel(
                table, text=text,
                font=("Arial", 14, "bold"), text_color="#1DB954",
                fg_color=hc, anchor="w", padx=10, pady=10
            ).grid(row=0, column=col_idx, sticky="nsew")

        for idx, cliente in enumerate(clientes):
            main_row = (idx * 2) + 1
            deuda_row = (idx * 2) + 2
            rc = "#121212" if idx % 2 == 0 else "#0a0a0a"
            id_cliente = cliente['idCliente']

            ctk.CTkLabel(table, text=cliente['documento'], text_color="#cccccc",
                         fg_color=rc, anchor="w", padx=10, pady=8
                         ).grid(row=main_row, column=0, sticky="nsew")
            ctk.CTkLabel(
                table, text=f"{cliente['nombre']} {cliente['apellidos']}",
                text_color="#ffffff", fg_color=rc, anchor="w", padx=10, pady=8
            ).grid(row=main_row, column=1, sticky="nsew")
            ctk.CTkLabel(table, text=cliente['telefono'] or "N/A", text_color="#cccccc",
                         fg_color=rc, anchor="w", padx=10, pady=8
                         ).grid(row=main_row, column=2, sticky="nsew")
            ctk.CTkLabel(table, text=cliente['correo'] or "N/A", text_color="#cccccc",
                         fg_color=rc, anchor="w", padx=10, pady=8
                         ).grid(row=main_row, column=3, sticky="nsew")

            # Actions cell
            af = ctk.CTkFrame(table, fg_color=rc, corner_radius=0)
            af.grid(row=main_row, column=4, sticky="nsew")

            ctk.CTkButton(
                af, text="Editar", width=60, height=28,
                font=("Arial", 12, "bold"),
                fg_color="#333333", hover_color="#555555", text_color="#ffffff",
                command=lambda doc=cliente['documento']: self._editar_cliente(doc)
            ).pack(side="left", padx=4, pady=6)

            # Expandable debts frame
            deuda_frame = ctk.CTkFrame(table, fg_color="#0b0b0b", corner_radius=8)

            btn_ventas = ctk.CTkButton(
                af, text="▶ Cuentas pendientes",
                font=("Arial", 12), width=90, height=28,
                fg_color="#1e2a1e", hover_color="#2d472d", text_color="#1DB954"
            )
            btn_ventas.configure(
                command=lambda idcli=id_cliente, df=deuda_frame, btn=btn_ventas, r=deuda_row:
                    self._toggle_deudas(idcli, df, btn, r)
            )
            btn_ventas.pack(side="left", padx=2, pady=6)

            if id_cliente in self.clientes_expandidos:
                self._cargar_deudas_cliente(deuda_frame, id_cliente)
                deuda_frame.grid(row=deuda_row, column=0, columnspan=5,
                                 padx=10, pady=(0, 10), sticky="ew")
                btn_ventas.configure(text="▼ Ocultar cuentas")

    # ── Debt accordion ─────────────────────────────────────────────────────────

    def _toggle_deudas(self, idcli, df, btn, row_idx):
        if idcli in self.clientes_expandidos:
            self.clientes_expandidos.discard(idcli)
            df.grid_forget()
            btn.configure(text="▶ Cuentas pendientes")
        else:
            self.clientes_expandidos.add(idcli)
            self._cargar_deudas_cliente(df, idcli)
            df.grid(row=row_idx, column=0, columnspan=5,
                    padx=10, pady=(0, 10), sticky="ew")
            btn.configure(text="▼ Ocultar cuentas")
        self.scroll.update_idletasks()

    def _cargar_deudas_cliente(self, df, idcli):
        for w in df.winfo_children():
            w.destroy()

        ctk.CTkLabel(
            df, text="Cargando deudas...",
            font=("Arial", 12), text_color="#888888"
        ).pack(anchor="w", padx=15, pady=10)

        def _fetch():
            try:
                deudas = obtener_deudas_cliente(idcli, self.controller.rol)
                df.after(0, lambda d=deudas: self._render_deudas_cliente(df, idcli, d))
            except Exception as e:
                df.after(0, lambda err=str(e): self._render_deudas_error(df, err))

        threading.Thread(target=_fetch, daemon=True).start()

    def _render_deudas_error(self, df, err):
        for w in df.winfo_children():
            w.destroy()
        ctk.CTkLabel(df, text=f"Error al cargar deudas: {err}",
                     text_color="red").pack(pady=10)

    def _render_deudas_cliente(self, df, idcli, deudas):
        for w in df.winfo_children():
            w.destroy()

        ctk.CTkLabel(
            df, text="Deudas pendientes del cliente:",
            font=("Arial", 13, "bold"), text_color="#cccccc"
        ).pack(anchor="w", padx=15, pady=(10, 4))

        if not deudas:
            ctk.CTkLabel(df, text="No se encontraron deudas.",
                         text_color="#888888", font=("Arial", 12)
                         ).pack(pady=(0, 10), anchor="w", padx=15)
            return

        for d in deudas:
            ya_pagado = float(d.get('total_pagado', 0) or 0)
            pendiente = float(d.get('saldo_pendiente', float(d['valor_total']) - ya_pagado) or 0)

            row_frame = ctk.CTkFrame(df, fg_color="#1a1a1a", corner_radius=8)
            row_frame.pack(fill="x", padx=15, pady=3)

            ctk.CTkLabel(
                row_frame,
                text=f"Venta #{d['idVenta']}  |  Fecha: {d['fecha_venta']}  |  Pendiente: ${pendiente:,.2f}",
                text_color="#cccccc", font=("Arial", 12)
            ).pack(side="left", padx=10, pady=8)

            ctk.CTkButton(
                row_frame, text="💳 Pagar", width=80, height=28,
                font=("Arial", 12, "bold"),
                fg_color="#1DB954", hover_color="#179643", text_color="#000000",
                command=lambda venta=d, monto=pendiente, cid=idcli, df_ref=df:
                    self._abrir_modal_pagar_deuda(venta, monto, cid, df_ref)
            ).pack(side="right", padx=(0, 5), pady=5)

            ctk.CTkButton(
                row_frame, text="✖ Cancelar", width=85, height=28,
                font=("Arial", 12, "bold"),
                fg_color="#5a1a1a", hover_color="#8b0000", text_color="#ff6b6b",
                command=lambda venta=d, cid=idcli, df_ref=df, pagado=ya_pagado:
                    self._confirmar_cancelar_venta(venta, cid, df_ref, pagado)
            ).pack(side="right", padx=(10, 0), pady=5)

    # ── Pay-debt modal ─────────────────────────────────────────────────────────

    def _abrir_modal_pagar_deuda(self, venta, monto_pendiente, id_cliente, df_ref):
        from database.connection import obtener_saldos_cuentas, pagar_venta_pendiente

        modal = ctk.CTkToplevel(self.scroll)
        modal.title("Registrar Pago")
        modal.geometry("400x380")
        modal.resizable(False, False)
        modal.configure(fg_color="#0d0d0d")
        modal.grab_set()
        modal.focus()

        ctk.CTkLabel(modal, text="💳 Registrar Pago",
                     font=("Arial", 18, "bold"), text_color="#1DB954"
                     ).pack(pady=(20, 4))
        ctk.CTkLabel(
            modal, text=f"Venta #{venta['idVenta']}  —  Pendiente: ${monto_pendiente:,.2f}",
            font=("Arial", 13), text_color="#aaaaaa"
        ).pack(pady=(0, 8))

        ctk.CTkLabel(modal, text="Método de Pago:", font=("Arial", 12)
                     ).pack(anchor="w", padx=30, pady=(4, 2))

        try:
            cuentas = obtener_saldos_cuentas(self.controller.rol)
            opciones = [f"{c['tipo_cuenta']} ({c['num_cuenta']})" for c in cuentas]
            mapa = {f"{c['tipo_cuenta']} ({c['num_cuenta']})": c['idMetodo_de_pago'] for c in cuentas}
        except Exception:
            opciones, mapa = [], {}

        if not opciones:
            opciones = ["Sin métodos disponibles"]

        combo_metodo = ctk.CTkComboBox(modal, values=opciones, width=340)
        combo_metodo.pack(padx=30)

        ctk.CTkLabel(modal, text="Monto a pagar ($):", font=("Arial", 12)
                     ).pack(anchor="w", padx=30, pady=(12, 2))

        ef = ctk.CTkFrame(modal, fg_color="transparent")
        ef.pack(padx=30, fill="x")
        entry_monto = ctk.CTkEntry(ef, placeholder_text="Ej: 15000", width=220)
        entry_monto.pack(side="left")
        ctk.CTkButton(
            ef, text="Pagar todo", width=110, height=32,
            font=("Arial", 11, "bold"),
            fg_color="#1a3a2a", hover_color="#24543c", text_color="#1DB954",
            command=lambda: (entry_monto.delete(0, "end"),
                             entry_monto.insert(0, f"{monto_pendiente:.2f}"))
        ).pack(side="left", padx=(8, 0))

        lbl_error = ctk.CTkLabel(modal, text="", text_color="#ff4d4d", wraplength=340)
        lbl_error.pack(pady=8)

        def confirmar():
            sel = combo_metodo.get()
            if sel not in mapa:
                lbl_error.configure(text="Selecciona un método de pago válido.")
                return
            try:
                monto_pago = float(entry_monto.get().strip().replace(",", "."))
            except ValueError:
                lbl_error.configure(text="Ingresa un monto numérico válido.")
                return
            try:
                pagar_venta_pendiente(
                    id_venta=venta['idVenta'],
                    id_cliente=id_cliente,
                    id_metodo_pago=mapa[sel],
                    monto=monto_pago,
                    rol=self.controller.rol
                )
                modal.destroy()
                self._cargar_deudas_cliente(df_ref, id_cliente)
                # Refresh accounts tab if available
                if hasattr(self.controller, '_tab_cuentas'):
                    self.controller._tab_cuentas.cargar()
            except Exception as e:
                lbl_error.configure(text=str(e))

        ctk.CTkButton(
            modal, text="✅ Confirmar Pago",
            font=("Arial", 13, "bold"),
            fg_color="#1DB954", hover_color="#179643", text_color="#000000",
            width=200, command=confirmar
        ).pack(pady=5)

    # ── Cancel-sale modal ──────────────────────────────────────────────────────

    def _confirmar_cancelar_venta(self, venta, id_cliente, df_ref, ya_pagado=0.0):
        from database.connection import cancelar_venta

        if ya_pagado > 0:
            geom, msg = "420x260", (
                f"Esta venta tiene un avance/abono de ${ya_pagado:,.2f}.\n\n"
                "El dinero quedará en la cuenta de la empresa y no se devolverá. "
                "La venta se cancelará y los productos regresarán al stock.\n\n"
                "¿Estás seguro de cancelar?"
            )
        else:
            geom, msg = "380x230", (
                f"¿Estás seguro de cancelar la Venta #{venta['idVenta']}?\n"
                "Esto restaurará el inventario de los productos."
            )

        modal = ctk.CTkToplevel(self.scroll)
        modal.title("Cancelar Venta")
        modal.geometry(geom)
        modal.resizable(False, False)
        modal.configure(fg_color="#0d0d0d")
        modal.grab_set()
        modal.focus()

        ctk.CTkLabel(modal, text="⚠ Cancelar Venta",
                     font=("Arial", 18, "bold"), text_color="#ff6b6b"
                     ).pack(pady=(20, 5))
        ctk.CTkLabel(modal, text=msg,
                     font=("Arial", 12), text_color="#cccccc",
                     wraplength=360, justify="center"
                     ).pack(pady=8)

        lbl_error = ctk.CTkLabel(modal, text="", text_color="#ff4d4d", wraplength=320)
        lbl_error.pack(pady=4)

        bf = ctk.CTkFrame(modal, fg_color="transparent")
        bf.pack(pady=10)

        def ejecutar():
            try:
                cancelar_venta(id_venta=venta['idVenta'], rol=self.controller.rol)
                modal.destroy()
                self._cargar_deudas_cliente(df_ref, id_cliente)
                if hasattr(self.controller, '_tab_productos'):
                    self.controller._tab_productos.cargar()
            except Exception as e:
                lbl_error.configure(text=str(e))

        ctk.CTkButton(bf, text="Sí, cancelar", width=120,
                      font=("Arial", 12, "bold"),
                      fg_color="#8b0000", hover_color="#cc0000", text_color="#ffffff",
                      command=ejecutar
                      ).pack(side="left", padx=10)
        ctk.CTkButton(bf, text="No, volver", width=120,
                      font=("Arial", 12, "bold"),
                      fg_color="#1e1e1e", hover_color="#333333", text_color="#cccccc",
                      command=modal.destroy
                      ).pack(side="left", padx=10)

    # ── Navigation helpers ─────────────────────────────────────────────────────

    def _abrir_nuevo_cliente(self):
        from gui.nuevo_cliente import NuevoClienteWindow
        NuevoClienteWindow(self.controller, rol=self.controller.rol, on_success=self.cargar)

    def _editar_cliente(self, documento):
        cliente = next((c for c in self.todos_clientes if c['documento'] == documento), None)
        if cliente:
            from gui.nuevo_cliente import NuevoClienteWindow
            NuevoClienteWindow(self.controller, cliente_datos=cliente, rol=self.controller.rol, on_success=self.cargar)
