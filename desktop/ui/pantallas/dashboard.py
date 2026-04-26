import requests
import json
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QFrame, QScrollArea, QGridLayout,
                             QSizePolicy, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPainter, QColor, QPen
from datetime import datetime

API_URL = "http://127.0.0.1:8000"

NOMBRES_METODO = {
    "efectivo": "💵 Efectivo",
    "tarjeta": "💳 Tarjeta",
    "mercadopago_qr": "📱 QR/MP",
    "transferencia": "🏦 Transf.",
}
COLORES_METODO = {
    "efectivo": "#27ae60",
    "tarjeta": "#3498db",
    "mercadopago_qr": "#009ee3",
    "transferencia": "#9b59b6",
}


class BarraHora(QWidget):
    """Barra visual para el gráfico de horario pico."""
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
        w = self.width()
        h = self.height()
        if self.max_ventas > 0 and self.ventas > 0:
            ratio = self.ventas / self.max_ventas
            bar_h = int((h - 20) * ratio)
            color = QColor("#e94560") if ratio >= 0.8 else QColor("#f39c12") if ratio >= 0.5 else QColor("#3498db")
            painter.fillRect(2, h - 20 - bar_h, w - 4, bar_h, color)
        painter.setPen(QColor("#a0a0b0"))
        painter.setFont(QFont("Arial", 7))
        painter.drawText(0, h - 5, w, 15, Qt.AlignmentFlag.AlignCenter, f"{self.hora:02d}")


