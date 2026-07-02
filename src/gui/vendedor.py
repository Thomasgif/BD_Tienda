import customtkinter as ctk
from math import isfinite
from database.connection import obtener_clientes, obtener_productos, obtener_saldos_cuentas

class VendedorWindow(ctk.CTkToplevel):
    def __init__(self, master=None, nombre_vendedor="Usuario", rol=0, id_empleado=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        
        # Almacenar el rol para usarlo en todas las operaciones de BD de esta sesión
        self.rol = rol           # 1 = gerente, 0 = empleado común
        self.id_empleado = id_empleado  # ID del empleado autenticado (para registrar compras, etc.)
        self.clientes_expandidos = set()

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
        # Limpiar el contenedor scrollable
        for widget in self.scroll_productos.winfo_children():
            widget.destroy()

        if not productos:
            ctk.CTkLabel(self.scroll_productos, text="No se encontraron productos.", text_color="#888888").pack(pady=20)
            return

        # 1. CREAR UN SÓLO CONTENEDOR MAESTRO PARA TODA LA TABLA
        table_frame = ctk.CTkFrame(self.scroll_productos, fg_color="transparent")
        table_frame.pack(fill="x", expand=True)
        
        # 2. CONFIGURAR LAS COLUMNAS UNA SOLA VEZ PARA TODO EL COMPONENTE
        table_frame.grid_columnconfigure(0, weight=1) # Referencia
        table_frame.grid_columnconfigure(1, weight=2) # Producto (Más ancho)
        table_frame.grid_columnconfigure(2, weight=1) # Precio Venta
        table_frame.grid_columnconfigure(3, weight=1) # Stock
        
        # 3. ENCABEZADOS (Ocupan la Fila 0 de la grilla única)
        headers_color = "#1e1e1e"
        
        # Usamos sticky="nsew" para que el fondo gris llene toda la celda uniformemente
        ctk.CTkLabel(table_frame, text="Referencia", font=("Arial", 14, "bold"), text_color="#1DB954", fg_color=headers_color, anchor="w", padx=10, pady=10).grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(table_frame, text="Producto", font=("Arial", 14, "bold"), text_color="#1DB954", fg_color=headers_color, anchor="w", padx=10, pady=10).grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(table_frame, text="Precio Venta", font=("Arial", 14, "bold"), text_color="#1DB954", fg_color=headers_color, anchor="w", padx=10, pady=10).grid(row=0, column=2, sticky="nsew")
        ctk.CTkLabel(table_frame, text="Stock (Bodega)", font=("Arial", 14, "bold"), text_color="#1DB954", fg_color=headers_color, anchor="w", padx=10, pady=10).grid(row=0, column=3, sticky="nsew")
        
        # 4. FILAS DE PRODUCTOS (Ocupan las filas consecutivas: idx + 1)
        for idx, prod in enumerate(productos):
            row_idx = idx + 1 # La fila 0 ya la tienen los encabezados
            row_color = "#121212" if idx % 2 == 0 else "#0a0a0a"
            
            # Celda 0: Referencia
            ctk.CTkLabel(table_frame, text=prod['referencia'], text_color="#cccccc", fg_color=row_color, anchor="w", padx=10, pady=8).grid(row=row_idx, column=0, sticky="nsew")
            
            # Celda 1: Nombre del producto
            ctk.CTkLabel(table_frame, text=prod['nombre'], text_color="#ffffff", fg_color=row_color, anchor="w", padx=10, pady=8).grid(row=row_idx, column=1, sticky="nsew")
            
            # Celda 2: Precio Venta
            precio = prod['precio_venta']
            ctk.CTkLabel(table_frame, text=f"${precio:,.2f}", text_color="#cccccc", fg_color=row_color, anchor="w", padx=10, pady=8).grid(row=row_idx, column=2, sticky="nsew")
            
            # Celda 3: Stock / Bodega
            stock = prod['bodega']
            stock_color = "#cccccc" if stock > 0 else "#ff4d4d"
            stock_text = str(stock) if stock > 0 else "Agotado"
            
            ctk.CTkLabel(table_frame, text=stock_text, text_color=stock_color, fg_color=row_color, anchor="w", padx=10, pady=8).grid(row=row_idx, column=3, sticky="nsew")
    def setup_ventas_tab(self, parent):
        self.carrito_ventas = []
        self.total_ventas = 0.0
        
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

        # Separador eliminado (o lo dejamos si es necesario, pero quitamos Forma de Pago)        
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
        
        lbl_lista = ctk.CTkLabel(top_bar, text="Estado de Cuentas", font=("Arial", 18, "bold"), text_color="#aaaaaa")
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
                # 1. CONTENEDOR MAESTRO ÚNICO PARA TU TABLA
                table_frame = ctk.CTkFrame(self.scroll_cuentas, fg_color="transparent")
                table_frame.pack(fill="x", expand=True)
                
                # 2. CONFIGURACIÓN DE COLUMNAS GLOBALES (3 columnas perfectas)
                table_frame.grid_columnconfigure(0, weight=1) # Método/Cuenta
                table_frame.grid_columnconfigure(1, weight=1) # Número
                table_frame.grid_columnconfigure(2, weight=1) # Saldo Total
                
                # 3. ENCABEZADOS DE LA TABLA (Fila 0 de la grilla)
                headers_color = "#1e1e1e"
                ctk.CTkLabel(table_frame, text="Método/Cuenta", font=("Arial", 14, "bold"), text_color="#1DB954", fg_color=headers_color, anchor="w", padx=10, pady=10).grid(row=0, column=0, sticky="nsew")
                ctk.CTkLabel(table_frame, text="Número", font=("Arial", 14, "bold"), text_color="#1DB954", fg_color=headers_color, anchor="w", padx=10, pady=10).grid(row=0, column=1, sticky="nsew")
                ctk.CTkLabel(table_frame, text="Saldo Total Recaudado", font=("Arial", 14, "bold"), text_color="#1DB954", fg_color=headers_color, anchor="w", padx=10, pady=10).grid(row=0, column=2, sticky="nsew")
                
                # 4. ITERACIÓN DE FILAS DINÁMICAS (Filas consecutivas: idx + 1)
                for idx, cuenta in enumerate(cuentas):
                    row_idx = idx + 1
                    row_color = "#121212" if idx % 2 == 0 else "#0a0a0a"
                    
                    # Celda 0: Tipo de Cuenta
                    ctk.CTkLabel(table_frame, text=cuenta['tipo_cuenta'], text_color="#ffffff", fg_color=row_color, anchor="w", padx=10, pady=8).grid(row=row_idx, column=0, sticky="nsew")
                    
                    # Celda 1: Número de Cuenta
                    ctk.CTkLabel(table_frame, text=cuenta['num_cuenta'], text_color="#cccccc", fg_color=row_color, anchor="w", padx=10, pady=8).grid(row=row_idx, column=1, sticky="nsew")
                    
                    # Celda 2: Saldo formateado con tu fuente negrita verde
                    saldo = cuenta['saldo_total']
                    ctk.CTkLabel(table_frame, text=f"${saldo:,.2f}", text_color="#1DB954", font=("Arial", 14, "bold"), fg_color=row_color, anchor="w", padx=10, pady=8).grid(row=row_idx, column=2, sticky="nsew")

        except Exception as e:
            with open("scratch/gui_debug.log", "a", encoding="utf-8") as f:
                f.write(f"Error: {e}\n")
            ctk.CTkLabel(self.scroll_cuentas, text=f"Error cargando cuentas:\n{e}", text_color="#ff4d4d").pack(pady=20)
            
        with open("scratch/gui_debug.log", "a", encoding="utf-8") as f:
            f.write("--- actualizar_cuentas_tab END ---\n\n")

    def render_cuentas(self, cuentas):
        """
        Renderiza la grilla única global para el estado de cuentas.
        """
        # Limpiar el contenedor scrollable
        for widget in self.scroll_cuentas.winfo_children():
            widget.destroy()

        if not cuentas:
            ctk.CTkLabel(self.scroll_cuentas, text="No hay registros de cuentas pendientes.", text_color="#888888").pack(pady=20)
            return

        # 1. CREAR UN SÓLO CONTENEDOR MAESTRO PARA TODA LA TABLA
        table_frame = ctk.CTkFrame(self.scroll_cuentas, fg_color="transparent")
        table_frame.pack(fill="x", expand=True)
        
        # 2. CONFIGURAR LAS COLUMNAS UNA SOLA VEZ
        table_frame.grid_columnconfigure(0, weight=1) # ID Venta
        table_frame.grid_columnconfigure(1, weight=2) # Cliente
        table_frame.grid_columnconfigure(2, weight=1) # Fecha
        table_frame.grid_columnconfigure(3, weight=1) # Total
        table_frame.grid_columnconfigure(4, weight=1) # Estado
        
        # 3. ENCABEZADOS (Fila 0)
        headers_color = "#1e1e1e"
        ctk.CTkLabel(table_frame, text="ID Venta", font=("Arial", 14, "bold"), text_color="#1DB954", fg_color=headers_color, anchor="w", padx=10, pady=10).grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(table_frame, text="Cliente", font=("Arial", 14, "bold"), text_color="#1DB954", fg_color=headers_color, anchor="w", padx=10, pady=10).grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(table_frame, text="Fecha", font=("Arial", 14, "bold"), text_color="#1DB954", fg_color=headers_color, anchor="w", padx=10, pady=10).grid(row=0, column=2, sticky="nsew")
        ctk.CTkLabel(table_frame, text="Total Facturado", font=("Arial", 14, "bold"), text_color="#1DB954", fg_color=headers_color, anchor="w", padx=10, pady=10).grid(row=0, column=3, sticky="nsew")
        ctk.CTkLabel(table_frame, text="Estado", font=("Arial", 14, "bold"), text_color="#1DB954", fg_color=headers_color, anchor="w", padx=10, pady=10).grid(row=0, column=4, sticky="nsew")
        
        # 4. FILAS DE CUENTAS (Filas consecutivas: idx + 1)
        for idx, cuenta in enumerate(cuentas):
            row_idx = idx + 1
            row_color = "#121212" if idx % 2 == 0 else "#0a0a0a"
            
            # Celdas informativas básicas
            ctk.CTkLabel(table_frame, text=cuenta.get('id_venta', 'N/A'), text_color="#cccccc", fg_color=row_color, anchor="w", padx=10, pady=8).grid(row=row_idx, column=0, sticky="nsew")
            
            nombre_cliente = f"{cuenta.get('nombre', '')} {cuenta.get('apellidos', '')}".strip() or "Cliente General"
            ctk.CTkLabel(table_frame, text=nombre_cliente, text_color="#ffffff", fg_color=row_color, anchor="w", padx=10, pady=8).grid(row=row_idx, column=1, sticky="nsew")
            
            ctk.CTkLabel(table_frame, text=cuenta.get('fecha', 'N/A'), text_color="#cccccc", fg_color=row_color, anchor="w", padx=10, pady=8).grid(row=row_idx, column=2, sticky="nsew")
            
            total = cuenta.get('total', 0)
            ctk.CTkLabel(table_frame, text=f"${total:,.2f}", text_color="#cccccc", fg_color=row_color, anchor="w", padx=10, pady=8).grid(row=row_idx, column=3, sticky="nsew")
            
            # Formatear dinámicamente el estado (Ej: "pendiente" en rojo, "pagado" en verde)
            estado = cuenta.get('estado', 'N/A').upper()
            estado_color = "#ff4d4d" if "PENDIENTE" in estado else "#1DB954"
            
            ctk.CTkLabel(table_frame, text=estado, text_color=estado_color, fg_color=row_color, font=("Arial", 12, "bold"), anchor="w", padx=10, pady=8).grid(row=row_idx, column=4, sticky="nsew")


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

        self.clientes_expandidos = set()

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
        # Limpiar el contenedor scrollable
        for widget in self.scroll_clientes.winfo_children():
            widget.destroy()

        if not clientes:
            ctk.CTkLabel(self.scroll_clientes, text="No se encontraron clientes.", text_color="#888888").pack(pady=20)
            return

        # 1. CREAR UN SÓLO CONTENEDOR MAESTRO PARA TODA LA TABLA
        table_frame = ctk.CTkFrame(self.scroll_clientes, fg_color="transparent")
        table_frame.pack(fill="x", expand=True)
        
        # 2. CONFIGURAR COLUMNAS GLOBALES (Se heredan a filas y encabezados)
        table_frame.grid_columnconfigure(0, weight=1) # Doc
        table_frame.grid_columnconfigure(1, weight=2) # Nombre
        table_frame.grid_columnconfigure(2, weight=1) # Telefono
        table_frame.grid_columnconfigure(3, weight=2) # Correo
        table_frame.grid_columnconfigure(4, weight=2) # Acciones
        
        # 3. ENCABEZADOS (Fila 0)
        headers_color = "#1e1e1e"
        ctk.CTkLabel(table_frame, text="Documento", font=("Arial", 14, "bold"), text_color="#1DB954", fg_color=headers_color, anchor="w", padx=10, pady=10).grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(table_frame, text="Nombre y Apellido", font=("Arial", 14, "bold"), text_color="#1DB954", fg_color=headers_color, anchor="w", padx=10, pady=10).grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(table_frame, text="Teléfono", font=("Arial", 14, "bold"), text_color="#1DB954", fg_color=headers_color, anchor="w", padx=10, pady=10).grid(row=0, column=2, sticky="nsew")
        ctk.CTkLabel(table_frame, text="Correo", font=("Arial", 14, "bold"), text_color="#1DB954", fg_color=headers_color, anchor="w", padx=10, pady=10).grid(row=0, column=3, sticky="nsew")
        ctk.CTkLabel(table_frame, text="Acciones", font=("Arial", 14, "bold"), text_color="#1DB954", fg_color=headers_color, anchor="w", padx=10, pady=10).grid(row=0, column=4, sticky="nsew")
        
        # 4. FILAS DE CLIENTES
        for idx, cliente in enumerate(clientes):
            # Calculamos las dos filas matemáticas que le corresponden a este registro
            main_row = (idx * 2) + 1   # Fila para los datos del cliente (1, 3, 5, 7...)
            deuda_row = (idx * 2) + 2  # Fila reservada para su desplegable (2, 4, 6, 8...)
            
            row_color = "#121212" if idx % 2 == 0 else "#0a0a0a"
            
            # Datos del cliente en la fila principal (main_row)
            ctk.CTkLabel(table_frame, text=cliente['documento'], text_color="#cccccc", fg_color=row_color, anchor="w", padx=10, pady=8).grid(row=main_row, column=0, sticky="nsew")
            
            nombre_completo = f"{cliente['nombre']} {cliente['apellidos']}"
            ctk.CTkLabel(table_frame, text=nombre_completo, text_color="#ffffff", fg_color=row_color, anchor="w", padx=10, pady=8).grid(row=main_row, column=1, sticky="nsew")
            ctk.CTkLabel(table_frame, text=cliente['telefono'] or "N/A", text_color="#cccccc", fg_color=row_color, anchor="w", padx=10, pady=8).grid(row=main_row, column=2, sticky="nsew")
            ctk.CTkLabel(table_frame, text=cliente['correo'] or "N/A", text_color="#cccccc", fg_color=row_color, anchor="w", padx=10, pady=8).grid(row=main_row, column=3, sticky="nsew")
            
            # Contenedor de acciones en la columna 4
            actions_frame = ctk.CTkFrame(table_frame, fg_color=row_color, corner_radius=0)
            actions_frame.grid(row=main_row, column=4, sticky="nsew", padx=0, pady=0)
            
            # Botón de Editar
            btn_editar = ctk.CTkButton(
                actions_frame, 
                text="Editar", 
                width=60, 
                height=28, 
                font=("Arial", 12, "bold"),
                fg_color="#333333", 
                hover_color="#555555",
                text_color="#ffffff",
                command=lambda doc=cliente['documento']: self.editar_cliente(doc)
            )
            btn_editar.pack(side="left", padx=4, pady=6)

            # Frame expandible (Hijo directo de table_frame, esperando ser gridded en deuda_row)
            deuda_frame = ctk.CTkFrame(table_frame, fg_color="#0b0b0b", corner_radius=8)
            id_cliente = cliente['idCliente']
           
            # Botón de Ventas / Cuentas
            btn_ventas = ctk.CTkButton(
                actions_frame,
                text="▶ Cuentas pendientes",
                font=("Arial", 12), width=90, height=28,
                fg_color="#1e2a1e", hover_color="#2d472d", text_color="#1DB954"
            )
            # Pasamos "deuda_row" a la función toggle para saber dónde debe aparecer
            btn_ventas.configure(
                command=lambda idcli=id_cliente, df=deuda_frame, btn=btn_ventas, r=deuda_row:
                    self._toggle_deudas(idcli, df, btn, r)
            )
            btn_ventas.pack(side="left", padx=2, pady=6)

            # Si el cliente ya estaba expandido en el estado, lo dibujamos de inmediato
            if id_cliente in self.clientes_expandidos:
                self._cargar_deudas_cliente(deuda_frame, id_cliente)
                deuda_frame.grid(row=deuda_row, column=0, columnspan=5, padx=10, pady=(0, 10), sticky="ew")
                btn_ventas.configure(text="▼ Ocultar cuentas")


    def _toggle_deudas(self, idcli, df, btn, row_idx):
        if idcli in self.clientes_expandidos:
            self.clientes_expandidos.discard(idcli)
            df.grid_forget() # Ocultamos removiendo de la grilla global
            btn.configure(text="▶ Cuentas pendientes")
        else:
            self.clientes_expandidos.add(idcli)
            self._cargar_deudas_cliente(df, idcli)
            # Lo posicionamos exactamente en la fila que le reservamos abajo de sus datos
            df.grid(row=row_idx, column=0, columnspan=5, padx=10, pady=(0, 10), sticky="ew")
            btn.configure(text="▼ Ocultar cuentas")
            
        # Reajustar el scrollbar dinámicamente
        self.update_idletasks()

    def _cargar_deudas_cliente(self,df,idcli):
        for w in df.winfo_children():
            w.destroy()
        try:
            from database.connection import obtener_deudas_cliente, pago_total_venta
            deudas = obtener_deudas_cliente(idcli, self.rol)
        except Exception as e:
            ctk.CTkLabel(df, text=f"Error al cargar deudas: {str(e)}", text_color="red").pack(pady=10)
            return
        
        ctk.CTkLabel(
            df,
            text="Deudas pendientes del cliente: ", 
            font=("Arial", 13, "bold"),text_color="#cccccc"
            ).pack(anchor="w", padx=15, pady=(10,4))

        if not deudas:
            ctk.CTkLabel(
                df,
                text="No se encontraron deudas.",
                text_color="#888888", font=("Arial", 12)).pack(pady=(0,10), anchor="w", padx=15)
            return

        for d in deudas:
            ya_pagado = pago_total_venta(d['idVenta'], self.rol)
            pendiente = float(d['valor_total']) - float(ya_pagado)

            row_frame = ctk.CTkFrame(df, fg_color="#1a1a1a", corner_radius=8)
            row_frame.pack(fill="x", padx=15, pady=3)

            txt_deuda = f"Venta #{d['idVenta']}  |  Fecha: {d['fecha_venta']}  |  Pendiente: ${pendiente:,.2f}"
            ctk.CTkLabel(row_frame, text=txt_deuda, text_color="#cccccc", font=("Arial", 12)).pack(
                side="left", padx=10, pady=8
            )

            ctk.CTkButton(
                row_frame, text="💳 Pagar", width=80, height=28,
                font=("Arial", 12, "bold"), fg_color="#1DB954", hover_color="#179643", text_color="#000000",
                command=lambda venta=d, monto=pendiente, cliente_id=idcli, df_ref=df: self._abrir_modal_pagar_deuda(venta, monto, cliente_id, df_ref)
            ).pack(side="right", padx=(0, 5), pady=5)

            ctk.CTkButton(
                row_frame, text="✖ Cancelar", width=85, height=28,
                font=("Arial", 12, "bold"), fg_color="#5a1a1a", hover_color="#8b0000", text_color="#ff6b6b",
                command=lambda venta=d, cliente_id=idcli, df_ref=df: self._confirmar_cancelar_venta(venta, cliente_id, df_ref)
            ).pack(side="right", padx=(10, 0), pady=5)

        
    # =========================================================================
    # PESTAÑA PROVEEDORES
    # =========================================================================

    def _abrir_modal_pagar_deuda(self, venta, monto_pendiente, id_cliente, df_ref):
        """Abre un modal para pagar una deuda pendiente, con opción de monto parcial o total."""
        modal = ctk.CTkToplevel(self)
        modal.title("Registrar Pago")
        modal.geometry("400x380")
        modal.resizable(False, False)
        modal.configure(fg_color="#0d0d0d")
        modal.grab_set()
        modal.focus()

        ctk.CTkLabel(modal, text="💳 Registrar Pago", font=("Arial", 18, "bold"), text_color="#1DB954").pack(pady=(20, 4))
        ctk.CTkLabel(modal, text=f"Venta #{venta['idVenta']}  —  Pendiente: ${monto_pendiente:,.2f}",
                     font=("Arial", 13), text_color="#aaaaaa").pack(pady=(0, 8))

        # ── Método de pago ─────────────────────────────────────────────────
        ctk.CTkLabel(modal, text="Método de Pago:", font=("Arial", 12)).pack(anchor="w", padx=30, pady=(4, 2))

        try:
            from database.connection import obtener_saldos_cuentas
            cuentas = obtener_saldos_cuentas(self.rol)
            opciones = [f"{c['tipo_cuenta']} ({c['num_cuenta']})" for c in cuentas]
            mapa = {f"{c['tipo_cuenta']} ({c['num_cuenta']})": c['idMetodo_de_pago'] for c in cuentas}
        except Exception:
            opciones = []
            mapa = {}

        if not opciones:
            opciones = ["Sin métodos disponibles"]

        combo_metodo = ctk.CTkComboBox(modal, values=opciones, width=340)
        combo_metodo.pack(padx=30)

        # ── Monto a pagar ──────────────────────────────────────────────────
        ctk.CTkLabel(modal, text="Monto a pagar ($):", font=("Arial", 12)).pack(anchor="w", padx=30, pady=(12, 2))

        entry_frame = ctk.CTkFrame(modal, fg_color="transparent")
        entry_frame.pack(padx=30, fill="x")

        entry_monto = ctk.CTkEntry(entry_frame, placeholder_text="Ej: 15000", width=220)
        entry_monto.pack(side="left")

        ctk.CTkButton(
            entry_frame, text="Pagar todo", width=110, height=32,
            font=("Arial", 11, "bold"), fg_color="#1a3a2a", hover_color="#24543c", text_color="#1DB954",
            command=lambda: (entry_monto.delete(0, "end"), entry_monto.insert(0, f"{monto_pendiente:.2f}"))
        ).pack(side="left", padx=(8, 0))

        lbl_error = ctk.CTkLabel(modal, text="", text_color="#ff4d4d", wraplength=340)
        lbl_error.pack(pady=8)

        def confirmar():
            sel = combo_metodo.get()
            if sel not in mapa:
                lbl_error.configure(text="Selecciona un método de pago válido.")
                return
            try:
                monto_str = entry_monto.get().strip().replace(",", ".")
                monto_pago = float(monto_str)
            except ValueError:
                lbl_error.configure(text="Ingresa un monto numérico válido.")
                return

            try:
                from database.connection import pagar_venta_pendiente
                pagar_venta_pendiente(
                    id_venta=venta['idVenta'],
                    id_cliente=id_cliente,
                    id_metodo_pago=mapa[sel],
                    monto=monto_pago,
                    rol=self.rol
                )
                modal.destroy()
                self._cargar_deudas_cliente(df_ref, id_cliente)
                if hasattr(self, 'actualizar_cuentas_tab'):
                    self.actualizar_cuentas_tab()
            except Exception as e:
                lbl_error.configure(text=str(e))

        ctk.CTkButton(
            modal, text="✅ Confirmar Pago", font=("Arial", 13, "bold"),
            fg_color="#1DB954", hover_color="#179643", text_color="#000000",
            width=200, command=confirmar
        ).pack(pady=5)

    def _confirmar_cancelar_venta(self, venta, id_cliente, df_ref):
        """Abre un modal de confirmación antes de cancelar una venta pendiente."""
        modal = ctk.CTkToplevel(self)
        modal.title("Cancelar Venta")
        modal.geometry("380x230")
        modal.resizable(False, False)
        modal.configure(fg_color="#0d0d0d")
        modal.grab_set()
        modal.focus()

        ctk.CTkLabel(modal, text="⚠ Cancelar Venta", font=("Arial", 18, "bold"), text_color="#ff6b6b").pack(pady=(20, 5))
        ctk.CTkLabel(
            modal,
            text=f"¿Estás seguro de cancelar la Venta #{venta['idVenta']}?\nEsto restaurará el inventario de los productos.",
            font=("Arial", 12), text_color="#cccccc", wraplength=320, justify="center"
        ).pack(pady=8)

        lbl_error = ctk.CTkLabel(modal, text="", text_color="#ff4d4d", wraplength=320)
        lbl_error.pack(pady=4)

        btn_frame = ctk.CTkFrame(modal, fg_color="transparent")
        btn_frame.pack(pady=10)

        def ejecutar_cancelacion():
            try:
                from database.connection import cancelar_venta
                cancelar_venta(id_venta=venta['idVenta'], rol=self.rol)
                modal.destroy()
                self._cargar_deudas_cliente(df_ref, id_cliente)
                if hasattr(self, 'actualizar_productos_tab'):
                    self.actualizar_productos_tab()
                if hasattr(self, 'actualizar_combobox_productos'):
                    self.actualizar_combobox_productos()
            except Exception as e:
                lbl_error.configure(text=str(e))

        ctk.CTkButton(
            btn_frame, text="Sí, cancelar", width=120, font=("Arial", 12, "bold"),
            fg_color="#8b0000", hover_color="#cc0000", text_color="#ffffff",
            command=ejecutar_cancelacion
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame, text="No, volver", width=120, font=("Arial", 12, "bold"),
            fg_color="#1e1e1e", hover_color="#333333", text_color="#cccccc",
            command=modal.destroy
        ).pack(side="left", padx=10)

    def setup_proveedores_tab(self, parent):
        """Configura la pestaña de proveedores con control de acceso por rol."""

        # ── Barra superior ────────────────────────────────────────────────────
        top_bar = ctk.CTkFrame(parent, fg_color="transparent")
        top_bar.pack(fill="x", padx=40, pady=(0, 16))

        ctk.CTkLabel(
            top_bar, text="Proveedores",
            font=("Arial", 18, "bold"), text_color="#aaaaaa",
        ).pack(side="left")

        # Botón Actualizar (siempre visible)
        ctk.CTkButton(
            top_bar, text="↻ Actualizar",
            font=("Arial", 12, "bold"),
            fg_color="#1e1e1e", hover_color="#333333",
            text_color="#1DB954", width=110,
            command=self.actualizar_lista_proveedores,
        ).pack(side="right")

        # Botón Nuevo Proveedor — SOLO GERENTE
        if self.rol == 1:
            ctk.CTkButton(
                top_bar, text="+ Nuevo Proveedor",
                font=("Arial", 13, "bold"),
                fg_color="#1DB954", hover_color="#179643",
                text_color="#000000", width=155,
                command=self.abrir_nuevo_proveedor,
            ).pack(side="right", padx=(0, 10))

        # ── Layout de 2 columnas ──────────────────────────────────────────────
        main_container = ctk.CTkFrame(parent, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=40, pady=(0, 20))

        # Columna izquierda — Lista
        left_frame = ctk.CTkFrame(main_container, fg_color="#0a0a0a", corner_radius=15, width=280)
        left_frame.pack(side="left", fill="y", padx=(0, 10))
        left_frame.pack_propagate(False)

        ctk.CTkLabel(
            left_frame, text="Lista de Proveedores",
            font=("Arial", 14, "bold"), text_color="#666666",
        ).pack(padx=16, pady=(14, 8), anchor="w")

        self.scroll_proveedores = ctk.CTkScrollableFrame(
            left_frame, fg_color="#0a0a0a", corner_radius=0,
        )
        self.scroll_proveedores.pack(fill="both", expand=True, padx=6, pady=(0, 10))

        # Columna derecha — Detalle
        self.right_frame_prov = ctk.CTkFrame(main_container, fg_color="#0a0a0a", corner_radius=15)
        self.right_frame_prov.pack(side="right", fill="both", expand=True, padx=(10, 0))

        # Placeholder inicial derecho
        ctk.CTkLabel(
            self.right_frame_prov,
            text="Selecciona un proveedor para ver\nsus compras pendientes de envío.",
            font=("Arial", 15), text_color="#444444",
        ).pack(expand=True)

        # Cargar lista inicial
        self._proveedores_data = []
        self.actualizar_lista_proveedores()

    def actualizar_lista_proveedores(self):
        """Recarga proveedores desde la BD y re-renderiza la lista."""
        try:
            from database.connection import obtener_proveedores_completos
            self._proveedores_data = obtener_proveedores_completos(self.rol)
        except Exception as e:
            self._proveedores_data = []
            print(f"Error al cargar proveedores: {e}")
        self.render_proveedores(self._proveedores_data)

    def render_proveedores(self, proveedores):
        """Renderiza la lista de proveedores en el panel izquierdo."""
        for w in self.scroll_proveedores.winfo_children():
            w.destroy()

        if not proveedores:
            ctk.CTkLabel(
                self.scroll_proveedores,
                text="No hay proveedores registrados.",
                text_color="#555555",
            ).pack(pady=20)
            return

        for idx, p in enumerate(proveedores):
            bg = "#161616" if idx % 2 == 0 else "#111111"
            row = ctk.CTkFrame(self.scroll_proveedores, fg_color=bg, corner_radius=8)
            row.pack(fill="x", pady=3, padx=4)
            row.grid_columnconfigure(0, weight=1)

            # Botón con nombre del proveedor
            ctk.CTkButton(
                row,
                text=f"  {p['nombre']}  —  NIT: {p.get('nit') or 'N/A'}",
                font=("Arial", 13),
                fg_color="transparent",
                hover_color="#1e2b1e",
                text_color="#ffffff",
                anchor="w",
                height=38,
                command=lambda prov=p: self.mostrar_detalle_proveedor(prov),
            ).grid(row=0, column=0, sticky="ew", padx=(4, 0), pady=4)

            # Botón Editar — SOLO GERENTE
            if self.rol == 1:
                ctk.CTkButton(
                    row, text="✏",
                    width=34, height=34,
                    font=("Arial", 14),
                    fg_color="#1e2b1e",
                    hover_color="#2d472d",
                    text_color="#1DB954",
                    command=lambda prov=p: self.editar_proveedor(prov),
                ).grid(row=0, column=1, padx=(4, 8), pady=4)

    def abrir_nuevo_proveedor(self):
        """Abre la ventana para registrar un nuevo proveedor (solo Gerente)."""
        from gui.nuevo_proveedor import NuevoProveedorWindow
        self.nuevo_prov_win = NuevoProveedorWindow(self)

    def editar_proveedor(self, proveedor):
        """Abre la ventana de edición para un proveedor existente (solo Gerente)."""
        from gui.nuevo_proveedor import NuevoProveedorWindow
        self.nuevo_prov_win = NuevoProveedorWindow(self, proveedor_datos=proveedor)

    def abrir_nueva_compra(self, proveedor):
        """Abre la ventana para registrar una nueva compra (solo Gerente)."""
        from gui.nueva_compra import NuevaCompraWindow
        self.nueva_compra_win = NuevaCompraWindow(self, proveedor=proveedor)

    def mostrar_detalle_proveedor(self, proveedor):
        """Renderiza el panel derecho con la info del proveedor y sus
        compras pendientes (sin envío asignado)."""
        # Limpiar panel derecho
        for widget in self.right_frame_prov.winfo_children():
            widget.destroy()

        # ── Info del proveedor ────────────────────────────────────────────────
        info_frame = ctk.CTkFrame(self.right_frame_prov, fg_color="transparent")
        info_frame.pack(fill="x", padx=20, pady=(20, 8))

        # Fila título + botón Nueva Compra (gerente)
        name_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        name_row.pack(fill="x")

        ctk.CTkLabel(
            name_row,
            text=proveedor.get('nombre', ''),
            font=("Arial", 22, "bold"), text_color="#ffffff",
        ).pack(side="left", anchor="w")

        if self.rol == 1:
            ctk.CTkButton(
                name_row,
                text="+ Nueva Compra",
                font=("Arial", 13, "bold"),
                fg_color="#1DB954", hover_color="#179643",
                text_color="#000000", height=34,
                command=lambda: self.abrir_nueva_compra(proveedor),
            ).pack(side="right")

        for label, key in [
            ("NIT",       "nit"),
            ("Teléfono",  "telefono"),
            ("Correo",    "correo"),
            ("Dirección", "direccion"),
        ]:
            valor = proveedor.get(key) or "N/A"
            ctk.CTkLabel(
                info_frame,
                text=f"{label}: {valor}",
                font=("Arial", 13), text_color="#888888",
            ).pack(anchor="w", pady=1)

        # ── Separador ─────────────────────────────────────────────────────────
        ctk.CTkFrame(self.right_frame_prov, height=1, fg_color="#2a2a2a").pack(fill="x", padx=20, pady=10)

        # ── Compras sin envío ────────────────────────────────────────────────
        ctk.CTkLabel(
            self.right_frame_prov,
            text="Compras Pendientes (sin envío asignado)",
            font=("Arial", 15, "bold"), text_color="#1DB954",
        ).pack(anchor="w", padx=20, pady=(0, 8))

        scroll_compras = ctk.CTkScrollableFrame(
            self.right_frame_prov, fg_color="#080808", corner_radius=10,
        )
        scroll_compras.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        try:
            from database.connection import obtener_compras_sin_envio_por_proveedor
            compras = obtener_compras_sin_envio_por_proveedor(
                proveedor['idProveedor'], self.rol
            )

            if not compras:
                ctk.CTkLabel(
                    scroll_compras,
                    text="Sin compras pendientes para este proveedor.",
                    text_color="#555555",
                ).pack(pady=24)
            else:
                for idx, c in enumerate(compras):
                    bg = "#181818" if idx % 2 == 0 else "#111111"
                    card = ctk.CTkFrame(scroll_compras, fg_color=bg, corner_radius=10)
                    card.pack(fill="x", pady=5)

                    id_compra = c.get('idCompra', 'N/A')
                    fecha = c.get('fechacompra', 'N/A')
                    if hasattr(fecha, 'strftime'):
                        fecha = fecha.strftime('%Y-%m-%d %H:%M')
                    total      = float(c.get('total_productos', 0))
                    unidades   = int(c.get('total_unidades', 0))

                    # Cabecera de la compra
                    hdr_row = ctk.CTkFrame(card, fg_color="transparent")
                    hdr_row.pack(fill="x", padx=12, pady=(10, 4))

                    ctk.CTkLabel(
                        hdr_row,
                        text=f"Compra #{id_compra}",
                        font=("Arial", 14, "bold"), text_color="#ffffff",
                    ).pack(side="left")

                    ctk.CTkLabel(
                        hdr_row,
                        text=fecha,
                        font=("Arial", 12), text_color="#777777",
                    ).pack(side="right")

                    # Detalle de productos
                    detalle = c.get('detalle', [])
                    if detalle:
                        for prod in detalle:
                            ctk.CTkLabel(
                                card,
                                text=f"  • {prod['nombre']}  ({prod['referencia']})   ×{prod['cantidad']}   ${float(prod.get('subtotal', 0)):,.2f}",
                                font=("Arial", 12), text_color="#aaaaaa",
                                anchor="w",
                            ).pack(fill="x", padx=16, pady=1)

                    # Pie de la compra
                    ctk.CTkLabel(
                        card,
                        text=f"  {unidades} unidades — Total estimado: ${total:,.2f}",
                        font=("Arial", 13, "bold"), text_color="#1DB954",
                        anchor="w",
                    ).pack(fill="x", padx=12, pady=(6, 10))

        except Exception as e:
            ctk.CTkLabel(
                scroll_compras,
                text=f"Error al cargar compras: {e}",
                text_color="#ff4d4d",
            ).pack(pady=20)

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
        # Limpiar el contenedor scrollable
        for widget in self.scroll_envios.winfo_children():
            widget.destroy()

        if not envios:
            ctk.CTkLabel(self.scroll_envios, text="No hay envíos registrados aún.", text_color="#888888").pack(pady=20)
            return

        # 1. CREAR UN SÓLO CONTENEDOR MAESTRO PARA TODA LA TABLA
        table_frame = ctk.CTkFrame(self.scroll_envios, fg_color="transparent")
        table_frame.pack(fill="x", expand=True)
        
        # 2. CONFIGURAR LAS COLUMNAS UNA SOLA VEZ
        table_frame.grid_columnconfigure(0, weight=1) # ID
        table_frame.grid_columnconfigure(1, weight=2) # Proveedor
        table_frame.grid_columnconfigure(2, weight=1) # Fecha
        table_frame.grid_columnconfigure(3, weight=1) # Valor a pagar
        table_frame.grid_columnconfigure(4, weight=1) # Acciones
        
        # 3. ENCABEZADOS (Fila 0)
        headers_color = "#1e1e1e"
        ctk.CTkLabel(table_frame, text="ID Envío", font=("Arial", 14, "bold"), text_color="#1DB954", fg_color=headers_color, anchor="w", padx=10, pady=10).grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(table_frame, text="Proveedor", font=("Arial", 14, "bold"), text_color="#1DB954", fg_color=headers_color, anchor="w", padx=10, pady=10).grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(table_frame, text="Fecha", font=("Arial", 14, "bold"), text_color="#1DB954", fg_color=headers_color, anchor="w", padx=10, pady=10).grid(row=0, column=2, sticky="nsew")
        ctk.CTkLabel(table_frame, text="Valor a Pagar", font=("Arial", 14, "bold"), text_color="#1DB954", fg_color=headers_color, anchor="w", padx=10, pady=10).grid(row=0, column=3, sticky="nsew")
        ctk.CTkLabel(table_frame, text="Acciones", font=("Arial", 14, "bold"), text_color="#1DB954", fg_color=headers_color, anchor="w", padx=10, pady=10).grid(row=0, column=4, sticky="nsew")
        
        # 4. FILAS DE ENVÍOS (Filas consecutivas: idx + 1)
        for idx, envio in enumerate(envios):
            row_idx = idx + 1
            row_color = "#121212" if idx % 2 == 0 else "#0a0a0a"
            
            # Celdas de información básica
            ctk.CTkLabel(table_frame, text=envio.get('idEnvio', 'N/A'), text_color="#cccccc", fg_color=row_color, anchor="w", padx=10, pady=8).grid(row=row_idx, column=0, sticky="nsew")
            ctk.CTkLabel(table_frame, text=envio.get('proveedor', 'N/A'), text_color="#ffffff", fg_color=row_color, anchor="w", padx=10, pady=8).grid(row=row_idx, column=1, sticky="nsew")
            ctk.CTkLabel(table_frame, text=envio.get('fecha', 'N/A'), text_color="#cccccc", fg_color=row_color, anchor="w", padx=10, pady=8).grid(row=row_idx, column=2, sticky="nsew")
            
            valor = envio.get('valor', 0)
            ctk.CTkLabel(table_frame, text=f"${valor:,.2f}", text_color="#cccccc", fg_color=row_color, anchor="w", padx=10, pady=8).grid(row=row_idx, column=3, sticky="nsew")
            
            # Celda de Acciones (Contenedor intermedio para mantener el fondo cebra intacto)
            actions_frame = ctk.CTkFrame(table_frame, fg_color=row_color, corner_radius=0)
            actions_frame.grid(row=row_idx, column=4, sticky="nsew")
            
            btn_detalles = ctk.CTkButton(
                actions_frame, 
                text="Ver Detalles", 
                width=80, 
                height=28, 
                font=("Arial", 12, "bold"),
                fg_color="#333333", 
                hover_color="#555555",
                text_color="#ffffff",
                command=lambda env=envio: self.ver_detalle_envio(env)
            )
            btn_detalles.pack(padx=10, pady=6, anchor="w")

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

        producto_sel = None
        for p in getattr(self, 'todos_productos', []):
            if f"{p['nombre']} ({p['referencia']})" == prod_str:
                producto_sel = p
                break
        
        if not producto_sel:
            return
            
        bodega = int(producto_sel.get('bodega', 0) or 0)
        cant_en_carrito = sum(item['cantidad'] for item in self.carrito_ventas if item['idProducto'] == producto_sel['idProducto'])
        if cantidad + cant_en_carrito > bodega:
            # No hay suficiente inventario
            return

        encontrado = False
        for item in self.carrito_ventas:
            if item['idProducto'] == producto_sel['idProducto']:
                item['cantidad'] += cantidad
                encontrado = True
                break
                
        if not encontrado:
            self.carrito_ventas.append({
                'idProducto': producto_sel['idProducto'],
                'nombre': producto_sel['nombre'],
                'referencia': producto_sel['referencia'],
                'precio_venta': float(producto_sel['precio_venta']),
                'cantidad': cantidad
            })

        self.actualizar_carrito_ui()
        
        # Reiniciar producto y cantidad
        self.entry_cantidad.delete(0, 'end')
        self.combo_producto.set("Seleccione producto...")

    def actualizar_carrito_ui(self):
        for w in self.scroll_carrito.winfo_children():
            w.destroy()
            
        self.total_ventas = 0.0
        
        if not self.carrito_ventas:
            self.lbl_carrito_vacio = ctk.CTkLabel(self.scroll_carrito, text="La lista está vacía.", text_color="#666666")
            self.lbl_carrito_vacio.pack(pady=20)
            self.lbl_total_venta.configure(text="Total Venta: $0.00")
            return
            
        for idx, item in enumerate(self.carrito_ventas):
            subtotal = item['cantidad'] * item['precio_venta']
            self.total_ventas += subtotal
            
            row = ctk.CTkFrame(self.scroll_carrito, fg_color="#1a1a1a", corner_radius=5)
            row.pack(fill="x", pady=2)
            
            lbl_desc = ctk.CTkLabel(row, text=f"{item['nombre']} ({item['referencia']}) x{item['cantidad']}", font=("Arial", 12))
            lbl_desc.pack(side="left", padx=10, pady=5)
            
            lbl_sub = ctk.CTkLabel(row, text=f"${subtotal:,.2f}", font=("Arial", 12, "bold"), text_color="#1DB954")
            lbl_sub.pack(side="right", padx=10, pady=5)
            
            btn_eliminar = ctk.CTkButton(row, text="X", width=25, height=25, fg_color="#ff4d4d", hover_color="#cc0000",
                                         command=lambda i=idx: self.eliminar_del_carrito(i))
            btn_eliminar.pack(side="right", padx=5)
            
        self.lbl_total_venta.configure(text=f"Total Venta: ${self.total_ventas:,.2f}")

    def eliminar_del_carrito(self, index):
        if 0 <= index < len(self.carrito_ventas):
            self.carrito_ventas.pop(index)
            self.actualizar_carrito_ui()

    def procesar_venta(self):
        if not self.carrito_ventas:
            return
            
        cliente_str = self.combo_cliente.get()
        if cliente_str == "Seleccione cliente..." or not cliente_str:
            return
            
        cliente_sel = None
        for c in getattr(self, 'todos_clientes', []):
            if f"{c['nombre']} {c['apellidos']} ({c['documento']})" == cliente_str:
                cliente_sel = c
                break
                
        if not cliente_sel:
            return
            
        modal = ctk.CTkToplevel(self)
        modal.title("Confirmar Venta")
        modal.geometry("400x455")
        modal.resizable(False, False)
        modal.configure(fg_color="#0d0d0d")
        modal.grab_set()
        modal.focus()
        
        ctk.CTkLabel(modal, text="Confirmar Venta", font=("Arial", 20, "bold"), text_color="#1DB954").pack(pady=(20, 10))
        ctk.CTkLabel(modal, text=f"Total: ${self.total_ventas:,.2f}", font=("Arial", 16, "bold")).pack(pady=5)
        
        ctk.CTkLabel(modal, text="Estado de Pago:", font=("Arial", 12)).pack(anchor="w", padx=30, pady=(5, 2))
        combo_estado = ctk.CTkComboBox(modal, values=["PAGADO", "PENDIENTE"], width=340)
        combo_estado.pack(padx=30)
        combo_estado.set("PAGADO")
        
        ctk.CTkLabel(modal, text="Método de Pago:", font=("Arial", 12)).pack(anchor="w", padx=30, pady=(10, 2))
        
        try:
            from database.connection import obtener_saldos_cuentas
            cuentas = obtener_saldos_cuentas(self.rol)
            opciones_cuentas = [f"{c['tipo_cuenta']} ({c['num_cuenta']})" for c in cuentas]
            self._cuentas_pago_map = {f"{c['tipo_cuenta']} ({c['num_cuenta']})": c['idMetodo_de_pago'] for c in cuentas}
        except Exception:
            opciones_cuentas = []
            self._cuentas_pago_map = {}
            
        if not opciones_cuentas:
            opciones_cuentas = ["Sin métodos"]
            
        combo_metodo = ctk.CTkComboBox(modal, values=opciones_cuentas, width=340)
        combo_metodo.pack(padx=30)

        ctk.CTkLabel(modal, text="Abono inicial ($):", font=("Arial", 12)).pack(anchor="w", padx=30, pady=(10, 2))
        entry_abono = ctk.CTkEntry(modal, width=340)
        entry_abono.pack(padx=30)

        lbl_ayuda_abono = ctk.CTkLabel(
            modal,
            text="El pago completo cubre el total de la venta.",
            text_color="#888888",
            font=("Arial", 11),
            wraplength=340
        )
        lbl_ayuda_abono.pack(pady=(3, 0))

        def actualizar_forma_pago(estado):
            entry_abono.configure(state="normal")
            entry_abono.delete(0, "end")
            if estado == "PAGADO":
                entry_abono.insert(0, f"{self.total_ventas:.2f}")
                entry_abono.configure(state="disabled")
                lbl_ayuda_abono.configure(text="El pago completo cubre el total de la venta.")
            else:
                entry_abono.configure(state="normal")
                entry_abono.insert(0, "0.00")
                lbl_ayuda_abono.configure(
                    text="Puede abonar una parte ahora o dejar 0 para pagar después desde Clientes."
                )

        combo_estado.configure(command=actualizar_forma_pago)
        actualizar_forma_pago("PAGADO")
        
        lbl_estado = ctk.CTkLabel(modal, text="", text_color="#ff4d4d", wraplength=340)
        lbl_estado.pack(pady=10)
        
        btn_confirmar = ctk.CTkButton(modal, text="Confirmar y Registrar", font=("Arial", 14, "bold"), fg_color="#1DB954", hover_color="#179643",
                                      command=lambda: self.finalizar_venta(
                                          modal, cliente_sel, combo_estado.get(), combo_metodo.get(),
                                          entry_abono.get(), lbl_estado
                                      ))
        btn_confirmar.pack(pady=10)
        
    def finalizar_venta(self, modal, cliente, estado_pago, metodo_str, monto_str, lbl_estado):
        try:
            id_metodo = None
            if estado_pago == "PAGADO":
                monto_pagado = self.total_ventas
            else:
                try:
                    monto_pagado = float(monto_str.strip().replace(",", "."))
                except (AttributeError, ValueError):
                    lbl_estado.configure(text="Ingrese un abono numérico válido.")
                    return

                if not isfinite(monto_pagado):
                    lbl_estado.configure(text="Ingrese un abono numérico válido.")
                    return
                if monto_pagado < 0:
                    lbl_estado.configure(text="El abono no puede ser negativo.")
                    return
                if monto_pagado >= self.total_ventas:
                    lbl_estado.configure(
                        text="Para pagar el total, seleccione el estado PAGADO."
                    )
                    return

            if monto_pagado > 0:
                if not getattr(self, '_cuentas_pago_map', {}) or metodo_str not in self._cuentas_pago_map:
                    lbl_estado.configure(text="Seleccione un método de pago válido para registrar el abono.")
                    return
                id_metodo = self._cuentas_pago_map[metodo_str]
                
            from database.connection import registrar_venta
            registrar_venta(
                id_empleado=self.id_empleado, 
                id_cliente=cliente['idCliente'], 
                productos=self.carrito_ventas, 
                id_metodo_pago=id_metodo, 
                monto_pagado=monto_pagado, 
                estado_pago=estado_pago, 
                valor_total=self.total_ventas, 
                rol=self.rol
            )
            
            lbl_estado.configure(text="¡Venta registrada con éxito!", text_color="#1DB954")
            modal.after(1200, modal.destroy)
            
            # Limpiar carrito
            self.carrito_ventas = []
            self.actualizar_carrito_ui()
            self.entry_cantidad.delete(0, 'end')
            self.combo_producto.set("Seleccione producto...")
            self.combo_cliente.set("Seleccione cliente...")
            
            # Actualizar datos de UI que dependan de bd
            if hasattr(self, 'actualizar_productos_tab'):
                self.actualizar_productos_tab()
            if hasattr(self, 'actualizar_combobox_productos'):
                self.actualizar_combobox_productos()
            if hasattr(self, 'actualizar_cuentas_tab'):
                self.actualizar_cuentas_tab()
                
        except Exception as e:
            lbl_estado.configure(text=str(e), text_color="#ff4d4d")

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
        """Renderiza la tabla completa de nómina mediante una grilla única global."""
        for w in self.scroll_empleados.winfo_children():
            w.destroy()

        empleados = getattr(self, '_todos_empleados_nomina', [])
        if not empleados:
            ctk.CTkLabel(
                self.scroll_empleados,
                text="No hay empleados registrados.", text_color="#888888"
            ).pack(pady=30)
            return

        # 1. CREAR UN SÓLO CONTENEDOR MAESTRO PARA TODA LA TABLA
        table_frame = ctk.CTkFrame(self.scroll_empleados, fg_color="transparent")
        table_frame.pack(fill="x", expand=True)

        # 2. CONFIGURAR LAS PROPORCIONES DE LAS COLUMNAS GLOBALES
        pesos = [2, 1, 1, 1, 1, 1]
        for i, w in enumerate(pesos):
            table_frame.grid_columnconfigure(i, weight=w)

        # 3. ENCABEZADOS (Fila 0 de la grilla)
        headers_color = "#1e1e1e"
        cols_hdr = ["Empleado", "Rol", "$/Hora", "Horas", "Total a Pagar", "Acciones"]
        for i, col in enumerate(cols_hdr):
            ctk.CTkLabel(
                table_frame, text=col,
                font=("Arial", 13, "bold"), text_color="#1DB954",
                fg_color=headers_color, anchor="w", padx=12, pady=10
            ).grid(row=0, column=i, sticky="nsew")

        # 4. FILAS DINÁMICAS (2 filas matemáticas por empleado)
        for idx, emp in enumerate(empleados):
            main_row = (idx * 2) + 1    # Fila para los datos principales
            ventas_row = (idx * 2) + 2  # Fila para su desplegable de ventas
            
            pago_hora   = float(emp.get('pago_hora',   0) or 0)
            trabajo_hora = float(emp.get('trabajo_hora', 0) or 0)
            total        = pago_hora * trabajo_hora
            emp_rol      = emp.get('rol', 0)

            bg = "#161616" if idx % 2 == 0 else "#0d0d0d"

            # Columna 0: Nombre
            ctk.CTkLabel(
                table_frame, text=emp['nombre'],
                font=("Arial", 14, "bold"), text_color="#ffffff",
                fg_color=bg, anchor="w", padx=12, pady=10
            ).grid(row=main_row, column=0, sticky="nsew")

            # Columna 1: Rol badge
            rol_txt   = "👑 Gerente" if emp_rol == 1 else "Empleado"
            rol_color = "#FFD700"   if emp_rol == 1 else "#aaaaaa"
            ctk.CTkLabel(
                table_frame, text=rol_txt,
                font=("Arial", 13), text_color=rol_color,
                fg_color=bg, anchor="w", padx=12, pady=10
            ).grid(row=main_row, column=1, sticky="nsew")

            # Columna 2: $/Hora
            ctk.CTkLabel(
                table_frame, text=f"${pago_hora:,.2f}",
                font=("Arial", 13), text_color="#cccccc",
                fg_color=bg, anchor="w", padx=12, pady=10
            ).grid(row=main_row, column=2, sticky="nsew")

            # Columna 3: Horas trabajadas
            horas_color = "#1DB954" if trabajo_hora > 0 else "#555555"
            ctk.CTkLabel(
                table_frame, text=f"{trabajo_hora:.1f} h",
                font=("Arial", 13, "bold"), text_color=horas_color,
                fg_color=bg, anchor="w", padx=12, pady=10
            ).grid(row=main_row, column=3, sticky="nsew")

            # Columna 4: Total a pagar
            total_color = "#1DB954" if total > 0 else "#555555"
            ctk.CTkLabel(
                table_frame, text=f"${total:,.2f}",
                font=("Arial", 14, "bold"), text_color=total_color,
                fg_color=bg, anchor="w", padx=12, pady=10
            ).grid(row=main_row, column=4, sticky="nsew")

            # Columna 5: Contenedor de Acciones (Mantiene el fondo cebra continuo)
            acc = ctk.CTkFrame(table_frame, fg_color=bg, corner_radius=0)
            acc.grid(row=main_row, column=5, sticky="nsew")

            # Frame expandible (Hijo directo de table_frame, esperando en su "ventas_row")
            ventas_frame = ctk.CTkFrame(table_frame, fg_color="#0b0b0b", corner_radius=8)
            id_emp = emp['idEmpleado']

            # Botón Ventas
            btn_ventas = ctk.CTkButton(
                acc, text="▶ Ventas",
                font=("Arial", 12), width=90, height=28,
                fg_color="#1e2a1e", hover_color="#2d472d", text_color="#1DB954"
            )
            btn_ventas.configure(
                command=lambda iid=id_emp, vf=ventas_frame, btn=btn_ventas, r=ventas_row:
                    self._toggle_ventas(iid, vf, btn, r)
            )
            btn_ventas.pack(side="left", padx=(0, 6), pady=6)

            # Botón Editar
            btn_editar = ctk.CTkButton(
                acc, text="✏ Editar",
                font=("Arial", 12), width=75, height=28,
                fg_color="#1e1e1e", hover_color="#2b2b2b", text_color="#ffffff",
                command=lambda e=emp: self._abrir_editar_empleado(e)
            )
            btn_editar.pack(side="left", padx=(0, 6), pady=6)

            # Botón Pagar
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
            btn_pagar.pack(side="left", pady=6)

            # Si el empleado ya estaba expandido, se dibuja en su fila reservada
            if id_emp in self._empleados_expandidos:
                self._cargar_ventas_en_frame(id_emp, ventas_frame)
                ventas_frame.grid(row=ventas_row, column=0, columnspan=6, padx=10, pady=(0, 10), sticky="ew")
                btn_ventas.configure(text="▼ Ventas")

    # --- Helpers del módulo empleados ---

    def _toggle_ventas(self, id_empleado, ventas_frame, btn, row):
        """Expande o colapsa el panel de ventas usando grid (sin pack)."""
        if id_empleado in self._empleados_expandidos:
            # Colapsar: Ocultar usando grid (colspan)
            self._empleados_expandidos.discard(id_empleado)
            ventas_frame.grid_forget()
            btn.configure(text="▶ Ventas")
        else:
            # Expandir: Mostrar usando grid (colspan)
            self._empleados_expandidos.add(id_empleado)
            self._cargar_ventas_en_frame(id_empleado, ventas_frame)
            ventas_frame.grid(row=row, column=0, columnspan=6, padx=10, pady=(0, 10), sticky="ew")
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
        # Limpiar el contenedor scrollable
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
            
        # 1. CONTENEDOR MAESTRO ÚNICO PARA TU TABLA
        table_frame = ctk.CTkFrame(self.scroll_cuentas_pagar, fg_color="transparent")
        table_frame.pack(fill="x", expand=True)
        
        # 2. CONFIGURACIÓN DE LAS COLUMNAS GLOBALES
        pesos = [1, 2, 2, 1, 1]
        for i, w in enumerate(pesos):
            table_frame.grid_columnconfigure(i, weight=w)
            
        # 3. ENCABEZADOS DE LA TABLA (Fila 0 de la grilla)
        headers_color = "#1e1e1e"
        cols = ["Compra ID", "Proveedor", "Fecha Compra", "Total Compra", "Estado Envío"]
        for i, col in enumerate(cols):
            ctk.CTkLabel(
                table_frame, text=col, 
                font=("Arial", 12, "bold"), text_color="#1DB954",
                fg_color=headers_color, anchor="w", padx=10, pady=8
            ).grid(row=0, column=i, sticky="nsew")
            
        # 4. ITERACIÓN DE FILAS DINÁMICAS (Filas consecutivas: idx + 1)
        for idx, c in enumerate(cuentas):
            row_idx = idx + 1
            bg = "#161616" if idx % 2 == 0 else "#0d0d0d"
            
            # Formateo y validación segura de la fecha
            fecha = c.get('fechacompra', '')
            if hasattr(fecha, 'strftime'):
                fecha = fecha.strftime('%d/%m/%Y %H:%M')
                
            total = float(c.get('total_compra', 0) or 0)
            
            # Celda 0: Compra ID
            ctk.CTkLabel(
                table_frame, text=f"#{c['idCompra']}", 
                font=("Arial", 13, "bold"), text_color="#ffffff",
                fg_color=bg, anchor="w", padx=10, pady=8
            ).grid(row=row_idx, column=0, sticky="nsew")
            
            # Celda 1: Proveedor
            ctk.CTkLabel(
                table_frame, text=c['proveedor'], 
                font=("Arial", 13), text_color="#ffffff",
                fg_color=bg, anchor="w", padx=10, pady=8
            ).grid(row=row_idx, column=1, sticky="nsew")
            
            # Celda 2: Fecha Compra
            ctk.CTkLabel(
                table_frame, text=str(fecha), 
                font=("Arial", 13), text_color="#cccccc",
                fg_color=bg, anchor="w", padx=10, pady=8
            ).grid(row=row_idx, column=2, sticky="nsew")
            
            # Celda 3: Total Compra
            ctk.CTkLabel(
                table_frame, text=f"${total:,.2f}", 
                font=("Arial", 13, "bold"), text_color="#1DB954",
                fg_color=bg, anchor="w", padx=10, pady=8
            ).grid(row=row_idx, column=3, sticky="nsew")
            
            # Celda 4: Estado Envío (Color dinámico semántico)
            est = c['estado_envio']
            est_color = "#1DB954" if est == "Envío Registrado" else "#FFD700"
            ctk.CTkLabel(
                table_frame, text=est, 
                font=("Arial", 13), text_color=est_color,
                fg_color=bg, anchor="w", padx=10, pady=8
            ).grid(row=row_idx, column=4, sticky="nsew")

    # ------------------ BALANCE: ESTADÍSTICAS ------------------
    def setup_balance_stats(self, parent):
        """Tabla de resumen financiero diario de los últimos 7 días."""
        top_bar = ctk.CTkFrame(parent, fg_color="transparent")
        top_bar.pack(fill="x", pady=(10, 15))

        ctk.CTkLabel(
            top_bar, text="Resumen Financiero — Últimos 7 Días",
            font=("Arial", 16, "bold"), text_color="#aaaaaa"
        ).pack(side="left")

        ctk.CTkButton(
            top_bar, text="↻ Actualizar",
            font=("Arial", 12, "bold"),
            fg_color="#1e1e1e", hover_color="#333333", text_color="#1DB954",
            width=100, command=self.actualizar_balance_stats
        ).pack(side="right")

        self.scroll_balance_stats = ctk.CTkScrollableFrame(parent, fg_color="#0a0a0a", corner_radius=10)
        self.scroll_balance_stats.pack(fill="both", expand=True, pady=(0, 10))

        self.actualizar_balance_stats()

    def actualizar_balance_stats(self):
        """Carga y renderiza la tabla de resumen financiero de 7 días."""
        if not hasattr(self, 'scroll_balance_stats'):
            return

        for w in self.scroll_balance_stats.winfo_children():
            w.destroy()

        try:
            from database.connection import obtener_resumen_financiero_7dias
            datos = obtener_resumen_financiero_7dias(self.rol)
        except Exception as e:
            ctk.CTkLabel(
                self.scroll_balance_stats,
                text=f"Error al cargar resumen financiero:\n{e}",
                text_color="#ff4d4d"
            ).pack(pady=20)
            return

        if not datos:
            ctk.CTkLabel(
                self.scroll_balance_stats,
                text="No hay datos financieros disponibles.",
                text_color="#888888"
            ).pack(pady=30)
            return

        # Contenedor de la tabla
        table = ctk.CTkFrame(self.scroll_balance_stats, fg_color="transparent")
        table.pack(fill="x", expand=True)

        # Columnas: Fecha | Saldo Inicial | Gastos | Costos | CxC | Abono | Ventas | Total
        col_headers = ["Fecha", "Saldo Inicial", "Gastos", "Costos", "CxC", "Abono", "Ventas", "Total"]
        col_weights = [2, 2, 1, 1, 1, 1, 2, 2]

        for i, w in enumerate(col_weights):
            table.grid_columnconfigure(i, weight=w)

        # Encabezados
        for i, (hdr, _) in enumerate(zip(col_headers, col_weights)):
            ctk.CTkLabel(
                table, text=hdr,
                font=("Arial", 12, "bold"), text_color="#1DB954",
                fg_color="#1e1e1e", anchor="w", padx=8, pady=10
            ).grid(row=0, column=i, sticky="nsew")

        # Acumuladores para fila totalizadora
        sum_gastos = 0.0
        sum_costos = 0.0
        sum_cxc = 0.0
        sum_abonos = 0.0
        sum_ventas = 0.0

        # Filas de datos
        for idx, dia in enumerate(datos):
            row_idx = idx + 1
            bg = "#121212" if idx % 2 == 0 else "#0a0a0a"

            fecha_str = dia['fecha']
            # Formatear fecha legible (dd/mm/yyyy)
            try:
                from datetime import datetime
                fecha_obj = datetime.strptime(fecha_str, "%Y-%m-%d")
                # Nombres de día en español
                dias_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
                nombre_dia = dias_semana[fecha_obj.weekday()]
                fecha_display = f"{nombre_dia} {fecha_obj.strftime('%d/%m')}"
            except Exception:
                fecha_display = fecha_str

            si = float(dia['saldo_inicial'])
            g = float(dia['gastos'])
            c = float(dia['costos'])
            cxc = float(dia['cxc'])
            a = float(dia['abonos'])
            v = float(dia['ventas_total'])
            se = float(dia['saldo_esperado'])

            sum_gastos += g
            sum_costos += c
            sum_cxc += cxc
            sum_abonos += a
            sum_ventas += v

            # Fecha
            ctk.CTkLabel(
                table, text=fecha_display,
                font=("Arial", 12, "bold"), text_color="#ffffff",
                fg_color=bg, anchor="w", padx=8, pady=8
            ).grid(row=row_idx, column=0, sticky="nsew")

            # Saldo Inicial
            ctk.CTkLabel(
                table, text=f"${si:,.0f}",
                font=("Arial", 12), text_color="#cccccc",
                fg_color=bg, anchor="w", padx=8, pady=8
            ).grid(row=row_idx, column=1, sticky="nsew")

            # Gastos (rojo)
            g_color = "#ff4d4d" if g > 0 else "#555555"
            ctk.CTkLabel(
                table, text=f"-${g:,.0f}" if g > 0 else "$0",
                font=("Arial", 12, "bold"), text_color=g_color,
                fg_color=bg, anchor="w", padx=8, pady=8
            ).grid(row=row_idx, column=2, sticky="nsew")

            # Costos (naranja)
            c_color = "#FF8C00" if c > 0 else "#555555"
            ctk.CTkLabel(
                table, text=f"-${c:,.0f}" if c > 0 else "$0",
                font=("Arial", 12, "bold"), text_color=c_color,
                fg_color=bg, anchor="w", padx=8, pady=8
            ).grid(row=row_idx, column=3, sticky="nsew")

            # CxC (amarillo)
            cxc_color = "#FFD700" if cxc > 0 else "#555555"
            ctk.CTkLabel(
                table, text=f"${cxc:,.0f}" if cxc > 0 else "$0",
                font=("Arial", 12), text_color=cxc_color,
                fg_color=bg, anchor="w", padx=8, pady=8
            ).grid(row=row_idx, column=4, sticky="nsew")

            # Abono (verde claro)
            a_color = "#1DB954" if a > 0 else "#555555"
            ctk.CTkLabel(
                table, text=f"+${a:,.0f}" if a > 0 else "$0",
                font=("Arial", 12, "bold"), text_color=a_color,
                fg_color=bg, anchor="w", padx=8, pady=8
            ).grid(row=row_idx, column=5, sticky="nsew")

            # Ventas
            v_color = "#ffffff" if v > 0 else "#555555"
            ctk.CTkLabel(
                table, text=f"${v:,.0f}" if v > 0 else "$0",
                font=("Arial", 12, "bold"), text_color=v_color,
                fg_color=bg, anchor="w", padx=8, pady=8
            ).grid(row=row_idx, column=6, sticky="nsew")

            # Total / Saldo Esperado
            se_color = "#1DB954" if se >= 0 else "#ff4d4d"
            ctk.CTkLabel(
                table, text=f"${se:,.0f}",
                font=("Arial", 13, "bold"), text_color=se_color,
                fg_color=bg, anchor="w", padx=8, pady=8
            ).grid(row=row_idx, column=7, sticky="nsew")

        # Fila totalizadora
        total_row = len(datos) + 1
        total_bg = "#1a2a1a"

        ctk.CTkLabel(
            table, text="TOTALES",
            font=("Arial", 12, "bold"), text_color="#1DB954",
            fg_color=total_bg, anchor="w", padx=8, pady=10
        ).grid(row=total_row, column=0, sticky="nsew")

        # Saldo Inicial del primer día
        primer_si = float(datos[0]['saldo_inicial'])
        ctk.CTkLabel(
            table, text=f"${primer_si:,.0f}",
            font=("Arial", 12, "bold"), text_color="#aaaaaa",
            fg_color=total_bg, anchor="w", padx=8, pady=10
        ).grid(row=total_row, column=1, sticky="nsew")

        ctk.CTkLabel(
            table, text=f"-${sum_gastos:,.0f}",
            font=("Arial", 12, "bold"), text_color="#ff4d4d",
            fg_color=total_bg, anchor="w", padx=8, pady=10
        ).grid(row=total_row, column=2, sticky="nsew")

        ctk.CTkLabel(
            table, text=f"-${sum_costos:,.0f}",
            font=("Arial", 12, "bold"), text_color="#FF8C00",
            fg_color=total_bg, anchor="w", padx=8, pady=10
        ).grid(row=total_row, column=3, sticky="nsew")

        ctk.CTkLabel(
            table, text=f"${sum_cxc:,.0f}",
            font=("Arial", 12, "bold"), text_color="#FFD700",
            fg_color=total_bg, anchor="w", padx=8, pady=10
        ).grid(row=total_row, column=4, sticky="nsew")

        ctk.CTkLabel(
            table, text=f"+${sum_abonos:,.0f}",
            font=("Arial", 12, "bold"), text_color="#1DB954",
            fg_color=total_bg, anchor="w", padx=8, pady=10
        ).grid(row=total_row, column=5, sticky="nsew")

        ctk.CTkLabel(
            table, text=f"${sum_ventas:,.0f}",
            font=("Arial", 12, "bold"), text_color="#ffffff",
            fg_color=total_bg, anchor="w", padx=8, pady=10
        ).grid(row=total_row, column=6, sticky="nsew")

        # Total final = saldo esperado del último día
        ultimo_se = float(datos[-1]['saldo_esperado'])
        se_total_color = "#1DB954" if ultimo_se >= 0 else "#ff4d4d"
        ctk.CTkLabel(
            table, text=f"${ultimo_se:,.0f}",
            font=("Arial", 13, "bold"), text_color=se_total_color,
            fg_color=total_bg, anchor="w", padx=8, pady=10
        ).grid(row=total_row, column=7, sticky="nsew")

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
