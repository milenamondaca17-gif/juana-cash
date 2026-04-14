import os
import requests
from PyQt6.QtWidgets import (QMainWindow, QStackedWidget, QWidget, QHBoxLayout,
                              QVBoxLayout, QPushButton, QLabel, QMessageBox,
                              QDialog, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from ui.pantallas.login import LoginScreen
from ui.pantallas.turno import TurnoScreen
from ui.pantallas.ventas import VentasScreen
from ui.pantallas.productos import ProductosScreen
from ui.pantallas.reportes import ReportesScreen
from ui.pantallas.clientes import ClientesScreen
from ui.pantallas.caja import CajaScreen
from ui.pantallas.sesiones import SesionesScreen
from ui.pantallas.usuarios import UsuariosScreen
from ui.pantallas.dashboard import DashboardScreen
from ui.pantallas.stock_avanzado import StockAvanzadoScreen

API_URL = "http://127.0.0.1:8000"


class AlertaCumpleanosDialog(QDialog):
    def __init__(self, parent=None, clientes=None):
        super().__init__(parent)
        self.setWindowTitle("🎂 Cumpleaños")
        self.setMinimumWidth(400)
        self.setStyleSheet("background-color: #1a1a2e; color: white;")
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        titulo = QLabel("🎂 Clientes con cumpleaños")
        titulo.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        titulo.setStyleSheet("color: #f39c12;")
        layout.addWidget(titulo)

        hoy = [c for c in clientes if c.get("tipo") == "hoy"]
        proximos = [c for c in clientes if c.get("tipo") == "proximo"]

        if hoy:
            lbl = QLabel("🎉 ¡HOY es el cumpleaños de:")
            lbl.setStyleSheet("color: #27ae60; font-size: 13px; font-weight: bold;")
            layout.addWidget(lbl)
            for c in hoy:
                fila = QLabel(f"   🎂 {c['nombre']}" + (f"  — {c['telefono']}" if c.get("telefono") else ""))
                fila.setStyleSheet("color: white; font-size: 13px; padding: 2px 0;")
                layout.addWidget(fila)

        if proximos:
            lbl2 = QLabel("📅 Próximos cumpleaños (7 días):")
            lbl2.setStyleSheet("color: #3498db; font-size: 12px; font-weight: bold; margin-top: 8px;")
            layout.addWidget(lbl2)
            for c in proximos:
                fila = QLabel(f"   📆 {c['nombre']}  —  {c['dia']:02d}/{c['mes']:02d}")
                fila.setStyleSheet("color: #a0a0b0; font-size: 12px; padding: 2px 0;")
                layout.addWidget(fila)

        btn = QPushButton("OK")
        btn.setFixedHeight(40)
        btn.setStyleSheet("QPushButton { background: #f39c12; color: white; border-radius: 8px; font-size: 14px; font-weight: bold; }")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)


