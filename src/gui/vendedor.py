import customtkinter as ctk
from database.connection import obtener_clientes, obtener_productos, obtener_saldos_cuentas

class VendedorWindow(ctk.CTkToplevel):
    def __init__(self, master=None, nombre_vendedor="Usuario", rol=0, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        
        # Almacenar el rol para usarlo en todas las operaciones de BD de esta sesión
        self.rol = rol  # 1 = gerente, 0 = empleado común
        
        self.title("Sistema de Ventas")
        self.geometry("1000x700")
        self.resizable(True, True)
        self.configure(fg_color="#050505")
        
        # Grid layout: 1 fila, 2 columnas (Sidebar a la izquierda, Contenido a la derecha)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # --- Sidebar (Barra de Navegación Lateral) ---
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#0a0a0a")
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(10, weight=1) # Espacio vacío ANTES del botón de cerrar sesión

        # Etiqueta para el Logo (Placeholder)
        self.logo_placeholder = ctk.CTkLabel(
            self.sidebar_frame, 
            text="[ LOGO ]", 
            width=100,
            height=100,
            corner_radius=15,
            fg_color="#1e1e1e",
            text_color="#555555",
            font=("Arial", 16, "bold")
        )
        self.logo_placeholder.grid(row=0, column=0, padx=20, pady=(30, 10))

        # Nombre de la Empresa
        self.empresa_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="Nombre Empresa", 
            font=("Arial", 20, "bold"),
            text_color="#ffffff"
        )
        self.empresa_label.grid(row=1, column=0, padx=20, pady=(0, 0))

        # Rol o usuario (muestra el tipo de acceso SQL del empleado)
        tipo_rol = "Gerente" if self.rol == 1 else "Empleado"
        self.rol_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text=f"{tipo_rol}: {nombre_vendedor}", 
            font=("Arial", 14),
            text_color="#1DB954"
        )
        self.rol_label.grid(row=2, column=0, padx=20, pady=(0, 30))

        # Botones de navegación
        self.nav_buttons = {}
        nav_items = ["Productos", "Ventas", "Cuentas", "Clientes", "Proveedores", "Envíos"]
        if self.rol == 1:
            nav_items.append("Empleados")
            nav_items.append("Balance")
        
        for i, item in enumerate(nav_items, start=3):
            btn = ctk.CTkButton(
                self.sidebar_frame,
                text=f"  {item}",
                fg_color="transparent",
                text_color="#888888",
                hover_color="#121212",
                anchor="w",
                height=40,
                font=("Arial", 15),
                command=lambda name=item: self.select_frame(name)
            )
            btn.grid(row=i, column=0, padx=15, pady=5, sticky="ew")
            self.nav_buttons[item] = btn

        # Botón de Cerrar Sesión (al final)
        self.logout_button = ctk.CTkButton(
            self.sidebar_frame,
            text="Cerrar Sesión",
            fg_color="#1a0505",
            hover_color="#330a0a",
            text_color="#ff4d4d",
            height=40,
            font=("Arial", 14, "bold"),
            command=self.logout
        )
        self.logout_button.grid(row=11, column=0, padx=20, pady=(10, 30), sticky="ew")

        # Cargar clientes iniciales usando el usuario SQL del rol del empleado
        try:
            self.todos_clientes = obtener_clientes(self.rol)
        except Exception as e:
            self.todos_clientes = []
            print(f"Error al cargar clientes: {e}")

        # --- Frames de Contenido (Main Frames) ---
        self.frames = {}
        
        # Crear los frames para cada pestaña y guardarlos en el diccionario
        for item in nav_items:
            frame = ctk.CTkFrame(self, corner_radius=15, fg_color="#121212")
            self.frames[item] = frame
            
            # Título de la sección
            title = ctk.CTkLabel(frame, text=item, font=("Arial", 32, "bold"), text_color="#ffffff")
            title.pack(anchor="w", padx=40, pady=(40, 10))
            
            # Separador estético
            separator = ctk.CTkFrame(frame, height=2, fg_color="#1DB954")
            separator.pack(fill="x", padx=40, pady=(0, 30))
            
            # Llamar la función específica de contenido para cada frame
            if item == "Productos":
                self.setup_productos_tab(frame)
            elif item == "Ventas":
                self.setup_ventas_tab(frame)
            elif item == "Cuentas":
                self.setup_cuentas_tab(frame)
            elif item == "Clientes":
                self.setup_clientes_tab(frame)
            elif item == "Proveedores":
                self.setup_proveedores_tab(frame)
            elif item == "Envíos":
                self.setup_envios_tab(frame)
            elif item == "Empleados":
                self.setup_empleados_tab(frame)
            elif item == "Balance":
                self.setup_balance_tab(frame)

        # Seleccionar la pestaña por defecto
        self.current_frame = None
        self.select_frame("Productos")

    def select_frame(self, name):
        # Actualizar colores de los botones de la barra lateral
        for btn_name, btn in self.nav_buttons.items():
            if btn_name == name:
                btn.configure(fg_color="#1DB954", text_color="#000000", font=("Arial", 15, "bold"))
            else:
                btn.configure(fg_color="transparent", text_color="#888888", font=("Arial", 15))

        # Ocultar el frame actual si existe
        if self.current_frame is not None:
            self.frames[self.current_frame].grid_forget()

        # Mostrar el nuevo frame con su contenido
        self.frames[name].grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.current_frame = name

        # Actualizar dinámicamente los datos de la pestaña activa
        if name == "Cuentas":
            self.actualizar_cuentas_tab()
        elif name == "Productos":
            self.actualizar_productos_tab()
        elif name == "Clientes":
            self.actualizar_clientes_tab()
        elif name == "Empleados":
            self.actualizar_empleados_tab()
        elif name == "Envíos":
            self.actualizar_lista_envios()


    def setup_productos_tab(self, parent):
        top_bar = ctk.CTkFrame(parent, fg_color="transparent")
        top_bar.pack(fill="x", padx=40, pady=(0, 20))
        
        # Título de la tabla/lista
        lbl_lista = ctk.CTkLabel(top_bar, text="Inventario de Productos", font=("Arial", 18, "bold"), text_color="#aaaaaa")
        lbl_lista.pack(side="left")

        # Barra de búsqueda
        self.entry_buscar_prod = ctk.CTkEntry(top_bar, placeholder_text="Buscar nombre o ref...", width=200)
        self.entry_buscar_prod.pack(side="right")
        self.entry_buscar_prod.bind("<KeyRelease>", self.filtrar_productos)

        # Frame escroleable para la lista de productos
        self.scroll_productos = ctk.CTkScrollableFrame(parent, fg_color="#0a0a0a", corner_radius=10)
        self.scroll_productos.pack(fill="both", expand=True, padx=40, pady=(0, 20))

        try:
            self.todos_productos = obtener_productos(self.rol)
            self.render_productos(self.todos_productos)
        except Exception as e:
            ctk.CTkLabel(self.scroll_productos, text=f"Error cargando productos:\n{e}", text_color="#ff4d4d").pack(pady=20)

    def filtrar_productos(self, event=None):
        query = self.entry_buscar_prod.get().lower()
        if not query:
            filtrados = self.todos_productos
        else:
            filtrados = [p for p in self.todos_productos if query in p['nombre'].lower() or query in p['referencia'].lower()]
        self.render_productos(filtrados)

    def render_productos(self, productos):
        for widget in self.scroll_productos.winfo_children():
            widget.destroy()

        if not productos:
            ctk.CTkLabel(self.scroll_productos, text="No se encontraron productos.", text_color="#888888").pack(pady=20)
            return

        # Encabezados
        headers_frame = ctk.CTkFrame(self.scroll_productos, fg_color="#1e1e1e", corner_radius=5)
        headers_frame.pack(fill="x", pady=(0, 10))
        
        # Configurar columnas
        headers_frame.grid_columnconfigure(0, weight=1) # Ref
        headers_frame.grid_columnconfigure(1, weight=2) # Nombre
        headers_frame.grid_columnconfigure(2, weight=1) # Precio Venta
        headers_frame.grid_columnconfigure(3, weight=1) # Stock
        
        ctk.CTkLabel(headers_frame, text="Referencia", font=("Arial", 14, "bold"), text_color="#1DB954").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        ctk.CTkLabel(headers_frame, text="Producto", font=("Arial", 14, "bold"), text_color="#1DB954").grid(row=0, column=1, padx=10, pady=10, sticky="w")
        ctk.CTkLabel(headers_frame, text="Precio Venta", font=("Arial", 14, "bold"), text_color="#1DB954").grid(row=0, column=2, padx=10, pady=10, sticky="w")
        ctk.CTkLabel(headers_frame, text="Stock (Bodega)", font=("Arial", 14, "bold"), text_color="#1DB954").grid(row=0, column=3, padx=10, pady=10, sticky="w")
        
        # Filas de productos
        for idx, prod in enumerate(productos):
            row_frame = ctk.CTkFrame(self.scroll_productos, fg_color="#121212" if idx % 2 == 0 else "#0a0a0a", corner_radius=0)
            row_frame.pack(fill="x")
            
            row_frame.grid_columnconfigure(0, weight=1)
            row_frame.grid_columnconfigure(1, weight=2)
            row_frame.grid_columnconfigure(2, weight=1)
            row_frame.grid_columnconfigure(3, weight=1)
            
            ctk.CTkLabel(row_frame, text=prod['referencia'], text_color="#cccccc").grid(row=0, column=0, padx=10, pady=8, sticky="w")
            ctk.CTkLabel(row_frame, text=prod['nombre'], text_color="#ffffff").grid(row=0, column=1, padx=10, pady=8, sticky="w")
            
            precio = prod['precio_venta']
            ctk.CTkLabel(row_frame, text=f"${precio:,.2f}", text_color="#cccccc").grid(row=0, column=2, padx=10, pady=8, sticky="w")
            
            stock = prod['bodega']
            stock_color = "#cccccc" if stock > 0 else "#ff4d4d"
            stock_text = str(stock) if stock > 0 else "Agotado"
            ctk.CTkLabel(row_frame, text=stock_text, text_color=stock_color).grid(row=0, column=3, padx=10, pady=8, sticky="w")

    def setup_ventas_tab(self, parent):
        # Layout de 2 columnas: Formulario a la izquierda, Carrito a la derecha
        # Frame contenedor principal
        main_container = ctk.CTkFrame(parent, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=40, pady=(0, 20))
        
        # Frame izquierdo (Formulario)
        form_frame = ctk.CTkFrame(main_container, fg_color="#0a0a0a", corner_radius=15)
        form_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Frame derecho (Lista de productos)
        cart_frame = ctk.CTkFrame(main_container, fg_color="#0a0a0a", corner_radius=15)
        cart_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))

        # ---- IZQUIERDA: FORMULARIO ----
        lbl_titulo = ctk.CTkLabel(form_frame, text="Facturar Venta", font=("Arial", 20, "bold"), text_color="#1DB954")
        lbl_titulo.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 15), sticky="w")
        
        # Cliente
        lbl_cliente = ctk.CTkLabel(form_frame, text="Cliente:", font=("Arial", 14, "bold"), text_color="#cccccc")
        lbl_cliente.grid(row=1, column=0, padx=20, pady=10, sticky="w")
        
        self.combo_cliente = ctk.CTkComboBox(form_frame, values=["Seleccione cliente..."], width=200)
        self.combo_cliente.grid(row=1, column=1, padx=20, pady=10, sticky="w")
        
        # Separador
        ctk.CTkFrame(form_frame, height=1, fg_color="#333333").grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
        
        # Producto
        lbl_producto = ctk.CTkLabel(form_frame, text="Añadir Producto:", font=("Arial", 14, "bold"), text_color="#cccccc")
        lbl_producto.grid(row=3, column=0, padx=20, pady=10, sticky="w")
        
        self.combo_producto = ctk.CTkComboBox(form_frame, values=["Seleccione producto..."], width=200)
        self.combo_producto.grid(row=3, column=1, padx=20, pady=10, sticky="w")
        
        # Cantidad
        lbl_cantidad = ctk.CTkLabel(form_frame, text="Cantidad:", font=("Arial", 14, "bold"), text_color="#cccccc")
        lbl_cantidad.grid(row=4, column=0, padx=20, pady=10, sticky="w")
        
        self.entry_cantidad = ctk.CTkEntry(form_frame, width=100, placeholder_text="Ej: 1")
        self.entry_cantidad.grid(row=4, column=1, padx=20, pady=10, sticky="w")
        
        # Botón Agregar al Carrito
        btn_agregar_prod = ctk.CTkButton(
            form_frame, 
            text="+ Añadir a la Lista", 
            font=("Arial", 14, "bold"),
            fg_color="#333333",
            hover_color="#555555",
            command=self.agregar_producto_lista
        )
        btn_agregar_prod.grid(row=5, column=0, columnspan=2, padx=20, pady=10)

        # Separador
        ctk.CTkFrame(form_frame, height=1, fg_color="#333333").grid(row=6, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
        
        # Forma de Pago
        lbl_pago = ctk.CTkLabel(form_frame, text="Forma de Pago:", font=("Arial", 14, "bold"), text_color="#cccccc")
        lbl_pago.grid(row=7, column=0, padx=20, pady=10, sticky="w")
        
        self.combo_pago = ctk.CTkComboBox(form_frame, values=["Seleccione método..."], width=200)
        self.combo_pago.grid(row=7, column=1, padx=20, pady=10, sticky="w")
        
        # Observaciones
        lbl_obs = ctk.CTkLabel(form_frame, text="Observaciones:", font=("Arial", 14, "bold"), text_color="#cccccc")
        lbl_obs.grid(row=8, column=0, padx=20, pady=10, sticky="nw")
        
        self.text_obs = ctk.CTkTextbox(form_frame, width=200, height=60, fg_color="#121212", border_color="#333333", border_width=1)
        self.text_obs.grid(row=8, column=1, padx=20, pady=10, sticky="w")
        
        # ---- DERECHA: CARRITO Y TOTAL ----
        lbl_carrito = ctk.CTkLabel(cart_frame, text="Lista de Productos", font=("Arial", 18, "bold"), text_color="#aaaaaa")
        lbl_carrito.pack(padx=20, pady=(20, 10), anchor="w")
        
        # Lista escroleable
        self.scroll_carrito = ctk.CTkScrollableFrame(cart_frame, fg_color="#121212", corner_radius=10)
        self.scroll_carrito.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Placeholder del carrito
        self.lbl_carrito_vacio = ctk.CTkLabel(self.scroll_carrito, text="La lista está vacía.", text_color="#666666")
        self.lbl_carrito_vacio.pack(pady=20)
        
        # Total
        self.lbl_total_venta = ctk.CTkLabel(cart_frame, text="Total Venta: $0.00", font=("Arial", 22, "bold"), text_color="#1DB954")
        self.lbl_total_venta.pack(padx=20, pady=(10, 20), anchor="e")

        # Botón Registrar
        btn_registrar = ctk.CTkButton(
            cart_frame, 
            text="Realizar Venta", 
            font=("Arial", 16, "bold"),
            fg_color="#1DB954",
            hover_color="#179643",
            text_color="black",
            height=45,
            command=self.procesar_venta
        )
        btn_registrar.pack(fill="x", padx=20, pady=(0, 20))

        # Inicializar comboboxes con datos reales
        self.actualizar_combobox_clientes()
        self.actualizar_combobox_productos()
        self.actualizar_combobox_pagos()

    def setup_cuentas_tab(self, parent):
        # Frame superior para título y botón de actualización
        top_bar = ctk.CTkFrame(parent, fg_color="transparent")
        top_bar.pack(fill="x", padx=40, pady=(0, 20))
        
        lbl_lista = ctk.CTkLabel(top_bar, text="Estado de Cuentas (Solo Lectura)", font=("Arial", 18, "bold"), text_color="#aaaaaa")
        lbl_lista.pack(side="left")

        # Botón para actualizar manualmente
        btn_actualizar = ctk.CTkButton(
            top_bar, 
            text="↻ Actualizar", 
            font=("Arial", 12, "bold"),
            fg_color="#1e1e1e", 
            hover_color="#333333", 
            text_color="#1DB954",
            width=100,
            command=self.actualizar_cuentas_tab
        )
        btn_actualizar.pack(side="right")

        # Frame escroleable para la lista de cuentas
        self.scroll_cuentas = ctk.CTkScrollableFrame(parent, fg_color="#0a0a0a", corner_radius=10)
        self.scroll_cuentas.pack(fill="both", expand=True, padx=40, pady=(0, 20))

        # Cargar los datos
        self.actualizar_cuentas_tab()

    def actualizar_cuentas_tab(self):
        if not hasattr(self, 'scroll_cuentas'):
            return
            
        import os
        os.makedirs("scratch", exist_ok=True)
        with open("scratch/gui_debug.log", "a", encoding="utf-8") as f:
            f.write("--- actualizar_cuentas_tab START ---\n")
            
        for widget in self.scroll_cuentas.winfo_children():
            widget.destroy()
            
        try:
            from database.connection import obtener_saldos_cuentas
            cuentas = obtener_saldos_cuentas(self.rol)
            
            with open("scratch/gui_debug.log", "a", encoding="utf-8") as f:
                f.write(f"Fetched accounts from DB: {cuentas}\n")
                
            if not cuentas:
                ctk.CTkLabel(self.scroll_cuentas, text="No hay cuentas registradas aún.", text_color="#888888").pack(pady=20)
            else:
                # Encabezados
                headers_frame = ctk.CTkFrame(self.scroll_cuentas, fg_color="#1e1e1e", corner_radius=5)
                headers_frame.pack(fill="x", pady=(0, 10))
                
                # Configurar columnas
                headers_frame.grid_columnconfigure(0, weight=1) # Tipo de Cuenta
                headers_frame.grid_columnconfigure(1, weight=1) # Número de Cuenta
                headers_frame.grid_columnconfigure(2, weight=1) # Saldo Total
                
                ctk.CTkLabel(headers_frame, text="Método/Cuenta", font=("Arial", 14, "bold"), text_color="#1DB954").grid(row=0, column=0, padx=10, pady=10, sticky="w")
                ctk.CTkLabel(headers_frame, text="Número", font=("Arial", 14, "bold"), text_color="#1DB954").grid(row=0, column=1, padx=10, pady=10, sticky="w")
                ctk.CTkLabel(headers_frame, text="Saldo Total Recaudado", font=("Arial", 14, "bold"), text_color="#1DB954").grid(row=0, column=2, padx=10, pady=10, sticky="w")
                
                # Filas de cuentas
                for idx, cuenta in enumerate(cuentas):
                    row_frame = ctk.CTkFrame(self.scroll_cuentas, fg_color="#121212" if idx % 2 == 0 else "#0a0a0a", corner_radius=0)
                    row_frame.pack(fill="x")
                    
                    row_frame.grid_columnconfigure(0, weight=1)
                    row_frame.grid_columnconfigure(1, weight=1)
                    row_frame.grid_columnconfigure(2, weight=1)
                    
                    ctk.CTkLabel(row_frame, text=cuenta['tipo_cuenta'], text_color="#ffffff").grid(row=0, column=0, padx=10, pady=8, sticky="w")
                    ctk.CTkLabel(row_frame, text=cuenta['num_cuenta'], text_color="#cccccc").grid(row=0, column=1, padx=10, pady=8, sticky="w")
                    
                    saldo = cuenta['saldo_total']
                    ctk.CTkLabel(row_frame, text=f"${saldo:,.2f}", text_color="#1DB954", font=("Arial", 14, "bold")).grid(row=0, column=2, padx=10, pady=8, sticky="w")

        except Exception as e:
            with open("scratch/gui_debug.log", "a", encoding="utf-8") as f:
                f.write(f"Error: {e}\n")
            ctk.CTkLabel(self.scroll_cuentas, text=f"Error cargando cuentas:\n{e}", text_color="#ff4d4d").pack(pady=20)
            
        with open("scratch/gui_debug.log", "a", encoding="utf-8") as f:
            f.write("--- actualizar_cuentas_tab END ---\n\n")


    def actualizar_productos_tab(self):
        if not hasattr(self, 'scroll_productos'):
            return
        try:
            self.todos_productos = obtener_productos(self.rol)
            self.filtrar_productos()
        except Exception as e:
            print(f"Error al actualizar productos: {e}")

    def actualizar_clientes_tab(self):
        if not hasattr(self, 'scroll_clientes'):
            return
        try:
            self.todos_clientes = obtener_clientes(self.rol)
            self.filtrar_clientes()
        except Exception as e:
            print(f"Error al actualizar clientes: {e}")

    def actualizar_empleados_tab(self):
        if hasattr(self, '_cargar_empleados_data'):
            self._cargar_empleados_data()


    def setup_clientes_tab(self, parent):
        # Frame superior para botones y búsqueda
        top_bar = ctk.CTkFrame(parent, fg_color="transparent")
        top_bar.pack(fill="x", padx=40, pady=(0, 20))
        
        lbl_lista = ctk.CTkLabel(top_bar, text="Lista de Clientes Registrados", font=("Arial", 18, "bold"), text_color="#aaaaaa")
        lbl_lista.pack(side="left")

        # Botón para registrar nuevo cliente
        btn_nuevo_cliente = ctk.CTkButton(
            top_bar, 
            text="+ Nuevo Cliente", 
            font=("Arial", 14, "bold"),
            fg_color="#1DB954",
            hover_color="#179643",
            text_color="black",
            command=self.abrir_nuevo_cliente
        )
        btn_nuevo_cliente.pack(side="right")

        # Barra de búsqueda
        self.entry_buscar_cliente = ctk.CTkEntry(top_bar, placeholder_text="Buscar nombre o doc...", width=200)
        self.entry_buscar_cliente.pack(side="right", padx=(0, 20))
        self.entry_buscar_cliente.bind("<KeyRelease>", self.filtrar_clientes)

        # Frame escroleable para la lista de clientes
        self.scroll_clientes = ctk.CTkScrollableFrame(parent, fg_color="#0a0a0a", corner_radius=10)
        self.scroll_clientes.pack(fill="both", expand=True, padx=40, pady=(0, 20))

        try:
            self.todos_clientes = obtener_clientes(self.rol)
            self.render_clientes(self.todos_clientes)
        except Exception as e:
            ctk.CTkLabel(self.scroll_clientes, text=f"Error cargando clientes:\n{e}", text_color="#ff4d4d").pack(pady=20)

    def filtrar_clientes(self, event=None):
        query = self.entry_buscar_cliente.get().lower()
        if not query:
            filtrados = self.todos_clientes
        else:
            filtrados = [c for c in self.todos_clientes if query in c['nombre'].lower() or query in c['apellidos'].lower() or query in str(c['documento']).lower()]
        self.render_clientes(filtrados)

    def render_clientes(self, clientes):
        for widget in self.scroll_clientes.winfo_children():
            widget.destroy()

        if not clientes:
            ctk.CTkLabel(self.scroll_clientes, text="No se encontraron clientes.", text_color="#888888").pack(pady=20)
            return

        # Encabezados
        headers_frame = ctk.CTkFrame(self.scroll_clientes, fg_color="#1e1e1e", corner_radius=5)
        headers_frame.pack(fill="x", pady=(0, 10))
        
        # Configurar columnas
        headers_frame.grid_columnconfigure(0, weight=1) # Doc
        headers_frame.grid_columnconfigure(1, weight=2) # Nombre
        headers_frame.grid_columnconfigure(2, weight=1) # Telefono
        headers_frame.grid_columnconfigure(3, weight=2) # Correo
        headers_frame.grid_columnconfigure(4, weight=1) # Acciones
        
        ctk.CTkLabel(headers_frame, text="Documento", font=("Arial", 14, "bold"), text_color="#1DB954").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        ctk.CTkLabel(headers_frame, text="Nombre y Apellido", font=("Arial", 14, "bold"), text_color="#1DB954").grid(row=0, column=1, padx=10, pady=10, sticky="w")
        ctk.CTkLabel(headers_frame, text="Teléfono", font=("Arial", 14, "bold"), text_color="#1DB954").grid(row=0, column=2, padx=10, pady=10, sticky="w")
        ctk.CTkLabel(headers_frame, text="Correo", font=("Arial", 14, "bold"), text_color="#1DB954").grid(row=0, column=3, padx=10, pady=10, sticky="w")
        ctk.CTkLabel(headers_frame, text="Acciones", font=("Arial", 14, "bold"), text_color="#1DB954").grid(row=0, column=4, padx=10, pady=10, sticky="w")
        
        # Filas de clientes
        for idx, cliente in enumerate(clientes):
            row_frame = ctk.CTkFrame(self.scroll_clientes, fg_color="#121212" if idx % 2 == 0 else "#0a0a0a", corner_radius=0)
            row_frame.pack(fill="x")
            
            row_frame.grid_columnconfigure(0, weight=1)
            row_frame.grid_columnconfigure(1, weight=2)
            row_frame.grid_columnconfigure(2, weight=1)
            row_frame.grid_columnconfigure(3, weight=2)
            row_frame.grid_columnconfigure(4, weight=1)
            
            ctk.CTkLabel(row_frame, text=cliente['documento'], text_color="#cccccc").grid(row=0, column=0, padx=10, pady=8, sticky="w")
            nombre_completo = f"{cliente['nombre']} {cliente['apellidos']}"
            ctk.CTkLabel(row_frame, text=nombre_completo, text_color="#ffffff").grid(row=0, column=1, padx=10, pady=8, sticky="w")
            ctk.CTkLabel(row_frame, text=cliente['telefono'] or "N/A", text_color="#cccccc").grid(row=0, column=2, padx=10, pady=8, sticky="w")
            ctk.CTkLabel(row_frame, text=cliente['correo'] or "N/A", text_color="#cccccc").grid(row=0, column=3, padx=10, pady=8, sticky="w")
            
            # Botón de Editar
            btn_editar = ctk.CTkButton(
                row_frame, 
                text="Editar", 
                width=60, 
                height=28, 
                font=("Arial", 12, "bold"),
                fg_color="#333333", 
                hover_color="#555555",
                text_color="#ffffff",
                command=lambda doc=cliente['documento']: self.editar_cliente(doc)
            )
            btn_editar.grid(row=0, column=4, padx=10, pady=8, sticky="w")

    def setup_proveedores_tab(self, parent):
        main_container = ctk.CTkFrame(parent, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=40, pady=(0, 20))
        
        # Izquierda: Lista de Proveedores
        left_frame = ctk.CTkFrame(main_container, fg_color="#0a0a0a", corner_radius=15)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Derecha: Detalles del Proveedor y Pedidos
        self.right_frame_prov = ctk.CTkFrame(main_container, fg_color="#0a0a0a", corner_radius=15)
        self.right_frame_prov.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        # --- IZQUIERDA: Proveedores ---
        lbl_titulo = ctk.CTkLabel(left_frame, text="Lista de Proveedores", font=("Arial", 20, "bold"), text_color="#1DB954")
        lbl_titulo.pack(padx=20, pady=(20, 15), anchor="w")
        
        self.scroll_proveedores = ctk.CTkScrollableFrame(left_frame, fg_color="#121212", corner_radius=10)
        self.scroll_proveedores.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Cargar proveedores
        try:
            from database.connection import obtener_proveedores
            proveedores = obtener_proveedores(self.rol)
            if not proveedores:
                ctk.CTkLabel(self.scroll_proveedores, text="No hay proveedores registrados.", text_color="#666666").pack(pady=20)
            else:
                for idx, p in enumerate(proveedores):
                    btn = ctk.CTkButton(
                        self.scroll_proveedores, 
                        text=f"{p['nombre']} (NIT: {p.get('nit', 'N/A') or 'N/A'})", 
                        font=("Arial", 14),
                        fg_color="#1e1e1e", 
                        hover_color="#1DB954",
                        text_color="#ffffff",
                        anchor="w",
                        height=40,
                        command=lambda prov=p: self.mostrar_detalle_proveedor(prov)
                    )
                    btn.pack(fill="x", pady=5, padx=5)
        except Exception as e:
            ctk.CTkLabel(self.scroll_proveedores, text=f"Error: {e}", text_color="#ff4d4d").pack(pady=20)
            
        # --- DERECHA: Placeholder Inicial ---
        self.lbl_detalle_placeholder = ctk.CTkLabel(self.right_frame_prov, text="Seleccione un proveedor a la izquierda\npara ver detalles y pedidos pendientes.", font=("Arial", 16), text_color="#666666")
        self.lbl_detalle_placeholder.pack(expand=True)

    def mostrar_detalle_proveedor(self, proveedor):
        # Limpiar frame derecho
        for widget in self.right_frame_prov.winfo_children():
            widget.destroy()
            
        # Info del proveedor
        info_frame = ctk.CTkFrame(self.right_frame_prov, fg_color="transparent")
        info_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(info_frame, text=proveedor['nombre'], font=("Arial", 24, "bold"), text_color="#ffffff").pack(anchor="w")
        ctk.CTkLabel(info_frame, text=f"NIT: {proveedor.get('nit', 'N/A') or 'N/A'}", font=("Arial", 14), text_color="#aaaaaa").pack(anchor="w")
        ctk.CTkLabel(info_frame, text=f"Teléfono: {proveedor.get('telefono', 'N/A') or 'N/A'}", font=("Arial", 14), text_color="#aaaaaa").pack(anchor="w")
        ctk.CTkLabel(info_frame, text=f"Correo: {proveedor.get('correo', 'N/A') or 'N/A'}", font=("Arial", 14), text_color="#aaaaaa").pack(anchor="w")
        ctk.CTkLabel(info_frame, text=f"Dirección: {proveedor.get('direccion', 'N/A') or 'N/A'}", font=("Arial", 14), text_color="#aaaaaa").pack(anchor="w")
        
        # Separador
        separador = ctk.CTkFrame(self.right_frame_prov, height=2, fg_color="#333333")
        separador.pack(fill="x", padx=20, pady=10)
        
        # Pedidos Pendientes
        ctk.CTkLabel(self.right_frame_prov, text="Pedidos / Envíos Pendientes por Pago", font=("Arial", 18, "bold"), text_color="#1DB954").pack(anchor="w", padx=20, pady=(10, 5))
        
        scroll_pedidos = ctk.CTkScrollableFrame(self.right_frame_prov, fg_color="#121212", corner_radius=10)
        scroll_pedidos.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Cargar pedidos del proveedor seleccionado
        try:
            from database.connection import obtener_pedidos_proveedor
            pedidos = obtener_pedidos_proveedor(proveedor['idProveedor'], self.rol)
            if not pedidos:
                ctk.CTkLabel(scroll_pedidos, text="Este proveedor no tiene pedidos registrados.", text_color="#666666").pack(pady=20)
            else:
                for idx, ped in enumerate(pedidos):
                    row_frame = ctk.CTkFrame(scroll_pedidos, fg_color="#1e1e1e" if idx % 2 == 0 else "#2a2a2a", corner_radius=8)
                    row_frame.pack(fill="x", pady=5)
                    
                    id_compra = ped.get('idCompra', 'N/A')
                    fecha_compra = ped.get('fechacompra', 'N/A')
                    if hasattr(fecha_compra, 'strftime'): fecha_compra = fecha_compra.strftime('%Y-%m-%d')
                    
                    id_envio = ped.get('idEnvio')
                    fecha_envio = ped.get('fecha_envio', 'N/A')
                    if hasattr(fecha_envio, 'strftime'): fecha_envio = fecha_envio.strftime('%Y-%m-%d')
                    
                    valor = float(ped.get('valor', 0))
                    
                    lbl_compra = ctk.CTkLabel(row_frame, text=f"Compra #{id_compra} - Fecha: {fecha_compra}", font=("Arial", 14, "bold"), text_color="#ffffff")
                    lbl_compra.pack(anchor="w", padx=10, pady=(10, 0))
                    
                    if id_envio:
                        detalle_envio = f"Envío Asociado: #{id_envio} | Fecha Est.: {fecha_envio} | Valor a pagar: ${valor:,.2f}"
                        color_envio = "#cccccc"
                    else:
                        detalle_envio = "Sin envío asociado (Aún no facturado/enviado)"
                        color_envio = "#888888"
                        
                    ctk.CTkLabel(row_frame, text=detalle_envio, font=("Arial", 12), text_color=color_envio).pack(anchor="w", padx=10, pady=(2, 10))
        except Exception as e:
            ctk.CTkLabel(scroll_pedidos, text=f"Error al cargar pedidos: {e}", text_color="#ff4d4d").pack(pady=20)

    def setup_envios_tab(self, parent):
        # Frame superior para botones y búsqueda
        top_bar = ctk.CTkFrame(parent, fg_color="transparent")
        top_bar.pack(fill="x", padx=40, pady=(0, 20))
        
        lbl_lista = ctk.CTkLabel(top_bar, text="Lista de Pedidos/Envíos de Proveedores", font=("Arial", 18, "bold"), text_color="#aaaaaa")
        lbl_lista.pack(side="left")

        # Botón para registrar nuevo envío
        btn_nuevo_envio = ctk.CTkButton(
            top_bar, 
            text="+ Nuevo Envío", 
            font=("Arial", 14, "bold"),
            fg_color="#1DB954",
            hover_color="#179643",
            text_color="black",
            command=self.abrir_nuevo_envio
        )
        btn_nuevo_envio.pack(side="right")

        # Barra de búsqueda
        self.entry_buscar_envio = ctk.CTkEntry(top_bar, placeholder_text="Buscar por proveedor...", width=200)
        self.entry_buscar_envio.pack(side="right", padx=(0, 20))
        self.entry_buscar_envio.bind("<KeyRelease>", self.filtrar_envios)

        # Frame escroleable para la lista
        self.scroll_envios = ctk.CTkScrollableFrame(parent, fg_color="#0a0a0a", corner_radius=10)
        self.scroll_envios.pack(fill="both", expand=True, padx=40, pady=(0, 20))

        # Cargar envíos desde la base de datos
        self.todos_envios = []
        self.actualizar_lista_envios()

    def actualizar_lista_envios(self):
        try:
            from database.connection import obtener_envios_list
            self.todos_envios = obtener_envios_list(self.rol)
            self.filtrar_envios()
        except Exception as e:
            print(f"Error al cargar envíos: {e}")
            self.todos_envios = []
            self.render_envios(self.todos_envios)

    def filtrar_envios(self, event=None):
        query = self.entry_buscar_envio.get().lower()
        if not query:
            filtrados = self.todos_envios
        else:
            # Asumimos que los envíos tendrán clave 'proveedor'
            filtrados = [e for e in self.todos_envios if query in str(e.get('proveedor', '')).lower()]
        self.render_envios(filtrados)

    def render_envios(self, envios):
        for widget in self.scroll_envios.winfo_children():
            widget.destroy()

        if not envios:
            ctk.CTkLabel(self.scroll_envios, text="No hay envíos registrados aún.", text_color="#888888").pack(pady=20)
            return

        # Encabezados
        headers_frame = ctk.CTkFrame(self.scroll_envios, fg_color="#1e1e1e", corner_radius=5)
        headers_frame.pack(fill="x", pady=(0, 10))
        
        headers_frame.grid_columnconfigure(0, weight=1) # ID
        headers_frame.grid_columnconfigure(1, weight=2) # Proveedor
        headers_frame.grid_columnconfigure(2, weight=1) # Fecha
        headers_frame.grid_columnconfigure(3, weight=1) # Valor a pagar
        headers_frame.grid_columnconfigure(4, weight=1) # Acciones
        
        ctk.CTkLabel(headers_frame, text="ID Envío", font=("Arial", 14, "bold"), text_color="#1DB954").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        ctk.CTkLabel(headers_frame, text="Proveedor", font=("Arial", 14, "bold"), text_color="#1DB954").grid(row=0, column=1, padx=10, pady=10, sticky="w")
        ctk.CTkLabel(headers_frame, text="Fecha", font=("Arial", 14, "bold"), text_color="#1DB954").grid(row=0, column=2, padx=10, pady=10, sticky="w")
        ctk.CTkLabel(headers_frame, text="Valor a Pagar", font=("Arial", 14, "bold"), text_color="#1DB954").grid(row=0, column=3, padx=10, pady=10, sticky="w")
        ctk.CTkLabel(headers_frame, text="Acciones", font=("Arial", 14, "bold"), text_color="#1DB954").grid(row=0, column=4, padx=10, pady=10, sticky="w")
        
        # Filas de envíos
        for idx, envio in enumerate(envios):
            row_frame = ctk.CTkFrame(self.scroll_envios, fg_color="#121212" if idx % 2 == 0 else "#0a0a0a", corner_radius=0)
            row_frame.pack(fill="x")
            
            row_frame.grid_columnconfigure(0, weight=1)
            row_frame.grid_columnconfigure(1, weight=2)
            row_frame.grid_columnconfigure(2, weight=1)
            row_frame.grid_columnconfigure(3, weight=1)
            row_frame.grid_columnconfigure(4, weight=1)
            
            ctk.CTkLabel(row_frame, text=envio.get('idEnvio', 'N/A'), text_color="#cccccc").grid(row=0, column=0, padx=10, pady=8, sticky="w")
            ctk.CTkLabel(row_frame, text=envio.get('proveedor', 'N/A'), text_color="#ffffff").grid(row=0, column=1, padx=10, pady=8, sticky="w")
            ctk.CTkLabel(row_frame, text=envio.get('fecha', 'N/A'), text_color="#cccccc").grid(row=0, column=2, padx=10, pady=8, sticky="w")
            
            valor = envio.get('valor', 0)
            ctk.CTkLabel(row_frame, text=f"${valor:,.2f}", text_color="#cccccc").grid(row=0, column=3, padx=10, pady=8, sticky="w")
            
            btn_detalles = ctk.CTkButton(
                row_frame, 
                text="Ver Detalles", 
                width=80, 
                height=28, 
                font=("Arial", 12, "bold"),
                fg_color="#333333", 
                hover_color="#555555",
                text_color="#ffffff",
                command=lambda env=envio: self.ver_detalle_envio(env)
            )
            btn_detalles.grid(row=0, column=4, padx=10, pady=8, sticky="w")

    def abrir_nuevo_envio(self):
        from gui.nuevo_envio import NuevoEnvioWindow
        self.nuevo_envio_win = NuevoEnvioWindow(self)

    def ver_detalle_envio(self, envio):
        from gui.detalle_envio import DetalleEnvioWindow
        if hasattr(self, 'detalle_envio_win') and self.detalle_envio_win.winfo_exists():
            self.detalle_envio_win.focus()
        else:
            self.detalle_envio_win = DetalleEnvioWindow(self, envio)

    def abrir_nuevo_cliente(self):
        from gui.nuevo_cliente import NuevoClienteWindow
        self.nuevo_cliente_win = NuevoClienteWindow(self)

    def editar_cliente(self, documento):
        cliente = next((c for c in self.todos_clientes if c['documento'] == documento), None)
        if cliente:
            from gui.nuevo_cliente import NuevoClienteWindow
            self.nuevo_cliente_win = NuevoClienteWindow(self, cliente_datos=cliente)

    def actualizar_lista_clientes(self):
        try:
            self.todos_clientes = obtener_clientes(self.rol)
            self.render_clientes(self.todos_clientes)
            self.actualizar_combobox_clientes()
        except Exception as e:
            print(f"Error al actualizar la lista de clientes: {e}")

    def actualizar_combobox_clientes(self):
        if not hasattr(self, 'combo_cliente'):
            return
        valores = ["Seleccione cliente..."]
        for c in self.todos_clientes:
            valores.append(f"{c['nombre']} {c['apellidos']} ({c['documento']})")
        self.combo_cliente.configure(values=valores)
        self.combo_cliente.set("Seleccione cliente...")

    def actualizar_combobox_productos(self):
        if not hasattr(self, 'combo_producto') or not hasattr(self, 'todos_productos'):
            return
        valores = ["Seleccione producto..."]
        for p in self.todos_productos:
            valores.append(f"{p['nombre']} ({p['referencia']})")
        self.combo_producto.configure(values=valores)
        self.combo_producto.set("Seleccione producto...")

    def actualizar_combobox_pagos(self):
        if not hasattr(self, 'combo_pago'):
            return
        try:
            cuentas = obtener_saldos_cuentas(self.rol)
            valores = ["Seleccione método..."]
            for c in cuentas:
                valores.append(f"{c['tipo_cuenta']} ({c['num_cuenta']})") 
            self.combo_pago.configure(values=valores)
            self.combo_pago.set("Seleccione método...")
        except Exception as e:
            print(f"Error al actualizar métodos de pago: {e}")

    def agregar_producto_lista(self):
        # Función en blanco temporalmente para simular agregar producto
        pass

    def procesar_venta(self):
        # Función en blanco temporalmente para implementar la lógica de ventas después
        pass

    def logout(self):
        # Limpiar los campos de la ventana de login original
        if hasattr(self.master, 'user_entry'):
            self.master.user_entry.delete(0, 'end')
            self.master.password_entry.delete(0, 'end')
            self.master.error_label.configure(text="")
            
        # Volver a mostrar la ventana de login
        self.master.deiconify()
        
        # Destruir esta ventana del vendedor
        self.destroy()

    # =========================================================================
    # MÓDULO EXCLUSIVO GERENTE — NÓMINA DE EMPLEADOS
    # =========================================================================

    def setup_empleados_tab(self, parent):
        """Tab exclusivo para el Gerente: gestión de nómina de empleados."""
        top_bar = ctk.CTkFrame(parent, fg_color="transparent")
        top_bar.pack(fill="x", padx=40, pady=(0, 20))

        ctk.CTkLabel(
            top_bar, text="Gestión de Nómina — Mes Actual",
            font=("Arial", 18, "bold"), text_color="#aaaaaa"
        ).pack(side="left")

        ctk.CTkButton(
            top_bar, text="↻ Actualizar",
            font=("Arial", 13, "bold"),
            fg_color="#1e1e1e", hover_color="#333333", text_color="#1DB954",
            width=110, command=self._cargar_empleados_data
        ).pack(side="right")

        ctk.CTkButton(
            top_bar, text="+ Registrar Empleado",
            font=("Arial", 13, "bold"),
            fg_color="#1DB954", hover_color="#179643", text_color="#000000",
            width=160, command=self._abrir_registrar_empleado
        ).pack(side="right", padx=(0, 10))

        self.scroll_empleados = ctk.CTkScrollableFrame(
            parent, fg_color="#0a0a0a", corner_radius=10
        )
        self.scroll_empleados.pack(fill="both", expand=True, padx=40, pady=(0, 20))

        self._empleados_expandidos = set()   # IDs con ventas desplegadas
        self._cargar_empleados_data()

    def _cargar_empleados_data(self):
        """Obtiene empleados de la BD y re-renderiza la tabla."""
        if not hasattr(self, 'scroll_empleados'):
            return
        try:
            from database.connection import obtener_empleados
            self._todos_empleados_nomina = obtener_empleados(self.rol)
        except Exception as e:
            self._todos_empleados_nomina = []
            print(f"Error cargando empleados: {e}")
        self._render_empleados_tabla()

    def _render_empleados_tabla(self):
        """Renderiza la tabla completa de nómina."""
        for w in self.scroll_empleados.winfo_children():
            w.destroy()

        empleados = getattr(self, '_todos_empleados_nomina', [])
        if not empleados:
            ctk.CTkLabel(
                self.scroll_empleados,
                text="No hay empleados registrados.", text_color="#888888"
            ).pack(pady=30)
            return

        # --- Encabezados ---
        hdr = ctk.CTkFrame(self.scroll_empleados, fg_color="#1e1e1e", corner_radius=5)
        hdr.pack(fill="x", pady=(0, 6))
        pesos = [2, 1, 1, 1, 1, 1]
        cols_hdr = ["Empleado", "Rol", "$/Hora", "Horas", "Total a Pagar", "Acciones"]
        for i, (col, w) in enumerate(zip(cols_hdr, pesos)):
            hdr.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(
                hdr, text=col,
                font=("Arial", 13, "bold"), text_color="#1DB954"
            ).grid(row=0, column=i, padx=10, pady=10, sticky="w")

        # --- Filas ---
        for idx, emp in enumerate(empleados):
            pago_hora   = float(emp.get('pago_hora',   0) or 0)
            trabajo_hora = float(emp.get('trabajo_hora', 0) or 0)
            total        = pago_hora * trabajo_hora
            emp_rol      = emp.get('rol', 0)

            bg = "#161616" if idx % 2 == 0 else "#0d0d0d"
            contenedor = ctk.CTkFrame(self.scroll_empleados, fg_color=bg, corner_radius=6)
            contenedor.pack(fill="x", pady=2)

            fila = ctk.CTkFrame(contenedor, fg_color="transparent")
            fila.pack(fill="x")
            for i, w in enumerate(pesos):
                fila.grid_columnconfigure(i, weight=w)

            # Nombre
            ctk.CTkLabel(
                fila, text=emp['nombre'],
                font=("Arial", 14, "bold"), text_color="#ffffff"
            ).grid(row=0, column=0, padx=12, pady=10, sticky="w")

            # Rol badge
            rol_txt   = "👑 Gerente" if emp_rol == 1 else "Empleado"
            rol_color = "#FFD700"   if emp_rol == 1 else "#aaaaaa"
            ctk.CTkLabel(
                fila, text=rol_txt,
                font=("Arial", 13), text_color=rol_color
            ).grid(row=0, column=1, padx=12, pady=10, sticky="w")

            # $/Hora
            ctk.CTkLabel(
                fila, text=f"${pago_hora:,.2f}",
                font=("Arial", 13), text_color="#cccccc"
            ).grid(row=0, column=2, padx=12, pady=10, sticky="w")

            # Horas trabajadas
            horas_color = "#1DB954" if trabajo_hora > 0 else "#555555"
            ctk.CTkLabel(
                fila, text=f"{trabajo_hora:.1f} h",
                font=("Arial", 13, "bold"), text_color=horas_color
            ).grid(row=0, column=3, padx=12, pady=10, sticky="w")

            # Total a pagar
            total_color = "#1DB954" if total > 0 else "#555555"
            ctk.CTkLabel(
                fila, text=f"${total:,.2f}",
                font=("Arial", 14, "bold"), text_color=total_color
            ).grid(row=0, column=4, padx=12, pady=10, sticky="w")

            # --- Botones de acción ---
            acc = ctk.CTkFrame(fila, fg_color="transparent")
            acc.grid(row=0, column=5, padx=10, pady=6, sticky="w")

            # Frame expandible de ventas (oculto por defecto)
            ventas_frame = ctk.CTkFrame(contenedor, fg_color="#0b0b0b", corner_radius=8)
            id_emp = emp['idEmpleado']

            btn_ventas = ctk.CTkButton(
                acc, text="▶ Ventas",
                font=("Arial", 12), width=90, height=28,
                fg_color="#1e2a1e", hover_color="#2d472d", text_color="#1DB954"
            )
            btn_ventas.configure(
                command=lambda iid=id_emp, vf=ventas_frame, btn=btn_ventas:
                    self._toggle_ventas(iid, vf, btn)
            )
            btn_ventas.pack(side="left", padx=(0, 6))

            btn_editar = ctk.CTkButton(
                acc, text="✏ Editar",
                font=("Arial", 12), width=75, height=28,
                fg_color="#1e1e1e", hover_color="#2b2b2b", text_color="#ffffff",
                command=lambda e=emp: self._abrir_editar_empleado(e)
            )
            btn_editar.pack(side="left", padx=(0, 6))

            btn_pagar = ctk.CTkButton(
                acc,
                text="💳 Pagar",
                font=("Arial", 12, "bold"), width=85, height=28,
                fg_color="#1a3322" if total > 0 else "#1a1a1a",
                hover_color="#1DB954" if total > 0 else "#1a1a1a",
                text_color="#1DB954" if total > 0 else "#444444",
                state="normal" if total > 0 else "disabled",
                command=lambda e=emp, t=total: self._abrir_modal_pago(e, t)
            )
            btn_pagar.pack(side="left")

            # Si ya estaba expandido, mostrarlo directamente
            if id_emp in self._empleados_expandidos:
                self._cargar_ventas_en_frame(id_emp, ventas_frame)
                ventas_frame.pack(fill="x", padx=10, pady=(0, 10))
                btn_ventas.configure(text="▼ Ventas")

    # --- Helpers del módulo empleados ---

    def _toggle_ventas(self, id_empleado, ventas_frame, btn):
        """Expande o colapsa el panel de ventas del mes de un empleado."""
        if id_empleado in self._empleados_expandidos:
            self._empleados_expandidos.discard(id_empleado)
            ventas_frame.pack_forget()
            btn.configure(text="▶ Ventas")
        else:
            self._empleados_expandidos.add(id_empleado)
            self._cargar_ventas_en_frame(id_empleado, ventas_frame)
            ventas_frame.pack(fill="x", padx=10, pady=(0, 10))
            btn.configure(text="▼ Ventas")

    def _cargar_ventas_en_frame(self, id_empleado, ventas_frame):
        """Llena el frame expandible con las ventas del mes del empleado."""
        for w in ventas_frame.winfo_children():
            w.destroy()
        try:
            from database.connection import obtener_ventas_mes_empleado
            ventas = obtener_ventas_mes_empleado(id_empleado, self.rol)
        except Exception as e:
            ctk.CTkLabel(ventas_frame, text=f"Error: {e}", text_color="#ff4d4d").pack(padx=12, pady=8)
            return

        ctk.CTkLabel(
            ventas_frame,
            text=f"  Ventas del mes ({len(ventas)} registros)",
            font=("Arial", 13, "bold"), text_color="#1DB954"
        ).pack(anchor="w", padx=12, pady=(10, 4))

        if not ventas:
            ctk.CTkLabel(
                ventas_frame,
                text="Sin ventas registradas este mes.",
                text_color="#666666", font=("Arial", 12)
            ).pack(anchor="w", padx=16, pady=(0, 10))
            return

        tabla = ctk.CTkFrame(ventas_frame, fg_color="#111111", corner_radius=5)
        tabla.pack(fill="x", padx=10, pady=(0, 10))

        # Encabezados mini-tabla
        th = ctk.CTkFrame(tabla, fg_color="#1a1a1a")
        th.pack(fill="x")
        mini_cols = [1, 2, 1, 1]
        mini_hdrs = ["# Venta", "Fecha", "Total", "Estado"]
        for i, (h, w) in enumerate(zip(mini_hdrs, mini_cols)):
            th.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(th, text=h, font=("Arial", 12, "bold"), text_color="#aaaaaa").grid(
                row=0, column=i, padx=10, pady=6, sticky="w"
            )

        total_mes = 0.0
        for i, v in enumerate(ventas):
            tr = ctk.CTkFrame(tabla, fg_color="#151515" if i % 2 == 0 else "#111111")
            tr.pack(fill="x")
            for j, w in enumerate(mini_cols):
                tr.grid_columnconfigure(j, weight=w)

            fecha = v.get('fecha_venta', '')
            if hasattr(fecha, 'strftime'):
                fecha = fecha.strftime('%d/%m/%Y %H:%M')

            valor  = float(v.get('valor_total', 0) or 0)
            total_mes += valor
            estado = str(v.get('estado_pago', 'N/A'))
            est_color = "#1DB954" if estado.lower() in ('pagado', 'completado') else "#FFD700"

            ctk.CTkLabel(tr, text=f"#{v.get('idVenta','?')}", text_color="#cccccc", font=("Arial", 12)
                         ).grid(row=0, column=0, padx=10, pady=5, sticky="w")
            ctk.CTkLabel(tr, text=str(fecha), text_color="#cccccc", font=("Arial", 12)
                         ).grid(row=0, column=1, padx=10, pady=5, sticky="w")
            ctk.CTkLabel(tr, text=f"${valor:,.2f}", text_color="#ffffff", font=("Arial", 12, "bold")
                         ).grid(row=0, column=2, padx=10, pady=5, sticky="w")
            ctk.CTkLabel(tr, text=estado, text_color=est_color, font=("Arial", 12)
                         ).grid(row=0, column=3, padx=10, pady=5, sticky="w")

        # Totalizador
        tf = ctk.CTkFrame(tabla, fg_color="#1a2a1a")
        tf.pack(fill="x")
        for j, w in enumerate(mini_cols): tf.grid_columnconfigure(j, weight=w)
        ctk.CTkLabel(tf, text="TOTAL MES", font=("Arial", 12, "bold"), text_color="#1DB954"
                     ).grid(row=0, column=0, columnspan=2, padx=10, pady=6, sticky="w")
        ctk.CTkLabel(tf, text=f"${total_mes:,.2f}", font=("Arial", 13, "bold"), text_color="#1DB954"
                     ).grid(row=0, column=2, padx=10, pady=6, sticky="w")

    def _abrir_modal_pago(self, emp, total):
        """Abre la ventana modal de confirmación de pago de nómina."""
        modal = ctk.CTkToplevel(self)
        modal.title("Confirmar Pago de Nómina")
        modal.geometry("480x400")
        modal.resizable(False, False)
        modal.configure(fg_color="#0d0d0d")
        modal.grab_set()  # bloquea el resto de la ventana
        modal.focus()

        # Título
        ctk.CTkLabel(
            modal, text="Confirmación de Pago",
            font=("Arial", 22, "bold"), text_color="#1DB954"
        ).pack(pady=(30, 5))

        ctk.CTkFrame(modal, height=2, fg_color="#1DB954").pack(fill="x", padx=30, pady=(0, 20))

        # Detalle del empleado
        info = ctk.CTkFrame(modal, fg_color="#161616", corner_radius=10)
        info.pack(fill="x", padx=30, pady=(0, 15))

        pago_hora    = float(emp.get('pago_hora',    0) or 0)
        trabajo_hora = float(emp.get('trabajo_hora', 0) or 0)

        filas_info = [
            ("Empleado:",       emp['nombre']),
            ("Sueldo por hora:", f"${pago_hora:,.2f}"),
            ("Horas trabajadas:",f"{trabajo_hora:.1f} h"),
            ("Total a pagar:",   f"${total:,.2f}"),
        ]
        for lbl_txt, val_txt in filas_info:
            row = ctk.CTkFrame(info, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=3)
            ctk.CTkLabel(row, text=lbl_txt, font=("Arial", 13), text_color="#aaaaaa", width=150, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=val_txt, font=("Arial", 13, "bold"), text_color="#ffffff").pack(side="left")

        # Selección de cuenta
        ctk.CTkLabel(
            modal, text="Cuenta de la empresa a debitar:",
            font=("Arial", 13), text_color="#cccccc"
        ).pack(anchor="w", padx=30, pady=(5, 2))

        try:
            cuentas = obtener_saldos_cuentas(self.rol)
        except Exception:
            cuentas = []

        self._cuentas_pago_emp = {}
        opciones = []
        for c in cuentas:
            label = f"{c['tipo_cuenta']} ···{c['num_cuenta'][-4:]}  (Saldo: ${float(c['saldo_total']):,.2f})"
            opciones.append(label)
            self._cuentas_pago_emp[label] = c['idMetodo_de_pago']

        if not opciones:
            opciones = ["Sin cuentas disponibles"]

        combo_cuenta = ctk.CTkComboBox(
            modal, values=opciones, width=400,
            fg_color="#1e1e1e", border_color="#333333",
            button_color="#1DB954", dropdown_hover_color="#1DB954"
        )
        combo_cuenta.set(opciones[0])
        combo_cuenta.pack(padx=30, pady=(0, 10))

        # Mensaje de estado
        lbl_estado = ctk.CTkLabel(modal, text="", font=("Arial", 12))
        lbl_estado.pack(pady=(0, 5))

        # Botones
        btn_row = ctk.CTkFrame(modal, fg_color="transparent")
        btn_row.pack(pady=(5, 20))

        ctk.CTkButton(
            btn_row, text="Cancelar",
            font=("Arial", 13), width=140, height=40,
            fg_color="#1a1a1a", hover_color="#2a2a2a", text_color="#888888",
            command=modal.destroy
        ).pack(side="left", padx=(0, 15))

        ctk.CTkButton(
            btn_row, text="✅  Confirmar Pago",
            font=("Arial", 13, "bold"), width=180, height=40,
            fg_color="#1DB954", hover_color="#179643", text_color="#000000",
            command=lambda: self._confirmar_pago(
                modal, emp['idEmpleado'], combo_cuenta.get(), total, lbl_estado
            )
        ).pack(side="left")

    def _confirmar_pago(self, modal, id_empleado, cuenta_label, monto, lbl_estado):
        """Ejecuta el pago: registra en BD, actualiza UI y cierra el modal."""
        id_metodo = self._cuentas_pago_emp.get(cuenta_label)
        if not id_metodo:
            lbl_estado.configure(text="⚠ Seleccione una cuenta válida.", text_color="#FFD700")
            return

        try:
            from database.connection import pagar_empleado
            pagar_empleado(id_empleado, id_metodo, monto, self.rol)
            lbl_estado.configure(text="✔ Pago registrado correctamente.", text_color="#1DB954")
            modal.after(1200, modal.destroy)
            # Refrescar tabla después de cerrar el modal
            modal.after(1400, self._cargar_empleados_data)
            # Actualizar balances en la pestaña Cuentas si ya está cargada
            self.actualizar_cuentas_tab()
        except Exception as e:
            lbl_estado.configure(text=f"Error: {e}", text_color="#ff4d4d")


    def _abrir_registrar_empleado(self):
        from gui.nuevo_empleado import NuevoEmpleadoWindow
        win = NuevoEmpleadoWindow(self)
        win.focus()

    def _abrir_editar_empleado(self, emp):
        from gui.nuevo_empleado import NuevoEmpleadoWindow
        win = NuevoEmpleadoWindow(self, empleado_datos=emp)
        win.focus()

    def cargar_lista_empleados(self):
        self._cargar_empleados_data()

    # =========================================================================
    # MÓDULO EXCLUSIVO GERENTE — BALANCE & GASTOS & CUENTAS POR PAGAR
    # =========================================================================

    def setup_balance_tab(self, parent):
        """Tab de Balance para el Gerente: Cuentas por Pagar, Estadísticas (Placeholder), Gastos."""
        # Usar un Tabview para las 3 secciones
        self.balance_tabview = ctk.CTkTabview(
            parent,
            fg_color="#121212",
            segmented_button_fg_color="#0a0a0a",
            segmented_button_selected_color="#1DB954",
            segmented_button_selected_hover_color="#179643",
            segmented_button_unselected_color="#1a1a1a",
            segmented_button_unselected_hover_color="#2b2b2b",
            text_color="#ffffff"
        )
        self.balance_tabview.pack(fill="both", expand=True, padx=40, pady=(0, 20))
        
        tab_cuentas = self.balance_tabview.add("Cuentas por Pagar")
        tab_stats = self.balance_tabview.add("Estadísticas de Productos")
        tab_gastos = self.balance_tabview.add("Gastos")
        
        # 1. Setup Cuentas por Pagar
        self.setup_balance_cuentas(tab_cuentas)
        
        # 2. Setup Estadísticas (Placeholder)
        self.setup_balance_stats(tab_stats)
        
        # 3. Setup Gastos
        self.setup_balance_gastos(tab_gastos)

    # ------------------ BALANCE: CUENTAS POR PAGAR ------------------
    def setup_balance_cuentas(self, parent):
        top_bar = ctk.CTkFrame(parent, fg_color="transparent")
        top_bar.pack(fill="x", pady=(10, 15))
        
        ctk.CTkLabel(
            top_bar, text="Cuentas por Pagar a Proveedores",
            font=("Arial", 16, "bold"), text_color="#aaaaaa"
        ).pack(side="left")
        
        ctk.CTkButton(
            top_bar, text="↻ Actualizar",
            font=("Arial", 12, "bold"),
            fg_color="#1e1e1e", hover_color="#333333", text_color="#1DB954",
            width=100, command=self.actualizar_balance_cuentas
        ).pack(side="right")
        
        self.scroll_cuentas_pagar = ctk.CTkScrollableFrame(parent, fg_color="#0a0a0a", corner_radius=10)
        self.scroll_cuentas_pagar.pack(fill="both", expand=True, pady=(0, 10))
        
        self.actualizar_balance_cuentas()

    def actualizar_balance_cuentas(self):
        for w in self.scroll_cuentas_pagar.winfo_children():
            w.destroy()
            
        try:
            from database.connection import obtener_cuentas_por_pagar
            cuentas = obtener_cuentas_por_pagar(self.rol)
        except Exception as e:
            cuentas = []
            print(f"Error al obtener cuentas por pagar: {e}")
            
        if not cuentas:
            ctk.CTkLabel(self.scroll_cuentas_pagar, text="No hay deudas o compras registradas.", text_color="#888888").pack(pady=30)
            return
            
        # Encabezados
        hdr = ctk.CTkFrame(self.scroll_cuentas_pagar, fg_color="#1e1e1e", corner_radius=5)
        hdr.pack(fill="x", pady=(0, 6))
        pesos = [1, 2, 2, 1, 1]
        cols = ["Compra ID", "Proveedor", "Fecha Compra", "Total Compra", "Estado Envío"]
        for i, (col, w) in enumerate(zip(cols, pesos)):
            hdr.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(hdr, text=col, font=("Arial", 12, "bold"), text_color="#1DB954").grid(row=0, column=i, padx=10, pady=8, sticky="w")
            
        for idx, c in enumerate(cuentas):
            bg = "#161616" if idx % 2 == 0 else "#0d0d0d"
            row = ctk.CTkFrame(self.scroll_cuentas_pagar, fg_color=bg, corner_radius=5)
            row.pack(fill="x", pady=2)
            
            for i, w in enumerate(pesos):
                row.grid_columnconfigure(i, weight=w)
                
            fecha = c.get('fechacompra', '')
            if hasattr(fecha, 'strftime'):
                fecha = fecha.strftime('%d/%m/%Y %H:%M')
                
            total = float(c.get('total_compra', 0) or 0)
            
            ctk.CTkLabel(row, text=f"#{c['idCompra']}", font=("Arial", 13, "bold"), text_color="#ffffff").grid(row=0, column=0, padx=10, pady=8, sticky="w")
            ctk.CTkLabel(row, text=c['proveedor'], font=("Arial", 13), text_color="#ffffff").grid(row=0, column=1, padx=10, pady=8, sticky="w")
            ctk.CTkLabel(row, text=str(fecha), font=("Arial", 13), text_color="#cccccc").grid(row=0, column=2, padx=10, pady=8, sticky="w")
            ctk.CTkLabel(row, text=f"${total:,.2f}", font=("Arial", 13, "bold"), text_color="#1DB954").grid(row=0, column=3, padx=10, pady=8, sticky="w")
            
            est = c['estado_envio']
            est_color = "#1DB954" if est == "Envío Registrado" else "#FFD700"
            ctk.CTkLabel(row, text=est, font=("Arial", 13), text_color=est_color).grid(row=0, column=4, padx=10, pady=8, sticky="w")

    # ------------------ BALANCE: ESTADÍSTICAS ------------------
    def setup_balance_stats(self, parent):
        info_frame = ctk.CTkFrame(parent, fg_color="#0a0a0a", corner_radius=15)
        info_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        lbl_title = ctk.CTkLabel(
            info_frame, 
            text="Estadísticas de Productos", 
            font=("Arial", 22, "bold"), 
            text_color="#1DB954"
        )
        lbl_title.pack(pady=(40, 10))
        
        lbl_desc = ctk.CTkLabel(
            info_frame, 
            text="Esta sección está planificada para mostrar análisis avanzados de ventas, rotación de inventarios y rendimientos.\n¡Próximamente disponible!", 
            font=("Arial", 14), 
            text_color="#888888",
            justify="center"
        )
        lbl_desc.pack(pady=10)

    # ------------------ BALANCE: GASTOS ------------------
    def setup_balance_gastos(self, parent):
        # Layout: Columna Izquierda (Formulario para registrar gasto), Columna Derecha (Historial de gastos)
        parent.grid_columnconfigure(0, weight=2)
        parent.grid_columnconfigure(1, weight=3)
        parent.grid_rowconfigure(0, weight=1)
        
        # Columna Izquierda: Formulario
        form_frame = ctk.CTkFrame(parent, fg_color="#0a0a0a", corner_radius=10)
        form_frame.grid(row=0, column=0, padx=(10, 10), pady=10, sticky="nsew")
        
        ctk.CTkLabel(form_frame, text="Registrar Nuevo Gasto", font=("Arial", 16, "bold"), text_color="#1DB954").pack(pady=(15, 15))
        
        # Descripción
        ctk.CTkLabel(form_frame, text="Descripción del Gasto *", font=("Arial", 12, "bold"), text_color="#aaaaaa").pack(anchor="w", padx=20, pady=(5, 2))
        self.entry_gasto_desc = ctk.CTkEntry(
            form_frame, placeholder_text="Ej: Pago de servicios públicos",
            height=38, corner_radius=8, fg_color="#1e1e1e", border_color="#2a2a2a", text_color="#ffffff"
        )
        self.entry_gasto_desc.pack(fill="x", padx=20, pady=(0, 10))
        
        # Monto
        ctk.CTkLabel(form_frame, text="Monto ($) *", font=("Arial", 12, "bold"), text_color="#aaaaaa").pack(anchor="w", padx=20, pady=(5, 2))
        self.entry_gasto_monto = ctk.CTkEntry(
            form_frame, placeholder_text="Ej: 450.00",
            height=38, corner_radius=8, fg_color="#1e1e1e", border_color="#2a2a2a", text_color="#ffffff"
        )
        self.entry_gasto_monto.pack(fill="x", padx=20, pady=(0, 10))
        
        # Cuenta
        ctk.CTkLabel(form_frame, text="Cuenta a debitar *", font=("Arial", 12, "bold"), text_color="#aaaaaa").pack(anchor="w", padx=20, pady=(5, 2))
        
        try:
            from database.connection import obtener_saldos_cuentas
            cuentas = obtener_saldos_cuentas(self.rol)
            self._cuentas_gastos = {f"{c['tipo_cuenta']} ({c['num_cuenta']})": c['idMetodo_de_pago'] for c in cuentas}
            opciones = ["Seleccione cuenta..."] + list(self._cuentas_gastos.keys())
        except Exception:
            opciones = ["Seleccione cuenta..."]
            self._cuentas_gastos = {}
            
        self.combo_gasto_cuenta = ctk.CTkComboBox(
            form_frame, values=opciones, height=38, corner_radius=8,
            fg_color="#1e1e1e", border_color="#2a2a2a", text_color="#ffffff"
        )
        self.combo_gasto_cuenta.pack(fill="x", padx=20, pady=(0, 15))
        self.combo_gasto_cuenta.set("Seleccione cuenta...")
        
        # Estado label
        self.lbl_gasto_status = ctk.CTkLabel(form_frame, text="", font=("Arial", 12), text_color="#ff4d4d", wraplength=220)
        self.lbl_gasto_status.pack(pady=5)
        
        # Guardar
        ctk.CTkButton(
            form_frame, text="Guardar Gasto",
            font=("Arial", 13, "bold"), fg_color="#1DB954", hover_color="#179643", text_color="#000000",
            height=40, command=self.guardar_gasto
        ).pack(fill="x", padx=20, pady=(5, 20))
        
        # Columna Derecha: Historial
        hist_frame = ctk.CTkFrame(parent, fg_color="#0a0a0a", corner_radius=10)
        hist_frame.grid(row=0, column=1, padx=(10, 10), pady=10, sticky="nsew")
        
        top_hist = ctk.CTkFrame(hist_frame, fg_color="transparent")
        top_hist.pack(fill="x", padx=15, pady=(15, 10))
        
        ctk.CTkLabel(top_hist, text="Historial de Gastos", font=("Arial", 16, "bold"), text_color="#aaaaaa").pack(side="left")
        
        ctk.CTkButton(
            top_hist, text="↻", font=("Arial", 12, "bold"),
            fg_color="#1e1e1e", hover_color="#333333", text_color="#1DB954",
            width=35, height=30, command=self.actualizar_gastos_historial
        ).pack(side="right")
        
        self.scroll_gastos = ctk.CTkScrollableFrame(hist_frame, fg_color="transparent")
        self.scroll_gastos.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        self.actualizar_gastos_historial()

    def guardar_gasto(self):
        self.lbl_gasto_status.configure(text="", text_color="#ff4d4d")
        desc = self.entry_gasto_desc.get().strip()
        monto_str = self.entry_gasto_monto.get().strip()
        cuenta_sel = self.combo_gasto_cuenta.get()
        
        if not desc or not monto_str or cuenta_sel == "Seleccione cuenta...":
            self.lbl_gasto_status.configure(text="Por favor complete todos los campos.")
            return
            
        try:
            monto = float(monto_str)
            if monto <= 0:
                raise ValueError()
        except ValueError:
            self.lbl_gasto_status.configure(text="El monto debe ser un número positivo.")
            return
            
        id_metodo = self._cuentas_gastos.get(cuenta_sel)
        if not id_metodo:
            self.lbl_gasto_status.configure(text="Cuenta seleccionada inválida.")
            return
            
        try:
            from database.connection import insertar_gasto
            insertar_gasto(id_metodo_pago=id_metodo, descripcion=desc, monto=monto, rol=self.rol)
            
            self.lbl_gasto_status.configure(text="¡Gasto registrado con éxito!", text_color="#1DB954")
            self.entry_gasto_desc.delete(0, 'end')
            self.entry_gasto_monto.delete(0, 'end')
            self.combo_gasto_cuenta.set("Seleccione cuenta...")
            
            # Recargar historial
            self.actualizar_gastos_historial()
            
            # Recargar el combo local de cuentas del formulario para actualizar saldo mostrado
            self.recargar_combo_cuentas_gasto()
            
        except Exception as e:
            self.lbl_gasto_status.configure(text=str(e), text_color="#ff4d4d")

    def recargar_combo_cuentas_gasto(self):
        try:
            from database.connection import obtener_saldos_cuentas
            cuentas = obtener_saldos_cuentas(self.rol)
            self._cuentas_gastos = {f"{c['tipo_cuenta']} ({c['num_cuenta']})": c['idMetodo_de_pago'] for c in cuentas}
            opciones = ["Seleccione cuenta..."] + list(self._cuentas_gastos.keys())
            self.combo_gasto_cuenta.configure(values=opciones)
        except Exception:
            pass

    def actualizar_gastos_historial(self):
        for w in self.scroll_gastos.winfo_children():
            w.destroy()
            
        try:
            from database.connection import obtener_gastos
            gastos = obtener_gastos(self.rol)
        except Exception as e:
            gastos = []
            print(f"Error al obtener gastos: {e}")
            
        if not gastos:
            ctk.CTkLabel(self.scroll_gastos, text="No hay gastos registrados.", text_color="#888888").pack(pady=20)
            return
            
        # Encabezados
        hdr = ctk.CTkFrame(self.scroll_gastos, fg_color="#1e1e1e", corner_radius=5)
        hdr.pack(fill="x", pady=(0, 6))
        pesos = [2, 1, 1, 1]
        cols = ["Descripción", "Cuenta", "Monto", "Fecha"]
        for i, (col, w) in enumerate(zip(cols, pesos)):
            hdr.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(hdr, text=col, font=("Arial", 11, "bold"), text_color="#1DB954").grid(row=0, column=i, padx=5, pady=6, sticky="w")
            
        for idx, g in enumerate(gastos):
            bg = "#161616" if idx % 2 == 0 else "#0d0d0d"
            row = ctk.CTkFrame(self.scroll_gastos, fg_color=bg, corner_radius=5)
            row.pack(fill="x", pady=2)
            
            for i, w in enumerate(pesos):
                row.grid_columnconfigure(i, weight=w)
                
            fecha = g.get('fecha', '')
            if hasattr(fecha, 'strftime'):
                fecha = fecha.strftime('%d/%m/%Y')
                
            monto = float(g.get('monto', 0) or 0)
            
            # Truncar descripción larga si es necesario
            desc = g['descripcion']
            if len(desc) > 20:
                desc = desc[:17] + "..."
                
            ctk.CTkLabel(row, text=desc, font=("Arial", 12), text_color="#ffffff").grid(row=0, column=0, padx=5, pady=6, sticky="w")
            ctk.CTkLabel(row, text=g['cuenta'], font=("Arial", 11), text_color="#cccccc").grid(row=0, column=1, padx=5, pady=6, sticky="w")
            ctk.CTkLabel(row, text=f"${monto:,.2f}", font=("Arial", 12, "bold"), text_color="#ff4d4d").grid(row=0, column=2, padx=5, pady=6, sticky="w")
            ctk.CTkLabel(row, text=str(fecha), font=("Arial", 11), text_color="#888888").grid(row=0, column=3, padx=5, pady=6, sticky="w")
