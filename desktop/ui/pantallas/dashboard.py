import requests
import json
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QFrame, QScrollArea, QGridLayout,
                             QSizePolicy, QTableWidget, QTableWidgetItem,
                             QHeaderView, QTabWidget)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPainter, QColor, QPen
from datetime import datetime, date, timedelta
from ui.theme import get_tema

_T = get_tema()
API_URL = "http://127.0.0.1:8000"

def _p(v):
    return f"${float(v):,.0f}".replace(",", ".")

def _tf(val):
    try: return float(val)
    except: return 0.0

def _ti(val):
    try: return int(val)
    except: return 0

NOMBRES_METODO = {
    "efectivo":       "💵 Efectivo",
    "tarjeta":        "💳 Tarjeta",
    "mercadopago_qr": "📱 QR/MP",
    "transferencia":  "🏦 Transf.",
    "debito":         "🏧 Débito",
    "fiado":          "💸 Fiado",
}
COLORES_METODO = {
    "efectivo":       "#27ae60",
    "tarjeta":        "#3498db",
    "mercadopago_qr": "#009ee3",
    "transferencia":  "#9b59b6",
    "debito":         "#1abc9c",
    "fiado":          "#e74c3c",
}
DIAS_ES = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]


# ── Widgets auxiliares ────────────────────────────────────────────────────────

class BarraHora(QWidget):
    def __init__(self, hora, ventas, max_ventas, parent=None):
        super().__init__(parent)
        self.hora = hora
        self.ventas = ventas
        self.max_ventas = max_ventas
        self.setFixedWidth(28)
        self.setMinimumHeight(80)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        if self.max_ventas > 0 and self.ventas > 0:
            ratio = self.ventas / self.max_ventas
            bar_h = int((h - 20) * ratio)
            color = QColor("#e94560") if ratio >= 0.8 else QColor("#f39c12") if ratio >= 0.5 else QColor("#3498db")
            painter.fillRect(2, h - 20 - bar_h, w - 4, bar_h, color)
        painter.setPen(QColor("#a0a0b0"))
        painter.setFont(QFont("Arial", 7))
        painter.drawText(0, h - 5, w, 15, Qt.AlignmentFlag.AlignCenter, f"{self.hora:02d}")


class BarraDia(QWidget):
    """Barra vertical para el gráfico de tendencia semanal."""
    def __init__(self, label, valor, max_v, es_hoy=False, parent=None):
        super().__init__(parent)
        self.label = label
        self.valor = valor
        self.max_v = max_v
        self.es_hoy = es_hoy
        self.setFixedWidth(38)
        self.setMinimumHeight(90)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        pad_bottom = 28

        if self.max_v > 0 and self.valor > 0:
            ratio = self.valor / self.max_v
            bar_h = int((h - pad_bottom - 4) * ratio)
            color = QColor("#D4A017") if self.es_hoy else QColor("#3498db")
            painter.fillRect(4, h - pad_bottom - bar_h, w - 8, bar_h, color)
            # Valor encima de la barra
            painter.setPen(QColor("#D4A017") if self.es_hoy else QColor("#a0a0b0"))
            painter.setFont(QFont("Arial", 6))
            val_txt = f"${self.valor/1000:.0f}k" if self.valor >= 1000 else f"${self.valor:.0f}"
            painter.drawText(0, h - pad_bottom - bar_h - 14, w, 14,
                             Qt.AlignmentFlag.AlignCenter, val_txt)

        painter.setPen(QColor("#D4A017") if self.es_hoy else QColor("#a0a0b0"))
        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold if self.es_hoy else QFont.Weight.Normal))
        painter.drawText(0, h - pad_bottom + 4, w, 20, Qt.AlignmentFlag.AlignCenter, self.label)