class AlertaDeudoresDialog(QDialog):
    def __init__(self, parent=None, deudores=None):
        super().__init__(parent)
        self.setWindowTitle("💸 Deudores")
        self.setMinimumWidth(520)
        self.setMinimumHeight(360)
        self.setStyleSheet("background-color: #1a1a2e; color: white;")
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        titulo = QLabel(f"💸 {len(deudores)} clientes con deuda pendiente")
        titulo.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        titulo.setStyleSheet("color: #e94560;")
        layout.addWidget(titulo)

        total_deuda = sum(float(d.get("deuda_actual", 0)) for d in deudores)
        lbl_total = QLabel(f"Total adeudado: ${total_deuda:,.2f}")
        lbl_total.setStyleSheet("color: #f39c12; font-size: 14px; font-weight: bold;")
        layout.addWidget(lbl_total)

        tabla = QTableWidget()
        tabla.setColumnCount(3)
        tabla.setHorizontalHeaderLabels(["Cliente", "Deuda", "Teléfono"])
        tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        tabla.setColumnWidth(1, 110)
        tabla.setColumnWidth(2, 120)
        tabla.setStyleSheet("""
            QTableWidget { background: #16213e; border: 1px solid #0f3460; border-radius: 8px; gridline-color: #0f3460; }
            QHeaderView::section { background: #0f3460; color: #a0a0b0; padding: 6px; border: none; }
            QTableWidgetItem { color: white; padding: 6px; }
        """)
        tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tabla.setRowCount(len(deudores))

        for i, d in enumerate(deudores):
            tabla.setItem(i, 0, QTableWidgetItem(d["nombre"]))
            item_deuda = QTableWidgetItem(f"${float(d['deuda_actual']):,.2f}")
            item_deuda.setForeground(Qt.GlobalColor.red)
            tabla.setItem(i, 1, item_deuda)
            tabla.setItem(i, 2, QTableWidgetItem(d.get("telefono") or "-"))

        layout.addWidget(tabla)

        btn = QPushButton("Cerrar")
        btn.setFixedHeight(40)
        btn.setStyleSheet("QPushButton { background: #e94560; color: white; border-radius: 8px; font-size: 13px; font-weight: bold; }")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Juana Cash - Sistema POS")
        self.setMinimumSize(1280, 720)
        self.usuario_actual = None
        self.cajero_actual = None

        central = QWidget()
        self.setCentralWidget(central)
        self.main_layout = QHBoxLayout(central)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # ── Sidebar ───────────────────────────────────────────────────────────
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(210)
        self.sidebar.setStyleSheet("background-color: #16213e;")
        self.sidebar.hide()
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        logo = QLabel("💰 Juana Cash")
        logo.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        logo.setStyleSheet("color: #e94560; padding: 20px;")
        sidebar_layout.addWidget(logo)

        self.lbl_cajero_sidebar = QLabel("")
        self.lbl_cajero_sidebar.setStyleSheet("color: #a0a0b0; font-size: 11px; padding: 0 20px 10px 20px;")
        self.lbl_cajero_sidebar.setWordWrap(True)
        sidebar_layout.addWidget(self.lbl_cajero_sidebar)

        self.btns_menu = {}
        self.menus_admin = ["usuarios", "sesiones", "dashboard", "stock"]
        menus = [
            ("🛒  Ventas",       "ventas"),
            ("📦  Productos",    "productos"),
            ("👥  Clientes",     "clientes"),
            ("🧾  Caja",         "caja"),
            ("📊  Reportes",     "reportes"),
            ("📈  Dashboard",    "dashboard"),
            ("📦  Stock",         "stock"),
            ("📋  Sesiones",     "sesiones"),
            ("👤  Usuarios",     "usuarios"),
        ]
        for texto, key in menus:
            btn = QPushButton(texto)
            btn.setFixedHeight(48)
            btn.setStyleSheet("""
                QPushButton { background: transparent; color: #a0a0b0; text-align: left;
                              padding-left: 20px; font-size: 14px; border: none; }
                QPushButton:hover { background: #0f3460; color: white; }
            """)
            btn.clicked.connect(lambda _, k=key: self.cambiar_pantalla(k))
            sidebar_layout.addWidget(btn)
            self.btns_menu[key] = btn

        sidebar_layout.addStretch()
        btn_salir = QPushButton("🚪  Cerrar sesión")
        btn_salir.setFixedHeight(48)
        btn_salir.setStyleSheet("QPushButton { background: transparent; color: #e94560; text-align: left; padding-left: 20px; font-size: 14px; border: none; }")
        btn_salir.clicked.connect(self.on_logout)
        sidebar_layout.addWidget(btn_salir)
        self.main_layout.addWidget(self.sidebar)

        # ── Stack de pantallas ────────────────────────────────────────────────
        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)

        self.login_screen    = LoginScreen(self.on_login_exitoso)
        self.turno_screen    = TurnoScreen(self.on_turno_seleccionado, {})
        self.ventas_screen   = VentasScreen(self.on_logout)
        self.productos_screen = ProductosScreen()
        self.reportes_screen = ReportesScreen()
        self.clientes_screen = ClientesScreen()
        self.caja_screen     = CajaScreen()
        self.sesiones_screen = SesionesScreen()
        self.usuarios_screen = UsuariosScreen()
        self.dashboard_screen = DashboardScreen()
        self.stock_screen = StockAvanzadoScreen()

        for screen in [
            self.login_screen, self.turno_screen, self.ventas_screen,
            self.productos_screen, self.reportes_screen, self.clientes_screen,
            self.caja_screen, self.sesiones_screen, self.usuarios_screen,
            self.dashboard_screen,
            self.stock_screen
        ]:
            self.stack.addWidget(screen)

        self.stack.setCurrentWidget(self.login_screen)

    def cambiar_pantalla(self, key):
        rol = self.cajero_actual.get("rol", "cajero") if self.cajero_actual else "cajero"
        if key in self.menus_admin and rol not in ["admin", "encargado"]:
            QMessageBox.warning(self, "Acceso denegado",
                "Solo admin o encargado pueden acceder a esta sección")
            return
        pantallas = {
            "ventas":    self.ventas_screen,
            "productos": self.productos_screen,
            "reportes":  self.reportes_screen,
            "clientes":  self.clientes_screen,
            "caja":      self.caja_screen,
            "sesiones":  self.sesiones_screen,
            "usuarios":  self.usuarios_screen,
            "dashboard": self.dashboard_screen,
            "stock":     self.stock_screen,
        }
        if key in pantallas:
            acciones = {
                "productos": lambda: self.productos_screen.cargar_productos(),
                "reportes":  lambda: self.reportes_screen.cargar_datos(),
                "clientes":  lambda: self.clientes_screen.cargar_clientes(),
                "caja":      lambda: self.caja_screen.actualizar_ventas(),
                "sesiones":  lambda: self.sesiones_screen.cargar_sesiones(),
                "usuarios":  lambda: self.usuarios_screen.cargar_usuarios(),
            }
            if key in acciones:
                acciones[key]()
            self.stack.setCurrentWidget(pantallas[key])

    def on_login_exitoso(self, usuario):
        self.usuario_actual = usuario
        self.turno_screen = TurnoScreen(self.on_turno_seleccionado, usuario)
        self.stack.addWidget(self.turno_screen)
        self.stack.setCurrentWidget(self.turno_screen)

    def on_turno_seleccionado(self, cajero):
        if cajero is None:
            self.stack.setCurrentWidget(self.login_screen)
            return

        self.cajero_actual = cajero
        nombre = cajero.get("nombre", "Cajero")
        turno  = cajero.get("turno", "")
        rol    = cajero.get("rol", "cajero")

        self.lbl_cajero_sidebar.setText(f"👤 {nombre}\n🎖 {rol}\n🕐 {turno[:5]}")

        for key, btn in self.btns_menu.items():
            if key in self.menus_admin and rol not in ["admin", "encargado"]:
                btn.setStyleSheet("""
                    QPushButton { background: transparent; color: #555; text-align: left;
                                  padding-left: 20px; font-size: 14px; border: none; }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton { background: transparent; color: #a0a0b0; text-align: left;
                                  padding-left: 20px; font-size: 14px; border: none; }
                    QPushButton:hover { background: #0f3460; color: white; }
                """)

        self.ventas_screen.set_usuario(cajero)
        self.caja_screen.set_usuario(cajero)
        self.sidebar.show()
        self.stack.setCurrentWidget(self.ventas_screen)
        self.setWindowTitle(f"Juana Cash — {nombre} | {rol} | {turno[:5]}")

        # Alertas disponibles manualmente desde el menú de clientes

    def verificar_cumpleanos(self):
        try:
            r = requests.get(f"{API_URL}/clientes/cumpleanos", timeout=4)
            if r.status_code == 200:
                data = r.json()
                if data:
                    dialog = AlertaCumpleanosDialog(self, data)
                    dialog.setWindowFlags(
                        dialog.windowFlags() | Qt.WindowType.WindowStaysOnTopHint
                    )
                    dialog.raise_()
                    dialog.activateWindow()
                    dialog.exec()
        except Exception:
            pass

    def verificar_deudores(self):
        try:
            r = requests.get(f"{API_URL}/clientes/deudores", timeout=4)
            if r.status_code == 200:
                data = r.json()
                if data:
                    dialog = AlertaDeudoresDialog(self, data)
                    dialog.setWindowFlags(
                        dialog.windowFlags() | Qt.WindowType.WindowStaysOnTopHint
                    )
                    dialog.raise_()
                    dialog.activateWindow()
                    dialog.exec()
        except Exception:
            pass

    def on_logout(self):
        self.usuario_actual = None
        self.cajero_actual = None
        self.sidebar.hide()
        self.stack.setCurrentWidget(self.login_screen)
        self.setWindowTitle("Juana Cash - Sistema POS")
