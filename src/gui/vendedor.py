"""
vendedor.py — VendedorWindow controller.

This file is now a thin shell: it builds the sidebar, creates content frames,
and delegates ALL tab logic to the modular classes in src/gui/tabs/.
"""
import customtkinter as ctk
import os
from PIL import Image
from database.connection import obtener_clientes, obtener_productos

# ── Tab imports ────────────────────────────────────────────────────────────────
from gui.tabs.productos import ProductosTab
from gui.tabs.ventas import VentasTab
from gui.tabs.cuentas import CuentasTab
from gui.tabs.clientes import ClientesTab
from gui.tabs.proveedores import ProveedoresTab
from gui.tabs.envios import EnviosTab
from gui.tabs.empleados import EmpleadosTab
from gui.tabs.balance import BalanceTab


class VendedorWindow(ctk.CTkToplevel):
    def __init__(self, master=None, nombre_vendedor="Usuario",
                 rol=0, id_empleado=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.rol = rol
        self.id_empleado = id_empleado

        # Shared data caches (used by VentasTab / modals)
        self.todos_clientes = []
        self.todos_productos = []
        try:
            self.todos_clientes = obtener_clientes(self.rol)
        except Exception as e:
            print(f"Error cargando clientes iniciales: {e}")
        try:
            self.todos_productos = obtener_productos(self.rol)
        except Exception as e:
            print(f"Error cargando productos iniciales: {e}")

        self.title("Sistema de Ventas")
        self.geometry("1000x700")
        self.resizable(True, True)
        self.configure(fg_color="#050505")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ── Sidebar ────────────────────────────────────────────────────────────
        self._build_sidebar(nombre_vendedor)

        # ── Content frames ─────────────────────────────────────────────────────
        nav_items = ["Productos", "Ventas", "Cuentas", "Clientes", "Proveedores", "Envíos"]
        if self.rol == 1:
            nav_items += ["Empleados", "Balance"]

        self.frames = {}
        self._tab_refs = {}   # stores tab class instances for cross-tab refreshing

        for item in nav_items:
            frame = ctk.CTkFrame(self, corner_radius=15, fg_color="#121212")
            self.frames[item] = frame

            ctk.CTkLabel(frame, text=item, font=("Arial", 32, "bold"),
                         text_color="#ffffff").pack(anchor="w", padx=40, pady=(40, 10))
            ctk.CTkFrame(frame, height=2, fg_color="#1DB954"
                         ).pack(fill="x", padx=40, pady=(0, 30))

            tab_instance = self._build_tab(item, frame)
            if tab_instance:
                self._tab_refs[item] = tab_instance

        # Expose tabs via named attributes for cross-tab callbacks
        self._tab_productos   = self._tab_refs.get("Productos")
        self._tab_ventas      = self._tab_refs.get("Ventas")
        self._tab_cuentas     = self._tab_refs.get("Cuentas")
        self._tab_clientes    = self._tab_refs.get("Clientes")
        self._tab_proveedores = self._tab_refs.get("Proveedores")
        self._tab_envios      = self._tab_refs.get("Envíos")
        self._tab_empleados   = self._tab_refs.get("Empleados")
        self._tab_balance     = self._tab_refs.get("Balance")

        self.current_frame = None
        self.select_frame("Productos")

    # ── Sidebar builder ────────────────────────────────────────────────────────

    def _build_sidebar(self, nombre_vendedor):
        sb = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#0a0a0a")
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_rowconfigure(10, weight=1)

        ruta_logo = os.path.join("assets", "logo.jpeg")
        try:
            img = Image.open(ruta_logo)
            if img.mode != "RGB":
                img = img.convert("RGB")
            self._logo_img = ctk.CTkImage(light_image=img, dark_image=img, size=(100, 100))
            logo_lbl = ctk.CTkLabel(sb, text="", image=self._logo_img)
        except Exception:
            logo_lbl = ctk.CTkLabel(sb, text="[ LOGO ]", width=100, height=100,
                                    corner_radius=15, fg_color="#1e1e1e",
                                    text_color="#ff4d4d", font=("Arial", 11, "bold"))
        logo_lbl.grid(row=0, column=0, padx=20, pady=(30, 10))

        ctk.CTkLabel(sb, text="Nice People", font=("Arial", 20, "bold"),
                     text_color="#ffffff").grid(row=1, column=0, padx=20)

        tipo_rol = "Gerente" if self.rol == 1 else "Empleado"
        ctk.CTkLabel(sb, text=f"{tipo_rol}: {nombre_vendedor}",
                     font=("Arial", 14), text_color="#1DB954"
                     ).grid(row=2, column=0, padx=20, pady=(0, 30))

        self.nav_buttons = {}
        nav_items = ["Productos", "Ventas", "Cuentas", "Clientes", "Proveedores", "Envíos"]
        if self.rol == 1:
            nav_items += ["Empleados", "Balance"]

        for i, item in enumerate(nav_items, start=3):
            btn = ctk.CTkButton(sb, text=f"  {item}",
                                fg_color="transparent", text_color="#888888",
                                hover_color="#121212", anchor="w",
                                height=40, font=("Arial", 15),
                                command=lambda name=item: self.select_frame(name))
            btn.grid(row=i, column=0, padx=15, pady=5, sticky="ew")
            self.nav_buttons[item] = btn

        ctk.CTkButton(sb, text="Cerrar Sesión",
                      fg_color="#1a0505", hover_color="#330a0a",
                      text_color="#ff4d4d", height=40,
                      font=("Arial", 14, "bold"), command=self.logout
                      ).grid(row=11, column=0, padx=20, pady=(10, 30), sticky="ew")

    # ── Tab factory ────────────────────────────────────────────────────────────

    def _build_tab(self, name, frame):
        if name == "Productos":
            return ProductosTab(frame, self)
        elif name == "Ventas":
            return VentasTab(frame, self)
        elif name == "Cuentas":
            return CuentasTab(frame, self)
        elif name == "Clientes":
            return ClientesTab(frame, self)
        elif name == "Proveedores":
            return ProveedoresTab(frame, self)
        elif name == "Envíos":
            return EnviosTab(frame, self)
        elif name == "Empleados":
            return EmpleadosTab(frame, self)
        elif name == "Balance":
            return BalanceTab(frame, self)
        return None

    # ── Navigation ─────────────────────────────────────────────────────────────

    def select_frame(self, name):
        for btn_name, btn in self.nav_buttons.items():
            if btn_name == name:
                btn.configure(fg_color="#1DB954", text_color="#000000",
                              font=("Arial", 15, "bold"))
            else:
                btn.configure(fg_color="transparent", text_color="#888888",
                              font=("Arial", 15))

        if self.current_frame is not None:
            self.frames[self.current_frame].grid_forget()

        self.frames[name].grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.current_frame = name

        # Refresh data when switching to a tab
        tab = self._tab_refs.get(name)
        if hasattr(tab, 'cargar'):
            tab.cargar()
        # Also keep ventas combos fresh after client/product changes
        if name == "Ventas" and self._tab_ventas:
            self._tab_ventas.refresh_clientes()
            self._tab_ventas.refresh_productos()

    # ── Compatibility helpers (called by sub-windows like NuevoClienteWindow) ──

    def actualizar_lista_clientes(self):
        if self._tab_clientes:
            self._tab_clientes.cargar()
        if self._tab_ventas:
            self._tab_ventas.refresh_clientes()

    def actualizar_lista_proveedores(self):
        if self._tab_proveedores:
            self._tab_proveedores.cargar()

    def actualizar_lista_envios(self):
        if self._tab_envios:
            self._tab_envios.cargar()

    def actualizar_productos_tab(self):
        if self._tab_productos:
            self._tab_productos.cargar()
        if self._tab_ventas:
            self._tab_ventas.refresh_productos()

    def actualizar_cuentas_tab(self):
        if self._tab_cuentas:
            self._tab_cuentas.cargar()

    def actualizar_combobox_productos(self):
        if self._tab_ventas:
            self._tab_ventas.refresh_productos()

    def cargar_lista_empleados(self):
        if self._tab_empleados:
            self._tab_empleados.cargar()

    def _abrir_actualizar_precio_producto(self, prod):
        from gui.actualizar_precio_producto import ActualizarPrecioProductoWindow
        ActualizarPrecioProductoWindow(self, producto_datos=prod).focus()

    # ── Logout ─────────────────────────────────────────────────────────────────

    def logout(self):
        if hasattr(self.master, 'user_entry'):
            self.master.user_entry.delete(0, 'end')
            self.master.password_entry.delete(0, 'end')
            self.master.error_label.configure(text="")
        self.master.deiconify()
        self.destroy()
