import threading
import customtkinter as ctk
from database.connection import obtener_empleados, obtener_ventas_mes_empleado, obtener_saldos_cuentas, pagar_empleado


class EmpleadosTab:
    """Manages the Empleados (payroll) tab — manager-only."""

    def __init__(self, parent_frame, controller):
        self.controller = controller
        self._todos_empleados = []
        self._expandidos = set()

        top_bar = ctk.CTkFrame(parent_frame, fg_color="transparent")
        top_bar.pack(fill="x", padx=40, pady=(0, 20))

        ctk.CTkLabel(
            top_bar, text="Gestión de Nómina — Mes Actual",
            font=("Arial", 18, "bold"), text_color="#aaaaaa"
        ).pack(side="left")

        ctk.CTkButton(
            top_bar, text="↻ Actualizar",
            font=("Arial", 13, "bold"),
            fg_color="#1e1e1e", hover_color="#333333", text_color="#1DB954",
            width=110, command=self.cargar
        ).pack(side="right")

        ctk.CTkButton(
            top_bar, text="+ Registrar Empleado",
            font=("Arial", 13, "bold"),
            fg_color="#1DB954", hover_color="#179643", text_color="#000000",
            width=160, command=self._abrir_registrar
        ).pack(side="right", padx=(0, 10))

        self.scroll = ctk.CTkScrollableFrame(
            parent_frame, fg_color="#0a0a0a", corner_radius=10
        )
        self.scroll.pack(fill="both", expand=True, padx=40, pady=(0, 20))

        self.cargar()

    # ── Public API ─────────────────────────────────────────────────────────────

    def cargar(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self.scroll, text="Cargando empleados...", text_color="#888888",
            font=("Arial", 14)
        ).pack(pady=30)

        def _fetch():
            try:
                data = obtener_empleados(self.controller.rol)
                self.scroll.after(0, lambda d=data: self._on_loaded(d))
            except Exception as e:
                self.scroll.after(0, lambda err=str(e): self._on_error(err))

        threading.Thread(target=_fetch, daemon=True).start()

    def _on_loaded(self, data):
        self._todos_empleados = data
        self._render()

    def _on_error(self, msg):
        for w in self.scroll.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self.scroll, text=f"Error cargando empleados:\n{msg}",
            text_color="#ff4d4d"
        ).pack(pady=20)

    # ── Rendering ──────────────────────────────────────────────────────────────

    def _render(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        if not self._todos_empleados:
            ctk.CTkLabel(
                self.scroll, text="No hay empleados registrados.",
                text_color="#888888"
            ).pack(pady=30)
            return

        table = ctk.CTkFrame(self.scroll, fg_color="transparent")
        table.pack(fill="x", expand=True)

        for i, w in enumerate([2, 1, 1, 1, 1, 1]):
            table.grid_columnconfigure(i, weight=w)

        hc = "#1e1e1e"
        for i, col in enumerate(["Empleado", "Rol", "$/Hora", "Horas", "Total a Pagar", "Acciones"]):
            ctk.CTkLabel(
                table, text=col,
                font=("Arial", 13, "bold"), text_color="#1DB954",
                fg_color=hc, anchor="w", padx=12, pady=10
            ).grid(row=0, column=i, sticky="nsew")

        for idx, emp in enumerate(self._todos_empleados):
            main_row = (idx * 2) + 1
            ventas_row = (idx * 2) + 2

            pago_hora = float(emp.get('pago_hora', 0) or 0)
            trabajo_hora = float(emp.get('trabajo_hora', 0) or 0)
            total = pago_hora * trabajo_hora
            emp_rol = emp.get('rol', 0)
            bg = "#161616" if idx % 2 == 0 else "#0d0d0d"
            id_emp = emp['idEmpleado']

            ctk.CTkLabel(table, text=emp['nombre'],
                         font=("Arial", 14, "bold"), text_color="#ffffff",
                         fg_color=bg, anchor="w", padx=12, pady=10
                         ).grid(row=main_row, column=0, sticky="nsew")

            rol_txt = "👑 Gerente" if emp_rol == 1 else "Empleado"
            rol_color = "#FFD700" if emp_rol == 1 else "#aaaaaa"
            ctk.CTkLabel(table, text=rol_txt, text_color=rol_color,
                         fg_color=bg, anchor="w", padx=12, pady=10
                         ).grid(row=main_row, column=1, sticky="nsew")

            ctk.CTkLabel(table, text=f"${pago_hora:,.2f}", text_color="#cccccc",
                         fg_color=bg, anchor="w", padx=12, pady=10
                         ).grid(row=main_row, column=2, sticky="nsew")

            horas_color = "#1DB954" if trabajo_hora > 0 else "#555555"
            ctk.CTkLabel(table, text=f"{trabajo_hora:.1f} h",
                         font=("Arial", 13, "bold"), text_color=horas_color,
                         fg_color=bg, anchor="w", padx=12, pady=10
                         ).grid(row=main_row, column=3, sticky="nsew")

            total_color = "#1DB954" if total > 0 else "#555555"
            ctk.CTkLabel(table, text=f"${total:,.2f}",
                         font=("Arial", 14, "bold"), text_color=total_color,
                         fg_color=bg, anchor="w", padx=12, pady=10
                         ).grid(row=main_row, column=4, sticky="nsew")

            acc = ctk.CTkFrame(table, fg_color=bg, corner_radius=0)
            acc.grid(row=main_row, column=5, sticky="nsew")

            ventas_frame = ctk.CTkFrame(table, fg_color="#0b0b0b", corner_radius=8)

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

            ctk.CTkButton(
                acc, text="✏ Editar",
                font=("Arial", 12), width=75, height=28,
                fg_color="#1e1e1e", hover_color="#2b2b2b", text_color="#ffffff",
                command=lambda e=emp: self._abrir_editar(e)
            ).pack(side="left", padx=(0, 6), pady=6)

            ctk.CTkButton(
                acc, text="💳 Pagar",
                font=("Arial", 12, "bold"), width=85, height=28,
                fg_color="#1a3322" if total > 0 else "#1a1a1a",
                hover_color="#1DB954" if total > 0 else "#1a1a1a",
                text_color="#1DB954" if total > 0 else "#444444",
                state="normal" if total > 0 else "disabled",
                command=lambda e=emp, t=total: self._abrir_modal_pago(e, t)
            ).pack(side="left", pady=6)

            if id_emp in self._expandidos:
                self._cargar_ventas(id_emp, ventas_frame)
                ventas_frame.grid(row=ventas_row, column=0, columnspan=6,
                                  padx=10, pady=(0, 10), sticky="ew")
                btn_ventas.configure(text="▼ Ventas")

    # ── Toggle / load helpers ──────────────────────────────────────────────────

    def _toggle_ventas(self, id_emp, vf, btn, row):
        if id_emp in self._expandidos:
            self._expandidos.discard(id_emp)
            vf.grid_forget()
            btn.configure(text="▶ Ventas")
        else:
            self._expandidos.add(id_emp)
            self._cargar_ventas(id_emp, vf)
            vf.grid(row=row, column=0, columnspan=6, padx=10, pady=(0, 10), sticky="ew")
            btn.configure(text="▼ Ventas")

    def _cargar_ventas(self, id_emp, vf):
        for w in vf.winfo_children():
            w.destroy()

        ctk.CTkLabel(
            vf, text="Cargando ventas del mes...",
            font=("Arial", 12), text_color="#888888"
        ).pack(anchor="w", padx=12, pady=10)

        def _fetch():
            try:
                ventas = obtener_ventas_mes_empleado(id_emp, self.controller.rol)
                vf.after(0, lambda v=ventas: self._render_ventas(vf, v))
            except Exception as e:
                vf.after(0, lambda err=str(e): self._render_ventas_error(vf, err))

        threading.Thread(target=_fetch, daemon=True).start()

    def _render_ventas_error(self, vf, err):
        for w in vf.winfo_children():
            w.destroy()
        ctk.CTkLabel(vf, text=f"Error: {err}", text_color="#ff4d4d").pack(padx=12, pady=8)

    def _render_ventas(self, vf, ventas):
        for w in vf.winfo_children():
            w.destroy()

        ctk.CTkLabel(
            vf, text=f"  Ventas del mes ({len(ventas)} registros)",
            font=("Arial", 13, "bold"), text_color="#1DB954"
        ).pack(anchor="w", padx=12, pady=(10, 4))

        if not ventas:
            ctk.CTkLabel(vf, text="Sin ventas registradas este mes.",
                         text_color="#666666", font=("Arial", 12)
                         ).pack(anchor="w", padx=16, pady=(0, 10))
            return

        tabla = ctk.CTkFrame(vf, fg_color="#111111", corner_radius=5)
        tabla.pack(fill="x", padx=10, pady=(0, 10))

        th = ctk.CTkFrame(tabla, fg_color="#1a1a1a")
        th.pack(fill="x")
        mini_cols = [1, 2, 1, 1]
        mini_hdrs = ["# Venta", "Fecha", "Total", "Estado"]
        for i, (h, w) in enumerate(zip(mini_hdrs, mini_cols)):
            th.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(th, text=h, font=("Arial", 12, "bold"), text_color="#aaaaaa"
                         ).grid(row=0, column=i, padx=10, pady=6, sticky="w")

        total_mes = 0.0
        for i, v in enumerate(ventas):
            tr = ctk.CTkFrame(tabla, fg_color="#151515" if i % 2 == 0 else "#111111")
            tr.pack(fill="x")
            for j, w in enumerate(mini_cols):
                tr.grid_columnconfigure(j, weight=w)

            fecha = v.get('fecha_venta', '')
            if hasattr(fecha, 'strftime'):
                fecha = fecha.strftime('%d/%m/%Y %H:%M')
            valor = float(v.get('valor_total', 0) or 0)
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

        tf = ctk.CTkFrame(tabla, fg_color="#1a2a1a")
        tf.pack(fill="x")
        for j, w in enumerate(mini_cols):
            tf.grid_columnconfigure(j, weight=w)
        ctk.CTkLabel(tf, text="TOTAL MES", font=("Arial", 12, "bold"), text_color="#1DB954"
                         ).grid(row=0, column=0, columnspan=2, padx=10, pady=6, sticky="w")
        ctk.CTkLabel(tf, text=f"${total_mes:,.2f}", font=("Arial", 13, "bold"), text_color="#1DB954"
                     ).grid(row=0, column=2, padx=10, pady=6, sticky="w")

    # ── Payment modal ──────────────────────────────────────────────────────────

    def _abrir_modal_pago(self, emp, total):
        modal = ctk.CTkToplevel(self.scroll)
        modal.title("Confirmar Pago de Nómina")
        modal.geometry("480x400")
        modal.resizable(False, False)
        modal.configure(fg_color="#0d0d0d")
        modal.grab_set()
        modal.focus()

        ctk.CTkLabel(modal, text="Confirmación de Pago",
                     font=("Arial", 22, "bold"), text_color="#1DB954"
                     ).pack(pady=(30, 5))
        ctk.CTkFrame(modal, height=2, fg_color="#1DB954").pack(fill="x", padx=30, pady=(0, 20))

        info = ctk.CTkFrame(modal, fg_color="#161616", corner_radius=10)
        info.pack(fill="x", padx=30, pady=(0, 15))

        pago_hora = float(emp.get('pago_hora', 0) or 0)
        trabajo_hora = float(emp.get('trabajo_hora', 0) or 0)

        for lbl_txt, val_txt in [
            ("Empleado:", emp['nombre']),
            ("Sueldo por hora:", f"${pago_hora:,.2f}"),
            ("Horas trabajadas:", f"{trabajo_hora:.1f} h"),
            ("Total a pagar:", f"${total:,.2f}"),
        ]:
            row = ctk.CTkFrame(info, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=3)
            ctk.CTkLabel(row, text=lbl_txt, font=("Arial", 13), text_color="#aaaaaa",
                         width=150, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=val_txt, font=("Arial", 13, "bold"), text_color="#ffffff"
                         ).pack(side="left")

        ctk.CTkLabel(modal, text="Cuenta de la empresa a debitar:",
                     font=("Arial", 13), text_color="#cccccc"
                     ).pack(anchor="w", padx=30, pady=(5, 2))

        try:
            cuentas = obtener_saldos_cuentas(self.controller.rol)
        except Exception:
            cuentas = []

        _cuentas_map = {}
        opciones = []
        for c in cuentas:
            label = f"{c['tipo_cuenta']} ···{c['num_cuenta'][-4:]}  (Saldo: ${float(c['saldo_total']):,.2f})"
            opciones.append(label)
            _cuentas_map[label] = c['idMetodo_de_pago']

        if not opciones:
            opciones = ["Sin cuentas disponibles"]

        combo_cuenta = ctk.CTkComboBox(
            modal, values=opciones, width=400,
            fg_color="#1e1e1e", border_color="#333333",
            button_color="#1DB954", dropdown_hover_color="#1DB954"
        )
        combo_cuenta.set(opciones[0])
        combo_cuenta.pack(padx=30, pady=(0, 10))

        lbl_estado = ctk.CTkLabel(modal, text="", font=("Arial", 12))
        lbl_estado.pack(pady=(0, 5))

        btn_row = ctk.CTkFrame(modal, fg_color="transparent")
        btn_row.pack(pady=(5, 20))

        ctk.CTkButton(btn_row, text="Cancelar",
                      font=("Arial", 13), width=140, height=40,
                      fg_color="#1a1a1a", hover_color="#2a2a2a", text_color="#888888",
                      command=modal.destroy
                      ).pack(side="left", padx=(0, 15))

        def confirmar():
            cuenta_label = combo_cuenta.get()
            id_metodo = _cuentas_map.get(cuenta_label)
            if not id_metodo:
                lbl_estado.configure(text="⚠ Seleccione una cuenta válida.", text_color="#FFD700")
                return
            try:
                pagar_empleado(emp['idEmpleado'], id_metodo, total, self.controller.rol)
                lbl_estado.configure(text="✔ Pago registrado correctamente.", text_color="#1DB954")
                modal.after(1200, modal.destroy)
                modal.after(1400, self.cargar)
                # Refresh cuentas if loaded
                if hasattr(self.controller, '_tab_cuentas'):
                    modal.after(1400, self.controller._tab_cuentas.cargar)
            except Exception as e:
                lbl_estado.configure(text=f"Error: {e}", text_color="#ff4d4d")

        ctk.CTkButton(btn_row, text="✅  Confirmar Pago",
                      font=("Arial", 13, "bold"), width=180, height=40,
                      fg_color="#1DB954", hover_color="#179643", text_color="#000000",
                      command=confirmar
                      ).pack(side="left")

    # ── Navigation helpers ─────────────────────────────────────────────────────

    def _abrir_registrar(self):
        from gui.nuevo_empleado import NuevoEmpleadoWindow
        NuevoEmpleadoWindow(self.controller, rol=self.controller.rol, on_success=self.cargar).focus()

    def _abrir_editar(self, emp):
        from gui.nuevo_empleado import NuevoEmpleadoWindow
        NuevoEmpleadoWindow(self.controller, empleado_datos=emp, rol=self.controller.rol, on_success=self.cargar).focus()
