import requests
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QFrame, QPushButton, QTableWidget,
                              QTableWidgetItem, QHeaderView, QMessageBox,
                              QScrollArea)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

API_URL = "http://127.0.0.1:8000"

class ReportesScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.periodo_actual = "hoy"
        self.setup_ui()
        self.cargar_datos()

    def setup_ui(self):
        self.setStyleSheet("background-color: #1a1a2e; color: white;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header
        top = QHBoxLayout()
        titulo = QLabel("📊 Reportes")
        titulo.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        titulo.setStyleSheet("color: white;")
        top.addWidget(titulo)
        top.addStretch()

        for texto, key in [("Hoy","hoy"),("Semana","semana"),("Mes","mes"),("Año","anio")]:
            btn = QPushButton(texto)
            btn.setFixedHeight(36)
            btn.setFixedWidth(80)
            btn.setStyleSheet("QPushButton { background: #0f3460; color: #a0a0b0; border-radius: 8px; font-size: 13px; } QPushButton:hover { background: #e94560; color: white; }")
            btn.clicked.connect(lambda _, k=key: self.cambiar_periodo(k))
            top.addWidget(btn)

        btn_act = QPushButton("🔄")
        btn_act.setFixedSize(36, 36)
        btn_act.setStyleSheet("QPushButton { background: #16213e; color: white; border-radius: 8px; } QPushButton:hover { background: #e94560; }")
        btn_act.clicked.connect(self.cargar_datos)
        top.addWidget(btn_act)
        layout.addLayout(top)

        self.lbl_periodo = QLabel("Mostrando: Hoy")
        self.lbl_periodo.setStyleSheet("color: #e94560; font-size: 13px; font-weight: bold;")
        layout.addWidget(self.lbl_periodo)

        # Alerta tickets
        self.lbl_alerta = QLabel("")
        self.lbl_alerta.setStyleSheet("""
            QLabel {
                background: #16213e;
                border-left: 4px solid #e67e22;
                border-radius: 6px;
                color: #f39c12;
                font-size: 13px;
                padding: 8px 12px;
            }
        """)
        self.lbl_alerta.hide()
        layout.addWidget(self.lbl_alerta)

        # Tarjetas conteo tickets
        tickets_frame = QFrame()
        tickets_frame.setStyleSheet("QFrame { background: #16213e; border-radius: 12px; }")
        tickets_layout = QHBoxLayout(tickets_frame)
        tickets_layout.setContentsMargins(16, 12, 16, 12)
        tickets_layout.setSpacing(0)

        self.card_tickets_hoy = self.crear_mini_card("Tickets hoy", "0", "#e94560")
        self.card_tickets_semana = self.crear_mini_card("Esta semana", "0", "#3498db")
        self.card_tickets_semana_pasada = self.crear_mini_card("Sem. anterior", "0", "#7f8c8d")
        self.card_tickets_mes = self.crear_mini_card("Este mes", "0", "#27ae60")
        self.card_tickets_mes_pasado = self.crear_mini_card("Mes anterior", "0", "#7f8c8d")

        for card in [self.card_tickets_hoy, self.card_tickets_semana,
                     self.card_tickets_semana_pasada, self.card_tickets_mes,
                     self.card_tickets_mes_pasado]:
            tickets_layout.addWidget(card[0])
        layout.addWidget(tickets_frame)

        # Tarjetas ventas
        cards_layout = QHBoxLayout()
        self.card_ventas = self.crear_card("💰 Total vendido", "$0", "#e94560")
        self.card_cantidad = self.crear_card("🛒 Tickets", "0", "#0f3460")
        self.card_promedio = self.crear_card("📈 Promedio ticket", "$0", "#27ae60")
        self.card_stock_bajo = self.crear_card("⚠️ Stock bajo", "0", "#e67e22")
        cards_layout.addWidget(self.card_ventas[0])
        cards_layout.addWidget(self.card_cantidad[0])
        cards_layout.addWidget(self.card_promedio[0])
        cards_layout.addWidget(self.card_stock_bajo[0])
        layout.addLayout(cards_layout)

        # Desglose por método de pago
        desglose_frame = QFrame()
        desglose_frame.setStyleSheet("QFrame { background: #16213e; border-radius: 10px; }")
        desglose_layout = QHBoxLayout(desglose_frame)
        desglose_layout.setContentsMargins(16, 10, 16, 10)

        self.cards_metodo = {}
        metodos = [
            ("💵", "Efectivo",      "efectivo",       "#27ae60"),
            ("💳", "Tarjeta",       "tarjeta",         "#3498db"),
            ("📱", "QR / MP",       "mercadopago_qr",  "#009ee3"),
            ("🏦", "Transferencia", "transferencia",   "#9b59b6"),
        ]
        for icono, nombre, key, color in metodos:
            card = QFrame()
            card.setStyleSheet(f"QFrame {{ background: #0f3460; border-radius: 8px; border-left: 3px solid {color}; }}")
            c_layout = QVBoxLayout(card)
            c_layout.setContentsMargins(10, 6, 10, 6)
            lbl_n = QLabel(f"{icono} {nombre}")
            lbl_n.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: bold;")
            c_layout.addWidget(lbl_n)
            lbl_v = QLabel("$0.00")
            lbl_v.setFont(QFont("Arial", 13, QFont.Weight.Bold))
            lbl_v.setStyleSheet(f"color: {color};")
            c_layout.addWidget(lbl_v)
            desglose_layout.addWidget(card)
            self.cards_metodo[key] = lbl_v

        layout.addWidget(desglose_frame)

        # Tablas
        tablas_layout = QHBoxLayout()

        col_izq = QVBoxLayout()
        lbl_v = QLabel("Ventas del período")
        lbl_v.setStyleSheet("color: #a0a0b0; font-size: 13px; font-weight: bold;")
        col_izq.addWidget(lbl_v)
        self.tabla_ventas = self.crear_tabla(["Ticket", "Total", "Método", "Fecha"])
        col_izq.addWidget(self.tabla_ventas)
        tablas_layout.addLayout(col_izq)

        col_der = QVBoxLayout()
        lbl_t = QLabel("Productos más vendidos")
        lbl_t.setStyleSheet("color: #a0a0b0; font-size: 13px; font-weight: bold;")
        col_der.addWidget(lbl_t)
        self.tabla_top = self.crear_tabla(["Producto", "Cantidad", "Total"])
        col_der.addWidget(self.tabla_top)
        tablas_layout.addLayout(col_der)

        layout.addLayout(tablas_layout)

    def crear_mini_card(self, titulo, valor, color):
        card = QFrame()
        card.setStyleSheet("QFrame { background: transparent; }")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 6, 12, 6)
        lbl_t = QLabel(titulo)
        lbl_t.setStyleSheet("color: #a0a0b0; font-size: 11px;")
        card_layout.addWidget(lbl_t)
        lbl_v = QLabel(valor)
        lbl_v.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        lbl_v.setStyleSheet(f"color: {color};")
        card_layout.addWidget(lbl_v)
        return card, lbl_v

    def crear_card(self, titulo, valor, color):
        card = QFrame()
        card.setStyleSheet(f"QFrame {{ background: #16213e; border-radius: 12px; border-left: 4px solid {color}; }}")
        card.setMinimumHeight(90)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 12, 16, 12)
        lbl_t = QLabel(titulo)
        lbl_t.setStyleSheet("color: #a0a0b0; font-size: 12px;")
        card_layout.addWidget(lbl_t)
        lbl_v = QLabel(valor)
        lbl_v.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        lbl_v.setStyleSheet(f"color: {color};")
        card_layout.addWidget(lbl_v)
        return card, lbl_v

    def crear_tabla(self, headers):
        tabla = QTableWidget()
        tabla.setColumnCount(len(headers))
        tabla.setHorizontalHeaderLabels(headers)
        tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        tabla.setStyleSheet("""
            QTableWidget { background: #16213e; border: 1px solid #0f3460; border-radius: 8px; gridline-color: #0f3460; }
            QHeaderView::section { background: #0f3460; color: #a0a0b0; padding: 8px; border: none; }
            QTableWidgetItem { color: white; padding: 8px; }
        """)
        tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        return tabla

    def cambiar_periodo(self, periodo):
        self.periodo_actual = periodo
        nombres = {"hoy": "Hoy", "semana": "Últimos 7 días", "mes": "Este mes", "anio": "Este año"}
        self.lbl_periodo.setText(f"Mostrando: {nombres.get(periodo, periodo)}")
        self.cargar_datos()

    def cargar_datos(self):
        try:
            # Conteo tickets
            r_conteo = requests.get(f"{API_URL}/reportes/conteo-tickets", timeout=5)
            if r_conteo.status_code == 200:
                conteo = r_conteo.json()
                self.card_tickets_hoy[1].setText(str(conteo["tickets_hoy"]))
                self.card_tickets_semana[1].setText(str(conteo["tickets_semana"]))
                self.card_tickets_semana_pasada[1].setText(str(conteo["tickets_semana_pasada"]))
                self.card_tickets_mes[1].setText(str(conteo["tickets_mes"]))
                self.card_tickets_mes_pasado[1].setText(str(conteo["tickets_mes_pasado"]))

                alertas = []
                if conteo.get("alerta_semana"):
                    alertas.append(conteo["alerta_semana"])
                if conteo.get("alerta_mes"):
                    alertas.append(conteo["alerta_mes"])
                if alertas:
                    self.lbl_alerta.setText("  |  ".join(alertas))
                    self.lbl_alerta.show()
                else:
                    self.lbl_alerta.hide()

            # Ventas por período
            endpoints = {"hoy": "/reportes/hoy", "semana": "/reportes/semana",
                        "mes": "/reportes/mes", "anio": "/reportes/anio"}
            r = requests.get(f"{API_URL}{endpoints[self.periodo_actual]}", timeout=5)
            if r.status_code == 200:
                datos = r.json()
                total = datos.get("total_vendido", 0)
                cantidad = datos.get("cantidad_ventas", 0)
                promedio = total / cantidad if cantidad > 0 else 0
                self.card_ventas[1].setText(f"${total:.2f}")
                self.card_cantidad[1].setText(str(cantidad))
                self.card_promedio[1].setText(f"${promedio:.2f}")

                ventas = datos.get("ventas", [])
                self.tabla_ventas.setRowCount(len(ventas))

                totales_metodo = {
                    "efectivo": 0, "tarjeta": 0,
                    "mercadopago_qr": 0, "transferencia": 0
                }

                for i, v in enumerate(ventas):
                    self.tabla_ventas.setItem(i, 0, QTableWidgetItem(v["numero"]))
                    self.tabla_ventas.setItem(i, 1, QTableWidgetItem(f"${float(v['total']):.2f}"))
                    metodo = v.get("metodo_pago", "efectivo")
                    nombres_m = {
                        "efectivo": "💵 Efectivo",
                        "tarjeta": "💳 Tarjeta",
                        "mercadopago_qr": "📱 QR/MP",
                        "transferencia": "🏦 Transf."
                    }
                    self.tabla_ventas.setItem(i, 2, QTableWidgetItem(nombres_m.get(metodo, metodo)))
                    self.tabla_ventas.setItem(i, 3, QTableWidgetItem(v["fecha"][:16]))
                    if metodo in totales_metodo:
                        totales_metodo[metodo] += float(v["total"])

                for key, lbl in self.cards_metodo.items():
                    lbl.setText(f"${totales_metodo.get(key, 0):.2f}")

            # Stock bajo
            r2 = requests.get(f"{API_URL}/reportes/stock-bajo", timeout=5)
            if r2.status_code == 200:
                self.card_stock_bajo[1].setText(str(len(r2.json())))

            # Top productos
            r3 = requests.get(f"{API_URL}/reportes/productos-mas-vendidos", timeout=5)
            if r3.status_code == 200:
                top = r3.json()
                self.tabla_top.setRowCount(len(top))
                for i, p in enumerate(top):
                    self.tabla_top.setItem(i, 0, QTableWidgetItem(p["nombre"]))
                    self.tabla_top.setItem(i, 1, QTableWidgetItem(str(p["cantidad"])))
                    self.tabla_top.setItem(i, 2, QTableWidgetItem(f"${p['facturado']:.2f}"))

        except Exception as e:
            print(f"Error cargando reportes: {e}")