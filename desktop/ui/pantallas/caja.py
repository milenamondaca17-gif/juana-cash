import requests
import threading
import smtplib
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QLineEdit, QFrame, QMessageBox,
                              QTableWidget, QTableWidgetItem, QHeaderView,
                              QDialog, QComboBox, QScrollArea, QSizePolicy,
                              QSpinBox, QCheckBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from datetime import datetime

# ─── Config de email ─────────────────────────────────────────────────────────
EMAIL_CONFIG_PATH = os.path.join(os.path.expanduser("~"), "JuanaCash_Data", "email_config.json")

def leer_email_config():
    try:
        if os.path.exists(EMAIL_CONFIG_PATH):
            with open(EMAIL_CONFIG_PATH) as f:
                return json.load(f)
    except Exception:
        pass
    return {
        "smtp_user": "",
        "smtp_pass": "",
        "destinatarios": ["milenamondaca17@gmail.com"],
        "habilitado": False
    }

def guardar_email_config(cfg):
    try:
        os.makedirs(os.path.dirname(EMAIL_CONFIG_PATH), exist_ok=True)
        with open(EMAIL_CONFIG_PATH, "w") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass

def enviar_email_cierre(asunto, cuerpo):
    """Envía el resumen de cierre por email. Corre en thread."""
    def _send():
        cfg = leer_email_config()
        if not cfg.get("habilitado") or not cfg.get("smtp_user") or not cfg.get("smtp_pass"):
            return
        try:
            destinatarios = cfg.get("destinatarios", ["milenamondaca17@gmail.com"])
            for dest in destinatarios:
                msg = MIMEMultipart()
                msg["From"]    = cfg["smtp_user"]
                msg["To"]      = dest
                msg["Subject"] = asunto
                msg.attach(MIMEText(cuerpo, "plain", "utf-8"))
                with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as s:
                    s.login(cfg["smtp_user"], cfg["smtp_pass"])
                    s.send_message(msg)
            print(f"[EMAIL OK] Cierre enviado a {destinatarios}")
        except Exception as e:
            print(f"[EMAIL ERROR] {e}")
    threading.Thread(target=_send, daemon=True).start()

API_URL = "http://127.0.0.1:8000"

def _p(v):
    """Precio en formato argentino: $10.000"""
    return f"${float(v):,.0f}".replace(",", ".")

from ui.theme import get_tema as _get_tema, TEMAS, guardar_tema
_T = _get_tema()

BG_MAIN  = _T["bg_app"]
BG_CARD  = _T["bg_card"]
BORDER   = _T["border"]
TEXT_MAIN  = _T["text_main"]
TEXT_MUTED = _T["text_muted"]
PRIMARY    = _T["primary"]
DANGER     = _T["danger"]
SUCCESS    = _T["success"]
WARNING    = _T["warning"]

class AnularDialog(QDialog):
    def __init__(self, parent=None, ticket=""):
        super().__init__(parent)
        self.setWindowTitle(f"🚫 Anular ticket {ticket}")
        self.setMinimumWidth(400)
        self.setStyleSheet(f"background-color: {BG_CARD}; color: {TEXT_MAIN};")
        self.setup_ui(ticket)

    def setup_ui(self, ticket):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)
        lbl = QLabel(f"⚠️ Anular ticket #{ticket}")
        lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {DANGER}; background: transparent;")
        layout.addWidget(lbl)
        lbl2 = QLabel("Esta acción devuelve el stock y no puede deshacerse.")
        lbl2.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; background: transparent;")
        layout.addWidget(lbl2)
        lbl_m = QLabel("Motivo de anulación:")
        lbl_m.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px; background: transparent;")
        layout.addWidget(lbl_m)
        self.combo_motivo = QComboBox()
        self.combo_motivo.addItems(["Error de carga", "Producto devuelto", "Error de precio", "Solicitud del cliente", "Otro"])
        self.combo_motivo.setFixedHeight(42)
        layout.addWidget(self.combo_motivo)
        lbl_p = QLabel("Contraseña de admin o encargado:")
        lbl_p.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px; background: transparent;")
        layout.addWidget(lbl_p)
        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password.setFixedHeight(44)
        layout.addWidget(self.input_password)
        btns = QHBoxLayout()
        btn_c = QPushButton("Cancelar")
        btn_c.setFixedHeight(40)
        btn_c.setStyleSheet(f"QPushButton {{ background: transparent; color: {TEXT_MUTED}; border: 1.5px solid {BORDER}; border-radius: 8px; font-weight: bold; }} QPushButton:hover {{ background: {BG_MAIN}; }}")
        btn_c.clicked.connect(self.reject)
        btns.addWidget(btn_c)
        btn_ok = QPushButton("🚫 Confirmar anulación")
        btn_ok.setFixedHeight(40)
        btn_ok.setStyleSheet(f"QPushButton {{ background: {DANGER}; color: white; border-radius: 8px; font-size: 14px; font-weight: bold; }} QPushButton:hover {{ background: #b91c1c; }}")
        btn_ok.clicked.connect(self.accept)
        btns.addWidget(btn_ok)
        layout.addLayout(btns)


class CajaScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.turno_actual = None
        self.usuario_id = 1
        self.nombre_cajero = ""
        self.ventas_data = []
        self._pagos_empleados_guardados = []
        self.setup_ui()
        self._timer_refresh = QTimer(self)
        self._timer_refresh.setInterval(10000)  # 10 segundos
        self._timer_refresh.timeout.connect(self.actualizar_ventas)

    def set_usuario(self, usuario):
        self.usuario_id = usuario.get("id", 1)
        self.nombre_cajero = usuario.get("nombre", "")

    def setup_ui(self):
        self.setStyleSheet(f"background-color: {BG_MAIN}; color: {TEXT_MAIN};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        titulo = QLabel("🏧 Caja")
        titulo.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        titulo.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent;")
        layout.addWidget(titulo)

        # Card estado
        CARD_SS = f"QFrame {{ background: {BG_CARD}; border-radius: 14px; border: 1.5px solid {BORDER}; border-left: 5px solid {DANGER}; }}"
        self.card_estado = QFrame()
        self.card_estado.setStyleSheet(CARD_SS)
        self.card_estado.setMinimumHeight(110)
        card_layout = QVBoxLayout(self.card_estado)
        card_layout.setContentsMargins(24, 16, 24, 16)
        self.lbl_estado = QLabel("⚪ Caja cerrada")
        self.lbl_estado.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.lbl_estado.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent;")
        card_layout.addWidget(self.lbl_estado)
        self.lbl_apertura = QLabel("")
        self.lbl_apertura.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px; background: transparent;")
        card_layout.addWidget(self.lbl_apertura)
        self.lbl_total_caja = QLabel("Total acumulado: $0.00")
        self.lbl_total_caja.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.lbl_total_caja.setStyleSheet(f"color: {DANGER}; background: transparent;")
        card_layout.addWidget(self.lbl_total_caja)
        self.lbl_ef_caja = QLabel("💵 Efectivo en caja: —")
        self.lbl_ef_caja.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.lbl_ef_caja.setStyleSheet(f"color: #16a34a; background: transparent;")
        card_layout.addWidget(self.lbl_ef_caja)
        layout.addWidget(self.card_estado)

        # Desglose por método
        desglose_frame = QFrame()
        desglose_frame.setStyleSheet(f"QFrame {{ background: {BG_CARD}; border-radius: 12px; border: 1.5px solid {BORDER}; }}")
        desglose_layout = QHBoxLayout(desglose_frame)
        desglose_layout.setContentsMargins(16, 12, 16, 12)
        desglose_layout.setSpacing(8)
        self.cards_metodo = {}
        metodos = [
            ("💵", "Efectivo",    "efectivo",       "#16a34a"),
            ("🏧", "Débito",      "debito",          "#10b981"),
            ("💳", "Tarjeta",     "tarjeta",         "#2563eb"),
            ("📱", "QR / MP",     "mercadopago_qr",  "#0284c7"),
            ("🏦", "Transf.",     "transferencia",   "#7c3aed"),
            ("💸", "Fiado",       "fiado",           "#dc2626"),
        ]
        for icono, nombre, key, color in metodos:
            card = QFrame()
            card.setStyleSheet(f"QFrame {{ background: {BG_MAIN}; border-radius: 10px; border-left: 4px solid {color}; }}")
            c_layout = QVBoxLayout(card)
            c_layout.setContentsMargins(12, 10, 12, 10)
            lbl_n = QLabel(f"{icono} {nombre}")
            lbl_n.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: bold; background: transparent;")
            c_layout.addWidget(lbl_n)
            lbl_v = QLabel("$0.00")
            lbl_v.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
            lbl_v.setStyleSheet(f"color: {color}; background: transparent;")
            c_layout.addWidget(lbl_v)
            desglose_layout.addWidget(card)
            self.cards_metodo[key] = lbl_v
        layout.addWidget(desglose_frame)

        # Botones de acción
        BTN_H = 40
        btns = QHBoxLayout()
        btns.setSpacing(8)

        lbl_monto = QLabel("Monto inicial ($):")
        lbl_monto.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 14px; background: transparent;")
        btns.addWidget(lbl_monto)

        self.input_monto = QLineEdit()
        self.input_monto.setPlaceholderText("5000")
        self.input_monto.setFixedWidth(120)
        self.input_monto.setFixedHeight(BTN_H)
        btns.addWidget(self.input_monto)

        def _btn(texto, color_bg, slot, enabled=True):
            b = QPushButton(texto)
            b.setFixedHeight(BTN_H)
            b.setStyleSheet(f"QPushButton {{ background: {color_bg}; color: white; border-radius: 8px; padding: 0 14px; font-size: 13px; font-weight: bold; }} QPushButton:hover {{ opacity: 0.85; }} QPushButton:disabled {{ background: {BORDER}; color: {TEXT_MUTED}; }}")
            b.clicked.connect(slot)
            b.setEnabled(enabled)
            return b

        self.btn_abrir  = _btn("🔓 Abrir caja",       SUCCESS,   self.abrir_caja)
        self.btn_cerrar = _btn("🔒 Cerrar caja",       DANGER,    self.cerrar_caja, enabled=False)
        btn_gasto       = _btn("💸 Gasto",             "#7c3aed", self.registrar_gasto)
        btn_empleados   = _btn("👥 Empleados",         "#ea580c", self.ver_historial_empleados)
        btn_histef      = _btn("💵 Hist. efectivo",    SUCCESS,   self.ver_historial_efectivo)
        btn_email_cfg   = _btn("📧 Email",             "#2563eb", self.ver_config_email)

        btn_paleta = QPushButton("🎨 Paleta")
        btn_paleta.setFixedHeight(BTN_H)
        btn_paleta.setStyleSheet(f"QPushButton {{ background: {PRIMARY}; color: white; border-radius: 8px; padding: 0 14px; font-size: 13px; font-weight: bold; }} QPushButton:hover {{ background: {_T['primary_hover']}; }}")
        btn_paleta.clicked.connect(self.elegir_paleta)

        btn_refresh = QPushButton("🔄 Actualizar")
        btn_refresh.setFixedHeight(BTN_H)
        btn_refresh.setStyleSheet(f"QPushButton {{ background: #0f766e; color: white; border-radius: 8px; padding: 0 14px; font-size: 13px; font-weight: bold; }} QPushButton:hover {{ background: #0d9488; }}")
        btn_refresh.clicked.connect(self.actualizar_ventas)

        for b in [self.btn_abrir, self.btn_cerrar, btn_gasto, btn_empleados, btn_histef, btn_email_cfg, btn_paleta, btn_refresh]:
            btns.addWidget(b)
        btns.addStretch()
        layout.addLayout(btns)

        # Label y tabla ventas turno
        lbl_resumen = QLabel("Ventas del turno")
        lbl_resumen.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        lbl_resumen.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent;")
        layout.addWidget(lbl_resumen)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(8)
        self.tabla.setHorizontalHeaderLabels(["Ticket", "Total", "Método", "Origen", "Estado", "Hora", "Anular", "🖨"])
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabla.setColumnWidth(1, 110)
        self.tabla.setColumnWidth(2, 100)
        self.tabla.setColumnWidth(3, 110)
        self.tabla.setColumnWidth(4, 90)
        self.tabla.setColumnWidth(5, 60)
        self.tabla.setColumnWidth(6, 90)
        self.tabla.setColumnWidth(7, 50)
        self.tabla.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.tabla.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.tabla)

        # Historial de cierres
        sep_h = QFrame()
        sep_h.setFixedHeight(1)
        sep_h.setStyleSheet(f"background: {BORDER}; border: none;")
        layout.addWidget(sep_h)

        hdr_hist = QHBoxLayout()
        lbl_hist = QLabel("📋 Historial de cierres")
        lbl_hist.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        lbl_hist.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent;")
        hdr_hist.addWidget(lbl_hist)
        hdr_hist.addStretch()
        btn_hist_ref = QPushButton("🔄")
        btn_hist_ref.setFixedSize(34, 34)
        btn_hist_ref.setStyleSheet(f"QPushButton {{ background: {BG_CARD}; color: {TEXT_MAIN}; border-radius: 8px; border: 1.5px solid {BORDER}; }}")
        btn_hist_ref.clicked.connect(self.cargar_historial)
        hdr_hist.addWidget(btn_hist_ref)
        layout.addLayout(hdr_hist)

        self.tabla_historial = QTableWidget()
        self.tabla_historial.setColumnCount(6)
        self.tabla_historial.setHorizontalHeaderLabels(["Apertura", "Cierre", "Apertura $", "Vendido $", "Declarado $", "Diferencia"])
        self.tabla_historial.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabla_historial.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla_historial.setColumnWidth(2, 100)
        self.tabla_historial.setColumnWidth(3, 100)
        self.tabla_historial.setColumnWidth(4, 110)
        self.tabla_historial.setColumnWidth(5, 100)
        self.tabla_historial.setMaximumHeight(220)
        self.tabla_historial.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.tabla_historial)



    def elegir_paleta(self):
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
        from PyQt6.QtGui import QFont
        dlg = QDialog(self)
        dlg.setWindowTitle("🎨 Elegir paleta de colores")
        dlg.setMinimumWidth(480)
        dlg.setStyleSheet(f"background: {BG_CARD}; color: {TEXT_MAIN};")
        lay = QVBoxLayout(dlg)
        lay.setSpacing(12)
        lay.setContentsMargins(24, 24, 24, 24)
        titulo = QLabel("🎨 Paleta de colores")
        titulo.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        titulo.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent;")
        lay.addWidget(titulo)
        sub = QLabel("Elegí un tema. La app se reinicia para aplicarlo.")
        sub.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; background: transparent; margin-bottom: 8px;")
        lay.addWidget(sub)

        from ui.theme import get_tema_key
        actual = get_tema_key()

        previews = {
            "violeta_calido": ("#7C3AED", "#10B981", "#F5F3FF"),
            "naranja_cielo":  ("#EA580C", "#0EA5E9", "#FFFBF5"),
            "rosa_sage":      ("#DB2777", "#4ADE80", "#FDF2F8"),
            "lila_sol":       ("#9333EA", "#FDE047", "#FAFAF9"),
            "clasico_oscuro": ("#556EE6", "#34C38F", "#050e1a"),
        }

        for key, tema in TEMAS.items():
            colores = previews.get(key, ("#888", "#888", "#fff"))
            fila = QFrame()
            es_actual = (key == actual)
            borde = PRIMARY if es_actual else BORDER
            fila.setStyleSheet(f"QFrame {{ background: {BG_MAIN}; border-radius: 12px; border: 2px solid {borde}; }}")
            fila_lay = QHBoxLayout(fila)
            fila_lay.setContentsMargins(14, 10, 14, 10)
            # Muestra de colores
            for c in colores:
                dot = QFrame()
                dot.setFixedSize(18, 18)
                dot.setStyleSheet(f"background: {c}; border-radius: 9px; border: none;")
                fila_lay.addWidget(dot)
            lbl = QLabel(tema["nombre"])
            lbl.setStyleSheet(f"color: {TEXT_MAIN}; font-size: 14px; font-weight: {'bold' if es_actual else 'normal'}; background: transparent; margin-left: 8px;")
            fila_lay.addWidget(lbl)
            if es_actual:
                lbl_act = QLabel("✓ Activo")
                lbl_act.setStyleSheet(f"color: {SUCCESS}; font-size: 12px; font-weight: bold; background: transparent;")
                fila_lay.addWidget(lbl_act)
            fila_lay.addStretch()
            btn_sel = QPushButton("Aplicar")
            btn_sel.setFixedHeight(32)
            btn_sel.setEnabled(not es_actual)
            btn_sel.setStyleSheet(f"QPushButton {{ background: {PRIMARY}; color: white; border-radius: 6px; font-size: 12px; font-weight: bold; padding: 0 14px; }} QPushButton:disabled {{ background: {BORDER}; color: {TEXT_MUTED}; }} QPushButton:hover {{ background: {_T['primary_hover']}; }}")
            def _aplicar(k=key):
                guardar_tema(k)
                QMessageBox.information(dlg, "Paleta guardada",
                    f"Paleta '{TEMAS[k]['nombre']}' guardada.\nReiniciá la app para aplicarla.")
                dlg.accept()
            btn_sel.clicked.connect(_aplicar)
            fila_lay.addWidget(btn_sel)
            lay.addWidget(fila)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setFixedHeight(38)
        btn_cerrar.setStyleSheet(f"QPushButton {{ background: {BG_MAIN}; color: {TEXT_MUTED}; border: 1.5px solid {BORDER}; border-radius: 8px; font-weight: bold; }}")
        btn_cerrar.clicked.connect(dlg.reject)
        lay.addWidget(btn_cerrar)
        dlg.exec()

    def ver_historial_efectivo(self):
        """Dialog con historial de efectivo día a día."""
        dialog = QDialog(self)
        dialog.setWindowTitle("💵 Historial de efectivo por día")
        dialog.setMinimumWidth(820)
        dialog.setMinimumHeight(500)
        dialog.setStyleSheet("background-color: #1a1a2e; color: white;")
        lay = QVBoxLayout(dialog)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(10)

        titulo = QLabel("💵 Historial de efectivo por día — últimos 30 días")
        titulo.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        titulo.setStyleSheet("color: white;")
        lay.addWidget(titulo)

        tabla = QTableWidget()
        tabla.setColumnCount(8)
        tabla.setHorizontalHeaderLabels(["Fecha", "💵 Efectivo", "🏧 Débito", "💳 Tarjeta", "📱 QR/MP", "🏦 Transf.", "💸 Fiado", "💰 Total"])
        tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in range(1, 8):
            tabla.setColumnWidth(col, 100)
        tabla.setStyleSheet("QTableWidget { background: #16213e; border: 1px solid #0f3460; border-radius: 8px; gridline-color: #0f3460; } QHeaderView::section { background: #0f3460; color: #a0a0b0; padding: 6px; border: none; } QTableWidgetItem { color: white; padding: 6px; }")
        tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        lay.addWidget(tabla)

        lbl_estado = QLabel("⏳ Cargando...")
        lbl_estado.setStyleSheet("color: #94A3B8; font-size: 12px;")
        lay.addWidget(lbl_estado)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setFixedHeight(38)
        btn_cerrar.setStyleSheet("QPushButton { background: #0f3460; color: white; border-radius: 8px; padding: 0 20px; }")
        btn_cerrar.clicked.connect(dialog.accept)
        lay.addWidget(btn_cerrar)

        def cargar():
            try:
                r = requests.get(f"{API_URL}/caja/historial-efectivo?dias=30", timeout=5)
                datos = r.json() if r.status_code == 200 else []
            except Exception:
                datos = []
            tabla.setRowCount(0)
            colores = ["white", "#27ae60", "#3498db", "#009ee3", "#9b59b6", "#e74c3c", "#f39c12"]
            for d in datos:
                row = tabla.rowCount()
                tabla.insertRow(row)
                vals = [
                    d.get("fecha", ""),
                    f"${float(d.get('efectivo', 0)):,.0f}",
                    f"${float(d.get('debito', 0)):,.0f}",
                    f"${float(d.get('tarjeta', 0)):,.0f}",
                    f"${float(d.get('mercadopago_qr', 0)):,.0f}",
                    f"${float(d.get('transferencia', 0)):,.0f}",
                    f"${float(d.get('fiado', 0)):,.0f}",
                    f"${float(d.get('total', 0)):,.0f}",
                ]
                for col, (val, color) in enumerate(zip(vals, colores)):
                    item = QTableWidgetItem(str(val))
                    item.setForeground(__import__('PyQt6.QtGui', fromlist=['QColor']).QColor(color))
                    tabla.setItem(row, col, item)
            lbl_estado.setText(f"✅ {len(datos)} día(s) con ventas" if datos else "Sin datos aún")

        threading.Thread(target=cargar, daemon=True).start()
        dialog.exec()

    def ver_historial_empleados(self):
        """Dialog para ver y registrar pagos de empleados del día."""
        dialog = QDialog(self)
        dialog.setWindowTitle("👥 Pago de empleados")
        dialog.setMinimumWidth(480)
        dialog.setStyleSheet("background-color: #1a1a2e; color: white;")
        lay = QVBoxLayout(dialog)
        lay.setContentsMargins(20, 16, 20, 20)
        lay.setSpacing(10)

        titulo = QLabel("👥 Registrar pagos de empleados")
        titulo.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        titulo.setStyleSheet("color: white;")
        lay.addWidget(titulo)

        sub = QLabel("Los pagos se descontarán del efectivo al cerrar caja.")
        sub.setStyleSheet("color: #a0a0b0; font-size: 12px;")
        lay.addWidget(sub)

        filas_emp = []
        for i in range(5):
            row_e = QHBoxLayout()
            lbl_n = QLabel(f"Empleado {i+1}:")
            lbl_n.setStyleSheet("color: #a0a0b0; font-size: 12px;")
            lbl_n.setFixedWidth(90)
            in_nombre = QLineEdit()
            in_nombre.setPlaceholderText("Nombre")
            in_nombre.setFixedHeight(38)
            in_nombre.setStyleSheet("QLineEdit { background: #0f3460; border: 1px solid #e67e22; border-radius: 6px; padding: 8px; color: white; font-size: 13px; }")
            in_monto = QLineEdit()
            in_monto.setPlaceholderText("$0")
            in_monto.setFixedWidth(100)
            in_monto.setFixedHeight(38)
            in_monto.setStyleSheet("QLineEdit { background: #0f3460; border: 1px solid #e67e22; border-radius: 6px; padding: 8px; color: white; font-size: 13px; }")
            row_e.addWidget(lbl_n)
            row_e.addWidget(in_nombre)
            row_e.addWidget(in_monto)
            lay.addLayout(row_e)
            filas_emp.append((in_nombre, in_monto))

        lbl_total_emp = QLabel("Total a pagar: $0")
        lbl_total_emp.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        lbl_total_emp.setStyleSheet("color: #e67e22;")
        lay.addWidget(lbl_total_emp)

        # Guardar referencia para que cerrar_caja pueda leerla
        self._filas_empleados_dialog = filas_emp
        self._lbl_total_emp_dialog = lbl_total_emp

        def actualizar_total():
            total = 0
            for in_n, in_m in filas_emp:
                try:
                    if in_n.text().strip():
                        total += float(in_m.text() or 0)
                except ValueError:
                    pass
            lbl_total_emp.setText(f"Total a pagar: ${total:,.0f}")

        for in_n, in_m in filas_emp:
            in_m.textChanged.connect(lambda _: actualizar_total())
            in_n.textChanged.connect(lambda _: actualizar_total())

        btns = QHBoxLayout()
        btn_c = QPushButton("Cancelar")
        btn_c.setFixedHeight(40)
        btn_c.setStyleSheet("QPushButton { background: transparent; color: #a0a0b0; border: 1px solid #a0a0b0; border-radius: 8px; }")
        btn_c.clicked.connect(dialog.reject)
        btns.addWidget(btn_c)
        btn_ok = QPushButton("✅ Guardar pagos")
        btn_ok.setFixedHeight(40)
        btn_ok.setStyleSheet("QPushButton { background: #e67e22; color: white; border-radius: 8px; font-weight: bold; }")
        btn_ok.clicked.connect(dialog.accept)
        btns.addWidget(btn_ok)
        lay.addLayout(btns)

        if dialog.exec():
            # Guardar los pagos en la instancia para usarlos en cerrar_caja
            self._pagos_empleados_guardados = []
            for in_n, in_m in filas_emp:
                nombre = in_n.text().strip()
                if not nombre:
                    continue
                try:
                    monto = float(in_m.text() or 0)
                    if monto > 0:
                        self._pagos_empleados_guardados.append({"nombre": nombre, "monto": monto})
                except ValueError:
                    pass
            total = sum(p["monto"] for p in self._pagos_empleados_guardados)
            if self._pagos_empleados_guardados:
                QMessageBox.information(self, "✅", f"Pagos guardados: ${total:,.0f}\nSe descontarán al cerrar caja.")

    def ver_config_email(self):
        """Dialog de configuración de email."""
        dialog = QDialog(self)
        dialog.setWindowTitle("📧 Configuración de email")
        dialog.setMinimumWidth(480)
        dialog.setStyleSheet("background-color: #1a1a2e; color: white;")
        lay = QVBoxLayout(dialog)
        lay.setContentsMargins(20, 16, 20, 20)
        lay.setSpacing(10)

        titulo = QLabel("📧 Envío automático al cerrar caja")
        titulo.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        titulo.setStyleSheet("color: white;")
        lay.addWidget(titulo)

        cfg_mail = leer_email_config()

        chk_email = QCheckBox("Enviar resumen al cerrar caja")
        chk_email.setChecked(cfg_mail.get("habilitado", False))
        chk_email.setStyleSheet("color: white; font-size: 13px;")
        lay.addWidget(chk_email)

        def fila_input(label, valor, placeholder, echo=False):
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet("color: #a0a0b0; font-size: 12px;")
            lbl.setFixedWidth(140)
            inp = QLineEdit(valor)
            inp.setPlaceholderText(placeholder)
            inp.setFixedHeight(38)
            if echo:
                inp.setEchoMode(QLineEdit.EchoMode.Password)
            inp.setStyleSheet("QLineEdit { background: #0f3460; border: 1px solid #3498db; border-radius: 6px; padding: 8px; color: white; }")
            row.addWidget(lbl)
            row.addWidget(inp)
            lay.addLayout(row)
            return inp

        in_user = fila_input("Gmail remitente:", cfg_mail.get("smtp_user", ""), "tucuenta@gmail.com")
        in_pass = fila_input("Contraseña de app:", cfg_mail.get("smtp_pass", ""), "Contraseña de aplicación", echo=True)
        in_dest = fila_input("Destinatarios:", ", ".join(cfg_mail.get("destinatarios", ["milenamondaca17@gmail.com"])), "email1@gmail.com, email2@gmail.com")

        sub = QLabel("💡 La contraseña de app se genera en:\nmyaccount.google.com → Seguridad → Contraseñas de aplicación")
        sub.setStyleSheet("color: #606880; font-size: 11px;")
        lay.addWidget(sub)

        lbl_status = QLabel("")
        lbl_status.setStyleSheet("color: #27ae60; font-size: 12px;")
        lay.addWidget(lbl_status)

        btns = QHBoxLayout()
        btn_test = QPushButton("✉️ Probar envío")
        btn_test.setFixedHeight(38)
        btn_test.setStyleSheet("QPushButton { background: #0f3460; color: #3498db; border: 1px solid #3498db; border-radius: 8px; font-weight: bold; }")
        btns.addWidget(btn_test)
        btn_ok = QPushButton("💾 Guardar")
        btn_ok.setFixedHeight(38)
        btn_ok.setStyleSheet("QPushButton { background: #3498db; color: white; border-radius: 8px; font-weight: bold; }")
        btns.addWidget(btn_ok)
        lay.addLayout(btns)

        def guardar():
            cfg = {
                "smtp_user": in_user.text().strip(),
                "smtp_pass": in_pass.text().strip(),
                "destinatarios": [d.strip() for d in in_dest.text().split(",") if d.strip()],
                "habilitado": chk_email.isChecked()
            }
            guardar_email_config(cfg)
            lbl_status.setText("✅ Guardado correctamente")
            QTimer.singleShot(2000, lambda: lbl_status.setText(""))

        def probar():
            guardar()
            cfg = leer_email_config()
            if not cfg.get("smtp_user") or not cfg.get("smtp_pass"):
                lbl_status.setStyleSheet("color: #e74c3c; font-size: 12px;")
                lbl_status.setText("❌ Completá el Gmail remitente y la contraseña de app")
                return
            lbl_status.setStyleSheet("color: #f39c12; font-size: 12px;")
            lbl_status.setText("⏳ Enviando...")

            def _send():
                try:
                    destinatarios = cfg.get("destinatarios", ["milenamondaca17@gmail.com"])
                    for dest in destinatarios:
                        msg = MIMEMultipart()
                        msg["From"]    = cfg["smtp_user"]
                        msg["To"]      = dest
                        msg["Subject"] = "Juana Cash - Prueba de email"
                        msg.attach(MIMEText(
                            "Este es un email de prueba del sistema Juana Cash.\n\nSi lo recibiste, la configuracion esta correcta.",
                            "plain", "utf-8"
                        ))
                        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as s:
                            s.login(cfg["smtp_user"], cfg["smtp_pass"])
                            s.send_message(msg)
                    QTimer.singleShot(0, lambda: (
                        lbl_status.setStyleSheet("color: #27ae60; font-size: 12px;"),
                        lbl_status.setText(f"✅ Enviado a {', '.join(destinatarios)}")
                    ))
                except Exception as e:
                    err = str(e)
                    QTimer.singleShot(0, lambda: (
                        lbl_status.setStyleSheet("color: #e74c3c; font-size: 12px;"),
                        lbl_status.setText(f"❌ Error: {err}")
                    ))

            threading.Thread(target=_send, daemon=True).start()

        btn_ok.clicked.connect(guardar)
        btn_test.clicked.connect(probar)
        dialog.exec()

    def _cargar_turno_activo(self):
        if self.turno_actual:
            return
        try:
            r = requests.get(f"{API_URL}/caja/turno-actual/{self.usuario_id}", timeout=5)
            if r.status_code == 200:
                data = r.json()
                if data.get("abierto"):
                    self.turno_actual = data
                    self.lbl_estado.setText("🟢 Caja abierta")
                    self.lbl_estado.setStyleSheet("color: #27ae60; font-size: 16px; font-weight: bold;")
                    apertura = data.get("apertura", "")
                    monto_ap = float(data.get("monto_apertura", 0))
                    self.lbl_apertura.setText(
                        f"Turno #{data['id']} — Monto inicial: ${monto_ap:,.0f}"
                        + (f" — Desde: {apertura[:16]}" if apertura else "")
                    )
                    self.btn_abrir.setEnabled(False)
                    self.btn_cerrar.setEnabled(True)
        except Exception:
            pass

    def showEvent(self, event):
        super().showEvent(event)
        self._cargar_turno_activo()
        self.cargar_historial()
        self.actualizar_ventas()
        self._timer_refresh.start()

    def hideEvent(self, event):
        super().hideEvent(event)
        self._timer_refresh.stop()

    def cargar_historial(self):
        try:
            r = requests.get(f"{API_URL}/caja/historial", timeout=5)
            cierres = r.json() if r.status_code == 200 else []
        except Exception:
            cierres = []
        self.tabla_historial.setRowCount(0)
        for c in cierres:
            row = self.tabla_historial.rowCount()
            self.tabla_historial.insertRow(row)
            diff = float(c.get("diferencia", 0))
            color_diff = "#27ae60" if abs(diff) < 100 else "#e74c3c"
            valores = [
                c.get("apertura", ""),
                c.get("cierre", ""),
                _p(c.get('monto_apertura', 0)),
                _p(c.get('monto_cierre_calculado', 0)),
                _p(c.get('monto_cierre_declarado', 0)),
                ("+" if diff >= 0 else "") + _p(diff),
            ]
            for col, val in enumerate(valores):
                item = QTableWidgetItem(str(val))
                item.setForeground(__import__('PyQt6.QtGui', fromlist=['QColor']).QColor(
                    color_diff if col == 5 else "white"
                ))
                self.tabla_historial.setItem(row, col, item)

    def abrir_caja(self):
        try:
            monto = float(self.input_monto.text() or 0)
        except ValueError:
            QMessageBox.warning(self, "Error", "Ingresá un monto válido")
            return
        try:
            r = requests.post(f"{API_URL}/caja/abrir", json={"usuario_id": self.usuario_id, "monto_apertura": monto}, timeout=5)
            if r.status_code == 200:
                self.turno_actual = r.json()
                self.lbl_estado.setText("🟢 Caja abierta")
                self.lbl_estado.setStyleSheet("color: #27ae60; font-size: 16px; font-weight: bold;")
                self.lbl_apertura.setText(f"Apertura: {datetime.now().strftime('%H:%M')} — Cajero: {self.nombre_cajero} — Monto inicial: {_p(monto)}")
                self.btn_abrir.setEnabled(False)
                self.btn_cerrar.setEnabled(True)
                try:
                    requests.post(f"{API_URL}/sesiones/registrar", json={"usuario_id": self.usuario_id, "nombre_cajero": self.nombre_cajero, "accion": "APERTURA_CAJA", "detalle": f"Monto inicial: ${monto:.2f}"}, timeout=3)
                except Exception:
                    pass
            else:
                QMessageBox.warning(self, "Error", "No se pudo abrir la caja")
        except Exception:
            QMessageBox.critical(self, "Error", "No se puede conectar al servidor")

    def cerrar_caja(self):
        if not self.turno_actual:
            return

        try:
            r_hoy = requests.get(f"{API_URL}/reportes/hoy", timeout=5)
            datos_hoy = r_hoy.json() if r_hoy.status_code == 200 else {}
        except Exception:
            datos_hoy = {}

        try:
            r_gastos = requests.get(f"{API_URL}/gastos/hoy", timeout=5)
            datos_gastos = r_gastos.json() if r_gastos.status_code == 200 else {}
        except Exception:
            datos_gastos = {}

        ventas = datos_hoy.get("ventas", [])
        desglose = datos_hoy.get("desglose_metodos", {})
        totales = {
            "efectivo":       float(desglose.get("efectivo", 0)),
            "debito":         float(desglose.get("debito", 0)),
            "tarjeta":        float(desglose.get("tarjeta", 0)),
            "mercadopago_qr": float(desglose.get("mercadopago_qr", 0)),
            "transferencia":  float(desglose.get("transferencia", 0)),
            "fiado":          float(desglose.get("fiado", 0)),
        }
        cant_tickets = 0
        cant_celular = 0
        for v in ventas:
            if v.get("estado") == "completada":
                cant_tickets += 1
                if v.get("origen", "") in ("celular", "celular_offline"):
                    cant_celular += 1

        total_vendido = datos_hoy.get("total_vendido", 0)
        total_gastos  = datos_gastos.get("total", 0)
        ticket_prom   = (total_vendido / cant_tickets) if cant_tickets > 0 else 0

        try:
            monto_apertura = float(self.turno_actual.get("monto_apertura", 0))
        except Exception:
            monto_apertura = 0

        total_emp_previo = sum(p["monto"] for p in getattr(self, '_pagos_empleados_guardados', []))
        efectivo_esperado = monto_apertura + totales["efectivo"] - total_gastos - total_emp_previo

        dialog = QDialog(self)
        dialog.setWindowTitle("Cierre de caja")
        dialog.setMinimumWidth(520)
        dialog.setStyleSheet("background-color: #1a1a2e; color: white;")
        lay = QVBoxLayout(dialog)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(10)

        titulo = QLabel("RESUMEN DE CIERRE")
        titulo.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        titulo.setStyleSheet("color: white;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(titulo)

        stats_frame = QFrame()
        stats_frame.setStyleSheet("QFrame { background: #0f3460; border-radius: 8px; }")
        stats_lay = QHBoxLayout(stats_frame)
        stats_lay.setContentsMargins(14, 10, 14, 10)
        stats_lay.setSpacing(0)
        for s_txt, s_val, s_color in [
            ("Tickets", str(cant_tickets), "#3498db"),
            ("📱 Celular", str(cant_celular), "#9b59b6"),
            ("Promedio", _p(ticket_prom), "#27ae60"),
            ("Apertura", str(self.turno_actual.get("apertura","?"))[:16].replace("T"," "), "#f39c12"),
        ]:
            col = QVBoxLayout()
            l1 = QLabel(s_txt); l1.setStyleSheet("color: #a0a0b0; font-size: 11px;"); l1.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l2 = QLabel(s_val); l2.setStyleSheet(f"color: {s_color}; font-size: 15px; font-weight: bold;"); l2.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col.addWidget(l1); col.addWidget(l2)
            stats_lay.addLayout(col)
        lay.addWidget(stats_frame)

        sep = QFrame(); sep.setFixedHeight(1); sep.setStyleSheet("background: #0f3460; border: none;")
        lay.addWidget(sep)

        subtitulo = QLabel("DEBES TENER EN CAJA:")
        subtitulo.setStyleSheet("color: #a0a0b0; font-size: 12px; letter-spacing: 2px; font-weight: bold;")
        lay.addWidget(subtitulo)

        def fila_metodo(icono, nombre, monto, color, detalle=""):
            f = QFrame()
            f.setStyleSheet(f"QFrame {{ background: #16213e; border-radius: 8px; border-left: 3px solid {color}; }}")
            fl = QHBoxLayout(f)
            fl.setContentsMargins(14, 10, 14, 10)
            lbl_n = QLabel(f"{icono}  {nombre}")
            lbl_n.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold;")
            fl.addWidget(lbl_n)
            if detalle:
                lbl_d = QLabel(detalle); lbl_d.setStyleSheet("color: #606880; font-size: 11px;")
                fl.addWidget(lbl_d)
            fl.addStretch()
            lbl_m = QLabel(_p(monto))
            lbl_m.setFont(QFont("Arial", 16, QFont.Weight.Bold))
            lbl_m.setStyleSheet(f"color: {color};")
            fl.addWidget(lbl_m)
            lay.addWidget(f)

        detalle_ef = f"{_p(monto_apertura)} + ef.{_p(totales['efectivo'])} - gastos {_p(total_gastos)}" + (f" - emp. {_p(total_emp_previo)}" if total_emp_previo else "")
        fila_metodo("💵", "Efectivo",          efectivo_esperado,         "#27ae60", detalle_ef)
        fila_metodo("🏧", "Débito",            totales["debito"],         "#10b981")
        fila_metodo("💳", "Tarjeta",           totales["tarjeta"],        "#3498db")
        fila_metodo("📱", "Mercado Pago/QR",   totales["mercadopago_qr"], "#009ee3")
        fila_metodo("🏦", "Transferencia",     totales["transferencia"],  "#9b59b6")
        fila_metodo("💸", "Fiado (pendiente)", totales["fiado"],          "#e74c3c")

        sep2 = QFrame(); sep2.setFixedHeight(1); sep2.setStyleSheet("background: #0f3460; border: none;")
        lay.addWidget(sep2)

        resumen_frame = QFrame()
        resumen_frame.setStyleSheet("QFrame { background: #0f3460; border-radius: 8px; }")
        res_lay = QVBoxLayout(resumen_frame)
        res_lay.setContentsMargins(14, 10, 14, 10); res_lay.setSpacing(4)
        for txt, val, color in [
            ("Total vendido:",    _p(total_vendido),                            "#27ae60"),
            ("Fiado del turno:",  _p(totales['fiado']),                         "#e74c3c"),
            ("Gastos del turno:", f"-{_p(total_gastos)}",                       "#e74c3c"),
            ("Neto del turno:",   _p(total_vendido - total_gastos),             "#f39c12"),
        ]:
            rw = QHBoxLayout()
            l1 = QLabel(txt); l1.setStyleSheet("color: #a0a0b0; font-size: 13px;")
            l2 = QLabel(val); l2.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold;")
            rw.addWidget(l1); rw.addStretch(); rw.addWidget(l2)
            res_lay.addLayout(rw)
        lay.addWidget(resumen_frame)

        # ── PAGO DE EMPLEADOS ─────────────────────────────────────────────
        sep_emp = QFrame(); sep_emp.setFixedHeight(1)
        sep_emp.setStyleSheet("background: #0f3460; border: none;")
        lay.addWidget(sep_emp)

        lbl_emp = QLabel("👥 Pago de empleados (opcional)")
        lbl_emp.setStyleSheet("color: #a0a0b0; font-size: 13px; font-weight: bold;")
        lay.addWidget(lbl_emp)

        emp_frame = QFrame()
        emp_frame.setStyleSheet("QFrame { background: #0f3460; border-radius: 8px; }")
        emp_lay = QVBoxLayout(emp_frame)
        emp_lay.setContentsMargins(12, 10, 12, 10)
        emp_lay.setSpacing(6)

        # Hasta 5 filas de empleados: nombre + monto
        filas_emp = []
        for i in range(5):
            row_e = QHBoxLayout()
            lbl_n = QLabel(f"Empleado {i+1}:")
            lbl_n.setStyleSheet("color: #a0a0b0; font-size: 12px;")
            lbl_n.setFixedWidth(90)
            in_nombre = QLineEdit()
            in_nombre.setPlaceholderText("Nombre")
            in_nombre.setFixedHeight(34)
            in_nombre.setStyleSheet("QLineEdit { background: #16213e; border: 1px solid #9b59b6; border-radius: 6px; padding: 6px; color: white; font-size: 12px; }")
            in_monto = QLineEdit()
            in_monto.setPlaceholderText("$0")
            in_monto.setFixedWidth(90)
            in_monto.setFixedHeight(34)
            in_monto.setStyleSheet("QLineEdit { background: #16213e; border: 1px solid #9b59b6; border-radius: 6px; padding: 6px; color: white; font-size: 12px; }")
            row_e.addWidget(lbl_n)
            row_e.addWidget(in_nombre)
            row_e.addWidget(in_monto)
            emp_lay.addLayout(row_e)
            filas_emp.append((in_nombre, in_monto))

        lbl_total_emp = QLabel("Total empleados: $0")
        lbl_total_emp.setStyleSheet("color: #9b59b6; font-size: 13px; font-weight: bold;")
        emp_lay.addWidget(lbl_total_emp)
        lay.addWidget(emp_frame)

        def actualizar_total_emp():
            total = 0
            for in_n, in_m in filas_emp:
                try:
                    if in_n.text().strip() and in_m.text().strip():
                        total += float(in_m.text())
                except ValueError:
                    pass
            lbl_total_emp.setText(f"Total empleados: {_p(total)}")
            # Actualizar efectivo esperado con descuento de empleados
            ef_neto = efectivo_esperado - total
            input_declarado.setPlaceholderText(_p(ef_neto).lstrip("$"))

        for in_n, in_m in filas_emp:
            in_m.textChanged.connect(lambda _: actualizar_total_emp())

        row_decl = QHBoxLayout()
        lbl_d = QLabel("Efectivo contado ($):"); lbl_d.setStyleSheet("color: #a0a0b0; font-size: 13px;")
        row_decl.addWidget(lbl_d)
        input_declarado = QLineEdit()
        input_declarado.setPlaceholderText(_p(efectivo_esperado).lstrip("$"))
        input_declarado.setFixedWidth(140); input_declarado.setFixedHeight(38)
        input_declarado.setStyleSheet("QLineEdit { background: #0f3460; border: 1px solid #e94560; border-radius: 8px; padding: 8px; color: white; font-size: 14px; }")
        row_decl.addWidget(input_declarado)
        lay.addLayout(row_decl)

        btns = QHBoxLayout()
        btn_c = QPushButton("Cancelar"); btn_c.setFixedHeight(42)
        btn_c.setStyleSheet("QPushButton { background: transparent; color: #a0a0b0; border: 1px solid #a0a0b0; border-radius: 8px; }")
        btn_c.clicked.connect(dialog.reject); btns.addWidget(btn_c)

        btn_exp = QPushButton("Exportar .txt"); btn_exp.setFixedHeight(42)
        btn_exp.setStyleSheet("QPushButton { background: #0f3460; color: #3498db; border-radius: 8px; font-size: 13px; font-weight: bold; border: 1px solid #3498db; }")
        btns.addWidget(btn_exp)

        btn_ok = QPushButton("Confirmar cierre"); btn_ok.setFixedHeight(42)
        btn_ok.setStyleSheet("QPushButton { background: #27ae60; color: white; border-radius: 8px; font-size: 14px; font-weight: bold; }")
        btns.addWidget(btn_ok)
        lay.addLayout(btns)

        def _obtener_pagos_empleados():
            pagos = []
            for in_n, in_m in filas_emp:
                nombre = in_n.text().strip()
                if not nombre:
                    continue
                try:
                    monto = float(in_m.text())
                    if monto > 0:
                        pagos.append({"nombre": nombre, "monto": monto})
                except ValueError:
                    pass
            return pagos

        def _txt_cierre(decl=None, diff=None):
            from datetime import datetime
            ts = datetime.now().strftime("%Y-%m-%d %H:%M")
            # Usar pagos del dialog de empleados si los hay
            pagos_emp = list(getattr(self, '_pagos_empleados_guardados', []))
            total_emp = sum(p["monto"] for p in pagos_emp)
            ls = ["="*40, "   JUANA CASH - CIERRE DE CAJA", "="*40,
                  f"Fecha:       {ts}", f"Cajero:      {getattr(self,'nombre_cajero','?')}",
                  f"Tickets:     {cant_tickets}", f"Prom ticket: ${ticket_prom:,.2f}",
                  "-"*40,
                  f"Efectivo:    ${totales['efectivo']:,.2f}",
                  f"Debito:      ${totales['debito']:,.2f}",
                  f"Tarjeta:     ${totales['tarjeta']:,.2f}",
                  f"Mdo Pago:    ${totales['mercadopago_qr']:,.2f}",
                  f"Transfer.:   ${totales['transferencia']:,.2f}",
                  f"Fiado:       ${totales['fiado']:,.2f}",
                  "-"*40,
                  f"Total:       ${total_vendido:,.2f}",
                  f"Gastos:     -${total_gastos:,.2f}",
                  f"NETO:        ${total_vendido - total_gastos:,.2f}",
                  "-"*40,
                  f"Apertura:    ${monto_apertura:,.2f}",
                  f"Ef. esperad: ${efectivo_esperado:,.2f}"]
            if decl is not None:
                ls += [f"Ef. contado: ${decl:,.2f}", f"Diferencia:  ${diff:+,.2f}"]
            if pagos_emp:
                ls += ["-"*40, "PAGOS DE EMPLEADOS:"]
                for p in pagos_emp:
                    ls.append(f"  {p['nombre']:20s} ${p['monto']:,.2f}")
                ls.append(f"  Total empleados:     ${total_emp:,.2f}")
                ls.append(f"  Efectivo neto:       ${(efectivo_esperado if decl is None else decl) - total_emp:,.2f}")
            ls += ["="*40]
            return "\n".join(ls)


        def exportar():
            import os; from datetime import datetime
            ruta = os.path.join(os.path.expanduser("~"), "JuanaCash_Tickets",
                                f"cierre_{datetime.now().strftime('%Y%m%d_%H%M')}.txt")
            os.makedirs(os.path.dirname(ruta), exist_ok=True)
            with open(ruta, "w", encoding="utf-8") as fh: fh.write(_txt_cierre())
            QMessageBox.information(dialog, "Exportado", f"Guardado en:\n{ruta}")

        btn_exp.clicked.connect(exportar)

        def confirmar_cierre():
            try:
                monto_declarado = float(input_declarado.text() or efectivo_esperado)
            except ValueError:
                monto_declarado = efectivo_esperado
            diferencia = monto_declarado - efectivo_esperado
            try:
                r = requests.post(f"{API_URL}/caja/cerrar/{self.turno_actual['id']}",
                                   json={"monto_cierre": monto_declarado,
                                         "pagos_empleados": self._pagos_empleados_guardados}, timeout=5)
                if r.status_code == 200:
                    try:
                        requests.post(f"{API_URL}/sesiones/registrar", json={
                            "usuario_id": self.usuario_id, "nombre_cajero": self.nombre_cajero,
                            "accion": "CIERRE_CAJA",
                            "detalle": f"Vendido: ${total_vendido:.2f} | Tickets: {cant_tickets} | Dif: ${diferencia:.2f}"
                        }, timeout=3)
                    except Exception: pass
                    try:
                        import os; from datetime import datetime
                        ruta = os.path.join(os.path.expanduser("~"), "JuanaCash_Tickets",
                                            f"cierre_{datetime.now().strftime('%Y%m%d_%H%M')}.txt")
                        os.makedirs(os.path.dirname(ruta), exist_ok=True)
                        with open(ruta, "w", encoding="utf-8") as fh: fh.write(_txt_cierre(monto_declarado, diferencia))
                    except Exception: pass
                    dialog.accept()
                    self.turno_actual = None
                    self.lbl_estado.setText("Caja cerrada")
                    self.lbl_estado.setStyleSheet("color: #a0a0b0; font-size: 16px; font-weight: bold;")
                    self.lbl_apertura.setText("")
                    self.lbl_total_caja.setText("Total acumulado: $0")
                    self._pagos_empleados_guardados = []
                    self.btn_abrir.setEnabled(True); self.btn_cerrar.setEnabled(False)
                    for lbl in self.cards_metodo.values(): lbl.setText("$0")
                    self.lbl_ef_caja.setText("💵 Efectivo en caja: —")
                    color_dif = "OK" if abs(diferencia) < 100 else "REVISAR"
                    QMessageBox.information(self, "Caja cerrada",
                        f"Cierre confirmado\n{color_dif} Diferencia: ${diferencia:+.2f}\n"
                        f"Tickets: {cant_tickets} | Promedio: ${ticket_prom:,.2f}")
            except Exception:
                QMessageBox.critical(dialog, "Error", "No se puede conectar al servidor")

        btn_ok.clicked.connect(confirmar_cierre)
        dialog.exec()


    def registrar_gasto(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("💸 Registrar gasto")
        dialog.setMinimumWidth(360)
        dialog.setStyleSheet("background-color: #1a1a2e; color: white;")
        lay = QVBoxLayout(dialog)
        lay.setSpacing(12)
        for lbl_txt in ["Descripción del gasto:", "Monto ($):", "Categoría:"]:
            lbl = QLabel(lbl_txt)
            lbl.setStyleSheet("color: #a0a0b0; font-size: 13px;")
            lay.addWidget(lbl)
            if lbl_txt == "Descripción del gasto:":
                input_desc = QLineEdit()
                input_desc.setPlaceholderText("Ej: Bolsas, nafta, insumos...")
                input_desc.setFixedHeight(44)
                input_desc.setStyleSheet("QLineEdit { background: #0f3460; border: 1px solid #9b59b6; border-radius: 8px; padding: 10px; color: white; font-size: 14px; }")
                lay.addWidget(input_desc)
            elif lbl_txt == "Monto ($):":
                input_monto = QLineEdit()
                input_monto.setFixedHeight(44)
                input_monto.setStyleSheet("QLineEdit { background: #0f3460; border: 1px solid #9b59b6; border-radius: 8px; padding: 10px; color: white; font-size: 18px; font-weight: bold; }")
                lay.addWidget(input_monto)
            elif lbl_txt == "Categoría:":
                combo = QComboBox()
                combo.addItems(["Insumos", "Limpieza", "Transporte", "Servicios", "Personal", "Impuestos", "Otro"])
                combo.setFixedHeight(40)
                combo.setStyleSheet("QComboBox { background: #0f3460; border: 1px solid #9b59b6; border-radius: 8px; padding: 8px; color: white; font-size: 14px; } QComboBox::drop-down { border: none; } QComboBox QAbstractItemView { background: #0f3460; color: white; selection-background-color: #9b59b6; }")
                lay.addWidget(combo)
        btns = QHBoxLayout()
        btn_c = QPushButton("Cancelar")
        btn_c.setFixedHeight(40)
        btn_c.setStyleSheet("QPushButton { background: transparent; color: #a0a0b0; border: 1px solid #a0a0b0; border-radius: 8px; }")
        btn_c.clicked.connect(dialog.reject)
        btns.addWidget(btn_c)
        btn_ok = QPushButton("✅ Registrar")
        btn_ok.setFixedHeight(40)
        btn_ok.setStyleSheet("QPushButton { background: #9b59b6; color: white; border-radius: 8px; font-size: 14px; font-weight: bold; }")
        btns.addWidget(btn_ok)
        lay.addLayout(btns)
        def confirmar():
            desc = input_desc.text().strip()
            if not desc:
                QMessageBox.warning(dialog, "Error", "Ingresá una descripción")
                return
            try:
                monto = float(input_monto.text())
            except ValueError:
                QMessageBox.warning(dialog, "Error", "Ingresá un monto válido")
                return
            if monto <= 0:
                QMessageBox.warning(dialog, "Error", "El monto debe ser mayor a cero")
                return
            try:
                r = requests.post(f"{API_URL}/gastos/", json={"descripcion": desc, "monto": monto, "categoria": combo.currentText(), "usuario_id": self.usuario_id}, timeout=5)
                if r.status_code == 200:
                    dialog.accept()
                    QMessageBox.information(self, "✅", f"Gasto registrado: ${monto:.2f}")
            except Exception:
                QMessageBox.critical(dialog, "Error", "No se puede conectar")
        btn_ok.clicked.connect(confirmar)
        input_monto.returnPressed.connect(confirmar)
        dialog.exec()

    def anular_venta(self, venta_id, numero):
        dialog = AnularDialog(self, numero)
        if dialog.exec():
            motivo = dialog.combo_motivo.currentText()
            password = dialog.input_password.text().strip()
            if not password:
                QMessageBox.warning(self, "Error", "Ingresá la contraseña")
                return
            try:
                r = requests.post(f"{API_URL}/ventas/{venta_id}/anular", json={
                    "motivo": motivo,
                    "password_admin": password,
                    "usuario_id": self.usuario_id
                }, timeout=5)
                if r.status_code == 200:
                    try:
                        requests.post(f"{API_URL}/sesiones/registrar", json={"usuario_id": self.usuario_id, "nombre_cajero": self.nombre_cajero, "accion": "ANULACION", "detalle": f"Ticket #{numero} — Motivo: {motivo}"}, timeout=3)
                    except Exception:
                        pass
                    QMessageBox.information(self, "✅", f"Ticket #{numero} anulado correctamente")
                    self.actualizar_ventas()
                elif r.status_code == 401:
                    QMessageBox.critical(self, "Error", "Contraseña incorrecta")
                elif r.status_code == 403:
                    QMessageBox.critical(self, "Error", "Solo admin o encargado pueden anular")
                else:
                    QMessageBox.critical(self, "Error", r.json().get("detail", "Error al anular"))
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def reimprimir_ticket(self, venta_id, numero):
        try:
            r = requests.get(f"{API_URL}/ventas/{venta_id}/detalle", timeout=5)
            if r.status_code != 200:
                QMessageBox.warning(self, "Error", "No se pudo obtener el ticket")
                return
            data = r.json()
            try:
                from ui.pantallas.impresora import imprimir_ticket
                ok, msg = imprimir_ticket(
                    venta={"numero": data["numero"], "fecha": data["fecha"]},
                    items=data["items"],
                    metodo_pago=data["metodo_pago"],
                    descuento=data.get("descuento", 0),
                    recargo=data.get("recargo", 0),
                )
                if ok:
                    QMessageBox.information(self, "🖨 Impreso", f"Ticket #{numero} impreso correctamente")
                else:
                    QMessageBox.warning(self, "⚠️ Impresora", msg)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al imprimir:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def actualizar_ventas(self):
        try:
            r = requests.get(f"{API_URL}/reportes/hoy", timeout=5)
            if r.status_code == 200:
                datos = r.json()
                total = datos.get("total_vendido", 0)
                self.lbl_total_caja.setText(f"Total acumulado: ${total:,.0f}".replace(",", "."))
                ventas = datos.get("ventas", [])
                # desglose_metodos ya suma p.monto por método, incluye cobros mixtos
                desglose = datos.get("desglose_metodos", {})
                self.ventas_data = ventas
                self.tabla.setRowCount(len(ventas))
                nombres_m = {
                    "efectivo":       "💵 Efectivo",
                    "debito":         "🏧 Débito",
                    "tarjeta":        "💳 Tarjeta",
                    "mercadopago_qr": "📱 QR/MP",
                    "transferencia":  "🏦 Transf.",
                    "fiado":          "💸 Fiado",
                }
                for i, v in enumerate(ventas):
                    self.tabla.setItem(i, 0, QTableWidgetItem(v["numero"]))
                    item_total = QTableWidgetItem(f"${float(v['total']):,.0f}".replace(",", "."))
                    if v.get("estado") == "anulada":
                        item_total.setForeground(Qt.GlobalColor.red)
                    self.tabla.setItem(i, 1, item_total)
                    metodo = v.get("metodo_pago", "efectivo")
                    metodo_sec = v.get("metodo_secundario")
                    monto_sec = float(v.get("monto_secundario", 0))
                    if metodo_sec and monto_sec > 0:
                        nombres_c = {"efectivo": "💵Ef", "debito": "🏧Déb", "tarjeta": "💳Tarj",
                                     "mercadopago_qr": "📱QR", "transferencia": "🏦Tr", "fiado": "💸Fiado"}
                        metodo_str = f"{nombres_c.get(metodo, metodo)}+{nombres_c.get(metodo_sec, metodo_sec)}"
                    else:
                        metodo_str = nombres_m.get(metodo, metodo)
                    self.tabla.setItem(i, 2, QTableWidgetItem(metodo_str))

                    origen = v.get("origen", "mostrador")
                    if origen == "celular":
                        item_origen = QTableWidgetItem("📱 Celular")
                        item_origen.setForeground(Qt.GlobalColor.cyan)
                    else:
                        item_origen = QTableWidgetItem("🖥 Mostrador")
                        item_origen.setForeground(Qt.GlobalColor.lightGray)
                    self.tabla.setItem(i, 3, item_origen)

                    estado = v.get("estado", "completada")
                    item_estado = QTableWidgetItem("✅ OK" if estado == "completada" else "🚫 Anulada")
                    item_estado.setForeground(Qt.GlobalColor.green if estado == "completada" else Qt.GlobalColor.red)
                    self.tabla.setItem(i, 4, item_estado)
                    self.tabla.setItem(i, 5, QTableWidgetItem(v["fecha"][11:16]))
                    if estado == "completada":
                        btn_anular = QPushButton("🚫 Anular")
                        btn_anular.setFixedHeight(26)
                        btn_anular.setStyleSheet("QPushButton { background: #e94560; color: white; border-radius: 4px; font-size: 11px; padding: 0 6px; }")
                        btn_anular.clicked.connect(lambda _, vid=v["id"], num=v["numero"]: self.anular_venta(vid, num))
                        self.tabla.setCellWidget(i, 6, btn_anular)
                    btn_reimp = QPushButton("🖨")
                    btn_reimp.setFixedHeight(26)
                    btn_reimp.setToolTip("Reimprimir ticket")
                    btn_reimp.setStyleSheet(f"QPushButton {{ background: {BG_CARD}; color: {TEXT_MAIN}; border-radius: 4px; font-size: 13px; border: 1px solid {BORDER}; }}")
                    btn_reimp.clicked.connect(lambda _, vid=v["id"], num=v["numero"]: self.reimprimir_ticket(vid, num))
                    self.tabla.setCellWidget(i, 7, btn_reimp)
                # Cards por método — usa desglose del server (correcto con cobros mixtos)
                for key, lbl in self.cards_metodo.items():
                    lbl.setText(f"${float(desglose.get(key, 0)):,.0f}".replace(",", "."))
                try:
                    r_gastos = requests.get(f"{API_URL}/gastos/hoy", timeout=5)
                    total_gastos = float(r_gastos.json().get("total", 0)) if r_gastos.status_code == 200 else 0
                except Exception:
                    total_gastos = 0
                monto_apertura = float((self.turno_actual or {}).get("monto_apertura", 0))
                ef_caja = monto_apertura + float(desglose.get("efectivo", 0)) - total_gastos
                self.lbl_ef_caja.setText(f"💵 Efectivo en caja: {_p(ef_caja)}")
        except Exception:
            pass