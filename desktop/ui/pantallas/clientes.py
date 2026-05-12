import requests
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QLineEdit, QFrame, QMessageBox,
                              QTableWidget, QTableWidgetItem, QHeaderView,
                              QDialog, QFormLayout, QDoubleSpinBox, QMenu)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

API_URL = "http://127.0.0.1:8000"

from ui.theme import get_tema as _gt
_T = _gt()
_BG = _T["bg_app"]; _CARD = _T["bg_card"]; _TXT = _T["text_main"]
_MUT = _T["text_muted"]; _PRI = _T["primary"]; _DGR = _T["danger"]
_BOR = _T["border"]; _OK = _T["success"]

class ClienteDialog(QDialog):
    def __init__(self, parent=None, cliente=None):
        super().__init__(parent)
        self.cliente = cliente
        self.setWindowTitle("✏️ Editar cliente" if cliente else "➕ Nuevo cliente")
        self.setMinimumWidth(420)
        self.setStyleSheet(f"background-color: {_CARD}; color: {_TXT};")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        titulo = QLabel("👤 Datos del cliente")
        titulo.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        titulo.setStyleSheet(f"color: {_PRI}; background: transparent;")
        layout.addWidget(titulo)

        estilo_input = f"QLineEdit {{ background: {_BG}; border: 1.5px solid {_BOR}; border-radius: 8px; padding: 8px; color: {_TXT}; font-size: 14px; }}"
        estilo_spin  = f"QDoubleSpinBox {{ background: {_BG}; border: 1.5px solid {_BOR}; border-radius: 8px; padding: 8px; color: {_TXT}; font-size: 14px; }}"

        form = QFormLayout()
        form.setSpacing(10)

        self.input_nombre = QLineEdit()
        self.input_nombre.setStyleSheet(estilo_input)
        self.input_nombre.setFixedHeight(40)
        form.addRow("Nombre *:", self.input_nombre)

        self.input_telefono = QLineEdit()
        self.input_telefono.setStyleSheet(estilo_input)
        self.input_telefono.setFixedHeight(40)
        form.addRow("Teléfono:", self.input_telefono)

        self.input_email = QLineEdit()
        self.input_email.setStyleSheet(estilo_input)
        self.input_email.setFixedHeight(40)
        form.addRow("Email:", self.input_email)

        self.input_direccion = QLineEdit()
        self.input_direccion.setStyleSheet(estilo_input)
        self.input_direccion.setFixedHeight(40)
        form.addRow("Dirección:", self.input_direccion)

        self.input_nacimiento = QLineEdit()
        self.input_nacimiento.setPlaceholderText("DD/MM/AAAA")
        self.input_nacimiento.setStyleSheet(estilo_input)
        self.input_nacimiento.setFixedHeight(40)
        form.addRow("Nacimiento:", self.input_nacimiento)

        self.input_limite = QDoubleSpinBox()
        self.input_limite.setRange(0, 9999999)
        self.input_limite.setPrefix("$")
        self.input_limite.setDecimals(2)
        self.input_limite.setFixedHeight(40)
        self.input_limite.setStyleSheet(estilo_spin)
        form.addRow("Límite crédito:", self.input_limite)

        self.input_notas = QLineEdit()
        self.input_notas.setStyleSheet(estilo_input)
        self.input_notas.setFixedHeight(40)
        form.addRow("Notas:", self.input_notas)

        layout.addLayout(form)

        if self.cliente:
            self.input_nombre.setText(self.cliente.get("nombre", ""))
            self.input_telefono.setText(self.cliente.get("telefono") or "")
            self.input_email.setText(self.cliente.get("email") or "")
            self.input_direccion.setText(self.cliente.get("direccion") or "")
            self.input_nacimiento.setText(self.cliente.get("fecha_nacimiento") or "")
            self.input_limite.setValue(float(self.cliente.get("limite_credito", 0)))
            self.input_notas.setText(self.cliente.get("notas") or "")

        btns = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setFixedHeight(44)
        btn_cancelar.setStyleSheet(f"QPushButton {{ background: transparent; color: {_MUT}; border: 1.5px solid {_BOR}; border-radius: 8px; font-weight: bold; }}")
        btn_cancelar.clicked.connect(self.reject)
        btns.addWidget(btn_cancelar)

        btn_guardar = QPushButton("💾 Guardar")
        btn_guardar.setFixedHeight(44)
        btn_guardar.setStyleSheet(f"QPushButton {{ background: {_PRI}; color: white; border-radius: 8px; font-size: 14px; font-weight: bold; }} QPushButton:hover {{ background: {_T['primary_hover']}; }}")
        btn_guardar.clicked.connect(self.guardar)
        btns.addWidget(btn_guardar)
        layout.addLayout(btns)

    def guardar(self):
        if not self.input_nombre.text().strip():
            QMessageBox.warning(self, "Error", "El nombre es obligatorio")
            return
        self.accept()

    def get_datos(self):
        return {
            "nombre":           self.input_nombre.text().strip(),
            "telefono":         self.input_telefono.text().strip() or None,
            "email":            self.input_email.text().strip() or None,
            "direccion":        self.input_direccion.text().strip() or None,
            "fecha_nacimiento": self.input_nacimiento.text().strip() or None,
            "limite_credito":   self.input_limite.value(),
            "notas":            self.input_notas.text().strip() or None,
        }


