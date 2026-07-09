import customtkinter as ctk
from database.connection import (
    obtener_ventas_cliente, obtener_detalle_venta,
    registrar_devolucion_cambio, obtener_saldos_cuentas
)


class DevolucionModal:
    """Returns & exchange modal window."""

    def __init__(self, parent_widget, controller):
        self.controller = controller
        self.dev_cliente_sel = None
        self.dev_venta_sel = None
        self.dev_producto_marcado = None
        self.dev_reemplazos = []
        self.dev_ventas_cliente = []
        self.dev_productos_venta = []

        modal = ctk.CTkToplevel(parent_widget)
        modal.title("Realizar Devolución y Cambio")
        modal.geometry("900x720")
        modal.resizable(True, True)
        modal.configure(fg_color="#0d0d0d")
        modal.grab_set()
        modal.focus()
        self._modal = modal

        ctk.CTkLabel(modal, text="🔄 Devolución y Cambio de Productos",
                     font=("Arial", 22, "bold"), text_color="#ff6b6b"
                     ).pack(pady=(20, 10))

        # ── Filter bar ─────────────────────────────────────────────────────────
        filter_frame = ctk.CTkFrame(modal, fg_color="#121212", corner_radius=10)
        filter_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(filter_frame, text="Cliente:", font=("Arial", 12, "bold")
                     ).grid(row=0, column=0, padx=15, pady=15, sticky="w")

        opciones_clientes = ["Seleccione cliente..."] + [
            f"{c['nombre']} {c['apellidos']} ({c['documento']})"
            for c in getattr(controller, 'todos_clientes', [])
        ]
        self._combo_cliente = ctk.CTkComboBox(filter_frame, values=opciones_clientes, width=280)
        self._combo_cliente.grid(row=0, column=1, padx=10, pady=15, sticky="w")

        ctk.CTkLabel(filter_frame, text="Venta asociada:", font=("Arial", 12, "bold")
                     ).grid(row=0, column=2, padx=15, pady=15, sticky="w")

        self._combo_venta = ctk.CTkComboBox(filter_frame, values=["Seleccione venta..."],
                                             width=300, state="disabled")
        self._combo_venta.grid(row=0, column=3, padx=10, pady=15, sticky="w")

        # ── Body: two columns ──────────────────────────────────────────────────
        body = ctk.CTkFrame(modal, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=10)
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        left_col = ctk.CTkFrame(body, fg_color="#0a0a0a", corner_radius=10)
        left_col.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        ctk.CTkLabel(left_col, text="1. Artículos Vendidos",
                     font=("Arial", 14, "bold"), text_color="#aaaaaa").pack(pady=5)
        self._scroll_art = ctk.CTkScrollableFrame(left_col, fg_color="#121212", corner_radius=8, height=220)
        self._scroll_art.pack(fill="both", expand=True, padx=15, pady=(5, 10))

        panel_marc = ctk.CTkFrame(left_col, fg_color="#121212", corner_radius=8)
        panel_marc.pack(fill="x", padx=15, pady=(0, 15))
        self._lbl_marcado = ctk.CTkLabel(panel_marc, text="Ningún artículo marcado para devolución",
                                         font=("Arial", 12, "italic"), text_color="#888888")
        self._lbl_marcado.pack(anchor="w", padx=15, pady=8)
        cant_frame = ctk.CTkFrame(panel_marc, fg_color="transparent")
        cant_frame.pack(fill="x", padx=15, pady=(0, 10))
        ctk.CTkLabel(cant_frame, text="Cant. a devolver:", font=("Arial", 12)).pack(side="left")
        self._entry_cant_dev = ctk.CTkEntry(cant_frame, width=70, placeholder_text="1")
        self._entry_cant_dev.pack(side="left", padx=10)
        self._entry_cant_dev.configure(state="disabled")
        self._entry_cant_dev.bind("<KeyRelease>", lambda e: self._recalcular())

        right_col = ctk.CTkFrame(body, fg_color="#0a0a0a", corner_radius=10)
        right_col.grid(row=0, column=1, padx=(10, 0), sticky="nsew")
        ctk.CTkLabel(right_col, text="2. Artículos de Reemplazo",
                     font=("Arial", 14, "bold"), text_color="#aaaaaa").pack(pady=5)

        form_reemp = ctk.CTkFrame(right_col, fg_color="#121212", corner_radius=8)
        form_reemp.pack(fill="x", padx=15, pady=5)
        opciones_prod = ["Seleccione producto..."] + [
            f"{p['nombre']} ({p['referencia']})"
            for p in getattr(controller, 'todos_productos', [])
        ]
        self._combo_reemp = ctk.CTkComboBox(form_reemp, values=opciones_prod, width=220)
        self._combo_reemp.pack(side="left", padx=5, pady=10)
        self._combo_reemp.set("Seleccione producto...")
        self._entry_cant_reemp = ctk.CTkEntry(form_reemp, width=60, placeholder_text="Cant")
        self._entry_cant_reemp.pack(side="left", padx=5, pady=10)
        ctk.CTkButton(form_reemp, text="+", width=40, font=("Arial", 14, "bold"),
                      command=self._agregar_reemplazo).pack(side="left", padx=5, pady=10)

        self._scroll_reemp = ctk.CTkScrollableFrame(right_col, fg_color="#121212", corner_radius=8, height=180)
        self._scroll_reemp.pack(fill="both", expand=True, padx=15, pady=(5, 15))

        # ── Bottom: summary + confirm ──────────────────────────────────────────
        bottom = ctk.CTkFrame(modal, fg_color="#121212", corner_radius=10)
        bottom.pack(fill="x", padx=20, pady=(5, 20))

        totales_f = ctk.CTkFrame(bottom, fg_color="transparent")
        totales_f.pack(fill="x", padx=20, pady=12)
        self._lbl_resumen = ctk.CTkLabel(totales_f,
                                         text="Valor devolución: $0.00  |  Valor reemplazo: $0.00",
                                         font=("Arial", 14, "bold"), text_color="#cccccc")
        self._lbl_resumen.pack(side="left")
        self._lbl_balance = ctk.CTkLabel(totales_f, text="Balance: $0.00",
                                         font=("Arial", 15, "bold"), text_color="#888888")
        self._lbl_balance.pack(side="right")

        self._pago_frame = ctk.CTkFrame(bottom, fg_color="transparent")
        ctk.CTkLabel(self._pago_frame, text="Cuenta para recibir excedente:",
                     font=("Arial", 12, "bold")).pack(side="left", padx=(0, 10))
        try:
            cuentas = obtener_saldos_cuentas(controller.rol)
            op_c = [f"{c['tipo_cuenta']} ({c['num_cuenta']})" for c in cuentas]
            self._cuentas_dev_map = {f"{c['tipo_cuenta']} ({c['num_cuenta']})": c['idMetodo_de_pago'] for c in cuentas}
        except Exception:
            op_c, self._cuentas_dev_map = [], {}
        if not op_c:
            op_c = ["Sin métodos"]
        self._combo_metodo_dev = ctk.CTkComboBox(self._pago_frame, values=op_c, width=250)
        self._combo_metodo_dev.pack(side="left")
        self._pago_frame.pack_forget()

        self._lbl_status = ctk.CTkLabel(bottom, text="", font=("Arial", 12),
                                        text_color="#ff4d4d", wraplength=800)
        self._lbl_status.pack(pady=5)

        ctk.CTkButton(bottom, text="Confirmar Devolución y Cambio",
                      font=("Arial", 16, "bold"), fg_color="#ff6b6b",
                      hover_color="#cc4444", text_color="#000000", height=45,
                      command=self._ejecutar
                      ).pack(fill="x", padx=20, pady=(0, 20))

        self._combo_cliente.configure(command=self._on_cliente)
        self._combo_venta.configure(command=self._on_venta)

    # ── Event handlers ─────────────────────────────────────────────────────────

    def _on_cliente(self, val):
        if val == "Seleccione cliente...":
            self._combo_venta.configure(values=["Seleccione venta..."], state="disabled")
            self._combo_venta.set("Seleccione venta...")
            self._limpiar()
            return
        self.dev_cliente_sel = next(
            (c for c in getattr(self.controller, 'todos_clientes', [])
             if f"{c['nombre']} {c['apellidos']} ({c['documento']})" == val), None
        )
        if not self.dev_cliente_sel:
            return
        try:
            self.dev_ventas_cliente = obtener_ventas_cliente(
                self.dev_cliente_sel['idCliente'], self.controller.rol)
            if not self.dev_ventas_cliente:
                self._combo_venta.configure(values=["Sin ventas registradas"], state="disabled")
                self._combo_venta.set("Sin ventas registradas")
                self._limpiar()
                return
            ops = [f"Venta #{v['idVenta']} - {v['fecha_venta']} (${float(v['valor_total']):,.2f}) [{v['estado_pago']}]"
                   for v in self.dev_ventas_cliente]
            self._combo_venta.configure(values=ops, state="normal")
            self._combo_venta.set("Seleccione venta...")
            self._limpiar()
        except Exception as ex:
            self._lbl_status.configure(text=f"Error: {ex}")

    def _on_venta(self, val):
        if val in ["Seleccione venta...", "Sin ventas registradas"]:
            self._limpiar()
            return
        try:
            id_venta = int(val.split(" - ")[0].replace("Venta #", ""))
        except Exception:
            return
        self.dev_venta_sel = next((v for v in self.dev_ventas_cliente if v['idVenta'] == id_venta), None)
        if not self.dev_venta_sel:
            return
        try:
            self.dev_productos_venta = obtener_detalle_venta(id_venta, self.controller.rol)
            self._render_articulos()
            self.dev_producto_marcado = None
            self._lbl_marcado.configure(text="Ningún artículo marcado para devolución",
                                        font=("Arial", 12, "italic"), text_color="#888888")
            self._entry_cant_dev.configure(state="normal")
            self._entry_cant_dev.delete(0, 'end')
            self._entry_cant_dev.configure(state="disabled")
            self.dev_reemplazos = []
            self._render_reemplazos()
            self._recalcular()
        except Exception as ex:
            self._lbl_status.configure(text=f"Error: {ex}")

    def _limpiar(self):
        self.dev_venta_sel = None
        self.dev_producto_marcado = None
        self.dev_reemplazos = []
        for w in self._scroll_art.winfo_children():
            w.destroy()
        self._entry_cant_dev.configure(state="normal")
        self._entry_cant_dev.delete(0, 'end')
        self._entry_cant_dev.configure(state="disabled")
        self._render_reemplazos()
        self._recalcular()

    def _render_articulos(self):
        for w in self._scroll_art.winfo_children():
            w.destroy()
        for p in self.dev_productos_venta:
            row = ctk.CTkFrame(self._scroll_art, fg_color="#181818", corner_radius=5)
            row.pack(fill="x", pady=2, padx=2)
            ctk.CTkLabel(row,
                         text=f"{p['nombre']} ({p['referencia']})\nCant vendida: {p['cantidad']} | Precio: ${float(p['precio_venta']):,.2f}",
                         font=("Arial", 11), justify="left").pack(side="left", padx=10, pady=5)
            ctk.CTkButton(row, text="Marcar", font=("Arial", 11, "bold"), width=60, height=25,
                          fg_color="#333333", hover_color="#555555",
                          command=lambda prod=p: self._marcar(prod)
                          ).pack(side="right", padx=10)

    def _marcar(self, prod):
        self.dev_producto_marcado = prod
        self._lbl_marcado.configure(
            text=f"MARCADO: {prod['nombre']} ({prod['referencia']})\nPrecio unitario: ${float(prod['precio_venta']):,.2f} | Max: {prod['cantidad']}",
            font=("Arial", 12, "bold"), text_color="#ff6b6b")
        self._entry_cant_dev.configure(state="normal")
        self._entry_cant_dev.delete(0, 'end')
        self._entry_cant_dev.insert(0, "1")
        self._recalcular()

    def _agregar_reemplazo(self):
        if not self.dev_producto_marcado:
            self._lbl_status.configure(text="Primero marque un artículo para devolución.")
            return
        prod_str = self._combo_reemp.get()
        if prod_str == "Seleccione producto...":
            self._lbl_status.configure(text="Seleccione un producto de reemplazo.")
            return
        try:
            cantidad = int(self._entry_cant_reemp.get().strip())
            if cantidad <= 0:
                raise ValueError()
        except ValueError:
            self._lbl_status.configure(text="Ingrese cantidad válida.")
            return
        prod_sel = next(
            (p for p in getattr(self.controller, 'todos_productos', [])
             if f"{p['nombre']} ({p['referencia']})" == prod_str), None
        )
        if not prod_sel:
            return
        for item in self.dev_reemplazos:
            if item['idProducto'] == prod_sel['idProducto']:
                item['cantidad'] += cantidad
                break
        else:
            self.dev_reemplazos.append({
                'idProducto': prod_sel['idProducto'],
                'nombre': prod_sel['nombre'],
                'referencia': prod_sel['referencia'],
                'precio_venta': float(prod_sel['precio_venta']),
                'cantidad': cantidad
            })
        self._entry_cant_reemp.delete(0, 'end')
        self._combo_reemp.set("Seleccione producto...")
        self._lbl_status.configure(text="")
        self._render_reemplazos()
        self._recalcular()

    def _render_reemplazos(self):
        for w in self._scroll_reemp.winfo_children():
            w.destroy()
        if not self.dev_reemplazos:
            ctk.CTkLabel(self._scroll_reemp, text="No hay artículos de reemplazo.",
                         text_color="#666666").pack(pady=10)
            return
        for idx, item in enumerate(self.dev_reemplazos):
            row = ctk.CTkFrame(self._scroll_reemp, fg_color="#181818", corner_radius=5)
            row.pack(fill="x", pady=2, padx=2)
            subt = item['cantidad'] * item['precio_venta']
            ctk.CTkLabel(row,
                         text=f"{item['nombre']} ({item['referencia']})\nCant: {item['cantidad']} x ${item['precio_venta']:,.2f} = ${subt:,.2f}",
                         font=("Arial", 11), justify="left").pack(side="left", padx=10, pady=5)
            ctk.CTkButton(row, text="Eliminar", font=("Arial", 11, "bold"), width=60, height=25,
                          fg_color="#ff4d4d", hover_color="#cc0000",
                          command=lambda i=idx: self._eliminar_reemp(i)
                          ).pack(side="right", padx=10)

    def _eliminar_reemp(self, idx):
        if 0 <= idx < len(self.dev_reemplazos):
            self.dev_reemplazos.pop(idx)
            self._render_reemplazos()
            self._recalcular()

    def _recalcular(self):
        if not self.dev_producto_marcado:
            self._lbl_resumen.configure(text="Valor devolución: $0.00  |  Valor reemplazo: $0.00")
            self._lbl_balance.configure(text="Balance: $0.00", text_color="#888888")
            self._pago_frame.pack_forget()
            return
        try:
            cant_dev = int(self._entry_cant_dev.get().strip())
            if cant_dev <= 0 or cant_dev > int(self.dev_producto_marcado['cantidad']):
                raise ValueError()
        except (ValueError, TypeError):
            self._lbl_resumen.configure(text="Cantidad inválida")
            self._lbl_balance.configure(text="Balance: --", text_color="#ff4d4d")
            self._pago_frame.pack_forget()
            return
        valor_dev = cant_dev * float(self.dev_producto_marcado['precio_venta'])
        valor_reemp = sum(i['cantidad'] * i['precio_venta'] for i in self.dev_reemplazos)
        balance = valor_reemp - valor_dev
        self._lbl_resumen.configure(
            text=f"Valor devolución: ${valor_dev:,.2f}  |  Valor reemplazo: ${valor_reemp:,.2f}")
        if round(balance, 2) < 0:
            self._lbl_balance.configure(text=f"Falta cubrir: ${abs(balance):,.2f}", text_color="#ff4d4d")
            self._pago_frame.pack_forget()
        elif round(balance, 2) == 0:
            self._lbl_balance.configure(text="Balance cubierto: $0.00", text_color="#1DB954")
            self._pago_frame.pack_forget()
        else:
            self._lbl_balance.configure(text=f"Exceso: ${balance:,.2f}", text_color="#1DB954")
            self._pago_frame.pack(fill="x", padx=20, pady=(0, 10))

    def _ejecutar(self):
        self._lbl_status.configure(text="")
        if not self.dev_cliente_sel:
            self._lbl_status.configure(text="Seleccione un cliente.")
            return
        if not self.dev_venta_sel:
            self._lbl_status.configure(text="Seleccione una venta.")
            return
        if not self.dev_producto_marcado:
            self._lbl_status.configure(text="Marque un artículo para devolución.")
            return
        try:
            cant_dev = int(self._entry_cant_dev.get().strip())
            if cant_dev <= 0 or cant_dev > int(self.dev_producto_marcado['cantidad']):
                raise ValueError()
        except (ValueError, TypeError):
            self._lbl_status.configure(text=f"Cantidad inválida (Máx: {self.dev_producto_marcado['cantidad']})")
            return
        if not self.dev_reemplazos:
            self._lbl_status.configure(text="Agregue al menos un artículo de reemplazo.")
            return
        valor_dev = cant_dev * float(self.dev_producto_marcado['precio_venta'])
        valor_reemp = sum(i['cantidad'] * i['precio_venta'] for i in self.dev_reemplazos)
        balance = valor_reemp - valor_dev
        if round(balance, 2) < 0:
            self._lbl_status.configure(text="El reemplazo debe ser igual o mayor al valor devuelto.")
            return
        id_metodo = None
        if round(balance, 2) > 0:
            metodo_str = self._combo_metodo_dev.get()
            if metodo_str not in self._cuentas_dev_map:
                self._lbl_status.configure(text="Seleccione un método de pago para el saldo adicional.")
                return
            id_metodo = self._cuentas_dev_map[metodo_str]
        try:
            registrar_devolucion_cambio(
                id_venta=self.dev_venta_sel['idVenta'],
                id_prod_devuelto=self.dev_producto_marcado['idProducto'],
                cant_devuelta=cant_dev,
                productos_nuevos=self.dev_reemplazos,
                id_metodo_pago=id_metodo,
                monto_adicional=balance,
                rol=self.controller.rol
            )
            self._lbl_status.configure(text="¡Devolución y cambio procesados con éxito!", text_color="#1DB954")
            self._modal.after(1500, self._modal.destroy)
            if hasattr(self.controller, '_tab_productos'):
                self.controller._tab_productos.cargar()
            if hasattr(self.controller, '_tab_cuentas'):
                self.controller._tab_cuentas.cargar()
        except Exception as ex:
            self._lbl_status.configure(text=f"Error: {ex}", text_color="#ff4d4d")
