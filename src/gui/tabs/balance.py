import threading
from datetime import datetime
import customtkinter as ctk
from database.connection import (
    obtener_cuentas_por_cobrar, obtener_resumen_financiero_7dias,
    obtener_saldos_cuentas, obtener_gastos, insertar_gasto
)


class BalanceTab:
    """Manager-only Balance tab: Cuentas por Pagar · Estadísticas 7 días · Gastos."""

    def __init__(self, parent_frame, controller):
        self.controller = controller

        self.tv = ctk.CTkTabview(
            parent_frame,
            fg_color="#121212",
            segmented_button_fg_color="#0a0a0a",
            segmented_button_selected_color="#1DB954",
            segmented_button_selected_hover_color="#179643",
            segmented_button_unselected_color="#1a1a1a",
            segmented_button_unselected_hover_color="#2b2b2b",
            text_color="#ffffff"
        )
        self.tv.pack(fill="both", expand=True, padx=40, pady=(0, 20))

        self._setup_cuentas(self.tv.add("Cuentas por pagar"))
        self._setup_stats(self.tv.add("Balance productos"))
        self._setup_gastos(self.tv.add("Gastos"))

    # ── Public API ─────────────────────────────────────────────────────────────

    def cargar(self):
        """Public method to refresh all balance tabs."""
        self._cargar_cuentas()
        self._cargar_stats()
        self._cargar_historial()

    def on_show(self):
        self._scroll_cuentas.update_idletasks()
        self._scroll_stats.update_idletasks()
        self._scroll_gastos.update_idletasks()

    # ═══════════════════════════════════════════════════════════════════════════
    # 1. CUENTAS POR PAGAR
    # ═══════════════════════════════════════════════════════════════════════════

    def _setup_cuentas(self, parent):
        top = ctk.CTkFrame(parent, fg_color="transparent")
        top.pack(fill="x", pady=(10, 15))

        ctk.CTkLabel(top, text="Cuentas por Pagar de clientes",
                     font=("Arial", 16, "bold"), text_color="#aaaaaa"
                     ).pack(side="left")
        ctk.CTkButton(top, text="↻ Actualizar",
                      font=("Arial", 12, "bold"),
                      fg_color="#1e1e1e", hover_color="#333333", text_color="#1DB954",
                      width=100, command=self._cargar_cuentas
                      ).pack(side="right")

        self._scroll_cuentas = ctk.CTkScrollableFrame(parent, fg_color="#0a0a0a", corner_radius=10)
        self._scroll_cuentas.pack(fill="both", expand=True, pady=(0, 10))

        self._cargar_cuentas()

    def _cargar_cuentas(self):
        for w in self._scroll_cuentas.winfo_children():
            w.destroy()

        ctk.CTkLabel(
            self._scroll_cuentas, text="Cargando cuentas por cobrar...",
            text_color="#888888", font=("Arial", 14)
        ).pack(pady=30)

        def _fetch():
            try:
                cuentas = obtener_cuentas_por_cobrar(self.controller.rol)
                self._scroll_cuentas.after(0, lambda c=cuentas: self._render_cuentas(c))
            except Exception as e:
                self._scroll_cuentas.after(0, lambda err=str(e): self._render_cuentas_error(err))

        threading.Thread(target=_fetch, daemon=True).start()

    def _render_cuentas_error(self, err):
        for w in self._scroll_cuentas.winfo_children():
            w.destroy()
        ctk.CTkLabel(self._scroll_cuentas, text=f"Error cargando cuentas:\n{err}",
                     text_color="#ff4d4d").pack(pady=20)

    def _render_cuentas(self, cuentas):
        for w in self._scroll_cuentas.winfo_children():
            w.destroy()

        if not cuentas:
            ctk.CTkLabel(self._scroll_cuentas, text="No hay deudas de clientes.",
                         text_color="#888888").pack(pady=30)
            return

        table = ctk.CTkFrame(self._scroll_cuentas, fg_color="transparent")
        table.pack(fill="x", expand=True)
        for i, w in enumerate([1, 2, 2, 1, 1, 1]):
            table.grid_columnconfigure(i, weight=w)

        hc = "#1e1e1e"
        for ci, col in enumerate(["Venta ID", "Cliente", "Fecha Venta", "Total Venta", "Abonado", "Saldo Pendiente"]):
            ctk.CTkLabel(table, text=col,
                         font=("Arial", 12, "bold"), text_color="#1DB954",
                         fg_color=hc, anchor="w", padx=10, pady=8
                         ).grid(row=0, column=ci, sticky="nsew")

        for idx, c in enumerate(cuentas):
            ri = idx + 1
            bg = "#161616" if idx % 2 == 0 else "#0d0d0d"

            fecha = c.get('fecha_venta', '')
            if hasattr(fecha, 'strftime'):
                fecha = fecha.strftime('%d/%m/%Y %H:%M')

            total = float(c.get('total_productos', 0) or 0)
            abonado = float(c.get('total_abonado', 0) or 0)
            saldo = float(c.get('saldo_pendiente', 0) or 0)

            for ci2, (text, color) in enumerate([
                (f"#{c['idVenta']}", "#ffffff"),
                (c['cliente'], "#ffffff"),
                (str(fecha), "#cccccc"),
            ]):
                ctk.CTkLabel(table, text=text, text_color=color,
                             fg_color=bg, anchor="w", padx=10, pady=8
                             ).grid(row=ri, column=ci2, sticky="nsew")

            ctk.CTkLabel(table, text=f"${total:,.2f}", text_color="#1DB954",
                         font=("Arial", 13, "bold"), fg_color=bg, anchor="w", padx=10, pady=8
                         ).grid(row=ri, column=3, sticky="nsew")
            ctk.CTkLabel(table, text=f"${abonado:,.2f}", text_color="#FF8C00",
                         font=("Arial", 13, "bold"), fg_color=bg, anchor="w", padx=10, pady=8
                         ).grid(row=ri, column=4, sticky="nsew")
            ctk.CTkLabel(table, text=f"${saldo:,.2f}", text_color="#ff4d4d",
                         font=("Arial", 13, "bold"), fg_color=bg, anchor="w", padx=10, pady=8
                         ).grid(row=ri, column=5, sticky="nsew")

    # ═══════════════════════════════════════════════════════════════════════════
    # 2. ESTADÍSTICAS 7 DÍAS
    # ═══════════════════════════════════════════════════════════════════════════

    def _setup_stats(self, parent):
        top = ctk.CTkFrame(parent, fg_color="transparent")
        top.pack(fill="x", pady=(10, 15))

        ctk.CTkLabel(top, text="Resumen Financiero — Últimos 7 Días",
                     font=("Arial", 16, "bold"), text_color="#aaaaaa"
                     ).pack(side="left")
        ctk.CTkButton(top, text="↻ Actualizar",
                      font=("Arial", 12, "bold"),
                      fg_color="#1e1e1e", hover_color="#333333", text_color="#1DB954",
                      width=100, command=self._cargar_stats
                      ).pack(side="right")

        self._scroll_stats = ctk.CTkScrollableFrame(parent, fg_color="#0a0a0a", corner_radius=10)
        self._scroll_stats.pack(fill="both", expand=True, pady=(0, 10))

        self._cargar_stats()

    def _cargar_stats(self):
        for w in self._scroll_stats.winfo_children():
            w.destroy()

        ctk.CTkLabel(
            self._scroll_stats, text="Cargando resumen financiero...",
            text_color="#888888", font=("Arial", 14)
        ).pack(pady=30)

        def _fetch():
            try:
                datos = obtener_resumen_financiero_7dias(self.controller.rol)
                self._scroll_stats.after(0, lambda d=datos: self._render_stats(d))
            except Exception as e:
                self._scroll_stats.after(0, lambda err=str(e): self._render_stats_error(err))

        threading.Thread(target=_fetch, daemon=True).start()

    def _render_stats_error(self, err):
        for w in self._scroll_stats.winfo_children():
            w.destroy()
        ctk.CTkLabel(self._scroll_stats, text=f"Error:\n{err}", text_color="#ff4d4d").pack(pady=20)

    def _render_stats(self, datos):
        for w in self._scroll_stats.winfo_children():
            w.destroy()

        if not datos:
            ctk.CTkLabel(self._scroll_stats, text="No hay datos financieros disponibles.",
                         text_color="#888888").pack(pady=30)
            return

        table = ctk.CTkFrame(self._scroll_stats, fg_color="transparent")
        table.pack(fill="x", expand=True)

        col_headers = ["Fecha", "Saldo Inicial", "Gastos", "Costos", "CxC", "Abono", "Ventas", "Total"]
        col_weights = [2, 2, 1, 1, 1, 1, 2, 2]
        for i, w in enumerate(col_weights):
            table.grid_columnconfigure(i, weight=w)

        for i, hdr in enumerate(col_headers):
            ctk.CTkLabel(table, text=hdr,
                         font=("Arial", 12, "bold"), text_color="#1DB954",
                         fg_color="#1e1e1e", anchor="w", padx=8, pady=10
                         ).grid(row=0, column=i, sticky="nsew")

        dias_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        sum_g = sum_c = sum_cxc = sum_a = sum_v = 0.0

        for idx, dia in enumerate(datos):
            ri = idx + 1
            bg = "#121212" if idx % 2 == 0 else "#0a0a0a"

            try:
                fo = datetime.strptime(dia['fecha'], "%Y-%m-%d")
                fecha_display = f"{dias_semana[fo.weekday()]} {fo.strftime('%d/%m')}"
            except Exception:
                fecha_display = dia['fecha']

            si = float(dia['saldo_inicial'])
            g = float(dia['gastos'])
            c = float(dia['costos'])
            cxc = float(dia['cxc'])
            a = float(dia['abonos'])
            v = float(dia['ventas_total'])
            se = float(dia['saldo_esperado'])
            sum_g += g; sum_c += c; sum_cxc += cxc; sum_a += a; sum_v += v

            cells = [
                (fecha_display, "#ffffff", "bold"),
                (f"${si:,.0f}", "#cccccc", "normal"),
                (f"-${g:,.0f}" if g > 0 else "$0", "#ff4d4d" if g > 0 else "#555555", "bold"),
                (f"-${c:,.0f}" if c > 0 else "$0", "#FF8C00" if c > 0 else "#555555", "bold"),
                (f"${cxc:,.0f}" if cxc > 0 else "$0", "#FFD700" if cxc > 0 else "#555555", "normal"),
                (f"+${a:,.0f}" if a > 0 else "$0", "#1DB954" if a > 0 else "#555555", "bold"),
                (f"${v:,.0f}" if v > 0 else "$0", "#ffffff" if v > 0 else "#555555", "bold"),
                (f"${se:,.0f}", "#1DB954" if se >= 0 else "#ff4d4d", "bold"),
            ]
            for ci, (text, color, weight) in enumerate(cells):
                ctk.CTkLabel(table, text=text, text_color=color,
                             font=("Arial", 12, weight), fg_color=bg, anchor="w", padx=8, pady=8
                             ).grid(row=ri, column=ci, sticky="nsew")

        # Totals row
        total_row = len(datos) + 1
        tb = "#1a2a1a"
        total_cells = [
            ("TOTALES", "#1DB954", "bold"),
            (f"${float(datos[0]['saldo_inicial']):,.0f}", "#aaaaaa", "bold"),
            (f"-${sum_g:,.0f}", "#ff4d4d", "bold"),
            (f"-${sum_c:,.0f}", "#FF8C00", "bold"),
            (f"${sum_cxc:,.0f}", "#FFD700", "bold"),
            (f"+${sum_a:,.0f}", "#1DB954", "bold"),
            (f"${sum_v:,.0f}", "#ffffff", "bold"),
            (f"${float(datos[-1]['saldo_esperado']):,.0f}",
             "#1DB954" if float(datos[-1]['saldo_esperado']) >= 0 else "#ff4d4d", "bold"),
        ]
        for ci, (text, color, weight) in enumerate(total_cells):
            ctk.CTkLabel(table, text=text, text_color=color,
                         font=("Arial", 12, weight), fg_color=tb, anchor="w", padx=8, pady=10
                         ).grid(row=total_row, column=ci, sticky="nsew")

    # ═══════════════════════════════════════════════════════════════════════════
    # 3. GASTOS
    # ═══════════════════════════════════════════════════════════════════════════

    def _setup_gastos(self, parent):
        parent.grid_columnconfigure(0, weight=2)
        parent.grid_columnconfigure(1, weight=3)
        parent.grid_rowconfigure(0, weight=1)

        # Left: form
        form = ctk.CTkFrame(parent, fg_color="#0a0a0a", corner_radius=10)
        form.grid(row=0, column=0, padx=(10, 10), pady=10, sticky="nsew")

        ctk.CTkLabel(form, text="Registrar Nuevo Gasto",
                     font=("Arial", 16, "bold"), text_color="#1DB954"
                     ).pack(pady=(15, 15))

        for label, attr, placeholder in [
            ("Descripción del Gasto *", "_entry_desc", "Ej: Pago de servicios públicos"),
            ("Monto ($) *", "_entry_monto", "Ej: 450.00"),
        ]:
            ctk.CTkLabel(form, text=label,
                         font=("Arial", 12, "bold"), text_color="#aaaaaa"
                         ).pack(anchor="w", padx=20, pady=(5, 2))
            e = ctk.CTkEntry(form, placeholder_text=placeholder, height=38,
                             corner_radius=8, fg_color="#1e1e1e",
                             border_color="#2a2a2a", text_color="#ffffff")
            e.pack(fill="x", padx=20, pady=(0, 10))
            setattr(self, attr, e)

        ctk.CTkLabel(form, text="Cuenta a debitar *",
                     font=("Arial", 12, "bold"), text_color="#aaaaaa"
                     ).pack(anchor="w", padx=20, pady=(5, 2))

        try:
            cuentas = obtener_saldos_cuentas(self.controller.rol)
            self._cuentas_gastos = {
                f"{c['tipo_cuenta']} ({c['num_cuenta']})": c['idMetodo_de_pago']
                for c in cuentas
            }
            opciones = ["Seleccione cuenta..."] + list(self._cuentas_gastos.keys())
        except Exception:
            opciones = ["Seleccione cuenta..."]
            self._cuentas_gastos = {}

        self._combo_cuenta = ctk.CTkComboBox(
            form, values=opciones, height=38, corner_radius=8,
            fg_color="#1e1e1e", border_color="#2a2a2a", text_color="#ffffff"
        )
        self._combo_cuenta.pack(fill="x", padx=20, pady=(0, 15))
        self._combo_cuenta.set("Seleccione cuenta...")

        self._lbl_status = ctk.CTkLabel(form, text="",
                                        font=("Arial", 12), text_color="#ff4d4d", wraplength=220)
        self._lbl_status.pack(pady=5)

        ctk.CTkButton(form, text="Guardar Gasto",
                      font=("Arial", 13, "bold"),
                      fg_color="#1DB954", hover_color="#179643", text_color="#000000",
                      height=40, command=self._guardar_gasto
                      ).pack(fill="x", padx=20, pady=(5, 20))

        # Right: history
        hist = ctk.CTkFrame(parent, fg_color="#0a0a0a", corner_radius=10)
        hist.grid(row=0, column=1, padx=(10, 10), pady=10, sticky="nsew")

        top_hist = ctk.CTkFrame(hist, fg_color="transparent")
        top_hist.pack(fill="x", padx=15, pady=(15, 10))
        ctk.CTkLabel(top_hist, text="Historial de Gastos",
                     font=("Arial", 16, "bold"), text_color="#aaaaaa"
                     ).pack(side="left")
        ctk.CTkButton(top_hist, text="↻",
                      font=("Arial", 12, "bold"),
                      fg_color="#1e1e1e", hover_color="#333333", text_color="#1DB954",
                      width=35, height=30, command=self._cargar_historial
                      ).pack(side="right")

        self._scroll_gastos = ctk.CTkScrollableFrame(hist, fg_color="transparent")
        self._scroll_gastos.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self._cargar_historial()

    def _guardar_gasto(self):
        self._lbl_status.configure(text="", text_color="#ff4d4d")
        desc = self._entry_desc.get().strip()
        monto_str = self._entry_monto.get().strip()
        cuenta_sel = self._combo_cuenta.get()

        if not desc or not monto_str or cuenta_sel == "Seleccione cuenta...":
            self._lbl_status.configure(text="Por favor complete todos los campos.")
            return
        try:
            monto = float(monto_str)
            if monto <= 0:
                raise ValueError()
        except ValueError:
            self._lbl_status.configure(text="El monto debe ser un número positivo.")
            return

        id_metodo = self._cuentas_gastos.get(cuenta_sel)
        if not id_metodo:
            self._lbl_status.configure(text="Cuenta seleccionada inválida.")
            return

        try:
            insertar_gasto(id_metodo_pago=id_metodo, descripcion=desc,
                           monto=monto, rol=self.controller.rol)
            self._lbl_status.configure(text="¡Gasto registrado con éxito!", text_color="#1DB954")
            self._entry_desc.delete(0, 'end')
            self._entry_monto.delete(0, 'end')
            self._combo_cuenta.set("Seleccione cuenta...")
            self._cargar_historial()
        except Exception as e:
            self._lbl_status.configure(text=str(e), text_color="#ff4d4d")

    def _cargar_historial(self):
        for w in self._scroll_gastos.winfo_children():
            w.destroy()

        ctk.CTkLabel(
            self._scroll_gastos, text="Cargando historial de gastos...",
            text_color="#888888", font=("Arial", 12)
        ).pack(pady=20)

        def _fetch():
            try:
                gastos = obtener_gastos(self.controller.rol)
                self._scroll_gastos.after(0, lambda g=gastos: self._render_historial(g))
            except Exception as e:
                self._scroll_gastos.after(0, lambda err=str(e): self._render_historial_error(err))

        threading.Thread(target=_fetch, daemon=True).start()

    def _render_historial_error(self, err):
        for w in self._scroll_gastos.winfo_children():
            w.destroy()
        ctk.CTkLabel(self._scroll_gastos, text=f"Error cargando gastos:\n{err}",
                     text_color="#ff4d4d").pack(pady=20)

    def _render_historial(self, gastos):
        for w in self._scroll_gastos.winfo_children():
            w.destroy()

        if not gastos:
            ctk.CTkLabel(self._scroll_gastos, text="No hay gastos registrados.",
                         text_color="#888888").pack(pady=20)
            return

        hdr = ctk.CTkFrame(self._scroll_gastos, fg_color="#1e1e1e", corner_radius=5)
        hdr.pack(fill="x", pady=(0, 6))
        pesos = [2, 1, 1, 1]
        cols = ["Descripción", "Cuenta", "Monto", "Fecha"]
        for i, (col, w) in enumerate(zip(cols, pesos)):
            hdr.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(hdr, text=col, font=("Arial", 11, "bold"), text_color="#1DB954"
                         ).grid(row=0, column=i, padx=5, pady=6, sticky="w")

        for idx, g in enumerate(gastos):
            bg = "#161616" if idx % 2 == 0 else "#0d0d0d"
            row = ctk.CTkFrame(self._scroll_gastos, fg_color=bg, corner_radius=5)
            row.pack(fill="x", pady=2)
            for i, w in enumerate(pesos):
                row.grid_columnconfigure(i, weight=w)

            fecha = g.get('fecha', '')
            if hasattr(fecha, 'strftime'):
                fecha = fecha.strftime('%d/%m/%Y')
            monto = float(g.get('monto', 0) or 0)
            desc = g['descripcion']
            if len(desc) > 20:
                desc = desc[:17] + "..."

            ctk.CTkLabel(row, text=desc, font=("Arial", 12), text_color="#ffffff"
                         ).grid(row=0, column=0, padx=5, pady=6, sticky="w")
            ctk.CTkLabel(row, text=g['cuenta'], font=("Arial", 11), text_color="#cccccc"
                         ).grid(row=0, column=1, padx=5, pady=6, sticky="w")
            ctk.CTkLabel(row, text=f"${monto:,.2f}",
                         font=("Arial", 12, "bold"), text_color="#ff4d4d"
                         ).grid(row=0, column=2, padx=5, pady=6, sticky="w")
            ctk.CTkLabel(row, text=str(fecha), font=("Arial", 11), text_color="#888888"
                         ).grid(row=0, column=3, padx=5, pady=6, sticky="w")

    # ── Public refresh helpers ─────────────────────────────────────────────────

    def actualizar_cuentas(self):
        self._cargar_cuentas()

    def actualizar_stats(self):
        self._cargar_stats()
