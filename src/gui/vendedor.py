"""
vendedor.py — VendedorWindow controller.

This file is now a thin shell: it builds the sidebar, creates placeholder
frames for each tab, and delegates ALL tab logic to the modular classes
in src/gui/tabs/.

Performance: tabs are built LAZILY (only when first selected). This means
no DB queries run at startup for tabs the user hasn't visited yet.
"""
import threading
import customtkinter as ctk
import os
from PIL import Image

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

        # Shared data caches — populated lazily by each tab when first visited.
        # No DB queries at startup; tabs fill these when they first load.
        self.todos_clientes = []
        self.todos_productos = []

        self.title("Sistema de Ventas")
        self.geometry("1000x700")
        self.resizable(True, True)
        self.configure(fg_color="#050505")

        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        icon_path = os.path.join(base_dir, "assets", "logo.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ── Sidebar ────────────────────────────────────────────────────────────
        self._build_sidebar(nombre_vendedor)

        # ── Nav items ──────────────────────────────────────────────────────────
        nav_items = ["Productos", "Ventas", "Cuentas", "Clientes", "Proveedores", "Envíos"]
        if self.rol == 1:
            nav_items += ["Empleados", "Balance"]

        # Mapping: tab name → tab class
        self._tab_classes = {
            "Productos":   ProductosTab,
            "Ventas":      VentasTab,
            "Cuentas":     CuentasTab,
            "Clientes":    ClientesTab,
            "Proveedores": ProveedoresTab,
            "Envíos":      EnviosTab,
            "Empleados":   EmpleadosTab,
            "Balance":     BalanceTab,
        }

        # Create placeholder frames for ALL tabs (so grid layout is ready),
        # but do NOT instantiate tab classes yet (lazy).
        self.frames = {}
        self._tab_refs = {}      # tab name → tab instance (built lazily)
        self._built_tabs = set() # track which tabs have been instantiated

        for item in nav_items:
            frame = ctk.CTkFrame(self, corner_radius=15, fg_color="#121212")
            self.frames[item] = frame

            # Title + separator go into the frame now so they're always visible
            ctk.CTkLabel(frame, text=item, font=("Arial", 32, "bold"),
                         text_color="#ffffff").pack(anchor="w", padx=40, pady=(40, 10))
            ctk.CTkFrame(frame, height=2, fg_color="#1DB954"
                         ).pack(fill="x", padx=40, pady=(0, 30))

        # Expose tab refs (populated on first visit)
        self._tab_productos   = None
        self._tab_ventas      = None
        self._tab_cuentas     = None
        self._tab_clientes    = None
        self._tab_proveedores = None
        self._tab_envios      = None
        self._tab_empleados   = None
        self._tab_balance     = None

        self.current_frame = None
        # Navigate to the first tab — this will trigger the lazy build
        self.select_frame("Productos")

    # ── Sidebar builder ────────────────────────────────────────────────────────

    def _build_sidebar(self, nombre_vendedor):
        sb = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#0a0a0a")
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_rowconfigure(10, weight=1)

        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        ruta_logo = os.path.join(base_dir, "assets", "logo.jpeg")
        if not os.path.exists(ruta_logo):
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
        """Instantiate the tab class for *name* and wire up the named attribute."""
        cls = self._tab_classes.get(name)
        if cls is None:
            return None
        instance = cls(frame, self)
        self._tab_refs[name] = instance

        # Update named shortcuts
        attr_map = {
            "Productos":   "_tab_productos",
            "Ventas":      "_tab_ventas",
            "Cuentas":     "_tab_cuentas",
            "Clientes":    "_tab_clientes",
            "Proveedores": "_tab_proveedores",
            "Envíos":      "_tab_envios",
            "Empleados":   "_tab_empleados",
            "Balance":     "_tab_balance",
        }
        if name in attr_map:
            setattr(self, attr_map[name], instance)

        self._built_tabs.add(name)
        return instance

    # ── Navigation ─────────────────────────────────────────────────────────────

    def select_frame(self, name):
        # Update button styles
        for btn_name, btn in self.nav_buttons.items():
            if btn_name == name:
                btn.configure(fg_color="#1DB954", text_color="#000000",
                              font=("Arial", 15, "bold"))
            else:
                btn.configure(fg_color="transparent", text_color="#888888",
                              font=("Arial", 15))

        # Hide the current frame
        if self.current_frame is not None:
            self.frames[self.current_frame].grid_forget()

        # LAZY BUILD: only instantiate the tab class on first visit.
        # The tab's __init__ is responsible for triggering its own async cargar().
        if name not in self._built_tabs:
            self._build_tab(name, self.frames[name])

        # Show the selected frame
        self.frames[name].grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.current_frame = name

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

    def actualizar_balance_cuentas(self):
        if self._tab_balance:
            self._tab_balance.actualizar_cuentas()

    def actualizar_balance_tab(self):
        if self._tab_balance:
            self._tab_balance.cargar()

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
