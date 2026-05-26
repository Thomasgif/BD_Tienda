import customtkinter as ctk
from database.connection import obtener_clientes, obtener_productos, obtener_saldos_cuentas

class VendedorWindow(ctk.CTkToplevel):
    def __init__(self, master=None, nombre_vendedor="Usuario", *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        
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
        self.sidebar_frame.grid_rowconfigure(7, weight=1) # Espacio vacío ANTES del botón de cerrar sesión

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

        # Rol o usuario
        self.rol_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text=f"Vendedor: {nombre_vendedor}", 
            font=("Arial", 14),
            text_color="#1DB954"
        )
        self.rol_label.grid(row=2, column=0, padx=20, pady=(0, 30))

        # Botones de navegación
        self.nav_buttons = {}
        nav_items = ["Productos", "Ventas", "Cuentas", "Clientes"]
        
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
        self.logout_button.grid(row=8, column=0, padx=20, pady=(10, 30), sticky="ew")

        # Cargar clientes iniciales
        try:
            self.todos_clientes = obtener_clientes()
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
            self.todos_productos = obtener_productos()
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
        # Título de la tabla/lista
        lbl_lista = ctk.CTkLabel(parent, text="Estado de Cuentas (Solo Lectura)", font=("Arial", 18, "bold"), text_color="#aaaaaa")
        lbl_lista.pack(anchor="w", padx=40, pady=(0, 20))

        # Frame escroleable para la lista de cuentas
        scroll_frame = ctk.CTkScrollableFrame(parent, fg_color="#0a0a0a", corner_radius=10)
        scroll_frame.pack(fill="both", expand=True, padx=40, pady=(0, 20))

        try:
            cuentas = obtener_saldos_cuentas()
            if not cuentas:
                ctk.CTkLabel(scroll_frame, text="No hay cuentas registradas aún.", text_color="#888888").pack(pady=20)
            else:
                # Encabezados
                headers_frame = ctk.CTkFrame(scroll_frame, fg_color="#1e1e1e", corner_radius=5)
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
                    row_frame = ctk.CTkFrame(scroll_frame, fg_color="#121212" if idx % 2 == 0 else "#0a0a0a", corner_radius=0)
                    row_frame.pack(fill="x")
                    
                    row_frame.grid_columnconfigure(0, weight=1)
                    row_frame.grid_columnconfigure(1, weight=1)
                    row_frame.grid_columnconfigure(2, weight=1)
                    
                    ctk.CTkLabel(row_frame, text=cuenta['tipo_cuenta'], text_color="#ffffff").grid(row=0, column=0, padx=10, pady=8, sticky="w")
                    ctk.CTkLabel(row_frame, text=cuenta['num_cuenta'], text_color="#cccccc").grid(row=0, column=1, padx=10, pady=8, sticky="w")
                    
                    saldo = cuenta['saldo_total']
                    ctk.CTkLabel(row_frame, text=f"${saldo:,.2f}", text_color="#1DB954", font=("Arial", 14, "bold")).grid(row=0, column=2, padx=10, pady=8, sticky="w")

        except Exception as e:
            ctk.CTkLabel(scroll_frame, text=f"Error cargando cuentas:\n{e}", text_color="#ff4d4d").pack(pady=20)

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
            self.todos_clientes = obtener_clientes()
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
            self.todos_clientes = obtener_clientes()
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
            cuentas = obtener_saldos_cuentas()
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
