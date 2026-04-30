import os
import requests
from datetime import datetime
from PyQt6.QtWidgets import (QMainWindow, QStackedWidget, QWidget, QHBoxLayout,
                             QVBoxLayout, QPushButton, QLabel, QMessageBox,
                             QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QFrame)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QIcon
from ui.theme import get_tema, TEMAS, guardar_tema

_T = get_tema()

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
        self.setMinimumSize(1280, 720)
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
        self.navbar.setFixedHeight(60)
        self.navbar.setStyleSheet(
            f"background-color: {_T['bg_navbar']}; border-bottom: 2px solid {_T['border']};"
        )
        self.navbar.hide()
        
        navbar_layout = QHBoxLayout(self.navbar)
        navbar_layout.setContentsMargins(15, 0, 15, 0)
        navbar_layout.setSpacing(5)

        logo = QLabel("JUANA CASH")
        logo.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        logo.setStyleSheet(f"color: {_T['logo_color']}; border: none; font-weight: bold; letter-spacing: 1px;")
        navbar_layout.addWidget(logo)

        navbar_layout.addSpacing(30)

        self.btns_menu = {}
        self.menus_admin = ["usuarios", "sesiones", "dashboard", "stock", "precios", "ia", "importador", "etiquetas", "ofertas", "alertas"]

        # Pestañas siempre visibles
        menus_principales = [
            ("🛒 Ventas",    "ventas"),
            ("🧾 Caja",      "caja"),
            ("📦 Productos", "productos"),
            ("👥 Clientes",  "clientes"),
            ("📈 Dashboard", "dashboard"),
            ("🔔 Alertas",   "alertas"),
            ("📊 Reportes",  "reportes"),
            ("🏷️ Ofertas",   "ofertas"),
        ]

        # Pestañas dentro de Config (ocultas por defecto)
        menus_config = [
            ("🖨️ Etiquetas",  "etiquetas"),
            ("📋 Stock",      "stock"),
            ("💰 Precios",    "precios"),
            ("📥 Importar",   "importador"),
            ("🤖 IA",         "ia"),
            ("👤 Usuarios",   "usuarios"),
        ]

        ESTILO_BTN = f"""
            QPushButton {{ background: transparent; color: {_T['navbar_text']}; font-size: 13px; font-weight: bold; border: none; padding: 0 12px; border-bottom: 3px solid transparent; border-radius: 0px; }}
            QPushButton:hover {{ color: {_T['text_main']}; background: {_T['bg_hover']}; border-bottom: 3px solid {_T['border']}; }}
            QPushButton:checked {{ color: {_T['navbar_active']}; background: {_T['navbar_active_bg']}; border-bottom: 3px solid {_T['navbar_border']}; }}
        """
        ESTILO_CONFIG = f"""
            QPushButton {{ background: {_T['bg_hover']}; color: {_T['navbar_text']}; font-size: 12px; font-weight: bold; border: none; padding: 0 10px; border-bottom: 3px solid transparent; border-left: 3px solid {_T['border']}; border-radius: 0px; }}
            QPushButton:hover {{ color: {_T['text_main']}; background: {_T['bg_selected']}; border-bottom: 3px solid {_T['border']}; }}
            QPushButton:checked {{ color: {_T['navbar_active']}; background: {_T['navbar_active_bg']}; border-bottom: 3px solid {_T['navbar_border']}; }}
        """

        for texto, key in menus_principales:
            btn = QPushButton(texto)
            btn.setFixedHeight(60)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(ESTILO_BTN)
            btn.clicked.connect(lambda _, k=key: self.cambiar_pantalla(k))
            navbar_layout.addWidget(btn)
            self.btns_menu[key] = btn

        # Botón Config toggle
        self._config_expandido = False
        self._btns_config_ocultos = []

        btn_config_toggle = QPushButton("⚙️ Config  ▾")
        btn_config_toggle.setFixedHeight(60)
        btn_config_toggle.setCheckable(True)
        btn_config_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_config_toggle.setStyleSheet(ESTILO_BTN)
        navbar_layout.addWidget(btn_config_toggle)
        self.btns_menu["config"] = btn_config_toggle

        # Crear botones ocultos de config
        for texto, key in menus_config:
            btn = QPushButton(texto)
            btn.setFixedHeight(52)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(ESTILO_CONFIG)
            btn.setVisible(False)
            btn.clicked.connect(lambda _, k=key: self.cambiar_pantalla(k))
            navbar_layout.addWidget(btn)
            self.btns_menu[key] = btn
            self._btns_config_ocultos.append(btn)

        def _toggle_config(checked):
            self._config_expandido = not self._config_expandido
            for b in self._btns_config_ocultos:
                b.setVisible(self._config_expandido)
            btn_config_toggle.setText("⚙️ Config  ▴" if self._config_expandido else "⚙️ Config  ▾")
            if checked:
                self.cambiar_pantalla("config")

        btn_config_toggle.clicked.connect(_toggle_config)

        navbar_layout.addStretch()

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
            lbl_ver.setStyleSheet(f"color: {_T['text_muted']}; font-size: 11px; border: none; margin-right: 10px;")
            navbar_layout.addWidget(lbl_ver)

        self.lbl_cajero_navbar = QLabel("")
        self.lbl_cajero_navbar.setStyleSheet(f"color: {_T['text_main']}; font-size: 13px; border: none; margin-right: 15px; font-weight: bold;")
        navbar_layout.addWidget(self.lbl_cajero_navbar)

        btn_salir = QPushButton("Salir")
        btn_salir.setFixedHeight(34)
        btn_salir.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_salir.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {_T['text_muted']}; font-size: 13px; font-weight: bold; border: 1.5px solid {_T['border']}; border-radius: 8px; padding: 0 15px; }}
            QPushButton:hover {{ background: {_T['danger']}; color: white; border-color: {_T['danger']}; }}
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
        self.importador_screen = ImportadorScreen()
        self.etiquetas_screen = GeneradorEtiquetasScreen()
        self.ofertas_screen = OfertasScreen()

        # Cuando se agrega/borra una oferta, el rotador se actualiza automáticamente
        self.ofertas_screen.oferta_cambiada.connect(
            lambda: self.ventas_screen.rotador_ofertas.cargar()
            if hasattr(self.ventas_screen, 'rotador_ofertas') else None
        )

        self.alertas_screen = AlertasPrecioScreen()

        for screen in [
            self.login_screen, self.turno_screen, self.ventas_screen,
            self.productos_screen, self.reportes_screen, self.clientes_screen,
            self.caja_screen, self.sesiones_screen, self.usuarios_screen,
            self.dashboard_screen,
            self.stock_screen,
            self.precios_screen,
            self.ia_screen,
            self.config_screen,
            self.importador_screen,
            self.etiquetas_screen,
            self.ofertas_screen,
            self.alertas_screen,
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
            "importador": self.importador_screen,
            "etiquetas": self.etiquetas_screen,
            "ofertas":   self.ofertas_screen,
            "alertas":   self.alertas_screen,
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

        # Timer para detectar ventas nuevas del celular
        if not hasattr(self, '_timer_celular'):
            self._timer_celular = QTimer()
            self._timer_celular.timeout.connect(self._chequear_ventas_celular)
        self._ultima_venta_celular = None
        self._timer_celular.start(15000)  # cada 15 segundos
        
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

        # Timer badge alertas de precios
        if not hasattr(self, '_timer_alertas'):
            self._timer_alertas = QTimer()
            self._timer_alertas.timeout.connect(self._actualizar_badge_alertas)
        self._timer_alertas.start(20000)
        self._actualizar_badge_alertas()
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
            f"background-color: {new_t['bg_navbar']}; border-bottom: 2px solid {new_t['border']};"
        )
        self.centralWidget().setStyleSheet(f"background-color: {new_t['bg_app']};")

        ESTILO_BTN = f"""
            QPushButton {{ background: transparent; color: {new_t['navbar_text']}; font-size: 13px; font-weight: bold; border: none; padding: 0 12px; border-bottom: 3px solid transparent; border-radius: 0px; }}
            QPushButton:hover {{ color: {new_t['text_main']}; background: {new_t['bg_hover']}; border-bottom: 3px solid {new_t['border']}; }}
            QPushButton:checked {{ color: {new_t['navbar_active']}; background: {new_t['navbar_active_bg']}; border-bottom: 3px solid {new_t['navbar_border']}; }}
        """
        ESTILO_CONFIG = f"""
            QPushButton {{ background: {new_t['bg_hover']}; color: {new_t['navbar_text']}; font-size: 12px; font-weight: bold; border: none; padding: 0 10px; border-bottom: 3px solid transparent; border-left: 3px solid {new_t['border']}; border-radius: 0px; }}
            QPushButton:hover {{ color: {new_t['text_main']}; background: {new_t['bg_selected']}; border-bottom: 3px solid {new_t['border']}; }}
            QPushButton:checked {{ color: {new_t['navbar_active']}; background: {new_t['navbar_active_bg']}; border-bottom: 3px solid {new_t['navbar_border']}; }}
        """
        for _, btn in self.btns_menu.items():
            if btn in self._btns_config_ocultos:
                btn.setStyleSheet(ESTILO_CONFIG)
            else:
                btn.setStyleSheet(ESTILO_BTN)

        if cajero:
            self.on_turno_seleccionado(cajero)
        else:
            self.stack.setCurrentWidget(self.login_screen)

    def on_logout(self):
        self.usuario_actual = None
        self.cajero_actual = None
        self.navbar.hide()
        self.stack.setCurrentWidget(self.login_screen)
        self.setWindowTitle("Juana Cash - Sistema POS")
        if hasattr(self, '_timer_timeout'):
            self._timer_timeout.stop()
        if hasattr(self, '_timer_celular'):
            self._timer_celular.stop()