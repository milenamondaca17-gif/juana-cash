import requests
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QLineEdit, QPushButton, QTableWidget,
                              QTableWidgetItem, QMessageBox, QFrame, QHeaderView,
                              QDialog, QDoubleSpinBox, QScrollArea,
                              QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QShortcut, QKeySequence
from datetime import datetime
import os

API_URL = "http://127.0.0.1:8000"

DEPARTAMENTOS = {
    "900": {"nombre": "Carnicería",  "icono": "🥩", "color": "#e74c3c"},
    "901": {"nombre": "Verdulería",  "icono": "🥬", "color": "#27ae60"},
    "902": {"nombre": "Panadería",   "icono": "🍞", "color": "#e67e22"},
    "903": {"nombre": "Fiambrería",  "icono": "🧀", "color": "#f39c12"},
    "904": {"nombre": "Lácteos",     "icono": "🥛", "color": "#3498db"},
    "905": {"nombre": "Limpieza",    "icono": "🧹", "color": "#9b59b6"},
    "906": {"nombre": "Bebidas",     "icono": "🍺", "color": "#1abc9c"},
    "907": {"nombre": "Cigarrería",  "icono": "🚬", "color": "#7f8c8d"},
    "908": {"nombre": "Confitería",  "icono": "🍬", "color": "#e91e8c"},
    "909": {"nombre": "Varios",      "icono": "📦", "color": "#95a5a6"},
}


