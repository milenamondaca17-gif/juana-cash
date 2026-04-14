import requests
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QLineEdit, QPushButton, QTableWidget,
                              QTableWidgetItem, QMessageBox, QFrame, QHeaderView,
                              QDialog, QDoubleSpinBox, QScrollArea,
                              QListWidget, QListWidgetItem, QGridLayout)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QShortcut, QKeySequence
from datetime import datetime
import os
try:
    from ui.pantallas.ticket_utils import ticket_para_whatsapp, abrir_whatsapp, formatear_ticket_texto, cargar_config_negocio
    cargar_config_negocio()
except Exception:
    ticket_para_whatsapp = None
    abrir_whatsapp = None

API_URL = "http://127.0.0.1:8000"

DEPARTAMENTOS = {
    "900": {"nombre": "Carnicer\u00eda",  "icono": "\ud83e\udd69", "color": "#e74c3c"},
    "901": {"nombre": "Verduler\u00eda",  "icono": "\ud83e\udd6c", "color": "#27ae60"},
    "902": {"nombre": "Panader\u00eda",   "icono": "\ud83c\udf5e", "color": "#e67e22"},
    "903": {"nombre": "Fiambrer\u00eda",  "icono": "\ud83e\uddc0", "color": "#f39c12"},
    "904": {"nombre": "L\u00e1cteos",     "icono": "\ud83e\udd5b", "color": "#3498db"},
    "905": {"nombre": "Limpieza",    "icono": "\ud83e\uddf9", "color": "#9b59b6"},
    "906": {"nombre": "Bebidas",     "icono": "\ud83c\udf7a", "color": "#1abc9c"},
    "907": {"nombre": "Cigarrer\u00eda",  "icono": "\ud83d\udeac", "color": "#7f8c8d"},
    "908": {"nombre": "Confiter\u00eda",  "icono": "\ud83c\udf6c", "color": "#e91e8c"},
    "909": {"nombre": "Varios",      "icono": "\ud83d\udce6", "color": "#95a5a6"},
}


