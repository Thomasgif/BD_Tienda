import threading
import customtkinter as ctk
from database.connection import obtener_envios_list


class EnviosTab:
    """Manages the Envíos (shipments) tab."""

    def __init__(self, parent_frame, controller):
        self.controller = controller
        self.todos_envios = []

        top_bar = ctk.CTkFrame(parent_frame, fg_color="transparent")
        top_bar.pack(fill="x", padx=40, pady=(0, 20))

        ctk.CTkLabel(
            top_bar, text="Lista de Pedidos/Envíos de Proveedores",
            font=("Arial", 18, "bold"), text_color="#aaaaaa"
        ).pack(side="left")

        ctk.CTkButton(
            top_bar, text="↻ Actualizar",
            font=("Arial", 12, "bold"),
            fg_color="#1e1e1e", hover_color="#333333", text_color="#1DB954",
            width=100, command=self.cargar
        ).pack(side="right")

        ctk.CTkButton(
            top_bar, text="+ Nuevo Envío",
            font=("Arial", 14, "bold"),
            fg_color="#1DB954", hover_color="#179643", text_color="black",
            command=self._abrir_nuevo_envio
        ).pack(side="right", padx=(0, 10))

        self.entry_buscar = ctk.CTkEntry(
            top_bar, placeholder_text="Buscar por proveedor...", width=200
        )
        self.entry_buscar.pack(side="right", padx=(0, 10))
        self.entry_buscar.bind("<KeyRelease>", self.filtrar)

        self.scroll = ctk.CTkScrollableFrame(
            parent_frame, fg_color="#0a0a0a", corner_radius=10
        )
        self.scroll.pack(fill="both", expand=True, padx=40, pady=(0, 20))

        self.cargar()

    def cargar(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self.scroll, text="Cargando envíos...", text_color="#888888",
            font=("Arial", 14)
        ).pack(pady=30)

        def _fetch():
            try:
                data = obtener_envios_list(self.controller.rol)
                self.scroll.after(0, lambda d=data: self._on_loaded(d))
            except Exception as e:
                self.scroll.after(0, lambda err=str(e): self._on_error(err))

        threading.Thread(target=_fetch, daemon=True).start()

    def _on_loaded(self, data):
        self.todos_envios = data
        self.filtrar()

    def _on_error(self, msg):
        for w in self.scroll.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self.scroll, text=f"Error al cargar envíos:\n{msg}",
            text_color="#ff4d4d"
        ).pack(pady=20)

    def on_show(self):
        self.scroll.update_idletasks()

    def filtrar(self, event=None):
        query = self.entry_buscar.get().lower()
        filtrados = self.todos_envios if not query else [
            e for e in self.todos_envios
            if query in str(e.get('proveedor', '')).lower()
        ]
        self._render(filtrados)

    def _render(self, envios):
        for w in self.scroll.winfo_children():
            w.destroy()

        if not envios:
            ctk.CTkLabel(self.scroll, text="No hay envíos registrados aún.",
                         text_color="#888888").pack(pady=20)
            return

        table = ctk.CTkFrame(self.scroll, fg_color="transparent")
        table.pack(fill="x", expand=True)
        for i, w in enumerate([1, 2, 1, 1, 1]):
            table.grid_columnconfigure(i, weight=w)

        hc = "#1e1e1e"
        for ci, text in enumerate(["ID Envío", "Proveedor", "Fecha", "Valor a Pagar", "Acciones"]):
            ctk.CTkLabel(table, text=text,
                         font=("Arial", 14, "bold"), text_color="#1DB954",
                         fg_color=hc, anchor="w", padx=10, pady=10
                         ).grid(row=0, column=ci, sticky="nsew")

        for idx, envio in enumerate(envios):
            ri = idx + 1
            rc = "#121212" if idx % 2 == 0 else "#0a0a0a"

            ctk.CTkLabel(table, text=envio.get('idEnvio', 'N/A'), text_color="#cccccc",
                         fg_color=rc, anchor="w", padx=10, pady=8
                         ).grid(row=ri, column=0, sticky="nsew")
            ctk.CTkLabel(table, text=envio.get('proveedor', 'N/A'), text_color="#ffffff",
                         fg_color=rc, anchor="w", padx=10, pady=8
                         ).grid(row=ri, column=1, sticky="nsew")
            ctk.CTkLabel(table, text=envio.get('fecha', 'N/A'), text_color="#cccccc",
                         fg_color=rc, anchor="w", padx=10, pady=8
                         ).grid(row=ri, column=2, sticky="nsew")
            ctk.CTkLabel(table, text=f"${envio.get('valor', 0):,.2f}", text_color="#cccccc",
                         fg_color=rc, anchor="w", padx=10, pady=8
                         ).grid(row=ri, column=3, sticky="nsew")

            af = ctk.CTkFrame(table, fg_color=rc, corner_radius=0)
            af.grid(row=ri, column=4, sticky="nsew")
            ctk.CTkButton(
                af, text="Ver Detalles", width=80, height=28,
                font=("Arial", 12, "bold"),
                fg_color="#333333", hover_color="#555555", text_color="#ffffff",
                command=lambda env=envio: self._ver_detalle(env)
            ).pack(padx=10, pady=6, anchor="w")

    def _abrir_nuevo_envio(self):
        from gui.nuevo_envio import NuevoEnvioWindow
        NuevoEnvioWindow(
            self.controller,
            id_empleado=self.controller.id_empleado,
            rol=self.controller.rol,
            on_success=self.cargar
        )

    def _ver_detalle(self, envio):
        from gui.detalle_envio import DetalleEnvioWindow
        DetalleEnvioWindow(self.controller, envio)
