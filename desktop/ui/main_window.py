import os
import requests
from datetime import datetime
from PyQt6.QtWidgets import (QMainWindow, QStackedWidget, QWidget, QHBoxLayout,
                             QVBoxLayout, QPushButton, QLabel, QMessageBox,
                             QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QFrame)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QIcon

# Importaciones de tus pantallas
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
from ui.pantallas.precios_masivos import PreciosMasivosScreen
from ui.pantallas.ia_screen import IAScreen
from ui.pantallas.config_screen import ConfigScreen
from ui.pantallas.importador import ImportadorScreen # LA NUEVA NAVE

try:
    from ui.pantallas.offline_manager import sincronizar_cola, cantidad_pendientes, servidor_disponible
except Exception:
    sincronizar_cola = None
    cantidad_pendientes = lambda: 0
    servidor_disponible = lambda: True

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
        central.setStyleSheet("background-color: #050e1a;") 
        self.setCentralWidget(central)
        
        self.main_layout = QVBoxLayout(central)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # ── Navbar Horizontal Superior ───────────────
        self.navbar = QFrame()
        self.navbar.setFixedHeight(60)
        self.navbar.setStyleSheet("background-color: #0a1628; border-bottom: 1px solid #1a2744;")
        self.navbar.hide()
        
        navbar_layout = QHBoxLayout(self.navbar)
        navbar_layout.setContentsMargins(15, 0, 15, 0)
        navbar_layout.setSpacing(5)

        logo = QLabel("JUANA CASH")
        logo.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        logo.setStyleSheet("color: #e63946; border: none; font-weight: bold;")
        navbar_layout.addWidget(logo)

        navbar_layout.addSpacing(30)

        self.btns_menu = {}
        # Agregamos "importador" a la lista de menús de administrador
        self.menus_admin = ["usuarios", "sesiones", "dashboard", "stock", "precios", "ia", "importador"]
        
        # Agregamos el botón a la lista visual
        menus = [
            ("🛒 Ventas",      "ventas"),
            ("📦 Prod.",        "productos"),
            ("👥 Client.",      "clientes"),
            ("🧾 Caja",         "caja"),
            ("📊 Repor.",       "reportes"),
            ("📈 Dash",         "dashboard"),
            ("📋 Stock",        "stock"),
            ("💰 Prec.",        "precios"),
            ("🤖 IA",           "ia"),
            ("⚙️ Config",       "config"),
            ("📋 Ses.",         "sesiones"),
            ("👤 Usuar.",       "usuarios"),
            ("📥 Importar",     "importador"),
        ]
        
        for texto, key in menus:
            btn = QPushButton(texto)
            btn.setFixedHeight(60)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton { background: transparent; color: #8899aa; font-size: 13px; font-weight: bold; border: none; padding: 0 12px; border-bottom: 3px solid transparent;}
                QPushButton:hover { color: #f0f0f0; background: #111d33; border-bottom: 3px solid #8899aa;}
                QPushButton:checked { color: white; background: #111d33; border-bottom: 3px solid #e63946;}
            """)
            btn.clicked.connect(lambda _, k=key: self.cambiar_pantalla(k))
            navbar_layout.addWidget(btn)
            self.btns_menu[key] = btn

        navbar_layout.addStretch()

        self.lbl_cajero_navbar = QLabel("")
        self.lbl_cajero_navbar.setStyleSheet("color: #f0f0f0; font-size: 13px; border: none; margin-right: 15px;")
        navbar_layout.addWidget(self.lbl_cajero_navbar)

        btn_salir = QPushButton("Salir")
        btn_salir.setFixedHeight(36)
        btn_salir.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_salir.setStyleSheet("""
            QPushButton { background: transparent; color: #8899aa; font-size: 13px; font-weight: bold; border: 1px solid #1a2744; border-radius: 6px; padding: 0 15px;}
            QPushButton:hover { background: #e63946; color: white; border-color: #e63946;}
        """)
        btn_salir.clicked.connect(self.on_logout)
        navbar_layout.addWidget(btn_salir)
        
        self.main_layout.addWidget(self.navbar)

        # ── Stack de pantallas ────────────────────────────────────────────────
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: transparent;")
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
        self.precios_screen = PreciosMasivosScreen()
        self.ia_screen = IAScreen()
        self.config_screen = ConfigScreen()
        self.importador_screen = ImportadorScreen() # ACTIVAMOS LA NAVE

        for screen in [
            self.login_screen, self.turno_screen, self.ventas_screen,
            self.productos_screen, self.reportes_screen, self.clientes_screen,
            self.caja_screen, self.sesiones_screen, self.usuarios_screen,
            self.dashboard_screen,
            self.stock_screen,
            self.precios_screen,
            self.ia_screen,
            self.config_screen,
            self.importador_screen # LO METEMOS AL STACK
        ]:
            self.stack.addWidget(screen)

        self.stack.setCurrentWidget(self.login_screen)

    def cambiar_pantalla(self, key):
        rol = self.cajero_actual.get("rol", "cajero") if self.cajero_actual else "cajero"
        
        if key in self.menus_admin and rol not in ["admin", "encargado"]:
            QMessageBox.warning(self, "Acceso denegado",
                "Solo admin o encargado pueden acceder a esta sección")
            for k, btn in self.btns_menu.items():
                btn.setChecked(btn.property("activo") == True)
            return

        for k, btn in self.btns_menu.items():
            es_activo = (k == key)
            btn.setChecked(es_activo)
            btn.setProperty("activo", es_activo)

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
            "precios":   self.precios_screen,
            "ia":        self.ia_screen,
            "config":    self.config_screen,
            "importador": self.importador_screen, # LO CONECTAMOS AL BOTON
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

        self.lbl_cajero_navbar.setText(f"👤 {nombre} | 🎖 {rol} | 🕐 {turno[:5]}")

        for key, btn in self.btns_menu.items():
            if key in self.menus_admin and rol not in ["admin", "encargado"]:
                btn.hide() 
            else:
                btn.show()

        self.ventas_screen.set_usuario(cajero)
        self.caja_screen.set_usuario(cajero)
        
        self.navbar.show() 
        self.cambiar_pantalla("ventas") 

        if not hasattr(self, '_timer_timeout'):
            self._timer_timeout = QTimer()
            self._timer_timeout.timeout.connect(self._check_timeout)
        self._ultimo_movimiento = datetime.now()
        self._timeout_minutos = 30
        self._timer_timeout.start(60000)

        if not hasattr(self, '_timer_offline'):
            self._timer_offline = QTimer()
            self._timer_offline.timeout.connect(self._sync_offline)
        self._timer_offline.start(30000)
        self.setWindowTitle(f"Juana Cash — {nombre} | {rol} | {turno[:5]}")

    def verificar_cumpleanos(self):
        try:
            r = requests.get(f"{API_URL}/clientes/cumpleanos", timeout=4)
            if r.status_code == 200:
                data = r.json()
                if data:
                    dialog = AlertaCumpleanosDialog(self, data)
                    dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
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
                    dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
                    dialog.raise_()
                    dialog.activateWindow()
                    dialog.exec()
        except Exception:
            pass

    def _check_timeout(self):
        if not self.cajero_actual:
            return
        try:
            r = requests.get("http://127.0.0.1:8000/config/", timeout=2)
            minutos = r.json().get("timeout_minutos", 30)
        except Exception:
            minutos = 30
        desde_ultimo = (datetime.now() - self._ultimo_movimiento).total_seconds() / 60
        if desde_ultimo >= minutos:
            self._timer_timeout.stop()
            QMessageBox.information(self, "⏱ Sesión expirada",
                f"La sesión se cerró automáticamente por {minutos} minutos de inactividad.")
            self.on_logout()

    def _sync_offline(self):
        if sincronizar_cola is None:
            return
        pendientes = cantidad_pendientes()
        if pendientes > 0:
            enviadas, fallidas, _ = sincronizar_cola()
            if enviadas > 0:
                self.setWindowTitle(self.windowTitle().split(" 📡")[0] + f" ✅ {enviadas} venta(s) sincronizada(s)")
                QTimer.singleShot(5000, lambda: self.setWindowTitle(self.windowTitle().split(" ✅")[0]))
        aun_pendientes = cantidad_pendientes()
        titulo_base = self.windowTitle().split(" 📡")[0].split(" ✅")[0]
        if aun_pendientes > 0:
            self.setWindowTitle(titulo_base + f" 📡 {aun_pendientes} offline")
        else:
            self.setWindowTitle(titulo_base)

    def mousePressEvent(self, event):
        self._ultimo_movimiento = datetime.now()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        self._ultimo_movimiento = datetime.now()
        super().keyPressEvent(event)

    def on_logout(self):
        self.usuario_actual = None
        self.cajero_actual = None
        self.navbar.hide() 
        self.stack.setCurrentWidget(self.login_screen)
        self.setWindowTitle("Juana Cash - Sistema POS")
        if hasattr(self, '_timer_timeout'):
            self._timer_timeout.stop()
        if hasattr(self, '_timer_offline'):
            self._timer_offline.stop()