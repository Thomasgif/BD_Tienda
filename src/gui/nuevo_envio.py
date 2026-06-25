import customtkinter as ctk
import datetime
import calendar

class DatePicker(ctk.CTkToplevel):
    def __init__(self, master, entry_target):
        super().__init__(master)
        self.entry_target = entry_target
        self.title("Seleccionar Fecha")
        self.geometry("300x320")
        self.resizable(False, False)
        self.configure(fg_color="#050505")
        self.transient(master)
        self.grab_set()
        
        self.current_date = datetime.date.today()
        self.year = self.current_date.year
        self.month = self.current_date.month
        
        self.build_ui()
        
    def build_ui(self):
        for widget in self.winfo_children():
            widget.destroy()
            
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=10, pady=10)
        
        btn_prev = ctk.CTkButton(top_frame, text="<", width=30, fg_color="#333", hover_color="#555", command=self.prev_month)
        btn_prev.pack(side="left")
        
        meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        lbl_month = ctk.CTkLabel(top_frame, text=f"{meses[self.month]} {self.year}", font=("Arial", 14, "bold"))
        lbl_month.pack(side="left", expand=True)
        
        btn_next = ctk.CTkButton(top_frame, text=">", width=30, fg_color="#333", hover_color="#555", command=self.next_month)
        btn_next.pack(side="right")
        
        days_frame = ctk.CTkFrame(self, fg_color="#121212", corner_radius=10)
        days_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        days_of_week = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sa", "Do"]
        for col, day in enumerate(days_of_week):
            lbl = ctk.CTkLabel(days_frame, text=day, font=("Arial", 12, "bold"), text_color="#1DB954")
            lbl.grid(row=0, column=col, padx=8, pady=5)
            
        cal = calendar.monthcalendar(self.year, self.month)
        for row, week in enumerate(cal, start=1):
            for col, day in enumerate(week):
                if day != 0:
                    btn = ctk.CTkButton(
                        days_frame, 
                        text=str(day), 
                        width=30, 
                        height=30,
                        fg_color="transparent",
                        text_color="#ffffff",
                        hover_color="#1DB954",
                        command=lambda d=day: self.select_date(d)
                    )
                    btn.grid(row=row, column=col, padx=2, pady=2)
                    
    def prev_month(self):
        self.month -= 1
        if self.month == 0:
            self.month = 12
            self.year -= 1
        self.build_ui()
        
    def next_month(self):
        self.month += 1
        if self.month == 13:
            self.month = 1
            self.year += 1
        self.build_ui()
        
    def select_date(self, day):
        selected = f"{self.year}-{self.month:02d}-{day:02d}"
        self.entry_target.delete(0, 'end')
        self.entry_target.insert(0, selected)
        self.destroy()

