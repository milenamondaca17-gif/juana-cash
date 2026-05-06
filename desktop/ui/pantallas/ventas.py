import requests
import os
import json
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTableWidget,
                             QTableWidgetItem, QMessageBox, QFrame, QHeaderView,
                             QDialog, QDoubleSpinBox, QScrollArea,
                             QListWidget, QListWidgetItem, QTextEdit)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QShortcut, QKeySequence, QPixmap

try:
    from ui.pantallas.ticket_utils import ticket_para_whatsapp, abrir_whatsapp, formatear_ticket_texto, cargar_config_negocio
    cargar_config_negocio()
except Exception:
    ticket_para_whatsapp = None
    abrir_whatsapp = None

try:
    from ui.pantallas.offline_manager import encolar_venta, sincronizar_cola, cantidad_pendientes
except Exception:
    encolar_venta = None

try:
    from ui.pantallas.ofertas import OfertasRotator
except Exception:
    OfertasRotator = None

API_URL = "http://127.0.0.1:8000"

from ui.theme import get_tema as _get_tema
_T = _get_tema()

DEPARTAMENTOS = {
    "7":    {"nombre": "Kiosco",     "icono": "🛒", "color": "#8e44ad"},
    "930":  {"nombre": "Carnicería", "icono": "🥩", "color": "#e74c3c"},
    "1003": {"nombre": "Fiambrería", "icono": "🧀", "color": "#f39c12"},
    "1004": {"nombre": "Lácteos",    "icono": "🥛", "color": "#3498db"},
    "1005": {"nombre": "Golosinas",  "icono": "🍬", "color": "#e91e8c"},
    "1006": {"nombre": "Líquidos",   "icono": "🍻", "color": "#1abc9c"},
    "901":  {"nombre": "Verdulería", "icono": "🥬", "color": "#27ae60"},
    "902":  {"nombre": "Panadería",  "icono": "🍞", "color": "#e67e22"},
    "905":  {"nombre": "Limpieza",   "icono": "🧹", "color": "#9b59b6"},
    "909":  {"nombre": "Varios",     "icono": "📦", "color": "#95a5a6"},
}

BG_MAIN      = _T["bg_app"]
BG_PANEL     = _T["bg_card"]
BORDER       = _T["border"]
TEXT_MAIN    = _T["text_main"]
TEXT_MUTED   = _T["text_muted"]
ACCENT_OFERTAS = _T["accent_yellow"]
ACCENT_TOTAL   = _T["accent_green"]
ACCENT_BOTON   = _T["primary"]

from PyQt6.QtWidgets import QCheckBox

def _p(v):
    """Precio en formato argentino: $10.000"""
    return f"${float(v):,.0f}".replace(",", ".")

# ─── AUDITORÍA PERSISTENTE ────────────────────────────────────────────────────
AUDITORIA_PATH = os.path.join(os.path.expanduser("~"), "JuanaCash_Tickets", "auditoria.json")

