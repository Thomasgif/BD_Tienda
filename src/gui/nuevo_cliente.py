import customtkinter as ctk
from database.connection import insertar_cliente, actualizar_cliente

class NuevoClienteWindow(ctk.CTkToplevel):
    def __init__(self, master=None, cliente_datos=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        
        self.cliente_datos = cliente_datos
        self.es_edicion = cliente_datos is not None
        
        # Heredar el rol del empleado desde la ventana padre (VendedorWindow)
        # Esto garantiza que las operaciones se ejecuten con el usuario SQL correcto.
        self.rol = getattr(master, 'rol', 0)
        
        # Configurar la ventana
        if self.es_edicion:
            self.title("Editar Cliente")
        else:
            self.title("Crear Nuevo Cliente")
            
        self.geometry("450x700")
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
        titulo_texto = "EDITAR CLIENTE" if self.es_edicion else "NUEVO CLIENTE"
        self.title_label = ctk.CTkLabel(
            self.frame, 
            text=titulo_texto, 
            font=("Arial", 22, "bold"), 
            text_color="#1DB954"
        )
        self.title_label.pack(side="top", pady=(20, 15))
        
        # Contenedor para los campos del formulario (se empaquetará al final de la inicialización)
        self.form_container = ctk.CTkFrame(self.frame, fg_color="transparent")
        
        # Estilo común para inputs
        input_style = {
            "height": 38,
            "corner_radius": 8,
            "fg_color": "#1e1e1e",
            "border_color": "#2a2a2a",
            "text_color": "#ffffff",
            "placeholder_text_color": "#666666"
        }
        
        # 1. Documento
        self.lbl_doc = ctk.CTkLabel(self.form_container, text="Documento / Cédula * (Máx. 11 caract.)", font=("Arial", 12, "bold"), text_color="#aaaaaa")
        self.lbl_doc.pack(anchor="w", pady=(5, 2))
        self.entry_doc = ctk.CTkEntry(self.form_container, placeholder_text="Ej: 10203040", **input_style)
        self.entry_doc.pack(fill="x", pady=(0, 10))
        
        # 2. Nombre
        self.lbl_nombre = ctk.CTkLabel(self.form_container, text="Nombre * (Máx. 20 caract.)", font=("Arial", 12, "bold"), text_color="#aaaaaa")
        self.lbl_nombre.pack(anchor="w", pady=(5, 2))
        self.entry_nombre = ctk.CTkEntry(self.form_container, placeholder_text="Ej: Juan", **input_style)
        self.entry_nombre.pack(fill="x", pady=(0, 10))
        
        # 3. Apellidos
        self.lbl_apellidos = ctk.CTkLabel(self.form_container, text="Apellidos * (Máx. 50 caract.)", font=("Arial", 12, "bold"), text_color="#aaaaaa")
        self.lbl_apellidos.pack(anchor="w", pady=(5, 2))
        self.entry_apellidos = ctk.CTkEntry(self.form_container, placeholder_text="Ej: Perez Gomez", **input_style)
        self.entry_apellidos.pack(fill="x", pady=(0, 10))
        
        # 4. Teléfono
        self.lbl_tel = ctk.CTkLabel(self.form_container, text="Teléfono (Opcional - Máx. 15 caract.)", font=("Arial", 12, "bold"), text_color="#aaaaaa")
        self.lbl_tel.pack(anchor="w", pady=(5, 2))
        self.entry_tel = ctk.CTkEntry(self.form_container, placeholder_text="Ej: 3001234567", **input_style)
        self.entry_tel.pack(fill="x", pady=(0, 10))
        
        # 5. Correo
        self.lbl_correo = ctk.CTkLabel(self.form_container, text="Correo Electrónico (Opcional - Máx. 30 caract.)", font=("Arial", 12, "bold"), text_color="#aaaaaa")
        self.lbl_correo.pack(anchor="w", pady=(5, 2))
        self.entry_correo = ctk.CTkEntry(self.form_container, placeholder_text="Ej: juan@correo.com", **input_style)
        self.entry_correo.pack(fill="x", pady=(0, 10))
        
        # 6. Dirección
        self.lbl_dir = ctk.CTkLabel(self.form_container, text="Dirección (Opcional - Máx. 50 caract.)", font=("Arial", 12, "bold"), text_color="#aaaaaa")
        self.lbl_dir.pack(anchor="w", pady=(5, 2))
        self.entry_dir = ctk.CTkEntry(self.form_container, placeholder_text="Ej: Calle 10 # 5-40", **input_style)
        self.entry_dir.pack(fill="x", pady=(0, 10))
        
        # Mensaje de error / éxito (empaquetado abajo)
        self.error_label = ctk.CTkLabel(self.frame, text="", font=("Arial", 12), text_color="#ff4d4d", wraplength=380)
        self.error_label.pack(side="bottom", pady=5)
        
        # Botonera (empaquetada abajo de todo)
        self.button_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.button_frame.pack(side="bottom", fill="x", padx=25, pady=(5, 20))
        
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
            command=self.guardar_cliente
        )
        self.btn_guardar.pack(side="right", fill="x", expand=True, padx=(10, 0))
        
        # Ahora que el título (arriba), y la botonera/error (abajo) están configurados,
        # expandimos el contenedor del formulario para ocupar todo el espacio del centro.
        self.form_container.pack(side="top", fill="both", expand=True, padx=25)
        
        # Si es edición, precargar los campos
        if self.es_edicion:
            self.cargar_datos()

    def cargar_datos(self):
        # Insertar valores en las entradas
        self.entry_doc.insert(0, self.cliente_datos.get('documento', ''))
        self.entry_nombre.insert(0, self.cliente_datos.get('nombre', ''))
        self.entry_apellidos.insert(0, self.cliente_datos.get('apellidos', ''))
        self.entry_tel.insert(0, self.cliente_datos.get('telefono', '') or '')
        self.entry_correo.insert(0, self.cliente_datos.get('correo', '') or '')
        self.entry_dir.insert(0, self.cliente_datos.get('direccion', '') or '')

    def guardar_cliente(self):
        # Limpiar error
        self.error_label.configure(text="", text_color="#ff4d4d")
        
        # Obtener valores de los campos
        doc = self.entry_doc.get().strip()
        nombre = self.entry_nombre.get().strip()
        apellidos = self.entry_apellidos.get().strip()
        tel = self.entry_tel.get().strip()
        correo = self.entry_correo.get().strip()
        direccion = self.entry_dir.get().strip()
        
        # VALIDACIONES FRONTEND
        # 1. Campos obligatorios
        if not doc or not nombre or not apellidos:
            self.error_label.configure(text="Por favor complete todos los campos marcados con asterisco (*).")
            return
            
        # 2. Longitudes máximas
        if len(doc) > 11:
            self.error_label.configure(text="El Documento no puede superar los 11 caracteres.")
            return
        if len(nombre) > 20:
            self.error_label.configure(text="El Nombre no puede superar los 20 caracteres.")
            return
        if len(apellidos) > 50:
            self.error_label.configure(text="Los Apellidos no pueden superar los 50 caracteres.")
            return
        if tel and len(tel) > 15:
            self.error_label.configure(text="El Teléfono no puede superar los 15 caracteres.")
            return
        if correo and len(correo) > 30:
            self.error_label.configure(text="El Correo no puede superar los 30 caracteres.")
            return
        if direccion and len(direccion) > 50:
            self.error_label.configure(text="La Dirección no puede superar los 50 caracteres.")
            return

        # GUARDAR EN BASE DE DATOS
        try:
            if self.es_edicion:
                id_cliente = self.cliente_datos.get('idCliente')
                actualizar_cliente(
                    id_cliente=id_cliente,
                    nombre=nombre,
                    apellidos=apellidos,
                    documento=doc,
                    rol=self.rol,
                    telefono=tel,
                    correo=correo,
                    direccion=direccion
                )
                mensaje_exito = "¡Cliente actualizado con éxito!"
            else:
                insertar_cliente(
                    nombre=nombre,
                    apellidos=apellidos,
                    documento=doc,
                    rol=self.rol,
                    telefono=tel,
                    correo=correo,
                    direccion=direccion
                )
                mensaje_exito = "¡Cliente registrado con éxito!"
                
            # Mostrar mensaje de éxito temporal
            self.error_label.configure(text=mensaje_exito, text_color="#1DB954")
            self.btn_guardar.configure(state="disabled")
            
            # Refrescar la tabla en el master (VendedorWindow) si tiene el método
            if self.master and hasattr(self.master, "actualizar_lista_clientes"):
                self.master.actualizar_lista_clientes()
                
            # Cerrar la ventana después de 1 segundo
            self.after(1000, self.destroy)
            
        except Exception as e:
            self.error_label.configure(text=str(e), text_color="#ff4d4d")
