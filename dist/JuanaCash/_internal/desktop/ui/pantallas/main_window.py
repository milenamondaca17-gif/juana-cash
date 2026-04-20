"""
JUANA CASH — Ventana principal (rediseño navbar horizontal)
Navbar 56px arriba, ítem activo con borde rojo inferior, fondo #050e1a.
"""

import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QApplication,
    QSpacerItem, QSizePolicy, QMessageBox
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QColor

# ---------- Colores Juana Cash ----------
BG        = "#050e1a"
NAV_BG    = "#0a1628"
NAV_BRD   = "#1a2744"
RED       = "#e63946"
WHITE     = "#f0f0f0"
GRAY      = "#8899aa"
ACTIVE_BG = "#111d33"

# ---------- Secciones del menú ----------
MENU_ITEMS = [
    {"key": "ventas",       "label": "Ventas",        "icon": "🛒"},
    {"key": "productos",    "label": "Productos",     "icon": "📦"},
    {"key": "clientes",     "label": "Clientes",      "icon": "👥"},
    {"key": "caja",         "label": "Caja",          "icon": "💰"},
    {"key": "reportes",     "label": "Reportes",      "icon": "📊"},
    {"key": "dashboard",    "label": "Dashboard",     "icon": "📈"},
    {"key": "stock",        "label": "Stock",         "icon": "📋"},
    {"key": "config",       "label": "Config",        "icon": "⚙️"},
]