class CobrarDialog(QDialog):
    def __init__(self, parent=None, total=0, cliente=None):
        super().__init__(parent)
        self.setWindowTitle("Cobrar venta")
        self.setMinimumWidth(460)
        self.setStyleSheet("background-color: #1a1a2e; color: white;")
        self.total_original = total
        self.descuento_pct = 0
        self.total_final = total
        self.metodo_pago = "efectivo"
        self.metodo_secundario = None
        self.monto_secundario = 0
        self.btns_pago = {}
        self.cliente = cliente
        self.descuento_puntos = 0
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        lbl_total = QLabel(f"Total: ${self.total_original:.2f}")
        lbl_total.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        lbl_total.setStyleSheet("color: #e94560;")
        lbl_total.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_total)

        if self.cliente and float(self.cliente.get("puntos", 0)) >= 100:
            puntos = float(self.cliente.get("puntos", 0))
            bloques = int(puntos // 100)
            descuento_max = bloques * 1000
            puntos_frame = QFrame()
            puntos_frame.setStyleSheet("QFrame { background: #0f3460; border-radius: 8px; border: 1px solid #f39c12; }")
            puntos_layout = QHBoxLayout(puntos_frame)
            puntos_layout.setContentsMargins(12, 8, 12, 8)
            lbl_pts = QLabel(f"⭐ {puntos:.0f} pts → descuento posible: ${descuento_max:,.0f}")
            lbl_pts.setStyleSheet("color: #f39c12; font-size: 12px;")
            puntos_layout.addWidget(lbl_pts)
            self.btn_canjear_pts = QPushButton("Canjear")
            self.btn_canjear_pts.setFixedHeight(28)
            self.btn_canjear_pts.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self.btn_canjear_pts.setStyleSheet("QPushButton { background: #f39c12; color: white; border-radius: 6px; font-size: 11px; font-weight: bold; padding: 0 10px; }")
            self.btn_canjear_pts.clicked.connect(lambda: self.aplicar_descuento_puntos(descuento_max))
            puntos_layout.addWidget(self.btn_canjear_pts)
            layout.addWidget(puntos_frame)

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

        lbl_metodo = QLabel("Metodo de pago principal:")
        lbl_metodo.setStyleSheet("color: #a0a0b0; font-size: 13px; font-weight: bold;")
        layout.addWidget(lbl_metodo)

        metodos_layout = QHBoxLayout()
        metodos_layout.setSpacing(8)
        metodos = [
            ("Efectivo", "efectivo", "#27ae60"),
            ("Tarjeta", "tarjeta", "#3498db"),
            ("QR/MP", "mercadopago_qr", "#009ee3"),
            ("Transf.", "transferencia", "#9b59b6"),
        ]
        for nombre, key, color in metodos:
            btn = QPushButton(nombre)
            btn.setFixedSize(90, 44)
            btn.setStyleSheet(f"QPushButton {{ background: #16213e; color: #a0a0b0; border: 2px solid #333; border-radius: 10px; font-size: 12px; }} QPushButton:hover {{ border: 2px solid {color}; color: white; }}")
            btn.clicked.connect(lambda _, k=key, c=color: self.seleccionar_metodo(k, c))
            metodos_layout.addWidget(btn)
            self.btns_pago[key] = (btn, color)
        layout.addLayout(metodos_layout)

        # Cobro mixto
        mixto_frame = QFrame()
        mixto_frame.setStyleSheet("QFrame { background: #16213e; border-radius: 8px; border: 1px solid #3498db; }")
        mixto_layout = QVBoxLayout(mixto_frame)
        mixto_layout.setContentsMargins(12, 8, 12, 8)
        mixto_layout.setSpacing(6)
        lbl_mixto = QLabel("Cobro mixto (opcional):")
        lbl_mixto.setStyleSheet("color: #3498db; font-size: 12px; font-weight: bold;")
        mixto_layout.addWidget(lbl_mixto)
        mixto_row = QHBoxLayout()
        self.combo_secundario = QPushButton("+ Agregar segundo metodo")
        self.combo_secundario.setFixedHeight(32)
        self.combo_secundario.setStyleSheet("QPushButton { background: #0f3460; color: #3498db; border-radius: 6px; font-size: 12px; border: 1px solid #3498db; }")
        self.combo_secundario.clicked.connect(self.toggle_mixto)
        mixto_row.addWidget(self.combo_secundario)
        mixto_layout.addLayout(mixto_row)
        self.mixto_detalle = QFrame()
        self.mixto_detalle.hide()
        mixto_det_layout = QHBoxLayout(self.mixto_detalle)
        mixto_det_layout.setContentsMargins(0, 4, 0, 0)
        self.btns_secundario = {}
        for nombre, key, color in metodos:
            btn2 = QPushButton(nombre)
            btn2.setFixedSize(80, 32)
            btn2.setStyleSheet(f"QPushButton {{ background: #0f3460; color: #a0a0b0; border: 1px solid #333; border-radius: 6px; font-size: 11px; }} QPushButton:hover {{ border: 1px solid {color}; color: white; }}")
            btn2.clicked.connect(lambda _, k=key, c=color: self.seleccionar_secundario(k, c))
            mixto_det_layout.addWidget(btn2)
            self.btns_secundario[key] = (btn2, color)
        self.input_monto_secundario = QLineEdit()
        self.input_monto_secundario.setPlaceholderText("Monto $")
        self.input_monto_secundario.setFixedWidth(100)
        self.input_monto_secundario.setFixedHeight(32)
        self.input_monto_secundario.setStyleSheet("QLineEdit { background: #0f3460; border: 1px solid #3498db; border-radius: 6px; padding: 4px 8px; color: white; font-size: 13px; }")
        self.input_monto_secundario.textChanged.connect(self.actualizar_vuelto_mixto)
        mixto_det_layout.addWidget(self.input_monto_secundario)
        mixto_layout.addWidget(self.mixto_detalle)
        self.lbl_mixto_resumen = QLabel("")
        self.lbl_mixto_resumen.setStyleSheet("color: #3498db; font-size: 12px;")
        mixto_layout.addWidget(self.lbl_mixto_resumen)
        layout.addWidget(mixto_frame)

        self.vuelto_frame = QFrame()
        self.vuelto_frame.setStyleSheet("QFrame { background: #16213e; border-radius: 8px; border: 1px solid #27ae60; }")
        vuelto_layout = QVBoxLayout(self.vuelto_frame)
        vuelto_layout.setContentsMargins(12, 10, 12, 10)
        vuelto_layout.setSpacing(6)
        lbl_entrega = QLabel("El cliente entrega ($):")
        lbl_entrega.setStyleSheet("color: #a0a0b0; font-size: 13px;")
        vuelto_layout.addWidget(lbl_entrega)
        self.input_entrega = QLineEdit()
        self.input_entrega.setPlaceholderText("Ingresa el monto recibido...")
        self.input_entrega.setFixedHeight(48)
        self.input_entrega.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.input_entrega.setStyleSheet("QLineEdit { background: #0f3460; border: 2px solid #27ae60; border-radius: 8px; padding: 0 16px; color: white; font-size: 20px; font-weight: bold; }")
        self.input_entrega.textChanged.connect(self.calcular_vuelto)
        vuelto_layout.addWidget(self.input_entrega)
        self.lbl_vuelto = QLabel("Vuelto: -")
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
        self.btn_cobrar = QPushButton("COBRAR")
        self.btn_cobrar.setFixedHeight(44)
        self.btn_cobrar.setStyleSheet("QPushButton { background: #27ae60; color: white; border-radius: 8px; font-size: 15px; font-weight: bold; }")
        self.btn_cobrar.clicked.connect(self.accept)
        btns.addWidget(self.btn_cobrar)
        layout.addLayout(btns)

        self.seleccionar_metodo("efectivo", "#27ae60")

    def aplicar_descuento_puntos(self, descuento_monto):
        self.descuento_puntos = descuento_monto
        self.total_final = max(0, self.total_original - descuento_monto - (self.total_original * self.descuento_pct / 100))
        self.lbl_total_final.setText(f"A cobrar: ${self.total_final:.2f}  (−${descuento_monto:,.0f} puntos)")
        self.lbl_total_final.setStyleSheet("color: #f39c12; font-size: 18px; font-weight: bold;")
        if hasattr(self, "btn_canjear_pts"):
            self.btn_canjear_pts.setText("✅ Canjeado")
            self.btn_canjear_pts.setEnabled(False)
            self.btn_canjear_pts.setStyleSheet("QPushButton { background: #27ae60; color: white; border-radius: 6px; font-size: 11px; padding: 0 10px; }")

    def toggle_mixto(self):
        if self.mixto_detalle.isVisible():
            self.mixto_detalle.hide()
            self.metodo_secundario = None
            self.monto_secundario = 0
            self.lbl_mixto_resumen.setText("")
            self.combo_secundario.setText("+ Agregar segundo metodo")
        else:
            self.mixto_detalle.show()
            self.combo_secundario.setText("- Quitar cobro mixto")

    def seleccionar_secundario(self, key, color):
        if key == self.metodo_pago:
            QMessageBox.warning(self, "Error", "El segundo metodo no puede ser igual al principal")
            return
        self.metodo_secundario = key
        nombres = {"efectivo": "Efectivo", "tarjeta": "Tarjeta", "mercadopago_qr": "QR/MP", "transferencia": "Transf."}
        for k, (btn, c) in self.btns_secundario.items():
            btn.setStyleSheet(f"QPushButton {{ background: #0f3460; color: #a0a0b0; border: 1px solid #333; border-radius: 6px; font-size: 11px; }}")
        btn, c = self.btns_secundario[key]
        btn.setStyleSheet(f"QPushButton {{ background: {color}; color: white; border: 1px solid {color}; border-radius: 6px; font-size: 11px; font-weight: bold; }}")
        self.actualizar_vuelto_mixto()

    def actualizar_vuelto_mixto(self):
        if not self.metodo_secundario:
            return
        try:
            self.monto_secundario = float(self.input_monto_secundario.text().replace(",", "."))
            restante = self.total_final - self.monto_secundario
            nombres = {"efectivo": "Efectivo", "tarjeta": "Tarjeta", "mercadopago_qr": "QR/MP", "transferencia": "Transf."}
            if restante < 0:
                self.lbl_mixto_resumen.setText(f"Excede por ${abs(restante):.2f}")
                self.lbl_mixto_resumen.setStyleSheet("color: #e94560; font-size: 12px;")
            else:
                self.lbl_mixto_resumen.setText(f"Restante en {nombres.get(self.metodo_pago, '')}: ${restante:.2f}")
                self.lbl_mixto_resumen.setStyleSheet("color: #27ae60; font-size: 12px;")
        except ValueError:
            self.lbl_mixto_resumen.setText("")

    def calcular_vuelto(self):
        try:
            entrega = float(self.input_entrega.text().replace(",", "."))
            base = self.total_final - self.monto_secundario
            vuelto = entrega - base
            if vuelto < 0:
                self.lbl_vuelto.setText(f"Falta: ${abs(vuelto):.2f}")
                self.lbl_vuelto.setStyleSheet("color: #e94560; font-size: 20px; font-weight: bold;")
            else:
                self.lbl_vuelto.setText(f"Vuelto: ${vuelto:.2f}")
                self.lbl_vuelto.setStyleSheet("color: #27ae60; font-size: 22px; font-weight: bold;")
        except ValueError:
            self.lbl_vuelto.setText("Vuelto: -")
            self.lbl_vuelto.setStyleSheet("color: #27ae60; font-size: 20px; font-weight: bold;")

    def seleccionar_metodo(self, key, color):
        self.metodo_pago = key
        nombres = {"efectivo": "Efectivo", "tarjeta": "Tarjeta", "mercadopago_qr": "QR/MP", "transferencia": "Transf."}
        for k, (btn, c) in self.btns_pago.items():
            btn.setStyleSheet(f"QPushButton {{ background: #16213e; color: #a0a0b0; border: 2px solid #333; border-radius: 10px; font-size: 12px; }} QPushButton:hover {{ border: 2px solid {c}; color: white; }}")
        if key in self.btns_pago:
            btn, c = self.btns_pago[key]
            btn.setStyleSheet(f"QPushButton {{ background: {color}; color: white; border: 2px solid {color}; border-radius: 10px; font-size: 12px; font-weight: bold; }}")
        self.vuelto_frame.setVisible(key == "efectivo")
        self.btn_cobrar.setText(f"COBRAR - {nombres.get(key, key)}")
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
        self.setWindowTitle(f"Editar - {item['nombre']}")
        self.setMinimumWidth(340)
        self.setStyleSheet("background-color: #1a1a2e; color: white;")
        self.nuevo_precio = item["precio_unitario"]
        self.nueva_cantidad = item["cantidad"]
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        lbl_titulo = QLabel(f"{self.item['nombre']}")
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
        btn_guardar = QPushButton("Guardar")
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
            QMessageBox.warning(self, "Error", "Ingresa valores validos")
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



class VentasScreen(QWidget):
    def __init__(self, on_logout_callback):
        super().__init__()
        self.on_logout_callback = on_logout_callback
        self.usuario = None
        self.items_venta = []
        self.ultimo_producto = None
        self.log_eliminados = []
        self.log_ventas = []
        self.log_modificaciones = []
        self.favoritos = []
        self.cliente_actual = None
        self.setup_ui()
        self.cargar_favoritos()

    def set_usuario(self, usuario):
        self.usuario = usuario
        self.lbl_cajero.setText(f"{usuario['nombre']}")

    def cargar_favoritos(self):
        try:
            r = requests.get(f"{API_URL}/productos/", timeout=3)
            if r.status_code == 200:
                productos = r.json()
                self.favoritos = sorted(productos, key=lambda p: float(p.get("stock_actual", 0)), reverse=True)[:8]
                self.actualizar_botones_favoritos()
        except Exception:
            pass

    def actualizar_botones_favoritos(self):
        while self.grid_favoritos.count():
            child = self.grid_favoritos.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        for i, p in enumerate(self.favoritos):
            btn = QPushButton(f"{p['nombre']}\
${float(p['precio_venta']):.2f}")
            btn.setFixedSize(110, 56)
            btn.setStyleSheet("QPushButton { background: #0f3460; color: white; border-radius: 8px; font-size: 11px; border: 1px solid #e94560; } QPushButton:hover { background: #e94560; }")
            btn.clicked.connect(lambda _, prod=p: self.agregar_item(prod))
            row, col = divmod(i, 4)
            self.grid_favoritos.addWidget(btn, row, col)

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
        titulo = QLabel("JUANA CASH")
        titulo.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        titulo.setStyleSheet("color: #e94560;")
        top_layout.addWidget(titulo)
        top_layout.addStretch()
        self.lbl_cajero = QLabel("")
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

        # Buscador
        busqueda_layout = QHBoxLayout()
        self.input_buscar = QLineEdit()
        self.input_buscar.setPlaceholderText("Codigo de barras, nombre o depto (900-909) - F3 para enfocar...")
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
        lbl_m = QLabel("Manual:")
        lbl_m.setStyleSheet("color: #27ae60; font-size: 12px; font-weight: bold;")
        lbl_m.setFixedWidth(60)
        manual_layout.addWidget(lbl_m)
        self.input_manual_nombre = QLineEdit()
        self.input_manual_nombre.setPlaceholderText("Nombre del articulo")
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

        # Favoritos
        favoritos_frame = QFrame()
        favoritos_frame.setStyleSheet("QFrame { background: #16213e; border-radius: 8px; border: 1px solid #f39c12; }")
        favoritos_main = QVBoxLayout(favoritos_frame)
        favoritos_main.setContentsMargins(8, 6, 8, 6)
        favoritos_main.setSpacing(4)
        fav_header = QHBoxLayout()
        lbl_fav = QLabel("Favoritos rapidos:")
        lbl_fav.setStyleSheet("color: #f39c12; font-size: 12px; font-weight: bold;")
        fav_header.addWidget(lbl_fav)
        btn_reload_fav = QPushButton("Actualizar")
        btn_reload_fav.setFixedHeight(24)
        btn_reload_fav.setStyleSheet("QPushButton { background: #0f3460; color: #f39c12; border-radius: 4px; font-size: 11px; padding: 0 8px; }")
        btn_reload_fav.clicked.connect(self.cargar_favoritos)
        fav_header.addWidget(btn_reload_fav)
        fav_header.addStretch()
        favoritos_main.addLayout(fav_header)
        self.grid_favoritos = QGridLayout()
        self.grid_favoritos.setSpacing(4)
        favoritos_main.addLayout(self.grid_favoritos)
        panel_izq.addWidget(favoritos_frame)

        # Hints
        hints_layout = QHBoxLayout()
        lbl_hint = QLabel("F1 Cobrar  |  F2 Cancelar  |  F3 Buscar  |  F4 Repetir ultimo  |  Doble clic para editar")
        lbl_hint.setStyleSheet("color: #27ae60; font-size: 11px; padding: 2px 4px; font-weight: bold;")
        hints_layout.addWidget(lbl_hint)
        btn_precios = QPushButton("Verificar precio")
        btn_precios.setFixedHeight(28)
        btn_precios.setStyleSheet("QPushButton { background: #0f3460; color: #3498db; border-radius: 6px; font-size: 11px; padding: 0 10px; border: 1px solid #3498db; }")
        btn_precios.clicked.connect(self.verificar_precio)
        hints_layout.addWidget(btn_precios)
        panel_izq.addLayout(hints_layout)

        # Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels(["Producto", "Precio", "Cantidad", "Subtotal", "Ajustar", ""])
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabla.setColumnWidth(4, 90)
        self.tabla.setColumnWidth(5, 34)
        self.tabla.setStyleSheet("QTableWidget { background: #16213e; border: 1px solid #0f3460; border-radius: 8px; gridline-color: #0f3460; } QHeaderView::section { background: #0f3460; color: #a0a0b0; padding: 8px; border: none; } QTableWidgetItem { color: white; padding: 6px; }")
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
        btn_cobrar = QPushButton("COBRAR  [F1]")
        btn_cobrar.setFixedHeight(50)
        btn_cobrar.setStyleSheet("QPushButton { background: #e94560; color: white; border-radius: 10px; font-size: 15px; font-weight: bold; } QPushButton:hover { background: #c73652; }")
        btn_cobrar.clicked.connect(self.cobrar)
        total_layout.addWidget(btn_cobrar)
        btn_repetir = QPushButton("Repetir ultimo [F4]")
        btn_repetir.setFixedHeight(36)
        btn_repetir.setStyleSheet("QPushButton { background: #f39c12; color: white; border-radius: 8px; font-size: 12px; font-weight: bold; }")
        btn_repetir.clicked.connect(self.repetir_ultimo)
        total_layout.addWidget(btn_repetir)
        btn_cancelar = QPushButton("Cancelar venta  [F2]")
        btn_cancelar.setFixedHeight(36)
        btn_cancelar.setStyleSheet("QPushButton { background: transparent; color: #a0a0b0; border: 1px solid #a0a0b0; border-radius: 8px; font-size: 12px; }")
        btn_cancelar.clicked.connect(self.cancelar_venta)
        total_layout.addWidget(btn_cancelar)
        btn_informe = QPushButton("Ver informe")
        btn_informe.setFixedHeight(36)
        btn_informe.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_informe.setStyleSheet("QPushButton { background: #0f3460; color: white; border-radius: 8px; font-size: 12px; }")
        btn_informe.clicked.connect(self.ver_informe)
        total_layout.addWidget(btn_informe)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #0f3460;")
        total_layout.addWidget(sep)

        self.btn_cliente = QPushButton("👤 Vincular cliente")
        self.btn_cliente.setFixedHeight(34)
        self.btn_cliente.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_cliente.setStyleSheet("QPushButton { background: #0f3460; color: #3498db; border-radius: 8px; font-size: 12px; border: 1px solid #3498db; } QPushButton:hover { background: #3498db; color: white; }")
        self.btn_cliente.clicked.connect(self.buscar_cliente)
        total_layout.addWidget(self.btn_cliente)

        self.lbl_cliente_info = QLabel("")
        self.lbl_cliente_info.setStyleSheet("color: #f39c12; font-size: 11px; padding: 2px 0;")
        self.lbl_cliente_info.setWordWrap(True)
        self.lbl_cliente_info.hide()
        total_layout.addWidget(self.lbl_cliente_info)

        panel_der.addWidget(total_frame)

        depto_label = QLabel("Subtotales por depto.")
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

        QShortcut(QKeySequence("F1"), self).activated.connect(self.cobrar)
        QShortcut(QKeySequence("F2"), self).activated.connect(self.cancelar_venta)
        QShortcut(QKeySequence("F3"), self).activated.connect(lambda: self.input_buscar.setFocus())
        QShortcut(QKeySequence("F4"), self).activated.connect(self.repetir_ultimo)

    def buscar_cliente(self):
        from PyQt6.QtWidgets import QListWidget, QListWidgetItem
        dialog = QDialog(self)
        dialog.setWindowTitle("👤 Vincular cliente")
        dialog.setMinimumWidth(400)
        dialog.setStyleSheet("background-color: #1a1a2e; color: white;")
        lay = QVBoxLayout(dialog)
        lay.setSpacing(10)
        lbl = QLabel("Buscar cliente:")
        lbl.setStyleSheet("color: #a0a0b0; font-size: 13px;")
        lay.addWidget(lbl)
        input_b = QLineEdit()
        input_b.setPlaceholderText("Nombre o teléfono...")
        input_b.setFixedHeight(44)
        input_b.setStyleSheet("QLineEdit { background: #0f3460; border: 1px solid #3498db; border-radius: 8px; padding: 10px; color: white; font-size: 14px; }")
        lay.addWidget(input_b)
        lista = QListWidget()
        lista.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        lista.setStyleSheet("QListWidget { background: #16213e; border: 1px solid #0f3460; border-radius: 8px; color: white; } QListWidget::item { padding: 10px; } QListWidget::item:hover { background: #0f3460; }")
        lista.setMinimumHeight(200)
        lay.addWidget(lista)
        clientes_encontrados = []
        def buscar():
            texto = input_b.text().strip()
            if not texto:
                return
            try:
                r = requests.get(f"{API_URL}/clientes/buscar", params={"q": texto}, timeout=5)
                if r.status_code == 200:
                    lista.clear()
                    clientes_encontrados.clear()
                    for c in r.json()[:10]:
                        puntos = float(c.get("puntos", 0))
                        deuda = float(c.get("deuda_actual", 0))
                        texto_item = c["nombre"]
                        if puntos > 0:
                            texto_item += f"  ⭐ {puntos:.0f} pts"
                        if deuda > 0:
                            texto_item += f"  💸 ${deuda:,.0f}"
                        item = QListWidgetItem(texto_item)
                        item.setData(Qt.ItemDataRole.UserRole, c)
                        lista.addItem(item)
                        clientes_encontrados.append(c)
            except Exception:
                pass
        input_b.returnPressed.connect(buscar)
        def seleccionar(item):
            c = item.data(Qt.ItemDataRole.UserRole)
            self.cliente_actual = c
            puntos = float(c.get("puntos", 0))
            texto = f"👤 {c['nombre']}"
            if puntos >= 100:
                texto += f"\n⭐ {puntos:.0f} pts (canjeables)"
            self.lbl_cliente_info.setText(texto)
            self.lbl_cliente_info.show()
            self.btn_cliente.setText(f"👤 {c['nombre'][:18]}")
            self.btn_cliente.setStyleSheet("QPushButton { background: #27ae60; color: white; border-radius: 8px; font-size: 11px; border: 1px solid #27ae60; }")
            dialog.accept()
        lista.itemDoubleClicked.connect(seleccionar)
        btns = QHBoxLayout()
        btn_sin = QPushButton("Sin cliente")
        btn_sin.setFixedHeight(38)
        btn_sin.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_sin.setStyleSheet("QPushButton { background: transparent; color: #a0a0b0; border: 1px solid #a0a0b0; border-radius: 8px; }")
        def desvincular():
            self.cliente_actual = None
            self.lbl_cliente_info.hide()
            self.btn_cliente.setText("👤 Vincular cliente")
            self.btn_cliente.setStyleSheet("QPushButton { background: #0f3460; color: #3498db; border-radius: 8px; font-size: 12px; border: 1px solid #3498db; } QPushButton:hover { background: #3498db; color: white; }")
            dialog.accept()
        btn_sin.clicked.connect(desvincular)
        btns.addWidget(btn_sin)
        btn_ok = QPushButton("Seleccionar")
        btn_ok.setFixedHeight(38)
        btn_ok.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_ok.setStyleSheet("QPushButton { background: #3498db; color: white; border-radius: 8px; font-size: 13px; font-weight: bold; }")
        def sel_highlighted():
            items = lista.selectedItems()
            if items:
                seleccionar(items[0])
        btn_ok.clicked.connect(sel_highlighted)
        btns.addWidget(btn_ok)
        lay.addLayout(btns)
        input_b.setFocus()
        dialog.exec()
        self.input_buscar.setFocus()

    def repetir_ultimo(self):
        if self.ultimo_producto:
            self.agregar_item(self.ultimo_producto)
        else:
            QMessageBox.information(self, "Info", "No hay producto anterior para repetir")

    def verificar_precio(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Verificar precio")
        dialog.setMinimumWidth(340)
        dialog.setStyleSheet("background-color: #1a1a2e; color: white;")
        lay = QVBoxLayout(dialog)
        lay.setSpacing(10)
        lbl = QLabel("Buscar producto:")
        lbl.setStyleSheet("color: #a0a0b0; font-size: 13px;")
        lay.addWidget(lbl)
        input_buscar = QLineEdit()
        input_buscar.setPlaceholderText("Nombre o codigo...")
        input_buscar.setFixedHeight(44)
        input_buscar.setStyleSheet("QLineEdit { background: #0f3460; border: 1px solid #3498db; border-radius: 8px; padding: 10px; color: white; font-size: 14px; }")
        lay.addWidget(input_buscar)
        lista = QListWidget()
        lista.setStyleSheet("QListWidget { background: #16213e; border: 1px solid #0f3460; border-radius: 8px; color: white; } QListWidget::item { padding: 8px; }")
        lista.setMinimumHeight(200)
        lay.addWidget(lista)
        def buscar():
            texto = input_buscar.text().strip()
            if not texto:
                return
            try:
                r = requests.get(f"{API_URL}/productos/buscar", params={"q": texto}, timeout=5)
                if r.status_code == 200:
                    lista.clear()
                    for p in r.json()[:10]:
                        stock = float(p.get("stock_actual", 0))
                        item = QListWidgetItem(f"{p['nombre']}  |  ${float(p['precio_venta']):.2f}  |  Stock: {stock}")
                        lista.addItem(item)
            except Exception:
                pass
        input_buscar.returnPressed.connect(buscar)
        btn_buscar = QPushButton("Buscar")
        btn_buscar.setFixedHeight(36)
        btn_buscar.setStyleSheet("QPushButton { background: #3498db; color: white; border-radius: 8px; font-size: 13px; }")
        btn_buscar.clicked.connect(buscar)
        lay.addWidget(btn_buscar)
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setFixedHeight(36)
        btn_cerrar.setStyleSheet("QPushButton { background: transparent; color: #a0a0b0; border: 1px solid #a0a0b0; border-radius: 8px; }")
        btn_cerrar.clicked.connect(dialog.reject)
        lay.addWidget(btn_cerrar)
        dialog.exec()

    def actualizar_subtotales_depto(self):
        while self.depto_layout.count():
            child = self.depto_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        subtotales = {}
        for item in self.items_venta:
            nombre = item["nombre"]
            depto_key = "Productos"
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
                    QMessageBox.warning(self, "No encontrado", f"No se encontro: {texto}")
                    return
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
        lbl_montos = QLabel("- Sin items aun -")
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
                lbl_montos.setText("- Sin items aun -")
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
                QMessageBox.warning(dialog, "Error", "Ingresa un monto valido")
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
        input_monto.setPlaceholderText("Ingresa el monto y presiona Enter...")
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
        btn_borrar = QPushButton("<- Borrar ultimo")
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
        btn_confirmar = QPushButton("Agregar al ticket")
        btn_confirmar.setFixedHeight(44)
        btn_confirmar.setStyleSheet(f"QPushButton {{ background: {depto['color']}; color: white; border-radius: 8px; font-size: 14px; font-weight: bold; }}")
        btns.addWidget(btn_confirmar)
        layout.addLayout(btns)

        def confirmar():
            if not montos_temp:
                QMessageBox.warning(dialog, "Error", "Ingresa al menos un monto")
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
            QMessageBox.warning(self, "Error", "Precio y cantidad deben ser numeros")
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
        self.ultimo_producto = producto
        stock = float(producto.get("stock_actual", 0))
        for item in self.items_venta:
            if item["producto_id"] == producto["id"]:
                item["cantidad"] += 1
                item["subtotal"] = item["cantidad"] * item["precio_unitario"]
                if stock > 0 and item["cantidad"] >= stock:
                    QMessageBox.warning(self, "Stock bajo", f"Atencion: {producto['nombre']} tiene solo {stock} unidades en stock")
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
        if stock <= 1 and stock > 0:
            QMessageBox.warning(self, "Stock bajo", f"Ultima unidad de: {producto['nombre']}")
        elif stock == 0:
            QMessageBox.warning(self, "Sin stock", f"{producto['nombre']} no tiene stock disponible")
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
            btn_menos = QPushButton("-")
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
            btn_del = QPushButton("X")
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
            with open(ruta, "w", encoding="utf-8") as f:
                f.write("=" * 40 + "\
")
                f.write("JUANA CASH - INFORME DE VENTA\
")
                f.write("=" * 40 + "\
")
                f.write(f"Ticket: {ticket}\
")
                f.write(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\
")
                f.write(f"Cajero: {self.usuario['nombre'] if self.usuario else 'N/A'}\
")
                f.write(f"Pago: {metodo_pago}\
")
                f.write("-" * 40 + "\
")
                if descuento_pct > 0:
                    f.write(f"DESCUENTO: {descuento_pct:.1f}%\
")
                    f.write(f"Total original: ${total_original:.2f}\
")
                    f.write(f"Total final: ${total_final:.2f}\
")
                else:
                    f.write(f"Total: ${total_final:.2f}\
")
                if metodo_pago == "efectivo" and vuelto > 0:
                    f.write(f"Vuelto: ${vuelto:.2f}\
")
                f.write("=" * 40 + "\
")
        except Exception as e:
            print(f"Error: {e}")

    def ver_informe(self):
        if not self.log_eliminados and not self.log_ventas and not self.log_modificaciones:
            QMessageBox.information(self, "Informe", "No hay eventos registrados.")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Informe de sesion")
        dialog.setMinimumSize(720, 520)
        dialog.setStyleSheet("background-color: #1a1a2e; color: white;")
        layout = QVBoxLayout(dialog)
        estilo = "QTableWidget { background: #16213e; border: 1px solid #0f3460; border-radius: 8px; gridline-color: #0f3460; } QHeaderView::section { background: #0f3460; color: #a0a0b0; padding: 6px; border: none; } QTableWidgetItem { color: white; padding: 6px; }"
        if self.log_ventas:
            lbl3 = QLabel("Ventas cerradas")
            lbl3.setStyleSheet("color: #27ae60; font-size: 13px; font-weight: bold; padding: 4px 0;")
            layout.addWidget(lbl3)
            t3 = QTableWidget()
            t3.setColumnCount(5)
            t3.setHorizontalHeaderLabels(["Ticket", "Total", "Desc %", "Pago", "Hora"])
            t3.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            t3.setStyleSheet(estilo)
            t3.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            t3.setRowCount(len(self.log_ventas))
            for i, d in enumerate(self.log_ventas):
                t3.setItem(i, 0, QTableWidgetItem(d["ticket"]))
                t3.setItem(i, 1, QTableWidgetItem(f"${d['total_final']:.2f}"))
                t3.setItem(i, 2, QTableWidgetItem(f"{d['descuento_pct']:.1f}%"))
                t3.setItem(i, 3, QTableWidgetItem(d.get("metodo_pago", "-")))
                t3.setItem(i, 4, QTableWidgetItem(d.get("hora", "")))
            layout.addWidget(t3)
        dialog.exec()

    def cobrar(self):
        if not self.items_venta:
            QMessageBox.warning(self, "Sin productos", "Agrega productos antes de cobrar")
            return
        total_original = sum(i["subtotal"] for i in self.items_venta)
        dialog = CobrarDialog(self, total_original, cliente=self.cliente_actual)
        if not dialog.exec():
            return
        descuento_pct = dialog.descuento_pct
        total_final = dialog.total_final
        metodo_pago = dialog.metodo_pago
        metodo_secundario = dialog.metodo_secundario
        monto_secundario = dialog.monto_secundario
        descuento_monto = total_original - total_final
        vuelto = 0
        if metodo_pago == "efectivo":
            try:
                entrega = float(dialog.input_entrega.text().replace(",", "."))
                vuelto = max(0, entrega - (total_final - monto_secundario))
            except ValueError:
                pass

        items_backend = [i for i in self.items_venta if i["producto_id"] != 0]
        if not items_backend:
            items_backend = [{"producto_id": 1, "cantidad": 1, "precio_unitario": total_final, "descuento": 0}]

        pagos = [{"metodo": metodo_pago, "monto": total_final - monto_secundario}]
        if metodo_secundario and monto_secundario > 0:
            pagos.append({"metodo": metodo_secundario, "monto": monto_secundario})

        try:
            r = requests.post(f"{API_URL}/ventas/", json={
                "usuario_id": self.usuario.get("id", 1) if self.usuario else 1,
                "items": items_backend,
                "pagos": pagos,
                "descuento": descuento_monto
            }, timeout=5)
            if r.status_code == 200:
                datos = r.json()
                ticket = datos["numero"]
                nombres_metodo = {"efectivo": "Efectivo", "tarjeta": "Tarjeta", "mercadopago_qr": "QR/MP", "transferencia": "Transf."}
                metodo_str = nombres_metodo.get(metodo_pago, metodo_pago)
                if metodo_secundario:
                    metodo_str += f" + {nombres_metodo.get(metodo_secundario, metodo_secundario)} (${monto_secundario:.2f})"
                self.log_ventas.append({
                    "ticket": ticket,
                    "total_original": total_original,
                    "descuento_pct": descuento_pct,
                    "total_final": total_final,
                    "metodo_pago": metodo_str,
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
                if self.cliente_actual:
                    cid = self.cliente_actual["id"]
                    if dialog.descuento_puntos > 0:
                        try:
                            requests.post(f"{API_URL}/clientes/{cid}/canjear-puntos", timeout=3)
                        except Exception:
                            pass
                    try:
                        requests.post(f"{API_URL}/clientes/{cid}/sumar-puntos", params={"monto": total_final}, timeout=3)
                    except Exception:
                        pass
                self.guardar_informe(ticket, descuento_pct, total_original, total_final, metodo_str, vuelto)
                msg = f"Ticket: {ticket}\
Total: ${total_final:.2f}\
Pago: {metodo_str}"
                if descuento_pct > 0:
                    msg += f"\
Descuento: {descuento_pct:.1f}%"
                if metodo_pago == "efectivo" and vuelto > 0:
                    msg += f"\
Vuelto: ${vuelto:.2f}"
                try:
                    from ui.pantallas.impresora import imprimir_ticket
                    exito, txt = imprimir_ticket({"numero": ticket, "total": total_final}, self.items_venta)
                    QMessageBox.information(self, "Venta registrada", msg + f"\
\
{txt}")
                except Exception:
                    QMessageBox.information(self, "Venta registrada", msg)
                self.cancelar_venta()
            else:
                QMessageBox.critical(self, "Error", "No se pudo registrar la venta")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se puede conectar al servidor\
{str(e)}")

    # \u2705 CORRECTO: cancelar_venta es m\u00e9todo de VentasScreen, NO de cobrar
    def cancelar_venta(self):
        self.items_venta = []
        self.cliente_actual = None
        self.lbl_cliente_info.hide()
        self.btn_cliente.setText("👤 Vincular cliente")
        self.btn_cliente.setStyleSheet("QPushButton { background: #0f3460; color: #3498db; border-radius: 8px; font-size: 12px; border: 1px solid #3498db; } QPushButton:hover { background: #3498db; color: white; }")
        self.actualizar_tabla()
        self.input_buscar.clear()
        self.input_buscar.setFocus()