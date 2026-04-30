import requests
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QFrame, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QMessageBox,
                             QScrollArea, QDateEdit, QLineEdit)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor, QBrush

API_URL = "http://127.0.0.1:8000"

from ui.theme import get_tema as _gt
_T = _gt()
_BG = _T["bg_app"]; _CARD = _T["bg_card"]; _TXT = _T["text_main"]
_MUT = _T["text_muted"]; _PRI = _T["primary"]; _DGR = _T["danger"]
_BOR = _T["border"]; _OK = _T["success"]

class ReportesScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.periodo_actual = "hoy"
        self.setup_ui()
        self.cargar_datos()

    def setup_ui(self):
        self.setStyleSheet(f"background-color: {_BG}; color: {_TXT};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        header_top = QHBoxLayout()
        titulo = QLabel("📊 Auditoría de Ventas")
        titulo.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        titulo.setStyleSheet(f"color: {_TXT}; background: transparent;")
        header_top.addWidget(titulo)
        header_top.addStretch()

        _btn_per_ss = f"QPushButton {{ background: {_T['primary_light']}; color: {_PRI}; border-radius: 6px; font-size: 12px; font-weight: bold; border: 1.5px solid {_PRI}; }} QPushButton:hover {{ background: {_PRI}; color: white; }}"
        for texto, key in [("Hoy","hoy"),("Semana","semana"),("Mes","mes"),("Año","anio")]:
            btn = QPushButton(texto)
            btn.setFixedHeight(34)
            btn.setFixedWidth(70)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(_btn_per_ss)
            btn.clicked.connect(lambda _, k=key: self.cambiar_periodo(k))
            header_top.addWidget(btn)
        layout.addLayout(header_top)

        filtros_lay = QHBoxLayout()

        busqueda_frame = QFrame()
        busqueda_frame.setStyleSheet(f"background: {_CARD}; border-radius: 8px; border: 1.5px solid {_BOR};")
        bus_lay = QHBoxLayout(busqueda_frame)
        bus_lay.setContentsMargins(10, 5, 10, 5)
        bus_lay.addWidget(QLabel("🔍"))
        self.input_buscar = QLineEdit()
        self.input_buscar.setPlaceholderText("Buscar ticket por número...")
        self.input_buscar.setStyleSheet("background: transparent; border: none; min-width: 200px;")
        self.input_buscar.textChanged.connect(self.filtrar_tabla_local)
        bus_lay.addWidget(self.input_buscar)
        filtros_lay.addWidget(busqueda_frame)

        filtros_lay.addStretch()

        filtros_lay.addWidget(QLabel("Desde:"))
        self.fecha_desde = QDateEdit(QDate.currentDate().addDays(-7))
        self.fecha_desde.setCalendarPopup(True)
        filtros_lay.addWidget(self.fecha_desde)

        filtros_lay.addWidget(QLabel("Hasta:"))
        self.fecha_hasta = QDateEdit(QDate.currentDate())
        self.fecha_hasta.setCalendarPopup(True)
        filtros_lay.addWidget(self.fecha_hasta)

        btn_filtrar = QPushButton("Filtrar")
        btn_filtrar.setFixedSize(80, 34)
        btn_filtrar.setStyleSheet(f"QPushButton {{ background: {_PRI}; color: white; border-radius: 6px; font-weight: bold; }} QPushButton:hover {{ background: {_T['primary_hover']}; }}")
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

        # Historial productos con filtro de fechas
        top_vlay = QVBoxLayout()

        # Cabecera con filtros
        top_header = QHBoxLayout()
        top_header.addWidget(QLabel("📦 PRODUCTOS VENDIDOS", styleSheet="color: #f39c12; font-size: 11px; font-weight: bold;"))
        top_header.addStretch()
        top_vlay.addLayout(top_header)

        # Filtros de fecha para productos
        prod_filtros = QHBoxLayout()
        prod_filtros.addWidget(QLabel("Desde:", styleSheet="color: #a0a0b0; font-size: 11px;"))
        self.prod_desde = QDateEdit(QDate.currentDate().addDays(-30))
        self.prod_desde.setCalendarPopup(True)
        self.prod_desde.setFixedHeight(28)
        self.prod_desde.setStyleSheet("background: #0f3460; border-radius: 4px; color: white; font-size: 11px; padding: 2px 4px;")
        prod_filtros.addWidget(self.prod_desde)

        prod_filtros.addWidget(QLabel("Hasta:", styleSheet="color: #a0a0b0; font-size: 11px;"))
        self.prod_hasta = QDateEdit(QDate.currentDate())
        self.prod_hasta.setCalendarPopup(True)
        self.prod_hasta.setFixedHeight(28)
        self.prod_hasta.setStyleSheet("background: #0f3460; border-radius: 4px; color: white; font-size: 11px; padding: 2px 4px;")
        prod_filtros.addWidget(self.prod_hasta)

        btn_prod = QPushButton("Filtrar")
        btn_prod.setFixedSize(60, 28)
        btn_prod.setStyleSheet("background: #e94560; border-radius: 4px; font-weight: bold; color: white; font-size: 11px;")
        btn_prod.clicked.connect(self.cargar_productos_por_fecha)
        prod_filtros.addWidget(btn_prod)
        top_vlay.addLayout(prod_filtros)

        self.tabla_top = QTableWidget()
        self.tabla_top.setColumnCount(4)
        self.tabla_top.setHorizontalHeaderLabels(["Producto", "Cant.", "Tickets", "Total $"])
        self.tabla_top.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabla_top.setColumnWidth(1, 60)
        self.tabla_top.setColumnWidth(2, 60)
        self.tabla_top.setColumnWidth(3, 90)
        self.tabla_top.setStyleSheet("background: #16213e; color: white; gridline-color: #0f3460;")
        top_vlay.addWidget(self.tabla_top)

        self.lbl_prod_total = QLabel("")
        self.lbl_prod_total.setStyleSheet("color: #27ae60; font-size: 11px; font-weight: bold;")
        top_vlay.addWidget(self.lbl_prod_total)

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

                # Top Productos — sincronizar fechas con el período seleccionado
                if self.periodo_actual == "hoy":
                    hoy = QDate.currentDate()
                    self.prod_desde.setDate(hoy)
                    self.prod_hasta.setDate(hoy)
                elif self.periodo_actual == "semana":
                    self.prod_desde.setDate(QDate.currentDate().addDays(-7))
                    self.prod_hasta.setDate(QDate.currentDate())
                elif self.periodo_actual == "mes":
                    self.prod_desde.setDate(QDate(QDate.currentDate().year(), QDate.currentDate().month(), 1))
                    self.prod_hasta.setDate(QDate.currentDate())
                elif self.periodo_actual == "anio":
                    self.prod_desde.setDate(QDate(QDate.currentDate().year(), 1, 1))
                    self.prod_hasta.setDate(QDate.currentDate())
                elif self.periodo_actual == "rango":
                    self.prod_desde.setDate(self.fecha_desde.date())
                    self.prod_hasta.setDate(self.fecha_hasta.date())
                self.cargar_productos_por_fecha()

        except Exception as e:
            print(f"Error en reportes: {e}")

    def cargar_productos_por_fecha(self):
        desde = self.prod_desde.date().toString("yyyy-MM-dd")
        hasta = self.prod_hasta.date().toString("yyyy-MM-dd")
        try:
            r = requests.get(f"{API_URL}/reportes/productos-por-fecha",
                params={"desde": desde, "hasta": hasta}, timeout=8)
            if r.status_code == 200:
                productos = r.json()
                self.tabla_top.setRowCount(len(productos))
                total_monto = 0.0
                total_cant  = 0.0
                for i, p in enumerate(productos):
                    self.tabla_top.setItem(i, 0, QTableWidgetItem(p["nombre"]))
                    item_cant = QTableWidgetItem(f"{float(p['cantidad']):g}")
                    item_cant.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.tabla_top.setItem(i, 1, item_cant)
                    item_tick = QTableWidgetItem(str(p["tickets"]))
                    item_tick.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.tabla_top.setItem(i, 2, item_tick)
                    self.tabla_top.setItem(i, 3, QTableWidgetItem(f"${float(p['facturado']):,.0f}"))
                    total_cant  += float(p["cantidad"])
                    total_monto += float(p["facturado"])
                self.lbl_prod_total.setText(
                    f"{len(productos)} productos · {total_cant:,.0f} unid. · ${total_monto:,.0f} total")
            else:
                self.tabla_top.setRowCount(0)
                self.lbl_prod_total.setText("Sin datos")
        except Exception as e:
            print(f"Error productos: {e}")

    def showEvent(self, event):
        super().showEvent(event)
        self.cargar_datos()    