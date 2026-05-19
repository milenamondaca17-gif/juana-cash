import requests, os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QFrame, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QMessageBox,
                             QScrollArea, QDateEdit, QLineEdit, QFileDialog)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor, QBrush

API_URL = "http://127.0.0.1:8000"

from ui.theme import get_tema as _gt
_T = _gt()
_BG = _T["bg_app"]; _CARD = _T["bg_card"]; _TXT = _T["text_main"]
_MUT = _T["text_muted"]; _PRI = _T["primary"]; _DGR = _T["danger"]
_BOR = _T["border"]; _OK = _T["success"]

def _p(v):
    return f"${float(v):,.0f}".replace(",", ".")

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

        btn_pdf = QPushButton("📄 PDF")
        btn_pdf.setFixedSize(80, 34)
        btn_pdf.setStyleSheet("QPushButton { background: #7c3aed; color: white; border-radius: 6px; font-weight: bold; } QPushButton:hover { background: #6d28d9; }")
        btn_pdf.clicked.connect(self._exportar_pdf)
        filtros_lay.addWidget(btn_pdf)
        
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

        # ── DEPARTAMENTOS (CARNICERÍA / FIAMBRERÍA) ──────────────────────────
        deptos_frame = QFrame()
        deptos_frame.setStyleSheet("background: #16213e; border-radius: 12px;")
        deptos_lay = QHBoxLayout(deptos_frame)
        deptos_lay.setContentsMargins(12, 8, 12, 8)
        deptos_lay.setSpacing(12)

        carne_card = QFrame()
        carne_card.setStyleSheet("background: #1a2744; border-left: 3px solid #e74c3c; border-radius: 8px;")
        carne_l = QVBoxLayout(carne_card)
        carne_l.setContentsMargins(12, 8, 12, 8)
        carne_l.addWidget(QLabel("🥩 CARNICERÍA", styleSheet="color: #e74c3c; font-size: 10px; font-weight: bold; background: transparent;"))
        self.lbl_carne_val = QLabel("$0", styleSheet="color: white; font-size: 20px; font-weight: bold; background: transparent;")
        self.lbl_carne_comp = QLabel("", styleSheet="color: #a0a0b0; font-size: 10px; background: transparent;")
        carne_l.addWidget(self.lbl_carne_val)
        carne_l.addWidget(self.lbl_carne_comp)

        fiamb_card = QFrame()
        fiamb_card.setStyleSheet("background: #1a2744; border-left: 3px solid #f39c12; border-radius: 8px;")
        fiamb_l = QVBoxLayout(fiamb_card)
        fiamb_l.setContentsMargins(12, 8, 12, 8)
        fiamb_l.addWidget(QLabel("🍖 FIAMBRERÍA", styleSheet="color: #f39c12; font-size: 10px; font-weight: bold; background: transparent;"))
        self.lbl_fiamb_val = QLabel("$0", styleSheet="color: white; font-size: 20px; font-weight: bold; background: transparent;")
        self.lbl_fiamb_comp = QLabel("", styleSheet="color: #a0a0b0; font-size: 10px; background: transparent;")
        fiamb_l.addWidget(self.lbl_fiamb_val)
        fiamb_l.addWidget(self.lbl_fiamb_comp)

        deptos_lay.addWidget(carne_card)
        deptos_lay.addWidget(fiamb_card)
        deptos_lay.addStretch()
        layout.addWidget(deptos_frame)

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
                
                self.card_total[1].setText(_p(total_periodo))
                self.card_pc[1].setText(_p(total_pc))
                self.card_celular[1].setText(_p(total_celular))

                self.card_tickets[1].setText(str(len(ventas)))
                promedio = total_periodo / len(ventas) if ventas else 0
                self.card_promedio[1].setText(_p(promedio))

                # Limpieza de métodos
                totales_metodo = {k: 0.0 for k in self.cards_metodo.keys()}
                
                # Llenado de tabla de ventas e inteligencia de cobro mixto
                self.tabla_ventas.setRowCount(len(ventas))
                for i, v in enumerate(ventas):
                    self.tabla_ventas.setItem(i, 0, QTableWidgetItem(str(v["numero"])))
                    self.tabla_ventas.setItem(i, 1, QTableWidgetItem(_p(float(v['total']))))
                    
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
                    lbl.setText(_p(totales_metodo[k]))

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
                self._cargar_departamentos()

        except Exception as e:
            print(f"Error en reportes: {e}")

    def _cargar_departamentos(self):
        import calendar as _cal
        from datetime import date as _date, timedelta as _td

        hoy = _date.today()
        if self.periodo_actual == "hoy":
            d_act, h_act = hoy.isoformat(), hoy.isoformat()
            d_prv = h_prv = (hoy - _td(days=1)).isoformat()
            label_prv = "vs ayer"
        elif self.periodo_actual == "semana":
            d_act = (hoy - _td(days=7)).isoformat(); h_act = hoy.isoformat()
            d_prv = (hoy - _td(days=14)).isoformat(); h_prv = (hoy - _td(days=8)).isoformat()
            label_prv = "vs sem. ant."
        elif self.periodo_actual == "mes":
            ini = hoy.replace(day=1)
            d_act = ini.isoformat(); h_act = hoy.isoformat()
            p_ini = _date(ini.year - 1, 12, 1) if ini.month == 1 else _date(ini.year, ini.month - 1, 1)
            p_dia = min(hoy.day, _cal.monthrange(p_ini.year, p_ini.month)[1])
            d_prv = p_ini.isoformat(); h_prv = _date(p_ini.year, p_ini.month, p_dia).isoformat()
            label_prv = "vs mes ant."
        elif self.periodo_actual == "anio":
            d_act = hoy.replace(month=1, day=1).isoformat(); h_act = hoy.isoformat()
            d_prv = _date(hoy.year - 1, 1, 1).isoformat()
            h_prv = _date(hoy.year - 1, hoy.month, min(hoy.day, _cal.monthrange(hoy.year - 1, hoy.month)[1])).isoformat()
            label_prv = "vs año ant."
        elif self.periodo_actual == "rango":
            d_act = self.fecha_desde.date().toString("yyyy-MM-dd")
            h_act = self.fecha_hasta.date().toString("yyyy-MM-dd")
            desde_d = self.fecha_desde.date().toPyDate()
            hasta_d = self.fecha_hasta.date().toPyDate()
            delta = (hasta_d - desde_d).days + 1
            d_prv = (desde_d - _td(days=delta)).isoformat()
            h_prv = (desde_d - _td(days=1)).isoformat()
            label_prv = "vs período ant."
        else:
            return
        try:
            r_act = requests.get(f"{API_URL}/reportes/departamentos",
                params={"desde": f"{d_act}T00:00:00", "hasta": f"{h_act}T23:59:59"}, timeout=5)
            r_prv = requests.get(f"{API_URL}/reportes/departamentos",
                params={"desde": f"{d_prv}T00:00:00", "hasta": f"{h_prv}T23:59:59"}, timeout=5)
            act = r_act.json() if r_act.status_code == 200 else {}
            prv = r_prv.json() if r_prv.status_code == 200 else {}
            carne_a = float(act.get("carniceria", 0)); carne_p = float(prv.get("carniceria", 0))
            fiamb_a = float(act.get("fiambreria", 0)); fiamb_p = float(prv.get("fiambreria", 0))
            self.lbl_carne_val.setText(_p(carne_a))
            self.lbl_fiamb_val.setText(_p(fiamb_a))
            def _cmp(a, p):
                if p == 0:
                    return "", "#a0a0b0"
                pct = ((a - p) / p) * 100
                return (f"↑ {pct:.1f}% {label_prv}", "#27ae60") if pct >= 0 else (f"↓ {abs(pct):.1f}% {label_prv}", "#e74c3c")
            txt_c, col_c = _cmp(carne_a, carne_p)
            txt_f, col_f = _cmp(fiamb_a, fiamb_p)
            self.lbl_carne_comp.setText(txt_c)
            self.lbl_carne_comp.setStyleSheet(f"color: {col_c}; font-size: 10px; background: transparent;")
            self.lbl_fiamb_comp.setText(txt_f)
            self.lbl_fiamb_comp.setStyleSheet(f"color: {col_f}; font-size: 10px; background: transparent;")
        except Exception as e:
            print(f"Error departamentos: {e}")

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
                    self.tabla_top.setItem(i, 3, QTableWidgetItem(_p(float(p['facturado']))))
                    total_cant  += float(p["cantidad"])
                    total_monto += float(p["facturado"])
                self.lbl_prod_total.setText(
                    f"{len(productos)} productos · {total_cant:,.0f} unid. · {_p(total_monto)} total")
            else:
                self.tabla_top.setRowCount(0)
                self.lbl_prod_total.setText("Sin datos")
        except Exception as e:
            print(f"Error productos: {e}")

    def _exportar_pdf(self):
        from datetime import date as _date
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors as _rl_colors
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
            from reportlab.lib.styles import ParagraphStyle
            from reportlab.lib.units import cm
        except ImportError:
            QMessageBox.critical(self, "Error", "Librería reportlab no disponible.")
            return

        periodo_labels = {"hoy": "Hoy", "semana": "Ultimos 7 dias", "mes": "Este mes", "anio": "Este anio", "rango": "Rango"}
        label = periodo_labels.get(self.periodo_actual, self.periodo_actual)
        nombre_def = f"JuanaCash_Reporte_{self.periodo_actual}_{_date.today().strftime('%Y%m%d')}.pdf"
        escritorio = os.path.join(os.path.expanduser("~"), "Desktop")
        ruta, _ = QFileDialog.getSaveFileName(self, "Guardar PDF", os.path.join(escritorio, nombre_def), "PDF (*.pdf)")
        if not ruta:
            return

        # Datos frescos
        try:
            url = f"{API_URL}/reportes/{self.periodo_actual}"
            params = {"desde": self.fecha_desde.date().toString("yyyy-MM-dd"),
                      "hasta": self.fecha_hasta.date().toString("yyyy-MM-dd")} if self.periodo_actual == "rango" else {}
            r = requests.get(url, params=params, timeout=10)
            if r.status_code != 200:
                QMessageBox.warning(self, "Error", "No se pudieron obtener los datos."); return
            d = r.json()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Sin conexion: {e}"); return

        desde_p = self.prod_desde.date().toString("yyyy-MM-dd")
        hasta_p = self.prod_hasta.date().toString("yyyy-MM-dd")
        try:
            r2 = requests.get(f"{API_URL}/reportes/productos-por-fecha",
                              params={"desde": desde_p, "hasta": hasta_p}, timeout=10)
            productos = r2.json() if r2.status_code == 200 else []
        except Exception:
            productos = []

        def _fmt(v): return f"${float(v):,.0f}".replace(",", ".")

        ventas = [v for v in d.get("ventas", []) if v.get("estado") == "completada"]
        total   = sum(float(v["total"]) for v in ventas)
        tickets = len(ventas)
        prom    = total / tickets if tickets > 0 else 0

        # Desglose metodos
        desglose = {}
        for v in ventas:
            m = v.get("metodo_pago", "efectivo")
            desglose[m] = desglose.get(m, 0.0) + float(v["total"])

        doc = SimpleDocTemplate(ruta, pagesize=A4,
                                leftMargin=1.5*cm, rightMargin=1.5*cm,
                                topMargin=2*cm, bottomMargin=2*cm)

        _ROJO  = _rl_colors.HexColor("#e94560")
        _GRIS  = _rl_colors.HexColor("#555555")
        _DARK  = _rl_colors.HexColor("#1a1a2e")
        _WHITE = _rl_colors.white

        t_titulo = ParagraphStyle("titulo", fontSize=20, fontName="Helvetica-Bold", textColor=_ROJO, spaceAfter=4)
        t_sub    = ParagraphStyle("sub",    fontSize=11, fontName="Helvetica",      textColor=_GRIS, spaceAfter=14)
        t_sec    = ParagraphStyle("sec",    fontSize=12, fontName="Helvetica-Bold", textColor=_DARK, spaceBefore=12, spaceAfter=6)

        story = [
            Paragraph("JUANA CASH — REPORTE DE VENTAS", t_titulo),
            Paragraph(f"{label}   |   Generado: {_date.today().strftime('%d/%m/%Y')}", t_sub),
        ]

        # Tabla resumen
        story.append(Paragraph("Resumen", t_sec))
        resumen_data = [["Total periodo", "Tickets", "Ticket promedio"],
                        [_fmt(total), str(tickets), _fmt(prom)]]
        tbl_res = Table(resumen_data, colWidths=[5.5*cm, 4*cm, 5.5*cm])
        tbl_res.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), _DARK),
            ("TEXTCOLOR",  (0,0), (-1,0), _WHITE),
            ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",   (0,0), (-1,0), 10),
            ("FONTSIZE",   (0,1), (-1,1), 13),
            ("FONTNAME",   (0,1), (-1,1), "Helvetica-Bold"),
            ("TEXTCOLOR",  (0,1), (-1,1), _ROJO),
            ("ALIGN",      (0,0), (-1,-1), "CENTER"),
            ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0,1), (-1,1), [_rl_colors.HexColor("#f8f8f8")]),
            ("BOX",        (0,0), (-1,-1), 0.5, _rl_colors.HexColor("#cccccc")),
            ("INNERGRID",  (0,0), (-1,-1), 0.3, _rl_colors.HexColor("#dddddd")),
            ("TOPPADDING", (0,0), (-1,-1), 8),
            ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ]))
        story.append(tbl_res)

        # Tabla metodos de pago
        if desglose:
            story.append(Paragraph("Metodos de pago", t_sec))
            metodos_data = [["Metodo", "Total"]] + [[k.replace("_", " ").title(), _fmt(v)] for k, v in sorted(desglose.items(), key=lambda x: -x[1])]
            tbl_met = Table(metodos_data, colWidths=[9*cm, 6*cm])
            tbl_met.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), _DARK),
                ("TEXTCOLOR",  (0,0), (-1,0), _WHITE),
                ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
                ("FONTSIZE",   (0,0), (-1,-1), 10),
                ("ROWBACKGROUNDS", (0,1), (-1,-1), [_rl_colors.white, _rl_colors.HexColor("#f8f8f8")]),
                ("ALIGN",      (1,0), (1,-1), "RIGHT"),
                ("BOX",        (0,0), (-1,-1), 0.5, _rl_colors.HexColor("#cccccc")),
                ("INNERGRID",  (0,0), (-1,-1), 0.3, _rl_colors.HexColor("#dddddd")),
                ("TOPPADDING", (0,0), (-1,-1), 6),
                ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ]))
            story.append(tbl_met)

        # Tabla productos
        if productos:
            story.append(Paragraph(f"Productos vendidos ({len(productos)})", t_sec))
            prod_data = [["Producto", "Cant.", "Tickets", "Total"]]
            for p in productos[:50]:
                prod_data.append([p["nombre"], f"{float(p['cantidad']):g}", str(p["tickets"]), _fmt(float(p["facturado"]))])
            tbl_prod = Table(prod_data, colWidths=[9*cm, 2.5*cm, 2.5*cm, 4*cm])
            tbl_prod.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), _DARK),
                ("TEXTCOLOR",  (0,0), (-1,0), _WHITE),
                ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
                ("FONTSIZE",   (0,0), (-1,-1), 9),
                ("ROWBACKGROUNDS", (0,1), (-1,-1), [_rl_colors.white, _rl_colors.HexColor("#f8f8f8")]),
                ("ALIGN",      (1,0), (-1,-1), "CENTER"),
                ("ALIGN",      (3,0), (3,-1), "RIGHT"),
                ("BOX",        (0,0), (-1,-1), 0.5, _rl_colors.HexColor("#cccccc")),
                ("INNERGRID",  (0,0), (-1,-1), 0.3, _rl_colors.HexColor("#dddddd")),
                ("TOPPADDING", (0,0), (-1,-1), 5),
                ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ]))
            story.append(tbl_prod)

        try:
            doc.build(story)
            QMessageBox.information(self, "PDF generado", f"Guardado en:\n{ruta}")
        except Exception as e:
            QMessageBox.critical(self, "Error al generar PDF", str(e))

    def showEvent(self, event):
        super().showEvent(event)
        self.cargar_datos()    