import requests
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QLineEdit, QFrame, QMessageBox,
                              QTableWidget, QTableWidgetItem, QHeaderView,
                              QDialog, QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from datetime import datetime

API_URL = "http://127.0.0.1:8000"

class AnularDialog(QDialog):
    def __init__(self, parent=None, ticket=""):
        super().__init__(parent)
        self.setWindowTitle(f"🚫 Anular ticket {ticket}")
        self.setMinimumWidth(380)
        self.setStyleSheet("background-color: #1a1a2e; color: white;")
        self.setup_ui(ticket)

    def setup_ui(self, ticket):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        lbl = QLabel(f"⚠️ Anular ticket #{ticket}")
        lbl.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        lbl.setStyleSheet("color: #e94560;")
        layout.addWidget(lbl)
        lbl2 = QLabel("Esta acción devuelve el stock y no puede deshacerse.")
        lbl2.setStyleSheet("color: #a0a0b0; font-size: 12px;")
        layout.addWidget(lbl2)
        lbl_m = QLabel("Motivo de anulación:")
        lbl_m.setStyleSheet("color: #a0a0b0; font-size: 13px;")
        layout.addWidget(lbl_m)
        self.combo_motivo = QComboBox()
        self.combo_motivo.addItems(["Error de carga", "Producto devuelto", "Error de precio", "Solicitud del cliente", "Otro"])
        self.combo_motivo.setFixedHeight(40)
        self.combo_motivo.setStyleSheet("QComboBox { background: #0f3460; border: 1px solid #e94560; border-radius: 8px; padding: 8px; color: white; } QComboBox QAbstractItemView { background: #0f3460; color: white; selection-background-color: #e94560; }")
        layout.addWidget(self.combo_motivo)
        lbl_p = QLabel("Contraseña de admin o encargado:")
        lbl_p.setStyleSheet("color: #a0a0b0; font-size: 13px;")
        layout.addWidget(lbl_p)
        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password.setFixedHeight(44)
        self.input_password.setStyleSheet("QLineEdit { background: #0f3460; border: 1px solid #e94560; border-radius: 8px; padding: 10px; color: white; font-size: 16px; }")
        layout.addWidget(self.input_password)
        btns = QHBoxLayout()
        btn_c = QPushButton("Cancelar")
        btn_c.setFixedHeight(40)
        btn_c.setStyleSheet("QPushButton { background: transparent; color: #a0a0b0; border: 1px solid #a0a0b0; border-radius: 8px; }")
        btn_c.clicked.connect(self.reject)
        btns.addWidget(btn_c)
        btn_ok = QPushButton("🚫 Confirmar anulación")
        btn_ok.setFixedHeight(40)
        btn_ok.setStyleSheet("QPushButton { background: #e94560; color: white; border-radius: 8px; font-size: 14px; font-weight: bold; }")
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
        self.setup_ui()

    def set_usuario(self, usuario):
        self.usuario_id = usuario.get("id", 1)
        self.nombre_cajero = usuario.get("nombre", "")

    def setup_ui(self):
        self.setStyleSheet("background-color: #1a1a2e; color: white;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        titulo = QLabel("🏧 Caja")
        titulo.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        titulo.setStyleSheet("color: white;")
        layout.addWidget(titulo)
        self.card_estado = QFrame()
        self.card_estado.setStyleSheet("QFrame { background: #16213e; border-radius: 12px; border-left: 4px solid #e94560; }")
        self.card_estado.setMinimumHeight(110)
        card_layout = QVBoxLayout(self.card_estado)
        card_layout.setContentsMargins(24, 16, 24, 16)
        self.lbl_estado = QLabel("⚪ Caja cerrada")
        self.lbl_estado.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.lbl_estado.setStyleSheet("color: #a0a0b0;")
        card_layout.addWidget(self.lbl_estado)
        self.lbl_apertura = QLabel("")
        self.lbl_apertura.setStyleSheet("color: #a0a0b0; font-size: 13px;")
        card_layout.addWidget(self.lbl_apertura)
        self.lbl_total_caja = QLabel("Total acumulado: $0.00")
        self.lbl_total_caja.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.lbl_total_caja.setStyleSheet("color: #e94560;")
        card_layout.addWidget(self.lbl_total_caja)
        layout.addWidget(self.card_estado)
        desglose_frame = QFrame()
        desglose_frame.setStyleSheet("QFrame { background: #16213e; border-radius: 10px; }")
        desglose_layout = QHBoxLayout(desglose_frame)
        desglose_layout.setContentsMargins(16, 12, 16, 12)
        desglose_layout.setSpacing(8)
        self.cards_metodo = {}
        metodos = [
            ("💵", "Efectivo",      "efectivo",        "#27ae60"),
            ("💳", "Tarjeta",       "tarjeta",          "#3498db"),
            ("📱", "QR / MP",       "mercadopago_qr",   "#009ee3"),
            ("🏦", "Transf.",       "transferencia",    "#9b59b6"),
            ("💸", "Fiado",         "fiado",            "#e74c3c"),
        ]
        for icono, nombre, key, color in metodos:
            card = QFrame()
            card.setStyleSheet(f"QFrame {{ background: #0f3460; border-radius: 8px; border-left: 3px solid {color}; }}")
            c_layout = QVBoxLayout(card)
            c_layout.setContentsMargins(10, 8, 10, 8)
            lbl_n = QLabel(f"{icono} {nombre}")
            lbl_n.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: bold;")
            c_layout.addWidget(lbl_n)
            lbl_v = QLabel("$0.00")
            lbl_v.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            lbl_v.setStyleSheet(f"color: {color};")
            c_layout.addWidget(lbl_v)
            desglose_layout.addWidget(card)
            self.cards_metodo[key] = lbl_v
        layout.addWidget(desglose_frame)
        btns = QHBoxLayout()
        lbl_monto = QLabel("Monto inicial ($):")
        lbl_monto.setStyleSheet("color: #a0a0b0; font-size: 14px;")
        btns.addWidget(lbl_monto)
        self.input_monto = QLineEdit()
        self.input_monto.setPlaceholderText("5000")
        self.input_monto.setFixedWidth(130)
        self.input_monto.setFixedHeight(40)
        self.input_monto.setStyleSheet("QLineEdit { background: #0f3460; border: 1px solid #e94560; border-radius: 8px; padding: 8px; color: white; font-size: 14px; }")
        btns.addWidget(self.input_monto)
        self.btn_abrir = QPushButton("🔓 Abrir caja")
        self.btn_abrir.setFixedHeight(40)
        self.btn_abrir.setStyleSheet("QPushButton { background: #27ae60; color: white; border-radius: 8px; padding: 0 20px; font-size: 14px; font-weight: bold; }")
        self.btn_abrir.clicked.connect(self.abrir_caja)
        btns.addWidget(self.btn_abrir)
        self.btn_cerrar = QPushButton("🔒 Cerrar caja")
        self.btn_cerrar.setFixedHeight(40)
        self.btn_cerrar.setEnabled(False)
        self.btn_cerrar.setStyleSheet("QPushButton { background: #e94560; color: white; border-radius: 8px; padding: 0 20px; font-size: 14px; font-weight: bold; } QPushButton:disabled { background: #555; color: #888; }")
        self.btn_cerrar.clicked.connect(self.cerrar_caja)
        btns.addWidget(self.btn_cerrar)
        btn_gasto = QPushButton("💸 Registrar gasto")
        btn_gasto.setFixedHeight(40)
        btn_gasto.setStyleSheet("QPushButton { background: #9b59b6; color: white; border-radius: 8px; padding: 0 16px; font-size: 13px; font-weight: bold; }")
        btn_gasto.clicked.connect(self.registrar_gasto)
        btns.addWidget(btn_gasto)
        btns.addStretch()
        layout.addLayout(btns)
        lbl_resumen = QLabel("Ventas del turno")
        lbl_resumen.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        lbl_resumen.setStyleSheet("color: #a0a0b0;")
        layout.addWidget(lbl_resumen)
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(7)
        self.tabla.setHorizontalHeaderLabels(["Ticket", "Total", "Método", "Origen", "Estado", "Hora", "Anular"])
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabla.setColumnWidth(1, 110)
        self.tabla.setColumnWidth(2, 100)
        self.tabla.setColumnWidth(3, 110)
        self.tabla.setColumnWidth(4, 90)
        self.tabla.setColumnWidth(5, 60)
        self.tabla.setColumnWidth(6, 90)
        self.tabla.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.tabla.setStyleSheet("QTableWidget { background: #16213e; border: 1px solid #0f3460; border-radius: 8px; gridline-color: #0f3460; } QHeaderView::section { background: #0f3460; color: #a0a0b0; padding: 8px; border: none; } QTableWidgetItem { color: white; padding: 8px; }")
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.tabla)

        # ── HISTORIAL DE CIERRES ─────────────────────────────────────────────
        sep_h = QFrame(); sep_h.setFixedHeight(1)
        sep_h.setStyleSheet("background: #0f3460; border: none;")
        layout.addWidget(sep_h)

        hdr_hist = QHBoxLayout()
        lbl_hist = QLabel("📋 Historial de cierres")
        lbl_hist.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        lbl_hist.setStyleSheet("color: #a0a0b0;")
        hdr_hist.addWidget(lbl_hist)
        hdr_hist.addStretch()
        btn_hist_ref = QPushButton("🔄")
        btn_hist_ref.setFixedSize(32, 32)
        btn_hist_ref.setStyleSheet("QPushButton { background: #16213e; color: white; border-radius: 6px; }")
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
        self.tabla_historial.setStyleSheet("QTableWidget { background: #16213e; border: 1px solid #0f3460; border-radius: 8px; gridline-color: #0f3460; } QHeaderView::section { background: #0f3460; color: #a0a0b0; padding: 6px; border: none; } QTableWidgetItem { color: white; padding: 6px; }")
        self.tabla_historial.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.tabla_historial)

    def showEvent(self, event):
        super().showEvent(event)
        self.cargar_historial()

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
                f"${float(c.get('monto_apertura',0)):,.0f}",
                f"${float(c.get('monto_cierre_calculado',0)):,.0f}",
                f"${float(c.get('monto_cierre_declarado',0)):,.0f}",
                f"${diff:+,.0f}",
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
                self.lbl_apertura.setText(f"Apertura: {datetime.now().strftime('%H:%M')} — Cajero: {self.nombre_cajero} — Monto inicial: ${monto:.2f}")
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
        totales = {"efectivo": 0, "tarjeta": 0, "mercadopago_qr": 0, "transferencia": 0, "fiado": 0}
        cant_tickets = 0
        cant_celular = 0
        for v in ventas:
            if v.get("estado") == "completada":
                cant_tickets += 1
                if v.get("origen", "") in ("celular", "celular_offline"):
                    cant_celular += 1
                m = v.get("metodo_pago", "efectivo")
                if m in totales:
                    totales[m] += float(v.get("total", 0))

        total_vendido = datos_hoy.get("total_vendido", 0)
        total_gastos  = datos_gastos.get("total", 0)
        ticket_prom   = (total_vendido / cant_tickets) if cant_tickets > 0 else 0

        try:
            monto_apertura = float(self.turno_actual.get("monto_apertura", 0))
        except Exception:
            monto_apertura = 0

        efectivo_esperado = monto_apertura + totales["efectivo"] - total_gastos

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
            ("Promedio", f"${ticket_prom:,.0f}", "#27ae60"),
            ("Apertura", str(self.turno_actual.get("fecha_apertura","?"))[:16].replace("T"," "), "#f39c12"),
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
            lbl_m = QLabel(f"${monto:,.2f}")
            lbl_m.setFont(QFont("Arial", 16, QFont.Weight.Bold))
            lbl_m.setStyleSheet(f"color: {color};")
            fl.addWidget(lbl_m)
            lay.addWidget(f)

        detalle_ef = f"apertura ${monto_apertura:,.0f} + ventas ${totales['efectivo']:,.0f} - gastos ${total_gastos:,.0f}"
        fila_metodo("💵", "Efectivo",        efectivo_esperado,         "#27ae60", detalle_ef)
        fila_metodo("💳", "Tarjeta",          totales["tarjeta"],        "#3498db")
        fila_metodo("📱", "Mercado Pago/QR",  totales["mercadopago_qr"], "#009ee3")
        fila_metodo("🏦", "Transferencia",    totales["transferencia"],  "#9b59b6")
        fila_metodo("💸", "Fiado (pendiente)", totales["fiado"],         "#e74c3c")

        sep2 = QFrame(); sep2.setFixedHeight(1); sep2.setStyleSheet("background: #0f3460; border: none;")
        lay.addWidget(sep2)

        resumen_frame = QFrame()
        resumen_frame.setStyleSheet("QFrame { background: #0f3460; border-radius: 8px; }")
        res_lay = QVBoxLayout(resumen_frame)
        res_lay.setContentsMargins(14, 10, 14, 10); res_lay.setSpacing(4)
        for txt, val, color in [
            ("Total vendido:",    f"${total_vendido:,.2f}",               "#27ae60"),
            ("Fiado del turno:",  f"${totales['fiado']:,.2f}",            "#e74c3c"),
            ("Gastos del turno:", f"-${total_gastos:,.2f}",               "#e74c3c"),
            ("Neto del turno:",   f"${total_vendido - total_gastos:,.2f}", "#f39c12"),
        ]:
            rw = QHBoxLayout()
            l1 = QLabel(txt); l1.setStyleSheet("color: #a0a0b0; font-size: 13px;")
            l2 = QLabel(val); l2.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold;")
            rw.addWidget(l1); rw.addStretch(); rw.addWidget(l2)
            res_lay.addLayout(rw)
        lay.addWidget(resumen_frame)

        row_decl = QHBoxLayout()
        lbl_d = QLabel("Efectivo contado ($):"); lbl_d.setStyleSheet("color: #a0a0b0; font-size: 13px;")
        row_decl.addWidget(lbl_d)
        input_declarado = QLineEdit()
        input_declarado.setPlaceholderText(f"{efectivo_esperado:.2f}")
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

        def _txt_cierre(decl=None, diff=None):
            from datetime import datetime
            ts = datetime.now().strftime("%Y-%m-%d %H:%M")
            ls = ["="*40, "   JUANA CASH - CIERRE DE CAJA", "="*40,
                  f"Fecha:       {ts}", f"Cajero:      {getattr(self,'nombre_cajero','?')}",
                  f"Tickets:     {cant_tickets}", f"Prom ticket: ${ticket_prom:,.2f}",
                  "-"*40,
                  f"Efectivo:    ${totales['efectivo']:,.2f}",
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
                                   json={"monto_cierre": monto_declarado}, timeout=5)
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
                    self.lbl_total_caja.setText("Total acumulado: $0.00")
                    self.btn_abrir.setEnabled(True); self.btn_cerrar.setEnabled(False)
                    for lbl in self.cards_metodo.values(): lbl.setText("$0.00")
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

    def actualizar_ventas(self):
        try:
            r = requests.get(f"{API_URL}/reportes/hoy", timeout=5)
            if r.status_code == 200:
                datos = r.json()
                total = datos.get("total_vendido", 0)
                self.lbl_total_caja.setText(f"Total acumulado: ${total:.2f}")
                ventas = datos.get("ventas", [])
                self.ventas_data = ventas
                self.tabla.setRowCount(len(ventas))
                totales_metodo = {"efectivo": 0, "tarjeta": 0, "mercadopago_qr": 0, "transferencia": 0, "fiado": 0}
                nombres_m = {
                    "efectivo":       "💵 Efectivo",
                    "tarjeta":        "💳 Tarjeta",
                    "mercadopago_qr": "📱 QR/MP",
                    "transferencia":  "🏦 Transf.",
                    "fiado":          "💸 Fiado",
                }
                for i, v in enumerate(ventas):
                    self.tabla.setItem(i, 0, QTableWidgetItem(v["numero"]))
                    item_total = QTableWidgetItem(f"${float(v['total']):.2f}")
                    if v.get("estado") == "anulada":
                        item_total.setForeground(Qt.GlobalColor.red)
                    self.tabla.setItem(i, 1, item_total)
                    metodo = v.get("metodo_pago", "efectivo")
                    self.tabla.setItem(i, 2, QTableWidgetItem(nombres_m.get(metodo, metodo)))

                    # Columna Origen — diferencia celular vs mostrador
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
                    if metodo in totales_metodo and estado == "completada":
                        totales_metodo[metodo] += float(v["total"])
                for key, lbl in self.cards_metodo.items():
                    lbl.setText(f"${totales_metodo.get(key, 0):.2f}")
        except Exception:
            pass