class NuevoEnvioWindow(ctk.CTkToplevel):
    def __init__(self, master=None, envio_datos=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        
        self.envio_datos = envio_datos
        self.es_edicion = envio_datos is not None
        
        # Heredar el rol del empleado desde la ventana padre (VendedorWindow)
        self.rol = getattr(master, 'rol', 0)
        
        # Configurar la ventana
        if self.es_edicion:
            self.title("Editar Envío")
        else:
            self.title("Registrar Nuevo Envío")
            
        self.geometry("450x690")
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
        titulo_texto = "EDITAR ENVÍO" if self.es_edicion else "NUEVO ENVÍO"
        self.title_label = ctk.CTkLabel(
            self.frame, 
            text=titulo_texto, 
            font=("Arial", 22, "bold"), 
            text_color="#1DB954"
        )
        self.title_label.pack(side="top", pady=(20, 15))
        
        # Contenedor para los campos del formulario
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
        
        # Estilo para los combobox (sin placeholder_text_color)
        combo_style = {
            "height": 38,
            "corner_radius": 8,
            "fg_color": "#1e1e1e",
            "border_color": "#2a2a2a",
            "text_color": "#ffffff"
        }
        
        # Cargar datos desde la base de datos
        try:
            from database.connection import obtener_proveedores, obtener_compras, obtener_saldos_cuentas
            proveedores_db = obtener_proveedores(self.rol)
            compras_db = obtener_compras(self.rol)
            cuentas_db = obtener_saldos_cuentas(self.rol)
            
            # Formatear la lista para el combobox
            proveedores_lista = ["Seleccione proveedor..."] + [f"{p['nombre']} (NIT: {p['nit'] or 'N/A'}) | ID: {p['idProveedor']}" for p in proveedores_db]
            
            # Helper para fecha
            def formato_fecha(f):
                return f.strftime('%Y-%m-%d') if hasattr(f, 'strftime') else str(f)
                
            compras_lista = ["Seleccione compra..."] + [f"Compra #{c['idCompra']} - {formato_fecha(c['fechacompra'])}" for c in compras_db]
            
            self._cuentas_envio = {f"{c['tipo_cuenta']} ({c['num_cuenta']})": c['idMetodo_de_pago'] for c in cuentas_db}
            cuentas_lista = ["Seleccione método..."] + list(self._cuentas_envio.keys())
        except Exception as e:
            print(f"Error al cargar combos desde DB: {e}")
            proveedores_lista = ["Seleccione proveedor..."]
            compras_lista = ["Seleccione compra..."]
            cuentas_lista = ["Seleccione método..."]
            self._cuentas_envio = {}
            
        # 1. Nombre del Proveedor
        self.lbl_proveedor = ctk.CTkLabel(self.form_container, text="Seleccionar Proveedor *", font=("Arial", 12, "bold"), text_color="#aaaaaa")
        self.lbl_proveedor.pack(anchor="w", pady=(5, 2))
        
        self.combo_proveedor = ctk.CTkComboBox(self.form_container, values=proveedores_lista, **combo_style)
        self.combo_proveedor.pack(fill="x", pady=(0, 10))
        
        # 2. Compra Asociada
        self.lbl_compra = ctk.CTkLabel(self.form_container, text="Seleccionar Compra Asociada *", font=("Arial", 12, "bold"), text_color="#aaaaaa")
        self.lbl_compra.pack(anchor="w", pady=(5, 2))
        
        self.combo_compra = ctk.CTkComboBox(self.form_container, values=compras_lista, **combo_style)
        self.combo_compra.pack(fill="x", pady=(0, 10))
        
        # 3. Fecha de Envío
        self.lbl_fecha = ctk.CTkLabel(self.form_container, text="Fecha Estimada (YYYY-MM-DD) *", font=("Arial", 12, "bold"), text_color="#aaaaaa")
        self.lbl_fecha.pack(anchor="w", pady=(5, 2))
        
        fecha_frame = ctk.CTkFrame(self.form_container, fg_color="transparent")
        fecha_frame.pack(fill="x", pady=(0, 10))
        
        self.entry_fecha = ctk.CTkEntry(fecha_frame, placeholder_text="Ej: 2026-06-25", **input_style)
        self.entry_fecha.pack(side="left", fill="x", expand=True, padx=(0, 0))
        
        btn_calendario = ctk.CTkButton(
            fecha_frame, 
            text="📅", 
            width=38, 
            height=38, 
            fg_color="#333333", 
            hover_color="#1DB954",
            command=lambda: DatePicker(self, self.entry_fecha)
        )
        btn_calendario.pack(side="right", padx=(10, 0))
        
        # 4. Valor a Pagar
        self.lbl_valor = ctk.CTkLabel(self.form_container, text="Valor a Pagar (Costo) *", font=("Arial", 12, "bold"), text_color="#aaaaaa")
        self.lbl_valor.pack(anchor="w", pady=(5, 2))
        self.entry_valor = ctk.CTkEntry(self.form_container, placeholder_text="Ej: 15000", **input_style)
        self.entry_valor.pack(fill="x", pady=(0, 10))
        
        # 5. Método de Pago (Cuenta a debitar)
        self.lbl_pago = ctk.CTkLabel(self.form_container, text="Método de Pago (Cuenta a debitar) *", font=("Arial", 12, "bold"), text_color="#aaaaaa")
        self.lbl_pago.pack(anchor="w", pady=(5, 2))
        
        self.combo_pago = ctk.CTkComboBox(self.form_container, values=cuentas_lista, **combo_style)
        self.combo_pago.pack(fill="x", pady=(0, 10))
        
        # Mensaje de error / éxito
        self.error_label = ctk.CTkLabel(self.frame, text="", font=("Arial", 12), text_color="#ff4d4d", wraplength=380)
        self.error_label.pack(side="bottom", pady=5)
        
        # Botonera
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
            command=self.guardar_envio
        )
        self.btn_guardar.pack(side="right", fill="x", expand=True, padx=(10, 0))
        
        self.form_container.pack(side="top", fill="both", expand=True, padx=25)
        
        # Si es edición, precargar los campos
        if self.es_edicion:
            self.cargar_datos()

    def cargar_datos(self):
        self.combo_proveedor.set(self.envio_datos.get('proveedor', 'Seleccione proveedor...'))
        self.combo_compra.set(str(self.envio_datos.get('idCompra', 'Seleccione compra...')))
        self.entry_fecha.insert(0, self.envio_datos.get('fecha', ''))
        self.entry_valor.insert(0, str(self.envio_datos.get('valor', '')))
        
        # precargar cuenta
        num_cuenta = self.envio_datos.get('num_cuenta')
        metodo_pago = self.envio_datos.get('metodo_pago')
        if num_cuenta and metodo_pago:
            self.combo_pago.set(f"{metodo_pago} ({num_cuenta})")
        else:
            self.combo_pago.set("Seleccione método...")

    def guardar_envio(self):
        self.error_label.configure(text="", text_color="#ff4d4d")
        
        proveedor = self.combo_proveedor.get()
        compra = self.combo_compra.get()
        fecha = self.entry_fecha.get().strip()
        valor = self.entry_valor.get().strip()
        metodo_pago = self.combo_pago.get()
        
        # Validaciones básicas
        if proveedor == "Seleccione proveedor..." or compra == "Seleccione compra..." or metodo_pago == "Seleccione método..." or not fecha or not valor:
            self.error_label.configure(text="Por favor complete todos los campos obligatorios (*).")
            return
            
        # GUARDAR EN BASE DE DATOS
        try:
            from database.connection import insertar_envio
            
            # Extraer ID de la compra (ej: "Compra #101 - 2026-06-25")
            try:
                id_compra_str = compra.split(" ")[1].replace("#", "")
                id_compra = int(id_compra_str)
            except:
                raise Exception("Formato de compra no válido.")
                
            id_metodo = self._cuentas_envio.get(metodo_pago)
            if not id_metodo:
                raise Exception("Seleccione un método de pago válido.")
                
            id_empleado = getattr(self.master, 'id_empleado', 1)
            
            insertar_envio(idCompra=id_compra, idEmpleado=id_empleado, fecha=fecha, valor=float(valor), idMetodo_de_pago=id_metodo, rol=self.rol)
            
            mensaje_exito = "¡Envío actualizado con éxito!" if self.es_edicion else "¡Envío registrado con éxito!"
            self.error_label.configure(text=mensaje_exito, text_color="#1DB954")
            self.btn_guardar.configure(state="disabled")
            
            # Refrescar la tabla en el master si existe el método
            if self.master and hasattr(self.master, "actualizar_lista_envios"):
                self.master.actualizar_lista_envios()
                
            self.after(1000, self.destroy)
        except Exception as e:
            self.error_label.configure(text=str(e), text_color="#ff4d4d")