class KPICard(QFrame):
    def __init__(self, icono, titulo, valor, color, subtitulo="", parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background: {_T['bg_card']};
                border-radius: 14px;
                border: 1.5px solid {_T['border_card']};
                border-left: 5px solid {color};
            }}
        """)
        self.setMinimumHeight(100)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(3)
        hdr = QHBoxLayout()
        lbl_icon = QLabel(icono)
        lbl_icon.setStyleSheet("font-size: 18px; background: transparent; border: none;")
        hdr.addWidget(lbl_icon)
        hdr.addStretch()
        self.lbl_titulo = QLabel(titulo)
        self.lbl_titulo.setStyleSheet(
            f"color: {_T['text_muted']}; font-size: 10px; font-weight: bold; "
            f"background: transparent; border: none; letter-spacing: 0.5px;")
        layout.addLayout(hdr)
        layout.addWidget(self.lbl_titulo)
        self.lbl_valor = QLabel(valor)
        self.lbl_valor.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self.lbl_valor.setStyleSheet(f"color: {color}; background: transparent; border: none;")
        layout.addWidget(self.lbl_valor)
        if subtitulo:
            self.lbl_sub = QLabel(subtitulo)
            self.lbl_sub.setStyleSheet(
                f"color: {_T['text_muted']}; font-size: 10px; background: transparent; border: none;")
            layout.addWidget(self.lbl_sub)
        else:
            self.lbl_sub = None

    def actualizar(self, valor, subtitulo=""):
        self.lbl_valor.setText(valor)
        if self.lbl_sub and subtitulo:
            self.lbl_sub.setText(subtitulo)


# ── Dashboard principal ───────────────────────────────────────────────────────

class DashboardScreen(QWidget):
    datos_recibidos = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.datos = None
        self._cargando = False
        self._request_id = 0
        self.setup_ui()
        self.datos_recibidos.connect(self._aplicar_datos)
        self.timer = QTimer()
        self.timer.timeout.connect(self._cargar_datos_hilo)
        self.timer.start(30000)

    def _cargar_datos_hilo(self):
        if self._cargando:
            return
        self._cargando = True
        self._request_id += 1
        import threading
        threading.Thread(target=self._fetch_datos, args=(self._request_id,), daemon=True).start()

    def _fetch_datos(self, req_id):
        import concurrent.futures
        datos = {}
        try:
            def get_dash():
                r = requests.get(f"{API_URL}/reportes/dashboard", timeout=5)
                return r.json() if r.ok else {}
            def get_horas():
                r = requests.get(f"{API_URL}/reportes/horario-pico", timeout=5)
                return r.json() if r.ok else []
            def get_turnos():
                r = requests.get(f"{API_URL}/caja/turnos-hoy", timeout=5)
                return r.json() if r.ok else []
            def get_insights():
                r = requests.get(f"{API_URL}/ia/insights-hoy", timeout=5)
                return r.json() if r.ok else {}
            def get_tendencia():
                r = requests.get(f"{API_URL}/caja/historial-efectivo?dias=8", timeout=5)
                return r.json() if r.ok else []

            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
                fd = ex.submit(get_dash)
                fh = ex.submit(get_horas)
                ft = ex.submit(get_turnos)
                fi = ex.submit(get_insights)
                fte = ex.submit(get_tendencia)
                datos          = fd.result(timeout=7)
                datos["horas_hoy"] = fh.result(timeout=7)
                datos["turnos_hoy"] = ft.result(timeout=7)
                datos["insights"]   = fi.result(timeout=7)
                datos["tendencia"]  = fte.result(timeout=7)

            if req_id == self._request_id:
                self.datos_recibidos.emit(datos)
        except Exception as e:
            print(f"[Dashboard] Error: {e}")
        finally:
            self._cargando = False

    def _aplicar_datos(self, datos):
        self.datos = datos
        self.lbl_hora.setText(f"Actualizado: {datetime.now().strftime('%H:%M:%S')}")
        self.actualizar_ui()

    # ── UI ────────────────────────────────────────────────────────────────────

    def setup_ui(self):
        self.setStyleSheet(f"background-color: {_T['bg_app']}; color: {_T['text_main']};")
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # Header
        hdr = QHBoxLayout()
        titulo = QLabel("📊 Dashboard")
        titulo.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        titulo.setStyleSheet(f"color: {_T['text_main']}; background: transparent;")
        hdr.addWidget(titulo)
        hdr.addStretch()
        self.lbl_hora = QLabel("")
        self.lbl_hora.setStyleSheet(f"color: {_T['text_muted']}; font-size: 11px; background: transparent;")
        hdr.addWidget(self.lbl_hora)
        btn_refresh = QPushButton("⟳ Actualizar")
        btn_refresh.setFixedHeight(34)
        btn_refresh.setStyleSheet(f"""
            QPushButton {{ background: {_T['primary_light']}; color: {_T['primary']};
                border-radius: 8px; font-size: 12px; padding: 0 14px;
                border: 1.5px solid {_T['primary']}; font-weight: bold; }}
            QPushButton:hover {{ background: {_T['primary']}; color: white; }}
        """)
        btn_refresh.clicked.connect(self.cargar_datos)
        hdr.addWidget(btn_refresh)
        root.addLayout(hdr)

        # Scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea {{ border: none; background: {_T['bg_app']}; }}")
        contenido = QWidget()
        contenido.setStyleSheet(f"background: {_T['bg_app']};")
        self.cl = QVBoxLayout(contenido)
        self.cl.setSpacing(12)
        self.cl.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(contenido)
        root.addWidget(scroll)

        CARD = f"QFrame {{ background: {_T['bg_card']}; border-radius: 14px; border: 1.5px solid {_T['border_card']}; }}"
        LBL  = f"color: {_T['text_muted']}; font-size: 11px; font-weight: bold; background: transparent; border: none; letter-spacing: 0.5px;"

        # ── 1. KPI Cards (5) ─────────────────────────────────────────────────
        grid_kpi = QGridLayout()
        grid_kpi.setSpacing(10)
        self.card_total   = KPICard("💰", "VENTAS HOY",      "$0",  "#e94560", "-")
        self.card_var     = KPICard("📈", "VS AYER",          "—",   "#f39c12")
        self.card_tickets = KPICard("🧾", "TICKETS",          "0",   "#3498db")
        self.card_prom    = KPICard("💳", "TICKET PROMEDIO",  "$0",  "#27ae60")
        self.card_proy    = KPICard("🎯", "PROYECCIÓN DÍA",   "$—",  "#9b59b6")
        for col, card in enumerate([self.card_total, self.card_var, self.card_tickets,
                                     self.card_prom, self.card_proy]):
            grid_kpi.addWidget(card, 0, col)
        self.cl.addLayout(grid_kpi)

        # ── 2. Tendencia 7 días + Turno activo ───────────────────────────────
        fila_tend = QHBoxLayout()
        fila_tend.setSpacing(12)

        self.panel_tend = QFrame()
        self.panel_tend.setStyleSheet(CARD)
        tend_lay = QVBoxLayout(self.panel_tend)
        tend_lay.setContentsMargins(18, 14, 18, 14)
        tend_lay.setSpacing(8)
        lbl_tend = QLabel("📅 Tendencia últimos 7 días")
        lbl_tend.setStyleSheet(LBL)
        tend_lay.addWidget(lbl_tend)
        self.barras_tend = QHBoxLayout()
        self.barras_tend.setSpacing(4)
        self.barras_tend.setAlignment(Qt.AlignmentFlag.AlignLeft)
        tend_lay.addLayout(self.barras_tend)
        fila_tend.addWidget(self.panel_tend, 3)

        self.panel_turno = QFrame()
        self.panel_turno.setStyleSheet(CARD)
        turno_lay = QVBoxLayout(self.panel_turno)
        turno_lay.setContentsMargins(18, 14, 18, 14)
        turno_lay.setSpacing(6)
        lbl_turno_t = QLabel("🔴 Turno activo ahora")
        lbl_turno_t.setStyleSheet(LBL)
        turno_lay.addWidget(lbl_turno_t)
        self.lbl_cajero_act  = QLabel("Sin turno abierto")
        self.lbl_cajero_act.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.lbl_cajero_act.setStyleSheet(f"color:{_T['text_main']}; background:transparent; border:none;")
        turno_lay.addWidget(self.lbl_cajero_act)
        self.lbl_turno_det = QLabel("")
        self.lbl_turno_det.setStyleSheet(f"color:{_T['text_muted']}; font-size:11px; background:transparent; border:none;")
        self.lbl_turno_det.setWordWrap(True)
        turno_lay.addWidget(self.lbl_turno_det)
        turno_lay.addStretch()
        fila_tend.addWidget(self.panel_turno, 2)

        self.cl.addLayout(fila_tend)

        # ── 3. Métodos de pago + Top productos (tabs Hoy / Año) ──────────────
        fila3 = QHBoxLayout()
        fila3.setSpacing(12)

        self.panel_metodos = QFrame()
        self.panel_metodos.setStyleSheet(CARD)
        self.panel_metodos.setMinimumHeight(200)
        met_lay = QVBoxLayout(self.panel_metodos)
        met_lay.setContentsMargins(18, 14, 18, 14)
        met_lay.setSpacing(8)
        lbl_m = QLabel("💳 Desglose por método de pago")
        lbl_m.setStyleSheet(LBL)
        met_lay.addWidget(lbl_m)
        self.metodos_contenido = QVBoxLayout()
        self.metodos_contenido.setSpacing(8)
        met_lay.addLayout(self.metodos_contenido)
        met_lay.addStretch()
        fila3.addWidget(self.panel_metodos, 1)

        self.panel_top = QFrame()
        self.panel_top.setStyleSheet(CARD)
        top_lay_outer = QVBoxLayout(self.panel_top)
        top_lay_outer.setContentsMargins(18, 14, 18, 14)
        top_lay_outer.setSpacing(6)
        lbl_top_t = QLabel("🏆 Top productos")
        lbl_top_t.setStyleSheet(LBL)
        top_lay_outer.addWidget(lbl_top_t)

        self.tabs_top = QTabWidget()
        self.tabs_top.setStyleSheet(f"""
            QTabWidget::pane {{ border: none; background: transparent; }}
            QTabBar::tab {{ background: {_T['bg_app']}; color: {_T['text_muted']};
                padding: 5px 14px; border-radius: 6px; margin-right: 4px; font-size: 11px; }}
            QTabBar::tab:selected {{ background: {_T['primary']}; color: white; font-weight: bold; }}
        """)

        tab_hoy = QWidget(); tab_hoy.setStyleSheet("background: transparent;")
        self.top_hoy_lay = QVBoxLayout(tab_hoy)
        self.top_hoy_lay.setSpacing(4)
        self.top_hoy_lay.setContentsMargins(0, 6, 0, 0)
        self.tabs_top.addTab(tab_hoy, "Hoy")

        tab_anio = QWidget(); tab_anio.setStyleSheet("background: transparent;")
        self.top_anio_lay = QVBoxLayout(tab_anio)
        self.top_anio_lay.setSpacing(4)
        self.top_anio_lay.setContentsMargins(0, 6, 0, 0)
        self.tabs_top.addTab(tab_anio, "Año")

        top_lay_outer.addWidget(self.tabs_top)
        fila3.addWidget(self.panel_top, 1)
        self.cl.addLayout(fila3)

        # ── 4. Horario pico HOY ───────────────────────────────────────────────
        self.panel_horario = QFrame()
        self.panel_horario.setStyleSheet(CARD)
        hor_lay = QVBoxLayout(self.panel_horario)
        hor_lay.setContentsMargins(18, 14, 18, 14)
        hor_lay.setSpacing(8)
        h_hdr = QHBoxLayout()
        lbl_h = QLabel("🕐 Horario pico — hoy")
        lbl_h.setStyleSheet(LBL)
        h_hdr.addWidget(lbl_h)
        h_hdr.addStretch()
        self.lbl_pico = QLabel("")
        self.lbl_pico.setStyleSheet(f"color:{_T['danger']}; font-size:12px; font-weight:bold; background:transparent;")
        h_hdr.addWidget(self.lbl_pico)
        hor_lay.addLayout(h_hdr)
        self.barras_container = QHBoxLayout()
        self.barras_container.setSpacing(2)
        self.barras_container.setAlignment(Qt.AlignmentFlag.AlignLeft)
        hor_lay.addLayout(self.barras_container)
        lbl_leyenda = QLabel("🔴 Hora pico   🟡 Moderado   🔵 Tranquilo")
        lbl_leyenda.setStyleSheet(f"color:{_T['text_muted']}; font-size:10px; background:transparent;")
        hor_lay.addWidget(lbl_leyenda)
        self.cl.addWidget(self.panel_horario)

        # ── 5. Turnos del día ─────────────────────────────────────────────────
        self.panel_turnos = QFrame()
        self.panel_turnos.setStyleSheet(CARD)
        turnos_lay = QVBoxLayout(self.panel_turnos)
        turnos_lay.setContentsMargins(18, 14, 18, 14)
        turnos_lay.setSpacing(8)
        lbl_turnos = QLabel("👥 Turnos del día")
        lbl_turnos.setStyleSheet(f"color:{_T['text_main']}; font-size:14px; font-weight:bold; background:transparent;")
        turnos_lay.addWidget(lbl_turnos)
        self.tabla_turnos = QTableWidget()
        self.tabla_turnos.setColumnCount(7)
        self.tabla_turnos.setHorizontalHeaderLabels(
            ["Cajero", "Apertura", "Cierre", "Estado", "Tickets", "Total", "Dif. Caja"])
        self.tabla_turnos.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for c in range(1, 7):
            self.tabla_turnos.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla_turnos.setMaximumHeight(200)
        self.tabla_turnos.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_turnos.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tabla_turnos.setAlternatingRowColors(True)
        self.tabla_turnos.setStyleSheet(f"""
            QTableWidget {{ background:{_T['bg_card']}; border:none; gridline-color:{_T['border_card']}; }}
            QHeaderView::section {{ background:{_T['bg_app']}; color:{_T['text_muted']};
                padding:6px; border:none; font-size:10px; font-weight:bold; }}
            QTableWidgetItem {{ color:{_T['text_main']}; padding:4px; }}
            QTableWidget::item:alternate {{ background:rgba(255,255,255,0.03); }}
        """)
        turnos_lay.addWidget(self.tabla_turnos)
        self.cl.addWidget(self.panel_turnos)

        # ── 6. Historial detallado ────────────────────────────────────────────
        self.panel_hist = QFrame()
        self.panel_hist.setStyleSheet(CARD)
        hist_lay = QVBoxLayout(self.panel_hist)
        hist_lay.setContentsMargins(18, 14, 18, 14)
        hdr_h = QHBoxLayout()
        lbl_hh = QLabel("📋 Historial de productos vendidos")
        lbl_hh.setStyleSheet(f"color:{_T['text_main']}; font-size:14px; font-weight:bold; background:transparent;")
        hdr_h.addWidget(lbl_hh)
        hdr_h.addStretch()
        BTN_F = f"""
            QPushButton {{ background:{_T['primary_light']}; color:{_T['primary']}; border-radius:6px;
                font-size:10px; font-weight:bold; border:1.5px solid {_T['primary']}; }}
            QPushButton:hover {{ background:{_T['primary']}; color:white; }}
            QPushButton:checked {{ background:{_T['primary']}; color:white; }}
        """
        self.btn_ver_dia = QPushButton("Día")
        self.btn_ver_sem = QPushButton("Semana")
        self.btn_ver_mes = QPushButton("Mes")
        for b in [self.btn_ver_dia, self.btn_ver_sem, self.btn_ver_mes]:
            b.setFixedSize(70, 28)
            b.setStyleSheet(BTN_F)
        hdr_h.addWidget(self.btn_ver_dia)
        hdr_h.addWidget(self.btn_ver_sem)
        hdr_h.addWidget(self.btn_ver_mes)
        hist_lay.addLayout(hdr_h)
        self.tabla_hist = QTableWidget()
        self.tabla_hist.setColumnCount(4)
        self.tabla_hist.setHorizontalHeaderLabels(["Fecha", "Producto", "Cant.", "Total $"])
        self.tabla_hist.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_hist.setMinimumHeight(300)
        self.tabla_hist.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_hist.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tabla_hist.setStyleSheet(f"""
            QTableWidget {{ background:{_T['bg_card']}; border:none; gridline-color:{_T['border_card']}; }}
            QHeaderView::section {{ background:{_T['bg_app']}; color:{_T['text_muted']};
                padding:6px; border:none; font-size:10px; font-weight:bold; }}
            QTableWidgetItem {{ color:{_T['text_main']}; padding:4px; }}
        """)
        hist_lay.addWidget(self.tabla_hist)
        self.cl.addWidget(self.panel_hist)
        self.cl.addStretch()

        self.btn_ver_dia.clicked.connect(lambda: self.cargar_ventas_periodo("dia"))
        self.btn_ver_sem.clicked.connect(lambda: self.cargar_ventas_periodo("semana"))
        self.btn_ver_mes.clicked.connect(lambda: self.cargar_ventas_periodo("mes"))

    # ── Datos → UI ────────────────────────────────────────────────────────────

    def cargar_datos(self):
        self._cargar_datos_hilo()

    def actualizar_ui(self):
        if not self.datos or not isinstance(self.datos, dict):
            return
        d = self.datos

        # ── KPIs ────────────────────────────────────────────────────────────
        total   = _tf(d.get("total_hoy"))
        var     = _tf(d.get("variacion_pct"))
        tickets = _ti(d.get("tickets_hoy"))
        prom    = _tf(d.get("ticket_promedio"))

        self.card_total.actualizar(_p(total))

        signo_v = "▲" if var >= 0 else "▼"
        col_v   = "#27ae60" if var >= 0 else "#e94560"
        self.card_var.actualizar(f"{signo_v} {abs(var):.1f}%", "respecto a ayer")
        self.card_var.lbl_valor.setStyleSheet(
            f"color:{col_v}; font-size:20px; font-weight:bold; background:transparent; border:none;")

        self.card_tickets.actualizar(str(tickets))
        self.card_prom.actualizar(_p(prom))

        ins = d.get("insights") or {}
        proyecc = ins.get("proyeccion_dia")
        self.card_proy.actualizar(_p(proyecc) if proyecc else "—",
                                  "a ritmo actual" if proyecc else "sin ventas aún")

        # ── Tendencia 7 días ─────────────────────────────────────────────────
        while self.barras_tend.count():
            c = self.barras_tend.takeAt(0)
            if c.widget(): c.widget().deleteLater()

        tendencia = d.get("tendencia") or []
        ultimos7  = list(reversed(tendencia[:7])) if tendencia else []
        hoy_str   = str(date.today())
        max_tend  = max((_tf(x.get("total", 0)) for x in ultimos7), default=1) or 1
        for x in ultimos7:
            fecha = x.get("fecha", "")
            try:
                dia_idx = datetime.strptime(fecha, "%Y-%m-%d").weekday()
                lbl = DIAS_ES[dia_idx]
            except Exception:
                lbl = fecha[-2:]
            barra = BarraDia(lbl, _tf(x.get("total", 0)), max_tend, es_hoy=(fecha == hoy_str))
            self.barras_tend.addWidget(barra)

        # ── Turno activo ─────────────────────────────────────────────────────
        turnos = d.get("turnos_hoy") or []
        turno_abierto = next((t for t in turnos if t.get("estado") == "abierto"), None)
        if turno_abierto:
            cajero   = turno_abierto.get("cajero", "?")
            apertura = turno_abierto.get("apertura", "")[-5:]
            tot_t    = _tf(turno_abierto.get("total_vendido", 0))
            tix_t    = _ti(turno_abierto.get("cantidad_ventas", 0))
            self.lbl_cajero_act.setText(f"👤 {cajero}")
            self.lbl_turno_det.setText(
                f"Desde las {apertura} hs\n"
                f"Tickets: {tix_t}  |  Vendido: {_p(tot_t)}"
            )
            self.panel_turno.setStyleSheet(
                f"QFrame {{ background:{_T['bg_card']}; border-radius:14px; "
                f"border:1.5px solid #27ae60; }}")
        else:
            self.lbl_cajero_act.setText("Sin turno abierto")
            self.lbl_turno_det.setText("")
            self.panel_turno.setStyleSheet(
                f"QFrame {{ background:{_T['bg_card']}; border-radius:14px; "
                f"border:1.5px solid {_T['border_card']}; }}")

        # ── Métodos de pago ──────────────────────────────────────────────────
        while self.metodos_contenido.count():
            c = self.metodos_contenido.takeAt(0)
            if c.widget(): c.widget().deleteLater()

        desglose = d.get("desglose_metodos") or {}
        if not desglose:
            lbl_sin = QLabel("Sin ventas registradas hoy")
            lbl_sin.setStyleSheet(f"color:{_T['text_muted']}; font-size:12px; background:transparent;")
            self.metodos_contenido.addWidget(lbl_sin)
        else:
            total_met = sum(_tf(v) for v in desglose.values()) or 1
            MAX_W = 220
            for metodo, monto in sorted(desglose.items(), key=lambda x: _tf(x[1]), reverse=True):
                monto_f = _tf(monto)
                pct     = (monto_f / total_met) * 100
                nombre  = NOMBRES_METODO.get(metodo, metodo)
                color   = COLORES_METODO.get(metodo, "#95a5a6")

                fila = QFrame()
                fila.setStyleSheet("QFrame { background: transparent; border: none; }")
                fl = QVBoxLayout(fila)
                fl.setContentsMargins(0, 0, 0, 0)
                fl.setSpacing(3)

                top_row = QHBoxLayout()
                lbl_n = QLabel(nombre)
                lbl_n.setStyleSheet(f"color:{color}; font-size:12px; font-weight:bold;")
                top_row.addWidget(lbl_n)
                top_row.addStretch()
                lbl_v = QLabel(f"{_p(monto_f)}  ({pct:.0f}%)")
                lbl_v.setStyleSheet(f"color:{_T['text_main']}; font-size:12px;")
                top_row.addWidget(lbl_v)
                fl.addLayout(top_row)

                bg = QFrame()
                bg.setFixedHeight(7)
                bg.setFixedWidth(MAX_W)
                bg.setStyleSheet(f"QFrame {{ background:{_T['bg_app']}; border-radius:4px; border:none; }}")
                fill = QFrame(bg)
                fill.setFixedHeight(7)
                fill.setFixedWidth(max(5, int(pct / 100 * MAX_W)))
                fill.setStyleSheet(f"QFrame {{ background:{color}; border-radius:4px; border:none; }}")
                fl.addWidget(bg)
                self.metodos_contenido.addWidget(fila)

        # ── Top productos Hoy ────────────────────────────────────────────────
        while self.top_hoy_lay.count():
            c = self.top_hoy_lay.takeAt(0)
            if c.widget(): c.widget().deleteLater()

        top_hoy = d.get("top_hoy") or []
        if not top_hoy:
            lbl_nh = QLabel("Sin ventas hoy todavía")
            lbl_nh.setStyleSheet(f"color:{_T['text_muted']}; font-size:11px;")
            self.top_hoy_lay.addWidget(lbl_nh)
        else:
            medallas = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
            for i, p in enumerate(top_hoy[:10]):
                self._fila_top(self.top_hoy_lay, i, p, medallas)

        # ── Top productos Año ────────────────────────────────────────────────
        while self.top_anio_lay.count():
            c = self.top_anio_lay.takeAt(0)
            if c.widget(): c.widget().deleteLater()

        top_anio = d.get("top_productos") or []
        medallas = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟",
                    "1️⃣1️⃣","1️⃣2️⃣","1️⃣3️⃣","1️⃣4️⃣","1️⃣5️⃣"]
        for i, p in enumerate(top_anio[:15]):
            self._fila_top(self.top_anio_lay, i, p, medallas)

        # ── Horario pico ─────────────────────────────────────────────────────
        while self.barras_container.count():
            c = self.barras_container.takeAt(0)
            if c.widget(): c.widget().deleteLater()

        horas_data = d.get("horas_hoy") or []
        max_v = max((_tf(h.get("ventas", 0)) for h in horas_data if isinstance(h, dict)), default=1) or 1
        hora_pico = ins.get("hora_pico_hoy")

        for h in horas_data:
            if not isinstance(h, dict): continue
            barra = BarraHora(_ti(h.get("hora", 0)), _tf(h.get("ventas", 0)), max_v)
            self.barras_container.addWidget(barra)

        if hora_pico is not None:
            tix_pico = ins.get("tickets_hora_pico", 0)
            self.lbl_pico.setText(f"🔥 Pico: {_ti(hora_pico):02d}:00 hs ({tix_pico} tickets)")
        else:
            self.lbl_pico.setText("Sin datos aún")

        # ── Turnos del día ───────────────────────────────────────────────────
        self.tabla_turnos.setRowCount(len(turnos))
        for i, t in enumerate(turnos):
            cajero   = t.get("cajero", "?")
            apertura = t.get("apertura", "")[-5:] if t.get("apertura") else "—"
            cierre   = t.get("cierre",   "")[-5:] if t.get("cierre")   else "—"
            estado   = "🟢 Abierto" if t.get("estado") == "abierto" else "⚫ Cerrado"
            tix_t    = str(t.get("cantidad_ventas", 0))
            tot_t    = _p(t.get("total_vendido", 0))
            dif      = _tf(t.get("total_vendido", 0)) - _tf(t.get("monto_cierre_declarado", 0))

            if t.get("estado") == "abierto":
                dif_txt  = "En curso"
                col_dif  = _T["text_muted"]
            elif abs(dif) < 500:
                dif_txt  = f"${dif:+,.0f}"
                col_dif  = "#27ae60"
            else:
                dif_txt  = f"⚠ ${dif:+,.0f}"
                col_dif  = "#e94560"

            for col, txt in enumerate([cajero, apertura, cierre, estado, tix_t, tot_t, dif_txt]):
                item = QTableWidgetItem(txt)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == 6:
                    item.setForeground(QColor(col_dif))
                self.tabla_turnos.setItem(i, col, item)

    def _fila_top(self, layout, idx, prod, medallas):
        if not isinstance(prod, dict): return
        w = QWidget()
        w.setFixedHeight(24)
        w.setStyleSheet("background: transparent;")
        fila = QHBoxLayout(w)
        fila.setContentsMargins(0, 0, 0, 0)
        fila.setSpacing(6)
        lbl_m = QLabel(medallas[idx] if idx < len(medallas) else f"{idx+1}.")
        lbl_m.setFixedWidth(26)
        lbl_m.setStyleSheet("font-size:12px; background:transparent; border:none;")
        fila.addWidget(lbl_m)
        nombre = str(prod.get("nombre", "?"))
        lbl_n = QLabel(nombre[:28] + ("…" if len(nombre) > 28 else ""))
        lbl_n.setStyleSheet(f"color:{_T['text_main']}; font-size:11px; background:transparent; border:none;")
        fila.addWidget(lbl_n)
        fila.addStretch()
        lbl_t = QLabel(_p(prod.get("total", 0)))
        lbl_t.setStyleSheet("color:#27ae60; font-size:11px; font-weight:bold; background:transparent; border:none;")
        fila.addWidget(lbl_t)
        layout.addWidget(w)

    def showEvent(self, event):
        super().showEvent(event)
        self._cargar_datos_hilo()

    def cargar_ventas_periodo(self, periodo):
        self.tabla_hist.setRowCount(0)
        try:
            r = requests.get(f"{API_URL}/reportes/ventas-periodo?periodo={periodo}", timeout=5)
            if r.status_code == 200:
                datos = r.json()
                self.tabla_hist.setRowCount(len(datos))
                for i, fila in enumerate(datos):
                    for col, val in enumerate([
                        str(fila.get("fecha", "-")),
                        str(fila.get("producto", "?")),
                        str(fila.get("cantidad", 0)),
                        _p(float(fila.get("total", 0)))
                    ]):
                        item = QTableWidgetItem(val)
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        self.tabla_hist.setItem(i, col, item)
        except Exception:
            self.tabla_hist.setRowCount(1)
            item = QTableWidgetItem("Sin conexión con el servidor")
            item.setForeground(QColor("#e94560"))
            self.tabla_hist.setItem(0, 0, item)