def _leer_auditoria():
    try:
        os.makedirs(os.path.dirname(AUDITORIA_PATH), exist_ok=True)
        if os.path.exists(AUDITORIA_PATH):
            with open(AUDITORIA_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return []

def _guardar_evento(evento):
    """Agrega un evento al historial persistente."""
    try:
        registros = _leer_auditoria()
        evento["fecha"] = datetime.now().strftime("%Y-%m-%d")
        evento["hora"] = datetime.now().strftime("%H:%M:%S")
        registros.append(evento)
        if len(registros) > 5000:
            registros = registros[-5000:]
        os.makedirs(os.path.dirname(AUDITORIA_PATH), exist_ok=True)
        with open(AUDITORIA_PATH, "w", encoding="utf-8") as f:
            json.dump(registros, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

class CobrarDialog(QDialog):
    def __init__(self, parent=None, total=0, cliente=None):
        super().__init__(parent)
        self.setWindowTitle("Cobrar venta")
        self.setMinimumWidth(500)
        self.setStyleSheet(f"background-color: {BG_MAIN}; color: {TEXT_MAIN};")
        self.total_original = total
        self.descuento_pct = 0
        self.total_final = total
        self.metodo_pago = "efectivo"
        self.metodo_secundario = None
        self.monto_secundario = 0
        self.btns_pago = {}
        self.btns_secundarios = {}
        self.cliente = cliente
        self.descuento_puntos = 0
        self.cupon_aplicado = None
        self.cupon_pct = 0
        self.recargo_pct = 0.0
        self.recargo_monto = 0.0
        self.setup_ui()

    def keyPressEvent(self, event):
        from PyQt6.QtCore import Qt
        if event.key() == Qt.Key.Key_F4:
            self.accept()
        else:
            super().keyPressEvent(event)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        lbl_total = QLabel(f"Total: {_p(self.total_original)}")
        lbl_total.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        lbl_total.setStyleSheet(f"color: {ACCENT_OFERTAS};")
        lbl_total.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_total)

        if self.cliente and float(self.cliente.get("puntos", 0)) >= 100:
            puntos = float(self.cliente.get("puntos", 0))
            bloques = int(puntos // 100)
            descuento_max = bloques * 1000
            puntos_frame = QFrame()
            puntos_frame.setStyleSheet(f"QFrame {{ background: {BG_PANEL}; border-radius: 8px; border: 1px solid {ACCENT_OFERTAS}; }}")
            puntos_layout = QHBoxLayout(puntos_frame)
            lbl_pts = QLabel(f"⭐ {puntos:.0f} pts → ${descuento_max:,.0f} off")
            lbl_pts.setStyleSheet(f"color: {ACCENT_OFERTAS};")
            puntos_layout.addWidget(lbl_pts)
            self.btn_canjear_pts = QPushButton("Canjear")
            self.btn_canjear_pts.clicked.connect(lambda: self.aplicar_descuento_puntos(descuento_max))
            self.btn_canjear_pts.setStyleSheet(f"background: {ACCENT_OFERTAS}; color: {BG_MAIN}; border-radius: 4px; font-weight: bold; padding: 5px;")
            puntos_layout.addWidget(self.btn_canjear_pts)
            layout.addWidget(puntos_frame)

        desc_frame = QFrame()
        desc_frame.setStyleSheet(f"QFrame {{ background: {BG_PANEL}; border-radius: 8px; }}")
        desc_layout = QHBoxLayout(desc_frame)
        desc_layout.addWidget(QLabel("Descuento (%):"))
        self.input_pct = QDoubleSpinBox()
        self.input_pct.setRange(0, 100)
        self.input_pct.setSingleStep(5)
        self.input_pct.setStyleSheet(f"background: {BG_MAIN}; border: 1px solid {BORDER}; color: {TEXT_MAIN}; padding: 5px;")
        self.input_pct.valueChanged.connect(self.actualizar_total)
        desc_layout.addWidget(self.input_pct)
        layout.addWidget(desc_frame)

        # ── Campo cupón de descuento ─────────────────────────────────────────
        cupon_frame = QFrame()
        cupon_frame.setStyleSheet(f"QFrame {{ background: {BG_PANEL}; border-radius: 8px; }}")
        cupon_lay = QHBoxLayout(cupon_frame)
        cupon_lay.setContentsMargins(10, 8, 10, 8)
        cupon_lay.addWidget(QLabel("🎟️ Cupón:", styleSheet="color: #a0a0b0; font-size: 13px;"))
        self.input_cupon = QLineEdit()
        self.input_cupon.setPlaceholderText("Escaneá o ingresá el código...")
        self.input_cupon.setFixedHeight(36)
        self.input_cupon.setStyleSheet(f"QLineEdit {{ background: {BG_MAIN}; border: 1px solid #8e44ad; border-radius: 6px; color: white; padding: 4px 8px; font-size: 13px; }}")
        self.input_cupon.returnPressed.connect(self.validar_cupon)
        cupon_lay.addWidget(self.input_cupon)
        btn_aplicar_cupon = QPushButton("Aplicar")
        btn_aplicar_cupon.setFixedSize(70, 36)
        btn_aplicar_cupon.setStyleSheet("QPushButton { background: #8e44ad; color: white; border-radius: 6px; font-weight: bold; } QPushButton:hover { background: #9b59b6; }")
        btn_aplicar_cupon.clicked.connect(self.validar_cupon)
        cupon_lay.addWidget(btn_aplicar_cupon)
        self.lbl_cupon_status = QLabel("")
        self.lbl_cupon_status.setStyleSheet("color: #27ae60; font-size: 12px; font-weight: bold;")
        cupon_lay.addWidget(self.lbl_cupon_status)
        layout.addWidget(cupon_frame)

        self.lbl_total_final = QLabel(f"A cobrar: {_p(self.total_original)}")
        self.lbl_total_final.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.lbl_total_final.setStyleSheet(f"color: {ACCENT_TOTAL};")
        self.lbl_total_final.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_total_final)

        # --- METODO PRINCIPAL ---
        lbl_metodo = QLabel("1️⃣ Método de pago principal:")
        lbl_metodo.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px; font-weight: bold;")
        layout.addWidget(lbl_metodo)

        metodos_layout = QHBoxLayout()
        metodos = [
            ("Efectivo", "efectivo",      ACCENT_TOTAL),
            ("Tarjeta",  "tarjeta",       ACCENT_BOTON),
            ("QR/MP",    "mercadopago_qr","#009ee3"),
            ("Transf.",  "transferencia", "#9b59b6"),
            ("Fiado",    "fiado",         "#e74c3c"),
        ]
        for nombre, key, color in metodos:
            btn = QPushButton(nombre)
            btn.setFixedSize(85, 44)
            btn.clicked.connect(lambda _, k=key, c=color: self.seleccionar_metodo(k, c))
            if key == "fiado" and not self.cliente:
                btn.setEnabled(False)
                btn.setToolTip("Vincula un cliente antes de usar Fiado")
                btn.setStyleSheet("background: #2a2a2a; color: #555; border: 1px solid #333; border-radius: 8px;")
            metodos_layout.addWidget(btn)
            self.btns_pago[key] = (btn, color)
        layout.addLayout(metodos_layout)

        # ── Recargo tarjeta crédito ───────────────────────────────────────────
        self.recargo_frame = QFrame()
        self.recargo_frame.setStyleSheet(f"QFrame {{ background: {BG_PANEL}; border-radius: 8px; border: 1.5px solid {ACCENT_BOTON}; }}")
        rec_lay = QVBoxLayout(self.recargo_frame)
        rec_lay.setContentsMargins(12, 10, 12, 10)
        rec_lay.setSpacing(6)
        lbl_rec_t = QLabel("💳 Recargo tarjeta crédito")
        lbl_rec_t.setStyleSheet(f"color: {ACCENT_BOTON}; font-weight: bold; font-size: 13px;")
        rec_lay.addWidget(lbl_rec_t)
        rec_pct_row = QHBoxLayout()
        lbl_rec_pct = QLabel("Recargo (%):")
        lbl_rec_pct.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px;")
        rec_pct_row.addWidget(lbl_rec_pct)
        self.spin_recargo = QDoubleSpinBox()
        self.spin_recargo.setRange(0, 50)
        self.spin_recargo.setSingleStep(1)
        self.spin_recargo.setValue(10)
        self.spin_recargo.setSuffix(" %")
        self.spin_recargo.setFixedHeight(36)
        self.spin_recargo.setFixedWidth(100)
        self.spin_recargo.setStyleSheet(f"QDoubleSpinBox {{ background: {BG_MAIN}; border: 1.5px solid {ACCENT_BOTON}; border-radius: 6px; padding: 5px; color: white; font-size: 14px; font-weight: bold; }}")
        self.spin_recargo.valueChanged.connect(self.actualizar_total)
        rec_pct_row.addWidget(self.spin_recargo)
        rec_pct_row.addStretch()
        rec_lay.addLayout(rec_pct_row)
        self.lbl_detalle_recargo = QLabel("")
        self.lbl_detalle_recargo.setStyleSheet(f"color: {ACCENT_BOTON}; font-size: 13px; font-weight: bold;")
        self.lbl_detalle_recargo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rec_lay.addWidget(self.lbl_detalle_recargo)
        self.recargo_frame.setVisible(False)
        layout.addWidget(self.recargo_frame)

        # --- INICIO COBRO MIXTO ---
        self.frame_mixto = QFrame()
        self.frame_mixto.setStyleSheet(f"QFrame {{ background: {BG_PANEL}; border-radius: 8px; border: 1px dashed {ACCENT_OFERTAS}; }}")
        mixto_lay = QVBoxLayout(self.frame_mixto)

        self.chk_mixto = QCheckBox("💳 Dividir pago (Cobro Mixto)")
        self.chk_mixto.setStyleSheet(f"color: {ACCENT_OFERTAS}; font-weight: bold; font-size: 14px;")
        self.chk_mixto.stateChanged.connect(self.toggle_mixto)
        mixto_lay.addWidget(self.chk_mixto)

        self.panel_secundario = QWidget()
        sec_lay = QVBoxLayout(self.panel_secundario)
        sec_lay.setContentsMargins(0, 10, 0, 0)

        row_monto = QHBoxLayout()
        lbl_monto_sec = QLabel("Monto del 2do método: $")
        lbl_monto_sec.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px;")
        row_monto.addWidget(lbl_monto_sec)

        self.input_monto_sec = QLineEdit()
        self.input_monto_sec.setPlaceholderText("Ej: 5000")
        self.input_monto_sec.setStyleSheet(f"background: {BG_MAIN}; color: white; font-size: 18px; padding: 5px; border: 1px solid {ACCENT_OFERTAS}; border-radius: 4px;")
        self.input_monto_sec.textChanged.connect(self.calcular_mixto)
        row_monto.addWidget(self.input_monto_sec)
        sec_lay.addLayout(row_monto)

        lbl_metodo_sec = QLabel("2️⃣ Elegí el 2do método:")
        lbl_metodo_sec.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px; font-weight: bold;")
        sec_lay.addWidget(lbl_metodo_sec)

        metodos_sec_layout = QHBoxLayout()
        for nombre, key, color in metodos:
            btn = QPushButton(nombre)
            btn.setFixedSize(85, 36)
            btn.clicked.connect(lambda _, k=key, c=color: self.seleccionar_metodo_sec(k, c))
            if key == "fiado" and not self.cliente:
                btn.setEnabled(False)
                btn.setToolTip("Vincula un cliente antes de usar Fiado")
                btn.setStyleSheet("background: #2a2a2a; color: #555; border: 1px solid #333; border-radius: 8px;")
            metodos_sec_layout.addWidget(btn)
            self.btns_secundarios[key] = (btn, color)
        sec_lay.addLayout(metodos_sec_layout)

        self.lbl_resumen_mixto = QLabel("")
        self.lbl_resumen_mixto.setStyleSheet(f"color: {ACCENT_TOTAL}; font-size: 14px; font-weight: bold;")
        self.lbl_resumen_mixto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sec_lay.addWidget(self.lbl_resumen_mixto)

        self.panel_secundario.setVisible(False)
        mixto_lay.addWidget(self.panel_secundario)
        layout.addWidget(self.frame_mixto)
        # --- FIN COBRO MIXTO ---

        self.vuelto_frame = QFrame()
        self.vuelto_frame.setStyleSheet(f"background: {BG_PANEL}; border: 1px solid {ACCENT_TOTAL}; border-radius: 8px;")
        v_lay = QVBoxLayout(self.vuelto_frame)
        self.input_entrega = QLineEdit()
        self.input_entrega.setStyleSheet(f"background: {BG_MAIN}; color: white; font-size: 20px; padding: 5px;")
        self.input_entrega.textChanged.connect(self.calcular_vuelto)
        v_lay.addWidget(QLabel("El cliente entrega en EFECTIVO ($):"))
        v_lay.addWidget(self.input_entrega)
        self.lbl_vuelto = QLabel("Vuelto: -")
        self.lbl_vuelto.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        self.lbl_vuelto.setStyleSheet(f"color: {ACCENT_TOTAL};")
        v_lay.addWidget(self.lbl_vuelto)
        layout.addWidget(self.vuelto_frame)

        btns = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setFixedHeight(44)
        btn_cancelar.clicked.connect(self.reject)
        btn_cancelar.setStyleSheet(f"background: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 6px;")
        btns.addWidget(btn_cancelar)
        self.btn_cobrar = QPushButton("COBRAR")
        self.btn_cobrar.setFixedHeight(44)
        self.btn_cobrar.clicked.connect(self.accept)
        btns.addWidget(self.btn_cobrar)
        layout.addLayout(btns)
        
        self.seleccionar_metodo("efectivo", ACCENT_TOTAL)

    def toggle_mixto(self, state):
        activo = (state == 2)
        self.panel_secundario.setVisible(activo)
        if not activo:
            self.metodo_secundario = None
            self.monto_secundario = 0
            self.input_monto_sec.clear()
            for btn, c in self.btns_secundarios.values():
                btn.setStyleSheet(f"background: {BG_PANEL}; color: {TEXT_MUTED}; border: 1px solid {BORDER}; border-radius: 8px;")
            self.lbl_resumen_mixto.setText("")
        self.calcular_mixto()

    def seleccionar_metodo(self, key, color):
        self.metodo_pago = key
        for k, (btn, c) in self.btns_pago.items():
            btn.setStyleSheet(f"background: {BG_PANEL}; color: {TEXT_MUTED}; border: 1px solid {BORDER}; border-radius: 8px;")
        self.btns_pago[key][0].setStyleSheet(f"background: {color}; color: white; font-weight: bold; border-radius: 8px;")
        self.recargo_frame.setVisible(key == "tarjeta")
        self.actualizar_total()

    def seleccionar_metodo_sec(self, key, color):
        self.metodo_secundario = key
        for k, (btn, c) in self.btns_secundarios.items():
            btn.setStyleSheet(f"background: {BG_PANEL}; color: {TEXT_MUTED}; border: 1px solid {BORDER}; border-radius: 8px;")
        self.btns_secundarios[key][0].setStyleSheet(f"background: {color}; color: white; font-weight: bold; border-radius: 8px;")
        self.calcular_mixto()

    def calcular_mixto(self):
        if not self.chk_mixto.isChecked():
            self.monto_secundario = 0
            self.vuelto_frame.setVisible(self.metodo_pago == "efectivo")
            nombres = {"efectivo": "Efectivo", "tarjeta": "Tarjeta", "mercadopago_qr": "QR/MP", "transferencia": "Transf."}
            nom_prin = nombres.get(self.metodo_pago, self.metodo_pago)
            self.btn_cobrar.setText(f"F4 - COBRAR {nom_prin}")
            self.calcular_vuelto()
            return
            
        try:
            monto_sec = float(self.input_monto_sec.text().replace(",", "."))
        except ValueError:
            monto_sec = 0
            
        if monto_sec > self.total_final:
            monto_sec = self.total_final
            
        self.monto_secundario = monto_sec
        monto_prin = self.total_final - self.monto_secundario
        
        nombres = {"efectivo": "Efectivo", "tarjeta": "Tarjeta", "mercadopago_qr": "QR/MP", "transferencia": "Transf."}
        nom_prin = nombres.get(self.metodo_pago, self.metodo_pago)
        nom_sec = nombres.get(self.metodo_secundario, "Segundo método") if self.metodo_secundario else "Segundo método"
        
        if self.metodo_secundario:
            self.lbl_resumen_mixto.setText(f"Pago: {_p(monto_prin)} ({nom_prin}) + {_p(self.monto_secundario)} ({nom_sec})")
            self.btn_cobrar.setText("F4 - COBRAR MIXTO")
        else:
            self.lbl_resumen_mixto.setText("⚠️ Elegí el segundo método de pago")
            self.btn_cobrar.setText("F4 - COBRAR MIXTO")
            
        # Mostrar el vuelto solo si ALGUNO de los dos métodos es efectivo
        self.vuelto_frame.setVisible((self.metodo_pago == "efectivo") or (self.metodo_secundario == "efectivo"))
        self.calcular_vuelto()

    def calcular_vuelto(self):
        # Si hay efectivo, calculamos el vuelto en base a CUÁNTO se paga en efectivo
        monto_en_efectivo = 0
        if self.metodo_pago == "efectivo":
            monto_en_efectivo = self.total_final - self.monto_secundario
        elif self.metodo_secundario == "efectivo":
            monto_en_efectivo = self.monto_secundario

        try:
            entrega = float(self.input_entrega.text().replace(",", "."))
            vuelto = entrega - monto_en_efectivo
            if vuelto < 0:
                self.lbl_vuelto.setText(f"Falta: {_p(abs(vuelto))}")
                self.lbl_vuelto.setStyleSheet("color: #F46A6A; font-size: 20px; font-weight: bold;")
            else:
                self.lbl_vuelto.setText(f"Vuelto: {_p(vuelto)}")
                self.lbl_vuelto.setStyleSheet(f"color: {ACCENT_TOTAL}; font-size: 20px; font-weight: bold;")
        except:
            self.lbl_vuelto.setText("Vuelto: -")
            self.lbl_vuelto.setStyleSheet(f"color: {ACCENT_TOTAL}; font-size: 20px; font-weight: bold;")

    def validar_cupon(self):
        codigo = self.input_cupon.text().strip().upper()
        if not codigo:
            return
        try:
            r = requests.get(f"{API_URL}/cupones/validar/{codigo}", timeout=5)
            data = r.json()
        except Exception:
            self.lbl_cupon_status.setText("❌ Error de conexión")
            self.lbl_cupon_status.setStyleSheet("color: #e74c3c; font-size: 12px; font-weight: bold;")
            return

        if data.get("valido"):
            self.cupon_aplicado = codigo
            self.cupon_pct = float(data.get("porcentaje", 0))
            self.lbl_cupon_status.setText(f"✅ -{self.cupon_pct:.0f}% ({data.get('cliente','')})")
            self.lbl_cupon_status.setStyleSheet("color: #27ae60; font-size: 12px; font-weight: bold;")
            self.input_cupon.setStyleSheet("QLineEdit { background: #0d2a1a; border: 1px solid #27ae60; border-radius: 6px; color: #27ae60; padding: 4px 8px; font-size: 13px; font-weight: bold; }")
            self.actualizar_total()
        else:
            self.cupon_aplicado = None
            self.cupon_pct = 0
            motivo = data.get("motivo", "Inválido")
            self.lbl_cupon_status.setText(f"❌ {motivo}")
            self.lbl_cupon_status.setStyleSheet("color: #e74c3c; font-size: 12px; font-weight: bold;")
            self.input_cupon.setStyleSheet("QLineEdit { background: #2a0d0d; border: 1px solid #e74c3c; border-radius: 6px; color: #e74c3c; padding: 4px 8px; font-size: 13px; }")
            self.actualizar_total()

    def actualizar_total(self):
        self.descuento_pct = self.input_pct.value()
        descuento_total = self.descuento_pct + self.cupon_pct
        subtotal = self.total_original - (self.total_original * descuento_total / 100) - self.descuento_puntos
        if self.metodo_pago == "tarjeta" and hasattr(self, "spin_recargo"):
            self.recargo_pct = self.spin_recargo.value()
            self.recargo_monto = round(subtotal * self.recargo_pct / 100, 2)
            self.total_final = subtotal + self.recargo_monto
            self.lbl_detalle_recargo.setText(
                f"Subtotal: {_p(subtotal)}  +  {self.recargo_pct:.0f}%: {_p(self.recargo_monto)}  =  {_p(self.total_final)}"
            )
        else:
            self.recargo_pct = 0.0
            self.recargo_monto = 0.0
            self.total_final = subtotal
        self.lbl_total_final.setText(f"A cobrar: {_p(self.total_final)}")
        self.calcular_mixto()

    def aplicar_descuento_puntos(self, monto):
        self.descuento_puntos = monto
        self.btn_canjear_pts.setEnabled(False)
        self.btn_canjear_pts.setText("Canjeado")
        self.actualizar_total()

class EditarItemDialog(QDialog):
    def __init__(self, parent=None, item=None):
        super().__init__(parent)
        self.item = item
        self.setWindowTitle(f"Editar - {item['nombre']}")
        self.setStyleSheet(f"background-color: {BG_MAIN}; color: {TEXT_MAIN};")
        self.nuevo_precio = item["precio_unitario"]
        self.nueva_cantidad = item["cantidad"]
        self.setup_ui()

    def setup_ui(self):
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel(self.item["nombre"]))
        self.input_precio = QLineEdit(str(self.item["precio_unitario"]))
        self.input_cant = QLineEdit(str(self.item["cantidad"]))
        self.input_precio.setStyleSheet(f"background: {BG_PANEL}; border: 1px solid {BORDER}; padding: 5px;")
        self.input_cant.setStyleSheet(f"background: {BG_PANEL}; border: 1px solid {BORDER}; padding: 5px;")
        lay.addWidget(QLabel("Precio:"))
        lay.addWidget(self.input_precio)
        lay.addWidget(QLabel("Cantidad:"))
        lay.addWidget(self.input_cant)
        btn = QPushButton("Guardar")
        btn.setStyleSheet(f"background: {ACCENT_BOTON}; color: white; padding: 8px;")
        btn.clicked.connect(self.guardar)
        lay.addWidget(btn)

    def guardar(self):
        try:
            self.nuevo_precio = float(self.input_precio.text())
            self.nueva_cantidad = float(self.input_cant.text())
            self.accept()
        except:
            QMessageBox.warning(self, "Error", "Valores inválidos")