class KPICard(QFrame):
    def __init__(self, icono, titulo, valor, color, subtitulo="", parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background: #16213e;
                border-radius: 12px;
                border-left: 4px solid {color};
            }}
        """)
        self.setMinimumHeight(100)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        header = QHBoxLayout()
        lbl_icon = QLabel(icono)
        lbl_icon.setStyleSheet("color: white; font-size: 18px; background: transparent; border: none;")
        header.addWidget(lbl_icon)
        header.addStretch()
        self.lbl_titulo = QLabel(titulo)
        self.lbl_titulo.setStyleSheet(f"color: #a0a0b0; font-size: 11px; background: transparent; border: none;")
        layout.addLayout(header)
        layout.addWidget(self.lbl_titulo)

        self.lbl_valor = QLabel(valor)
        self.lbl_valor.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        self.lbl_valor.setStyleSheet(f"color: {color}; background: transparent; border: none;")
        layout.addWidget(self.lbl_valor)

        if subtitulo:
            self.lbl_sub = QLabel(subtitulo)
            self.lbl_sub.setStyleSheet("color: #555; font-size: 10px; background: transparent; border: none;")
            layout.addWidget(self.lbl_sub)
        else:
            self.lbl_sub = None

    def actualizar(self, valor, subtitulo=""):
        self.lbl_valor.setText(valor)
        if self.lbl_sub and subtitulo:
            self.lbl_sub.setText(subtitulo)


class DashboardScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.datos = None
        self.setup_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self._cargar_datos_hilo)
        self.timer.start(30000)

    def _cargar_datos_hilo(self):
        import threading
        threading.Thread(target=self.cargar_datos, daemon=True).start()

    def setup_ui(self):
        self.setStyleSheet("background-color: #1a1a2e; color: white;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)

        # ── Header ────────────────────────────────────────────────────────────
        header = QHBoxLayout()
        titulo = QLabel("📊 Dashboard")
        titulo.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        titulo.setStyleSheet("color: white;")
        header.addWidget(titulo)
        header.addStretch()
        self.lbl_hora = QLabel("")
        self.lbl_hora.setStyleSheet("color: #555; font-size: 11px;")
        header.addWidget(self.lbl_hora)
        btn_refresh = QPushButton("⟳ Actualizar")
        btn_refresh.setFixedHeight(34)
        btn_refresh.setStyleSheet("""
            QPushButton { background: #0f3460; color: #3498db; border-radius: 8px;
                          font-size: 12px; padding: 0 14px; border: 1px solid #3498db; }
            QPushButton:hover { background: #3498db; color: white; }
        """)
        btn_refresh.clicked.connect(self.cargar_datos)
        header.addWidget(btn_refresh)
        layout.addLayout(header)

        # ── Scroll area ───────────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        contenido = QWidget()
        contenido.setStyleSheet("background: transparent;")
        self.contenido_layout = QVBoxLayout(contenido)
        self.contenido_layout.setSpacing(14)
        self.contenido_layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(contenido)
        layout.addWidget(scroll)

        # ── KPI Cards ─────────────────────────────────────────────────────────
        self.grid_kpi = QGridLayout()
        self.grid_kpi.setSpacing(10)

        # ACÁ ESTABA EL ERROR: Le agrego el 5to parámetro ("-") para que nazca con el texto creado
        self.card_total = KPICard("💰", "VENTAS HOY", "$0", "#e94560", "-")
        self.card_tickets = KPICard("🧾", "TICKETS HOY", "0", "#3498db")
        self.card_promedio = KPICard("📈", "TICKET PROMEDIO", "$0", "#27ae60")
        self.card_metodo = KPICard("💳", "MÉTODO PRINCIPAL", "-", "#f39c12")

        self.grid_kpi.addWidget(self.card_total, 0, 0)
        self.grid_kpi.addWidget(self.card_tickets, 0, 1)
        self.grid_kpi.addWidget(self.card_promedio, 0, 2)
        self.grid_kpi.addWidget(self.card_metodo, 0, 3)
        self.contenido_layout.addLayout(self.grid_kpi)

        # ── Fila 2: Métodos + Top productos ───────────────────────────────────
        fila2 = QHBoxLayout()
        fila2.setSpacing(10)

        self.panel_metodos = QFrame()
        self.panel_metodos.setStyleSheet("QFrame { background: #16213e; border-radius: 12px; }")
        self.panel_metodos.setMinimumHeight(180)
        self.metodos_layout = QVBoxLayout(self.panel_metodos)
        self.metodos_layout.setContentsMargins(16, 14, 16, 14)
        self.metodos_layout.setSpacing(8)
        lbl_m = QLabel("💳 Desglose por método")
        lbl_m.setStyleSheet("color: #a0a0b0; font-size: 12px; font-weight: bold;")
        self.metodos_layout.addWidget(lbl_m)
        self.metodos_contenido = QVBoxLayout()
        self.metodos_contenido.setSpacing(6)
        self.metodos_layout.addLayout(self.metodos_contenido)
        self.metodos_layout.addStretch()
        fila2.addWidget(self.panel_metodos, 1)

        self.panel_top = QFrame()
        self.panel_top.setStyleSheet("QFrame { background: #16213e; border-radius: 12px; }")
        self.panel_top.setMinimumHeight(480)
        self.top_layout = QVBoxLayout(self.panel_top)
        self.top_layout.setContentsMargins(16, 14, 16, 14)
        self.top_layout.setSpacing(6)
        lbl_t = QLabel("🏆 Top productos del año")
        lbl_t.setStyleSheet("color: #a0a0b0; font-size: 12px; font-weight: bold;")
        self.top_layout.addWidget(lbl_t)
        self.top_contenido = QVBoxLayout()
        self.top_contenido.setSpacing(4)
        self.top_layout.addLayout(self.top_contenido)
        self.top_layout.addStretch()
        fila2.addWidget(self.panel_top, 1)

        self.contenido_layout.addLayout(fila2)

        # ── Horario pico ──────────────────────────────────────────────────────
        self.panel_horario = QFrame()
        self.panel_horario.setStyleSheet("QFrame { background: #16213e; border-radius: 12px; }")
        horario_layout = QVBoxLayout(self.panel_horario)
        horario_layout.setContentsMargins(16, 14, 16, 14)
        horario_layout.setSpacing(8)

        h_header = QHBoxLayout()
        lbl_h = QLabel("🕐 Horario pico de hoy")
        lbl_h.setStyleSheet("color: #a0a0b0; font-size: 12px; font-weight: bold;")
        h_header.addWidget(lbl_h)
        h_header.addStretch()
        self.lbl_pico = QLabel("")
        self.lbl_pico.setStyleSheet("color: #e94560; font-size: 12px; font-weight: bold;")
        h_header.addWidget(self.lbl_pico)
        horario_layout.addLayout(h_header)

        self.barras_container = QHBoxLayout()
        self.barras_container.setSpacing(2)
        self.barras_container.setAlignment(Qt.AlignmentFlag.AlignLeft)
        horario_layout.addLayout(self.barras_container)

        leyenda = QLabel("🔴 Pico alto   🟡 Moderado   🔵 Bajo")
        leyenda.setStyleSheet("color: #555; font-size: 10px;")
        horario_layout.addWidget(leyenda)

        self.contenido_layout.addWidget(self.panel_horario)
        # ── SECCIÓN: HISTORIAL DETALLADO DÍA TRAS DÍA ──────────────────
        self.panel_detallado = QFrame()
        self.panel_detallado.setStyleSheet("QFrame { background: #16213e; border-radius: 12px; }")
        detallado_layout = QVBoxLayout(self.panel_detallado)
        detallado_layout.setContentsMargins(16, 14, 16, 14)

        header_det = QHBoxLayout()
        lbl_det = QLabel("📋 Historial de Productos Vendidos")
        lbl_det.setStyleSheet("color: #a0a0b0; font-size: 14px; font-weight: bold;")
        header_det.addWidget(lbl_det)
        header_det.addStretch()

        # Botones de Filtro
        self.btn_ver_dia = QPushButton("Día")
        self.btn_ver_sem = QPushButton("Semana")
        self.btn_ver_mes = QPushButton("Mes")
        for b in [self.btn_ver_dia, self.btn_ver_sem, self.btn_ver_mes]:
            b.setFixedSize(70, 25)
            b.setStyleSheet("""
                QPushButton { background: #0f3460; color: white; border-radius: 5px; font-size: 10px; border: 1px solid #3498db; }
                QPushButton:hover { background: #3498db; }
            """)
        
        header_det.addWidget(self.btn_ver_dia)
        header_det.addWidget(self.btn_ver_sem)
        header_det.addWidget(self.btn_ver_mes)
        detallado_layout.addLayout(header_det)

        # La Tabla
        self.tabla_detallada = QTableWidget()
        self.tabla_detallada.setColumnCount(4)
        self.tabla_detallada.setHorizontalHeaderLabels(["Fecha", "Producto", "Cant.", "Total $"])
        self.tabla_detallada.setStyleSheet("""
            QTableWidget { background: transparent; color: white; gridline-color: #1a1a2e; border: none; font-size: 11px; }
            QHeaderView::section { background: #0f3460; color: #a0a0b0; padding: 5px; border: none; font-weight: bold; }
        """)
        self.tabla_detallada.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_detallada.setMinimumHeight(400) # Para que se vea bien grande
        detallado_layout.addWidget(self.tabla_detallada)

        self.contenido_layout.addWidget(self.panel_detallado)
        
        # Conexiones de los botones
        self.btn_ver_dia.clicked.connect(lambda: self.cargar_ventas_periodo("dia"))
        self.btn_ver_sem.clicked.connect(lambda: self.cargar_ventas_periodo("semana"))
        self.btn_ver_mes.clicked.connect(lambda: self.cargar_ventas_periodo("mes"))
        
        # Volvemos a poner el stretch al final de todo para que empuje hacia arriba
        self.contenido_layout.addStretch()

    def cargar_datos(self):
        self.lbl_hora.setText(f"Actualizado: {datetime.now().strftime('%H:%M:%S')}")
        try:
            r = requests.get(f"{API_URL}/reportes/dashboard", timeout=5)
            if r.status_code == 200:
                self.datos = r.json()
                self.actualizar_ui()
            else:
                self.lbl_hora.setText(f"⚠️ Error del servidor: {r.status_code}")
        except Exception as e:
            self.lbl_hora.setText(f"⚠️ Bug: {str(e)[:40]}") 
            print(f"ERROR: {e}")

    def actualizar_ui(self):
        if not self.datos or not isinstance(self.datos, dict):
            return
        d = self.datos

        def to_float(val):
            try: return float(val)
            except: return 0.0

        def to_int(val):
            try: return int(val)
            except: return 0

        # KPIs
        total = to_float(d.get("total_hoy"))
        var = to_float(d.get("variacion_pct"))
        signo = "▲" if var >= 0 else "▼"
        color_var = "#27ae60" if var >= 0 else "#e94560"
        
        self.card_total.actualizar(f"${total:,.0f}", f"{signo} {abs(var):.1f}% vs ayer")
        # Protección extra antes de pintar el color
        if self.card_total.lbl_sub:
            self.card_total.lbl_sub.setStyleSheet(f"color: {color_var}; font-size: 11px; background: transparent; border: none;")

        tickets = to_int(d.get("tickets_hoy"))
        self.card_tickets.actualizar(str(tickets))
        
        promedio = to_float(d.get("ticket_promedio"))
        self.card_promedio.actualizar(f"${promedio:,.0f}")

        metodo_principal = str(d.get("metodo_mas_usado") or "efectivo")
        nombre_mp = NOMBRES_METODO.get(metodo_principal, metodo_principal)
        color_mp = COLORES_METODO.get(metodo_principal, "#f39c12")
        self.card_metodo.actualizar(nombre_mp)
        self.card_metodo.lbl_valor.setStyleSheet(f"color: {color_mp}; font-size: 16px; font-weight: bold; background: transparent; border: none;")

        # Métodos de pago
        while self.metodos_contenido.count():
            child = self.metodos_contenido.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        desglose = d.get("desglose_metodos")
        if not isinstance(desglose, dict): 
            desglose = {}
            
        total_metodos = sum(to_float(v) for v in desglose.values()) or 1
        for metodo, monto in sorted(desglose.items(), key=lambda x: to_float(x[1]), reverse=True):
            monto_f = to_float(monto)
            fila = QFrame()
            fila.setStyleSheet("QFrame { background: transparent; border: none; }")
            fila_layout = QVBoxLayout(fila)
            fila_layout.setContentsMargins(0, 0, 0, 0)
            fila_layout.setSpacing(2)

            nombre = NOMBRES_METODO.get(metodo, metodo)
            color = COLORES_METODO.get(metodo, "#95a5a6")
            pct = (monto_f / total_metodos) * 100

            top_row = QHBoxLayout()
            lbl_n = QLabel(nombre)
            lbl_n.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: bold;")
            top_row.addWidget(lbl_n)
            top_row.addStretch()
            lbl_v = QLabel(f"${monto_f:,.0f}  ({pct:.0f}%)")
            lbl_v.setStyleSheet("color: white; font-size: 12px;")
            top_row.addWidget(lbl_v)
            fila_layout.addLayout(top_row)

            barra = QFrame()
            barra.setFixedHeight(6)
            barra.setStyleSheet(f"QFrame {{ background: #0f3460; border-radius: 3px; border: none; }}")
            barra_inner = QFrame(barra)
            barra_inner.setFixedHeight(6)
            barra_w = max(4, int(pct * 2))
            barra_inner.setFixedWidth(barra_w)
            barra_inner.setStyleSheet(f"QFrame {{ background: {color}; border-radius: 3px; border: none; }}")
            fila_layout.addWidget(barra)

            self.metodos_contenido.addWidget(fila)

        # Top productos
        while self.top_contenido.count():
            child = self.top_contenido.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        top_prod = d.get("top_productos")
        if not isinstance(top_prod, list):
            top_prod = []
            
        medallas = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟",
                    "1️⃣1️⃣","1️⃣2️⃣","1️⃣3️⃣","1️⃣4️⃣","1️⃣5️⃣"]
        for i, prod in enumerate(top_prod):
            if not isinstance(prod, dict): continue
            w = QWidget()
            w.setFixedHeight(26)
            w.setStyleSheet("background: transparent;")
            fila = QHBoxLayout(w)
            fila.setContentsMargins(0, 0, 0, 0)
            fila.setSpacing(6)

            lbl_med = QLabel(medallas[i] if i < len(medallas) else f"{i+1}.")
            lbl_med.setFixedWidth(28)
            lbl_med.setFixedHeight(22)
            lbl_med.setStyleSheet("font-size: 13px; background: transparent; border: none;")
            fila.addWidget(lbl_med)

            nombre_prod = str(prod.get("nombre", "Desconocido"))
            lbl_nombre = QLabel(nombre_prod[:30] + ("…" if len(nombre_prod) > 30 else ""))
            lbl_nombre.setFixedHeight(22)
            lbl_nombre.setStyleSheet("color: white; font-size: 12px; background: transparent; border: none;")
            fila.addWidget(lbl_nombre)
            fila.addStretch()

            total_prod = to_float(prod.get("total", 0))
            lbl_total = QLabel(f"${total_prod:,.0f}")
            lbl_total.setFixedHeight(22)
            lbl_total.setStyleSheet("color: #27ae60; font-size: 12px; font-weight: bold; background: transparent; border: none;")
            fila.addWidget(lbl_total)

            self.top_contenido.addWidget(w)

        # Horario pico
        while self.barras_container.count():
            child = self.barras_container.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        horas_data = d.get("horas_hoy")
        if not isinstance(horas_data, list):
            horas_data = []
            
        max_v = max((to_float(h.get("ventas", 0)) for h in horas_data if isinstance(h, dict)), default=1) or 1
        hora_pico = d.get("hora_pico")

        for h in horas_data:
            if not isinstance(h, dict): continue
            barra = BarraHora(to_int(h.get("hora", 0)), to_float(h.get("ventas", 0)), max_v)
            self.barras_container.addWidget(barra)

        if hora_pico is not None:
            self.lbl_pico.setText(f"🔥 Pico: {to_int(hora_pico):02d}:00 hs")
        else:
            self.lbl_pico.setText("")

    def showEvent(self, event):
        super().showEvent(event)
        self.cargar_datos()
    def cargar_ventas_periodo(self, periodo):
        try:
            # Esta es la ruta que creamos en el servidor
            r = requests.get(f"{API_URL}/reportes/ventas-periodo?periodo={periodo}", timeout=5)
            if r.status_code == 200:
                datos = r.json()
                self.tabla_detallada.setRowCount(len(datos))
                for i, fila in enumerate(datos):
                    # Sacamos los datos con cuidado para que no falle
                    fecha = str(fila.get("fecha", "-"))
                    prod = str(fila.get("producto", "Desconocido"))
                    cant = str(fila.get("cantidad", 0))
                    total = f"$ {float(fila.get('total', 0)):,.2f}"

                    self.tabla_detallada.setItem(i, 0, QTableWidgetItem(fecha))
                    self.tabla_detallada.setItem(i, 1, QTableWidgetItem(prod))
                    self.tabla_detallada.setItem(i, 2, QTableWidgetItem(cant))
                    self.tabla_detallada.setItem(i, 3, QTableWidgetItem(total))
            else:
                print(f"Error en el servidor: {r.status_code}")
        except Exception as e:
            print(f"Error cargando la tabla: {e}")    