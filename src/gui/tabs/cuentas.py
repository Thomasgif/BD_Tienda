import threading
import customtkinter as ctk
from database.connection import obtener_saldos_cuentas


class CuentasTab:
    """Manages the Cuentas (account balances) tab."""

    def __init__(self, parent_frame, controller):
        self.controller = controller

        top_bar = ctk.CTkFrame(parent_frame, fg_color="transparent")
        top_bar.pack(fill="x", padx=40, pady=(0, 20))

        ctk.CTkLabel(
            top_bar, text="Estado de Cuentas",
            font=("Arial", 18, "bold"), text_color="#aaaaaa"
        ).pack(side="left")

        ctk.CTkButton(
            top_bar, text="↻ Actualizar",
            font=("Arial", 12, "bold"),
            fg_color="#1e1e1e", hover_color="#333333", text_color="#1DB954",
            width=100, command=self.cargar
        ).pack(side="right")

        self.scroll = ctk.CTkScrollableFrame(
            parent_frame, fg_color="#0a0a0a", corner_radius=10
        )
        self.scroll.pack(fill="both", expand=True, padx=40, pady=(0, 20))

        # Carga asíncrona al construir el tab
        self.cargar()

    def cargar(self):
        """Fetch account balances asynchronously."""
        for w in self.scroll.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self.scroll, text="Cargando cuentas...", text_color="#888888",
            font=("Arial", 14)
        ).pack(pady=30)

        def _fetch():
            try:
                data = obtener_saldos_cuentas(self.controller.rol)
                self.scroll.after(0, lambda d=data: self._render(d))
            except Exception as e:
                self.scroll.after(0, lambda err=str(e): self._on_error(err))

        threading.Thread(target=_fetch, daemon=True).start()

    def _on_error(self, msg):
        for w in self.scroll.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self.scroll, text=f"Error cargando cuentas:\n{msg}",
            text_color="#ff4d4d"
        ).pack(pady=20)

    def _render(self, cuentas):
        for w in self.scroll.winfo_children():
            w.destroy()

        if not cuentas:
            ctk.CTkLabel(
                self.scroll, text="No hay cuentas registradas aún.",
                text_color="#888888"
            ).pack(pady=20)
            return

        table = ctk.CTkFrame(self.scroll, fg_color="transparent")
        table.pack(fill="x", expand=True)
        for i, w in enumerate([1, 1, 1]):
            table.grid_columnconfigure(i, weight=w)

        hc = "#1e1e1e"
        for col_idx, text in enumerate(["Método/Cuenta", "Número", "Saldo Total Recaudado"]):
            ctk.CTkLabel(
                table, text=text,
                font=("Arial", 14, "bold"), text_color="#1DB954",
                fg_color=hc, anchor="w", padx=10, pady=10
            ).grid(row=0, column=col_idx, sticky="nsew")

        for idx, cuenta in enumerate(cuentas):
            ri = idx + 1
            rc = "#121212" if idx % 2 == 0 else "#0a0a0a"
            ctk.CTkLabel(table, text=cuenta['tipo_cuenta'], text_color="#ffffff",
                         fg_color=rc, anchor="w", padx=10, pady=8
                         ).grid(row=ri, column=0, sticky="nsew")
            ctk.CTkLabel(table, text=cuenta['num_cuenta'], text_color="#cccccc",
                         fg_color=rc, anchor="w", padx=10, pady=8
                         ).grid(row=ri, column=1, sticky="nsew")
            ctk.CTkLabel(
                table, text=f"${cuenta['saldo_total']:,.2f}",
                text_color="#1DB954", font=("Arial", 14, "bold"),
                fg_color=rc, anchor="w", padx=10, pady=8
            ).grid(row=ri, column=2, sticky="nsew")
