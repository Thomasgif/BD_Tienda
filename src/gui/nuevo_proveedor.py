import customtkinter as ctk


class NuevoProveedorWindow(ctk.CTkToplevel):
    """
    Ventana modal para crear un nuevo proveedor o editar uno existente.
    Solo disponible para usuarios con rol Gerente (rol = 1).
    """

    def __init__(self, master=None, proveedor_datos=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.proveedor_datos = proveedor_datos
        self.es_edicion = proveedor_datos is not None
        self.rol = getattr(master, 'rol', 1)

        # ── Configurar ventana ────────────────────────────────────────────────
        self.title("Editar Proveedor" if self.es_edicion else "Registrar Nuevo Proveedor")
        self.geometry("460x560")
        self.resizable(False, False)
        self.configure(fg_color="#050505")
        self.transient(master)
        self.grab_set()

        # ── Frame contenedor ─────────────────────────────────────────────────
        self.frame = ctk.CTkFrame(
            self,
            corner_radius=15,
            fg_color="#121212",
            border_color="#1DB954",
            border_width=1,
        )
        self.frame.pack(padx=20, pady=20, fill="both", expand=True)

        # Título
        titulo = "EDITAR PROVEEDOR" if self.es_edicion else "NUEVO PROVEEDOR"
        ctk.CTkLabel(
            self.frame,
            text=titulo,
            font=("Arial", 20, "bold"),
            text_color="#1DB954",
        ).pack(side="top", pady=(20, 10))

        # ── Formulario ────────────────────────────────────────────────────────
        self.form_container = ctk.CTkScrollableFrame(self.frame, fg_color="transparent")
        self.form_container.pack(side="top", fill="both", expand=True, padx=20, pady=(5, 10))

        _input = {
            "height": 38,
            "corner_radius": 8,
            "fg_color": "#1e1e1e",
            "border_color": "#2a2a2a",
            "text_color": "#ffffff",
            "placeholder_text_color": "#666666",
        }

        # 1. Nombre
        ctk.CTkLabel(self.form_container, text="Nombre *", font=("Arial", 12, "bold"), text_color="#aaaaaa").pack(anchor="w", pady=(5, 2))
        self.entry_nombre = ctk.CTkEntry(self.form_container, placeholder_text="Ej: Distribuidora ABC", **_input)
        self.entry_nombre.pack(fill="x", pady=(0, 10))

        # 2. NIT
        ctk.CTkLabel(self.form_container, text="NIT", font=("Arial", 12, "bold"), text_color="#aaaaaa").pack(anchor="w", pady=(5, 2))
        self.entry_nit = ctk.CTkEntry(self.form_container, placeholder_text="Ej: 9001234567", **_input)
        self.entry_nit.pack(fill="x", pady=(0, 10))

        # 3. Teléfono
        ctk.CTkLabel(self.form_container, text="Teléfono", font=("Arial", 12, "bold"), text_color="#aaaaaa").pack(anchor="w", pady=(5, 2))
        self.entry_telefono = ctk.CTkEntry(self.form_container, placeholder_text="Ej: 6014567890", **_input)
        self.entry_telefono.pack(fill="x", pady=(0, 10))

        # 4. Correo
        ctk.CTkLabel(self.form_container, text="Correo Electrónico", font=("Arial", 12, "bold"), text_color="#aaaaaa").pack(anchor="w", pady=(5, 2))
        self.entry_correo = ctk.CTkEntry(self.form_container, placeholder_text="Ej: ventas@proveedor.com", **_input)
        self.entry_correo.pack(fill="x", pady=(0, 10))

        # 5. Dirección
        ctk.CTkLabel(self.form_container, text="Dirección", font=("Arial", 12, "bold"), text_color="#aaaaaa").pack(anchor="w", pady=(5, 2))
        self.entry_direccion = ctk.CTkEntry(self.form_container, placeholder_text="Ej: Calle 10 # 20-30, Bogotá", **_input)
        self.entry_direccion.pack(fill="x", pady=(0, 10))

        # ── Feedback ──────────────────────────────────────────────────────────
        self.error_label = ctk.CTkLabel(
            self.frame, text="", font=("Arial", 12),
            text_color="#ff4d4d", wraplength=380,
        )
        self.error_label.pack(side="bottom", pady=5)

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
            btn_frame, text="Guardar",
            fg_color="#1DB954", hover_color="#179643",
            text_color="#000000", height=40,
            font=("Arial", 13, "bold"),
            command=self.guardar_proveedor,
        )
        self.btn_guardar.pack(side="right", fill="x", expand=True, padx=(10, 0))

        # ── Precargar datos en modo edición ───────────────────────────────────
        if self.es_edicion:
            self._cargar_datos()

    # ── Cargar datos al editar ────────────────────────────────────────────────
    def _cargar_datos(self):
        d = self.proveedor_datos
        self.entry_nombre.insert(0, d.get('nombre', ''))
        self.entry_nit.insert(0, d.get('nit', '') or '')
        self.entry_telefono.insert(0, d.get('telefono', '') or '')
        self.entry_correo.insert(0, d.get('correo', '') or '')
        self.entry_direccion.insert(0, d.get('direccion', '') or '')

    # ── Guardar ───────────────────────────────────────────────────────────────
    def guardar_proveedor(self):
        self.error_label.configure(text="", text_color="#ff4d4d")

        nombre    = self.entry_nombre.get().strip()
        nit       = self.entry_nit.get().strip()
        telefono  = self.entry_telefono.get().strip()
        correo    = self.entry_correo.get().strip()
        direccion = self.entry_direccion.get().strip()

        if not nombre:
            self.error_label.configure(text="El nombre del proveedor es obligatorio.")
            return

        if len(nombre) > 20:
            self.error_label.configure(text="El nombre no puede superar los 20 caracteres.")
            return

        try:
            from database.connection import insertar_proveedor, actualizar_proveedor

            if self.es_edicion:
                actualizar_proveedor(
                    id_proveedor=self.proveedor_datos['idProveedor'],
                    nombre=nombre, nit=nit, telefono=telefono,
                    correo=correo, direccion=direccion,
                    rol=self.rol,
                )
                msg = "¡Proveedor actualizado con éxito!"
            else:
                insertar_proveedor(
                    nombre=nombre, nit=nit, telefono=telefono,
                    correo=correo, direccion=direccion,
                    rol=self.rol,
                )
                msg = "¡Proveedor registrado con éxito!"

            self.error_label.configure(text=msg, text_color="#1DB954")
            self.btn_guardar.configure(state="disabled")

            # Refrescar lista en la ventana padre
            if self.master and hasattr(self.master, 'actualizar_lista_proveedores'):
                self.master.actualizar_lista_proveedores()

            self.after(1000, self.destroy)

        except Exception as e:
            self.error_label.configure(text=str(e), text_color="#ff4d4d")
