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
            ("💵", "Efectivo", "efectivo", "#27ae60"),
            ("💳", "Tarjeta", "tarjeta", "#3498db"),
            ("📱", "QR / MP", "mercadopago_qr", "#009ee3"),
            ("🏦", "Transferencia", "transferencia", "#9b59b6"),
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
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels(["Ticket", "Total", "Método de pago", "Estado", "Hora", "Anular"])
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabla.setColumnWidth(5, 120)
        self.tabla.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.tabla.setStyleSheet("QTableWidget { background: #16213e; border: 1px solid #0f3460; border-radius: 8px; gridline-color: #0f3460; } QHeaderView::section { background: #0f3460; color: #a0a0b0; padding: 8px; border: none; } QTableWidgetItem { color: white; padding: 8px; }")
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.tabla)

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
            monto_cierre = float(self.input_monto.text() or 0)
        except ValueError:
            monto_cierre = 0
        try:
            r_hoy = requests.get(f"{API_URL}/reportes/hoy", timeout=5)
            total_calculado = r_hoy.json().get("total_vendido", 0) if r_hoy.status_code == 200 else 0
        except Exception:
            total_calculado = 0
        diferencia = monto_cierre - total_calculado
        color_dif = "✅" if abs(diferencia) < 100 else "⚠️"
        respuesta = QMessageBox.question(self, "🔒 Cerrar caja",
            f"RESUMEN DE CIERRE\n{'═' * 30}\nTotal calculado: ${total_calculado:.2f}\nMonto declarado: ${monto_cierre:.2f}\n{color_dif} Diferencia: ${diferencia:.2f}\n\n¿Confirmás el cierre?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if respuesta == QMessageBox.StandardButton.Yes:
            try:
                r = requests.post(f"{API_URL}/caja/cerrar/{self.turno_actual['id']}", json={"monto_cierre": monto_cierre}, timeout=5)
                if r.status_code == 200:
                    try:
                        requests.post(f"{API_URL}/sesiones/registrar", json={"usuario_id": self.usuario_id, "nombre_cajero": self.nombre_cajero, "accion": "CIERRE_CAJA", "detalle": f"Total: ${total_calculado:.2f} | Declarado: ${monto_cierre:.2f} | Dif: ${diferencia:.2f}"}, timeout=3)
                    except Exception:
                        pass
                    try:
                        import backup
                        backup.hacer_backup()
                    except Exception:
                        pass
                    QMessageBox.information(self, "✅ Caja cerrada", f"Caja cerrada correctamente\nTotal: ${total_calculado:.2f}\n{'✅ Sin diferencia' if abs(diferencia) < 1 else f'Diferencia: ${diferencia:.2f}'}")
                    self.turno_actual = None
                    self.lbl_estado.setText("⚪ Caja cerrada")
                    self.lbl_estado.setStyleSheet("color: #a0a0b0; font-size: 16px; font-weight: bold;")
                    self.lbl_apertura.setText("")
                    self.lbl_total_caja.setText("Total acumulado: $0.00")
                    self.btn_abrir.setEnabled(True)
                    self.btn_cerrar.setEnabled(False)
                    for lbl in self.cards_metodo.values():
                        lbl.setText("$0.00")
            except Exception:
                QMessageBox.critical(self, "Error", "No se puede conectar al servidor")

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
                totales_metodo = {"efectivo": 0, "tarjeta": 0, "mercadopago_qr": 0, "transferencia": 0}
                nombres_m = {"efectivo": "💵 Efectivo", "tarjeta": "💳 Tarjeta", "mercadopago_qr": "📱 QR/MP", "transferencia": "🏦 Transf."}
                for i, v in enumerate(ventas):
                    self.tabla.setItem(i, 0, QTableWidgetItem(v["numero"]))
                    item_total = QTableWidgetItem(f"${float(v['total']):.2f}")
                    if v.get("estado") == "anulada":
                        item_total.setForeground(Qt.GlobalColor.red)
                    self.tabla.setItem(i, 1, item_total)
                    metodo = v.get("metodo_pago", "efectivo")
                    self.tabla.setItem(i, 2, QTableWidgetItem(nombres_m.get(metodo, metodo)))
                    estado = v.get("estado", "completada")
                    item_estado = QTableWidgetItem("✅ OK" if estado == "completada" else "🚫 Anulada")
                    item_estado.setForeground(Qt.GlobalColor.green if estado == "completada" else Qt.GlobalColor.red)
                    self.tabla.setItem(i, 3, item_estado)
                    self.tabla.setItem(i, 4, QTableWidgetItem(v["fecha"][11:16]))
                    if estado == "completada":
                        btn_anular = QPushButton("🚫 Anular")
                        btn_anular.setFixedHeight(26)
                        btn_anular.setStyleSheet("QPushButton { background: #e94560; color: white; border-radius: 4px; font-size: 11px; padding: 0 6px; }")
                        btn_anular.clicked.connect(lambda _, vid=v["id"], num=v["numero"]: self.anular_venta(vid, num))
                        self.tabla.setCellWidget(i, 5, btn_anular)
                    if metodo in totales_metodo and estado == "completada":
                        totales_metodo[metodo] += float(v["total"])
                for key, lbl in self.cards_metodo.items():
                    lbl.setText(f"${totales_metodo.get(key, 0):.2f}")
        except Exception:
            pass