class CobrarDialog(QDialog):
    def __init__(self, parent=None, total=0):
        super().__init__(parent)
        self.setWindowTitle("💳 Cobrar venta")
        self.setMinimumWidth(420)
        self.setStyleSheet("background-color: #1a1a2e; color: white;")
        self.total_original = total
        self.descuento_pct = 0
        self.total_final = total
        self.metodo_pago = "efectivo"
        self.btns_pago = {}
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        lbl_total = QLabel(f"Total: ${self.total_original:.2f}")
        lbl_total.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        lbl_total.setStyleSheet("color: #e94560;")
        lbl_total.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_total)

        desc_frame = QFrame()
        desc_frame.setStyleSheet("QFrame { background: #16213e; border-radius: 8px; }")
        desc_layout = QHBoxLayout(desc_frame)
        desc_layout.setContentsMargins(12, 8, 12, 8)
        lbl_desc = QLabel("Descuento (%):")
        lbl_desc.setStyleSheet("color: #a0a0b0; font-size: 13px;")
        desc_layout.addWidget(lbl_desc)
        self.input_pct = QDoubleSpinBox()
        self.input_pct.setRange(0, 100)
        self.input_pct.setSingleStep(5)
        self.input_pct.setDecimals(1)
        self.input_pct.setSuffix(" %")
        self.input_pct.setFixedHeight(40)
        self.input_pct.setFixedWidth(120)
        self.input_pct.setStyleSheet("QDoubleSpinBox { background: #0f3460; border: 1px solid #e94560; border-radius: 8px; padding: 6px; color: white; font-size: 15px; }")
        self.input_pct.valueChanged.connect(self.actualizar_total)
        desc_layout.addWidget(self.input_pct)
        layout.addWidget(desc_frame)

        self.lbl_total_final = QLabel(f"A cobrar: ${self.total_original:.2f}")
        self.lbl_total_final.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.lbl_total_final.setStyleSheet("color: #27ae60;")
        self.lbl_total_final.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_total_final)

        lbl_metodo = QLabel("Método de pago:")
        lbl_metodo.setStyleSheet("color: #a0a0b0; font-size: 13px; font-weight: bold;")
        layout.addWidget(lbl_metodo)

        metodos_layout = QHBoxLayout()
        metodos_layout.setSpacing(8)
        metodos = [
            ("💵", "Efectivo",      "efectivo",       "#27ae60"),
            ("💳", "Tarjeta",       "tarjeta",         "#3498db"),
            ("📱", "QR / MP",       "mercadopago_qr",  "#009ee3"),
            ("🏦", "Transferencia", "transferencia",   "#9b59b6"),
        ]
        for icono, nombre, key, color in metodos:
            btn = QPushButton(f"{icono}\n{nombre}")
            btn.setFixedSize(82, 64)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: #16213e;
                    color: #a0a0b0;
                    border: 2px solid #333;
                    border-radius: 10px;
                    font-size: 12px;
                }}
                QPushButton:hover {{ border: 2px solid {color}; color: white; }}
            """)
            btn.clicked.connect(lambda _, k=key, c=color: self.seleccionar_metodo(k, c))
            metodos_layout.addWidget(btn)
            self.btns_pago[key] = (btn, color)
        layout.addLayout(metodos_layout)

        self.vuelto_frame = QFrame()
        self.vuelto_frame.setStyleSheet("QFrame { background: #16213e; border-radius: 8px; border: 1px solid #27ae60; }")
        vuelto_layout = QVBoxLayout(self.vuelto_frame)
        vuelto_layout.setContentsMargins(12, 10, 12, 10)
        vuelto_layout.setSpacing(6)
        lbl_entrega = QLabel("El cliente entrega ($):")
        lbl_entrega.setStyleSheet("color: #a0a0b0; font-size: 13px;")
        vuelto_layout.addWidget(lbl_entrega)
        self.input_entrega = QLineEdit()
        self.input_entrega.setPlaceholderText("Ingresá el monto recibido...")
        self.input_entrega.setFixedHeight(48)
        self.input_entrega.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.input_entrega.setStyleSheet("""
            QLineEdit {
                background: #0f3460;
                border: 2px solid #27ae60;
                border-radius: 8px;
                padding: 0 16px;
                color: white;
                font-size: 20px;
                font-weight: bold;
            }
        """)
        self.input_entrega.textChanged.connect(self.calcular_vuelto)
        vuelto_layout.addWidget(self.input_entrega)
        self.lbl_vuelto = QLabel("Vuelto: —")
        self.lbl_vuelto.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        self.lbl_vuelto.setStyleSheet("color: #27ae60;")
        self.lbl_vuelto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vuelto_layout.addWidget(self.lbl_vuelto)
        layout.addWidget(self.vuelto_frame)

        btns = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setFixedHeight(44)
        btn_cancelar.setStyleSheet("QPushButton { background: transparent; color: #a0a0b0; border: 1px solid #a0a0b0; border-radius: 8px; }")
        btn_cancelar.clicked.connect(self.reject)
        btns.addWidget(btn_cancelar)
        self.btn_cobrar = QPushButton("✅ COBRAR")
        self.btn_cobrar.setFixedHeight(44)
        self.btn_cobrar.setStyleSheet("QPushButton { background: #27ae60; color: white; border-radius: 8px; font-size: 15px; font-weight: bold; }")
        self.btn_cobrar.clicked.connect(self.accept)
        btns.addWidget(self.btn_cobrar)
        layout.addLayout(btns)

        self.seleccionar_metodo("efectivo", "#27ae60")

    def calcular_vuelto(self):
        try:
            entrega = float(self.input_entrega.text().replace(",", "."))
            vuelto = entrega - self.total_final
            if vuelto < 0:
                self.lbl_vuelto.setText(f"⚠️ Falta: ${abs(vuelto):.2f}")
                self.lbl_vuelto.setStyleSheet("color: #e94560; font-size: 20px; font-weight: bold;")
            else:
                self.lbl_vuelto.setText(f"Vuelto: ${vuelto:.2f}")
                self.lbl_vuelto.setStyleSheet("color: #27ae60; font-size: 22px; font-weight: bold;")
        except ValueError:
            self.lbl_vuelto.setText("Vuelto: —")
            self.lbl_vuelto.setStyleSheet("color: #27ae60; font-size: 20px; font-weight: bold;")

    def seleccionar_metodo(self, key, color):
        self.metodo_pago = key
        nombres = {
            "efectivo": "Efectivo",
            "tarjeta": "Tarjeta",
            "mercadopago_qr": "QR / MP",
            "transferencia": "Transferencia"
        }
        for k, (btn, c) in self.btns_pago.items():
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: #16213e;
                    color: #a0a0b0;
                    border: 2px solid #333;
                    border-radius: 10px;
                    font-size: 12px;
                }}
                QPushButton:hover {{ border: 2px solid {c}; color: white; }}
            """)
        if key in self.btns_pago:
            btn, c = self.btns_pago[key]
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {color};
                    color: white;
                    border: 2px solid {color};
                    border-radius: 10px;
                    font-size: 12px;
                    font-weight: bold;
                }}
            """)
        self.vuelto_frame.setVisible(key == "efectivo")
        self.btn_cobrar.setText(f"✅ COBRAR — {nombres.get(key, key)}")
        self.btn_cobrar.setStyleSheet(f"QPushButton {{ background: {color}; color: white; border-radius: 8px; font-size: 15px; font-weight: bold; }}")

    def actualizar_total(self):
        pct = self.input_pct.value()
        ahorro = self.total_original * pct / 100
        self.total_final = self.total_original - ahorro
        self.descuento_pct = pct
        self.lbl_total_final.setText(f"A cobrar: ${self.total_final:.2f}")
        self.calcular_vuelto()


class EditarItemDialog(QDialog):
    def __init__(self, parent=None, item=None):
        super().__init__(parent)
        self.item = item
        self.setWindowTitle(f"✏️ Editar — {item['nombre']}")
        self.setMinimumWidth(340)
        self.setStyleSheet("background-color: #1a1a2e; color: white;")
        self.nuevo_precio = item["precio_unitario"]
        self.nueva_cantidad = item["cantidad"]
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        lbl_titulo = QLabel(f"✏️ {self.item['nombre']}")
        lbl_titulo.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        lbl_titulo.setStyleSheet("color: #e94560;")
        lbl_titulo.setWordWrap(True)
        layout.addWidget(lbl_titulo)
        lbl_precio = QLabel("Precio unitario ($):")
        lbl_precio.setStyleSheet("color: #a0a0b0; font-size: 13px;")
        layout.addWidget(lbl_precio)
        self.input_precio = QLineEdit()
        self.input_precio.setText(str(self.item["precio_unitario"]))
        self.input_precio.setFixedHeight(44)
        self.input_precio.setStyleSheet("QLineEdit { background: #0f3460; border: 1px solid #e94560; border-radius: 8px; padding: 10px; color: white; font-size: 16px; }")
        layout.addWidget(self.input_precio)
        lbl_cant = QLabel("Cantidad:")
        lbl_cant.setStyleSheet("color: #a0a0b0; font-size: 13px;")
        layout.addWidget(lbl_cant)
        self.input_cant = QLineEdit()
        self.input_cant.setText(str(self.item["cantidad"]))
        self.input_cant.setFixedHeight(44)
        self.input_cant.setStyleSheet("QLineEdit { background: #0f3460; border: 1px solid #e94560; border-radius: 8px; padding: 10px; color: white; font-size: 16px; }")
        layout.addWidget(self.input_cant)
        self.lbl_subtotal = QLabel(f"Subtotal: ${self.item['subtotal']:.2f}")
        self.lbl_subtotal.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.lbl_subtotal.setStyleSheet("color: #27ae60;")
        layout.addWidget(self.lbl_subtotal)
        self.input_precio.textChanged.connect(self.actualizar_subtotal)
        self.input_cant.textChanged.connect(self.actualizar_subtotal)
        btns = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setFixedHeight(44)
        btn_cancelar.setStyleSheet("QPushButton { background: transparent; color: #a0a0b0; border: 1px solid #a0a0b0; border-radius: 8px; }")
        btn_cancelar.clicked.connect(self.reject)
        btns.addWidget(btn_cancelar)
        btn_guardar = QPushButton("💾 Guardar")
        btn_guardar.setFixedHeight(44)
        btn_guardar.setStyleSheet("QPushButton { background: #e94560; color: white; border-radius: 8px; font-size: 14px; font-weight: bold; }")
        btn_guardar.clicked.connect(self.guardar)
        btns.addWidget(btn_guardar)
        layout.addLayout(btns)

    def actualizar_subtotal(self):
        try:
            precio = float(self.input_precio.text())
            cant = float(self.input_cant.text())
            self.lbl_subtotal.setText(f"Subtotal: ${precio * cant:.2f}")
        except ValueError:
            pass

    def guardar(self):
        try:
            self.nuevo_precio = float(self.input_precio.text())
            self.nueva_cantidad = float(self.input_cant.text())
        except ValueError:
            QMessageBox.warning(self, "Error", "Ingresá valores válidos")
            return
        self.accept()


class MontoDeptoInput(QLineEdit):
    def __init__(self, on_enter_callback, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.on_enter_callback = on_enter_callback

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.on_enter_callback()
            event.accept()
            return
        super().keyPressEvent(event)


class BuscadorConSugerencias(QLineEdit):
    def __init__(self, on_seleccionar_callback, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.on_seleccionar_callback = on_seleccionar_callback
        self.historial = []
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.buscar_sugerencias)
        self.textChanged.connect(self.on_texto_cambiado)

        self.lista = QListWidget(self)
        self.lista.setWindowFlags(Qt.WindowType.Popup)
        self.lista.setStyleSheet("""
            QListWidget {
                background: #16213e;
                border: 2px solid #e94560;
                border-radius: 8px;
                color: white;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 10px 16px;
                border-bottom: 1px solid #0f3460;
            }
            QListWidget::item:hover {
                background: #0f3460;
                color: #e94560;
            }
            QListWidget::item:selected {
                background: #e94560;
                color: white;
            }
        """)
        self.lista.itemClicked.connect(self.seleccionar_sugerencia)
        self.lista.hide()

    def on_texto_cambiado(self, texto):
        if len(texto) >= 2 and texto not in DEPARTAMENTOS:
            self.timer.start(300)
        elif len(texto) == 0:
            self.mostrar_historial()
        else:
            self.lista.hide()

    def mostrar_historial(self):
        if not self.historial:
            self.lista.hide()
            return
        self.lista.clear()
        for p in self.historial[-8:]:
            item = QListWidgetItem(f"🕐 {p['nombre']}  —  ${float(p['precio_venta']):.2f}")
            item.setData(Qt.ItemDataRole.UserRole, p)
            self.lista.addItem(item)
        pos = self.mapToGlobal(self.rect().bottomLeft())
        self.lista.move(pos)
        self.lista.resize(self.width(), min(len(self.historial), 8) * 44)
        self.lista.show()
        self.lista.raise_()

    def agregar_historial(self, producto):
        self.historial = [p for p in self.historial if p["id"] != producto["id"]]
        self.historial.append(producto)
        if len(self.historial) > 20:
            self.historial = self.historial[-20:]

    def buscar_sugerencias(self):
        texto = self.text().strip()
        if not texto or len(texto) < 2:
            self.lista.hide()
            return
        try:
            r = requests.get(f"{API_URL}/productos/buscar", params={"q": texto}, timeout=3)
            if r.status_code == 200:
                productos = r.json()
                if productos:
                    self.lista.clear()
                    for p in productos[:8]:
                        item = QListWidgetItem(f"{p['nombre']}  —  ${float(p['precio_venta']):.2f}")
                        item.setData(Qt.ItemDataRole.UserRole, p)
                        self.lista.addItem(item)
                    pos = self.mapToGlobal(self.rect().bottomLeft())
                    self.lista.move(pos)
                    self.lista.resize(self.width(), min(len(productos), 8) * 44)
                    self.lista.show()
                    self.lista.raise_()
                else:
                    self.lista.hide()
        except Exception:
            self.lista.hide()

    def seleccionar_sugerencia(self, item):
        producto = item.data(Qt.ItemDataRole.UserRole)
        self.lista.hide()
        self.clear()
        self.agregar_historial(producto)
        self.on_seleccionar_callback(producto)

    def keyPressEvent(self, event):
        if self.lista.isVisible():
            if event.key() == Qt.Key.Key_Down:
                self.lista.setFocus()
                self.lista.setCurrentRow(0)
                return
            elif event.key() == Qt.Key.Key_Escape:
                self.lista.hide()
                return
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.lista.hide()
        super().keyPressEvent(event)

    def focusOutEvent(self, event):
        QTimer.singleShot(200, self.lista.hide)
        super().focusOutEvent(event)

    def focusInEvent(self, event):
        if not self.text():
            self.mostrar_historial()
        super().focusInEvent(event)


class VentasScreen(QWidget):
    def __init__(self, on_logout_callback):
        super().__init__()
        self.on_logout_callback = on_logout_callback
        self.usuario = None
        self.items_venta = []
        self.log_eliminados = []
        self.log_ventas = []
        self.log_modificaciones = []
        self.setup_ui()

    def set_usuario(self, usuario):
        self.usuario = usuario
        self.lbl_cajero.setText(f"👤 {usuario['nombre']}")

    def setup_ui(self):
        self.setStyleSheet("background-color: #1a1a2e; color: white;")
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        topbar = QFrame()
        topbar.setFixedHeight(56)
        topbar.setStyleSheet("background-color: #16213e; border-bottom: 2px solid #e94560;")
        top_layout = QHBoxLayout(topbar)
        top_layout.setContentsMargins(20, 0, 20, 0)
        titulo = QLabel("💰 JUANA CASH")
        titulo.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        titulo.setStyleSheet("color: #e94560;")
        top_layout.addWidget(titulo)
        top_layout.addStretch()
        self.lbl_cajero = QLabel("👤 ")
        self.lbl_cajero.setStyleSheet("color: #a0a0b0; font-size: 13px;")
        top_layout.addWidget(self.lbl_cajero)
        btn_logout = QPushButton("Salir")
        btn_logout.setFixedWidth(80)
        btn_logout.setStyleSheet("QPushButton { background: #e94560; color: white; border-radius: 6px; padding: 6px; }")
        btn_logout.clicked.connect(self.on_logout_callback)
        top_layout.addWidget(btn_logout)
        layout.addWidget(topbar)

        contenido = QHBoxLayout()
        contenido.setContentsMargins(12, 12, 12, 12)
        contenido.setSpacing(10)

        panel_izq = QVBoxLayout()
        panel_izq.setSpacing(8)

        # Buscador con sugerencias e historial
        busqueda_layout = QHBoxLayout()
        self.input_buscar = BuscadorConSugerencias(self.agregar_item)
        self.input_buscar.setPlaceholderText("🔍 Código de barras, nombre o depto (900-909) — F3 para enfocar...")
        self.input_buscar.setFixedHeight(46)
        self.input_buscar.setStyleSheet("QLineEdit { background: #0f3460; border: 2px solid #e94560; border-radius: 8px; padding: 0 16px; color: white; font-size: 14px; }")
        self.input_buscar.returnPressed.connect(self.buscar_producto)
        busqueda_layout.addWidget(self.input_buscar)
        btn_buscar = QPushButton("Agregar")
        btn_buscar.setFixedSize(90, 46)
        btn_buscar.setStyleSheet("QPushButton { background: #e94560; color: white; border-radius: 8px; font-size: 13px; font-weight: bold; }")
        btn_buscar.clicked.connect(self.buscar_producto)
        busqueda_layout.addWidget(btn_buscar)
        panel_izq.addLayout(busqueda_layout)

        # Manual
        manual_frame = QFrame()
        manual_frame.setStyleSheet("QFrame { background: #16213e; border-radius: 8px; border: 1px solid #27ae60; }")
        manual_layout = QHBoxLayout(manual_frame)
        manual_layout.setContentsMargins(10, 5, 10, 5)
        manual_layout.setSpacing(6)
        lbl_m = QLabel("💲 Manual:")
        lbl_m.setStyleSheet("color: #27ae60; font-size: 12px; font-weight: bold;")
        lbl_m.setFixedWidth(70)
        manual_layout.addWidget(lbl_m)
        self.input_manual_nombre = QLineEdit()
        self.input_manual_nombre.setPlaceholderText("Nombre del artículo")
        self.input_manual_nombre.setFixedHeight(34)
        self.input_manual_nombre.setStyleSheet("QLineEdit { background: #0f3460; border: 1px solid #27ae60; border-radius: 6px; padding: 0 8px; color: white; font-size: 13px; }")
        manual_layout.addWidget(self.input_manual_nombre, 3)
        self.input_manual_precio = QLineEdit()
        self.input_manual_precio.setPlaceholderText("Precio $")
        self.input_manual_precio.setFixedSize(90, 34)
        self.input_manual_precio.setStyleSheet("QLineEdit { background: #0f3460; border: 1px solid #27ae60; border-radius: 6px; padding: 0 8px; color: white; font-size: 13px; }")
        manual_layout.addWidget(self.input_manual_precio)
        self.input_manual_cant = QLineEdit()
        self.input_manual_cant.setText("1")
        self.input_manual_cant.setFixedSize(50, 34)
        self.input_manual_cant.setStyleSheet("QLineEdit { background: #0f3460; border: 1px solid #27ae60; border-radius: 6px; padding: 0 8px; color: white; font-size: 13px; }")
        manual_layout.addWidget(self.input_manual_cant)
        btn_manual = QPushButton("+ Agregar")
        btn_manual.setFixedSize(85, 34)
        btn_manual.setStyleSheet("QPushButton { background: #27ae60; color: white; border-radius: 6px; font-size: 12px; font-weight: bold; }")
        btn_manual.clicked.connect(self.agregar_manual)
        self.input_manual_precio.returnPressed.connect(self.agregar_manual)
        manual_layout.addWidget(btn_manual)
        panel_izq.addWidget(manual_frame)

        # Hint con atajos
        lbl_hint = QLabel("⌨️  F1 Cobrar  |  F2 Cancelar  |  F3 Buscar  |  Doble clic para editar precio  |  🕐 Clic en buscador para ver historial")
        lbl_hint.setStyleSheet("color: #27ae60; font-size: 11px; padding: 2px 4px; font-weight: bold;")
        panel_izq.addWidget(lbl_hint)

        # Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels(["Producto", "Precio", "Cantidad", "Subtotal", "Ajustar", ""])
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabla.setColumnWidth(4, 90)
        self.tabla.setColumnWidth(5, 34)
        self.tabla.setStyleSheet("""
            QTableWidget { background: #16213e; border: 1px solid #0f3460; border-radius: 8px; gridline-color: #0f3460; }
            QHeaderView::section { background: #0f3460; color: #a0a0b0; padding: 8px; border: none; }
            QTableWidgetItem { color: white; padding: 6px; }
        """)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.cellDoubleClicked.connect(self.editar_item_doble_clic)
        panel_izq.addWidget(self.tabla)
        contenido.addLayout(panel_izq, 3)

        # Panel derecho
        panel_der = QVBoxLayout()
        panel_der.setSpacing(8)

        total_frame = QFrame()
        total_frame.setFixedWidth(260)
        total_frame.setStyleSheet("QFrame { background: #16213e; border-radius: 12px; }")
        total_layout = QVBoxLayout(total_frame)
        total_layout.setContentsMargins(16, 16, 16, 16)
        total_layout.setSpacing(8)
        lbl_resumen = QLabel("RESUMEN")
        lbl_resumen.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        lbl_resumen.setStyleSheet("color: #a0a0b0;")
        total_layout.addWidget(lbl_resumen)
        total_layout.addWidget(QLabel("TOTAL"))
        self.lbl_total = QLabel("$0.00")
        self.lbl_total.setFont(QFont("Arial", 30, QFont.Weight.Bold))
        self.lbl_total.setStyleSheet("color: #e94560;")
        total_layout.addWidget(self.lbl_total)
        btn_cobrar = QPushButton("💳 COBRAR  [F1]")
        btn_cobrar.setFixedHeight(50)
        btn_cobrar.setStyleSheet("QPushButton { background: #e94560; color: white; border-radius: 10px; font-size: 15px; font-weight: bold; } QPushButton:hover { background: #c73652; }")
        btn_cobrar.clicked.connect(self.cobrar)
        total_layout.addWidget(btn_cobrar)
        btn_cancelar = QPushButton("🗑 Cancelar venta  [F2]")
        btn_cancelar.setFixedHeight(36)
        btn_cancelar.setStyleSheet("QPushButton { background: transparent; color: #a0a0b0; border: 1px solid #a0a0b0; border-radius: 8px; font-size: 12px; }")
        btn_cancelar.clicked.connect(self.cancelar_venta)
        total_layout.addWidget(btn_cancelar)
        btn_informe = QPushButton("📋 Ver informe")
        btn_informe.setFixedHeight(36)
        btn_informe.setStyleSheet("QPushButton { background: #0f3460; color: white; border-radius: 8px; font-size: 12px; }")
        btn_informe.clicked.connect(self.ver_informe)
        total_layout.addWidget(btn_informe)
        panel_der.addWidget(total_frame)

        depto_label = QLabel("📊 Subtotales por depto.")
        depto_label.setStyleSheet("color: #a0a0b0; font-size: 12px; font-weight: bold;")
        panel_der.addWidget(depto_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(260)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.depto_container = QWidget()
        self.depto_container.setStyleSheet("background: transparent;")
        self.depto_layout = QVBoxLayout(self.depto_container)
        self.depto_layout.setContentsMargins(0, 0, 0, 0)
        self.depto_layout.setSpacing(4)
        scroll.setWidget(self.depto_container)
        panel_der.addWidget(scroll)
        panel_der.addStretch()
        contenido.addLayout(panel_der)
        layout.addLayout(contenido)

        # ⌨️ Atajos de teclado
        QShortcut(QKeySequence("F1"), self).activated.connect(self.cobrar)
        QShortcut(QKeySequence("F2"), self).activated.connect(self.cancelar_venta)
        QShortcut(QKeySequence("F3"), self).activated.connect(lambda: self.input_buscar.setFocus())

    def actualizar_subtotales_depto(self):
        while self.depto_layout.count():
            child = self.depto_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        subtotales = {}
        for item in self.items_venta:
            nombre = item["nombre"]
            depto_key = "🛍️ Productos"
            depto_color = "#e94560"
            for codigo, depto in DEPARTAMENTOS.items():
                if nombre.startswith(depto["icono"]):
                    depto_key = f"{depto['icono']} {depto['nombre']}"
                    depto_color = depto["color"]
                    break
            if depto_key not in subtotales:
                subtotales[depto_key] = {"total": 0, "color": depto_color}
            subtotales[depto_key]["total"] += item["subtotal"]
        if not subtotales:
            lbl = QLabel("Sin items")
            lbl.setStyleSheet("color: #555; font-size: 12px; padding: 8px;")
            self.depto_layout.addWidget(lbl)
            return
        for depto_nombre, data in subtotales.items():
            card = QFrame()
            card.setStyleSheet(f"QFrame {{ background: #16213e; border-radius: 8px; border-left: 3px solid {data['color']}; }}")
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(10, 8, 10, 8)
            lbl_n = QLabel(depto_nombre)
            lbl_n.setStyleSheet(f"color: {data['color']}; font-size: 12px; font-weight: bold;")
            card_layout.addWidget(lbl_n)
            card_layout.addStretch()
            lbl_t = QLabel(f"${data['total']:.2f}")
            lbl_t.setFont(QFont("Arial", 13, QFont.Weight.Bold))
            lbl_t.setStyleSheet(f"color: {data['color']};")
            card_layout.addWidget(lbl_t)
            self.depto_layout.addWidget(card)

    def buscar_producto(self):
        texto = self.input_buscar.text().strip()
        if not texto:
            return
        if texto in DEPARTAMENTOS:
            depto = DEPARTAMENTOS[texto]
            self.input_buscar.clear()
            self.abrir_ingreso_departamento(depto)
            return
        try:
            r = requests.get(f"{API_URL}/productos/buscar", params={"q": texto}, timeout=5)
            if r.status_code == 200:
                productos = r.json()
                if not productos:
                    QMessageBox.warning(self, "No encontrado", f"No se encontró: {texto}")
                    return
                self.input_buscar.agregar_historial(productos[0])
                self.agregar_item(productos[0])
                self.input_buscar.clear()
        except Exception:
            QMessageBox.critical(self, "Error", "No se puede conectar al servidor")

    def abrir_ingreso_departamento(self, depto):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{depto['icono']} {depto['nombre']}")
        dialog.setMinimumWidth(340)
        dialog.setStyleSheet("background-color: #1a1a2e; color: white;")
        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)
        header = QFrame()
        header.setStyleSheet(f"QFrame {{ background: {depto['color']}; border-radius: 10px; }}")
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(16, 12, 16, 12)
        lbl_h = QLabel(f"{depto['icono']} {depto['nombre']}")
        lbl_h.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        lbl_h.setStyleSheet("color: white;")
        lbl_h.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h_layout.addWidget(lbl_h)
        layout.addWidget(header)
        montos_temp = []
        lista_frame = QFrame()
        lista_frame.setStyleSheet(f"QFrame {{ background: #16213e; border-radius: 8px; border: 1px solid {depto['color']}; }}")
        lista_layout = QVBoxLayout(lista_frame)
        lista_layout.setContentsMargins(10, 8, 10, 8)
        lista_layout.setSpacing(4)
        lbl_montos = QLabel("— Sin items aún —")
        lbl_montos.setStyleSheet("color: #555; font-size: 12px;")
        lbl_montos.setWordWrap(True)
        lista_layout.addWidget(lbl_montos)
        lbl_total_depto = QLabel("Total: $0.00")
        lbl_total_depto.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        lbl_total_depto.setStyleSheet(f"color: {depto['color']};")
        lbl_total_depto.setAlignment(Qt.AlignmentFlag.AlignRight)
        lista_layout.addWidget(lbl_total_depto)
        layout.addWidget(lista_frame)

        def actualizar_lista():
            if not montos_temp:
                lbl_montos.setText("— Sin items aún —")
                lbl_montos.setStyleSheet("color: #555; font-size: 12px;")
                lbl_total_depto.setText("Total: $0.00")
                return
            texto = "  +  ".join([f"${m:.2f}" for m in montos_temp])
            lbl_montos.setText(texto)
            lbl_montos.setStyleSheet("color: white; font-size: 13px;")
            lbl_total_depto.setText(f"Total: ${sum(montos_temp):.2f}")

        def agregar_monto():
            texto_input = input_monto.text().strip()
            if not texto_input:
                return
            try:
                monto = float(texto_input.replace(",", "."))
            except ValueError:
                QMessageBox.warning(dialog, "Error", "Ingresá un monto válido")
                return
            if monto <= 0:
                return
            montos_temp.append(monto)
            input_monto.clear()
            input_monto.setFocus()
            actualizar_lista()

        def borrar_ultimo():
            if montos_temp:
                montos_temp.pop()
                actualizar_lista()

        input_monto = MontoDeptoInput(agregar_monto)
        input_monto.setPlaceholderText("Ingresá el monto y presioná Enter...")
        input_monto.setFixedHeight(44)
        input_monto.setAlignment(Qt.AlignmentFlag.AlignRight)
        input_monto.setStyleSheet(f"QLineEdit {{ background: #1a1a2e; border: 2px solid {depto['color']}; border-radius: 8px; padding: 0 16px; color: white; font-size: 20px; font-weight: bold; }}")
        input_frame = QFrame()
        input_frame.setStyleSheet("QFrame { background: #0f3460; border-radius: 8px; }")
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(8, 6, 8, 6)
        input_layout.setSpacing(8)
        input_layout.addWidget(input_monto)
        btn_add = QPushButton("+ Sumar")
        btn_add.setFixedSize(80, 44)
        btn_add.setStyleSheet(f"QPushButton {{ background: {depto['color']}; color: white; border-radius: 8px; font-size: 13px; font-weight: bold; }}")
        btn_add.clicked.connect(agregar_monto)
        input_layout.addWidget(btn_add)
        layout.addWidget(input_frame)
        btn_borrar = QPushButton("← Borrar último")
        btn_borrar.setFixedHeight(34)
        btn_borrar.setStyleSheet("QPushButton { background: transparent; color: #e94560; border: 1px solid #e94560; border-radius: 6px; font-size: 12px; }")
        btn_borrar.clicked.connect(borrar_ultimo)
        layout.addWidget(btn_borrar)
        btns = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setFixedHeight(44)
        btn_cancelar.setStyleSheet("QPushButton { background: transparent; color: #a0a0b0; border: 1px solid #a0a0b0; border-radius: 8px; }")
        btn_cancelar.clicked.connect(dialog.reject)
        btns.addWidget(btn_cancelar)
        btn_confirmar = QPushButton("✅ Agregar al ticket")
        btn_confirmar.setFixedHeight(44)
        btn_confirmar.setStyleSheet(f"QPushButton {{ background: {depto['color']}; color: white; border-radius: 8px; font-size: 14px; font-weight: bold; }}")
        btns.addWidget(btn_confirmar)
        layout.addLayout(btns)

        def confirmar():
            if not montos_temp:
                QMessageBox.warning(dialog, "Error", "Ingresá al menos un monto")
                return
            total = sum(montos_temp)
            self.items_venta.append({
                "producto_id": 0,
                "nombre": f"{depto['icono']} {depto['nombre']}",
                "precio_unitario": total,
                "cantidad": 1,
                "subtotal": total,
                "descuento": 0
            })
            self.actualizar_tabla()
            dialog.accept()

        btn_confirmar.clicked.connect(confirmar)
        input_monto.setFocus()
        dialog.exec()

    def agregar_manual(self):
        nombre = self.input_manual_nombre.text().strip()
        try:
            precio = float(self.input_manual_precio.text())
            cantidad = float(self.input_manual_cant.text() or 1)
        except ValueError:
            QMessageBox.warning(self, "Error", "Precio y cantidad deben ser números")
            return
        if not nombre or precio <= 0:
            return
        self.items_venta.append({
            "producto_id": 0,
            "nombre": f"[M] {nombre}",
            "precio_unitario": precio,
            "cantidad": cantidad,
            "subtotal": precio * cantidad,
            "descuento": 0
        })
        self.actualizar_tabla()
        self.input_manual_nombre.clear()
        self.input_manual_precio.clear()
        self.input_manual_cant.setText("1")
        self.input_manual_nombre.setFocus()

    def agregar_item(self, producto):
        for item in self.items_venta:
            if item["producto_id"] == producto["id"]:
                item["cantidad"] += 1
                item["subtotal"] = item["cantidad"] * item["precio_unitario"]
                self.actualizar_tabla()
                return
        self.items_venta.append({
            "producto_id": producto["id"],
            "nombre": producto["nombre"],
            "precio_unitario": float(producto["precio_venta"]),
            "cantidad": 1,
            "subtotal": float(producto["precio_venta"]),
            "descuento": 0
        })
        self.actualizar_tabla()

    def editar_item_doble_clic(self, row, col):
        if row >= len(self.items_venta):
            return
        item = self.items_venta[row]
        precio_original = item["precio_unitario"]
        dialog = EditarItemDialog(self, item)
        if dialog.exec():
            if dialog.nuevo_precio != precio_original:
                self.log_modificaciones.append({
                    "producto": item["nombre"],
                    "precio_original": precio_original,
                    "precio_nuevo": dialog.nuevo_precio,
                    "hora": datetime.now().strftime("%H:%M:%S"),
                    "ticket": "-"
                })
            item["precio_unitario"] = dialog.nuevo_precio
            item["cantidad"] = dialog.nueva_cantidad
            item["subtotal"] = dialog.nuevo_precio * dialog.nueva_cantidad
            self.actualizar_tabla()

    def cambiar_cantidad(self, idx, delta):
        if idx >= len(self.items_venta):
            return
        item = self.items_venta[idx]
        nueva_cantidad = item["cantidad"] + delta
        if nueva_cantidad <= 0:
            self.log_eliminados.append({
                "producto": item["nombre"],
                "cantidad": item["cantidad"],
                "precio": item["precio_unitario"],
                "hora": datetime.now().strftime("%H:%M:%S"),
                "motivo": "Cantidad reducida a 0",
                "venta_cerrada": False,
                "ticket": "-"
            })
            self.items_venta.pop(idx)
        else:
            item["cantidad"] = nueva_cantidad
            item["subtotal"] = nueva_cantidad * item["precio_unitario"]
        self.actualizar_tabla()

    def actualizar_tabla(self):
        self.tabla.setRowCount(len(self.items_venta))
        total = 0
        for i, item in enumerate(self.items_venta):
            nombre_item = QTableWidgetItem(item["nombre"])
            if item["producto_id"] == 0:
                nombre_item.setForeground(Qt.GlobalColor.green)
            self.tabla.setItem(i, 0, nombre_item)
            self.tabla.setItem(i, 1, QTableWidgetItem(f"${item['precio_unitario']:.2f}"))
            self.tabla.setItem(i, 2, QTableWidgetItem(str(item["cantidad"])))
            self.tabla.setItem(i, 3, QTableWidgetItem(f"${item['subtotal']:.2f}"))
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(2, 1, 2, 1)
            btn_layout.setSpacing(3)
            btn_menos = QPushButton("−")
            btn_menos.setFixedSize(26, 24)
            btn_menos.setStyleSheet("QPushButton { background: #0f3460; color: white; border-radius: 4px; font-size: 14px; font-weight: bold; } QPushButton:hover { background: #e94560; }")
            btn_menos.clicked.connect(lambda _, idx=i: self.cambiar_cantidad(idx, -1))
            btn_layout.addWidget(btn_menos)
            btn_mas = QPushButton("+")
            btn_mas.setFixedSize(26, 24)
            btn_mas.setStyleSheet("QPushButton { background: #0f3460; color: white; border-radius: 4px; font-size: 14px; font-weight: bold; } QPushButton:hover { background: #27ae60; }")
            btn_mas.clicked.connect(lambda _, idx=i: self.cambiar_cantidad(idx, 1))
            btn_layout.addWidget(btn_mas)
            self.tabla.setCellWidget(i, 4, btn_widget)
            btn_del = QPushButton("✕")
            btn_del.setFixedSize(26, 24)
            btn_del.setStyleSheet("QPushButton { color: #e94560; background: transparent; font-size: 13px; }")
            btn_del.clicked.connect(lambda _, idx=i: self.eliminar_item(idx))
            self.tabla.setCellWidget(i, 5, btn_del)
            total += item["subtotal"]
        self.lbl_total.setText(f"${total:.2f}")
        self.actualizar_subtotales_depto()

    def eliminar_item(self, idx):
        if idx >= len(self.items_venta):
            return
        item = self.items_venta[idx]
        self.log_eliminados.append({
            "producto": item["nombre"],
            "cantidad": item["cantidad"],
            "precio": item["precio_unitario"],
            "hora": datetime.now().strftime("%H:%M:%S"),
            "motivo": "Eliminado manualmente",
            "venta_cerrada": False,
            "ticket": "-"
        })
        self.items_venta.pop(idx)
        self.actualizar_tabla()

    def guardar_informe(self, ticket, descuento_pct, total_original, total_final, metodo_pago, vuelto=0):
        try:
            carpeta = os.path.join(os.path.expanduser("~"), "JuanaCash_Tickets")
            os.makedirs(carpeta, exist_ok=True)
            fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
            ruta = os.path.join(carpeta, f"informe_{fecha}.txt")
            nombres_metodo = {
                "efectivo": "Efectivo",
                "tarjeta": "Tarjeta",
                "mercadopago_qr": "QR / Mercado Pago",
                "transferencia": "Transferencia"
            }
            with open(ruta, "w", encoding="utf-8") as f:
                f.write("=" * 40 + "\n")
                f.write("JUANA CASH — INFORME DE VENTA\n")
                f.write("=" * 40 + "\n")
                f.write(f"Ticket: {ticket}\n")
                f.write(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write(f"Cajero: {self.usuario['nombre'] if self.usuario else 'N/A'}\n")
                f.write(f"Pago: {nombres_metodo.get(metodo_pago, metodo_pago)}\n")
                f.write("-" * 40 + "\n")
                if descuento_pct > 0:
                    f.write(f"DESCUENTO: {descuento_pct:.1f}%\n")
                    f.write(f"Total original: ${total_original:.2f}\n")
                    f.write(f"Ahorro: ${total_original - total_final:.2f}\n")
                    f.write(f"Total final: ${total_final:.2f}\n")
                else:
                    f.write(f"Total: ${total_final:.2f}\n")
                if metodo_pago == "efectivo" and vuelto > 0:
                    f.write(f"Vuelto entregado: ${vuelto:.2f}\n")
                if self.log_modificaciones:
                    f.write("-" * 40 + "\n")
                    f.write("PRECIOS MODIFICADOS:\n")
                    for m in self.log_modificaciones:
                        f.write(f"  {m['hora']} — {m['producto']}: ${m['precio_original']:.2f} → ${m['precio_nuevo']:.2f}\n")
                if self.log_eliminados:
                    f.write("-" * 40 + "\n")
                    f.write("PRODUCTOS ELIMINADOS:\n")
                    for log in self.log_eliminados:
                        f.write(f"  {log['hora']} — {log['producto']} x{log['cantidad']} — {log['motivo']}\n")
                f.write("=" * 40 + "\n")
        except Exception as e:
            print(f"Error: {e}")

    def ver_informe(self):
        if not self.log_eliminados and not self.log_ventas and not self.log_modificaciones:
            QMessageBox.information(self, "📋 Informe", "No hay eventos registrados.")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("📋 Informe de sesión")
        dialog.setMinimumSize(720, 520)
        dialog.setStyleSheet("background-color: #1a1a2e; color: white;")
        layout = QVBoxLayout(dialog)
        estilo = """
            QTableWidget { background: #16213e; border: 1px solid #0f3460; border-radius: 8px; gridline-color: #0f3460; }
            QHeaderView::section { background: #0f3460; color: #a0a0b0; padding: 6px; border: none; }
            QTableWidgetItem { color: white; padding: 6px; }
        """
        if self.log_modificaciones:
            lbl = QLabel("✏️ Precios modificados")
            lbl.setStyleSheet("color: #f39c12; font-size: 13px; font-weight: bold; padding: 4px 0;")
            layout.addWidget(lbl)
            t = QTableWidget()
            t.setColumnCount(4)
            t.setHorizontalHeaderLabels(["Producto", "Precio original", "Precio nuevo", "Hora"])
            t.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            t.setStyleSheet(estilo)
            t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            t.setRowCount(len(self.log_modificaciones))
            for i, m in enumerate(self.log_modificaciones):
                t.setItem(i, 0, QTableWidgetItem(m["producto"]))
                t.setItem(i, 1, QTableWidgetItem(f"${m['precio_original']:.2f}"))
                nuevo = QTableWidgetItem(f"${m['precio_nuevo']:.2f}")
                nuevo.setForeground(Qt.GlobalColor.yellow)
                t.setItem(i, 2, nuevo)
                t.setItem(i, 3, QTableWidgetItem(m["hora"]))
            layout.addWidget(t)

        if self.log_eliminados:
            lbl2 = QLabel("🗑 Productos eliminados")
            lbl2.setStyleSheet("color: #e94560; font-size: 13px; font-weight: bold; padding: 4px 0;")
            layout.addWidget(lbl2)
            t2 = QTableWidget()
            t2.setColumnCount(5)
            t2.setHorizontalHeaderLabels(["Producto", "Cant.", "Precio", "Hora", "Estado"])
            t2.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            t2.setStyleSheet(estilo)
            t2.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            t2.setRowCount(len(self.log_eliminados))
            for i, log in enumerate(self.log_eliminados):
                t2.setItem(i, 0, QTableWidgetItem(log["producto"]))
                t2.setItem(i, 1, QTableWidgetItem(str(log["cantidad"])))
                t2.setItem(i, 2, QTableWidgetItem(f"${log['precio']:.2f}"))
                t2.setItem(i, 3, QTableWidgetItem(log["hora"]))
                estado = f"✅ {log['ticket']}" if log["venta_cerrada"] else "⏳ Pendiente"
                item_e = QTableWidgetItem(estado)
                item_e.setForeground(Qt.GlobalColor.green if log["venta_cerrada"] else Qt.GlobalColor.yellow)
                t2.setItem(i, 4, item_e)
            layout.addWidget(t2)

        if self.log_ventas:
            lbl3 = QLabel("💰 Ventas cerradas")
            lbl3.setStyleSheet("color: #27ae60; font-size: 13px; font-weight: bold; padding: 4px 0;")
            layout.addWidget(lbl3)
            t3 = QTableWidget()
            t3.setColumnCount(6)
            t3.setHorizontalHeaderLabels(["Ticket", "Original", "Desc %", "Total", "Pago", "Vuelto"])
            t3.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            t3.setStyleSheet(estilo)
            t3.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            t3.setRowCount(len(self.log_ventas))
            for i, d in enumerate(self.log_ventas):
                t3.setItem(i, 0, QTableWidgetItem(d["ticket"]))
                t3.setItem(i, 1, QTableWidgetItem(f"${d['total_original']:.2f}"))
                t3.setItem(i, 2, QTableWidgetItem(f"{d['descuento_pct']:.1f}%"))
                t3.setItem(i, 3, QTableWidgetItem(f"${d['total_final']:.2f}"))
                t3.setItem(i, 4, QTableWidgetItem(d.get("metodo_pago", "-")))
                vuelto = d.get("vuelto", 0)
                t3.setItem(i, 5, QTableWidgetItem(f"${vuelto:.2f}" if vuelto > 0 else "-"))
            layout.addWidget(t3)
        dialog.exec()

    def cobrar(self):
        if not self.items_venta:
            QMessageBox.warning(self, "Sin productos", "Agregá productos antes de cobrar")
            return
        total_original = sum(i["subtotal"] for i in self.items_venta)
        dialog = CobrarDialog(self, total_original)
        if not dialog.exec():
            return
        descuento_pct = dialog.descuento_pct
        total_final = dialog.total_final
        metodo_pago = dialog.metodo_pago
        descuento_monto = total_original - total_final
        vuelto = 0
        if metodo_pago == "efectivo":
            try:
                entrega = float(dialog.input_entrega.text().replace(",", "."))
                vuelto = max(0, entrega - total_final)
            except ValueError:
                pass
        items_backend = [i for i in self.items_venta if i["producto_id"] != 0]
        if not items_backend:
            items_backend = [{"producto_id": 1, "cantidad": 1, "precio_unitario": total_final, "descuento": 0}]
        try:
            r = requests.post(f"{API_URL}/ventas/", json={
                "usuario_id": self.usuario.get("id", 1) if self.usuario else 1,
                "items": items_backend,
                "pagos": [{"metodo": metodo_pago, "monto": total_final}],
                "descuento": descuento_monto
            }, timeout=5)
            if r.status_code == 200:
                datos = r.json()
                ticket = datos["numero"]
                nombres_metodo = {
                    "efectivo": "💵 Efectivo",
                    "tarjeta": "💳 Tarjeta",
                    "mercadopago_qr": "📱 QR / MP",
                    "transferencia": "🏦 Transferencia"
                }
                self.log_ventas.append({
                    "ticket": ticket,
                    "total_original": total_original,
                    "descuento_pct": descuento_pct,
                    "ahorro": descuento_monto,
                    "total_final": total_final,
                    "metodo_pago": nombres_metodo.get(metodo_pago, metodo_pago),
                    "vuelto": vuelto,
                    "hora": datetime.now().strftime("%H:%M:%S")
                })
                for log in self.log_eliminados:
                    if not log["venta_cerrada"]:
                        log["venta_cerrada"] = True
                        log["ticket"] = ticket
                for m in self.log_modificaciones:
                    if m["ticket"] == "-":
                        m["ticket"] = ticket
                self.guardar_informe(ticket, descuento_pct, total_original, total_final, metodo_pago, vuelto)
                msg = f"Ticket: {ticket}\nTotal: ${total_final:.2f}\nPago: {nombres_metodo.get(metodo_pago, metodo_pago)}"
                if descuento_pct > 0:
                    msg += f"\nDescuento: {descuento_pct:.1f}% (-${descuento_monto:.2f})"
                if metodo_pago == "efectivo" and vuelto > 0:
                    msg += f"\n💵 Vuelto: ${vuelto:.2f}"
                try:
                    from ui.pantallas.impresora import imprimir_ticket
                    exito, txt = imprimir_ticket(
                        {"numero": ticket, "total": total_final},
                        self.items_venta
                    )
                    QMessageBox.information(self, "✅ Venta registrada", msg + f"\n\n🖨️ {txt}")
                except Exception:
                    QMessageBox.information(self, "✅ Venta registrada", msg)
                self.cancelar_venta()
            else:
                QMessageBox.critical(self, "Error", "No se pudo registrar la venta")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se puede conectar al servidor\n{str(e)}")

    def cancelar_venta(self):
        self.items_venta = []
        self.actualizar_tabla()