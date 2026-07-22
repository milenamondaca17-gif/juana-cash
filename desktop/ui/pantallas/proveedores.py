import requests
import threading
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QFrame, QHeaderView, QTableWidget, QTableWidgetItem, QMessageBox,
    QDialog, QFormLayout, QComboBox, QDoubleSpinBox, QTabWidget,
    QTextEdit, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

API_URL = "http://127.0.0.1:8000"

from ui.theme import get_tema as _gt
_T = _gt()
_BG = _T["bg_app"]; _CARD = _T["bg_card"]; _TXT = _T["text_main"]
_MUT = _T["text_muted"]; _PRI = _T["primary"]; _DGR = _T["danger"]
_BOR = _T["border"]; _OK = _T["success"]; _WARN = _T["warning"]

def _p(v):
    return f"${float(v):,.0f}".replace(",", ".")

DIAS = ["", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
CONDICIONES = ["contado", "7dias", "15dias", "30dias"]
CONDICIONES_LABEL = {"contado": "Contado", "7dias": "7 días", "15dias": "15 días", "30dias": "30 días"}
METODOS_PAGO = ["efectivo", "transferencia", "cheque", "debito"]
METODOS_LABEL = {"efectivo": "💵 Efectivo", "transferencia": "🏦 Transferencia", "cheque": "📄 Cheque", "debito": "💳 Débito/Tarjeta"}

_estilo_inp = lambda: f"background:{_T['bg_input']}; border:1.5px solid {_BOR}; border-radius:8px; padding:6px 10px; color:{_TXT}; font-size:13px;"


# ── Dialog agregar/editar proveedor ──────────────────────────────────────────

class ProveedorDialog(QDialog):
    def __init__(self, parent=None, proveedor=None):
        super().__init__(parent)
        self.proveedor = proveedor
        self.setWindowTitle("✏️ Editar proveedor" if proveedor else "➕ Nuevo proveedor")
        self.setMinimumWidth(460)
        self.setStyleSheet(f"background:{_CARD}; color:{_TXT};")
        self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setSpacing(12); lay.setContentsMargins(24, 20, 24, 20)
        lay.addWidget(QLabel("📦 Datos del proveedor", styleSheet=f"color:{_PRI}; font-size:15px; font-weight:bold;"))

        est = f"QLineEdit {{ {_estilo_inp()} }} QTextEdit {{ {_estilo_inp()} }}"
        cest = f"QComboBox {{ {_estilo_inp()} }} QComboBox QAbstractItemView {{ background:{_CARD}; color:{_TXT}; }}"

        form = QFormLayout(); form.setSpacing(10)

        self.inp_nombre = QLineEdit(); self.inp_nombre.setFixedHeight(38)
        self.inp_nombre.setStyleSheet(f"QLineEdit {{ {_estilo_inp()} }}")
        form.addRow("Nombre *:", self.inp_nombre)

        self.inp_telefono = QLineEdit(); self.inp_telefono.setFixedHeight(38)
        self.inp_telefono.setStyleSheet(f"QLineEdit {{ {_estilo_inp()} }}")
        form.addRow("Teléfono:", self.inp_telefono)

        self.inp_vendedor = QLineEdit(); self.inp_vendedor.setFixedHeight(38)
        self.inp_vendedor.setStyleSheet(f"QLineEdit {{ {_estilo_inp()} }}")
        form.addRow("Vendedor:", self.inp_vendedor)

        self.inp_cuit = QLineEdit(); self.inp_cuit.setFixedHeight(38)
        self.inp_cuit.setStyleSheet(f"QLineEdit {{ {_estilo_inp()} }}")
        form.addRow("CUIT:", self.inp_cuit)

        self.combo_dia = QComboBox(); self.combo_dia.addItems(["Sin día fijo"] + DIAS[1:])
        self.combo_dia.setFixedHeight(38); self.combo_dia.setStyleSheet(cest)
        form.addRow("Día de visita:", self.combo_dia)

        self.combo_cond = QComboBox()
        self.combo_cond.addItems([CONDICIONES_LABEL[c] for c in CONDICIONES])
        self.combo_cond.setFixedHeight(38); self.combo_cond.setStyleSheet(cest)
        form.addRow("Condición de pago:", self.combo_cond)

        self.inp_notas = QTextEdit(); self.inp_notas.setFixedHeight(70)
        self.inp_notas.setStyleSheet(f"QTextEdit {{ {_estilo_inp()} }}")
        form.addRow("Notas:", self.inp_notas)

        lay.addLayout(form)

        if self.proveedor:
            self.inp_nombre.setText(self.proveedor.get("nombre", ""))
            self.inp_telefono.setText(self.proveedor.get("telefono") or "")
            self.inp_vendedor.setText(self.proveedor.get("vendedor") or "")
            self.inp_cuit.setText(self.proveedor.get("cuit") or "")
            dia = self.proveedor.get("dia_visita") or ""
            idx = self.combo_dia.findText(dia)
            if idx >= 0: self.combo_dia.setCurrentIndex(idx)
            cond = self.proveedor.get("condicion_pago", "contado")
            self.combo_cond.setCurrentIndex(CONDICIONES.index(cond) if cond in CONDICIONES else 0)
            self.inp_notas.setPlainText(self.proveedor.get("notas") or "")

        btns = QHBoxLayout()
        b_cancel = QPushButton("Cancelar"); b_cancel.setFixedHeight(40)
        b_cancel.setStyleSheet(f"background:transparent; color:{_MUT}; border:1.5px solid {_BOR}; border-radius:8px;")
        b_cancel.clicked.connect(self.reject)
        b_ok = QPushButton("💾 Guardar"); b_ok.setFixedHeight(40)
        b_ok.setStyleSheet(f"background:{_PRI}; color:white; border-radius:8px; font-weight:bold;")
        b_ok.clicked.connect(self._guardar)
        btns.addWidget(b_cancel); btns.addWidget(b_ok)
        lay.addLayout(btns)

    def _guardar(self):
        if not self.inp_nombre.text().strip():
            QMessageBox.warning(self, "Error", "El nombre es obligatorio")
            return
        self.accept()

    def get_datos(self):
        cond = CONDICIONES[self.combo_cond.currentIndex()]
        dia = self.combo_dia.currentText()
        if dia == "Sin día fijo": dia = ""
        return {
            "nombre": self.inp_nombre.text().strip(),
            "telefono": self.inp_telefono.text().strip() or None,
            "vendedor": self.inp_vendedor.text().strip() or None,
            "cuit": self.inp_cuit.text().strip() or None,
            "dia_visita": dia or None,
            "condicion_pago": cond,
            "notas": self.inp_notas.toPlainText().strip() or None,
        }


# ── Dialog registrar compra ───────────────────────────────────────────────────

class CompraDialog(QDialog):
    def __init__(self, parent=None, nombre_proveedor=""):
        super().__init__(parent)
        self.setWindowTitle(f"📥 Registrar compra — {nombre_proveedor}")
        self.setMinimumWidth(400)
        self.setStyleSheet(f"background:{_CARD}; color:{_TXT};")
        self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setSpacing(12); lay.setContentsMargins(24, 20, 24, 20)
        est = f"QLineEdit {{ {_estilo_inp()} }}"
        cest = f"QComboBox {{ {_estilo_inp()} }} QComboBox QAbstractItemView {{ background:{_CARD}; color:{_TXT}; }}"
        dbl = f"QDoubleSpinBox {{ {_estilo_inp()} }}"

        # ── Sección factura ──
        lay.addWidget(QLabel("📋 Datos de la factura", styleSheet=f"color:{_PRI}; font-weight:bold; font-size:13px;"))
        form = QFormLayout(); form.setSpacing(10)

        self.inp_factura = QLineEdit(); self.inp_factura.setFixedHeight(38)
        self.inp_factura.setStyleSheet(est); self.inp_factura.setPlaceholderText("Ej: 0001-00012345")
        form.addRow("N° Factura:", self.inp_factura)

        self.spin_monto = QDoubleSpinBox(); self.spin_monto.setRange(0.01, 99999999)
        self.spin_monto.setPrefix("$"); self.spin_monto.setFixedHeight(38)
        self.spin_monto.setDecimals(0)
        self.spin_monto.setStyleSheet(dbl)
        self.spin_monto.valueChanged.connect(self._sync_pago)
        form.addRow("Monto total factura *:", self.spin_monto)

        self.combo_cond = QComboBox()
        self.combo_cond.addItems(["Contado", "Crédito"])
        self.combo_cond.setFixedHeight(38); self.combo_cond.setStyleSheet(cest)
        self.combo_cond.currentIndexChanged.connect(self._toggle_venc)
        form.addRow("Condición:", self.combo_cond)

        self.inp_venc = QLineEdit(); self.inp_venc.setFixedHeight(38)
        self.inp_venc.setStyleSheet(est); self.inp_venc.setPlaceholderText("YYYY-MM-DD")
        self.inp_venc.setVisible(False)
        self.lbl_venc = QLabel("Fecha vencimiento:")
        self.lbl_venc.setVisible(False)
        form.addRow(self.lbl_venc, self.inp_venc)

        self.inp_notas = QLineEdit(); self.inp_notas.setFixedHeight(38)
        self.inp_notas.setStyleSheet(est)
        form.addRow("Notas:", self.inp_notas)
        lay.addLayout(form)

        # ── Separador ──
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background:{_BOR}; max-height:1px; margin:4px 0;")
        lay.addWidget(sep)

        # ── Sección pago ──
        lay.addWidget(QLabel("💵 Pago", styleSheet=f"color:{_OK}; font-weight:bold; font-size:13px;"))
        form2 = QFormLayout(); form2.setSpacing(10)

        self.spin_pago = QDoubleSpinBox(); self.spin_pago.setRange(0, 99999999)
        self.spin_pago.setPrefix("$"); self.spin_pago.setFixedHeight(38)
        self.spin_pago.setDecimals(0)
        self.spin_pago.setStyleSheet(dbl)
        form2.addRow("Importe a pagar ahora *:", self.spin_pago)

        self.combo_metodo = QComboBox()
        self.combo_metodo.addItems([METODOS_LABEL[m] for m in METODOS_PAGO])
        self.combo_metodo.setFixedHeight(38); self.combo_metodo.setStyleSheet(cest)
        form2.addRow("Método de pago *:", self.combo_metodo)

        self.inp_ref = QLineEdit(); self.inp_ref.setFixedHeight(38)
        self.inp_ref.setStyleSheet(est); self.inp_ref.setPlaceholderText("Nro. transferencia, cheque, etc.")
        form2.addRow("Referencia:", self.inp_ref)
        lay.addLayout(form2)

        btns = QHBoxLayout()
        b_c = QPushButton("Cancelar"); b_c.setFixedHeight(42)
        b_c.setStyleSheet(f"background:transparent; color:{_MUT}; border:1.5px solid {_BOR}; border-radius:8px;")
        b_c.clicked.connect(self.reject)
        b_ok = QPushButton("📥 Registrar"); b_ok.setFixedHeight(42)
        b_ok.setStyleSheet(f"background:{_PRI}; color:white; border-radius:8px; font-weight:bold; font-size:14px;")
        b_ok.clicked.connect(self.accept)
        btns.addWidget(b_c); btns.addWidget(b_ok)
        lay.addLayout(btns)

    def _toggle_venc(self, idx):
        es_credito = (idx == 1)
        self.inp_venc.setVisible(es_credito)
        self.lbl_venc.setVisible(es_credito)
        # Si es crédito, el pago puede ser 0 (no paga ahora)
        if es_credito:
            self.spin_pago.setValue(0)
        else:
            self.spin_pago.setValue(self.spin_monto.value())

    def _sync_pago(self, valor):
        # Solo sincronizar si es contado
        if self.combo_cond.currentIndex() == 0:
            self.spin_pago.setValue(valor)

    def get_datos(self):
        return {
            "factura": {
                "nro_factura": self.inp_factura.text().strip() or None,
                "monto_total": self.spin_monto.value(),
                "condicion": "credito" if self.combo_cond.currentIndex() == 1 else "contado",
                "fecha_vencimiento": self.inp_venc.text().strip() or None,
                "notas": self.inp_notas.text().strip() or None,
            },
            "pago": {
                "monto": self.spin_pago.value(),
                "metodo_pago": METODOS_PAGO[self.combo_metodo.currentIndex()],
                "referencia": self.inp_ref.text().strip() or None,
            } if self.spin_pago.value() > 0 else None,
        }


# ── Dialog registrar pago ─────────────────────────────────────────────────────

class PagoDialog(QDialog):
    def __init__(self, parent=None, nombre_proveedor="", saldo=0):
        super().__init__(parent)
        self.setWindowTitle(f"💵 Registrar pago — {nombre_proveedor}")
        self.setMinimumWidth(400)
        self.setStyleSheet(f"background:{_CARD}; color:{_TXT};")
        self.saldo = saldo
        self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setSpacing(12); lay.setContentsMargins(24, 20, 24, 20)
        est = f"QLineEdit {{ {_estilo_inp()} }}"
        cest = f"QComboBox {{ {_estilo_inp()} }} QComboBox QAbstractItemView {{ background:{_CARD}; color:{_TXT}; }}"

        if self.saldo > 0:
            lbl_saldo = QLabel(f"Saldo pendiente: {_p(self.saldo)}")
            lbl_saldo.setStyleSheet(f"color:{_WARN}; font-size:14px; font-weight:bold;")
            lay.addWidget(lbl_saldo)

        form = QFormLayout(); form.setSpacing(10)

        self.spin_monto = QDoubleSpinBox(); self.spin_monto.setRange(0.01, 99999999)
        self.spin_monto.setPrefix("$"); self.spin_monto.setFixedHeight(38)
        if self.saldo > 0: self.spin_monto.setValue(self.saldo)
        self.spin_monto.setStyleSheet(f"QDoubleSpinBox {{ {_estilo_inp()} }}")
        form.addRow("Monto *:", self.spin_monto)

        self.combo_metodo = QComboBox()
        self.combo_metodo.addItems([METODOS_LABEL[m] for m in METODOS_PAGO])
        self.combo_metodo.setFixedHeight(38); self.combo_metodo.setStyleSheet(cest)
        form.addRow("Método de pago *:", self.combo_metodo)

        self.inp_ref = QLineEdit(); self.inp_ref.setFixedHeight(38)
        self.inp_ref.setStyleSheet(est); self.inp_ref.setPlaceholderText("Nro. transferencia, cheque, etc.")
        form.addRow("Referencia:", self.inp_ref)

        self.inp_notas = QLineEdit(); self.inp_notas.setFixedHeight(38)
        self.inp_notas.setStyleSheet(est)
        form.addRow("Notas:", self.inp_notas)

        lay.addLayout(form)
        btns = QHBoxLayout()
        b_c = QPushButton("Cancelar"); b_c.setFixedHeight(40)
        b_c.setStyleSheet(f"background:transparent; color:{_MUT}; border:1.5px solid {_BOR}; border-radius:8px;")
        b_c.clicked.connect(self.reject)
        b_ok = QPushButton("💵 Registrar pago"); b_ok.setFixedHeight(40)
        b_ok.setStyleSheet(f"background:{_OK}; color:white; border-radius:8px; font-weight:bold;")
        b_ok.clicked.connect(self.accept)
        btns.addWidget(b_c); btns.addWidget(b_ok)
        lay.addLayout(btns)

    def get_datos(self):
        return {
            "monto": self.spin_monto.value(),
            "metodo_pago": METODOS_PAGO[self.combo_metodo.currentIndex()],
            "referencia": self.inp_ref.text().strip() or None,
            "notas": self.inp_notas.text().strip() or None,
        }


# ── Dialog detalle del proveedor ──────────────────────────────────────────────

class DetalleProveedorDialog(QDialog):
    def __init__(self, parent, proveedor: dict):
        super().__init__(parent)
        self.proveedor = proveedor
        self.pid = proveedor["id"]
        self.setWindowTitle(f"📦 {proveedor['nombre']}")
        self.setMinimumSize(720, 520)
        self.setStyleSheet(f"background:{_BG}; color:{_TXT};")
        self._build()
        self._cargar_todo()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(20, 16, 20, 16); lay.setSpacing(12)

        # Header
        hr = QHBoxLayout()
        hr.addWidget(QLabel(self.proveedor["nombre"],
            styleSheet=f"color:{_TXT}; font-size:18px; font-weight:bold;"))
        hr.addStretch()
        self.lbl_saldo = QLabel("")
        self.lbl_saldo.setStyleSheet(f"color:{_WARN}; font-size:14px; font-weight:bold;")
        hr.addWidget(self.lbl_saldo)

        btn_compra = QPushButton("📥 Registrar compra"); btn_compra.setFixedHeight(34)
        btn_compra.setStyleSheet(f"background:{_PRI}; color:white; border-radius:8px; padding:0 12px; font-weight:bold;")
        btn_compra.clicked.connect(self._registrar_compra)
        hr.addWidget(btn_compra)

        btn_pago = QPushButton("💵 Registrar pago"); btn_pago.setFixedHeight(34)
        btn_pago.setStyleSheet(f"background:{_OK}; color:white; border-radius:8px; padding:0 12px; font-weight:bold;")
        btn_pago.clicked.connect(self._registrar_pago)
        hr.addWidget(btn_pago)

        if self.proveedor.get("telefono"):
            btn_wa = QPushButton("📱 WhatsApp"); btn_wa.setFixedHeight(34)
            btn_wa.setStyleSheet(f"background:#25D366; color:white; border-radius:8px; padding:0 12px; font-weight:bold;")
            btn_wa.clicked.connect(self._abrir_whatsapp)
            hr.addWidget(btn_wa)

        lay.addLayout(hr)

        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border:1.5px solid {_BOR}; background:{_CARD}; border-radius:10px; }}
            QTabBar::tab {{ background:{_BG}; color:{_MUT}; padding:8px 16px; font-weight:bold; border-bottom:2px solid transparent; }}
            QTabBar::tab:selected {{ color:{_PRI}; border-bottom:2px solid {_PRI}; background:{_CARD}; }}
        """)

        # Tab Info
        tab_info = QWidget(); tab_info.setStyleSheet(f"background:{_CARD};")
        il = QVBoxLayout(tab_info); il.setContentsMargins(16, 12, 16, 12); il.setSpacing(8)
        p = self.proveedor
        for lbl, val in [
            ("Teléfono", p.get("telefono") or "—"),
            ("Vendedor", p.get("vendedor") or "—"),
            ("CUIT", p.get("cuit") or "—"),
            ("Día de visita", p.get("dia_visita") or "—"),
            ("Condición de pago", CONDICIONES_LABEL.get(p.get("condicion_pago", "contado"), "—")),
            ("Notas", p.get("notas") or "—"),
        ]:
            row = QHBoxLayout()
            row.addWidget(QLabel(lbl + ":", styleSheet=f"color:{_MUT}; font-size:13px; min-width:140px;"))
            row.addWidget(QLabel(val, styleSheet=f"color:{_TXT}; font-size:13px;"))
            row.addStretch()
            il.addLayout(row)
        il.addStretch()
        tabs.addTab(tab_info, "ℹ️ Info")

        # Tab Productos
        tab_prods = QWidget(); tab_prods.setStyleSheet(f"background:{_CARD};")
        pl = QVBoxLayout(tab_prods); pl.setContentsMargins(8, 8, 8, 8)
        self.tabla_prods = QTableWidget()
        self.tabla_prods.setColumnCount(4)
        self.tabla_prods.setHorizontalHeaderLabels(["Producto", "Precio costo", "Precio venta", "Stock"])
        self.tabla_prods.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabla_prods.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_prods.setStyleSheet(f"background:{_CARD}; color:{_TXT}; gridline-color:{_BOR}; border:none;")
        pl.addWidget(self.tabla_prods)
        tabs.addTab(tab_prods, "📦 Productos")

        # Tab Compras
        tab_compras = QWidget(); tab_compras.setStyleSheet(f"background:{_CARD};")
        cl = QVBoxLayout(tab_compras); cl.setContentsMargins(8, 8, 8, 8)
        self.tabla_compras = QTableWidget()
        self.tabla_compras.setColumnCount(6)
        self.tabla_compras.setHorizontalHeaderLabels(["Fecha", "N° Factura", "Monto", "Condición", "Vencimiento", "Estado"])
        self.tabla_compras.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_compras.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_compras.setStyleSheet(f"background:{_CARD}; color:{_TXT}; gridline-color:{_BOR}; border:none;")
        cl.addWidget(self.tabla_compras)
        tabs.addTab(tab_compras, "📋 Compras")

        # Tab Pagos
        tab_pagos = QWidget(); tab_pagos.setStyleSheet(f"background:{_CARD};")
        pagl = QVBoxLayout(tab_pagos); pagl.setContentsMargins(8, 8, 8, 8)
        self.tabla_pagos = QTableWidget()
        self.tabla_pagos.setColumnCount(5)
        self.tabla_pagos.setHorizontalHeaderLabels(["Fecha", "Monto", "Método", "Referencia", "Notas"])
        self.tabla_pagos.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_pagos.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_pagos.setStyleSheet(f"background:{_CARD}; color:{_TXT}; gridline-color:{_BOR}; border:none;")
        pagl.addWidget(self.tabla_pagos)
        tabs.addTab(tab_pagos, "💵 Pagos")

        lay.addWidget(tabs)

    def _cargar_todo(self):
        def _fetch():
            try:
                pid = self.pid
                prods = requests.get(f"{API_URL}/proveedores/{pid}/productos", timeout=5).json()
                compras = requests.get(f"{API_URL}/proveedores/{pid}/compras", timeout=5).json()
                pagos = requests.get(f"{API_URL}/proveedores/{pid}/pagos", timeout=5).json()
                saldo = requests.get(f"{API_URL}/proveedores/{pid}/saldo", timeout=5).json().get("saldo", 0)
                QTimer.singleShot(0, lambda: self._aplicar(prods, compras, pagos, saldo))
            except Exception:
                pass
        threading.Thread(target=_fetch, daemon=True).start()

    def _aplicar(self, prods, compras, pagos, saldo):
        if saldo > 0:
            self.lbl_saldo.setText(f"Deuda: {_p(saldo)}")
        else:
            self.lbl_saldo.setText("✅ Sin deuda")
            self.lbl_saldo.setStyleSheet(f"color:{_OK}; font-size:13px; font-weight:bold;")

        self.tabla_prods.setRowCount(len(prods))
        for i, p in enumerate(prods):
            self.tabla_prods.setItem(i, 0, QTableWidgetItem(p["nombre"]))
            self.tabla_prods.setItem(i, 1, QTableWidgetItem(_p(p["precio_costo"])))
            self.tabla_prods.setItem(i, 2, QTableWidgetItem(_p(p["precio_venta"])))
            self.tabla_prods.setItem(i, 3, QTableWidgetItem(str(p["stock_actual"])))
            self.tabla_prods.setRowHeight(i, 30)

        self.tabla_compras.setRowCount(len(compras))
        for i, c in enumerate(compras):
            self.tabla_compras.setItem(i, 0, QTableWidgetItem(c["fecha"][:10]))
            self.tabla_compras.setItem(i, 1, QTableWidgetItem(c.get("nro_factura") or "—"))
            self.tabla_compras.setItem(i, 2, QTableWidgetItem(_p(c["monto_total"])))
            self.tabla_compras.setItem(i, 3, QTableWidgetItem("Crédito" if c["condicion"] == "credito" else "Contado"))
            self.tabla_compras.setItem(i, 4, QTableWidgetItem(c.get("fecha_vencimiento") or "—"))
            estado = "✅ Pagado" if c["pagado"] else "⏳ Pendiente"
            item_est = QTableWidgetItem(estado)
            item_est.setForeground(Qt.GlobalColor.green if c["pagado"] else Qt.GlobalColor.yellow)
            self.tabla_compras.setItem(i, 5, item_est)
            self.tabla_compras.setRowHeight(i, 30)

        self.tabla_pagos.setRowCount(len(pagos))
        for i, pg in enumerate(pagos):
            self.tabla_pagos.setItem(i, 0, QTableWidgetItem(pg["fecha"][:10]))
            self.tabla_pagos.setItem(i, 1, QTableWidgetItem(_p(pg["monto"])))
            self.tabla_pagos.setItem(i, 2, QTableWidgetItem(METODOS_LABEL.get(pg["metodo_pago"], pg["metodo_pago"])))
            self.tabla_pagos.setItem(i, 3, QTableWidgetItem(pg.get("referencia") or "—"))
            self.tabla_pagos.setItem(i, 4, QTableWidgetItem(pg.get("notas") or "—"))
            self.tabla_pagos.setRowHeight(i, 30)

    def _registrar_compra(self):
        dlg = CompraDialog(self, self.proveedor["nombre"])
        if dlg.exec():
            datos = dlg.get_datos()
            try:
                r = requests.post(f"{API_URL}/proveedores/{self.pid}/compras",
                                  json=datos["factura"], timeout=5)
                if r.status_code == 200:
                    compra_id = r.json().get("id")
                    # Registrar el pago si el usuario ingresó importe
                    if datos["pago"] and datos["pago"]["monto"] > 0:
                        pago_data = {**datos["pago"], "compra_id": compra_id}
                        requests.post(f"{API_URL}/proveedores/{self.pid}/pagos",
                                      json=pago_data, timeout=5)
                    self._cargar_todo()
                    msg = "Compra registrada"
                    if datos["pago"] and datos["pago"]["monto"] > 0:
                        msg += f"\nPago de ${datos['pago']['monto']:,.0f} registrado".replace(",", ".")
                    QMessageBox.information(self, "✅", msg)
                else:
                    QMessageBox.critical(self, "Error", r.text)
            except Exception:
                QMessageBox.critical(self, "Error", "No se puede conectar al servidor")

    def _registrar_pago(self):
        try:
            saldo = requests.get(f"{API_URL}/proveedores/{self.pid}/saldo", timeout=5).json().get("saldo", 0)
        except Exception:
            saldo = 0
        dlg = PagoDialog(self, self.proveedor["nombre"], saldo)
        if dlg.exec():
            datos = dlg.get_datos()
            try:
                r = requests.post(f"{API_URL}/proveedores/{self.pid}/pagos", json=datos, timeout=5)
                if r.status_code == 200:
                    self._cargar_todo()
                    QMessageBox.information(self, "✅", "Pago registrado")
                else:
                    QMessageBox.critical(self, "Error", r.text)
            except Exception:
                QMessageBox.critical(self, "Error", "No se puede conectar al servidor")

    def _abrir_whatsapp(self):
        import subprocess
        tel = (self.proveedor.get("telefono") or "").replace(" ", "").replace("-", "").replace("+", "")
        if tel:
            subprocess.Popen(["cmd", "/c", f"start https://wa.me/54{tel}"])


# ── Pantalla principal ────────────────────────────────────────────────────────

class ProveedoresScreen(QWidget):
    _proveedores_listos = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.proveedores = []
        self.setup_ui()
        self._proveedores_listos.connect(self._aplicar)

    def showEvent(self, event):
        super().showEvent(event)
        self.cargar()

    def setup_ui(self):
        self.setStyleSheet(f"background:{_BG}; color:{_TXT};")
        lay = QVBoxLayout(self); lay.setContentsMargins(24, 20, 24, 20); lay.setSpacing(16)

        # Header
        hr = QHBoxLayout()
        tit = QLabel("📦 Proveedores")
        tit.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        tit.setStyleSheet(f"color:{_TXT};")
        hr.addWidget(tit); hr.addStretch()

        self.inp_buscar = QLineEdit()
        self.inp_buscar.setPlaceholderText("🔍 Buscar proveedor...")
        self.inp_buscar.setFixedWidth(220); self.inp_buscar.setFixedHeight(36)
        self.inp_buscar.setStyleSheet(f"QLineEdit {{ {_estilo_inp()} }}")
        self.inp_buscar.textChanged.connect(self._filtrar)
        hr.addWidget(self.inp_buscar)

        btn_nuevo = QPushButton("➕ Nuevo proveedor"); btn_nuevo.setFixedHeight(36)
        btn_nuevo.setStyleSheet(f"QPushButton {{ background:{_PRI}; color:white; border-radius:8px; padding:0 16px; font-weight:bold; }} QPushButton:hover {{ background:{_T['primary_hover']}; }}")
        btn_nuevo.clicked.connect(self._nuevo)
        hr.addWidget(btn_nuevo)

        btn_ref = QPushButton("↻"); btn_ref.setFixedSize(36, 36)
        btn_ref.setStyleSheet(f"QPushButton {{ background:{_T['primary_light']}; color:{_PRI}; border-radius:8px; border:1.5px solid {_PRI}; }} QPushButton:hover {{ background:{_PRI}; color:white; }}")
        btn_ref.clicked.connect(self.cargar)
        hr.addWidget(btn_ref)
        lay.addLayout(hr)

        # Cards resumen
        self._cards_row = QHBoxLayout(); self._cards_row.setSpacing(12)
        self.card_total = self._card("🏭 Proveedores", "0", _PRI)
        self.card_deuda = self._card("💰 Deuda total", "$0", _WARN)
        self.card_hoy   = self._card("📅 Visitan hoy", "0", _OK)
        for c in [self.card_total, self.card_deuda, self.card_hoy]:
            self._cards_row.addWidget(c[0])
        lay.addLayout(self._cards_row)

        # Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(7)
        self.tabla.setHorizontalHeaderLabels(["Nombre", "Teléfono", "Vendedor", "Día visita", "Condición", "Productos", "Deuda"])
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.doubleClicked.connect(self._ver_detalle)
        self.tabla.setStyleSheet(f"QTableWidget {{ background:{_CARD}; color:{_TXT}; gridline-color:{_BOR}; border:1.5px solid {_BOR}; border-radius:10px; font-size:13px; }}")
        lay.addWidget(self.tabla)

        lbl_hint = QLabel("💡 Doble click para ver detalle, compras y pagos")
        lbl_hint.setStyleSheet(f"color:{_MUT}; font-size:11px;")
        lay.addWidget(lbl_hint)

    def _card(self, titulo, valor, color):
        card = QFrame()
        card.setStyleSheet(f"QFrame {{ background:{_CARD}; border-radius:12px; border-left:5px solid {color}; border:1.5px solid {_BOR}; border-left:5px solid {color}; }}")
        card.setMinimumHeight(76)
        cl = QVBoxLayout(card); cl.setContentsMargins(16, 10, 16, 10)
        cl.addWidget(QLabel(titulo, styleSheet=f"color:{_MUT}; font-size:11px;"))
        lbl_val = QLabel(valor)
        lbl_val.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        lbl_val.setStyleSheet(f"color:{color};")
        cl.addWidget(lbl_val)
        return card, lbl_val

    def cargar(self):
        def _fetch():
            try:
                r = requests.get(f"{API_URL}/proveedores/", timeout=8)
                if r.status_code == 200:
                    self._proveedores_listos.emit(r.json())
            except Exception:
                pass
        threading.Thread(target=_fetch, daemon=True).start()

    def _aplicar(self, proveedores):
        from datetime import datetime
        self.proveedores = proveedores
        self._mostrar(proveedores)
        # Cards
        self.card_total[1].setText(str(len(proveedores)))
        deuda_total = sum(float(p.get("saldo_pendiente", 0)) for p in proveedores)
        self.card_deuda[1].setText(_p(deuda_total))
        hoy = datetime.now().strftime("%A").capitalize()
        dias_es = {"Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles",
                   "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sábado", "Sunday": "Domingo"}
        hoy_es = dias_es.get(datetime.now().strftime("%A"), "")
        visitan_hoy = sum(1 for p in proveedores if p.get("dia_visita") == hoy_es)
        self.card_hoy[1].setText(str(visitan_hoy))

    def _mostrar(self, proveedores):
        self.tabla.setRowCount(len(proveedores))
        for i, p in enumerate(proveedores):
            self.tabla.setItem(i, 0, QTableWidgetItem(p["nombre"]))
            self.tabla.setItem(i, 1, QTableWidgetItem(p.get("telefono") or "—"))
            self.tabla.setItem(i, 2, QTableWidgetItem(p.get("vendedor") or "—"))
            self.tabla.setItem(i, 3, QTableWidgetItem(p.get("dia_visita") or "—"))
            self.tabla.setItem(i, 4, QTableWidgetItem(CONDICIONES_LABEL.get(p.get("condicion_pago", "contado"), "—")))
            self.tabla.setItem(i, 5, QTableWidgetItem(str(p.get("cantidad_productos", 0))))
            saldo = float(p.get("saldo_pendiente", 0))
            item_saldo = QTableWidgetItem(_p(saldo) if saldo > 0 else "✅ $0")
            if saldo > 0:
                item_saldo.setForeground(Qt.GlobalColor.yellow)
            else:
                item_saldo.setForeground(Qt.GlobalColor.green)
            self.tabla.setItem(i, 6, item_saldo)
            self.tabla.setRowHeight(i, 34)

    def _filtrar(self, texto):
        t = texto.lower()
        filtrados = [p for p in self.proveedores if t in p["nombre"].lower()
                     or t in (p.get("vendedor") or "").lower()
                     or t in (p.get("telefono") or "").lower()]
        self._mostrar(filtrados)

    def _nuevo(self):
        dlg = ProveedorDialog(self)
        if dlg.exec():
            datos = dlg.get_datos()
            try:
                r = requests.post(f"{API_URL}/proveedores/", json=datos, timeout=5)
                if r.status_code == 200:
                    self.cargar()
                    QMessageBox.information(self, "✅", "Proveedor creado")
                else:
                    QMessageBox.critical(self, "Error", r.text)
            except Exception:
                QMessageBox.critical(self, "Error", "No se puede conectar al servidor")

    def _ver_detalle(self, index):
        row = index.row()
        # Buscar en tabla visible
        nombre_item = self.tabla.item(row, 0)
        if not nombre_item:
            return
        nombre = nombre_item.text()
        proveedor = next((p for p in self.proveedores if p["nombre"] == nombre), None)
        if not proveedor:
            return

        dlg = DetalleProveedorDialog(self, proveedor)

        # Agregar botón editar en el footer
        btn_edit = QPushButton("✏️ Editar datos")
        btn_edit.setFixedHeight(38)
        btn_edit.setStyleSheet(f"background:{_T['primary_light']}; color:{_PRI}; border:1.5px solid {_PRI}; border-radius:8px; padding:0 14px; font-weight:bold;")
        btn_edit.clicked.connect(lambda: self._editar_desde_detalle(dlg, proveedor))
        dlg.layout().addWidget(btn_edit)

        dlg.exec()
        self.cargar()

    def _editar_desde_detalle(self, detalle_dlg, proveedor):
        dlg = ProveedorDialog(self, proveedor)
        if dlg.exec():
            datos = dlg.get_datos()
            try:
                r = requests.put(f"{API_URL}/proveedores/{proveedor['id']}", json=datos, timeout=5)
                if r.status_code == 200:
                    QMessageBox.information(self, "✅", "Proveedor actualizado")
                    detalle_dlg.accept()
            except Exception:
                QMessageBox.critical(self, "Error", "No se puede conectar al servidor")

