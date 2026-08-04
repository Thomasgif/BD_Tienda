import customtkinter as ctk
from math import isfinite
from database.connection import (
    obtener_clientes, obtener_productos, obtener_saldos_cuentas,
    obtener_ventas_cliente, obtener_detalle_venta,
    registrar_devolucion_cambio, registrar_venta
)


class VentasTab:
    """Manages the Ventas tab: cart, checkout, returns modal."""

    def __init__(self, parent_frame, controller):
        self.controller = controller
        self.carrito_ventas = []
        self.total_ventas = 0.0
        self.total_final_venta = 0.0
        self.descuento_aplicado = 0.0

        main = ctk.CTkFrame(parent_frame, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=40, pady=(0, 20))

        form_frame = ctk.CTkFrame(main, fg_color="#0a0a0a", corner_radius=15)
        form_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        cart_frame = ctk.CTkFrame(main, fg_color="#0a0a0a", corner_radius=15)
        cart_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))

        # ── Form (left) ────────────────────────────────────────────────────────
        ctk.CTkLabel(form_frame, text="Facturar Venta",
                     font=("Arial", 20, "bold"), text_color="#1DB954"
                     ).grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 15), sticky="w")

        ctk.CTkLabel(form_frame, text="Cliente:", font=("Arial", 14, "bold"), text_color="#cccccc"
                     ).grid(row=1, column=0, padx=20, pady=10, sticky="w")
        self.combo_cliente = ctk.CTkComboBox(form_frame, values=["Seleccione cliente..."], width=200)
        self.combo_cliente.grid(row=1, column=1, padx=20, pady=10, sticky="w")

        ctk.CTkFrame(form_frame, height=1, fg_color="#333333"
                     ).grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=10)

        ctk.CTkLabel(form_frame, text="Añadir Producto:", font=("Arial", 14, "bold"), text_color="#cccccc"
                     ).grid(row=3, column=0, padx=20, pady=10, sticky="w")
        self.combo_producto = ctk.CTkComboBox(form_frame, values=["Seleccione producto..."], width=200)
        self.combo_producto.grid(row=3, column=1, padx=20, pady=10, sticky="w")

        ctk.CTkLabel(form_frame, text="Cantidad:", font=("Arial", 14, "bold"), text_color="#cccccc"
                     ).grid(row=4, column=0, padx=20, pady=10, sticky="w")
        self.entry_cantidad = ctk.CTkEntry(form_frame, width=100, placeholder_text="Ej: 1")
        self.entry_cantidad.grid(row=4, column=1, padx=20, pady=10, sticky="w")

        ctk.CTkButton(form_frame, text="+ Añadir a la Lista",
                      font=("Arial", 14, "bold"), fg_color="#333333", hover_color="#555555",
                      command=self._agregar_producto
                      ).grid(row=5, column=0, columnspan=2, padx=20, pady=10)

        ctk.CTkFrame(form_frame, height=1, fg_color="#333333"
                     ).grid(row=6, column=0, columnspan=2, sticky="ew", padx=20, pady=10)

        ctk.CTkButton(form_frame, text="🔄 Devolución / Cambio",
                      font=("Arial", 14, "bold"), fg_color="#3a1e1e",
                      hover_color="#5e2626", text_color="#ff8888", height=38,
                      command=self._abrir_devolucion
                      ).grid(row=7, column=0, columnspan=2, padx=20, pady=(10, 20), sticky="ew")

        # ── Cart (right) ───────────────────────────────────────────────────────
        ctk.CTkLabel(cart_frame, text="Lista de Productos",
                     font=("Arial", 18, "bold"), text_color="#aaaaaa"
                     ).pack(padx=20, pady=(20, 10), anchor="w")

        self.scroll_carrito = ctk.CTkScrollableFrame(cart_frame, fg_color="#121212", corner_radius=10)
        self.scroll_carrito.pack(fill="both", expand=True, padx=20, pady=10)
        ctk.CTkLabel(self.scroll_carrito, text="La lista está vacía.", text_color="#666666").pack(pady=20)

        desc_frame = ctk.CTkFrame(cart_frame, fg_color="transparent")
        desc_frame.pack(fill="x", padx=20, pady=(5, 5))
        ctk.CTkLabel(desc_frame, text="Descuento ($):", font=("Arial", 14, "bold"), text_color="#cccccc"
                     ).pack(side="left")
        self.entry_descuento = ctk.CTkEntry(desc_frame, width=120, placeholder_text="Máx 8%")
        self.entry_descuento.pack(side="right")
        self.entry_descuento.bind("<KeyRelease>", self._on_descuento)

        self.lbl_total = ctk.CTkLabel(cart_frame, text="Total Venta: $0.00",
                                      font=("Arial", 22, "bold"), text_color="#1DB954")
        self.lbl_total.pack(padx=20, pady=(5, 20), anchor="e")

        ctk.CTkButton(cart_frame, text="Realizar Venta",
                      font=("Arial", 16, "bold"), fg_color="#1DB954",
                      hover_color="#179643", text_color="black", height=45,
                      command=self._procesar_venta
                      ).pack(fill="x", padx=20, pady=(0, 20))

        self._refresh_combos()

    # ── Public API ─────────────────────────────────────────────────────────────

    def refresh_clientes(self):
        try:
            self.controller.todos_clientes = obtener_clientes(self.controller.rol)
        except Exception:
            pass
        vals = ["Seleccione cliente..."] + [
            f"{c['nombre']} {c['apellidos']} ({c['documento']})"
            for c in getattr(self.controller, 'todos_clientes', [])
        ]
        self.combo_cliente.configure(values=vals)
        self.combo_cliente.set("Seleccione cliente...")

    def refresh_productos(self):
        try:
            self.controller.todos_productos = obtener_productos(self.controller.rol)
        except Exception:
            pass
        vals = ["Seleccione producto..."] + [
            f"{p['nombre']} ({p['referencia']})"
            for p in getattr(self.controller, 'todos_productos', [])
        ]
        self.combo_producto.configure(values=vals)
        self.combo_producto.set("Seleccione producto...")

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _refresh_combos(self):
        self.refresh_clientes()
        self.refresh_productos()

    def _agregar_producto(self):
        prod_str = self.combo_producto.get()
        cant_str = self.entry_cantidad.get().strip()
        if prod_str == "Seleccione producto..." or not prod_str:
            return
        try:
            cantidad = int(cant_str)
            if cantidad <= 0:
                return
        except ValueError:
            return

        prod_sel = next(
            (p for p in getattr(self.controller, 'todos_productos', [])
             if f"{p['nombre']} ({p['referencia']})" == prod_str), None
        )
        if not prod_sel:
            return

        bodega = int(prod_sel.get('bodega', 0) or 0)
        en_carrito = sum(i['cantidad'] for i in self.carrito_ventas
                         if i['idProducto'] == prod_sel['idProducto'])
        if cantidad + en_carrito > bodega:
            return

        for item in self.carrito_ventas:
            if item['idProducto'] == prod_sel['idProducto']:
                item['cantidad'] += cantidad
                break
        else:
            self.carrito_ventas.append({
                'idProducto': prod_sel['idProducto'],
                'nombre': prod_sel['nombre'],
                'referencia': prod_sel['referencia'],
                'precio_venta': float(prod_sel['precio_venta']),
                'cantidad': cantidad
            })

        self._actualizar_carrito_ui()
        self.entry_cantidad.delete(0, 'end')
        self.combo_producto.set("Seleccione producto...")

    def _actualizar_carrito_ui(self):
        for w in self.scroll_carrito.winfo_children():
            w.destroy()
        self.total_ventas = 0.0

        if not self.carrito_ventas:
            ctk.CTkLabel(self.scroll_carrito, text="La lista está vacía.", text_color="#666666").pack(pady=20)
            self.lbl_total.configure(text="Total Venta: $0.00")
            return

        for idx, item in enumerate(self.carrito_ventas):
            subtotal = item['cantidad'] * item['precio_venta']
            self.total_ventas += subtotal
            row = ctk.CTkFrame(self.scroll_carrito, fg_color="#1a1a1a", corner_radius=5)
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"{item['nombre']} ({item['referencia']}) x{item['cantidad']}",
                         font=("Arial", 12)).pack(side="left", padx=10, pady=5)
            ctk.CTkLabel(row, text=f"${subtotal:,.2f}", font=("Arial", 12, "bold"),
                         text_color="#1DB954").pack(side="right", padx=10, pady=5)
            ctk.CTkButton(row, text="X", width=25, height=25,
                          fg_color="#ff4d4d", hover_color="#cc0000",
                          command=lambda i=idx: self._eliminar(i)).pack(side="right", padx=5)

        self._on_descuento()

    def _on_descuento(self, event=None):
        desc_str = self.entry_descuento.get().strip().replace(",", ".")
        if not desc_str:
            self.descuento_aplicado = 0.0
            self.total_final_venta = self.total_ventas
            self.lbl_total.configure(text=f"Total Venta: ${self.total_ventas:,.2f}", text_color="#1DB954")
            return
        try:
            descuento = float(desc_str)
            max_desc = self.total_ventas * 0.08
            if descuento < 0 or descuento > max_desc:
                self.lbl_total.configure(
                    text=f"Descuento inválido (Máx: ${max_desc:,.2f})", text_color="#ff4d4d")
                self.descuento_aplicado = 0.0
                self.total_final_venta = self.total_ventas
            else:
                self.descuento_aplicado = descuento
                self.total_final_venta = self.total_ventas - descuento
                self.lbl_total.configure(
                    text=f"Total Venta: ${self.total_final_venta:,.2f} (-${descuento:,.2f})",
                    text_color="#1DB954")
        except ValueError:
            self.lbl_total.configure(text="Descuento inválido", text_color="#ff4d4d")

    def _eliminar(self, index):
        if 0 <= index < len(self.carrito_ventas):
            self.carrito_ventas.pop(index)
            self._actualizar_carrito_ui()

    def _procesar_venta(self):
        if not self.carrito_ventas:
            return
        cliente_str = self.combo_cliente.get()
        if cliente_str == "Seleccione cliente...":
            return
        cliente_sel = next(
            (c for c in getattr(self.controller, 'todos_clientes', [])
             if f"{c['nombre']} {c['apellidos']} ({c['documento']})" == cliente_str), None
        )
        if not cliente_sel:
            return

        desc_str = self.entry_descuento.get().strip().replace(",", ".")
        descuento = 0.0
        if desc_str:
            try:
                descuento = float(desc_str)
                if descuento < 0 or descuento > self.total_ventas * 0.08:
                    return
            except ValueError:
                return

        self.total_final_venta = self.total_ventas - descuento

        modal = ctk.CTkToplevel(self.scroll_carrito)
        modal.title("Confirmar Venta")
        modal.geometry("400x475")
        modal.resizable(False, False)
        modal.configure(fg_color="#0d0d0d")
        modal.grab_set()
        modal.focus()

        ctk.CTkLabel(modal, text="Confirmar Venta", font=("Arial", 20, "bold"), text_color="#1DB954"
                     ).pack(pady=(20, 10))
        txt = f"Total: ${self.total_final_venta:,.2f}"
        if descuento > 0:
            txt += f"\n(Subtotal: ${self.total_ventas:,.2f} - Descuento: ${descuento:,.2f})"
        ctk.CTkLabel(modal, text=txt, font=("Arial", 14, "bold"), justify="center").pack(pady=5)

        ctk.CTkLabel(modal, text="Estado de Pago:", font=("Arial", 12)
                     ).pack(anchor="w", padx=30, pady=(5, 2))
        combo_estado = ctk.CTkComboBox(modal, values=["PAGADO", "PENDIENTE"], width=340)
        combo_estado.pack(padx=30)
        combo_estado.set("PAGADO")

        ctk.CTkLabel(modal, text="Método de Pago:", font=("Arial", 12)
                     ).pack(anchor="w", padx=30, pady=(10, 2))
        try:
            cuentas = obtener_saldos_cuentas(self.controller.rol)
            opciones_c = [f"{c['tipo_cuenta']} ({c['num_cuenta']})" for c in cuentas]
            _cuentas_map = {f"{c['tipo_cuenta']} ({c['num_cuenta']})": c['idMetodo_de_pago'] for c in cuentas}
        except Exception:
            opciones_c, _cuentas_map = [], {}
        if not opciones_c:
            opciones_c = ["Sin métodos"]
        combo_metodo = ctk.CTkComboBox(modal, values=opciones_c, width=340)
        combo_metodo.pack(padx=30)

        ctk.CTkLabel(modal, text="Abono inicial ($):", font=("Arial", 12)
                     ).pack(anchor="w", padx=30, pady=(10, 2))
        entry_abono = ctk.CTkEntry(modal, width=340)
        entry_abono.pack(padx=30)

        lbl_ayuda = ctk.CTkLabel(modal, text="El pago completo cubre el total de la venta.",
                                 text_color="#888888", font=("Arial", 11), wraplength=340)
        lbl_ayuda.pack(pady=(3, 0))

        def actualizar_forma(estado):
            entry_abono.configure(state="normal")
            entry_abono.delete(0, "end")
            if estado == "PAGADO":
                entry_abono.insert(0, f"{self.total_final_venta:.2f}")
                entry_abono.configure(state="disabled")
                lbl_ayuda.configure(text="El pago completo cubre el total de la venta.")
            else:
                entry_abono.insert(0, "0.00")
                lbl_ayuda.configure(text="Puede abonar una parte ahora o dejar 0 para pagar después.")

        combo_estado.configure(command=actualizar_forma)
        actualizar_forma("PAGADO")

        lbl_estado = ctk.CTkLabel(modal, text="", text_color="#ff4d4d", wraplength=340)
        lbl_estado.pack(pady=10)

        def confirmar():
            estado_pago = combo_estado.get()
            metodo_str = combo_metodo.get()
            total_v = self.total_final_venta
            id_metodo = None
            if estado_pago == "PAGADO":
                monto_pagado = total_v
            else:
                try:
                    monto_pagado = float(entry_abono.get().strip().replace(",", "."))
                    if not isfinite(monto_pagado) or monto_pagado < 0:
                        lbl_estado.configure(text="Abono inválido.")
                        return
                    if monto_pagado >= total_v:
                        lbl_estado.configure(text="Para pagar el total, seleccione PAGADO.")
                        return
                except ValueError:
                    lbl_estado.configure(text="Ingrese un abono numérico válido.")
                    return
            if monto_pagado > 0:
                if metodo_str not in _cuentas_map:
                    lbl_estado.configure(text="Seleccione un método de pago válido.")
                    return
                id_metodo = _cuentas_map[metodo_str]
            try:
                registrar_venta(
                    id_empleado=self.controller.id_empleado,
                    id_cliente=cliente_sel['idCliente'],
                    productos=self.carrito_ventas,
                    id_metodo_pago=id_metodo,
                    monto_pagado=monto_pagado,
                    estado_pago=estado_pago,
                    valor_total=total_v,
                    rol=self.controller.rol
                )
                lbl_estado.configure(text="¡Venta registrada con éxito!", text_color="#1DB954")
                modal.after(1200, modal.destroy)
                self.carrito_ventas = []
                self.entry_descuento.delete(0, 'end')
                self._actualizar_carrito_ui()
                self.entry_cantidad.delete(0, 'end')
                self.combo_producto.set("Seleccione producto...")
                self.combo_cliente.set("Seleccione cliente...")
                if hasattr(self.controller, '_tab_productos'):
                    self.controller._tab_productos.cargar()
                if hasattr(self.controller, '_tab_cuentas'):
                    self.controller._tab_cuentas.cargar()
            except Exception as e:
                lbl_estado.configure(text=str(e), text_color="#ff4d4d")

        ctk.CTkButton(modal, text="Confirmar y Registrar",
                      font=("Arial", 14, "bold"), fg_color="#1DB954",
                      hover_color="#179643", command=confirmar
                      ).pack(pady=10)

    def _abrir_devolucion(self):
        """Opens the returns/exchange modal."""
        from gui.modals.devolucion import DevolucionModal
        DevolucionModal(self.scroll_carrito, self.controller)
