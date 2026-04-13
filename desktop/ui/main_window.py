import os
from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt
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
        self.menus_admin = ["usuarios", "sesiones"]
        menus = [
            ("🛒  Ventas", "ventas"),
            ("📦  Productos", "productos"),
            ("👥  Clientes", "clientes"),
            ("🏧  Caja", "caja"),
            ("📊  Reportes", "reportes"),
            ("📋  Sesiones", "sesiones"),
            ("👤  Usuarios", "usuarios"),
        ]
        for texto, key in menus:
            btn = QPushButton(texto)
            btn.setFixedHeight(48)
            btn.setStyleSheet("QPushButton { background: transparent; color: #a0a0b0; text-align: left; padding-left: 20px; font-size: 14px; border: none; } QPushButton:hover { background: #0f3460; color: white; }")
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
        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)
        self.login_screen = LoginScreen(self.on_login_exitoso)
        self.turno_screen = TurnoScreen(self.on_turno_seleccionado, {})
        self.ventas_screen = VentasScreen(self.on_logout)
        self.productos_screen = ProductosScreen()
        self.reportes_screen = ReportesScreen()
        self.clientes_screen = ClientesScreen()
        self.caja_screen = CajaScreen()
        self.sesiones_screen = SesionesScreen()
        self.usuarios_screen = UsuariosScreen()
        self.stack.addWidget(self.login_screen)
        self.stack.addWidget(self.turno_screen)
        self.stack.addWidget(self.ventas_screen)
        self.stack.addWidget(self.productos_screen)
        self.stack.addWidget(self.reportes_screen)
        self.stack.addWidget(self.clientes_screen)
        self.stack.addWidget(self.caja_screen)
        self.stack.addWidget(self.sesiones_screen)
        self.stack.addWidget(self.usuarios_screen)
        self.stack.setCurrentWidget(self.login_screen)

    def cambiar_pantalla(self, key):
        rol = self.cajero_actual.get("rol", "cajero") if self.cajero_actual else "cajero"
        if key in self.menus_admin and rol not in ["admin", "encargado"]:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Acceso denegado", "Solo admin o encargado pueden acceder a esta sección")
            return
        pantallas = {
            "ventas": self.ventas_screen,
            "productos": self.productos_screen,
            "reportes": self.reportes_screen,
            "clientes": self.clientes_screen,
            "caja": self.caja_screen,
            "sesiones": self.sesiones_screen,
            "usuarios": self.usuarios_screen,
        }
        if key in pantallas:
            if key == "productos":
                self.productos_screen.cargar_productos()
            elif key == "reportes":
                self.reportes_screen.cargar_datos()
            elif key == "clientes":
                self.clientes_screen.cargar_clientes()
            elif key == "caja":
                self.caja_screen.actualizar_ventas()
            elif key == "sesiones":
                self.sesiones_screen.cargar_sesiones()
            elif key == "usuarios":
                self.usuarios_screen.cargar_usuarios()
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
        turno = cajero.get("turno", "")
        rol = cajero.get("rol", "cajero")
        self.lbl_cajero_sidebar.setText(f"👤 {nombre}\n🎭 {rol}\n🕐 {turno[:5]}")
        for key, btn in self.btns_menu.items():
            if key in self.menus_admin and rol not in ["admin", "encargado"]:
                btn.setStyleSheet("QPushButton { background: transparent; color: #555; text-align: left; padding-left: 20px; font-size: 14px; border: none; }")
            else:
                btn.setStyleSheet("QPushButton { background: transparent; color: #a0a0b0; text-align: left; padding-left: 20px; font-size: 14px; border: none; } QPushButton:hover { background: #0f3460; color: white; }")
        self.ventas_screen.set_usuario(cajero)
        self.caja_screen.set_usuario(cajero)
        self.sidebar.show()
        self.stack.setCurrentWidget(self.ventas_screen)
        self.setWindowTitle(f"Juana Cash — {nombre} | {rol} | {turno[:5]}")

    def on_logout(self):
        self.usuario_actual = None
        self.cajero_actual = None
        self.sidebar.hide()
        self.stack.setCurrentWidget(self.login_screen)
        self.setWindowTitle("Juana Cash - Sistema POS")