class HistorialDialog(QDialog):
    def __init__(self, parent=None, cliente_id=None, nombre=""):
        super().__init__(parent)
        self.cliente_id = cliente_id
        self.setWindowTitle(f"📋 Historial — {nombre}")
        self.setMinimumSize(620, 500)
        self.setStyleSheet("background-color: #1a1a2e; color: white;")
        self.setup_ui()
        self.cargar()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        titulo = QLabel(f"📋 Historial de fiados")
        titulo.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        titulo.setStyleSheet("color: #3498db;")
        layout.addWidget(titulo)

        # Resumen
        self.resumen_frame = QFrame()
        self.resumen_frame.setStyleSheet("QFrame { background: #16213e; border-radius: 8px; }")
        resumen_layout = QHBoxLayout(self.resumen_frame)
        resumen_layout.setContentsMargins(16, 10, 16, 10)

        self.lbl_puntos = QLabel("⭐ 0 puntos")
        self.lbl_puntos.setStyleSheet("color: #f39c12; font-size: 14px; font-weight: bold;")
        resumen_layout.addWidget(self.lbl_puntos)
        resumen_layout.addStretch()
        self.lbl_deuda = QLabel("💸 Deuda: $0.00")
        self.lbl_deuda.setStyleSheet("color: #e94560; font-size: 14px; font-weight: bold;")
        resumen_layout.addWidget(self.lbl_deuda)
        resumen_layout.addStretch()
        self.lbl_total_f = QLabel("📊 Total fiado: $0.00")
        self.lbl_total_f.setStyleSheet("color: #a0a0b0; font-size: 13px;")
        resumen_layout.addWidget(self.lbl_total_f)
        layout.addWidget(self.resumen_frame)

        # Tabla de historial
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["Fecha", "Descripción", "Monto", "Estado", "Pagos"])
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla.setColumnWidth(0, 110)
        self.tabla.setColumnWidth(2, 100)
        self.tabla.setColumnWidth(3, 90)
        self.tabla.setColumnWidth(4, 100)
        self.tabla.setStyleSheet("""
            QTableWidget { background: #16213e; border: 1px solid #0f3460; border-radius: 8px; gridline-color: #0f3460; }
            QHeaderView::section { background: #0f3460; color: #a0a0b0; padding: 6px; border: none; }
            QTableWidgetItem { color: white; padding: 6px; }
        """)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.tabla)

        self.lbl_vacio = QLabel("Sin registros de fiado para este cliente.")
        self.lbl_vacio.setStyleSheet("color: #555; font-size: 13px; padding: 20px;")
        self.lbl_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_vacio.hide()
        layout.addWidget(self.lbl_vacio)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setFixedHeight(40)
        btn_cerrar.setStyleSheet("QPushButton { background: #0f3460; color: white; border-radius: 8px; font-size: 13px; }")
        btn_cerrar.clicked.connect(self.accept)
        layout.addWidget(btn_cerrar)

    def cargar(self):
        try:
            r = requests.get(f"{API_URL}/clientes/{self.cliente_id}/historial", timeout=5)
            if r.status_code == 200:
                data = r.json()
                c = data.get("cliente", {})
                self.lbl_puntos.setText(f"⭐ {float(c.get('puntos', 0)):.0f} puntos")
                self.lbl_deuda.setText(f"💸 Deuda: ${float(c.get('deuda_actual', 0)):,.2f}")
                self.lbl_total_f.setText(f"📊 Total fiado: ${data.get('total_fiado', 0):,.2f}")

                historial = data.get("historial", [])
                if not historial:
                    self.tabla.hide()
                    self.lbl_vacio.show()
                    return

                self.tabla.setRowCount(len(historial))
                for i, f in enumerate(historial):
                    fecha = str(f.get("fecha", ""))[:10]
                    self.tabla.setItem(i, 0, QTableWidgetItem(fecha))
                    self.tabla.setItem(i, 1, QTableWidgetItem(f.get("descripcion", "")))

                    item_monto = QTableWidgetItem(f"${float(f.get('monto', 0)):,.2f}")
                    item_monto.setForeground(Qt.GlobalColor.red)
                    self.tabla.setItem(i, 2, item_monto)

                    estado = f.get("estado", "pendiente")
                    item_estado = QTableWidgetItem(estado.capitalize())
                    if estado == "pagado":
                        item_estado.setForeground(Qt.GlobalColor.green)
                    else:
                        item_estado.setForeground(Qt.GlobalColor.yellow)
                    self.tabla.setItem(i, 3, item_estado)

                    pagos = f.get("pagos", [])
                    total_pagado = sum(float(p.get("monto", 0)) for p in pagos)
                    lbl_pagos = QTableWidgetItem(f"${total_pagado:,.2f} ({len(pagos)} pago{'s' if len(pagos) != 1 else ''})")
                    lbl_pagos.setForeground(Qt.GlobalColor.green)
                    self.tabla.setItem(i, 4, lbl_pagos)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el historial\n{str(e)}")


class ClientesScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.clientes = []
        self.usuario_actual = {}
        self.setup_ui()

    def set_usuario(self, usuario):
        self.usuario_actual = usuario or {}

    def _puede_cargar_fiado(self):
        rol    = self.usuario_actual.get("rol", "")
        nombre = self.usuario_actual.get("nombre", "").lower()
        return rol in ("admin", "encargado") or "fernanda" in nombre

    def setup_ui(self):
        self.setStyleSheet(f"background-color: {_BG}; color: {_TXT};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        header = QHBoxLayout()
        titulo = QLabel("👥 Clientes")
        titulo.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        titulo.setStyleSheet(f"color: {_TXT}; background: transparent;")
        header.addWidget(titulo)
        header.addStretch()

        self.input_buscar = QLineEdit()
        self.input_buscar.setPlaceholderText("🔍 Buscar cliente...")
        self.input_buscar.setFixedWidth(220)
        self.input_buscar.setFixedHeight(36)
        self.input_buscar.textChanged.connect(self.filtrar)
        header.addWidget(self.input_buscar)

        btn_nuevo = QPushButton("➕ Nuevo cliente")
        btn_nuevo.setFixedHeight(36)
        btn_nuevo.setStyleSheet(f"QPushButton {{ background: {_PRI}; color: white; border-radius: 8px; padding: 0 16px; font-weight: bold; }} QPushButton:hover {{ background: {_T['primary_hover']}; }}")
        btn_nuevo.clicked.connect(self.nuevo_cliente)
        header.addWidget(btn_nuevo)

        btn_act = QPushButton("🔄")
        btn_act.setFixedSize(36, 36)
        btn_act.setStyleSheet(f"QPushButton {{ background: {_T['primary_light']}; color: {_PRI}; border-radius: 8px; border: 1.5px solid {_PRI}; }} QPushButton:hover {{ background: {_PRI}; color: white; }}")
        btn_act.clicked.connect(self.cargar_clientes)
        header.addWidget(btn_act)
        layout.addLayout(header)

        resumen = QHBoxLayout()
        self.card_total    = self.crear_card("👥 Total clientes", "0", "#2563eb")
        self.card_deudores = self.crear_card("💸 Con deuda",      "0", "#dc2626")
        self.card_puntos   = self.crear_card("⭐ Con puntos",     "0", "#d97706")
        for c in [self.card_total, self.card_deudores, self.card_puntos]:
            resumen.addWidget(c[0])
        layout.addLayout(resumen)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(9)
        self.tabla.setHorizontalHeaderLabels([
            "Nombre", "Teléfono", "Puntos ⭐", "Deuda 💸",
            "Límite", "Nacimiento", "Acciones", "Historial", ""
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabla.setColumnWidth(1, 110)
        self.tabla.setColumnWidth(2, 90)
        self.tabla.setColumnWidth(3, 90)
        self.tabla.setColumnWidth(4, 90)
        self.tabla.setColumnWidth(5, 100)
        self.tabla.setColumnWidth(6, 110)
        self.tabla.setColumnWidth(7, 90)
        self.tabla.setColumnWidth(8, 32)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.tabla)

    def crear_card(self, titulo, valor, color):
        card = QFrame()
        card.setStyleSheet(f"QFrame {{ background: {_CARD}; border-radius: 12px; border: 1.5px solid {_BOR}; border-left: 5px solid {color}; }}")
        card.setMinimumHeight(80)
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(16, 10, 16, 10)
        lbl_t = QLabel(titulo)
        lbl_t.setStyleSheet(f"color: {_MUT}; font-size: 12px; font-weight: bold; background: transparent;")
        c_layout.addWidget(lbl_t)
        lbl_v = QLabel(valor)
        lbl_v.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        lbl_v.setStyleSheet(f"color: {color}; background: transparent;")
        c_layout.addWidget(lbl_v)
        return card, lbl_v

    def showEvent(self, event):
        super().showEvent(event)
        self.cargar_clientes()

    def cargar_clientes(self):
        try:
            r = requests.get(f"{API_URL}/clientes/", timeout=5)
            if r.status_code == 200:
                self.clientes = r.json()
                self.mostrar_clientes(self.clientes)
                self.actualizar_resumen()
        except Exception:
            QMessageBox.critical(self, "Error", "No se puede conectar al servidor")

    def actualizar_resumen(self):
        total      = len(self.clientes)
        deudores   = sum(1 for c in self.clientes if float(c.get("deuda_actual", 0)) > 0)
        con_puntos = sum(1 for c in self.clientes if float(c.get("puntos", 0)) > 0)
        self.card_total[1].setText(str(total))
        self.card_deudores[1].setText(str(deudores))
        self.card_puntos[1].setText(str(con_puntos))

    def filtrar(self, texto):
        if not texto:
            self.mostrar_clientes(self.clientes)
            return
        filtrados = [c for c in self.clientes
                     if texto.lower() in c["nombre"].lower()
                     or texto in (c.get("telefono") or "")]
        self.mostrar_clientes(filtrados)

    def mostrar_clientes(self, clientes):
        self.tabla.setRowCount(len(clientes))
        for i, c in enumerate(clientes):
            self.tabla.setItem(i, 0, QTableWidgetItem(c["nombre"]))
            self.tabla.setItem(i, 1, QTableWidgetItem(c.get("telefono") or "-"))

            puntos = float(c.get("puntos", 0))
            item_pts = QTableWidgetItem(f"⭐ {puntos:.0f}")
            if puntos >= 100:
                item_pts.setForeground(Qt.GlobalColor.yellow)
            self.tabla.setItem(i, 2, item_pts)

            deuda = float(c.get("deuda_actual", 0))
            item_deuda = QTableWidgetItem(f"${deuda:,.2f}")
            if deuda > 0:
                item_deuda.setForeground(Qt.GlobalColor.red)
            self.tabla.setItem(i, 3, item_deuda)

            limite = float(c.get("limite_credito", 0))
            self.tabla.setItem(i, 4, QTableWidgetItem(f"${limite:,.2f}" if limite > 0 else "Sin límite"))
            self.tabla.setItem(i, 5, QTableWidgetItem(c.get("fecha_nacimiento") or "-"))

            # ── Botones de acciones ──────────────────────────────────────────
            btn_acc = QPushButton("⚙️ Acciones ▾")
            btn_acc.setFixedHeight(28)
            btn_acc.setStyleSheet(f"""
                QPushButton {{
                    background: {_PRI}; color: white; border-radius: 6px;
                    font-size: 11px; font-weight: bold; padding: 0 8px;
                }}
                QPushButton:hover {{ background: {_T['primary_hover']}; }}
            """)

            def _hacer_menu(idx=i, pts=puntos, deu=deuda):
                menu = QMenu()
                menu.setStyleSheet(f"""
                    QMenu {{ background: {_CARD}; border: 1px solid {_BOR};
                             color: {_TXT}; border-radius: 6px; padding: 4px; }}
                    QMenu::item {{ padding: 8px 20px; border-radius: 4px; }}
                    QMenu::item:selected {{ background: {_T['bg_hover']}; }}
                """)
                menu.addAction("✏️  Editar cliente",    lambda: self.editar_cliente(idx))
                if self._puede_cargar_fiado():
                    menu.addAction("💸  Cargar deuda",   lambda: self.registrar_fiado(idx))
                if deu > 0:
                    menu.addAction("💰  Registrar pago", lambda: self.registrar_pago_cliente(idx))
                if pts >= 100:
                    menu.addAction("⭐  Canjear puntos", lambda: self.canjear_puntos(idx))
                menu.addAction("🎟️  Generar cupón",     lambda: self.generar_cupon(idx))
                menu.addSeparator()
                menu.addAction("🗑️  Eliminar cliente",  lambda: self.eliminar_cliente(
                    self.get_clientes_visibles()[idx]["id"]))
                menu.exec(btn_acc.mapToGlobal(btn_acc.rect().bottomLeft()))

            btn_acc.clicked.connect(lambda _=None, f=_hacer_menu: f())
            self.tabla.setCellWidget(i, 6, btn_acc)

            # ── Historial ───────────────────────────────────────────────────
            btn_hist = QPushButton("📋")
            btn_hist.setFixedSize(30, 28)
            btn_hist.setToolTip("Ver historial de fiados")
            btn_hist.setStyleSheet("QPushButton { background: #3498db; color: white; border-radius: 4px; }")
            btn_hist.clicked.connect(lambda _, idx=i: self.ver_historial(idx))
            self.tabla.setCellWidget(i, 7, btn_hist)

            if self._puede_cargar_fiado():
                btn_deuda = QPushButton("💸 Deuda")
                btn_deuda.setFixedHeight(28)
                btn_deuda.setStyleSheet("QPushButton { background: #e94560; color: white; border-radius: 6px; font-size: 11px; font-weight: bold; padding: 0 6px; } QPushButton:hover { background: #c0392b; }")
                btn_deuda.clicked.connect(lambda _, idx=i: self.registrar_fiado(idx))
                self.tabla.setCellWidget(i, 8, btn_deuda)
                self.tabla.setColumnHidden(8, False)

            self.tabla.setColumnHidden(8, True)

    # ─── Acciones ─────────────────────────────────────────────────────────────

    def ver_historial(self, idx):
        c = self.get_clientes_visibles()[idx]
        dialog = HistorialDialog(self, c["id"], c["nombre"])
        dialog.exec()

    def canjear_puntos(self, idx):
        c = self.get_clientes_visibles()[idx]
        puntos = float(c.get("puntos", 0))
        bloques = int(puntos // 100)
        descuento = bloques * 1000

        resp = QMessageBox.question(
            self, "⭐ Canjear puntos",
            f"Cliente: {c['nombre']}\n"
            f"Puntos disponibles: {puntos:.0f}\n\n"
            f"Se van a canjear {bloques * 100:.0f} puntos\n"
            f"Descuento a aplicar: ${descuento:,.2f}\n\n"
            f"¿Confirmar canje?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resp == QMessageBox.StandardButton.Yes:
            try:
                r = requests.post(f"{API_URL}/clientes/{c['id']}/canjear-puntos", timeout=5)
                if r.status_code == 200:
                    data = r.json()
                    QMessageBox.information(
                        self, "✅ Canje exitoso",
                        f"Descuento generado: ${data['descuento']:,.2f}\n"
                        f"Puntos usados: {data['puntos_usados']:.0f}\n"
                        f"Puntos restantes: {data['puntos_restantes']:.0f}"
                    )
                    self.cargar_clientes()
                else:
                    msg = r.json().get("detail", "Error al canjear")
                    QMessageBox.warning(self, "Error", msg)
            except Exception:
                QMessageBox.critical(self, "Error", "No se puede conectar al servidor")

    def nuevo_cliente(self):
        dialog = ClienteDialog(self)
        if dialog.exec():
            datos = dialog.get_datos()
            try:
                r = requests.post(f"{API_URL}/clientes/", json=datos, timeout=5)
                if r.status_code == 200:
                    self.cargar_clientes()
                    QMessageBox.information(self, "✅", "Cliente creado correctamente")
                else:
                    QMessageBox.critical(self, "Error", "No se pudo crear el cliente")
            except Exception:
                QMessageBox.critical(self, "Error", "No se puede conectar al servidor")

    def editar_cliente(self, idx):
        c = self.get_clientes_visibles()[idx]
        dialog = ClienteDialog(self, c)
        if dialog.exec():
            datos = dialog.get_datos()
            try:
                r = requests.put(f"{API_URL}/clientes/{c['id']}", json=datos, timeout=5)
                if r.status_code == 200:
                    self.cargar_clientes()
                else:
                    QMessageBox.critical(self, "Error", "No se pudo actualizar")
            except Exception:
                QMessageBox.critical(self, "Error", "No se puede conectar al servidor")

    def generar_cupon(self, idx):
        c = self.get_clientes_visibles()[idx]

        dialog = QDialog(self)
        dialog.setWindowTitle("🎟️ Generar cupón de descuento")
        dialog.setMinimumWidth(380)
        dialog.setStyleSheet("background: #1a1a2e; color: white;")
        lay = QVBoxLayout(dialog)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(12)

        lay.addWidget(QLabel(f"Cliente: <b>{c['nombre']}</b>",
            styleSheet="color: white; font-size: 14px;"))

        lay.addWidget(QLabel("Porcentaje de descuento (%):",
            styleSheet="color: #a0a0b0; font-size: 12px;"))
        spin_pct = QDoubleSpinBox()
        spin_pct.setRange(1, 100)
        spin_pct.setValue(10)
        spin_pct.setSuffix(" %")
        spin_pct.setFixedHeight(40)
        spin_pct.setStyleSheet("QDoubleSpinBox { background: #0f3460; border: 1px solid #8e44ad; border-radius: 8px; padding: 6px; color: white; font-size: 14px; }")
        lay.addWidget(spin_pct)

        lay.addWidget(QLabel("PIN del dueño (autorización):",
            styleSheet="color: #a0a0b0; font-size: 12px;"))
        input_pin = QLineEdit()
        input_pin.setEchoMode(QLineEdit.EchoMode.Password)
        input_pin.setMaxLength(6)
        input_pin.setFixedHeight(40)
        input_pin.setStyleSheet("QLineEdit { background: #0f3460; border: 1px solid #e94560; border-radius: 8px; padding: 8px; color: white; font-size: 18px; letter-spacing: 4px; }")
        lay.addWidget(input_pin)

        lbl_err = QLabel("")
        lbl_err.setStyleSheet("color: #e74c3c; font-size: 12px;")
        lay.addWidget(lbl_err)

        btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setFixedHeight(38)
        btn_cancel.setStyleSheet("QPushButton { background: transparent; color: #a0a0b0; border: 1px solid #a0a0b0; border-radius: 8px; }")
        btn_cancel.clicked.connect(dialog.reject)
        btns.addWidget(btn_cancel)

        btn_ok = QPushButton("🎟️ Generar cupón")
        btn_ok.setFixedHeight(38)
        btn_ok.setStyleSheet("QPushButton { background: #8e44ad; color: white; border-radius: 8px; font-weight: bold; }")
        btns.addWidget(btn_ok)
        lay.addLayout(btns)

        def confirmar():
            pin = input_pin.text().strip()
            pct = spin_pct.value()
            try:
                r = requests.post(
                    f"{API_URL}/clientes/{c['id']}/generar-cupon",
                    json={"porcentaje": pct, "pin_dueno": pin},
                    timeout=5
                )
                if r.status_code == 200:
                    data = r.json()
                    dialog.accept()
                    QMessageBox.information(self, "✅ Cupón generado",
                        f"Cliente: {c['nombre']}\n"
                        f"Código: {data['codigo']}\n"
                        f"Descuento: {data['porcentaje']:.0f}%\n\n"
                        f"Entregá este código al cliente.\nSe usará automáticamente en la próxima compra.")
                    self.cargar_clientes()
                elif r.status_code == 403:
                    lbl_err.setText("❌ PIN incorrecto")
                    input_pin.clear()
                else:
                    lbl_err.setText(f"❌ Error: {r.status_code}")
            except Exception as ex:
                lbl_err.setText(f"❌ Error de conexión: {ex}")

        btn_ok.clicked.connect(confirmar)
        dialog.exec()

    def registrar_fiado(self, idx):
        c = self.get_clientes_visibles()[idx]
        deuda  = float(c.get("deuda_actual", 0))
        limite = float(c.get("limite_credito", 0))

        if limite > 0 and deuda >= limite:
            QMessageBox.warning(self, "⚠️ Límite alcanzado",
                f"{c['nombre']} tiene deuda de ${deuda:,.2f}\n"
                f"Límite de crédito: ${limite:,.2f}\n\n"
                f"No se puede fiar más hasta que pague.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"💸 Fiar a {c['nombre']}")
        dialog.setMinimumWidth(320)
        dialog.setStyleSheet("background-color: #1a1a2e; color: white;")
        lay = QVBoxLayout(dialog)
        lay.setSpacing(10)

        lbl = QLabel(f"Deuda actual: ${deuda:,.2f}")
        lbl.setStyleSheet("color: #e94560; font-size: 14px; font-weight: bold;")
        lay.addWidget(lbl)

        lbl2 = QLabel("Monto a fiar ($):")
        lbl2.setStyleSheet("color: #a0a0b0; font-size: 13px;")
        lay.addWidget(lbl2)

        input_monto = QLineEdit()
        input_monto.setFixedHeight(44)
        input_monto.setStyleSheet("QLineEdit { background: #0f3460; border: 1px solid #e94560; border-radius: 8px; padding: 10px; color: white; font-size: 16px; }")
        lay.addWidget(input_monto)

        lbl3 = QLabel("Descripción:")
        lbl3.setStyleSheet("color: #a0a0b0; font-size: 13px;")
        lay.addWidget(lbl3)

        input_desc = QLineEdit()
        input_desc.setFixedHeight(40)
        input_desc.setStyleSheet("QLineEdit { background: #0f3460; border: 1px solid #e94560; border-radius: 8px; padding: 8px; color: white; font-size: 14px; }")
        lay.addWidget(input_desc)

        btns = QHBoxLayout()
        btn_c = QPushButton("Cancelar")
        btn_c.setFixedHeight(40)
        btn_c.setStyleSheet("QPushButton { background: transparent; color: #a0a0b0; border: 1px solid #a0a0b0; border-radius: 8px; }")
        btn_c.clicked.connect(dialog.reject)
        btns.addWidget(btn_c)

        btn_ok = QPushButton("✅ Registrar fiado")
        btn_ok.setFixedHeight(40)
        btn_ok.setStyleSheet("QPushButton { background: #e94560; color: white; border-radius: 8px; font-size: 14px; font-weight: bold; }")
        btns.addWidget(btn_ok)
        lay.addLayout(btns)

        def confirmar():
            try:
                monto = float(input_monto.text())
            except ValueError:
                QMessageBox.warning(dialog, "Error", "Ingresá un monto válido")
                return
            if limite > 0 and (deuda + monto) > limite:
                QMessageBox.warning(dialog, "⚠️ Límite",
                    f"Este fiado supera el límite de crédito de ${limite:,.2f}")
                return
            try:
                r = requests.post(f"{API_URL}/fiados/", json={
                    "cliente_id": c["id"],
                    "monto": monto,
                    "descripcion": input_desc.text().strip() or "Fiado"
                }, timeout=5)
                if r.status_code == 200:
                    self.cargar_clientes()
                    dialog.accept()
                    QMessageBox.information(self, "✅", f"Fiado registrado: ${monto:,.2f}")
            except Exception:
                QMessageBox.critical(dialog, "Error", "No se puede conectar")

        btn_ok.clicked.connect(confirmar)
        input_monto.returnPressed.connect(confirmar)
        dialog.exec()

    def registrar_pago_cliente(self, idx):
        c = self.get_clientes_visibles()[idx]
        deuda = float(c.get("deuda_actual", 0))
        if deuda <= 0:
            QMessageBox.information(self, "Sin deuda", f"{c['nombre']} no tiene deuda pendiente.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"💰 Pago de {c['nombre']}")
        dialog.setMinimumWidth(320)
        dialog.setStyleSheet("background-color: #1a1a2e; color: white;")
        lay = QVBoxLayout(dialog)
        lay.setSpacing(10)
        lay.setContentsMargins(20, 18, 20, 18)

        lbl = QLabel(f"Deuda total: ${deuda:,.2f}")
        lbl.setStyleSheet("color: #e94560; font-size: 14px; font-weight: bold;")
        lay.addWidget(lbl)

        lbl2 = QLabel("Monto a pagar ($):")
        lbl2.setStyleSheet("color: #a0a0b0; font-size: 13px;")
        lay.addWidget(lbl2)

        input_monto = QLineEdit()
        input_monto.setPlaceholderText(f"{deuda:.2f}")
        input_monto.setFixedHeight(44)
        input_monto.setStyleSheet("QLineEdit { background: #0f3460; border: 1px solid #27ae60; border-radius: 8px; padding: 10px; color: white; font-size: 16px; }")
        lay.addWidget(input_monto)

        btns = QHBoxLayout()
        btn_c = QPushButton("Cancelar")
        btn_c.setFixedHeight(40)
        btn_c.setStyleSheet("QPushButton { background: transparent; color: #a0a0b0; border: 1px solid #a0a0b0; border-radius: 8px; }")
        btn_c.clicked.connect(dialog.reject)
        btns.addWidget(btn_c)

        btn_ok = QPushButton("💰 Registrar pago")
        btn_ok.setFixedHeight(40)
        btn_ok.setStyleSheet("QPushButton { background: #27ae60; color: white; border-radius: 8px; font-size: 14px; font-weight: bold; }")
        btns.addWidget(btn_ok)
        lay.addLayout(btns)

        def confirmar():
            txt = input_monto.text().strip()
            try:
                monto_pago = float(txt) if txt else deuda
            except ValueError:
                QMessageBox.warning(dialog, "Error", "Ingresá un monto válido")
                return
            if monto_pago <= 0:
                QMessageBox.warning(dialog, "Error", "El monto debe ser mayor a cero")
                return
            try:
                r_f = requests.get(f"{API_URL}/fiados/cliente/{c['id']}", timeout=5)
                if r_f.status_code != 200:
                    QMessageBox.critical(dialog, "Error", "No se pudieron obtener los fiados")
                    return
                fiados = sorted(
                    [f for f in r_f.json() if f.get("estado") != "pagado" and float(f.get("saldo", 0)) > 0],
                    key=lambda f: f.get("id", 0)
                )
                restante = monto_pago
                for fiado in fiados:
                    if restante <= 0:
                        break
                    pago = min(restante, float(fiado.get("saldo", 0)))
                    requests.post(f"{API_URL}/fiados/pagar", json={
                        "fiado_id": fiado["id"],
                        "usuario_id": 1,
                        "monto": pago,
                        "metodo": "efectivo",
                    }, timeout=5)
                    restante -= pago
                self.cargar_clientes()
                dialog.accept()
                QMessageBox.information(self, "✅ Pago registrado",
                    f"Pago de ${monto_pago:,.2f} registrado para {c['nombre']}")
            except Exception as ex:
                QMessageBox.critical(dialog, "Error", f"No se pudo registrar el pago\n{str(ex)}")

        btn_ok.clicked.connect(confirmar)
        input_monto.returnPressed.connect(confirmar)
        dialog.exec()

    def eliminar_cliente(self, cid):
        resp = QMessageBox.question(self, "Eliminar",
            "¿Eliminar este cliente?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp == QMessageBox.StandardButton.Yes:
            try:
                r = requests.delete(f"{API_URL}/clientes/{cid}", timeout=5)
                if r.status_code == 200:
                    self.cargar_clientes()
            except Exception:
                QMessageBox.critical(self, "Error", "No se puede conectar al servidor")

    def get_clientes_visibles(self):
        texto = self.input_buscar.text()
        if not texto:
            return self.clientes
        return [c for c in self.clientes
                if texto.lower() in c["nombre"].lower()
                or texto in (c.get("telefono") or "")]
