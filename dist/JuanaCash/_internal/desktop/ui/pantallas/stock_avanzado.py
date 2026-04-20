import requests
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QLineEdit, QFrame, QMessageBox,
                              QTableWidget, QTableWidgetItem, QHeaderView,
                              QDialog, QDoubleSpinBox, QTabWidget, QScrollArea,
                              QGridLayout, QProgressBar)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor

API_URL = "http://127.0.0.1:8000"

COLORES_ALERTA = {
    "sin_stock": "#e74c3c",
    "critico":   "#e94560",
    "bajo":      "#f39c12",
    "moderado":  "#3498db",
    None:        "#27ae60",
}

LABELS_ALERTA = {
    "sin_stock": "❌ Sin stock",
    "critico":   "🔴 Crítico",
    "bajo":      "🟡 Bajo",
    "moderado":  "🔵 Moderado",
    None:        "✅ OK",
}


class InventarioRapidoDialog(QDialog):
    """Diálogo para hacer inventario rápido escaneando o buscando productos."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📋 Inventario Rápido")
        self.setMinimumSize(700, 500)
        self.setStyleSheet("background-color: #1a1a2e; color: white;")
        self.ajustes = {}  # producto_id -> {nombre, stock_nuevo}
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        titulo = QLabel("📋 Inventario Rápido")
        titulo.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        titulo.setStyleSheet("color: #f39c12;")
        layout.addWidget(titulo)

        instruccion = QLabel("Escaneá o buscá cada producto e ingresá el stock real contado.")
        instruccion.setStyleSheet("color: #a0a0b0; font-size: 12px;")
        layout.addWidget(instruccion)

        # Buscador
        busq = QHBoxLayout()
        self.input_buscar = QLineEdit()
        self.input_buscar.setPlaceholderText("Escaneá código o escribí nombre...")
        self.input_buscar.setFixedHeight(44)
        self.input_buscar.setStyleSheet("QLineEdit { background: #0f3460; border: 2px solid #f39c12; border-radius: 8px; padding: 0 14px; color: white; font-size: 14px; }")
        self.input_buscar.returnPressed.connect(self.buscar_producto)
        busq.addWidget(self.input_buscar)
        btn_b = QPushButton("Buscar")
        btn_b.setFixedSize(90, 44)
        btn_b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_b.setStyleSheet("QPushButton { background: #f39c12; color: white; border-radius: 8px; font-size: 13px; font-weight: bold; }")
        btn_b.clicked.connect(self.buscar_producto)
        busq.addWidget(btn_b)
        layout.addLayout(busq)

        # Tabla de ajustes
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels(["Producto", "Stock actual", "Stock contado", "Diferencia"])
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabla.setColumnWidth(1, 110)
        self.tabla.setColumnWidth(2, 120)
        self.tabla.setColumnWidth(3, 100)
        self.tabla.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tabla.setStyleSheet("""
            QTableWidget { background: #16213e; border: 1px solid #0f3460; border-radius: 8px; gridline-color: #0f3460; }
            QHeaderView::section { background: #0f3460; color: #a0a0b0; padding: 6px; border: none; }
            QTableWidgetItem { color: white; padding: 6px; }
        """)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.tabla)

        self.lbl_total = QLabel("0 productos en cola")
        self.lbl_total.setStyleSheet("color: #a0a0b0; font-size: 12px;")
        layout.addWidget(self.lbl_total)

        btns = QHBoxLayout()
        btn_limpiar = QPushButton("🗑 Limpiar")
        btn_limpiar.setFixedHeight(40)
        btn_limpiar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_limpiar.setStyleSheet("QPushButton { background: transparent; color: #e94560; border: 1px solid #e94560; border-radius: 8px; font-size: 13px; }")
        btn_limpiar.clicked.connect(self.limpiar)
        btns.addWidget(btn_limpiar)
        btns.addStretch()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setFixedHeight(40)
        btn_cancelar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_cancelar.setStyleSheet("QPushButton { background: transparent; color: #a0a0b0; border: 1px solid #a0a0b0; border-radius: 8px; }")
        btn_cancelar.clicked.connect(self.reject)
        btns.addWidget(btn_cancelar)
        btn_aplicar = QPushButton("✅ Aplicar todo")
        btn_aplicar.setFixedHeight(40)
        btn_aplicar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_aplicar.setStyleSheet("QPushButton { background: #f39c12; color: white; border-radius: 8px; font-size: 13px; font-weight: bold; padding: 0 16px; }")
        btn_aplicar.clicked.connect(self.aplicar)
        btns.addWidget(btn_aplicar)
        layout.addLayout(btns)

    def buscar_producto(self):
        texto = self.input_buscar.text().strip()
        if not texto:
            return
        try:
            r = requests.get(f"{API_URL}/productos/buscar", params={"q": texto}, timeout=5)
            if r.status_code == 200:
                productos = r.json()
                if not productos:
                    QMessageBox.warning(self, "No encontrado", f"No se encontró: {texto}")
                    self.input_buscar.clear()
                    self.input_buscar.setFocus()
                    return
                p = productos[0]
                self.agregar_a_inventario(p)
                self.input_buscar.clear()
                self.input_buscar.setFocus()
        except Exception:
            QMessageBox.critical(self, "Error", "No se puede conectar al servidor")
        self.input_buscar.setFocus()

    def agregar_a_inventario(self, producto):
        pid = producto["id"]
        stock_actual = float(producto.get("stock_actual", 0))

        if pid in self.ajustes:
            QMessageBox.information(self, "Ya agregado",
                f"{producto['nombre']} ya está en la lista.\nStock contado actual: {self.ajustes[pid]['stock_nuevo']:.0f}")
            return

        # Diálogo para ingresar el stock contado
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Contar: {producto['nombre']}")
        dialog.setMinimumWidth(340)
        dialog.setStyleSheet("background-color: #1a1a2e; color: white;")
        lay = QVBoxLayout(dialog)
        lay.setSpacing(10)

        lbl = QLabel(f"Stock actual en sistema: {stock_actual:.0f}")
        lbl.setStyleSheet("color: #a0a0b0; font-size: 13px;")
        lay.addWidget(lbl)

        lbl2 = QLabel("Stock contado físicamente:")
        lbl2.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        lay.addWidget(lbl2)

        input_stock = QDoubleSpinBox()
        input_stock.setRange(0, 99999)
        input_stock.setDecimals(0)
        input_stock.setValue(stock_actual)
        input_stock.setFixedHeight(52)
        input_stock.setStyleSheet("QDoubleSpinBox { background: #0f3460; border: 2px solid #f39c12; border-radius: 8px; padding: 8px; color: white; font-size: 22px; font-weight: bold; }")
        lay.addWidget(input_stock)

        btns = QHBoxLayout()
        btn_c = QPushButton("Cancelar")
        btn_c.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_c.setFixedHeight(40)
        btn_c.setStyleSheet("QPushButton { background: transparent; color: #a0a0b0; border: 1px solid #a0a0b0; border-radius: 8px; }")
        btn_c.clicked.connect(dialog.reject)
        btns.addWidget(btn_c)
        btn_ok = QPushButton("✅ Confirmar")
        btn_ok.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_ok.setFixedHeight(40)
        btn_ok.setStyleSheet("QPushButton { background: #f39c12; color: white; border-radius: 8px; font-size: 13px; font-weight: bold; }")
        btn_ok.clicked.connect(dialog.accept)
        btns.addWidget(btn_ok)
        lay.addLayout(btns)

        if dialog.exec():
            stock_nuevo = input_stock.value()
            self.ajustes[pid] = {
                "nombre": producto["nombre"],
                "stock_actual": stock_actual,
                "stock_nuevo": stock_nuevo
            }
            self.actualizar_tabla()

    def actualizar_tabla(self):
        items = list(self.ajustes.items())
        self.tabla.setRowCount(len(items))
        for i, (pid, data) in enumerate(items):
            self.tabla.setItem(i, 0, QTableWidgetItem(data["nombre"]))
            self.tabla.setItem(i, 1, QTableWidgetItem(f"{data['stock_actual']:.0f}"))
            item_nuevo = QTableWidgetItem(f"{data['stock_nuevo']:.0f}")
            item_nuevo.setForeground(QColor("#f39c12"))
            self.tabla.setItem(i, 2, item_nuevo)
            dif = data["stock_nuevo"] - data["stock_actual"]
            item_dif = QTableWidgetItem(f"{'+' if dif >= 0 else ''}{dif:.0f}")
            item_dif.setForeground(QColor("#27ae60") if dif >= 0 else QColor("#e94560"))
            self.tabla.setItem(i, 3, item_dif)
        self.lbl_total.setText(f"{len(items)} producto{'s' if len(items) != 1 else ''} en cola")

    def limpiar(self):
        self.ajustes.clear()
        self.actualizar_tabla()

    def aplicar(self):
        if not self.ajustes:
            QMessageBox.warning(self, "Vacío", "No hay ajustes para aplicar")
            return
        resp = QMessageBox.question(self, "Confirmar",
            f"¿Aplicar {len(self.ajustes)} ajustes de stock?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp != QMessageBox.StandardButton.Yes:
            return
        try:
            payload = [
                {"producto_id": pid, "stock_nuevo": data["stock_nuevo"], "motivo": "Inventario rápido"}
                for pid, data in self.ajustes.items()
            ]
            r = requests.post(f"{API_URL}/stock/ajuste-masivo", json=payload, timeout=10)
            if r.status_code == 200:
                datos = r.json()
                QMessageBox.information(self, "✅ Listo",
                    f"Se ajustaron {datos['ajustados']} productos correctamente.")
                self.accept()
            else:
                QMessageBox.critical(self, "Error", "No se pudo aplicar el inventario")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se puede conectar al servidor\n{str(e)}")


class StockAvanzadoScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.datos_prediccion = []
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("background-color: #1a1a2e; color: white;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header
        header = QHBoxLayout()
        titulo = QLabel("📦 Stock Avanzado")
        titulo.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        titulo.setStyleSheet("color: white;")
        header.addWidget(titulo)
        header.addStretch()

        btn_inventario = QPushButton("📋 Inventario Rápido")
        btn_inventario.setFixedHeight(36)
        btn_inventario.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_inventario.setStyleSheet("QPushButton { background: #f39c12; color: white; border-radius: 8px; font-size: 13px; font-weight: bold; padding: 0 14px; } QPushButton:hover { background: #d68910; }")
        btn_inventario.clicked.connect(self.abrir_inventario)
        header.addWidget(btn_inventario)

        btn_act = QPushButton("🔄")
        btn_act.setFixedSize(36, 36)
        btn_act.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_act.setStyleSheet("QPushButton { background: #16213e; color: white; border-radius: 8px; } QPushButton:hover { background: #e94560; }")
        btn_act.clicked.connect(self.cargar_datos)
        header.addWidget(btn_act)
        layout.addLayout(header)

        # Cards resumen
        self.grid_cards = QHBoxLayout()
        self.card_sin_stock = self._card("❌ Sin stock", "0", "#e74c3c")
        self.card_critico   = self._card("🔴 Crítico (≤3 días)", "0", "#e94560")
        self.card_bajo      = self._card("🟡 Bajo (≤7 días)", "0", "#f39c12")
        self.card_ok        = self._card("✅ Con stock OK", "0", "#27ae60")
        for card, _ in [self.card_sin_stock, self.card_critico, self.card_bajo, self.card_ok]:
            self.grid_cards.addWidget(card)
        layout.addLayout(self.grid_cards)

        # Filtros
        filtros = QHBoxLayout()
        self.btns_filtro = {}
        for key, label, color in [
            ("todos", "Todos", "#a0a0b0"),
            ("sin_stock", "❌ Sin stock", "#e74c3c"),
            ("critico", "🔴 Crítico", "#e94560"),
            ("bajo", "🟡 Bajo", "#f39c12"),
            ("moderado", "🔵 Moderado", "#3498db"),
        ]:
            btn = QPushButton(label)
            btn.setFixedHeight(30)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.setStyleSheet(f"QPushButton {{ background: #16213e; color: {color}; border: 1px solid {color}; border-radius: 6px; font-size: 12px; padding: 0 10px; }} QPushButton:hover {{ background: {color}; color: white; }}")
            btn.clicked.connect(lambda _, k=key: self.filtrar(k))
            filtros.addWidget(btn)
            self.btns_filtro[key] = btn
        filtros.addStretch()

        self.input_buscar = QLineEdit()
        self.input_buscar.setPlaceholderText("🔍 Buscar producto...")
        self.input_buscar.setFixedWidth(200)
        self.input_buscar.setFixedHeight(30)
        self.input_buscar.setStyleSheet("QLineEdit { background: #16213e; border: 1px solid #e94560; border-radius: 6px; padding: 0 8px; color: white; font-size: 12px; }")
        self.input_buscar.textChanged.connect(lambda t: self.mostrar_datos(self.datos_filtrados))
        filtros.addWidget(self.input_buscar)
        layout.addLayout(filtros)

        # Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(7)
        self.tabla.setHorizontalHeaderLabels([
            "Producto", "Stock actual", "Stock mín.", "Vendido 30d",
            "Vel. diaria", "Días restantes", "Estado"
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabla.setColumnWidth(1, 100)
        self.tabla.setColumnWidth(2, 90)
        self.tabla.setColumnWidth(3, 100)
        self.tabla.setColumnWidth(4, 90)
        self.tabla.setColumnWidth(5, 110)
        self.tabla.setColumnWidth(6, 120)
        self.tabla.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tabla.setStyleSheet("""
            QTableWidget { background: #16213e; border: 1px solid #0f3460; border-radius: 8px; gridline-color: #0f3460; }
            QHeaderView::section { background: #0f3460; color: #a0a0b0; padding: 8px; border: none; }
            QTableWidgetItem { color: white; padding: 6px; }
        """)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.tabla)

        self.datos_filtrados = []
        self.filtro_activo = "todos"

    def _card(self, titulo, valor, color):
        card = QFrame()
        card.setStyleSheet(f"QFrame {{ background: #16213e; border-radius: 10px; border-left: 4px solid {color}; }}")
        card.setMinimumHeight(80)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(14, 10, 14, 10)
        lbl_t = QLabel(titulo)
        lbl_t.setStyleSheet("color: #a0a0b0; font-size: 11px;")
        cl.addWidget(lbl_t)
        lbl_v = QLabel(valor)
        lbl_v.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        lbl_v.setStyleSheet(f"color: {color};")
        cl.addWidget(lbl_v)
        return card, lbl_v

    def cargar_datos(self):
        try:
            r = requests.get(f"{API_URL}/stock/prediccion", timeout=8)
            if r.status_code == 200:
                self.datos_prediccion = r.json()
                self.actualizar_cards()
                self.filtrar(self.filtro_activo)
        except Exception:
            QMessageBox.warning(self, "Error", "No se pudo conectar al servidor")

    def actualizar_cards(self):
        sin_stock = sum(1 for p in self.datos_prediccion if p["alerta"] == "sin_stock")
        critico   = sum(1 for p in self.datos_prediccion if p["alerta"] == "critico")
        bajo      = sum(1 for p in self.datos_prediccion if p["alerta"] == "bajo")
        ok        = sum(1 for p in self.datos_prediccion if p["alerta"] is None)
        self.card_sin_stock[1].setText(str(sin_stock))
        self.card_critico[1].setText(str(critico))
        self.card_bajo[1].setText(str(bajo))
        self.card_ok[1].setText(str(ok))

    def filtrar(self, key):
        self.filtro_activo = key
        if key == "todos":
            self.datos_filtrados = self.datos_prediccion
        else:
            self.datos_filtrados = [p for p in self.datos_prediccion if p["alerta"] == key]
        self.mostrar_datos(self.datos_filtrados)

    def mostrar_datos(self, datos):
        texto = self.input_buscar.text().lower()
        if texto:
            datos = [p for p in datos if texto in p["nombre"].lower()]

        self.tabla.setRowCount(len(datos))
        for i, p in enumerate(datos):
            self.tabla.setItem(i, 0, QTableWidgetItem(p["nombre"]))

            item_stock = QTableWidgetItem(f"{p['stock_actual']:.0f}")
            if p["alerta"] in ("sin_stock", "critico"):
                item_stock.setForeground(QColor("#e94560"))
            elif p["alerta"] == "bajo":
                item_stock.setForeground(QColor("#f39c12"))
            self.tabla.setItem(i, 1, item_stock)

            self.tabla.setItem(i, 2, QTableWidgetItem(f"{p['stock_minimo']:.0f}"))
            self.tabla.setItem(i, 3, QTableWidgetItem(f"{p['vendido_30d']:.0f}"))
            self.tabla.setItem(i, 4, QTableWidgetItem(f"{p['velocidad_diaria']:.1f}/día"))

            dias = p["dias_restantes"]
            label_dias = f"{dias} días" if dias < 999 else "Sin datos"
            item_dias = QTableWidgetItem(label_dias)
            color_dias = COLORES_ALERTA.get(p["alerta"], "#27ae60")
            item_dias.setForeground(QColor(color_dias))
            self.tabla.setItem(i, 5, item_dias)

            label_estado = LABELS_ALERTA.get(p["alerta"], "✅ OK")
            item_estado = QTableWidgetItem(label_estado)
            item_estado.setForeground(QColor(COLORES_ALERTA.get(p["alerta"], "#27ae60")))
            self.tabla.setItem(i, 6, item_estado)

    def abrir_inventario(self):
        dialog = InventarioRapidoDialog(self)
        if dialog.exec():
            self.cargar_datos()

    def showEvent(self, event):
        super().showEvent(event)
        self.cargar_datos()
