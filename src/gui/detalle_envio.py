import customtkinter as ctk

class DetalleEnvioWindow(ctk.CTkToplevel):
    def __init__(self, master=None, envio=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        
        self.envio = envio
        self.rol = getattr(master, 'rol', 0)
        
        self.title(f"Detalles - Envío #{self.envio['idEnvio']}")
        self.geometry("600x500")
        self.resizable(False, False)
        self.configure(fg_color="#050505")
        
        # Asegurar que la ventana aparezca por encima
        self.transient(master)
        self.grab_set()
        
        self.build_ui()
        
    def build_ui(self):
        # Frame Principal
        main_frame = ctk.CTkFrame(self, fg_color="#121212", corner_radius=15)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(header_frame, text=f"Envío #{self.envio['idEnvio']} - {self.envio['proveedor']}", font=("Arial", 22, "bold"), text_color="#1DB954").pack(anchor="w")
        
        fecha = self.envio['fecha']
        if hasattr(fecha, 'strftime'):
            fecha = fecha.strftime('%Y-%m-%d')
            
        ctk.CTkLabel(header_frame, text=f"Asociado a la Compra #{self.envio['idCompra']} | Fecha de Envío: {fecha}", font=("Arial", 14), text_color="#aaaaaa").pack(anchor="w", pady=(5, 0))
        
        # Separator
        ctk.CTkFrame(main_frame, height=2, fg_color="#333333").pack(fill="x", padx=20, pady=10)
        
        # Lista de Productos
        ctk.CTkLabel(main_frame, text="Productos Solicitados", font=("Arial", 16, "bold"), text_color="#ffffff").pack(anchor="w", padx=20, pady=(0, 10))
        
        scroll_prods = ctk.CTkScrollableFrame(main_frame, fg_color="#1a1a1a", corner_radius=10)
        scroll_prods.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Cargar productos de la base de datos
        try:
            from database.connection import obtener_detalle_compra
            detalles = obtener_detalle_compra(self.envio['idCompra'], self.rol)
            
            if not detalles:
                ctk.CTkLabel(scroll_prods, text="No hay productos registrados para esta compra.", text_color="#666666").pack(pady=20)
            else:
                for idx, det in enumerate(detalles):
                    row = ctk.CTkFrame(scroll_prods, fg_color="#222222" if idx % 2 == 0 else "#2a2a2a", corner_radius=5)
                    row.pack(fill="x", pady=2)
                    
                    nombre = det['nombre']
                    cant = det['cantidad']
                    precio = det['precio_compra']
                    sub = det['subtotal']
                    
                    ctk.CTkLabel(row, text=f"{cant}x {nombre}", font=("Arial", 14, "bold"), text_color="#cccccc").pack(side="left", padx=10, pady=10)
                    ctk.CTkLabel(row, text=f"${precio:,.2f} c/u  →  Total: ${sub:,.2f}", font=("Arial", 14), text_color="#1DB954").pack(side="right", padx=10, pady=10)
        except Exception as e:
            ctk.CTkLabel(scroll_prods, text=f"Error al cargar productos: {e}", text_color="#ff4d4d").pack(pady=20)
        
        # Footer
        footer_frame = ctk.CTkFrame(main_frame, fg_color="#1e1e1e", corner_radius=10)
        footer_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        valor_pagar = float(self.envio['valor'] or 0)
        ctk.CTkLabel(footer_frame, text="Total Facturado al Proveedor:", font=("Arial", 16), text_color="#aaaaaa").pack(side="left", padx=20, pady=15)
        ctk.CTkLabel(footer_frame, text=f"${valor_pagar:,.2f}", font=("Arial", 20, "bold"), text_color="#1DB954").pack(side="right", padx=20, pady=15)