class NavButton(QPushButton):
    """Botón de la navbar horizontal con indicador rojo inferior."""

    def __init__(self, key: str, label: str, icon_text: str, parent=None):
        super().__init__(parent)
        self.key = key
        self.setText(f"{icon_text}  {label}")
        self.setCheckable(True)
        self.setFixedHeight(56)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
        self._apply_style(False)

    def _apply_style(self, active: bool):
        if active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ACTIVE_BG};
                    color: {WHITE};
                    border: none;
                    border-bottom: 3px solid {RED};
                    padding: 0 16px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {GRAY};
                    border: none;
                    border-bottom: 3px solid transparent;
                    padding: 0 16px;
                }}
                QPushButton:hover {{
                    color: {WHITE};
                    background-color: {ACTIVE_BG};
                    border-bottom: 3px solid {GRAY};
                }}
            """)

    def set_active(self, active: bool):
        self.setChecked(active)
        self._apply_style(active)


class MainWindow(QMainWindow):
    """Ventana principal con navbar horizontal superior."""

    logout_requested = pyqtSignal()

    def __init__(self, user_data: dict = None, parent=None):
        super().__init__(parent)
        self.user_data = user_data or {}
        self.setWindowTitle("Juana Cash - Mostrador Principal")
        self.setMinimumSize(1200, 700)
        self.showMaximized()

        self._nav_buttons: dict[str, NavButton] = {}
        self._pages: dict[str, QWidget] = {}
        self._current_key: str = ""

        self._build_ui()
        self._load_pages()
        self.navigate("ventas")

    # ================================================================= UI
    def _build_ui(self):
        central = QWidget()
        central.setStyleSheet(f"background-color: {BG};")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---- Navbar superior ----
        navbar = QWidget()
        navbar.setFixedHeight(56)
        navbar.setStyleSheet(f"""
            background-color: {NAV_BG};
            border-bottom: 1px solid {NAV_BRD};
        """)

        nav_lay = QHBoxLayout(navbar)
        nav_lay.setContentsMargins(15, 0, 15, 0)
        nav_lay.setSpacing(5)

        # Logo a la izquierda
        logo = QLabel("JUANA CASH")
        logo.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        logo.setStyleSheet(f"color: {RED}; background: transparent; border: none; letter-spacing: 1px;")
        nav_lay.addWidget(logo)

        nav_lay.addSpacing(30)

        # Botones del menú
        for item in MENU_ITEMS:
            btn = NavButton(item["key"], item["label"], item["icon"])
            btn.clicked.connect(lambda checked, k=item["key"]: self.navigate(k))
            self._nav_buttons[item["key"]] = btn
            nav_lay.addWidget(btn)

        nav_lay.addStretch()

        # Info usuario
        user_name = self.user_data.get("nombre", self.user_data.get("email", "Admin"))
        user_role = self.user_data.get("rol", "admin").capitalize()
        lbl_user = QLabel(f"👤 {user_name}  •  {user_role}")
        lbl_user.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        lbl_user.setStyleSheet(f"color: {WHITE}; background: transparent; border: none;")
        nav_lay.addWidget(lbl_user)

        nav_lay.addSpacing(20)

        # Botón salir
        btn_exit = QPushButton("Salir")
        btn_exit.setFixedSize(80, 36)
        btn_exit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_exit.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        btn_exit.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {GRAY};
                border: 2px solid {NAV_BRD};
                border-radius: 8px;
            }}
            QPushButton:hover {{
                color: {WHITE};
                background-color: {RED};
                border-color: {RED};
            }}
        """)
        btn_exit.clicked.connect(self._on_logout)
        nav_lay.addWidget(btn_exit)

        root.addWidget(navbar)

        # ---- Contenido (Donde cargan las pantallas) ----
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent; border: none;")
        root.addWidget(self.stack)

    # ================================================================= Páginas
    def _load_pages(self):
        """
        Intentá importar cada pantalla. Si no existe, crea un placeholder.
        Adaptá los imports a tu estructura real de carpetas.
        """
        page_map = {
            "ventas":    "desktop.ui.pantallas.ventas",
            "productos": "desktop.ui.pantallas.productos",
            "clientes":  "desktop.ui.pantallas.clientes",
            "caja":      "desktop.ui.pantallas.caja",
            "reportes":  "desktop.ui.pantallas.reportes",
            "dashboard": "desktop.ui.pantallas.dashboard",
            "stock":     "desktop.ui.pantallas.stock",
            "config":    "desktop.ui.pantallas.configuracion",
        }

        # Nombres de clase esperados por convención
        class_names = {
            "ventas":    "VentasScreen",
            "productos": "ProductosScreen",
            "clientes":  "ClientesScreen",
            "caja":      "CajaScreen",
            "reportes":  "ReportesScreen",
            "dashboard": "DashboardScreen",
            "stock":     "StockScreen",
            "config":    "ConfiguracionScreen",
        }

        for key, module_path in page_map.items():
            try:
                import importlib
                mod = importlib.import_module(module_path)
                cls_name = class_names.get(key, "Screen")
                cls = getattr(mod, cls_name)
                # Pasamos user_data si el constructor lo acepta
                try:
                    page = cls(user_data=self.user_data)
                except TypeError:
                    page = cls()
                self._pages[key] = page
            except Exception:
                page = self._placeholder(key)
                self._pages[key] = page

            self.stack.addWidget(self._pages[key])

    def _placeholder(self, key: str) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl = QLabel(f"🏗️ Sección: {key.upper()}\n(En construcción)")
        lbl.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {GRAY}; background: transparent;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(lbl)
        return w

    # ================================================================= Navegación
    def navigate(self, key: str):
        if key == self._current_key:
            return
        # Desactivar anterior
        if self._current_key in self._nav_buttons:
            self._nav_buttons[self._current_key].set_active(False)
        # Activar nuevo
        if key in self._nav_buttons:
            self._nav_buttons[key].set_active(True)
        if key in self._pages:
            self.stack.setCurrentWidget(self._pages[key])
        self._current_key = key

    # ================================================================= Logout
    def _on_logout(self):
        reply = QMessageBox.question(
            self, "Cerrar sesión",
            "¿Querés salir del mostrador?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.logout_requested.emit()
            self.close()

# ------------------------------------------------------------------ standalone
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow(user_data={"nombre": "Lucas", "rol": "admin", "email": "lucas@juanacash.com"})
    win.show()
    sys.exit(app.exec())