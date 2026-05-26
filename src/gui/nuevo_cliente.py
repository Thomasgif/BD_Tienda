import customtkinter as ctk

class NuevoClienteWindow(ctk.CTkToplevel):
    def __init__(self, master=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        
        self.title("Crear Nuevo Cliente")
        self.geometry("400x500")
        self.resizable(False, False)
        self.configure(fg_color="#050505")
        
        # Etiqueta temporal
        self.label = ctk.CTkLabel(
            self, 
            text="Formulario Nuevo Cliente\n(En construcción)", 
            font=("Arial", 20, "bold"),
            text_color="#1DB954"
        )
        self.label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Mantener el foco en esta ventana secundaria
        self.grab_set()
