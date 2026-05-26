import sys
import os
import customtkinter as ctk


# Agregamos la ruta del directorio padre (src) para poder importar el módulo de base de datos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importamos la función de validación de base de datos que creamos
from database.connection import validar_credenciales

# Configuración básica de aspecto
ctk.set_appearance_mode("dark")  # Modo oscuro
ctk.set_default_color_theme("green")  # Temática verde

class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Sistema de Ventas - Acceso de Empleados")
        self.geometry("500x600")
        self.resizable(False, False)
        
        # Color de fondo negro absoluto para que resalte la temática
        self.configure(fg_color="#050505")

        # Frame central para contener el formulario
        self.frame = ctk.CTkFrame(
            master=self, 
            width=400, 
            height=500, 
            corner_radius=15, 
            fg_color="#121212", 
            border_color="#1DB954", 
            border_width=1
        )
        self.frame.place(relx=0.5, rely=0.5, anchor="center")

        # Título del Login
        self.title_label = ctk.CTkLabel(
            master=self.frame, 
            text="BIENVENIDO", 
            font=("Arial", 28, "bold"), 
            text_color="#1DB954"
        )
        self.title_label.place(relx=0.5, y=60, anchor="center")

        self.subtitle_label = ctk.CTkLabel(
            master=self.frame, 
            text="Inicie sesión para continuar", 
            font=("Arial", 14), 
            text_color="#888888"
        )
        self.subtitle_label.place(relx=0.5, y=95, anchor="center")

        # Campo de Usuario
        self.user_entry = ctk.CTkEntry(
            master=self.frame, 
            width=300, 
            height=45, 
            placeholder_text="Correo o Documento",
            font=("Arial", 14),
            corner_radius=8,
            fg_color="#1e1e1e",
            border_color="#2a2a2a",
            text_color="#ffffff",
            placeholder_text_color="#666666"
        )
        self.user_entry.place(relx=0.5, y=190, anchor="center")

        # Campo de Contraseña
        self.password_entry = ctk.CTkEntry(
            master=self.frame, 
            width=300, 
            height=45, 
            placeholder_text="Contraseña (Documento)",
            show="*",
            font=("Arial", 14),
            corner_radius=8,
            fg_color="#1e1e1e",
            border_color="#2a2a2a",
            text_color="#ffffff",
            placeholder_text_color="#666666"
        )
        self.password_entry.place(relx=0.5, y=270, anchor="center")

        # Mensaje de error / éxito (oculto por defecto)
        self.error_label = ctk.CTkLabel(master=self.frame, text="", font=("Arial", 12), text_color="#ff4d4d")
        self.error_label.place(relx=0.5, y=330, anchor="center")

        # Botón de Login
        self.login_button = ctk.CTkButton(
            master=self.frame, 
            text="Ingresar", 
            width=300, 
            height=45, 
            font=("Arial", 16, "bold"),
            corner_radius=8,
            fg_color="#1DB954",
            hover_color="#179643",
            text_color="#000000",
            command=self.login_event
        )
        self.login_button.place(relx=0.5, y=390, anchor="center")
        
        # Footer
        self.footer_label = ctk.CTkLabel(master=self.frame, text="© Sistema de Ventas v1.0", font=("Arial", 10), text_color="#555555")
        self.footer_label.place(relx=0.5, y=470, anchor="center")

    def login_event(self):
        # Limpiar mensajes previos
        self.error_label.configure(text="")
        
        usuario = self.user_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not usuario or not password:
            self.error_label.configure(text="Por favor, complete todos los campos.", text_color="#ff4d4d")
            return

        try:
            # Intentar validar con la base de datos
            # Recordar: El usuario es correo o documento, y la contraseña es el documento
            empleado = validar_credenciales(usuario, password)
            
            if empleado:
                # Login exitoso: Mostramos mensaje de bienvenida y el nombre del empleado
                nombre_empleado = empleado['nombre']
                self.error_label.configure(text=f"¡Bienvenido, {nombre_empleado}!", text_color="#1DB954")
                
                # Importamos y abrimos la ventana del vendedor
                from gui.vendedor import VendedorWindow
                self.withdraw()  # Oculta la ventana de login
                self.vendedor_window = VendedorWindow(self)
                # Cerramos toda la aplicación cuando se cierre la ventana de vendedor
                self.vendedor_window.protocol("WM_DELETE_WINDOW", self.destroy)
            else:
                # Si retorna None, es porque el correo/documento o el documento (contraseña) no coinciden
                self.error_label.configure(text="Credenciales incorrectas.", text_color="#ff4d4d")
                
        except Exception as e:
            # Si el servidor de base de datos está caído o hay otro error,
            # lo capturamos para evitar que el programa se cierre inesperadamente y se lo mostramos al usuario
            self.error_label.configure(text=str(e), text_color="#ff4d4d")


if __name__ == "__main__":
    app = LoginWindow()
    app.mainloop()
