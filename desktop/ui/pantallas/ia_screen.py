import requests
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QFrame, QTableWidget, QTableWidgetItem,
                              QHeaderView, QDoubleSpinBox, QLineEdit, QScrollArea,
                              QGridLayout, QTabWidget, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor

API_URL = "http://127.0.0.1:8000"

def _p(v):
    return f"${float(v):,.0f}".replace(",", ".")

DIAS_ES = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]


def variacion_label(pct):
    if pct is None:
        return "—", "#a0a0b0"
    if pct > 0:
        return f"▲ {pct:.1f}%", "#27ae60"
    elif pct < 0:
        return f"▼ {abs(pct):.1f}%", "#e94560"
    return "= 0%", "#a0a0b0"


class ComparativoWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("QFrame { background: #16213e; border-radius: 12px; }")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        titulo = QLabel("📊 Comparativo Semanal")
        titulo.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        titulo.setStyleSheet("color: white;")
        header.addWidget(titulo)
        header.addStretch()
        btn_act = QPushButton("🔄")
        btn_act.setFixedSize(30, 30)
        btn_act.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_act.setStyleSheet("QPushButton { background: #0f3460; color: white; border-radius: 6px; } QPushButton:hover { background: #e94560; }")
        btn_act.clicked.connect(self.cargar)
        header.addWidget(btn_act)
        layout.addLayout(header)

        # Cards de variación
        self.grid = QGridLayout()
        self.grid.setSpacing(10)
        self.card_ventas    = self._mini_card("💰 Ventas", "$0", "$0", "#e94560")
        self.card_tickets   = self._mini_card("🧾 Tickets", "0", "0", "#3498db")
        self.card_promedio  = self._mini_card("📈 Ticket prom.", "$0", "$0", "#27ae60")
        self.card_proyecc   = self._mini_card("🎯 Proyección", "$0", "esta semana", "#f39c12")
        self.grid.addWidget(self.card_ventas[0], 0, 0)
        self.grid.addWidget(self.card_tickets[0], 0, 1)
        self.grid.addWidget(self.card_promedio[0], 0, 2)
        self.grid.addWidget(self.card_proyecc[0], 0, 3)
        layout.addLayout(self.grid)

        # Top productos
        fila2 = QHBoxLayout()
        fila2.setSpacing(10)

        panel_top = QFrame()
        panel_top.setStyleSheet("QFrame { background: #0f3460; border-radius: 8px; }")
        top_lay = QVBoxLayout(panel_top)
        top_lay.setContentsMargins(12, 10, 12, 10)
        lbl_top = QLabel("🏆 Top producto")
        lbl_top.setStyleSheet("color: #f39c12; font-size: 12px; font-weight: bold;")
        top_lay.addWidget(lbl_top)
        self.lbl_top_actual = QLabel("Esta semana: —")
        self.lbl_top_actual.setStyleSheet("color: white; font-size: 12px;")
        top_lay.addWidget(self.lbl_top_actual)
        self.lbl_top_pasada = QLabel("Semana pasada: —")
        self.lbl_top_pasada.setStyleSheet("color: #a0a0b0; font-size: 11px;")
        top_lay.addWidget(self.lbl_top_pasada)
        fila2.addWidget(panel_top)

        panel_metodos = QFrame()
        panel_metodos.setStyleSheet("QFrame { background: #0f3460; border-radius: 8px; }")
        met_lay = QVBoxLayout(panel_metodos)
        met_lay.setContentsMargins(12, 10, 12, 10)
        lbl_met = QLabel("💳 Métodos esta semana")
        lbl_met.setStyleSheet("color: #3498db; font-size: 12px; font-weight: bold;")
        met_lay.addWidget(lbl_met)
        self.lbl_metodos = QLabel("—")
        self.lbl_metodos.setStyleSheet("color: white; font-size: 11px;")
        self.lbl_metodos.setWordWrap(True)
        met_lay.addWidget(self.lbl_metodos)
        fila2.addWidget(panel_metodos)

        layout.addLayout(fila2)

    def _mini_card(self, titulo, val_actual, val_pasado, color):
        card = QFrame()
        card.setStyleSheet(f"QFrame {{ background: #0f3460; border-radius: 8px; border-left: 3px solid {color}; }}")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(10, 8, 10, 8)
        cl.setSpacing(3)
        lbl_t = QLabel(titulo)
        lbl_t.setStyleSheet("color: #a0a0b0; font-size: 10px;")
        cl.addWidget(lbl_t)
        lbl_v = QLabel(val_actual)
        lbl_v.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        lbl_v.setStyleSheet(f"color: {color};")
        cl.addWidget(lbl_v)
        lbl_p = QLabel(val_pasado)
        lbl_p.setStyleSheet("color: #555; font-size: 10px;")
        cl.addWidget(lbl_p)
        return card, lbl_v, lbl_p

    def cargar(self):
        try:
            r = requests.get(f"{API_URL}/ia/comparativo-semanal", timeout=6)
            if r.status_code == 200:
                d = r.json()
                act = d["semana_actual"]
                pas = d["semana_pasada"]

                # Ventas
                txt_var, color_var = variacion_label(d["variacion_total"])
                self.card_ventas[1].setText(_p(act['total']))
                self.card_ventas[2].setText(f"sem ant: {_p(pas['total'])}  {txt_var}")
                self.card_ventas[2].setStyleSheet(f"color: {color_var}; font-size: 10px;")

                # Tickets
                txt_var2, color_var2 = variacion_label(d["variacion_tickets"])
                self.card_tickets[1].setText(str(act["tickets"]))
                self.card_tickets[2].setText(f"sem ant: {pas['tickets']}  {txt_var2}")
                self.card_tickets[2].setStyleSheet(f"color: {color_var2}; font-size: 10px;")

                # Promedio
                txt_var3, color_var3 = variacion_label(d["variacion_promedio"])
                self.card_promedio[1].setText(_p(act['promedio_ticket']))
                self.card_promedio[2].setText(f"sem ant: {_p(pas['promedio_ticket'])}  {txt_var3}")
                self.card_promedio[2].setStyleSheet(f"color: {color_var3}; font-size: 10px;")

                # Proyección
                self.card_proyecc[1].setText(_p(d['proyeccion_semanal']))
                self.card_proyecc[2].setText(f"{d['dias_transcurridos']} días transcurridos")

                # Top productos
                tp = act.get("top_producto")
                if tp:
                    self.lbl_top_actual.setText(f"Esta semana: {tp['nombre']} ({_p(tp['facturado'])})")
                tp2 = pas.get("top_producto")
                if tp2:
                    self.lbl_top_pasada.setText(f"Sem. pasada: {tp2['nombre']} ({_p(tp2['facturado'])})")

                # Métodos
                metodos = act.get("metodos", {})
                nombres = {"efectivo": "Efectivo", "tarjeta": "Tarjeta", "mercadopago_qr": "QR/MP", "transferencia": "Transf."}
                txt_met = "  ".join([f"{nombres.get(k, k)}: {_p(v)}" for k, v in metodos.items()])
                self.lbl_metodos.setText(txt_met or "Sin datos")
        except Exception:
            pass


class AnomaliaWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("QFrame { background: #16213e; border-radius: 12px; }")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        titulo = QLabel("🔍 Detección de Anomalías")
        titulo.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        titulo.setStyleSheet("color: white;")
        header.addWidget(titulo)
        header.addStretch()
        btn_act = QPushButton("🔄")
        btn_act.setFixedSize(30, 30)
        btn_act.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_act.setStyleSheet("QPushButton { background: #0f3460; color: white; border-radius: 6px; } QPushButton:hover { background: #e94560; }")
        btn_act.clicked.connect(self.cargar)
        header.addWidget(btn_act)
        layout.addLayout(header)

        self.lbl_stats = QLabel("Analizando ventas de los últimos 30 días...")
        self.lbl_stats.setStyleSheet("color: #a0a0b0; font-size: 12px;")
        layout.addWidget(self.lbl_stats)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels(["Ticket", "Total", "Tipo", "Desvío"])
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabla.setColumnWidth(1, 100)
        self.tabla.setColumnWidth(2, 80)
        self.tabla.setColumnWidth(3, 80)
        self.tabla.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tabla.setMaximumHeight(200)
        self.tabla.setStyleSheet("""
            QTableWidget { background: #0f3460; border: none; border-radius: 8px; gridline-color: #1a1a2e; }
            QHeaderView::section { background: #1a1a2e; color: #a0a0b0; padding: 6px; border: none; }
            QTableWidgetItem { color: white; padding: 6px; }
        """)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.tabla)

    def cargar(self):
        try:
            r = requests.get(f"{API_URL}/ia/anomalias", timeout=6)
            if r.status_code == 200:
                d = r.json()
                promedio = d.get("promedio", 0)
                desvio   = d.get("desvio", 0)
                anomalias = d.get("anomalias", [])

                self.lbl_stats.setText(
                    f"Promedio: ${promedio:,.0f}  |  Desvío std: ${desvio:,.0f}  |  "
                    f"{len(anomalias)} anomalía{'s' if len(anomalias) != 1 else ''} detectada{'s' if len(anomalias) != 1 else ''} "
                    f"de {d.get('total_ventas_analizadas', 0)} ventas"
                )

                if not anomalias:
                    self.tabla.setRowCount(1)
                    item = QTableWidgetItem("✅ No se detectaron anomalías en los últimos 30 días")
                    item.setForeground(QColor("#27ae60"))
                    self.tabla.setItem(0, 0, item)
                    return

                self.tabla.setRowCount(len(anomalias))
                for i, a in enumerate(anomalias):
                    self.tabla.setItem(i, 0, QTableWidgetItem(f"#{a['numero']}  {a['fecha'][5:16]}"))
                    item_total = QTableWidgetItem(f"${a['total']:,.0f}")
                    color = "#e94560" if a["tipo"] == "alta" else "#3498db"
                    item_total.setForeground(QColor(color))
                    self.tabla.setItem(i, 1, item_total)
                    tipo_txt = "⬆ Alta" if a["tipo"] == "alta" else "⬇ Baja"
                    item_tipo = QTableWidgetItem(tipo_txt)
                    item_tipo.setForeground(QColor(color))
                    self.tabla.setItem(i, 2, item_tipo)
                    self.tabla.setItem(i, 3, QTableWidgetItem(f"{a['desviacion']:.1f}σ"))
        except Exception:
            pass


class PrecioDinamicoWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("QFrame { background: #16213e; border-radius: 12px; }")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        titulo = QLabel("💡 Precio Dinámico Sugerido")
        titulo.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        titulo.setStyleSheet("color: white;")
        layout.addWidget(titulo)

        fila = QHBoxLayout()
        self.input_buscar = QLineEdit()
        self.input_buscar.setPlaceholderText("Buscar producto...")
        self.input_buscar.setFixedHeight(40)
        self.input_buscar.setStyleSheet("QLineEdit { background: #0f3460; border: 1px solid #9b59b6; border-radius: 8px; padding: 0 10px; color: white; font-size: 13px; }")
        self.input_buscar.returnPressed.connect(self.buscar_y_analizar)
        fila.addWidget(self.input_buscar)

        lbl_margen = QLabel("Margen objetivo:")
        lbl_margen.setStyleSheet("color: #a0a0b0; font-size: 12px;")
        fila.addWidget(lbl_margen)

        self.input_margen = QDoubleSpinBox()
        self.input_margen.setRange(1, 90)
        self.input_margen.setValue(30)
        self.input_margen.setSuffix(" %")
        self.input_margen.setFixedHeight(40)
        self.input_margen.setFixedWidth(100)
        self.input_margen.setStyleSheet("QDoubleSpinBox { background: #0f3460; border: 1px solid #9b59b6; border-radius: 8px; padding: 6px; color: white; font-size: 13px; }")
        fila.addWidget(self.input_margen)

        btn = QPushButton("Analizar")
        btn.setFixedHeight(40)
        btn.setFixedWidth(90)
        btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn.setStyleSheet("QPushButton { background: #9b59b6; color: white; border-radius: 8px; font-size: 13px; font-weight: bold; }")
        btn.clicked.connect(self.buscar_y_analizar)
        fila.addWidget(btn)
        layout.addLayout(fila)

        self.resultado_frame = QFrame()
        self.resultado_frame.setStyleSheet("QFrame { background: #0f3460; border-radius: 8px; }")
        self.resultado_frame.hide()
        res_lay = QGridLayout(self.resultado_frame)
        res_lay.setContentsMargins(16, 12, 16, 12)
        res_lay.setSpacing(8)

        self.lbl_nombre = QLabel("")
        self.lbl_nombre.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        self.lbl_nombre.setStyleSheet("color: white;")
        res_lay.addWidget(self.lbl_nombre, 0, 0, 1, 4)

        for col, (label, attr) in enumerate([
            ("Precio actual", "lbl_actual"),
            ("Precio costo", "lbl_costo"),
            ("Margen actual", "lbl_margen"),
            ("Precio sugerido", "lbl_sugerido"),
        ]):
            lbl_t = QLabel(label)
            lbl_t.setStyleSheet("color: #a0a0b0; font-size: 10px;")
            res_lay.addWidget(lbl_t, 1, col)
            lbl_v = QLabel("—")
            lbl_v.setFont(QFont("Arial", 13, QFont.Weight.Bold))
            lbl_v.setStyleSheet("color: white;")
            res_lay.addWidget(lbl_v, 2, col)
            setattr(self, attr, lbl_v)

        self.lbl_recomendacion = QLabel("")
        self.lbl_recomendacion.setStyleSheet("color: #f39c12; font-size: 12px; font-weight: bold;")
        self.lbl_recomendacion.setWordWrap(True)
        res_lay.addWidget(self.lbl_recomendacion, 3, 0, 1, 4)

        layout.addWidget(self.resultado_frame)
        self.producto_id_actual = None

    def buscar_y_analizar(self):
        texto = self.input_buscar.text().strip()
        if not texto:
            return
        try:
            r = requests.get(f"{API_URL}/productos/buscar", params={"q": texto}, timeout=5)
            if r.status_code == 200:
                productos = r.json()
                if not productos:
                    QMessageBox.warning(self, "No encontrado", f"No se encontró: {texto}")
                    return
                self.analizar_producto(productos[0]["id"])
        except Exception:
            pass

    def analizar_producto(self, producto_id):
        margen = self.input_margen.value()
        try:
            r = requests.get(f"{API_URL}/ia/precio-sugerido/{producto_id}",
                             params={"margen_objetivo": margen}, timeout=5)
            if r.status_code == 200:
                d = r.json()
                self.lbl_nombre.setText(d["producto"])
                self.lbl_actual.setText(f"${d['precio_actual']:,.0f}")
                self.lbl_costo.setText(f"${d['precio_costo']:,.0f}" if d["precio_costo"] else "—")
                margen_a = d.get("margen_actual")
                self.lbl_margen.setText(f"{margen_a:.1f}%" if margen_a else "—")
                if d["precio_sugerido"]:
                    self.lbl_sugerido.setText(f"${d['precio_sugerido']:,.0f}")
                    colores = {"subir": "#e94560", "revisar": "#f39c12", "ok": "#27ae60"}
                    self.lbl_sugerido.setStyleSheet(f"color: {colores.get(d['recomendacion'], 'white')}; font-size: 13px; font-weight: bold;")
                else:
                    self.lbl_sugerido.setText("Sin costo cargado")
                self.lbl_recomendacion.setText(f"💡 {d['mensaje']}  |  Vendido 30d: {d['vendido_30d']:.0f} unidades")
                self.resultado_frame.show()
        except Exception:
            pass


class IAScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("background-color: #1a1a2e; color: white;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        header = QHBoxLayout()
        titulo = QLabel("🤖 Inteligencia Artificial")
        titulo.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        titulo.setStyleSheet("color: white;")
        header.addWidget(titulo)
        header.addStretch()
        btn_act = QPushButton("⟳ Actualizar todo")
        btn_act.setFixedHeight(34)
        btn_act.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_act.setStyleSheet("QPushButton { background: #0f3460; color: #3498db; border: 1px solid #3498db; border-radius: 8px; font-size: 12px; padding: 0 14px; } QPushButton:hover { background: #3498db; color: white; }")
        btn_act.clicked.connect(self.cargar_todo)
        header.addWidget(btn_act)
        layout.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        contenido = QWidget()
        contenido.setStyleSheet("background: transparent;")
        cont_lay = QVBoxLayout(contenido)
        cont_lay.setSpacing(14)
        cont_lay.setContentsMargins(0, 0, 0, 0)

        self.comparativo = ComparativoWidget()
        cont_lay.addWidget(self.comparativo)

        fila2 = QHBoxLayout()
        fila2.setSpacing(14)
        self.anomalias = AnomaliaWidget()
        fila2.addWidget(self.anomalias)
        self.precio_din = PrecioDinamicoWidget()
        fila2.addWidget(self.precio_din)
        cont_lay.addLayout(fila2)

        cont_lay.addStretch()
        scroll.setWidget(contenido)
        layout.addWidget(scroll)

    def cargar_todo(self):
        self.comparativo.cargar()
        self.anomalias.cargar()

    def showEvent(self, event):
        super().showEvent(event)
        self.cargar_todo()