class EditorOfertasDialog(QDialog):
    def __init__(self, parent=None, texto_actual=""):
        super().__init__(parent)
        self.setWindowTitle("📝 Editar Ofertas")
        self.setMinimumWidth(500)
        self.setStyleSheet(f"background-color: {BG_MAIN}; color: {TEXT_MAIN};")
        lay = QVBoxLayout(self)
        self.txt = QTextEdit(self)
        self.txt.setPlainText(texto_actual)
        self.txt.setStyleSheet(f"background: {BG_PANEL}; border: 1px solid {BORDER}; color: white; font-size: 16px;")
        lay.addWidget(self.txt)
        btns = QHBoxLayout()
        btn_c = QPushButton("Cancelar")
        btn_c.setFixedHeight(40)
        btn_c.setStyleSheet(f"background: transparent; color: {TEXT_MUTED}; border: 1px solid {BORDER}; border-radius: 6px; font-weight: bold;")
        btn_c.clicked.connect(self.reject)
        btns.addWidget(btn_c)
        btn_g = QPushButton("Guardar Cambios")
        btn_g.setFixedHeight(40)
        btn_g.setStyleSheet(f"background: {ACCENT_OFERTAS}; color: {BG_MAIN}; border-radius: 6px; font-weight: bold;")
        btn_g.clicked.connect(self.accept)
        btns.addWidget(btn_g)
        lay.addLayout(btns)

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
        self.cliente_actual = None
        self.tickets_en_espera = []
        # Cache local de productos — se carga al inicio, búsqueda sin red
        self.productos_cache = []        # lista completa
        self.productos_codigo = {}       # codigo_barra → producto (lookup O(1))
        self.setup_ui()

    def set_usuario(self, usuario):
        self.usuario = usuario
        # Cargar cache de productos en hilo separado al iniciar
        import threading
        threading.Thread(target=self._cargar_cache_productos, daemon=True).start()

    def _cargar_cache_productos(self):
        """Carga todos los productos una sola vez. Búsquedas sin red."""
        try:
            r = requests.get(f"{API_URL}/productos/", timeout=10)
            if r.status_code == 200:
                productos = r.json()
                self.productos_cache = productos
                self.productos_codigo = {
                    str(p["codigo_barra"]): p
                    for p in productos
                    if p.get("codigo_barra")
                }
        except Exception:
            pass

    def setup_ui(self):
        self.setStyleSheet(f"background-color: {BG_MAIN}; color: {TEXT_MAIN};")
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        contenido = QHBoxLayout()
        contenido.setContentsMargins(10, 10, 10, 10)
        contenido.setSpacing(10)

        # ═══════════════════════════════════════════════════
        # PANEL IZQUIERDO
        # ═══════════════════════════════════════════════════
        panel_izq = QVBoxLayout()
        panel_izq.setSpacing(8)

        busq_frame = QFrame()
        busq_frame.setStyleSheet(f"QFrame {{ background: {BG_PANEL}; border-radius: 12px; border: 2px solid {ACCENT_BOTON}; }}")
        busq_layout = QHBoxLayout(busq_frame)
        busq_layout.setContentsMargins(4, 4, 4, 4)
        busq_layout.setSpacing(6)
        lbl_scan = QLabel("🔍")
        lbl_scan.setStyleSheet(f"color: {ACCENT_BOTON}; font-size: 18px; padding: 0 6px;")
        busq_layout.addWidget(lbl_scan)
        
        self.input_buscar = QLineEdit()
        self.input_buscar.setPlaceholderText("Escaneá o buscá por nombre  —  F3 para enfocar")
        self.input_buscar.setFixedHeight(44)
        self.input_buscar.setStyleSheet("QLineEdit { background: transparent; border: none; font-size: 16px; padding: 0 8px; }")
        self.input_buscar.returnPressed.connect(self.buscar_producto)
        busq_layout.addWidget(self.input_buscar)
        
        btn_buscar = QPushButton("AGREGAR")
        btn_buscar.setFixedSize(100, 44)
        btn_buscar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_buscar.setStyleSheet(f"QPushButton {{ background: {ACCENT_BOTON}; color: white; border-radius: 8px; font-size: 13px; font-weight: bold; letter-spacing: 1px; }}")
        btn_buscar.clicked.connect(self.buscar_producto)
        busq_layout.addWidget(btn_buscar)
        panel_izq.addWidget(busq_frame)

        self.input_manual_nombre = QLineEdit(); self.input_manual_nombre.hide()
        self.input_manual_precio = QLineEdit(); self.input_manual_precio.hide()
        self.input_manual_cant = QLineEdit(); self.input_manual_cant.setText("1"); self.input_manual_cant.hide()

        self.frame_ofertas = QFrame()
        self.frame_ofertas.setFixedHeight(60)
        self.frame_ofertas.setStyleSheet(f"QFrame {{ background: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 12px; }}")
        lay_ofertas = QHBoxLayout(self.frame_ofertas)
        lay_ofertas.setContentsMargins(10, 0, 10, 0)
        
        self.contenedor_marquee = QWidget()
        self.contenedor_marquee.setStyleSheet("background: transparent;")
        layout_marquee = QHBoxLayout(self.contenedor_marquee)
        layout_marquee.setContentsMargins(0, 0, 0, 0)
        
        self.texto_ofertas = QLabel("¡Bienvenidos a EL CUERVO STORE!   *** Ofertas del día   *** ")
        self.texto_ofertas.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.texto_ofertas.setStyleSheet(f"color: {ACCENT_OFERTAS}; background: transparent; border: none;")
        self.texto_ofertas.adjustSize()
        layout_marquee.addWidget(self.texto_ofertas)
        
        lay_ofertas.addWidget(self.contenedor_marquee, stretch=1)
        
        btn_editar_ofertas = QPushButton("📝 Editar")
        btn_editar_ofertas.setFixedSize(70, 30)
        btn_editar_ofertas.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_editar_ofertas.setStyleSheet(f"QPushButton {{ background: transparent; color: {TEXT_MUTED}; border: 1px solid {BORDER}; border-radius: 6px; font-weight: bold; font-size: 11px; }} QPushButton:hover {{ background: {BORDER}; color: white; }}")
        btn_editar_ofertas.clicked.connect(self.abrir_editor_ofertas)
        lay_ofertas.addWidget(btn_editar_ofertas, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        panel_izq.addWidget(self.frame_ofertas)

        self.offset_marquee = 0
        self.timer_marquee = QTimer(self)
        self.timer_marquee.timeout.connect(self.animar_marquee)
        self.timer_marquee.start(60)
        self.input_buscar.installEventFilter(self)

        atajos_frame = QFrame()
        atajos_frame.setStyleSheet(f"QFrame {{ background: {BG_PANEL}; border-radius: 8px; }}")
        atajos_lay = QHBoxLayout(atajos_frame)
        atajos_lay.setContentsMargins(12, 6, 12, 6)
        atajos_lay.setSpacing(0)
        # NUEVO: Agregamos "F5 Pausar" a la lista visual de atajos
        for texto, color in [
            ("F2 Rápido",    "#e67e22"),
            ("F3 Precios",   "#1abc9c"),
            ("F5 Pausar",    "#F59E0B"),
            ("F6 Buscar",    ACCENT_BOTON),
            ("F9 Cobrar",    ACCENT_TOTAL),
        ]:
            lbl = QLabel(f"<b style='color:{color}'>{texto.split()[0]}</b><span style='color:{TEXT_MUTED}'> {texto.split()[1]}</span>")
            lbl.setStyleSheet("font-size: 13px; padding: 0 10px;")
            atajos_lay.addWidget(lbl)
        atajos_lay.addStretch()
        btn_precios = QPushButton("🔎 Verificar precio")
        btn_precios.setFixedHeight(30)
        btn_precios.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_precios.setStyleSheet(f"QPushButton {{ background: {BG_MAIN}; color: {ACCENT_BOTON}; border-radius: 6px; font-size: 12px; padding: 0 10px; border: 1px solid {BORDER}; font-weight: bold;}} QPushButton:hover {{ background: {ACCENT_BOTON}; color: white; }}")
        btn_precios.clicked.connect(self.verificar_precio)
        atajos_lay.addWidget(btn_precios)
        panel_izq.addWidget(atajos_frame)

        self.tabla = QTableWidget(0, 6)
        self.tabla.setHorizontalHeaderLabels(["Producto", "Precio unit.", "Cant.", "Subtotal", "Ajustar", ""])
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabla.setColumnWidth(1, 150)
        self.tabla.setColumnWidth(2, 70)
        self.tabla.setColumnWidth(3, 150)
        self.tabla.setColumnWidth(4, 110)
        self.tabla.setColumnWidth(5, 50)
        self.tabla.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        self.tabla.verticalHeader().setDefaultSectionSize(60) 
        self.tabla.setShowGrid(False)
        self.tabla.setStyleSheet(f"""
            QTableWidget {{ background: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 12px; gridline-color: transparent; outline: none; font-size: 18px; font-weight: bold; }}
            QHeaderView::section {{ background: {BG_MAIN}; color: {TEXT_MUTED}; padding: 10px; border: none; font-size: 13px; letter-spacing: 1px; text-transform: uppercase; font-weight: bold; }}
            QTableWidget::item {{ color: {TEXT_MAIN}; padding: 6px 8px; border-bottom: 1px solid {BORDER}; }}
            QTableWidget::item:selected {{ background: {BORDER}; }}
        """)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.cellDoubleClicked.connect(self.editar_item_doble_clic)
        panel_izq.addWidget(self.tabla)
        contenido.addLayout(panel_izq, 3)

        # ═══════════════════════════════════════════════════
        # PANEL DERECHO
        # ═══════════════════════════════════════════════════
        panel_der = QVBoxLayout()
        panel_der.setSpacing(8)

        total_frame = QFrame()
        total_frame.setMinimumWidth(350) 
        total_frame.setStyleSheet(f"QFrame {{ background: {BG_PANEL}; border-radius: 16px; border: 1px solid {BORDER}; }}")
        total_layout = QVBoxLayout(total_frame)
        total_layout.setContentsMargins(18, 18, 18, 18)
        total_layout.setSpacing(10)

        lbl_total_titulo = QLabel("TOTAL A COBRAR")
        lbl_total_titulo.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; letter-spacing: 2px; font-weight: bold;")
        total_layout.addWidget(lbl_total_titulo)

        self.lbl_total = QLabel("$0")
        self.lbl_total.setFont(QFont("Arial", 44, QFont.Weight.Bold))
        self.lbl_total.setStyleSheet(f"color: {ACCENT_TOTAL}; letter-spacing: -1px; margin-top: -8px; margin-bottom: 8px;")
        self.lbl_total.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_total.setMinimumWidth(260)
        self.lbl_total.setWordWrap(False)
        total_layout.addWidget(self.lbl_total)

        sep0 = QFrame(); sep0.setFixedHeight(1)
        sep0.setStyleSheet(f"background: {BORDER}; border: none;")
        total_layout.addWidget(sep0)

        btn_cobrar = QPushButton("  💳  COBRAR")
        btn_cobrar.setFixedHeight(65)
        btn_cobrar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_cobrar.setStyleSheet(f"""
            QPushButton {{ background: {ACCENT_TOTAL}; color: {BG_MAIN}; border-radius: 12px; font-size: 20px; font-weight: bold; letter-spacing: 2px; border: none; }}
            QPushButton:hover {{ background: #45D4A0; }}
        """)
        btn_cobrar.clicked.connect(self.cobrar)
        total_layout.addWidget(btn_cobrar)

        fila_btns = QHBoxLayout()
        fila_btns.setSpacing(6)
        btn_repetir = QPushButton("↩ F4")
        btn_repetir.setFixedHeight(40)
        btn_repetir.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_repetir.setStyleSheet(f"QPushButton {{ background: {BG_MAIN}; color: {ACCENT_OFERTAS}; border-radius: 8px; font-size: 14px; font-weight: bold; border: 1px solid {ACCENT_OFERTAS}; }}")
        btn_repetir.clicked.connect(self.repetir_ultimo)
        fila_btns.addWidget(btn_repetir)

        btn_cancelar = QPushButton("✕")
        btn_cancelar.setFixedHeight(40)
        btn_cancelar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_cancelar.setStyleSheet(f"QPushButton {{ background: {BG_MAIN}; color: {TEXT_MUTED}; border-radius: 8px; font-size: 14px; font-weight: bold; border: 1px solid {BORDER}; }}")
        btn_cancelar.clicked.connect(self.cancelar_venta)
        fila_btns.addWidget(btn_cancelar)

        btn_informe = QPushButton("📋")
        btn_informe.setFixedSize(40, 40)
        btn_informe.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_informe.setStyleSheet(f"QPushButton {{ background: {BG_MAIN}; color: {ACCENT_BOTON}; border-radius: 8px; font-size: 16px; border: 1px solid {BORDER}; }}")
        btn_informe.clicked.connect(self.ver_informe)
        fila_btns.addWidget(btn_informe)
        total_layout.addLayout(fila_btns)

        sep1 = QFrame(); sep1.setFixedHeight(1)
        sep1.setStyleSheet(f"background: {BORDER}; border: none;")
        total_layout.addWidget(sep1)

        self.btn_cliente = QPushButton("👤  Vincular cliente")
        self.btn_cliente.setFixedHeight(40)
        self.btn_cliente.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_cliente.setStyleSheet(f"QPushButton {{ background: {BG_MAIN}; color: {ACCENT_BOTON}; border-radius: 8px; font-size: 14px; border: 1px solid {BORDER}; }}")
        self.btn_cliente.clicked.connect(self.buscar_cliente)
        total_layout.addWidget(self.btn_cliente)

        self.lbl_cliente_info = QLabel("")
        self.lbl_cliente_info.setStyleSheet(f"color: {ACCENT_OFERTAS}; font-size: 12px; padding: 2px 0;")
        self.lbl_cliente_info.setWordWrap(True)
        self.lbl_cliente_info.hide()
        total_layout.addWidget(self.lbl_cliente_info)

        panel_der.addWidget(total_frame)

        # ── Rotador de Ofertas (reemplaza el desglose) ──
        if OfertasRotator:
            self.rotador_ofertas = OfertasRotator()
            panel_der.addWidget(self.rotador_ofertas, 1)
        else:
            lbl_sin = QLabel("Ofertas no disponibles")
            lbl_sin.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
            panel_der.addWidget(lbl_sin)

        contenido.addLayout(panel_der, 1)
        layout.addLayout(contenido)

        QShortcut(QKeySequence("F2"), self).activated.connect(self.cobrar_sin_ticket)
        QShortcut(QKeySequence("F3"), self).activated.connect(self.verificar_precio)
        QShortcut(QKeySequence("F5"), self).activated.connect(self.pausar_venta_actual)
        QShortcut(QKeySequence("F6"), self).activated.connect(self.abrir_busqueda_avanzada)
        QShortcut(QKeySequence("F9"), self).activated.connect(self.cobrar)

        # ── Foco automático para lectora de barras ──
        # Cada 600ms verifica si el foco está en otro lado y lo devuelve
        # Solo actúa si no hay un dialog abierto y no se está editando nada
        self._timer_foco = QTimer()
        self._timer_foco.timeout.connect(self._restaurar_foco_lectora)
        self._timer_foco.start(1000)
        
        # BOTÓN PARA RECUPERAR TICKETS PAUSADOS
        self.btn_recuperar_pausa = QPushButton("⏳ Recuperar (0)")
        self.btn_recuperar_pausa.setFixedSize(120, 30)
        self.btn_recuperar_pausa.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_recuperar_pausa.setStyleSheet(f"background: #F59E0B; color: {BG_MAIN}; border-radius: 6px; font-weight: bold; font-size: 12px;")
        self.btn_recuperar_pausa.clicked.connect(self.ver_ventas_pausadas)
        self.btn_recuperar_pausa.hide()
        # Lo metemos en el layout donde está el botón de "Vincular cliente" (total_layout)
        # Se agregará al final del bloque __init__ de la UI
        total_layout.insertWidget(total_layout.count() - 1, self.btn_recuperar_pausa)
        
    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        if obj is self.input_buscar:
            if event.type() == QEvent.Type.FocusIn:
                self.timer_marquee.stop()
            elif event.type() == QEvent.Type.FocusOut:
                self.timer_marquee.start(60)
        return super().eventFilter(obj, event)

    def animar_marquee(self):
        self.offset_marquee -= 2
        ancho_texto = self.texto_ofertas.width()
        ancho_contenedor = self.contenedor_marquee.width()
        if self.offset_marquee < -ancho_texto: 
            self.offset_marquee = ancho_contenedor
        self.texto_ofertas.move(self.offset_marquee, 15) 

    def abrir_editor_ofertas(self):
        dialog = EditorOfertasDialog(self, self.texto_ofertas.text())
        if dialog.exec():
            nuevo_texto = dialog.txt.toPlainText().replace('\n', '   *** ')
            self.texto_ofertas.setText(nuevo_texto)
            self.texto_ofertas.adjustSize()
            self.offset_marquee = self.contenedor_marquee.width()

    def buscar_cliente(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("👤 Vincular cliente")
        dialog.setMinimumWidth(400)
        dialog.setStyleSheet(f"background-color: {BG_MAIN}; color: white;")
        lay = QVBoxLayout(dialog)
        lay.setSpacing(10)
        lbl = QLabel("Buscar cliente:")
        lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px;")
        lay.addWidget(lbl)
        input_b = QLineEdit()
        input_b.setPlaceholderText("Nombre o teléfono...")
        input_b.setFixedHeight(44)
        input_b.setStyleSheet(f"QLineEdit {{ background: {BG_PANEL}; border: 1px solid {ACCENT_BOTON}; border-radius: 8px; padding: 10px; color: white; font-size: 14px; }}")
        lay.addWidget(input_b)
        lista = QListWidget()
        lista.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        lista.setStyleSheet(f"QListWidget {{ background: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 8px; color: white; }} QListWidget::item {{ padding: 10px; }} QListWidget::item:hover {{ background: {BORDER}; }}")
        lista.setMinimumHeight(200)
        lay.addWidget(lista)
        clientes_encontrados = []
        def buscar():
            texto = input_b.text().strip()
            if not texto: return
            try:
                r = requests.get(f"{API_URL}/clientes/buscar", params={"q": texto}, timeout=5)
                if r.status_code == 200:
                    lista.clear()
                    clientes_encontrados.clear()
                    for c in r.json()[:10]:
                        puntos = float(c.get("puntos", 0))
                        deuda = float(c.get("deuda_actual", 0))
                        texto_item = c["nombre"]
                        if puntos > 0: texto_item += f"  ⭐ {puntos:.0f} pts"
                        if deuda > 0: texto_item += f"  💸 ${deuda:,.0f}"
                        item = QListWidgetItem(texto_item)
                        item.setData(Qt.ItemDataRole.UserRole, c)
                        lista.addItem(item)
                        clientes_encontrados.append(c)
            except Exception: pass
        input_b.returnPressed.connect(buscar)
        def seleccionar(item):
            c = item.data(Qt.ItemDataRole.UserRole)
            self.cliente_actual = c
            puntos = float(c.get("puntos", 0))
            texto = f"👤 {c['nombre']}"
            if puntos >= 100: texto += f"\n⭐ {puntos:.0f} pts (canjeables)"
            self.lbl_cliente_info.setText(texto)
            self.lbl_cliente_info.show()
            self.btn_cliente.setText(f"👤 {c['nombre'][:18]}")
            self.btn_cliente.setStyleSheet(f"QPushButton {{ background: {ACCENT_TOTAL}; color: {BG_MAIN}; border-radius: 8px; font-size: 11px; font-weight:bold; border: none; }}")
            dialog.accept()
        lista.itemDoubleClicked.connect(seleccionar)
        btns = QHBoxLayout()
        btn_sin = QPushButton("Sin cliente")
        btn_sin.setFixedHeight(38)
        btn_sin.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_sin.setStyleSheet(f"QPushButton {{ background: transparent; color: {TEXT_MUTED}; border: 1px solid {BORDER}; border-radius: 8px; }}")
        def desvincular():
            self.cliente_actual = None
            self.lbl_cliente_info.hide()
            self.btn_cliente.setText("👤 Vincular cliente")
            self.btn_cliente.setStyleSheet(f"QPushButton {{ background: {BG_MAIN}; color: {ACCENT_BOTON}; border-radius: 8px; font-size: 12px; border: 1px solid {BORDER}; }}")
            dialog.accept()
        btn_sin.clicked.connect(desvincular)
        btns.addWidget(btn_sin)
        btn_ok = QPushButton("Seleccionar")
        btn_ok.setFixedHeight(38)
        btn_ok.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_ok.setStyleSheet(f"QPushButton {{ background: {ACCENT_BOTON}; color: white; border-radius: 8px; font-size: 13px; font-weight: bold; }}")
        def sel_highlighted():
            items = lista.selectedItems()
            if items: seleccionar(items[0])
        btn_ok.clicked.connect(sel_highlighted)
        btns.addWidget(btn_ok)
        lay.addLayout(btns)
        input_b.setFocus()
        dialog.exec()
        self.input_buscar.setFocus()

    def repetir_ultimo(self):
        if self.ultimo_producto: self.agregar_item(self.ultimo_producto)
        else: QMessageBox.information(self, "Info", "No hay producto anterior para repetir")

    def verificar_precio(self):
        """F3 — Buscador de precios. Solo consulta, no agrega al ticket."""
        dialog = QDialog(self)
        dialog.setWindowTitle("🔎 F3 — Verificar precio")
        dialog.setMinimumWidth(480)
        dialog.setStyleSheet(f"background-color: {BG_MAIN}; color: {TEXT_MAIN};")
        lay = QVBoxLayout(dialog)
        lay.setSpacing(10)
        lay.setContentsMargins(16, 16, 16, 16)

        input_b = QLineEdit()
        input_b.setPlaceholderText("Nombre o código de barras...")
        input_b.setFixedHeight(48)
        input_b.setStyleSheet(f"QLineEdit {{ background: {BG_PANEL}; border: 2px solid #1abc9c; border-radius: 10px; padding: 10px; color: white; font-size: 16px; }}")
        lay.addWidget(input_b)

        resultado_frame = QFrame()
        resultado_frame.setStyleSheet(f"QFrame {{ background: {BG_PANEL}; border-radius: 12px; border: 1px solid {BORDER}; }}")
        resultado_frame.setMinimumHeight(120)
        res_lay = QVBoxLayout(resultado_frame)
        res_lay.setContentsMargins(16, 14, 16, 14)
        lbl_nombre = QLabel("—")
        lbl_nombre.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        lbl_nombre.setStyleSheet(f"color: {TEXT_MAIN};")
        lbl_precio = QLabel("")
        lbl_precio.setFont(QFont("Arial", 32, QFont.Weight.Bold))
        lbl_precio.setStyleSheet("color: #1abc9c;")
        lbl_stock  = QLabel("")
        lbl_stock.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px;")
        lbl_codigo = QLabel("")
        lbl_codigo.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        res_lay.addWidget(lbl_nombre)
        res_lay.addWidget(lbl_precio)
        res_lay.addWidget(lbl_stock)
        res_lay.addWidget(lbl_codigo)
        lay.addWidget(resultado_frame)

        def buscar():
            texto = input_b.text().strip()
            if not texto: return
            p = None
            if self.productos_cache:
                if texto in self.productos_codigo:
                    p = self.productos_codigo[texto]
                else:
                    matches = [x for x in self.productos_cache if texto.lower() in x["nombre"].lower()]
                    if matches: p = matches[0]
            if not p:
                try:
                    r = requests.get(f"{API_URL}/productos/buscar", params={"q": texto}, timeout=5)
                    if r.status_code == 200 and r.json():
                        p = r.json()[0]
                except Exception:
                    pass
            if p:
                stock = float(p.get("stock_actual", 0))
                lbl_nombre.setText(p["nombre"])
                lbl_precio.setText(f"${float(p['precio_venta']):,.2f}")
                color_stock = "#27ae60" if stock > 5 else ("#f39c12" if stock > 0 else "#e74c3c")
                lbl_stock.setText(f"Stock: {stock:g} unidades")
                lbl_stock.setStyleSheet(f"color: {color_stock}; font-size: 13px;")
                lbl_codigo.setText(f"Código: {p.get('codigo_barra') or 'sin código'}")
                resultado_frame.setStyleSheet(f"QFrame {{ background: {BG_PANEL}; border-radius: 12px; border: 1px solid #1abc9c; }}")
            else:
                lbl_nombre.setText("No encontrado")
                lbl_precio.setText("")
                lbl_stock.setText("")
                lbl_codigo.setText("")
                resultado_frame.setStyleSheet(f"QFrame {{ background: {BG_PANEL}; border-radius: 12px; border: 1px solid #e74c3c; }}")

        input_b.returnPressed.connect(buscar)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setFixedHeight(40)
        btn_cerrar.setStyleSheet(f"background: transparent; color: {TEXT_MUTED}; border: 1px solid {BORDER}; border-radius: 8px;")
        btn_cerrar.clicked.connect(dialog.accept)
        lay.addWidget(btn_cerrar)

        input_b.setFocus()
        dialog.exec()
        self.input_buscar.setFocus()

    def actualizar_subtotales_depto(self):
        while self.depto_layout.count():
            child = self.depto_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        subtotales = {}
        for item in self.items_venta:
            nombre = item["nombre"]
            depto_key = "Productos"
            depto_color = ACCENT_BOTON
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
            lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; padding: 8px;")
            self.depto_layout.addWidget(lbl)
            return
        for depto_nombre, data in subtotales.items():
            card = QFrame()
            card.setStyleSheet(f"QFrame {{ background: {BG_PANEL}; border-radius: 8px; border-left: 3px solid {data['color']}; }}")
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

    def _parsear_codigo_balanza(self, texto):
        """
        Balanza Coura — formato EAN-13 con precio embebido.
        Estructura: 2 + 5 dígitos PLU + 5 dígitos precio (sin decimales) + 1 verificador
        Ejemplo: 2201000235135 → precio = $23.513
        """
        texto = texto.strip()
        if len(texto) != 13:
            return None
        if not texto.startswith("2"):
            return None
        if not texto.isdigit():
            return None
        try:
            precio_str = texto[7:12]   # posiciones 7-11 (precio embebido en EAN-13 de balanza)
            precio     = int(precio_str)
            if precio <= 0:
                return None
            return precio
        except Exception:
            return None

    def buscar_producto(self):
        texto = self.input_buscar.text().strip()
        if not texto:
            return

        # ── Balanza Coura — precio embebido en código ────────────────────────
        precio_balanza = self._parsear_codigo_balanza(texto)
        if precio_balanza:
            self.input_buscar.clear()
            self.items_venta.append({
                "producto_id":     0,
                "nombre":          "Carnicería (balanza)",
                "precio_unitario": precio_balanza,
                "cantidad":        1,
                "subtotal":        precio_balanza,
                "descuento":       0,
            })
            self.actualizar_tabla()
            return

        # Código de departamento especial
        if texto in DEPARTAMENTOS:
            depto = DEPARTAMENTOS[texto]
            self.input_buscar.clear()
            self.abrir_ingreso_departamento(depto)
            return

        # 1. Buscar en cache local — sin red, instantáneo
        if self.productos_cache:
            # Coincidencia exacta por código de barras primero
            if texto in self.productos_codigo:
                self.agregar_item(self.productos_codigo[texto])
                self.input_buscar.clear()
                return

            # Búsqueda por nombre (contiene, sin distinción de mayúsculas)
            texto_lower = texto.lower()
            resultados = [
                p for p in self.productos_cache
                if texto_lower in p["nombre"].lower()
                and p.get("activo", True)
            ]

            if not resultados:
                QMessageBox.warning(self, "No encontrado", f"No se encontró: {texto}")
                return

            if len(resultados) == 1:
                self.agregar_item(resultados[0])
                self.input_buscar.clear()
                return

            # Múltiples resultados — selector rápido
            self._mostrar_selector_rapido(resultados)
            return

        # 2. Fallback a API si el cache todavía no cargó
        try:
            r = requests.get(f"{API_URL}/productos/buscar", params={"q": texto}, timeout=5)
            if r.status_code == 200:
                productos = r.json()
                if not productos:
                    QMessageBox.warning(self, "No encontrado", f"No se encontró: {texto}")
                    return
                self.agregar_item(productos[0])
                self.input_buscar.clear()
        except Exception:
            QMessageBox.critical(self, "Error", "No se puede conectar al servidor")

    def _mostrar_selector_rapido(self, productos):
        """Muestra lista rápida cuando hay múltiples coincidencias de nombre."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Seleccionar producto")
        dialog.setMinimumWidth(500)
        dialog.setStyleSheet(f"background-color: {BG_MAIN}; color: {TEXT_MAIN};")
        lay = QVBoxLayout(dialog)
        lay.setSpacing(8)
        lay.setContentsMargins(12, 12, 12, 12)

        lista = QListWidget()
        lista.setStyleSheet(f"""
            QListWidget {{ background: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 8px; font-size: 15px; }}
            QListWidget::item {{ color: {TEXT_MAIN}; padding: 10px; border-bottom: 1px solid {BORDER}; }}
            QListWidget::item:selected {{ background: {ACCENT_BOTON}; }}
        """)
        for p in productos[:20]:
            texto_item = f"{p['nombre']}   {_p(p.get('precio_venta') or 0)}"
            item = QListWidgetItem(texto_item)
            item.setData(Qt.ItemDataRole.UserRole, p)
            lista.addItem(item)
        lay.addWidget(lista)

        seleccionado = [False]  # flag para evitar doble ejecución

        def seleccionar(item=None):
            if seleccionado[0]:
                return
            if item is None:
                item = lista.currentItem()
            if item is None:
                return
            seleccionado[0] = True
            p = item.data(Qt.ItemDataRole.UserRole)
            self.agregar_item(p)
            self.input_buscar.clear()
            dialog.accept()

        lista.itemDoubleClicked.connect(seleccionar)
        lista.itemActivated.connect(seleccionar)

        btn = QPushButton("✅ Agregar seleccionado")
        btn.setFixedHeight(40)
        btn.setStyleSheet(f"background: {ACCENT_BOTON}; color: white; border-radius: 8px; font-weight: bold;")
        btn.clicked.connect(lambda: seleccionar())
        lay.addWidget(btn)

        lista.setCurrentRow(0)
        lista.setFocus()
        dialog.exec()
        self.input_buscar.clear()
        self.input_buscar.setFocus()

    def abrir_ingreso_departamento(self, depto):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{depto['icono']} {depto['nombre']}")
        dialog.setMinimumWidth(340)
        dialog.setStyleSheet(f"background-color: {BG_MAIN}; color: white;")
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
        lista_frame.setStyleSheet(f"QFrame {{ background: {BG_PANEL}; border-radius: 8px; border: 1px solid {depto['color']}; }}")
        lista_layout = QVBoxLayout(lista_frame)
        lista_layout.setContentsMargins(10, 8, 10, 8)
        lista_layout.setSpacing(4)
        lbl_montos = QLabel("- Sin ítems aún -")
        lbl_montos.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
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
                lbl_montos.setText("- Sin ítems aún -")
                lbl_montos.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
                lbl_total_depto.setText("Total: $0.00")
                return
            texto = "  +  ".join([f"${m:.2f}" for m in montos_temp])
            lbl_montos.setText(texto)
            lbl_montos.setStyleSheet("color: white; font-size: 13px;")
            lbl_total_depto.setText(f"Total: ${sum(montos_temp):.2f}")

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

        def agregar_monto():
            texto_input = input_monto.text().strip()
            
            # --- ACÁ ESTÁ LA MAGIA DEL DOBLE ENTER ---
            if not texto_input:
                if montos_temp:  # Si ya hay montos cargados y apretás Enter de nuevo, baja al ticket
                    confirmar()
                return
            # -----------------------------------------
            
            try: monto = float(texto_input.replace(",", "."))
            except ValueError:
                QMessageBox.warning(dialog, "Error", "Ingresá un monto válido")
                return
            if monto <= 0: return
            montos_temp.append(monto)
            input_monto.clear()
            input_monto.setFocus()
            actualizar_lista()

        def borrar_ultimo():
            if montos_temp:
                montos_temp.pop()
                actualizar_lista()

        input_monto = MontoDeptoInput(agregar_monto)
        input_monto.setPlaceholderText("Monto y Enter (DOBLE ENTER finaliza)")
        input_monto.setFixedHeight(44)
        input_monto.setAlignment(Qt.AlignmentFlag.AlignRight)
        input_monto.setStyleSheet(f"QLineEdit {{ background: {BG_MAIN}; border: 2px solid {depto['color']}; border-radius: 8px; padding: 0 16px; color: white; font-size: 20px; font-weight: bold; }}")
        input_frame = QFrame()
        input_frame.setStyleSheet(f"QFrame {{ background: {BG_PANEL}; border-radius: 8px; }}")
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
        btn_borrar = QPushButton("<- Borrar último")
        btn_borrar.setFixedHeight(34)
        btn_borrar.setStyleSheet(f"QPushButton {{ background: transparent; color: {TEXT_MUTED}; border: 1px solid {TEXT_MUTED}; border-radius: 6px; font-size: 12px; }}")
        btn_borrar.clicked.connect(borrar_ultimo)
        layout.addWidget(btn_borrar)
        btns = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setFixedHeight(44)
        btn_cancelar.setStyleSheet(f"QPushButton {{ background: transparent; color: {TEXT_MUTED}; border: 1px solid {BORDER}; border-radius: 8px; }}")
        btn_cancelar.clicked.connect(dialog.reject)
        btns.addWidget(btn_cancelar)
        btn_confirmar = QPushButton("Agregar al ticket")
        btn_confirmar.setFixedHeight(44)
        btn_confirmar.setStyleSheet(f"QPushButton {{ background: {depto['color']}; color: white; border-radius: 8px; font-size: 14px; font-weight: bold; }}")
        btns.addWidget(btn_confirmar)
        layout.addLayout(btns)

        btn_confirmar.clicked.connect(confirmar)
        input_monto.setFocus()
        dialog.exec()
        self.input_buscar.clear()
        self.input_buscar.setFocus()

    def agregar_manual(self):
        nombre = self.input_manual_nombre.text().strip()
        try:
            precio = float(self.input_manual_precio.text())
            cantidad = float(self.input_manual_cant.text() or 1)
        except ValueError:
            QMessageBox.warning(self, "Error", "Precio y cantidad deben ser numeros")
            return
        if not nombre or precio <= 0: return
        self.items_venta.append({
            "producto_id": 0, "nombre": f"[M] {nombre}",
            "precio_unitario": precio, "cantidad": cantidad,
            "subtotal": precio * cantidad, "descuento": 0
        })
        self.actualizar_tabla()
        self.input_manual_nombre.clear(); self.input_manual_precio.clear(); self.input_manual_cant.setText("1")
        self.input_manual_nombre.setFocus()

    def agregar_item(self, producto):
        self.ultimo_producto = producto
        for item in self.items_venta:
            if item["producto_id"] == producto["id"]:
                item["cantidad"] += 1
                item["subtotal"] = item["cantidad"] * item["precio_unitario"]
                self.actualizar_tabla()
                QTimer.singleShot(30, self.input_buscar.setFocus)
                return
        self.items_venta.append({
            "producto_id": producto["id"], "nombre": producto["nombre"],
            "precio_unitario": float(producto.get("precio_venta") or 0), "cantidad": 1,
            "subtotal": float(producto.get("precio_venta") or 0), "descuento": 0
        })
        self.actualizar_tabla()
        QTimer.singleShot(30, self.input_buscar.setFocus)

    def editar_item_doble_clic(self, row, col):
        if row >= len(self.items_venta): return
        item = self.items_venta[row]
        precio_original = item["precio_unitario"]
        dialog = EditarItemDialog(self, item)
        if dialog.exec():
            if dialog.nuevo_precio != precio_original:
                self.log_modificaciones.append({
                    "producto": item["nombre"], "precio_original": precio_original,
                    "precio_nuevo": dialog.nuevo_precio, "hora": datetime.now().strftime("%H:%M:%S"), "ticket": "-"
                })
                _guardar_evento({"tipo": "modificacion", "producto": item["nombre"],
                    "precio_original": precio_original, "precio_nuevo": dialog.nuevo_precio})
            item["precio_unitario"] = dialog.nuevo_precio
            item["cantidad"] = dialog.nueva_cantidad
            item["subtotal"] = dialog.nuevo_precio * dialog.nueva_cantidad
            self.actualizar_tabla()

    def cambiar_cantidad(self, idx, delta):
        if idx >= len(self.items_venta): return
        item = self.items_venta[idx]
        nueva_cantidad = item["cantidad"] + delta
        if nueva_cantidad <= 0:
            self.log_eliminados.append({
                "producto": item["nombre"], "cantidad": item["cantidad"], "precio": item["precio_unitario"],
                "hora": datetime.now().strftime("%H:%M:%S"), "motivo": "Cantidad reducida a 0", "venta_cerrada": False, "ticket": "-"
            })
            _guardar_evento({"tipo": "eliminado", "producto": item["nombre"],
                "cantidad": item["cantidad"], "precio": item["precio_unitario"], "motivo": "Cantidad reducida a 0"})
            self.items_venta.pop(idx)
        else:
            item["cantidad"] = nueva_cantidad
            item["subtotal"] = nueva_cantidad * item["precio_unitario"]
        self.actualizar_tabla()

    def actualizar_tabla(self):
        self.tabla.setUpdatesEnabled(False)
        n = len(self.items_venta)
        self.tabla.setRowCount(n)
        total = 0
        for i, item in enumerate(self.items_venta):
            # Actualizar textos siempre
            nombre_item = QTableWidgetItem(item["nombre"])
            if item["producto_id"] == 0:
                nombre_item.setForeground(Qt.GlobalColor.green)
            self.tabla.setItem(i, 0, nombre_item)
            self.tabla.setItem(i, 1, QTableWidgetItem(_p(item['precio_unitario'])))
            self.tabla.setItem(i, 2, QTableWidgetItem(str(item["cantidad"])))
            self.tabla.setItem(i, 3, QTableWidgetItem(_p(item['subtotal'])))

            # Crear botones solo si la celda está vacía (fila nueva)
            if self.tabla.cellWidget(i, 4) is None:
                btn_widget = QWidget()
                btn_layout = QHBoxLayout(btn_widget)
                btn_layout.setContentsMargins(5, 5, 5, 5)
                btn_layout.setSpacing(5)
                btn_menos = QPushButton("-")
                btn_menos.setFixedSize(36, 36)
                btn_menos.setStyleSheet(f"QPushButton {{ background: {BG_MAIN}; color: {TEXT_MAIN}; border-radius: 6px; font-size: 20px; font-weight: bold; border: 1px solid {BORDER}; }} QPushButton:hover {{ background: #F46A6A; border: none; }}")
                btn_menos.clicked.connect(lambda _, idx=i: self.cambiar_cantidad(idx, -1))
                btn_layout.addWidget(btn_menos)
                btn_mas = QPushButton("+")
                btn_mas.setFixedSize(36, 36)
                btn_mas.setStyleSheet(f"QPushButton {{ background: {BG_MAIN}; color: {TEXT_MAIN}; border-radius: 6px; font-size: 20px; font-weight: bold; border: 1px solid {BORDER}; }} QPushButton:hover {{ background: {ACCENT_TOTAL}; border: none; }}")
                btn_mas.clicked.connect(lambda _, idx=i: self.cambiar_cantidad(idx, 1))
                btn_layout.addWidget(btn_mas)
                self.tabla.setCellWidget(i, 4, btn_widget)
                btn_del = QPushButton("X")
                btn_del.setFixedSize(36, 36)
                btn_del.setStyleSheet(f"QPushButton {{ color: #F46A6A; background: transparent; font-size: 20px; font-weight: bold; }}")
                btn_del.clicked.connect(lambda _, idx=i: self.eliminar_item(idx))
                self.tabla.setCellWidget(i, 5, btn_del)

            total += item["subtotal"]

        self.tabla.setUpdatesEnabled(True)
        self.lbl_total.setText(_p(total))

    def eliminar_item(self, idx):
        if idx >= len(self.items_venta): return
        item = self.items_venta[idx]
        self.log_eliminados.append({
            "producto": item["nombre"], "cantidad": item["cantidad"], "precio": item["precio_unitario"],
            "hora": datetime.now().strftime("%H:%M:%S"), "motivo": "Eliminado con X", "venta_cerrada": False, "ticket": "-"
        })
        _guardar_evento({"tipo": "eliminado", "producto": item["nombre"],
            "cantidad": item["cantidad"], "precio": item["precio_unitario"], "motivo": "Eliminado con X"})
        self.items_venta.pop(idx)
        self.actualizar_tabla()
        self.input_buscar.setFocus()

    def guardar_informe(self, ticket, descuento_pct, total_original, total_final, metodo_pago, vuelto=0):
        try:
            carpeta = os.path.join(os.path.expanduser("~"), "JuanaCash_Tickets")
            os.makedirs(carpeta, exist_ok=True)
            fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
            ruta = os.path.join(carpeta, f"informe_{fecha}.txt")
            with open(ruta, "w", encoding="utf-8") as f:
                f.write("=" * 40 + "\n")
                f.write("JUANA CASH - INFORME DE VENTA\n")
                f.write("=" * 40 + "\n")
                f.write(f"Ticket: {ticket}\n")
                f.write(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write(f"Cajero: {self.usuario['nombre'] if self.usuario else 'N/A'}\n")
                f.write(f"Pago: {metodo_pago}\n")
                f.write("-" * 40 + "\n")
                if descuento_pct > 0:
                    f.write(f"DESCUENTO: {descuento_pct:.1f}%\n")
                    f.write(f"Total original: ${total_original:.2f}\n")
                    f.write(f"Total final: ${total_final:.2f}\n")
                else:
                    f.write(f"Total: ${total_final:.2f}\n")
                if metodo_pago == "efectivo" and vuelto > 0:
                    f.write(f"Vuelto: ${vuelto:.2f}\n")
                f.write("=" * 40 + "\n")
        except Exception as e: print(f"Error: {e}")

    def ver_informe(self):
        registros = _leer_auditoria()
        if not registros and not self.log_eliminados and not self.log_modificaciones:
            QMessageBox.information(self, "Informe", "No hay eventos registrados.\n\nAcá se muestran artículos borrados\ny modificaciones de precio.")
            self.input_buscar.setFocus()
            return

        lineas = []
        lineas.append("=" * 60)
        lineas.append("📋 HISTORIAL DE AUDITORÍA")
        lineas.append("=" * 60)

        # Agrupar por fecha
        por_fecha = {}
        for r in registros:
            fecha = r.get("fecha", "Sin fecha")
            if fecha not in por_fecha:
                por_fecha[fecha] = []
            por_fecha[fecha].append(r)

        # Mostrar últimas 10 fechas (más reciente primero)
        fechas = sorted(por_fecha.keys(), reverse=True)[:10]
        for fecha in fechas:
            eventos = por_fecha[fecha]
            eliminados = [e for e in eventos if e.get("tipo") == "eliminado"]
            modificaciones = [e for e in eventos if e.get("tipo") == "modificacion"]

            lineas.append(f"\n📅 {fecha}")
            lineas.append("-" * 50)

            if eliminados:
                lineas.append(f"  🗑 Productos eliminados: {len(eliminados)}")
                for e in eliminados:
                    lineas.append(f"    {e.get('hora','')}  {e.get('producto','')}  x{e.get('cantidad','')}  ${float(e.get('precio',0)):,.2f}  [{e.get('motivo','')}]")

            if modificaciones:
                lineas.append(f"  ✏️ Precios modificados: {len(modificaciones)}")
                for e in modificaciones:
                    lineas.append(f"    {e.get('hora','')}  {e.get('producto','')}  ${float(e.get('precio_original',0)):,.2f} → ${float(e.get('precio_nuevo',0)):,.2f}")

            if not eliminados and not modificaciones:
                lineas.append("  Sin movimientos")

        lineas.append("\n" + "=" * 60)
        lineas.append(f"Total registros: {len(registros)}")
        lineas.append("=" * 60)

        texto = "\n".join(lineas)
        dialog = QDialog(self)
        dialog.setWindowTitle("📋 Historial de auditoría")
        dialog.resize(750, 550)
        dialog.setStyleSheet(f"background-color: {BG_MAIN}; color: {TEXT_MAIN};")
        layout = QVBoxLayout(dialog)
        txt = QTextEdit()
        txt.setReadOnly(True)
        txt.setPlainText(texto)
        txt.setFont(QFont("Courier New", 10))
        txt.setStyleSheet(f"background: {BG_PANEL}; color: {TEXT_MAIN}; border: 1px solid {BORDER}; border-radius: 8px; padding: 10px;")
        layout.addWidget(txt)
        btn = QPushButton("Cerrar")
        btn.setFixedHeight(36)
        btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn.setStyleSheet(f"background: {ACCENT_BOTON}; color: white; border-radius: 8px;")
        btn.clicked.connect(dialog.accept)
        layout.addWidget(btn)
        dialog.exec()
        self.input_buscar.setFocus()

    def cobrar_sin_ticket(self):
        """F2 — Cobra la venta actual sin imprimir ticket."""
        if not self.items_venta:
            QMessageBox.warning(self, "Sin productos", "Agrega productos antes de cobrar")
            return
        total_original = sum(i["subtotal"] for i in self.items_venta)
        dialog = CobrarDialog(self, total_original, cliente=self.cliente_actual)
        if not dialog.exec(): return
        descuento_pct     = dialog.descuento_pct
        total_final       = dialog.total_final
        metodo_pago       = dialog.metodo_pago
        metodo_secundario = dialog.metodo_secundario
        monto_secundario  = dialog.monto_secundario
        recargo_monto     = dialog.recargo_monto
        recargo_pct       = dialog.recargo_pct
        descuento_monto   = max(0, total_original - (total_final - recargo_monto))
        vuelto = 0
        try:
            entrega = float(dialog.input_entrega.text().replace(",", "."))
            if metodo_pago == "efectivo":
                vuelto = max(0, entrega - (total_final - monto_secundario))
            elif metodo_secundario == "efectivo":
                vuelto = max(0, entrega - monto_secundario)
        except (ValueError, TypeError):
            pass
        # Incluir TODOS los items — balanza/depto (pid=0) como genérico (pid=1)
        # Si se filtraban, venta.total quedaba menor que lo cobrado (el bug)
        items_backend = []
        for _i in self.items_venta:
            if _i["producto_id"] != 0:
                items_backend.append(_i)
            else:
                items_backend.append({"producto_id": 1, "cantidad": 1,
                                       "precio_unitario": _i["subtotal"], "descuento": 0})
        if not items_backend:
            # Solo ocurre si el carrito estaba vacío (imposible, hay guard arriba)
            items_backend = [{"producto_id": 1, "cantidad": 1,
                               "precio_unitario": total_final - recargo_monto, "descuento": 0}]
        pagos = [{"metodo": metodo_pago, "monto": total_final - monto_secundario}]
        if metodo_secundario and monto_secundario > 0:
            pagos.append({"metodo": metodo_secundario, "monto": monto_secundario})
        cliente_id = self.cliente_actual["id"] if self.cliente_actual else None
        try:
            r = requests.post(f"{API_URL}/ventas/", json={
                "usuario_id": self.usuario.get("id", 1) if self.usuario else 1,
                "cliente_id": cliente_id,
                "items": items_backend,
                "pagos": pagos,
                "descuento": descuento_monto,
                "recargo": recargo_monto
            }, timeout=5)
            if r.status_code == 200:
                datos = r.json()
                ticket = datos["numero"]
                nombres_metodo = {"efectivo": "Efectivo", "tarjeta": "Tarjeta crédito", "mercadopago_qr": "QR/MP", "transferencia": "Transf."}
                metodo_str = nombres_metodo.get(metodo_pago, metodo_pago)
                if recargo_monto > 0:
                    metodo_str += f" (+{recargo_pct:.0f}% recargo)"
                if metodo_secundario:
                    metodo_str += f" + {nombres_metodo.get(metodo_secundario, metodo_secundario)} (${monto_secundario:.2f})"
                self.log_ventas.append({"ticket": ticket, "total_original": total_original, "descuento_pct": descuento_pct, "total_final": total_final, "metodo_pago": metodo_str, "vuelto": vuelto, "hora": datetime.now().strftime("%H:%M:%S")})
                for log in self.log_eliminados:
                    if not log["venta_cerrada"]:
                        log["venta_cerrada"] = True; log["ticket"] = ticket
                for m in self.log_modificaciones:
                    if m["ticket"] == "-": m["ticket"] = ticket
                if self.cliente_actual:
                    cid = self.cliente_actual["id"]
                    if dialog.descuento_puntos > 0:
                        try: requests.post(f"{API_URL}/clientes/{cid}/canjear-puntos", timeout=3)
                        except Exception: pass
                    try: requests.post(f"{API_URL}/clientes/{cid}/sumar-puntos", params={"monto": total_final}, timeout=3)
                    except Exception: pass
                if hasattr(dialog, 'cupon_aplicado') and dialog.cupon_aplicado:
                    try:
                        requests.post(
                            f"{API_URL}/cupones/usar/{dialog.cupon_aplicado}",
                            json={"venta_id": datos.get("id")},
                            timeout=3
                        )
                    except Exception:
                        pass
                self.guardar_informe(ticket, descuento_pct, total_original, total_final, metodo_str, vuelto)
                msg = f"✅ Ticket #{ticket} — ${total_final:,.0f} ({metodo_str})"
                if metodo_pago == "efectivo" and vuelto > 0:
                    msg += f" — Vuelto: ${vuelto:,.0f}"
                self.lbl_total.setText(msg)
                self.lbl_total.setStyleSheet(f"color: #27ae60; font-size: 28px; font-weight: bold;")
                self.cancelar_venta()
                QTimer.singleShot(3000, lambda: self.lbl_total.setStyleSheet(f"color: {ACCENT_TOTAL}; letter-spacing: -1px;"))
            else: QMessageBox.critical(self, "Error", "No se pudo registrar la venta")
        except Exception as e: QMessageBox.critical(self, "Error", f"No se puede conectar al servidor\n{str(e)}")

    def cobrar(self):
        if not self.items_venta:
            QMessageBox.warning(self, "Sin productos", "Agrega productos antes de cobrar")
            return
        total_original = sum(i["subtotal"] for i in self.items_venta)
        dialog = CobrarDialog(self, total_original, cliente=self.cliente_actual)
        if not dialog.exec(): return
        descuento_pct    = dialog.descuento_pct
        total_final      = dialog.total_final
        metodo_pago      = dialog.metodo_pago
        metodo_secundario = dialog.metodo_secundario
        monto_secundario = dialog.monto_secundario
        recargo_monto    = dialog.recargo_monto
        recargo_pct      = dialog.recargo_pct
        # descuento_monto excluye el recargo (solo descuentos reales)
        descuento_monto = max(0, total_original - (total_final - recargo_monto))
        vuelto = 0
        try:
            entrega = float(dialog.input_entrega.text().replace(",", "."))
            if metodo_pago == "efectivo":
                vuelto = max(0, entrega - (total_final - monto_secundario))
            elif metodo_secundario == "efectivo":
                vuelto = max(0, entrega - monto_secundario)
        except (ValueError, TypeError):
            pass
        # Incluir TODOS los items — balanza/depto (pid=0) como genérico (pid=1)
        # Si se filtraban, venta.total quedaba menor que lo cobrado (el bug)
        items_backend = []
        for _i in self.items_venta:
            if _i["producto_id"] != 0:
                items_backend.append(_i)
            else:
                items_backend.append({"producto_id": 1, "cantidad": 1,
                                       "precio_unitario": _i["subtotal"], "descuento": 0})
        if not items_backend:
            # Solo ocurre si el carrito estaba vacío (imposible, hay guard arriba)
            items_backend = [{"producto_id": 1, "cantidad": 1,
                               "precio_unitario": total_final - recargo_monto, "descuento": 0}]
        pagos = [{"metodo": metodo_pago, "monto": total_final - monto_secundario}]
        if metodo_secundario and monto_secundario > 0:
            pagos.append({"metodo": metodo_secundario, "monto": monto_secundario})
        cliente_id = self.cliente_actual["id"] if self.cliente_actual else None
        try:
            r = requests.post(f"{API_URL}/ventas/", json={
                "usuario_id": self.usuario.get("id", 1) if self.usuario else 1,
                "cliente_id": cliente_id,
                "items": items_backend,
                "pagos": pagos,
                "descuento": descuento_monto,
                "recargo": recargo_monto
            }, timeout=5)
            if r.status_code == 200:
                datos = r.json()
                ticket = datos["numero"]
                nombres_metodo = {"efectivo": "Efectivo", "tarjeta": "Tarjeta crédito", "mercadopago_qr": "QR/MP", "transferencia": "Transf."}
                metodo_str = nombres_metodo.get(metodo_pago, metodo_pago)
                if recargo_monto > 0:
                    metodo_str += f" (+{recargo_pct:.0f}% recargo)"
                if metodo_secundario:
                    metodo_str += f" + {nombres_metodo.get(metodo_secundario, metodo_secundario)} (${monto_secundario:.2f})"
                self.log_ventas.append({ "ticket": ticket, "total_original": total_original, "descuento_pct": descuento_pct, "total_final": total_final, "metodo_pago": metodo_str, "vuelto": vuelto, "hora": datetime.now().strftime("%H:%M:%S") })
                for log in self.log_eliminados:
                    if not log["venta_cerrada"]:
                        log["venta_cerrada"] = True; log["ticket"] = ticket
                for m in self.log_modificaciones:
                    if m["ticket"] == "-": m["ticket"] = ticket
                if self.cliente_actual:
                    cid = self.cliente_actual["id"]
                    if dialog.descuento_puntos > 0:
                        try: requests.post(f"{API_URL}/clientes/{cid}/canjear-puntos", timeout=3)
                        except Exception: pass
                    try: requests.post(f"{API_URL}/clientes/{cid}/sumar-puntos", params={"monto": total_final}, timeout=3)
                    except Exception: pass
                self.guardar_informe(ticket, descuento_pct, total_original, total_final, metodo_str, vuelto)
                msg = f"Ticket: {ticket}\nTotal: ${total_final:,.0f}\nPago: {metodo_str}"
                if recargo_monto > 0: msg += f"\nRecargo crédito: ${recargo_monto:,.0f}"
                if descuento_pct > 0: msg += f"\nDescuento: {descuento_pct:.1f}%"
                if metodo_pago == "efectivo" and vuelto > 0: msg += f"\nVuelto: ${vuelto:,.0f}"
                cliente_nombre = self.cliente_actual.get("nombre") if self.cliente_actual else None
                try:
                    from ui.pantallas.impresora import imprimir_ticket
                    ok, txt = imprimir_ticket(
                        {"numero": ticket, "total": total_final},
                        self.items_venta,
                        metodo_pago=metodo_pago,
                        descuento=descuento_monto,
                        vuelto=vuelto,
                        cliente=cliente_nombre,
                        recargo=recargo_monto,
                        recargo_pct=recargo_pct,
                    )
                    if ok:
                        QMessageBox.information(self, "✅ Venta registrada", msg)
                    else:
                        QMessageBox.warning(self, "✅ Venta registrada  ⚠️ Sin impresión",
                            msg + f"\n\n⚠️ {txt}")
                except Exception as ex:
                    QMessageBox.warning(self, "✅ Venta registrada  ⚠️ Sin impresión",
                        msg + f"\n\n⚠️ Error impresora: {ex}")
                self.cancelar_venta()
                if hasattr(dialog, 'cupon_aplicado') and dialog.cupon_aplicado:
                    try:
                        requests.post(
                            f"{API_URL}/cupones/usar/{dialog.cupon_aplicado}",
                            json={"venta_id": datos.get('id')},
                            timeout=3
                        )
                    except Exception:
                        pass
            else: QMessageBox.critical(self, "Error", "No se pudo registrar la venta")
        except Exception as e: QMessageBox.critical(self, "Error", f"No se puede conectar al servidor\n{str(e)}")

    def abrir_busqueda_avanzada(self):
        """F6 — Buscador de artículos. Enter agrega directo al ticket."""
        dialog = QDialog(self)
        dialog.setWindowTitle("🛒 F6 — Buscar y agregar")
        dialog.setMinimumSize(560, 460)
        dialog.setStyleSheet(f"background-color: {BG_MAIN}; color: {TEXT_MAIN};")
        lay = QVBoxLayout(dialog)
        lay.setSpacing(8)
        lay.setContentsMargins(14, 14, 14, 14)

        input_b = QLineEdit()
        input_b.setPlaceholderText("Nombre o código → Enter busca → Enter de nuevo agrega")
        input_b.setFixedHeight(48)
        input_b.setStyleSheet(f"QLineEdit {{ background: {BG_PANEL}; border: 2px solid {ACCENT_BOTON}; border-radius: 10px; padding: 10px; color: white; font-size: 15px; }}")
        lay.addWidget(input_b)

        tabla_b = QTableWidget(0, 4)
        tabla_b.setHorizontalHeaderLabels(["Código", "Nombre", "Precio", "Stock"])
        tabla_b.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        tabla_b.setColumnWidth(0, 100)
        tabla_b.setColumnWidth(2, 100)
        tabla_b.setColumnWidth(3, 70)
        tabla_b.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tabla_b.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        tabla_b.verticalHeader().setDefaultSectionSize(44)
        tabla_b.setStyleSheet(f"""
            QTableWidget {{ background: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 10px; font-size: 14px; }}
            QHeaderView::section {{ background: {BG_MAIN}; color: {TEXT_MUTED}; padding: 8px; border: none; font-size: 12px; }}
            QTableWidget::item {{ color: {TEXT_MAIN}; padding: 6px; border-bottom: 1px solid {BORDER}; }}
            QTableWidget::item:selected {{ background: {ACCENT_BOTON}; }}
        """)
        lay.addWidget(tabla_b)

        lbl_hint = QLabel("↵ Enter en el buscador busca  ·  ↵ Enter en la tabla agrega al ticket")
        lbl_hint.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        lay.addWidget(lbl_hint)

        productos_encontrados = []

        def poblar_tabla(productos):
            productos_encontrados.clear()
            productos_encontrados.extend(productos[:30])
            tabla_b.setRowCount(len(productos_encontrados))
            for i, p in enumerate(productos_encontrados):
                tabla_b.setItem(i, 0, QTableWidgetItem(p.get("codigo_barra") or ""))
                tabla_b.setItem(i, 1, QTableWidgetItem(p["nombre"]))
                tabla_b.setItem(i, 2, QTableWidgetItem(_p(p['precio_venta'])))
                stock = float(p.get("stock_actual", 0))
                item_s = QTableWidgetItem(f"{stock:g}")
                if stock <= 0:
                    item_s.setForeground(Qt.GlobalColor.red)
                elif stock <= float(p.get("stock_minimo", 0)):
                    item_s.setForeground(Qt.GlobalColor.yellow)
                tabla_b.setItem(i, 3, item_s)
            if productos_encontrados:
                tabla_b.setCurrentRow(0)

        def buscar():
            texto = input_b.text().strip()
            if not texto: return
            if self.productos_cache:
                if texto in self.productos_codigo:
                    # Coincidencia exacta de código → agrega de una
                    self.agregar_item(self.productos_codigo[texto])
                    input_b.clear()
                    dialog.accept()
                    return
                texto_lower = texto.lower()
                resultados = [p for p in self.productos_cache
                              if texto_lower in p["nombre"].lower() and p.get("activo", True)]
            else:
                try:
                    r = requests.get(f"{API_URL}/productos/buscar", params={"q": texto}, timeout=5)
                    resultados = r.json() if r.status_code == 200 else []
                except Exception:
                    resultados = []

            if len(resultados) == 1:
                # Un solo resultado → agrega directo
                self.agregar_item(resultados[0])
                input_b.clear()
                dialog.accept()
                return

            poblar_tabla(resultados)
            if resultados:
                tabla_b.setFocus()  # Mover foco a tabla para poder navegar con teclado

        def agregar_fila(row=None):
            if row is None:
                row = tabla_b.currentRow()
            if 0 <= row < len(productos_encontrados):
                self.agregar_item(productos_encontrados[row])
                input_b.clear()
                tabla_b.setRowCount(0)
                productos_encontrados.clear()
                input_b.setFocus()

        def tabla_key_enter():
            agregar_fila()

        input_b.returnPressed.connect(buscar)
        tabla_b.cellDoubleClicked.connect(lambda row, _: agregar_fila(row))
        tabla_b.itemActivated.connect(lambda item: agregar_fila(tabla_b.row(item)))

        btn_row = QHBoxLayout()
        btn_c = QPushButton("Cerrar")
        btn_c.setFixedHeight(40)
        btn_c.setStyleSheet(f"background: transparent; color: {TEXT_MUTED}; border: 1px solid {BORDER}; border-radius: 8px;")
        btn_c.clicked.connect(dialog.reject)
        btn_row.addWidget(btn_c)
        btn_a = QPushButton("✅  Agregar  (Enter)")
        btn_a.setFixedHeight(40)
        btn_a.setStyleSheet(f"background: {ACCENT_BOTON}; color: white; border-radius: 8px; font-weight: bold; font-size: 14px;")
        btn_a.clicked.connect(lambda: agregar_fila())
        btn_row.addWidget(btn_a)
        lay.addLayout(btn_row)

        input_b.setFocus()
        dialog.exec()
        self.input_buscar.setFocus()
        dialog.setWindowTitle("🔍 F6 — Buscar producto")
        dialog.setMinimumSize(600, 500)
        dialog.setStyleSheet(f"background-color: {BG_MAIN}; color: {TEXT_MAIN};")
        lay = QVBoxLayout(dialog)
        lay.setSpacing(10)
        lay.setContentsMargins(16, 16, 16, 16)

        input_b = QLineEdit()
        input_b.setPlaceholderText("Nombre o código de barras...")
        input_b.setFixedHeight(48)
        input_b.setStyleSheet(f"QLineEdit {{ background: {BG_PANEL}; border: 2px solid {ACCENT_BOTON}; border-radius: 10px; padding: 10px; color: white; font-size: 16px; }}")
        lay.addWidget(input_b)

        tabla_b = QTableWidget(0, 4)
        tabla_b.setHorizontalHeaderLabels(["Código", "Nombre", "Precio", "Stock"])
        tabla_b.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        tabla_b.setColumnWidth(0, 100)
        tabla_b.setColumnWidth(2, 100)
        tabla_b.setColumnWidth(3, 80)
        tabla_b.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tabla_b.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        tabla_b.setStyleSheet(f"""
            QTableWidget {{ background: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 10px; font-size: 14px; }}
            QHeaderView::section {{ background: {BG_MAIN}; color: {TEXT_MUTED}; padding: 8px; border: none; }}
            QTableWidget::item {{ color: {TEXT_MAIN}; padding: 6px; border-bottom: 1px solid {BORDER}; }}
            QTableWidget::item:selected {{ background: {ACCENT_BOTON}; }}
        """)
        lay.addWidget(tabla_b)

        lbl_hint = QLabel("↵ Enter o doble clic para agregar al ticket")
        lbl_hint.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        lay.addWidget(lbl_hint)

        productos_encontrados = []

        def buscar():
            texto = input_b.text().strip()
            if not texto: return
            # Buscar en cache local — sin red
            if self.productos_cache:
                texto_lower = texto.lower()
                if texto in self.productos_codigo:
                    productos = [self.productos_codigo[texto]]
                else:
                    productos = [p for p in self.productos_cache
                                 if texto_lower in p["nombre"].lower() and p.get("activo", True)]
            else:
                # Fallback API
                try:
                    r = requests.get(f"{API_URL}/productos/buscar", params={"q": texto}, timeout=5)
                    productos = r.json() if r.status_code == 200 else []
                except Exception:
                    productos = []
            productos_encontrados.clear()
            productos_encontrados.extend(productos)
            tabla_b.setRowCount(len(productos))
            for i, p in enumerate(productos):
                tabla_b.setItem(i, 0, QTableWidgetItem(p.get("codigo_barra") or ""))
                tabla_b.setItem(i, 1, QTableWidgetItem(p["nombre"]))
                tabla_b.setItem(i, 2, QTableWidgetItem(_p(p['precio_venta'])))
                stock = float(p.get("stock_actual", 0))
                item_stock = QTableWidgetItem(f"{stock:g}")
                if stock <= 0:
                    item_stock.setForeground(Qt.GlobalColor.red)
                elif stock <= float(p.get("stock_minimo", 0)):
                    item_stock.setForeground(Qt.GlobalColor.yellow)
                tabla_b.setItem(i, 3, item_stock)

        def agregar_seleccionado():
            row = tabla_b.currentRow()
            if row >= 0 and row < len(productos_encontrados):
                self.agregar_item(productos_encontrados[row])
                dialog.accept()

        input_b.returnPressed.connect(buscar)
        tabla_b.cellDoubleClicked.connect(lambda: agregar_seleccionado())

        btn_row = QHBoxLayout()
        btn_c = QPushButton("Cerrar")
        btn_c.setFixedHeight(40)
        btn_c.setStyleSheet(f"background: transparent; color: {TEXT_MUTED}; border: 1px solid {BORDER}; border-radius: 8px;")
        btn_c.clicked.connect(dialog.reject)
        btn_row.addWidget(btn_c)
        btn_a = QPushButton("✅ Agregar seleccionado")
        btn_a.setFixedHeight(40)
        btn_a.setStyleSheet(f"background: {ACCENT_BOTON}; color: white; border-radius: 8px; font-weight: bold;")
        btn_a.clicked.connect(agregar_seleccionado)
        btn_row.addWidget(btn_a)
        lay.addLayout(btn_row)

        input_b.setFocus()
        dialog.exec()
        self.input_buscar.setFocus()

    def _restaurar_foco_lectora(self):
        """Devuelve el foco al buscador automáticamente para que la lectora siempre funcione."""
        from PyQt6.QtWidgets import QApplication
        widget_activo = QApplication.focusWidget()
        # Si el foco está en la tabla, un botón o en ningún lado — volver al buscador
        # No interrumpir si está en un QLineEdit (puede ser que esté escribiendo algo)
        if widget_activo is None or isinstance(widget_activo, (QPushButton, QTableWidget)):
            self.input_buscar.setFocus()

    def cancelar_venta(self):
        self.items_venta = []
        self.cliente_actual = None
        self.lbl_cliente_info.hide()
        self.btn_cliente.setText("👤 Vincular cliente")
        self.btn_cliente.setStyleSheet(f"QPushButton {{ background: {BG_MAIN}; color: {ACCENT_BOTON}; border-radius: 8px; font-size: 14px; border: 1px solid {BORDER}; }}")
        self.actualizar_tabla()
        self.input_buscar.clear()
        self.input_buscar.setFocus()
        # ==========================================
    # LÓGICA DE TICKETS EN ESPERA (NUEVO F5)
    # ==========================================
    def pausar_venta_actual(self):
        if not self.items_venta:
            QMessageBox.information(self, "Aviso", "No hay productos para pausar.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Pausar Venta (F5)")
        dialog.setStyleSheet(f"background-color: {BG_MAIN}; color: white;")
        lay = QVBoxLayout(dialog)
        
        lay.addWidget(QLabel("Nombre o nota para identificar este ticket:"))
        input_nombre = QLineEdit()
        input_nombre.setPlaceholderText(f"Cliente {len(self.tickets_en_espera) + 1}")
        input_nombre.setStyleSheet(f"background: {BG_PANEL}; border: 1px solid {ACCENT_BOTON}; padding: 8px;")
        lay.addWidget(input_nombre)

        def confirmar():
            nombre = input_nombre.text().strip() or f"Cliente {len(self.tickets_en_espera) + 1}"
            
            # Guardar la venta actual en la memoria
            venta_pausada = {
                "nombre": nombre,
                "items": list(self.items_venta), # Copia de la lista
                "cliente": self.cliente_actual
            }
            self.tickets_en_espera.append(venta_pausada)
            
            # Limpiar la pantalla
            self.items_venta = []
            self.cliente_actual = None
            self.lbl_cliente_info.hide()
            self.btn_cliente.setText("👤 Vincular cliente")
            self.btn_cliente.setStyleSheet(f"QPushButton {{ background: {BG_MAIN}; color: {ACCENT_BOTON}; border-radius: 8px; font-size: 14px; border: 1px solid {BORDER}; }}")
            self.actualizar_tabla()
            
            # Actualizar botón de recuperación
            self.btn_recuperar_pausa.setText(f"⏳ Recuperar ({len(self.tickets_en_espera)})")
            self.btn_recuperar_pausa.show()
            
            dialog.accept()

        btn = QPushButton("Pausar Ticket")
        btn.setStyleSheet(f"background: #F59E0B; color: black; font-weight: bold; padding: 10px;")
        btn.clicked.connect(confirmar)
        lay.addWidget(btn)
        
        input_nombre.returnPressed.connect(confirmar)
        dialog.exec()
        self.input_buscar.setFocus()

    def ver_ventas_pausadas(self):
        if not self.tickets_en_espera: return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Ventas en Espera")
        dialog.setMinimumWidth(400)
        dialog.setStyleSheet(f"background-color: {BG_MAIN}; color: white;")
        lay = QVBoxLayout(dialog)
        
        lista = QListWidget()
        lista.setStyleSheet(f"QListWidget {{ background: {BG_PANEL}; border: 1px solid {BORDER}; color: white; }} QListWidget::item {{ padding: 10px; border-bottom: 1px solid {BORDER}; }}")
        
        for i, t in enumerate(self.tickets_en_espera):
            total = sum(item["subtotal"] for item in t["items"])
            item = QListWidgetItem(f"🛒 {t['nombre']} - {len(t['items'])} prod. - ${total:.2f}")
            item.setData(Qt.ItemDataRole.UserRole, i)
            lista.addItem(item)
            
        lay.addWidget(lista)

        def recuperar(item):
            if self.items_venta:
                # Si hay cosas cargadas, preguntamos si quiere reemplazarlas
                resp = QMessageBox.question(self, "Atención", "Hay productos cargados. ¿Reemplazarlos por el ticket en espera?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if resp == QMessageBox.StandardButton.No: return

            idx = item.data(Qt.ItemDataRole.UserRole)
            ticket_recuperado = self.tickets_en_espera.pop(idx)
            
            self.items_venta = ticket_recuperado["items"]
            self.cliente_actual = ticket_recuperado["cliente"]
            
            if self.cliente_actual:
                self.lbl_cliente_info.setText(f"👤 {self.cliente_actual['nombre']}")
                self.lbl_cliente_info.show()
                self.btn_cliente.setText(f"👤 {self.cliente_actual['nombre'][:18]}")
            
            self.actualizar_tabla()
            
            # Ocultar o actualizar botón
            if not self.tickets_en_espera:
                self.btn_recuperar_pausa.hide()
            else:
                self.btn_recuperar_pausa.setText(f"⏳ Recuperar ({len(self.tickets_en_espera)})")
                
            dialog.accept()

        lista.itemDoubleClicked.connect(recuperar)
        
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(dialog.reject)
        lay.addWidget(btn_cerrar)
        
        dialog.exec()
        self.input_buscar.setFocus()            