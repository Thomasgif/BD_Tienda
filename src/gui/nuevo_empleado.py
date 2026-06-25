import customtkinter as ctk

class NuevoEmpleadoWindow(ctk.CTkToplevel):
    def __init__(self, master=None, empleado_datos=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        
        self.empleado_datos = empleado_datos
        self.es_edicion = empleado_datos is not None
        
        self.rol = getattr(master, 'rol', 1) # Rol del usuario logueado (debería ser 1 - Gerente)
        
        # Configurar la ventana
        if self.es_edicion:
            self.title("Editar Empleado")
        else:
            self.title("Registrar Nuevo Empleado")
            
        self.geometry("460x650")
        self.resizable(False, False)
        self.configure(fg_color="#050505")
        
        # Asegurar que la ventana aparezca por encima y tome el foco
        self.transient(master)
        self.grab_set()
        
        # Frame Principal contenedor
        self.frame = ctk.CTkFrame(
            self,
            corner_radius=15,
            fg_color="#121212",
            border_color="#1DB954",
            border_width=1
        )
        self.frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        # Título de la ventana
        titulo_texto = "EDITAR EMPLEADO" if self.es_edicion else "NUEVO EMPLEADO"
        self.title_label = ctk.CTkLabel(
            self.frame, 
            text=titulo_texto, 
            font=("Arial", 20, "bold"), 
            text_color="#1DB954"
        )
        self.title_label.pack(side="top", pady=(20, 10))
        
        # Contenedor para los campos del formulario
        self.form_container = ctk.CTkScrollableFrame(self.frame, fg_color="transparent")
        self.form_container.pack(side="top", fill="both", expand=True, padx=20, pady=(5, 10))
        
        # Estilo común para inputs
        input_style = {
            "height": 38,
            "corner_radius": 8,
            "fg_color": "#1e1e1e",
            "border_color": "#2a2a2a",
            "text_color": "#ffffff",
            "placeholder_text_color": "#666666"
        }
        
        # 1. Nombre Completo
        self.lbl_nombre = ctk.CTkLabel(self.form_container, text="Nombre Completo *", font=("Arial", 12, "bold"), text_color="#aaaaaa")
        self.lbl_nombre.pack(anchor="w", pady=(5, 2))
        self.entry_nombre = ctk.CTkEntry(self.form_container, placeholder_text="Ej: Juan Pérez", **input_style)
        self.entry_nombre.pack(fill="x", pady=(0, 10))
        
        # 2. Documento
        self.lbl_documento = ctk.CTkLabel(self.form_container, text="Documento de Identidad *", font=("Arial", 12, "bold"), text_color="#aaaaaa")
        self.lbl_documento.pack(anchor="w", pady=(5, 2))
        self.entry_documento = ctk.CTkEntry(self.form_container, placeholder_text="Ej: 10203040", **input_style)
        self.entry_documento.pack(fill="x", pady=(0, 10))
        
        # 3. Pago por Hora
        self.lbl_pago = ctk.CTkLabel(self.form_container, text="Pago por Hora ($) *", font=("Arial", 12, "bold"), text_color="#aaaaaa")
        self.lbl_pago.pack(anchor="w", pady=(5, 2))
        self.entry_pago = ctk.CTkEntry(self.form_container, placeholder_text="Ej: 15.00", **input_style)
        self.entry_pago.pack(fill="x", pady=(0, 10))
        
        # 4. Horas Trabajadas (solo editable si es edición, por defecto 0 para nuevos)
        self.lbl_horas = ctk.CTkLabel(self.form_container, text="Horas Trabajadas", font=("Arial", 12, "bold"), text_color="#aaaaaa")
        self.lbl_horas.pack(anchor="w", pady=(5, 2))
        self.entry_horas = ctk.CTkEntry(self.form_container, placeholder_text="Ej: 0.00", **input_style)
        self.entry_horas.pack(fill="x", pady=(0, 10))
        if not self.es_edicion:
            self.entry_horas.insert(0, "0.0")
            self.entry_horas.configure(state="disabled") # por defecto inicia en 0 horas
            
        # 5. Teléfono
        self.lbl_telefono = ctk.CTkLabel(self.form_container, text="Teléfono", font=("Arial", 12, "bold"), text_color="#aaaaaa")
        self.lbl_telefono.pack(anchor="w", pady=(5, 2))
        self.entry_telefono = ctk.CTkEntry(self.form_container, placeholder_text="Ej: 3001234567", **input_style)
        self.entry_telefono.pack(fill="x", pady=(0, 10))
        
        # 6. Correo Electrónico
        self.lbl_correo = ctk.CTkLabel(self.form_container, text="Correo Electrónico", font=("Arial", 12, "bold"), text_color="#aaaaaa")
        self.lbl_correo.pack(anchor="w", pady=(5, 2))
        self.entry_correo = ctk.CTkEntry(self.form_container, placeholder_text="Ej: empleado@tienda.com", **input_style)
        self.entry_correo.pack(fill="x", pady=(0, 10))
        
        # 7. Rol
        self.lbl_rol = ctk.CTkLabel(self.form_container, text="Rol del Empleado *", font=("Arial", 12, "bold"), text_color="#aaaaaa")
        self.lbl_rol.pack(anchor="w", pady=(5, 2))
        self.combo_rol = ctk.CTkComboBox(
            self.form_container, 
            values=["Vendedor / Empleado", "Gerente / Administrador"], 
            height=38,
            corner_radius=8,
            fg_color="#1e1e1e",
            border_color="#2a2a2a",
            text_color="#ffffff"
        )
        self.combo_rol.pack(fill="x", pady=(0, 15))
        self.combo_rol.set("Vendedor / Empleado")
        
        # Botón eliminar (Solo en edición)
        if self.es_edicion:
            self.btn_eliminar = ctk.CTkButton(
                self.form_container,
                text="❌ Eliminar Empleado",
                fg_color="#4a0f0f",
                hover_color="#731515",
                text_color="#ffffff",
                height=38,
                font=("Arial", 12, "bold"),
                command=self.confirmar_eliminacion
            )
            self.btn_eliminar.pack(fill="x", pady=(10, 5))

        # Mensaje de error / éxito
        self.error_label = ctk.CTkLabel(self.frame, text="", font=("Arial", 12), text_color="#ff4d4d", wraplength=380)
        self.error_label.pack(side="bottom", pady=5)
        
        # Botonera de abajo
        self.button_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.button_frame.pack(side="bottom", fill="x", padx=25, pady=(5, 15))
        
        self.btn_cancelar = ctk.CTkButton(
            self.button_frame, 
            text="Cancelar", 
            fg_color="#1e1e1e", 
            hover_color="#2b2b2b",
            text_color="#ffffff",
            height=40,
            font=("Arial", 13, "bold"),
            command=self.destroy
        )
        self.btn_cancelar.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.btn_guardar = ctk.CTkButton(
            self.button_frame, 
            text="Guardar", 
            fg_color="#1DB954", 
            hover_color="#179643",
            text_color="#000000",
            height=40,
            font=("Arial", 13, "bold"),
            command=self.guardar_empleado
        )
        self.btn_guardar.pack(side="right", fill="x", expand=True, padx=(10, 0))
        
        # Si es edición, precargar los campos
        if self.es_edicion:
            self.cargar_datos()

    def cargar_datos(self):
        self.entry_nombre.insert(0, self.empleado_datos.get('nombre', ''))
        self.entry_documento.insert(0, self.empleado_datos.get('documento', ''))
        self.entry_pago.insert(0, str(self.empleado_datos.get('pago_hora', '')))
        self.entry_horas.insert(0, str(self.empleado_datos.get('trabajo_hora', '')))
        self.entry_telefono.insert(0, self.empleado_datos.get('telefono', '') or '')
        self.entry_correo.insert(0, self.empleado_datos.get('correo', '') or '')
        
        rol_val = self.empleado_datos.get('rol', 0)
        if rol_val == 1:
            self.combo_rol.set("Gerente / Administrador")
        else:
            self.combo_rol.set("Vendedor / Empleado")

    def guardar_empleado(self):
        self.error_label.configure(text="", text_color="#ff4d4d")
        
        nombre = self.entry_nombre.get().strip()
        documento = self.entry_documento.get().strip()
        pago_hora_str = self.entry_pago.get().strip()
        horas_str = self.entry_horas.get().strip()
        telefono = self.entry_telefono.get().strip() or None
        correo = self.entry_correo.get().strip() or None
        rol_combo = self.combo_rol.get()
        
        # Validaciones
        if not nombre or not documento or not pago_hora_str or not horas_str:
            self.error_label.configure(text="Por favor complete los campos obligatorios (*).")
            return
            
        try:
            pago_hora = float(pago_hora_str)
            horas = float(horas_str)
            if pago_hora < 0 or horas < 0:
                raise ValueError("Los valores numéricos no pueden ser negativos.")
        except ValueError:
            self.error_label.configure(text="El Pago por Hora y las Horas Trabajadas deben ser números válidos y positivos.")
            return
            
        rol_empleado = 1 if rol_combo == "Gerente / Administrador" else 0
        
        try:
            from database.connection import insertar_empleado, actualizar_empleado
            
            if self.es_edicion:
                id_empleado = self.empleado_datos['idEmpleado']
                actualizar_empleado(
                    id_empleado=id_empleado,
                    nombre=nombre,
                    documento=documento,
                    trabajo_hora=horas,
                    pago_hora=pago_hora,
                    telefono=telefono,
                    correo=correo,
                    rol_empleado=rol_empleado,
                    rol=self.rol
                )
                mensaje_exito = "¡Empleado actualizado con éxito!"
            else:
                insertar_empleado(
                    nombre=nombre,
                    documento=documento,
                    trabajo_hora=horas,
                    pago_hora=pago_hora,
                    telefono=telefono,
                    correo=correo,
                    rol_empleado=rol_empleado,
                    rol=self.rol
                )
                mensaje_exito = "¡Empleado registrado con éxito!"
                
            self.error_label.configure(text=mensaje_exito, text_color="#1DB954")
            self.btn_guardar.configure(state="disabled")
            
            if self.master and hasattr(self.master, "cargar_lista_empleados"):
                self.master.cargar_lista_empleados()
                
            self.after(1000, self.destroy)
        except Exception as e:
            self.error_label.configure(text=str(e), text_color="#ff4d4d")

    def confirmar_eliminacion(self):
        # Crear ventana emergente de confirmación
        modal = ctk.CTkToplevel(self)
        modal.title("Confirmar Eliminación")
        modal.geometry("320x180")
        modal.resizable(False, False)
        modal.configure(fg_color="#0b0b0b")
        modal.transient(self)
        modal.grab_set()
        
        lbl = ctk.CTkLabel(
            modal, 
            text=f"¿Está seguro de que desea eliminar a\n{self.empleado_datos['nombre']}?", 
            font=("Arial", 12),
            text_color="#ffffff"
        )
        lbl.pack(pady=25)
        
        btn_frame = ctk.CTkFrame(modal, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20)
        
        btn_cancelar = ctk.CTkButton(
            btn_frame, 
            text="No", 
            fg_color="#1e1e1e", 
            hover_color="#2b2b2b",
            height=32,
            command=modal.destroy
        )
        btn_cancelar.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        btn_si = ctk.CTkButton(
            btn_frame, 
            text="Sí, Eliminar", 
            fg_color="#a82323", 
            hover_color="#bd3535",
            height=32,
            command=lambda: self.ejecutar_eliminacion(modal)
        )
        btn_si.pack(side="right", fill="x", expand=True, padx=(10, 0))

    def ejecutar_eliminacion(self, modal_confirmacion):
        modal_confirmacion.destroy()
        try:
            from database.connection import eliminar_empleado
            eliminar_empleado(id_empleado=self.empleado_datos['idEmpleado'], rol=self.rol)
            
            self.error_label.configure(text="¡Empleado eliminado con éxito!", text_color="#1DB954")
            self.btn_guardar.configure(state="disabled")
            
            if self.master and hasattr(self.master, "cargar_lista_empleados"):
                self.master.cargar_lista_empleados()
                
            self.after(1000, self.destroy)
        except Exception as e:
            self.error_label.configure(text=str(e), text_color="#ff4d4d")
