import os, math, random, threading
import requests
from datetime import datetime
from PyQt6.QtWidgets import (QMainWindow, QStackedWidget, QWidget, QHBoxLayout,
                             QVBoxLayout, QPushButton, QLabel, QMessageBox,
                             QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
                             QApplication)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QIcon, QPainter, QColor, QBrush, QPen
from ui.theme import get_tema, TEMAS, guardar_tema


class FuegosArtificiales(QWidget):
    """Overlay de fuegos artificiales que se muestra sobre toda la ventana."""
    _COLORES = ["#FFD700","#FF6B6B","#4ECDC4","#45B7D1","#FF69B4",
                "#98FB98","#FFA500","#DDA0DD","#00FA9A","#FF4500"]

    def __init__(self, parent, cajero_nombre="", titulo="¡FELICITACIONES!", mensaje="{nombre}, llegaste a la meta del turno! 🎉"):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(0, 0, parent.width(), parent.height())
        self._particles = []
        self._elapsed   = 0
        self._duration  = 5000
        self._titulo    = titulo
        self._mensaje   = mensaje.replace("{nombre}", cajero_nombre) if cajero_nombre else mensaje.replace("{nombre}", "")

        self._lanzar_rafaga()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)
        self.raise_()
        self.show()

    def _lanzar_rafaga(self):
        W, H = self.width(), self.height()
        for _ in range(7):
            cx = random.randint(W // 8, W * 7 // 8)
            cy = random.randint(H // 8, H // 2)
            col = random.choice(self._COLORES)
            for _ in range(30):
                ang   = random.uniform(0, math.tau)
                spd   = random.uniform(2, 9)
                self._particles.append({
                    "x": cx, "y": cy,
                    "vx": spd * math.cos(ang),
                    "vy": spd * math.sin(ang),
                    "col": col,
                    "life": random.uniform(0.7, 1.0),
                    "size": random.uniform(3, 7),
                })

    def _tick(self):
        self._elapsed += 16
        if self._elapsed > self._duration:
            self._timer.stop()
            self.hide()
            self.deleteLater()
            return
        if self._elapsed % 700 < 16:
            self._lanzar_rafaga()
        for p in self._particles:
            p["x"]  += p["vx"]
            p["y"]  += p["vy"]
            p["vy"] += 0.18
            p["life"] -= 0.018
        self._particles = [p for p in self._particles if p["life"] > 0]
        self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Fondo semi-oscuro para que los fuegos se vean
        painter.fillRect(self.rect(), QColor(0, 0, 0, 90))

        # Partículas
        for p in self._particles:
            alpha = max(0, min(255, int(p["life"] * 255)))
            c = QColor(p["col"]); c.setAlpha(alpha)
            painter.setBrush(QBrush(c))
            painter.setPen(Qt.PenStyle.NoPen)
            sz = p["size"]
            painter.drawEllipse(int(p["x"] - sz/2), int(p["y"] - sz/2), int(sz), int(sz))

        # Banner de festejo (primeros 4 s)
        if self._elapsed < 4000:
            fade_in  = min(1.0, self._elapsed / 300)
            fade_out = 1.0 if self._elapsed < 3200 else max(0.0, 1.0 - (self._elapsed - 3200) / 800)
            alpha    = int(255 * fade_in * fade_out)
            cx, cy   = self.width() // 2, self.height() // 2

            # Fondo del banner
            bw, bh = min(self.width() - 80, 780), 170
            bx, by = cx - bw // 2, cy - bh // 2
            bg = QColor(5, 14, 26, int(alpha * 0.92))
            painter.setBrush(QBrush(bg))
            border_col = QColor(212, 160, 23, alpha)
            painter.setPen(QPen(border_col, 3))
            painter.drawRoundedRect(bx, by, bw, bh, 18, 18)

            # Título dorado
            font_t = QFont("Segoe UI", 36, QFont.Weight.Black)
            painter.setFont(font_t)
            gold = QColor("#FFD700"); gold.setAlpha(alpha)
            painter.setPen(QPen(gold))
            painter.drawText(bx, by + 10, bw, 80, Qt.AlignmentFlag.AlignCenter, self._titulo)

            # Separador
            sep_col = QColor(212, 160, 23, int(alpha * 0.5))
            painter.setPen(QPen(sep_col, 1))
            painter.drawLine(bx + 40, by + 88, bx + bw - 40, by + 88)

            # Mensaje
            font_m = QFont("Segoe UI", 18, QFont.Weight.Bold)
            painter.setFont(font_m)
            white = QColor(255, 255, 255, alpha)
            painter.setPen(QPen(white))
            painter.drawText(bx, by + 95, bw, 60, Qt.AlignmentFlag.AlignCenter, self._mensaje)

        painter.end()

_T = get_tema()

def _leer_config_logros():
    """Lee meta_ventas, logro_titulo y logro_mensaje desde app_config.json."""
    try:
        cfg_path = os.path.join(os.path.expanduser("~"), "JuanaCash_Data", "app_config.json")
        if os.path.exists(cfg_path):
            import json as _json
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = _json.load(f)
            return {
                "meta":    cfg.get("meta_ventas", 750000),
                "titulo":  cfg.get("logro_titulo", "¡FELICITACIONES!"),
                "mensaje": cfg.get("logro_mensaje", "{nombre}, llegaste a la meta del turno! 🎉"),
            }
    except Exception:
        pass
    return {"meta": 750000, "titulo": "¡FELICITACIONES!", "mensaje": "{nombre}, llegaste a la meta del turno! 🎉"}

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
try:
    from ui.pantallas.proveedores import ProveedoresScreen
    _PROVEEDORES_OK = True
except Exception:
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
    class ProveedoresScreen(QWidget):
        def __init__(self):
            super().__init__()
            lay = QVBoxLayout(self)
            lay.addWidget(QLabel("Módulo Proveedores no disponible. Reinstalá la app."))
    _PROVEEDORES_OK = False
from ui.pantallas.dashboard import DashboardScreen
from ui.pantallas.stock_avanzado import StockAvanzadoScreen
from ui.pantallas.precios_masivos import PreciosMasivosScreen
from ui.pantallas.ia_screen import IAScreen
from ui.pantallas.config_screen import ConfigScreen
from ui.pantallas.importador import ImportadorScreen # LA NUEVA NAVE
from ui.pantallas.etiquetas.generador_etiquetas import GeneradorEtiquetasScreen # <-- LA FÁBRICA DE ETIQUETAS
from ui.pantallas.ofertas import OfertasScreen # <-- PANTALLA DE OFERTAS
from ui.pantallas.precios_alerta import AlertasPrecioScreen  # <-- ALERTAS DE PRECIOS

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
        self.setMinimumWidth(420)
        self.setStyleSheet(f"background-color: {_T['bg_card']}; color: {_T['text_main']};")
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        titulo = QLabel("🎂 Clientes con cumpleaños")
        titulo.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        titulo.setStyleSheet(f"color: {_T['accent_yellow']}; background: transparent;")
        layout.addWidget(titulo)

        hoy = [c for c in clientes if c.get("tipo") == "hoy"]
        proximos = [c for c in clientes if c.get("tipo") == "proximo"]

        if hoy:
            lbl = QLabel("🎉 HOY es el cumpleaños de:")
            lbl.setStyleSheet(f"color: {_T['success']}; font-size: 13px; font-weight: bold; background: transparent;")
            layout.addWidget(lbl)
            for c in hoy:
                fila = QLabel(f"   🎂 {c['nombre']}" + (f"  — {c['telefono']}" if c.get("telefono") else ""))
                fila.setStyleSheet(f"color: {_T['text_main']}; font-size: 13px; padding: 2px 0; background: transparent;")
                layout.addWidget(fila)

        if proximos:
            lbl2 = QLabel("📅 Próximos cumpleaños (7 días):")
            lbl2.setStyleSheet(f"color: {_T['primary']}; font-size: 12px; font-weight: bold; margin-top: 8px; background: transparent;")
            layout.addWidget(lbl2)
            for c in proximos:
                fila = QLabel(f"   📆 {c['nombre']}  —  {c['dia']:02d}/{c['mes']:02d}")
                fila.setStyleSheet(f"color: {_T['text_muted']}; font-size: 12px; padding: 2px 0; background: transparent;")
                layout.addWidget(fila)

        btn = QPushButton("OK")
        btn.setFixedHeight(40)
        btn.setStyleSheet(f"QPushButton {{ background: {_T['accent_yellow']}; color: white; border-radius: 8px; font-size: 14px; font-weight: bold; }} QPushButton:hover {{ background: {_T['warning']}; }}")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)

class AlertaDeudoresDialog(QDialog):
    def __init__(self, parent=None, deudores=None):
        super().__init__(parent)
        self.setWindowTitle("💸 Deudores")
        self.setMinimumWidth(520)
        self.setMinimumHeight(380)
        self.setStyleSheet(f"background-color: {_T['bg_card']}; color: {_T['text_main']};")
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        titulo = QLabel(f"💸 {len(deudores)} clientes con deuda pendiente")
        titulo.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        titulo.setStyleSheet(f"color: {_T['danger']}; background: transparent;")
        layout.addWidget(titulo)

        total_deuda = sum(float(d.get("deuda_actual", 0)) for d in deudores)
        lbl_total = QLabel(f"Total adeudado: ${total_deuda:,.2f}")
        lbl_total.setStyleSheet(f"color: {_T['accent_orange']}; font-size: 14px; font-weight: bold; background: transparent;")
        layout.addWidget(lbl_total)

        tabla = QTableWidget()
        tabla.setColumnCount(3)
        tabla.setHorizontalHeaderLabels(["Cliente", "Deuda", "Teléfono"])
        tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        tabla.setColumnWidth(1, 110)
        tabla.setColumnWidth(2, 120)
        tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tabla.setRowCount(len(deudores))

        from PyQt6.QtGui import QColor
        for i, d in enumerate(deudores):
            tabla.setItem(i, 0, QTableWidgetItem(d["nombre"]))
            item_deuda = QTableWidgetItem(f"${float(d['deuda_actual']):,.2f}")
            item_deuda.setForeground(QColor(_T['danger']))
            tabla.setItem(i, 1, item_deuda)
            tabla.setItem(i, 2, QTableWidgetItem(d.get("telefono") or "-"))

        layout.addWidget(tabla)

        btn = QPushButton("Cerrar")
        btn.setFixedHeight(40)
        btn.setStyleSheet(f"QPushButton {{ background: {_T['danger']}; color: white; border-radius: 8px; font-size: 13px; font-weight: bold; }} QPushButton:hover {{ background: #b91c1c; }}")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Juana Cash - Sistema POS")
        screen = QApplication.primaryScreen().availableGeometry()
        min_w = min(1280, screen.width())
        min_h = min(720, screen.height())
        self.setMinimumSize(min_w, min_h)
        self.usuario_actual = None
        self.cajero_actual = None

        central = QWidget()
        central.setStyleSheet(f"background-color: {_T['bg_app']};")
        self.setCentralWidget(central)
        
        self.main_layout = QVBoxLayout(central)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # ── Navbar Horizontal Superior ───────────────
        self.navbar = QFrame()
        self.navbar.setFixedHeight(62)
        self.navbar.setStyleSheet(
            f"QFrame {{ background: {_T['bg_navbar']}; border-radius: 0px; border-bottom: 1.5px solid {_T['navbar_border']}; }}"
        )
        self.navbar.hide()

        navbar_layout = QHBoxLayout(self.navbar)
        navbar_layout.setContentsMargins(20, 0, 16, 0)
        navbar_layout.setSpacing(2)

        logo = QLabel(
            f"<span style='color:{_T['logo_color']};font-weight:900;font-size:17px;letter-spacing:1px;'>JUANA</span>"
            f"<span style='color:{_T.get('navbar_muted', _T['text_muted'])};font-weight:300;font-size:17px;letter-spacing:1px;'> CASH</span>"
            f"<span style='color:{_T['accent_green']};font-weight:900;font-size:15px;'>$</span>"
        )
        logo.setStyleSheet("border: none; background: transparent;")
        navbar_layout.addWidget(logo)

        navbar_layout.addSpacing(24)

        self.btns_menu = {}
        self.menus_admin = ["usuarios", "sesiones", "dashboard", "ofertas", "alertas"]

        menus_principales = [
            ("🛒 Ventas",       "ventas"),
            ("🧾 Caja",         "caja"),
            ("📦 Productos",    "productos"),
            ("👥 Clientes",     "clientes"),
            ("🏭 Proveedores",  "proveedores"),
            ("📈 Dashboard",    "dashboard"),
            ("🔔 Alertas",      "alertas"),
            ("📊 Reportes",     "reportes"),
            ("🏷️ Ofertas",      "ofertas"),
            ("⚙ Config",        "config"),
        ]

        ESTILO_BTN = (
            f"QPushButton {{ background: transparent; color: {_T['navbar_text']}; font-size: 12px; font-weight: 600;"
            f" border: none; border-radius: 8px; padding: 5px 13px; margin: 10px 2px; }}"
            f"QPushButton:hover {{ background: {_T.get('navbar_hover_bg', _T['bg_hover'])}; color: {_T.get('navbar_hover_text', _T['text_main'])}; }}"
            f"QPushButton:checked {{ background: {_T['navbar_active_bg']}; color: {_T['navbar_active']}; font-weight: 700; }}"
        )

        for texto, key in menus_principales:
            btn = QPushButton(texto)
            btn.setFixedHeight(62)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(ESTILO_BTN)
            btn.clicked.connect(lambda _, k=key: self.cambiar_pantalla(k))
            navbar_layout.addWidget(btn)
            self.btns_menu[key] = btn

        navbar_layout.addStretch()

        # Separador derecho
        _sep_der = QFrame()
        _sep_der.setFixedSize(1, 28)
        _sep_der.setStyleSheet(f"background: {_T['navbar_border']}; border: none; border-radius: 0;")
        navbar_layout.addWidget(_sep_der)
        navbar_layout.addSpacing(10)

        try:
            import json, sys
            _candidatos = [
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "version.json"),
                os.path.join(os.path.dirname(sys.executable), "version.json"),
            ]
            _ver = ""
            for _p in _candidatos:
                _p = os.path.normpath(_p)
                if os.path.exists(_p):
                    _ver = json.load(open(_p)).get("version", "")
                    break
        except Exception:
            _ver = ""
        if _ver:
            lbl_ver = QLabel(f"v{_ver}")
            lbl_ver.setStyleSheet(f"color: {_T.get('navbar_muted', _T['text_muted'])}; font-size: 10px; border: none; margin-right: 6px; letter-spacing: 1px;")
            navbar_layout.addWidget(lbl_ver)

        self.lbl_cajero_navbar = QLabel("")
        self.lbl_cajero_navbar.setStyleSheet(
            f"color: {_T['navbar_active']}; font-size: 11px; font-weight: 700;"
            f" border: 1px solid {_T['navbar_border']}; background: {_T['navbar_active_bg']};"
            f" border-radius: 14px; padding: 4px 14px; margin-right: 4px;"
        )
        navbar_layout.addWidget(self.lbl_cajero_navbar)

        btn_salir = QPushButton("✕ Salir")
        btn_salir.setFixedHeight(32)
        btn_salir.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_salir.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {_T.get('navbar_muted', _T['text_muted'])}; font-size: 12px; font-weight: 600; border: 1px solid {_T['navbar_border']}; border-radius: 10px; padding: 0 14px; }}
            QPushButton:hover {{ background: {_T['danger']}; color: white; border-color: {_T['danger']}; }}
        """)
        btn_salir.clicked.connect(self.on_logout)
        navbar_layout.addWidget(btn_salir)
        
        self.main_layout.addWidget(self.navbar)

        # ── Barra de meta por turno (1 barra = empleado logueado) ───────────────
        from PyQt6.QtWidgets import QProgressBar
        self._META = 750_000

        self._meta_bar = QFrame()
        self._meta_bar.setFixedHeight(34)
        self._meta_bar.setStyleSheet(f"background: {_T['bg_card']}; border-bottom: 1px solid {_T['border']};")
        self._meta_bar.hide()

        _mb_lay = QHBoxLayout(self._meta_bar)
        _mb_lay.setContentsMargins(18, 3, 18, 3)
        _mb_lay.setSpacing(12)

        _BAR_SS = (f"QProgressBar{{background:{_T['border']};border-radius:4px;border:none;}}"
                   "QProgressBar::chunk{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                   "stop:0 #b45309,stop:0.6 #f59e0b,stop:1 #fde68a);border-radius:4px;}")

        self._bar_meta = QProgressBar()
        self._bar_meta.setMaximum(self._META); self._bar_meta.setValue(0)
        self._bar_meta.setFixedHeight(8); self._bar_meta.setTextVisible(False)
        self._bar_meta.setStyleSheet(_BAR_SS)
        _mb_lay.addWidget(self._bar_meta, 1)

        self._lbl_meta_pct = QLabel("0%", styleSheet="color:#64748b;font-size:11px;font-weight:bold;background:transparent;min-width:36px;")
        _mb_lay.addWidget(self._lbl_meta_pct)

        self.main_layout.addWidget(self._meta_bar)

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
        self.usuarios_screen    = UsuariosScreen()
        self.proveedores_screen = ProveedoresScreen()
        self.dashboard_screen   = DashboardScreen()
        self.stock_screen = StockAvanzadoScreen()
        self.precios_screen = PreciosMasivosScreen()
        self.ia_screen = IAScreen()
        self.config_screen = ConfigScreen()
        self.importador_screen = ImportadorScreen()
        self.etiquetas_screen = GeneradorEtiquetasScreen()
        self.ofertas_screen = OfertasScreen()

        # Cuando se guarda un producto, actualizar el caché de ventas inmediatamente
        self.productos_screen.producto_guardado.connect(
            lambda: threading.Thread(
                target=self.ventas_screen._cargar_cache_productos, daemon=True
            ).start()
        )

        # Cuando se agrega/borra una oferta, el rotador se actualiza automáticamente
        self.ofertas_screen.oferta_cambiada.connect(
            lambda: self.ventas_screen.rotador_ofertas.cargar()
            if hasattr(self.ventas_screen, 'rotador_ofertas') else None
        )

        self.alertas_screen = AlertasPrecioScreen()

        # Agregar pantallas de admin como pestañas dentro de Config
        self.config_screen.agregar_tab(self.etiquetas_screen,  "🖨️ Etiquetas")
        self.config_screen.agregar_tab(self.stock_screen,      "📋 Stock")
        self.config_screen.agregar_tab(self.precios_screen,    "💰 Precios")
        self.config_screen.agregar_tab(self.importador_screen, "📥 Importar")
        self.config_screen.agregar_tab(self.ia_screen,         "🤖 IA")
        self.config_screen.agregar_tab(self.usuarios_screen,   "👤 Usuarios")

        for screen in [
            self.login_screen, self.turno_screen, self.ventas_screen,
            self.productos_screen, self.reportes_screen, self.clientes_screen,
            self.caja_screen, self.sesiones_screen, self.dashboard_screen,
            self.proveedores_screen,
            self.config_screen, self.ofertas_screen, self.alertas_screen,
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
            "ventas":       self.ventas_screen,
            "productos":    self.productos_screen,
            "reportes":     self.reportes_screen,
            "clientes":     self.clientes_screen,
            "caja":         self.caja_screen,
            "sesiones":     self.sesiones_screen,
            "dashboard":    self.dashboard_screen,
            "proveedores":  self.proveedores_screen,
            "config":       self.config_screen,
            "ofertas":      self.ofertas_screen,
            "alertas":      self.alertas_screen,
        }
        if key not in pantallas:
            return

        # Mostrar pantalla — cada una carga sus datos con showEvent propio
        self.stack.setCurrentWidget(pantallas[key])

    def on_login_exitoso(self, usuario):
        self.usuario_actual = usuario
        from datetime import datetime as _dt
        _hora = _dt.now().hour * 60 + _dt.now().minute
        if 9*60+30 <= _hora <= 13*60+30:
            turno = "Mañana (09:30 - 13:30)"
        elif 18*60 <= _hora <= 22*60:
            turno = "Tarde (18:00 - 22:00)"
        elif _hora < 9*60+30:
            turno = "Mañana (09:30 - 13:30)"
        else:
            turno = "Tarde (18:00 - 22:00)"
        cajero = {
            "nombre": usuario.get("nombre", ""),
            "turno": turno,
            "rol":   usuario.get("rol", "cajero"),
            "id":    usuario.get("id", 1)
        }
        try:
            requests.post(f"{API_URL}/sesiones/registrar", json={
                "usuario_id": cajero["id"],
                "nombre_cajero": cajero["nombre"],
                "turno": turno,
                "accion": "APERTURA_TURNO",
                "detalle": f"Turno iniciado: {turno}"
            }, timeout=3)
        except Exception:
            pass
        self.on_turno_seleccionado(cajero)

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
        self.clientes_screen.set_usuario(cajero)

        # Verificar si hay turno abierto; si no, pedir monto inicial obligatorio
        self._pedir_monto_inicial_si_necesario(cajero)

        # Timer para detectar ventas nuevas del celular
        if not hasattr(self, '_timer_celular'):
            self._timer_celular = QTimer()
            self._timer_celular.timeout.connect(self._chequear_ventas_celular)
        self._ultima_venta_celular = None
        self._timer_celular.start(15000)  # cada 15 segundos
        
        self.navbar.show()
        self._meta_bar.show()
        self._meta_celebrado = False
        _logros = _leer_config_logros()
        self._META = _logros["meta"]
        self._bar_meta.setMaximum(self._META)
        if not hasattr(self, '_timer_meta'):
            self._timer_meta = QTimer()
            self._timer_meta.timeout.connect(self._actualizar_meta)
        self._timer_meta.start(30000)
        self._actualizar_meta()

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

        if not hasattr(self, '_timer_update'):
            self._timer_update = QTimer()
            self._timer_update.timeout.connect(self._chequear_actualizacion)
        self._timer_update.start(6 * 60 * 60 * 1000)  # cada 6 horas

        # Timer badge alertas de precios
        if not hasattr(self, '_timer_alertas'):
            self._timer_alertas = QTimer()
            self._timer_alertas.timeout.connect(self._actualizar_badge_alertas)
        self._timer_alertas.start(20000)
        self._actualizar_badge_alertas()
        self.setWindowTitle(f"Juana Cash — {nombre} | {rol} | {turno[:5]}")

    def _pedir_monto_inicial_si_necesario(self, cajero):
        from datetime import date as _date
        usuario_id = cajero.get("id", 1)
        try:
            r = requests.get(f"{API_URL}/caja/turno-actual/{usuario_id}", timeout=4)
            if r.status_code == 200 and r.json().get("abierto"):
                apertura = r.json().get("apertura", "")
                # Solo saltar el diálogo si el turno abierto es de HOY
                if apertura and apertura[:10] == str(_date.today()):
                    return
                # Turno de otro día quedó abierto — igual pedir monto nuevo
        except Exception:
            pass  # Si no hay conexión, igual mostrar el diálogo

        # No hay turno abierto — mostrar diálogo obligatorio para ingresar monto inicial
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout
        from PyQt6.QtGui import QFont

        dlg = QDialog(self)
        dlg.setWindowTitle("Abrir caja")
        dlg.setFixedWidth(380)
        dlg.setWindowFlags(dlg.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)
        dlg.setStyleSheet(f"background: {_T['bg_card']}; color: {_T['text_main']};")

        lay = QVBoxLayout(dlg)
        lay.setSpacing(14)
        lay.setContentsMargins(28, 24, 28, 24)

        titulo = QLabel("💵 Ingresar monto inicial de caja")
        titulo.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        titulo.setStyleSheet(f"color: {_T['text_main']}; background: transparent;")
        lay.addWidget(titulo)

        sub = QLabel(f"Cajero: {cajero.get('nombre', '')}  |  {cajero.get('turno', '')}")
        sub.setStyleSheet(f"color: {_T['text_muted']}; font-size: 12px; background: transparent;")
        lay.addWidget(sub)

        lbl = QLabel("¿Cuánto efectivo hay en la caja para empezar el turno?")
        lbl.setWordWrap(True)
        lbl.setStyleSheet(f"color: {_T['text_muted']}; font-size: 13px; background: transparent;")
        lay.addWidget(lbl)

        inp = QLineEdit()
        inp.setPlaceholderText("Ej: 10000")
        inp.setFixedHeight(48)
        inp.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        inp.setStyleSheet(f"QLineEdit {{ background: {_T['bg_app']}; border: 2px solid {_T['primary']}; border-radius: 10px; padding: 8px 14px; color: {_T['text_main']}; }}")
        lay.addWidget(inp)

        lbl_err = QLabel("")
        lbl_err.setStyleSheet("color: #dc2626; font-size: 12px; background: transparent;")
        lay.addWidget(lbl_err)

        btn_ok = QPushButton("✅ Abrir caja")
        btn_ok.setFixedHeight(44)
        btn_ok.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        btn_ok.setStyleSheet(f"QPushButton {{ background: {_T['success']}; color: white; border-radius: 10px; font-weight: bold; }} QPushButton:hover {{ background: #15803d; }}")
        lay.addWidget(btn_ok)

        def confirmar():
            txt = inp.text().strip().replace(".", "").replace(",", ".")
            try:
                monto = float(txt) if txt else 0.0
            except ValueError:
                lbl_err.setText("Ingresá un número válido")
                return
            try:
                r2 = requests.post(f"{API_URL}/caja/abrir",
                                   json={"usuario_id": usuario_id, "monto_apertura": monto},
                                   timeout=5)
                if r2.status_code == 200:
                    self.caja_screen.turno_actual = None
                    self.caja_screen._cargar_turno_activo()
                    dlg.accept()
                else:
                    lbl_err.setText("No se pudo abrir la caja, intentá de nuevo")
            except Exception:
                lbl_err.setText("Sin conexión al servidor")

        btn_ok.clicked.connect(confirmar)
        inp.returnPressed.connect(confirmar)
        inp.setFocus()
        dlg.exec()

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
        def _check():
            try:
                r = requests.get("http://127.0.0.1:8000/config/", timeout=2)
                minutos = r.json().get("timeout_minutos", 30)
            except Exception:
                minutos = 30
            desde_ultimo = (datetime.now() - self._ultimo_movimiento).total_seconds() / 60
            if desde_ultimo >= minutos:
                self._timer_timeout.stop()
                QTimer.singleShot(0, lambda: (
                    QMessageBox.information(self, "⏱ Sesión expirada",
                        f"La sesión se cerró automáticamente por {minutos} minutos de inactividad."),
                    self.on_logout()
                ))
        import threading
        threading.Thread(target=_check, daemon=True).start()

    def _actualizar_badge_alertas(self):
        def _fetch():
            try:
                import requests as _req
                r = _req.get("http://localhost:8000/alertas-precio/pendientes", timeout=3)
                if r.status_code != 200:
                    return
                n = r.json().get("pendientes", 0)
                def _update():
                    btn = self.btns_menu.get("alertas")
                    if btn:
                        btn.setText(f"🔔 Alertas {f'({n})' if n > 0 else ''}")
                        btn.setStyleSheet(
                            f"""QPushButton {{
                                background: {'#7f1d1d' if n > 0 else '#16213e'};
                                color: {'#fca5a5' if n > 0 else '#a0a0b0'};
                                border: none; border-radius: 0px;
                                font-size: 13px; font-weight: {'bold' if n > 0 else 'normal'};
                                padding: 0 8px; text-align: left;
                            }}
                            QPushButton:hover {{ background: #0f3460; color: white; }}
                            QPushButton:checked {{ background: #e94560; color: white; font-weight: bold; }}"""
                        )
                QTimer.singleShot(0, _update)
            except Exception:
                pass
        import threading
        threading.Thread(target=_fetch, daemon=True).start()

    def _sync_offline(self):
        if sincronizar_cola is None:
            return
        def _sync():
            pendientes = cantidad_pendientes()
            if pendientes > 0:
                enviadas, fallidas, _ = sincronizar_cola()
                if enviadas > 0:
                    QTimer.singleShot(0, lambda: self.setWindowTitle(
                        self.windowTitle().split(" 📡")[0] + f" ✅ {enviadas} venta(s) sincronizada(s)"))
                    QTimer.singleShot(5000, lambda: self.setWindowTitle(
                        self.windowTitle().split(" ✅")[0]))
            aun_pendientes = cantidad_pendientes()
            def _titulo():
                titulo_base = self.windowTitle().split(" 📡")[0].split(" ✅")[0]
                if aun_pendientes > 0:
                    self.setWindowTitle(titulo_base + f" 📡 {aun_pendientes} offline")
                else:
                    self.setWindowTitle(titulo_base)
            QTimer.singleShot(0, _titulo)
        import threading
        threading.Thread(target=_sync, daemon=True).start()

    def mousePressEvent(self, event):
        self._ultimo_movimiento = datetime.now()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        self._ultimo_movimiento = datetime.now()
        super().keyPressEvent(event)

    def _chequear_ventas_celular(self):
        def _fetch():
            try:
                r = requests.get(f"{API_URL}/reportes/hoy", timeout=3)
                if r.status_code != 200:
                    return
                ventas = r.json().get("ventas", [])
                ventas_celular = [v for v in ventas if v.get("origen") == "celular" and v.get("estado") == "completada"]
                if not ventas_celular:
                    return
                ultima = ventas_celular[0]
                clave  = ultima.get("numero")
                if clave == self._ultima_venta_celular:
                    return
                self._ultima_venta_celular = clave
                total  = float(ultima.get("total", 0))
                metodo = ultima.get("metodo_pago", "efectivo")
                def _update():
                    self.setWindowTitle(self.windowTitle().split(" 📲")[0] + f" 📲 Celular: ${total:,.0f} ({metodo})")
                    QTimer.singleShot(8000, lambda: self.setWindowTitle(self.windowTitle().split(" 📲")[0]))
                    if hasattr(self.caja_screen, 'actualizar_ventas'):
                        self.caja_screen.actualizar_ventas()
                QTimer.singleShot(0, _update)
            except Exception:
                pass
        import threading
        threading.Thread(target=_fetch, daemon=True).start()

    def _actualizar_meta(self):
        try:
            params = {}
            if hasattr(self, 'caja_screen'):
                apertura = self.caja_screen._apertura_iso()
                if apertura:
                    from datetime import datetime as _dtn, date as _date
                    try:
                        ap_dt = _dtn.fromisoformat(apertura)
                        hoy_inicio = _dtn.combine(_date.today(), _dtn.min.time())
                        if ap_dt < hoy_inicio:
                            apertura = hoy_inicio.strftime("%Y-%m-%dT%H:%M:%S")
                    except Exception:
                        pass
                    params['desde'] = apertura
            r = requests.get(f"{API_URL}/reportes/hoy", params=params, timeout=3)
            if not r.ok:
                return
            total = float(r.json().get("total_vendido", 0))
        except Exception:
            return

        META = self._META
        pct  = min(100, int(total / META * 100))
        val  = int(min(total, META))
        col  = "#10b981" if total >= META else ("#f59e0b" if pct >= 50 else "#64748b")

        self._bar_meta.setValue(val)
        self._lbl_meta_pct.setText(f"{pct}%")
        self._lbl_meta_pct.setStyleSheet(
            f"color:{col};font-size:11px;font-weight:bold;background:transparent;min-width:36px;"
        )
        if total >= META and not getattr(self, '_meta_celebrado', False):
            self._meta_celebrado = True
            _cfg = _leer_config_logros()
            nombre = (self.cajero_actual or {}).get("nombre", "")
            fw = FuegosArtificiales(self, nombre, _cfg["titulo"], _cfg["mensaje"])
            fw.setGeometry(0, 0, self.width(), self.height())
            fw.raise_()

    def recargar_tema(self, tema_key):
        import sys as _sys
        global _T
        from ui.theme import get_qss, TEMAS
        from PyQt6.QtWidgets import QApplication

        new_t = TEMAS[tema_key]
        QApplication.instance().setStyleSheet(get_qss(new_t))

        # Parchear variables de tema directamente en cada módulo
        # Python busca globals en __dict__ del módulo en cada llamada,
        # así que setattr actualiza todos los widgets nuevos que se creen.
        _mods = [
            'ui.pantallas.login', 'ui.pantallas.turno', 'ui.pantallas.ventas',
            'ui.pantallas.productos', 'ui.pantallas.reportes', 'ui.pantallas.clientes',
            'ui.pantallas.caja', 'ui.pantallas.sesiones', 'ui.pantallas.usuarios',
            'ui.pantallas.dashboard', 'ui.pantallas.stock_avanzado',
            'ui.pantallas.precios_masivos', 'ui.pantallas.ia_screen',
            'ui.pantallas.config_screen', 'ui.pantallas.importador',
            'ui.pantallas.etiquetas.generador_etiquetas',
            'ui.pantallas.ofertas', 'ui.pantallas.precios_alerta',
        ]
        _vars = {
            '_T': None, '_BG': 'bg_app', '_CARD': 'bg_card', '_INP': 'bg_input',
            '_TXT': 'text_main', '_MUT': 'text_muted', '_PRI': 'primary',
            '_BOR': 'border', '_OK': 'success', '_DGR': 'danger',
            '_TXT_INP': 'text_input',
            'BG_MAIN': 'bg_app', 'BG_PANEL': 'bg_card', 'BORDER': 'border',
            'TEXT_MAIN': 'text_main', 'TEXT_MUTED': 'text_muted',
            'ACCENT': 'primary', 'ACCENT_OK': 'success',
        }
        for mod_name in _mods:
            mod = _sys.modules.get(mod_name)
            if mod is None:
                continue
            for attr, key in _vars.items():
                if attr == '_T':
                    if hasattr(mod, '_T') and isinstance(getattr(mod, '_T'), dict):
                        getattr(mod, '_T').update(new_t)
                elif key and hasattr(mod, attr):
                    setattr(mod, attr, new_t.get(key, getattr(mod, attr)))

        cajero = self.cajero_actual

        while self.stack.count() > 0:
            w = self.stack.widget(0)
            self.stack.removeWidget(w)
            w.deleteLater()

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
        from ui.pantallas.importador import ImportadorScreen
        from ui.pantallas.etiquetas.generador_etiquetas import GeneradorEtiquetasScreen
        from ui.pantallas.ofertas import OfertasScreen
        from ui.pantallas.precios_alerta import AlertasPrecioScreen

        self.login_screen     = LoginScreen(self.on_login_exitoso)
        self.turno_screen     = TurnoScreen(self.on_turno_seleccionado, {})
        self.ventas_screen    = VentasScreen(self.on_logout)
        self.productos_screen = ProductosScreen()
        self.reportes_screen  = ReportesScreen()
        self.clientes_screen  = ClientesScreen()
        self.caja_screen      = CajaScreen()
        self.sesiones_screen  = SesionesScreen()
        self.usuarios_screen  = UsuariosScreen()
        self.dashboard_screen = DashboardScreen()
        self.stock_screen     = StockAvanzadoScreen()
        self.precios_screen   = PreciosMasivosScreen()
        self.ia_screen        = IAScreen()
        self.config_screen    = ConfigScreen()
        self.importador_screen = ImportadorScreen()
        self.etiquetas_screen = GeneradorEtiquetasScreen()
        self.ofertas_screen   = OfertasScreen()
        self.alertas_screen   = AlertasPrecioScreen()

        self.ofertas_screen.oferta_cambiada.connect(
            lambda: self.ventas_screen.rotador_ofertas.cargar()
            if hasattr(self.ventas_screen, 'rotador_ofertas') else None
        )

        for screen in [
            self.login_screen, self.turno_screen, self.ventas_screen,
            self.productos_screen, self.reportes_screen, self.clientes_screen,
            self.caja_screen, self.sesiones_screen, self.usuarios_screen,
            self.dashboard_screen, self.stock_screen, self.precios_screen,
            self.ia_screen, self.config_screen, self.importador_screen,
            self.etiquetas_screen, self.ofertas_screen, self.alertas_screen,
        ]:
            self.stack.addWidget(screen)

        _T = new_t
        self.navbar.setStyleSheet(
            f"QFrame {{ background: {new_t['bg_navbar']}; border-radius: 0px; border-bottom: 1.5px solid {new_t['navbar_border']}; }}"
        )
        self.centralWidget().setStyleSheet(f"background-color: {new_t['bg_app']};")

        ESTILO_BTN = (
            f"QPushButton {{ background: transparent; color: {new_t['navbar_text']}; font-size: 12px; font-weight: 600;"
            f" border: none; border-radius: 8px; padding: 5px 13px; margin: 10px 2px; }}"
            f"QPushButton:hover {{ background: {new_t.get('navbar_hover_bg', new_t['bg_hover'])}; color: {new_t.get('navbar_hover_text', new_t['text_main'])}; }}"
            f"QPushButton:checked {{ background: {new_t['navbar_active_bg']}; color: {new_t['navbar_active']}; font-weight: 700; }}"
        )
        for _, btn in self.btns_menu.items():
            btn.setStyleSheet(ESTILO_BTN)

        if cajero:
            self.on_turno_seleccionado(cajero)
        else:
            self.stack.setCurrentWidget(self.login_screen)

    def _chequear_actualizacion(self):
        def _run():
            try:
                import urllib.request, json as _j, ssl, time, sys, os
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                ts  = int(time.time())
                url = f"https://raw.githubusercontent.com/milenamondaca17-gif/juana-cash/main/version.json?t={ts}"
                data = _j.loads(urllib.request.urlopen(url, timeout=8, context=ctx).read().decode())
                v_gh = data.get("desktop_version", data.get("version", "0.0.0"))

                v_local = "0.0.0"
                for p in [os.path.join(os.path.dirname(sys.executable), "version.json"),
                          os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "version.json"))]:
                    if os.path.exists(p):
                        v_local = _j.load(open(p, encoding="utf-8")).get("version", "0.0.0")
                        break

                if [int(x) for x in v_gh.split(".")] <= [int(x) for x in v_local.split(".")]:
                    return

                installer_url = data.get("installer_url", "")

                def _preguntar():
                    from PyQt6.QtWidgets import QMessageBox
                    r = QMessageBox.question(
                        self, "Actualización disponible",
                        f"Nueva versión disponible: v{v_gh}  (tenés v{v_local})\n\n"
                        "¿Actualizar ahora?\n"
                        "La app se cierra, instala y vuelve a abrir sola.",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if r == QMessageBox.StandardButton.Yes:
                        self._descargar_e_instalar(installer_url, v_gh)
                QTimer.singleShot(0, _preguntar)
            except Exception:
                pass
        import threading
        threading.Thread(target=_run, daemon=True).start()

    def _descargar_e_instalar(self, installer_url, version_nueva):
        from PyQt6.QtWidgets import QProgressDialog
        prog = QProgressDialog(f"Descargando v{version_nueva}...", None, 0, 100, self)
        prog.setWindowTitle("Actualizando Juana Cash")
        prog.setWindowModality(Qt.WindowModality.ApplicationModal)
        prog.setMinimumDuration(0)
        prog.setValue(0)
        prog.show()

        def _download():
            try:
                import urllib.request, tempfile, subprocess, ssl
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode    = ssl.CERT_NONE
                _tf  = tempfile.NamedTemporaryFile(delete=False, suffix=".exe", prefix="JuanaCash_Update_")
                tmp  = _tf.name
                _tf.close()
                with urllib.request.urlopen(installer_url, context=ctx) as r:
                    total      = int(r.headers.get("Content-Length") or 0)
                    descargado = 0
                    with open(tmp, "wb") as f:
                        while True:
                            chunk = r.read(65536)
                            if not chunk:
                                break
                            f.write(chunk)
                            descargado += len(chunk)
                            if total > 0:
                                pct = int(descargado / total * 100)
                                QTimer.singleShot(0, lambda p=pct: prog.setValue(p))
                DETACHED = 0x00000008 | 0x00000200
                subprocess.Popen([tmp, "/VERYSILENT", "/NORESTART", "/CLOSEAPPLICATIONS"], creationflags=DETACHED)
                QTimer.singleShot(2000, QApplication.instance().quit)
            except Exception as e:
                def _err():
                    prog.close()
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.warning(self, "Error de actualización",
                        f"No se pudo descargar:\n{e}\n\nCerrá y abrí la app para intentar de nuevo.")
                QTimer.singleShot(0, _err)
        import threading
        threading.Thread(target=_download, daemon=True).start()

    def on_logout(self):
        self.usuario_actual = None
        self.cajero_actual = None
        self.navbar.hide()
        self._meta_bar.hide()
        self._bar_meta.setValue(0)
        self._lbl_meta_pct.setText("0%")
        self._meta_celebrado = False
        self.stack.setCurrentWidget(self.login_screen)
        self.setWindowTitle("Juana Cash - Sistema POS")
        if hasattr(self, '_timer_timeout'):
            self._timer_timeout.stop()
        if hasattr(self, '_timer_meta'):
            self._timer_meta.stop()
        if hasattr(self, '_timer_celular'):
            self._timer_celular.stop()