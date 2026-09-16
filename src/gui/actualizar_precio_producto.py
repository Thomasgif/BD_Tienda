import customtkinter as ctk


class ActualizarPrecioProductoWindow(ctk.CTkToplevel):
    """
    Ventana modal para actualizar el precio de venta (valor venta) de un producto.
    Solo disponible para usuarios con rol Gerente (rol = 1).
    Muestra todos los atributos del producto, incluyendo la descripción, de forma detallada y de solo lectura.
    """

    def __init__(self, master=None, producto_datos=None, rol=None, on_success=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.producto_datos = producto_datos or {}
        self.on_success = on_success
        if rol is not None:
            self.rol = rol
        else:
            self.rol = getattr(master, 'rol', 0)

        # ── Configurar ventana ────────────────────────────────────────────────
        self.title("Detalle y Actualización de Valor Venta")
        self.geometry("500x640")
        self.resizable(False, False)
        self.configure(fg_color="#050505")
        self.transient(master)
        self.grab_set()

        # ── Frame contenedor principal ───────────────────────────────────────
        self.frame = ctk.CTkFrame(
            self,
            corner_radius=15,
            fg_color="#121212",
            border_color="#1DB954",
            border_width=1,
        )
        self.frame.pack(padx=20, pady=20, fill="both", expand=True)

        # Título
        ctk.CTkLabel(
            self.frame,
            text="DETALLE DE PRODUCTO",
            font=("Arial", 20, "bold"),
            text_color="#1DB954",
        ).pack(side="top", pady=(20, 10))

        # ── Contenido de los atributos (Solo Lectura) ──────────────────────────
        self.info_container = ctk.CTkScrollableFrame(self.frame, fg_color="transparent")
        self.info_container.pack(side="top", fill="both", expand=True, padx=20, pady=(5, 10))

        # Estilo para inputs de solo lectura
        _readonly_style = {
            "height": 38,
            "corner_radius": 8,
            "fg_color": "#181818",
            "border_color": "#222222",
            "text_color": "#888888",
        }

        # 1. ID de Producto
        ctk.CTkLabel(self.info_container, text="ID Producto", font=("Arial", 12, "bold"), text_color="#888888").pack(anchor="w", pady=(5, 2))
        self.entry_id = ctk.CTkEntry(self.info_container, **_readonly_style)
        self.entry_id.insert(0, str(self.producto_datos.get('idProducto', '')))
        self.entry_id.configure(state="disabled")
        self.entry_id.pack(fill="x", pady=(0, 10))

        # 2. Nombre
        ctk.CTkLabel(self.info_container, text="Nombre", font=("Arial", 12, "bold"), text_color="#888888").pack(anchor="w", pady=(5, 2))
        self.entry_nombre = ctk.CTkEntry(self.info_container, **_readonly_style)
        self.entry_nombre.insert(0, self.producto_datos.get('nombre', ''))
        self.entry_nombre.configure(state="disabled")
        self.entry_nombre.pack(fill="x", pady=(0, 10))

        # 3. Referencia
        ctk.CTkLabel(self.info_container, text="Referencia", font=("Arial", 12, "bold"), text_color="#888888").pack(anchor="w", pady=(5, 2))
        self.entry_ref = ctk.CTkEntry(self.info_container, **_readonly_style)
        self.entry_ref.insert(0, self.producto_datos.get('referencia', ''))
        self.entry_ref.configure(state="disabled")
        self.entry_ref.pack(fill="x", pady=(0, 10))

        # 4. Precio de Compra (Costo)
        ctk.CTkLabel(self.info_container, text="Precio Compra (Costo)", font=("Arial", 12, "bold"), text_color="#888888").pack(anchor="w", pady=(5, 2))
        precio_c = self.producto_datos.get('precio_compra', 0.0)
        self.entry_precio_compra = ctk.CTkEntry(self.info_container, **_readonly_style)
        self.entry_precio_compra.insert(0, f"${float(precio_c or 0):,.2f}")
        self.entry_precio_compra.configure(state="disabled")
        self.entry_precio_compra.pack(fill="x", pady=(0, 10))

        # 5. Stock (Bodega)
        ctk.CTkLabel(self.info_container, text="Stock en Bodega", font=("Arial", 12, "bold"), text_color="#888888").pack(anchor="w", pady=(5, 2))
        self.entry_stock = ctk.CTkEntry(self.info_container, **_readonly_style)
        self.entry_stock.insert(0, f"{self.producto_datos.get('bodega', 0)} unidades")
        self.entry_stock.configure(state="disabled")
        self.entry_stock.pack(fill="x", pady=(0, 10))

        # 6. Descripción
        descripcion= self.producto_datos.get('descripcion', '') if None!=self.producto_datos.get('descripcion', '') else  "    "
        ctk.CTkLabel(self.info_container, text="Descripción", font=("Arial", 12, "bold"), text_color="#888888").pack(anchor="w", pady=(5, 2))
        self.txt_desc = ctk.CTkTextbox(self.info_container, height=60, corner_radius=8, fg_color="#181818", border_color="#222222", text_color="#888888")
        self.txt_desc.insert("1.0", descripcion )
        self.txt_desc.configure(state="disabled")
        self.txt_desc.pack(fill="x", pady=(0, 10))

        # Separador estético
        ctk.CTkFrame(self.info_container, height=1, fg_color="#333333").pack(fill="x", pady=15)

        # ── Formulario editable: Precio Venta ─────────────────────────────────
        ctk.CTkLabel(self.info_container, text="Precio Venta (Valor Venta) *", font=("Arial", 13, "bold"), text_color="#1DB954").pack(anchor="w", pady=(5, 2))
        
        self.entry_precio_venta = ctk.CTkEntry(
            self.info_container,
            height=40,
            corner_radius=8,
            fg_color="#1e1e1e",
            border_color="#1DB954",
            text_color="#ffffff",
            placeholder_text="Ej: 25000.00"
        )
        # Mostrar el precio de venta actual en el campo editable
        precio_v = self.producto_datos.get('precio_venta', 0.0)
        self.entry_precio_venta.insert(0, f"{float(precio_v or 0):.2f}")
        self.entry_precio_venta.pack(fill="x", pady=(0, 15))

        # ── Mensaje de estado / errores ──────────────────────────────────────
        self.status_label = ctk.CTkLabel(
            self.frame, text="", font=("Arial", 12),
            text_color="#ff4d4d", wraplength=400,
        )
        self.status_label.pack(side="bottom", pady=5)

        # Restringir acción si no es gerente
        if self.rol != 1:
            self.status_label.configure(text="⚠ Acceso restringido. Solo el gerente puede actualizar precios.", text_color="#ff4d4d")
            self.entry_precio_venta.configure(state="disabled", border_color="#555555")

        # ── Botones ───────────────────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", padx=25, pady=(5, 15))

        ctk.CTkButton(
            btn_frame, text="Cancelar",
            fg_color="#1e1e1e", hover_color="#2b2b2b",
            text_color="#ffffff", height=40,
            font=("Arial", 13, "bold"),
            command=self.destroy,
        ).pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_guardar = ctk.CTkButton(
            btn_frame, text="Guardar Cambios",
            fg_color="#1DB954", hover_color="#179643",
            text_color="#000000", height=40,
            font=("Arial", 13, "bold"),
            command=self.guardar_precio,
        )
        if self.rol != 1:
            self.btn_guardar.configure(state="disabled", fg_color="#333333", text_color="#777777")
        self.btn_guardar.pack(side="right", fill="x", expand=True, padx=(10, 0))

    # ── Guardar Cambios ───────────────────────────────────────────────────────
    def guardar_precio(self):
        if self.rol != 1:
            self.status_label.configure(text="⚠ Permiso denegado.")
            return

        self.status_label.configure(text="", text_color="#ff4d4d")
        precio_str = self.entry_precio_venta.get().strip()

        if not precio_str:
            self.status_label.configure(text="Por favor ingrese el nuevo precio de venta.")
            return

        try:
            precio_val = float(precio_str)
            if precio_val <= 0:
                raise ValueError()
        except ValueError:
            self.status_label.configure(text="El precio de venta debe ser un número positivo válido.")
            return

        try:
            from database.connection import actualizar_precio_producto
            actualizar_precio_producto(
                id_producto=self.producto_datos['idProducto'],
                precio_venta=precio_val,
                rol=self.rol
            )

            self.status_label.configure(text="✔ ¡Precio de venta actualizado con éxito!", text_color="#1DB954")
            self.btn_guardar.configure(state="disabled")
            self.entry_precio_venta.configure(state="disabled")

            # Refrescar productos en la ventana padre
            if self.on_success:
                try:
                    self.on_success()
                except Exception as ex:
                    print(f"Error en on_success: {ex}")

            if self.master and hasattr(self.master, 'actualizar_productos_tab'):
                self.master.actualizar_productos_tab()

            self.after(1200, self.destroy)

        except Exception as e:
            self.status_label.configure(text=str(e), text_color="#ff4d4d")
