import requests
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QFrame, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QMessageBox,
                             QScrollArea, QDateEdit, QLineEdit)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor, QBrush

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

        # ── CABECERA Y FILTROS ───────────────────────────────────────────────
        header_top = QHBoxLayout()
        titulo = QLabel("📊 Auditoría de Ventas")
        titulo.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        header_top.addWidget(titulo)
        header_top.addStretch()
        
        # Filtros rápidos
        for texto, key in [("Hoy","hoy"),("Semana","semana"),("Mes","mes"),("Año","anio")]:
            btn = QPushButton(texto)
            btn.setFixedHeight(34)
            btn.setFixedWidth(70)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton { background: #0f3460; color: #a0a0b0; border-radius: 6px; font-size: 12px; font-weight: bold; }
                QPushButton:hover { background: #16213e; color: white; border: 1px solid #e94560; }
            """)
            btn.clicked.connect(lambda _, k=key: self.cambiar_periodo(k))
            header_top.addWidget(btn)
        layout.addLayout(header_top)

        # Barra de búsqueda y fecha
        filtros_lay = QHBoxLayout()
        
        busqueda_frame = QFrame()
        busqueda_frame.setStyleSheet("background: #16213e; border-radius: 8px;")
        bus_lay = QHBoxLayout(busqueda_frame)
        bus_lay.setContentsMargins(10, 5, 10, 5)
        
        bus_lay.addWidget(QLabel("🔍"))
        self.input_buscar = QLineEdit()
        self.input_buscar.setPlaceholderText("Buscar ticket por número...")
        self.input_buscar.setStyleSheet("background: transparent; border: none; color: white; min-width: 200px;")
        self.input_buscar.textChanged.connect(self.filtrar_tabla_local)
        bus_lay.addWidget(self.input_buscar)
        filtros_lay.addWidget(busqueda_frame)

        filtros_lay.addStretch()
        
        filtros_lay.addWidget(QLabel("Desde:"))
        self.fecha_desde = QDateEdit(QDate.currentDate().addDays(-7))
        self.fecha_desde.setCalendarPopup(True)
        self.fecha_desde.setStyleSheet("background: #0f3460; padding: 5px; border-radius: 4px;")
        filtros_lay.addWidget(self.fecha_desde)

        filtros_lay.addWidget(QLabel("Hasta:"))
        self.fecha_hasta = QDateEdit(QDate.currentDate())
        self.fecha_hasta.setCalendarPopup(True)
        self.fecha_hasta.setStyleSheet("background: #0f3460; padding: 5px; border-radius: 4px;")
        filtros_lay.addWidget(self.fecha_hasta)

        btn_filtrar = QPushButton("Filtrar")
        btn_filtrar.setFixedSize(80, 32)
        btn_filtrar.setStyleSheet("background: #e94560; border-radius: 4px; font-weight: bold;")
        btn_filtrar.clicked.connect(lambda: self.cambiar_periodo("rango"))
        filtros_lay.addWidget(btn_filtrar)
        
        layout.addLayout(filtros_lay)

        # ── TARJETAS DE CONTEO (CON PC Y CELULAR) ────────────────────────────
        conteo_frame = QFrame()
        conteo_frame.setStyleSheet("background: #16213e; border-radius: 12px;")
        conteo_lay = QHBoxLayout(conteo_frame)
        
        self.card_total = self.crear_mini_card("TOTAL PERÍODO", "$0", "#e94560")
        self.card_pc = self.crear_mini_card("💻 MOSTRADOR", "$0", "#3B82F6")     # NUEVA TARJETA
        self.card_celular = self.crear_mini_card("📱 CELULAR", "$0", "#F59E0B") # NUEVA TARJETA
        self.card_tickets = self.crear_mini_card("CANT. TICKETS", "0", "#3498db")
        self.card_promedio = self.crear_mini_card("PROMEDIO", "$0", "#27ae60")
        
        conteo_lay.addWidget(self.card_total[0])
        conteo_lay.addWidget(self.card_pc[0])
        conteo_lay.addWidget(self.card_celular[0])
        conteo_lay.addWidget(self.card_tickets[0])
        conteo_lay.addWidget(self.card_promedio[0])
        layout.addWidget(conteo_frame)

        # ── MÉTODOS DE PAGO ──────────────────────────────────────────────────
        metodos_lay = QHBoxLayout()
        self.cards_metodo = {}
        config_metodos = [
            ("💵 Efectivo", "efectivo", "#27ae60"),
            ("💳 Tarjeta", "tarjeta", "#3498db"),
            ("📱 QR/MP", "mercadopago_qr", "#009ee3"),
            ("🏦 Transf.", "transferencia", "#9b59b6")
        ]
        for nom, key, col in config_metodos:
            card = QFrame()
            card.setStyleSheet(f"background: #16213e; border-left: 3px solid {col}; border-radius: 8px;")
            l = QVBoxLayout(card)
            l.addWidget(QLabel(nom, styleSheet=f"color: {col}; font-size: 10px; font-weight: bold;"))
            lbl_v = QLabel("$0")
            lbl_v.setStyleSheet(f"color: white; font-size: 14px; font-weight: bold;")
            l.addWidget(lbl_v)
            self.cards_metodo[key] = lbl_v
            metodos_lay.addWidget(card)
        layout.addLayout(metodos_lay)

        # ── TABLAS ───────────────────────────────────────────────────────────
        tablas_split = QHBoxLayout()
        
        # Historial de ventas
        ventas_vlay = QVBoxLayout()
        ventas_vlay.addWidget(QLabel("📜 HISTORIAL DETALLADO", styleSheet="color: #a0a0b0; font-size: 11px; font-weight: bold;"))
        self.tabla_ventas = QTableWidget()
        
        self.tabla_ventas.setColumnCount(5) # AHORA SON 5 COLUMNAS
        self.tabla_ventas.setHorizontalHeaderLabels(["Ticket", "Total", "Método", "Origen", "Hora"]) # SE AGREGA "ORIGEN"
        self.tabla_ventas.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_ventas.setStyleSheet("background: #16213e; gridline-color: #0f3460; color: white;")
        ventas_vlay.addWidget(self.tabla_ventas)
        tablas_split.addLayout(ventas_vlay, 3)

        # Ranking productos
        top_vlay = QVBoxLayout()
        top_vlay.addWidget(QLabel("🏆 TOP PRODUCTOS", styleSheet="color: #f39c12; font-size: 11px; font-weight: bold;"))
        self.tabla_top = QTableWidget()
        self.tabla_top.setColumnCount(2)
        self.tabla_top.setHorizontalHeaderLabels(["Producto", "Vendido"])
        self.tabla_top.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_top.setStyleSheet("background: #16213e; color: white;")
        top_vlay.addWidget(self.tabla_top)
        tablas_split.addLayout(top_vlay, 2)

        layout.addLayout(tablas_split)
    def crear_mini_card(self, titulo, valor, color):
        card = QFrame()
        l = QVBoxLayout(card)
        t = QLabel(titulo, styleSheet="color: #a0a0b0; font-size: 10px;")
        v = QLabel(valor, styleSheet=f"color: {color}; font-size: 24px; font-weight: bold;")
        l.addWidget(t)
        l.addWidget(v)
        return card, v

    def cambiar_periodo(self, periodo):
        self.periodo_actual = periodo
        self.cargar_datos()

    def filtrar_tabla_local(self):
        busqueda = self.input_buscar.text().lower()
        for i in range(self.tabla_ventas.rowCount()):
            num_ticket = self.tabla_ventas.item(i, 0).text().lower()
            self.tabla_ventas.setRowHidden(i, busqueda not in num_ticket)

    def cargar_datos(self):
        try:
            # Construimos la URL según el filtro
            url = f"{API_URL}/reportes/{self.periodo_actual}"
            if self.periodo_actual == "rango":
                params = {
                    "desde": self.fecha_desde.date().toString("yyyy-MM-dd"),
                    "hasta": self.fecha_hasta.date().toString("yyyy-MM-dd")
                }
                r = requests.get(url, params=params, timeout=5)
            else:
                r = requests.get(url, timeout=5)

            if r.status_code == 200:
                d = r.json()
                ventas = d.get("ventas", [])
                
                # TOTALES SEPARADOS (NUEVO)
                total_periodo = 0.0
                total_pc = 0.0
                total_celular = 0.0
                
                for v in ventas:
                    monto = float(v.get("total", 0))
                    total_periodo += monto
                    
                    origen = str(v.get("origen", "mostrador")).lower()
                    if origen == "celular":
                        total_celular += monto
                    else:
                        total_pc += monto
                
                self.card_total[1].setText(f"${total_periodo:,.2f}")
                self.card_pc[1].setText(f"${total_pc:,.2f}")
                self.card_celular[1].setText(f"${total_celular:,.2f}")
                
                self.card_tickets[1].setText(str(len(ventas)))
                promedio = total_periodo / len(ventas) if ventas else 0
                self.card_promedio[1].setText(f"${promedio:,.0f}")

                # Limpieza de métodos
                totales_metodo = {k: 0.0 for k in self.cards_metodo.keys()}
                
                # Llenado de tabla de ventas e inteligencia de cobro mixto
                self.tabla_ventas.setRowCount(len(ventas))
                for i, v in enumerate(ventas):
                    self.tabla_ventas.setItem(i, 0, QTableWidgetItem(str(v["numero"])))
                    self.tabla_ventas.setItem(i, 1, QTableWidgetItem(f"${float(v['total']):.2f}"))
                    
                    # Inteligencia de métodos (Soporta Mixto)
                    m1 = v.get("metodo_pago", "efectivo")
                    m2 = v.get("metodo_secundario")
                    txt_metodo = m1.upper()
                    
                    if m2:
                        txt_metodo = f"MIXTO"
                        monto2 = float(v.get("monto_secundario", 0))
                        monto1 = float(v["total"]) - monto2
                        if m1 in totales_metodo: totales_metodo[m1] += monto1
                        if m2 in totales_metodo: totales_metodo[m2] += monto2
                    else:
                        if m1 in totales_metodo: totales_metodo[m1] += float(v["total"])

                    self.tabla_ventas.setItem(i, 2, QTableWidgetItem(txt_metodo))
                    
                    # COLUMNA ORIGEN (NUEVA)
                    origen = str(v.get("origen", "mostrador")).lower()
                    if origen == "celular":
                        item_origen = QTableWidgetItem("📱 Celular")
                        item_origen.setForeground(QBrush(QColor("#F59E0B")))
                    else:
                        item_origen = QTableWidgetItem("💻 Mostrador")
                        item_origen.setForeground(QBrush(QColor("#3B82F6")))
                    
                    self.tabla_ventas.setItem(i, 3, item_origen)
                    
                    hora = v["fecha"].split("T")[1][:5] if "T" in v["fecha"] else v["fecha"][-8:-3]
                    self.tabla_ventas.setItem(i, 4, QTableWidgetItem(hora))

                # Actualizar cards de métodos
                for k, lbl in self.cards_metodo.items():
                    lbl.setText(f"${totales_metodo[k]:,.0f}")

                # Top Productos
                r_top = requests.get(f"{API_URL}/reportes/productos-mas-vendidos", timeout=5)
                if r_top.status_code == 200:
                    top = r_top.json()
                    self.tabla_top.setRowCount(len(top))
                    for i, p in enumerate(top):
                        self.tabla_top.setItem(i, 0, QTableWidgetItem(p["nombre"]))
                        self.tabla_top.setItem(i, 1, QTableWidgetItem(f"${p['facturado']:,.0f}"))

        except Exception as e:
            print(f"Error en reportes: {e}")

    def showEvent(self, event):
        super().showEvent(event)
        self.cargar_datos()    