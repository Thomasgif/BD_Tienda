import customtkinter as ctk


class NuevaCompraWindow(ctk.CTkToplevel):
    """
    Ventana modal para registrar una nueva compra para un proveedor específico.

    - Solo accesible para el Gerente (rol = 1).
    - Al confirmar, inserta COMPRA + DETALLE_COMPRA en la BD.
    - El inventario (PRODUCTO.bodega) y el ajuste de precio_compra NO se actualizan
      aquí; eso ocurre cuando se confirma el envío asociado a esta compra,
      distribuyendo el valor del envío entre el total de unidades.
    """

    def __init__(self, master=None, proveedor=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.proveedor = proveedor or {}
        self.rol       = getattr(master, 'rol', 1)
        self.id_emp    = getattr(master, 'id_empleado', None)

        # Lista de productos en el carrito: [{'idProducto', 'nombre', 'referencia', 'precio_compra', 'cantidad'}]
        self._carrito = []
        self._productos_db = []   # todos los productos disponibles

        # ── Ventana ───────────────────────────────────────────────────────────
        nombre_prov = self.proveedor.get('nombre', 'Proveedor')
        self.title(f"Nueva Compra — {nombre_prov}")
        self.geometry("620x680")
        self.resizable(False, False)
        self.configure(fg_color="#050505")
        self.transient(master)
        self.grab_set()

        # ── Frame principal ───────────────────────────────────────────────────
        self.frame = ctk.CTkFrame(
            self, corner_radius=15,
            fg_color="#121212",
            border_color="#1DB954", border_width=1,
        )
        self.frame.pack(padx=20, pady=20, fill="both", expand=True)

        # Título
        ctk.CTkLabel(
            self.frame,
            text=f"NUEVA COMPRA",
            font=("Arial", 20, "bold"), text_color="#1DB954",
        ).pack(side="top", pady=(20, 2))

        ctk.CTkLabel(
            self.frame,
            text=f"Proveedor: {nombre_prov}  (NIT: {self.proveedor.get('nit') or 'N/A'})",
            font=("Arial", 13), text_color="#aaaaaa",
        ).pack(side="top", pady=(0, 10))

        # ── Separador ─────────────────────────────────────────────────────────
        ctk.CTkFrame(self.frame, height=1, fg_color="#2a2a2a").pack(fill="x", padx=20, pady=(0, 10))

        # ── Sección agregar producto ──────────────────────────────────────────
        add_frame = ctk.CTkFrame(self.frame, fg_color="#1a1a1a", corner_radius=10)
        add_frame.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(
            add_frame, text="Agregar Producto",
            font=("Arial", 13, "bold"), text_color="#cccccc",
        ).pack(anchor="w", padx=15, pady=(12, 6))

        selector_row = ctk.CTkFrame(add_frame, fg_color="transparent")
        selector_row.pack(fill="x", padx=15, pady=(0, 12))
        selector_row.grid_columnconfigure(0, weight=1)

        # ComboBox de productos
        self.combo_producto = ctk.CTkComboBox(
            selector_row,
            values=["Cargando productos..."],
            height=36, corner_radius=8,
            fg_color="#1e1e1e", border_color="#333333",
            text_color="#ffffff",
            dropdown_fg_color="#1e1e1e",
            dropdown_text_color="#ffffff",
        )
        self.combo_producto.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        # Entry cantidad
        self.entry_cantidad = ctk.CTkEntry(
            selector_row,
            placeholder_text="Cant.", width=70, height=36,
            corner_radius=8, fg_color="#1e1e1e",
            border_color="#333333", text_color="#ffffff",
            placeholder_text_color="#666666",
        )
        self.entry_cantidad.grid(row=0, column=1, padx=(0, 8))

        # Botón añadir
        ctk.CTkButton(
            selector_row, text="+ Añadir",
            width=90, height=36,
            fg_color="#1e3a1e", hover_color="#2d572d",
            text_color="#1DB954", font=("Arial", 13, "bold"),
            command=self._agregar_producto,
        ).grid(row=0, column=2)

        # ── Carrito ───────────────────────────────────────────────────────────
        ctk.CTkLabel(
            self.frame, text="Productos en esta compra",
            font=("Arial", 13, "bold"), text_color="#aaaaaa",
        ).pack(anchor="w", padx=20, pady=(4, 4))

        self.scroll_carrito = ctk.CTkScrollableFrame(
            self.frame, fg_color="#0d0d0d", corner_radius=10,
        )
        self.scroll_carrito.pack(fill="both", expand=True, padx=20, pady=(0, 6))

        self.lbl_carrito_vacio = ctk.CTkLabel(
            self.scroll_carrito,
            text="Aún no has agregado ningún producto.",
            text_color="#555555",
        )
        self.lbl_carrito_vacio.pack(pady=20)

        # ── Total estimado ────────────────────────────────────────────────────
        total_row = ctk.CTkFrame(self.frame, fg_color="transparent")
        total_row.pack(fill="x", padx=20, pady=(4, 2))

        ctk.CTkLabel(
            total_row,
            text="* El precio de compra se ajustará al confirmar el envío.",
            font=("Arial", 11), text_color="#555555",
        ).pack(side="left")

        self.lbl_total = ctk.CTkLabel(
            total_row,
            text="Total estimado: $0.00",
            font=("Arial", 15, "bold"), text_color="#1DB954",
        )
        self.lbl_total.pack(side="right")

        # ── Feedback ──────────────────────────────────────────────────────────
        self.error_label = ctk.CTkLabel(
            self.frame, text="",
            font=("Arial", 12), text_color="#ff4d4d", wraplength=540,
        )
        self.error_label.pack(side="bottom", pady=4)

        # ── Botones ───────────────────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", padx=20, pady=(4, 16))

        ctk.CTkButton(
            btn_frame, text="Cancelar",
            fg_color="#1e1e1e", hover_color="#2b2b2b",
            text_color="#ffffff", height=42,
            font=("Arial", 13, "bold"),
            command=self.destroy,
        ).pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_confirmar = ctk.CTkButton(
            btn_frame, text="✔ Confirmar Compra",
            fg_color="#1DB954", hover_color="#179643",
            text_color="#000000", height=42,
            font=("Arial", 14, "bold"),
            command=self._confirmar_compra,
        )
        self.btn_confirmar.pack(side="right", fill="x", expand=True, padx=(10, 0))

        # ── Cargar productos de la BD ─────────────────────────────────────────
        self._cargar_productos()

    # ── Lógica interna ────────────────────────────────────────────────────────

    def _cargar_productos(self):
        try:
            from database.connection import obtener_productos_para_compra
            self._productos_db = obtener_productos_para_compra(self.rol)
            valores = [
                f"{p['nombre']} (Ref: {p['referencia']}) — ${float(p['precio_compra']):,.2f}"
                for p in self._productos_db
            ]
            if valores:
                self.combo_producto.configure(values=valores)
                self.combo_producto.set(valores[0])
            else:
                self.combo_producto.configure(values=["Sin productos registrados"])
                self.combo_producto.set("Sin productos registrados")
        except Exception as e:
            self.combo_producto.configure(values=[f"Error: {e}"])
            self.combo_producto.set(f"Error: {e}")

    def _agregar_producto(self):
        self.error_label.configure(text="", text_color="#ff4d4d")

        # Identificar producto seleccionado
        sel = self.combo_producto.get()
        idx = None
        for i, p in enumerate(self._productos_db):
            label = f"{p['nombre']} (Ref: {p['referencia']}) — ${float(p['precio_compra']):,.2f}"
            if label == sel:
                idx = i
                break

        if idx is None:
            self.error_label.configure(text="Selecciona un producto válido de la lista.")
            return

        # Validar cantidad
        cantidad_str = self.entry_cantidad.get().strip()
        if not cantidad_str:
            self.error_label.configure(text="Ingresa la cantidad.")
            return
        try:
            cantidad = int(cantidad_str)
            if cantidad <= 0:
                raise ValueError
        except ValueError:
            self.error_label.configure(text="La cantidad debe ser un número entero positivo.")
            return

        prod = self._productos_db[idx]

        # Si ya está en el carrito, sumar la cantidad
        for item in self._carrito:
            if item['idProducto'] == prod['idProducto']:
                item['cantidad'] += cantidad
                self._render_carrito()
                self.entry_cantidad.delete(0, "end")
                return

        # Añadir nuevo ítem
        self._carrito.append({
            'idProducto':   prod['idProducto'],
            'nombre':       prod['nombre'],
            'referencia':   prod['referencia'],
            'precio_compra': float(prod['precio_compra']),
            'cantidad':     cantidad,
        })
        self._render_carrito()
        self.entry_cantidad.delete(0, "end")

    def _render_carrito(self):
        for w in self.scroll_carrito.winfo_children():
            w.destroy()

        if not self._carrito:
            ctk.CTkLabel(
                self.scroll_carrito,
                text="Aún no has agregado ningún producto.",
                text_color="#555555",
            ).pack(pady=20)
            self.lbl_total.configure(text="Total estimado: $0.00")
            return

        # Encabezados
        hdr = ctk.CTkFrame(self.scroll_carrito, fg_color="#1e1e1e", corner_radius=6)
        hdr.pack(fill="x", pady=(0, 6))
        for col, w in zip([2, 1, 1, 1, 0], ["Producto", "Ref.", "P/Compra", "Cant.", "Subtotal"]):
            hdr.grid_columnconfigure(len(hdr.grid_slaves()), weight=max(col, 1))

        hdr.grid_columnconfigure(0, weight=2)
        hdr.grid_columnconfigure(1, weight=1)
        hdr.grid_columnconfigure(2, weight=1)
        hdr.grid_columnconfigure(3, weight=1)
        hdr.grid_columnconfigure(4, weight=1)
        hdr.grid_columnconfigure(5, weight=0)

        for ci, txt in enumerate(["Producto", "Ref.", "P/Compra", "Cant.", "Subtotal", ""]):
            ctk.CTkLabel(
                hdr, text=txt,
                font=("Arial", 12, "bold"), text_color="#1DB954",
            ).grid(row=0, column=ci, padx=8, pady=8, sticky="w")

        total = 0.0
        for idx, item in enumerate(self._carrito):
            subtotal = item['precio_compra'] * item['cantidad']
            total += subtotal

            bg = "#141414" if idx % 2 == 0 else "#0f0f0f"
            row = ctk.CTkFrame(self.scroll_carrito, fg_color=bg, corner_radius=6)
            row.pack(fill="x", pady=2)

            for ci, w in enumerate([2, 1, 1, 1, 1, 0]):
                row.grid_columnconfigure(ci, weight=max(w, 1) if ci < 5 else 0)

            ctk.CTkLabel(row, text=item['nombre'],
                         font=("Arial", 13), text_color="#ffffff").grid(row=0, column=0, padx=8, pady=8, sticky="w")
            ctk.CTkLabel(row, text=item['referencia'],
                         font=("Arial", 12), text_color="#aaaaaa").grid(row=0, column=1, padx=8, pady=8, sticky="w")
            ctk.CTkLabel(row, text=f"${item['precio_compra']:,.2f}",
                         font=("Arial", 12), text_color="#cccccc").grid(row=0, column=2, padx=8, pady=8, sticky="w")
            ctk.CTkLabel(row, text=str(item['cantidad']),
                         font=("Arial", 13, "bold"), text_color="#ffffff").grid(row=0, column=3, padx=8, pady=8, sticky="w")
            ctk.CTkLabel(row, text=f"${subtotal:,.2f}",
                         font=("Arial", 13, "bold"), text_color="#1DB954").grid(row=0, column=4, padx=8, pady=8, sticky="w")

            # Botón eliminar ítem
            ctk.CTkButton(
                row, text="✕", width=28, height=28,
                fg_color="#3a1414", hover_color="#5a1f1f",
                text_color="#ff4d4d", font=("Arial", 13, "bold"),
                command=lambda i=idx: self._eliminar_item(i),
            ).grid(row=0, column=5, padx=(4, 8), pady=4)

        self.lbl_total.configure(text=f"Total estimado: ${total:,.2f}")

    def _eliminar_item(self, idx):
        if 0 <= idx < len(self._carrito):
            self._carrito.pop(idx)
        self._render_carrito()

    def _confirmar_compra(self):
        self.error_label.configure(text="", text_color="#ff4d4d")

        if not self._carrito:
            self.error_label.configure(text="Agrega al menos un producto antes de confirmar.")
            return

        if not self.id_emp:
            self.error_label.configure(text="No se pudo identificar al empleado. Inicia sesión nuevamente.")
            return

        try:
            from database.connection import insertar_compra

            productos = [
                {'idProducto': item['idProducto'], 'cantidad': item['cantidad']}
                for item in self._carrito
            ]

            id_compra = insertar_compra(
                id_proveedor=self.proveedor['idProveedor'],
                id_empleado=self.id_emp,
                productos=productos,
                rol=self.rol,
            )

            self.error_label.configure(
                text=f"¡Compra #{id_compra} registrada exitosamente!", text_color="#1DB954"
            )
            self.btn_confirmar.configure(state="disabled")

            # Refrescar el detalle del proveedor en la ventana padre
            if self.master and hasattr(self.master, 'mostrar_detalle_proveedor'):
                self.master.mostrar_detalle_proveedor(self.proveedor)

            self.after(1200, self.destroy)

        except Exception as e:
            self.error_label.configure(text=str(e), text_color="#ff4d4d")
