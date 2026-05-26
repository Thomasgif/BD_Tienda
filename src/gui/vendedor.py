import customtkinter as ctk

class VendedorWindow(ctk.CTkToplevel):
    def __init__(self, master=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        
        self.title("Panel de Vendedor")
        self.geometry("900x700")
        self.resizable(True, True)
        self.configure(fg_color="#050505")
        
        # Frame superior para título y botón
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        # Título principal
        self.title_label = ctk.CTkLabel(
            self.top_frame, 
            text="Panel de Control - Vendedor", 
            font=("Arial", 28, "bold"),
            text_color="#1DB954"
        )
        self.title_label.pack(side="left")

        # Botón de Cerrar Sesión
        self.logout_button = ctk.CTkButton(
            self.top_frame,
            text="Cerrar Sesión",
            width=120,
            fg_color="#ff4d4d",
            hover_color="#cc0000",
            text_color="white",
            font=("Arial", 14, "bold"),
            command=self.logout
        )
        self.logout_button.pack(side="right")

        # Crear Tabview (Pestañas)
        self.tabview = ctk.CTkTabview(
            self, 
            fg_color="#121212", 
            segmented_button_fg_color="#1e1e1e",
            segmented_button_selected_color="#1DB954",
            segmented_button_selected_hover_color="#179643"
        )
        self.tabview.pack(padx=20, pady=10, fill="both", expand=True)

        # Añadir las pestañas
        self.tabview.add("Productos")
        self.tabview.add("Ventas")
        self.tabview.add("Cuentas")
        self.tabview.add("Clientes")

        # --- Contenido de la pestaña Productos ---
        self.setup_productos_tab(self.tabview.tab("Productos"))

        # --- Contenido de la pestaña Ventas ---
        self.setup_ventas_tab(self.tabview.tab("Ventas"))

        # --- Contenido de la pestaña Cuentas ---
        self.setup_cuentas_tab(self.tabview.tab("Cuentas"))

        # --- Contenido de la pestaña Clientes ---
        self.setup_clientes_tab(self.tabview.tab("Clientes"))

    def setup_productos_tab(self, parent):
        label = ctk.CTkLabel(parent, text="Gestión de Productos", font=("Arial", 20, "bold"), text_color="#1DB954")
        label.pack(pady=20)
        # Aquí puedes agregar tablas o formularios para buscar/ver productos
        placeholder = ctk.CTkLabel(parent, text="Aquí irá la lista de productos (inventario) y buscador.", text_color="#888888", font=("Arial", 14))
        placeholder.pack()

    def setup_ventas_tab(self, parent):
        label = ctk.CTkLabel(parent, text="Registro de Ventas", font=("Arial", 20, "bold"), text_color="#1DB954")
        label.pack(pady=20)
        # Aquí puedes agregar el formulario para registrar una nueva venta
        placeholder = ctk.CTkLabel(parent, text="Aquí irá el formulario para facturar una nueva venta.", text_color="#888888", font=("Arial", 14))
        placeholder.pack()

    def setup_cuentas_tab(self, parent):
        label = ctk.CTkLabel(parent, text="Estado de Cuentas / Pagos", font=("Arial", 20, "bold"), text_color="#1DB954")
        label.pack(pady=20)
        # Aquí puedes ver el registro de pagos o caja
        placeholder = ctk.CTkLabel(parent, text="Aquí irán los métodos de pago y el reporte de facturación.", text_color="#888888", font=("Arial", 14))
        placeholder.pack()

    def setup_clientes_tab(self, parent):
        label = ctk.CTkLabel(parent, text="Directorio de Clientes", font=("Arial", 20, "bold"), text_color="#1DB954")
        label.pack(pady=20)
        # Formulario para registrar o ver clientes
        placeholder = ctk.CTkLabel(parent, text="Aquí irá el listado y registro de nuevos clientes.", text_color="#888888", font=("Arial", 14))
        placeholder.pack()

    def logout(self):
        # Limpiar los campos de la ventana de login
        if hasattr(self.master, 'user_entry'):
            self.master.user_entry.delete(0, 'end')
            self.master.password_entry.delete(0, 'end')
            self.master.error_label.configure(text="")
            
        # Volver a mostrar la ventana de login original
        self.master.deiconify()
        
        # Destruir esta ventana del vendedor
        self.destroy()
