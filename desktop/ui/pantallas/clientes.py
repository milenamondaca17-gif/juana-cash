import requests
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QLineEdit, QFrame, QMessageBox,
                              QTableWidget, QTableWidgetItem, QHeaderView,
                              QDialog, QFormLayout, QDoubleSpinBox, QMenu, QComboBox,
                              QTabWidget, QDateEdit)
from PyQt6.QtCore import QDate
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

API_URL = "http://127.0.0.1:8000"

from ui.theme import get_tema as _gt
_T = _gt()
_BG = _T["bg_app"]; _CARD = _T["bg_card"]; _TXT = _T["text_main"]
_MUT = _T["text_muted"]; _PRI = _T["primary"]; _DGR = _T["danger"]
_BOR = _T["border"]; _OK = _T["success"]

def _p(v):
    return f"${float(v):,.0f}".replace(",", ".")

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
                self.lbl_puntos.setText(f"⭐ {int(float(c.get('puntos', 0)))} puntos")
                self.lbl_deuda.setText(f"💸 Deuda: {_p(float(c.get('deuda_actual', 0)))}")
                self.lbl_total_f.setText(f"📊 Total fiado: {_p(data.get('total_fiado', 0))}")

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

                    item_monto = QTableWidgetItem(_p(float(f.get('monto', 0))))
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
                    lbl_pagos = QTableWidgetItem(f"{_p(total_pagado)} ({len(pagos)} pago{'s' if len(pagos) != 1 else ''})")
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
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: none; background: {_BG}; }}
            QTabBar::tab {{ background: {_BG}; color: {_MUT}; padding: 12px 24px;
                            border: none; font-size: 13px; font-weight: bold;
                            border-bottom: 2px solid transparent; }}
            QTabBar::tab:selected {{ color: {_PRI}; border-bottom: 2px solid {_PRI}; }}
            QTabBar::tab:hover {{ color: {_TXT}; }}
        """)

        tab1 = QWidget()
        tab1.setStyleSheet(f"background: {_BG};")
        self._build_tab_clientes(tab1)
        self.tabs.addTab(tab1, "👥 Clientes")

        tab2 = QWidget()
        tab2.setStyleSheet(f"background: {_BG};")
        self._build_tab_fiados(tab2)
        self.tabs.addTab(tab2, "📅 Fiados por día")

        self.tabs.currentChanged.connect(self._on_tab_changed)
        outer.addWidget(self.tabs)

    def _build_tab_clientes(self, widget):
        layout = QVBoxLayout(widget)
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

    def _build_tab_fiados(self, widget):
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        header = QHBoxLayout()
        titulo = QLabel("📅 Fiados por día")
        titulo.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        titulo.setStyleSheet(f"color: {_TXT}; background: transparent;")
        header.addWidget(titulo)
        header.addStretch()

        estilo_fecha = f"""
            QDateEdit {{ background: {_CARD}; border: 1.5px solid {_BOR}; border-radius: 8px;
                         padding: 0 10px; color: {_TXT}; font-size: 13px; min-width: 120px; height: 36px; }}
            QDateEdit::drop-down {{ border: none; width: 20px; }}
            QDateEdit::up-button, QDateEdit::down-button {{ width: 0; }}
        """
        lbl_desde = QLabel("Desde:")
        lbl_desde.setStyleSheet(f"color: {_MUT}; font-size: 13px; background: transparent;")
        header.addWidget(lbl_desde)
        self.date_desde = QDateEdit()
        self.date_desde.setCalendarPopup(True)
        self.date_desde.setDate(QDate.currentDate().addMonths(-1))
        self.date_desde.setDisplayFormat("dd/MM/yyyy")
        self.date_desde.setStyleSheet(estilo_fecha)
        self.date_desde.dateChanged.connect(self.cargar_fiados_por_dia)
        header.addWidget(self.date_desde)

        lbl_hasta = QLabel("Hasta:")
        lbl_hasta.setStyleSheet(f"color: {_MUT}; font-size: 13px; background: transparent;")
        header.addWidget(lbl_hasta)
        self.date_hasta = QDateEdit()
        self.date_hasta.setCalendarPopup(True)
        self.date_hasta.setDate(QDate.currentDate())
        self.date_hasta.setDisplayFormat("dd/MM/yyyy")
        self.date_hasta.setStyleSheet(estilo_fecha)
        self.date_hasta.dateChanged.connect(self.cargar_fiados_por_dia)
        header.addWidget(self.date_hasta)

        btn_ref = QPushButton("🔄")
        btn_ref.setFixedSize(36, 36)
        btn_ref.setStyleSheet(f"QPushButton {{ background: {_T['primary_light']}; color: {_PRI}; border-radius: 8px; border: 1.5px solid {_PRI}; }} QPushButton:hover {{ background: {_PRI}; color: white; }}")
        btn_ref.clicked.connect(self.cargar_fiados_por_dia)
        header.addWidget(btn_ref)
        layout.addLayout(header)

        resumen = QHBoxLayout()
        self.card_fiado_total     = self.crear_card("💸 Total fiado",  "$0", "#dc2626")
        self.card_fiado_pendiente = self.crear_card("⏳ Pendiente",    "$0", "#d97706")
        self.card_fiado_pagado    = self.crear_card("✅ Cobrado",      "$0", "#16a34a")
        for c in [self.card_fiado_total, self.card_fiado_pendiente, self.card_fiado_pagado]:
            resumen.addWidget(c[0])
        layout.addLayout(resumen)

        self.tabla_fiados = QTableWidget()
        self.tabla_fiados.setColumnCount(6)
        self.tabla_fiados.setHorizontalHeaderLabels(["Fecha", "Cliente", "Monto", "Descripción", "Estado", "📱"])
        self.tabla_fiados.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla_fiados.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.tabla_fiados.setColumnWidth(0, 100)
        self.tabla_fiados.setColumnWidth(2, 110)
        self.tabla_fiados.setColumnWidth(4, 90)
        self.tabla_fiados.setColumnWidth(5, 40)
        self.tabla_fiados.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_fiados.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_fiados.setStyleSheet(f"""
            QTableWidget {{ background: {_CARD}; border: 1.5px solid {_BOR}; border-radius: 8px; gridline-color: {_BOR}; }}
            QHeaderView::section {{ background: {_BG}; color: {_MUT}; padding: 8px; border: none; font-weight: bold; }}
            QTableWidget::item {{ color: {_TXT}; padding: 6px; }}
            QTableWidget::item:selected {{ background: {_T['bg_hover']}; }}
        """)
        layout.addWidget(self.tabla_fiados)

    def _on_tab_changed(self, idx):
        if idx == 1:
            self.cargar_fiados_por_dia()

    def cargar_fiados_por_dia(self):
        try:
            r = requests.get(f"{API_URL}/fiados/todos", timeout=5)
            if r.status_code != 200:
                return
            fiados = r.json()

            desde = self.date_desde.date().toString("yyyy-MM-dd")
            hasta = self.date_hasta.date().toString("yyyy-MM-dd")
            fiados = [f for f in fiados
                      if desde <= (f.get("fecha") or "") <= hasta]

            total     = sum(f["monto"] for f in fiados)
            pendiente = sum(f["monto"] for f in fiados if f["estado"] in ("pendiente", "parcial"))
            pagado    = sum(f["monto"] for f in fiados if f["estado"] == "pagado")
            self.card_fiado_total[1].setText(_p(total))
            self.card_fiado_pendiente[1].setText(_p(pendiente))
            self.card_fiado_pagado[1].setText(_p(pagado))

            self._fiados_data = fiados
            self.tabla_fiados.setRowCount(len(fiados))
            for i, f in enumerate(fiados):
                self.tabla_fiados.setItem(i, 0, QTableWidgetItem(f.get("fecha") or ""))
                self.tabla_fiados.setItem(i, 1, QTableWidgetItem(f.get("cliente") or ""))

                item_monto = QTableWidgetItem(_p(f["monto"]))
                item_monto.setForeground(Qt.GlobalColor.red)
                self.tabla_fiados.setItem(i, 2, item_monto)

                self.tabla_fiados.setItem(i, 3, QTableWidgetItem(f.get("descripcion") or ""))

                estado = f.get("estado", "pendiente")
                item_est = QTableWidgetItem(estado.capitalize())
                if estado == "pagado":
                    item_est.setForeground(Qt.GlobalColor.green)
                elif estado == "parcial":
                    item_est.setForeground(Qt.GlobalColor.yellow)
                else:
                    item_est.setForeground(Qt.GlobalColor.red)
                self.tabla_fiados.setItem(i, 4, item_est)

                btn_wa = QPushButton("📲")
                btn_wa.setFixedSize(32, 28)
                btn_wa.setToolTip("Enviar ticket por WhatsApp")
                btn_wa.setStyleSheet("QPushButton { background: #25D366; color: white; border-radius: 4px; font-size: 13px; } QPushButton:hover { background: #128C7E; }")
                btn_wa.clicked.connect(lambda _, idx=i: self._enviar_whatsapp_fiado(idx))
                self.tabla_fiados.setCellWidget(i, 5, btn_wa)
        except Exception:
            pass

    def _enviar_whatsapp_fiado(self, idx):
        from ui.pantallas.whatsapp_ticket import servidor_activo, enviar_ticket_whatsapp, formatear_ticket_whatsapp
        if not hasattr(self, "_fiados_data") or idx >= len(self._fiados_data):
            return
        f = self._fiados_data[idx]
        tel = f.get("telefono", "")
        if not tel:
            QMessageBox.warning(self, "Sin teléfono",
                f"{f.get('cliente', 'El cliente')} no tiene teléfono registrado.")
            return
        if not servidor_activo():
            QMessageBox.warning(self, "WhatsApp inactivo",
                "El servidor de WhatsApp no está corriendo.")
            return

        venta_id = f.get("venta_id")
        if venta_id:
            try:
                r = requests.get(f"{API_URL}/ventas/{venta_id}/detalle", timeout=5)
                if r.status_code == 200:
                    det = r.json()
                    mensaje = formatear_ticket_whatsapp(
                        {"numero": det.get("numero", ""), "total": det.get("total", 0)},
                        det.get("items", []),
                        metodo_pago="fiado",
                        descuento=det.get("descuento", 0),
                        recargo=det.get("recargo", 0),
                        cliente=f.get("cliente", ""),
                    )
                else:
                    venta_id = None
            except Exception:
                venta_id = None

        if not venta_id:
            saldo = float(f.get("saldo", f.get("monto", 0)))
            mensaje = (
                f"*AUTOSERVICIO SAN VALENTIN*\n"
                f"📋 Recordatorio de fiado\n\n"
                f"Estimado/a {f.get('cliente', '')}:\n"
                f"El {f.get('fecha', '')} registramos un fiado de {_p(f['monto'])}\n"
            )
            if f.get("descripcion"):
                mensaje += f"Detalle: {f['descripcion']}\n"
            if saldo > 0 and saldo != float(f["monto"]):
                mensaje += f"Saldo pendiente: *{_p(saldo)}*\n"
            else:
                mensaje += f"Monto: *{_p(f['monto'])}*\n"
            mensaje += "\n_Gracias por su confianza — Juana Cash_"

        ok, respuesta = enviar_ticket_whatsapp(tel, mensaje)
        if ok:
            QMessageBox.information(self, "✅ Enviado",
                f"Ticket enviado a {f.get('cliente')} ({tel})")
        else:
            QMessageBox.warning(self, "Error al enviar", respuesta)

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
                self.clientes = sorted(r.json(), key=lambda c: c.get("nombre", "").lower())
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
            item_deuda = QTableWidgetItem(_p(deuda))
            if deuda > 0:
                item_deuda.setForeground(Qt.GlobalColor.red)
            self.tabla.setItem(i, 3, item_deuda)

            limite = float(c.get("limite_credito", 0))
            self.tabla.setItem(i, 4, QTableWidgetItem(_p(limite) if limite > 0 else "Sin límite"))
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

        self.tabla.setColumnHidden(8, not self._puede_cargar_fiado())

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
            btn_ok.setEnabled(False)
            try:
                monto = float(input_monto.text().strip().replace(".", "").replace(",", "."))
            except ValueError:
                btn_ok.setEnabled(True)
                QMessageBox.warning(dialog, "Error", "Ingresá un monto válido")
                return
            if monto <= 0:
                btn_ok.setEnabled(True)
                QMessageBox.warning(dialog, "Error", "El monto debe ser mayor a cero")
                return
            if limite > 0 and (deuda + monto) > limite:
                QMessageBox.warning(dialog, "⚠️ Límite",
                    f"Este fiado supera el límite de crédito de {_p(limite)}")
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
                    QMessageBox.information(self, "✅", f"Fiado registrado: {_p(monto)}")
                else:
                    btn_ok.setEnabled(True)
                    QMessageBox.warning(dialog, "Error", r.json().get("detail", "No se pudo registrar"))
            except Exception:
                btn_ok.setEnabled(True)
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

        lbl = QLabel(f"Deuda total: {_p(deuda)}")
        lbl.setStyleSheet("color: #e94560; font-size: 14px; font-weight: bold;")
        lay.addWidget(lbl)

        lbl_met = QLabel("Método de pago:")
        lbl_met.setStyleSheet("color: #a0a0b0; font-size: 13px;")
        lay.addWidget(lbl_met)
        combo_metodo = QComboBox()
        combo_metodo.addItems(["💵 Efectivo", "🏦 Transferencia", "📱 QR / Mercado Pago", "🏧 Débito", "💳 Tarjeta"])
        combo_metodo.setFixedHeight(38)
        combo_metodo.setStyleSheet("QComboBox { background: #0f3460; border: 1px solid #a0a0b0; border-radius: 8px; padding: 6px 10px; color: white; } QComboBox::drop-down { border: none; }")
        lay.addWidget(combo_metodo)

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
            btn_ok.setEnabled(False)
            txt = input_monto.text().strip()
            try:
                monto_pago = float(txt) if txt else deuda
            except ValueError:
                btn_ok.setEnabled(True)
                QMessageBox.warning(dialog, "Error", "Ingresá un monto válido")
                return
            if monto_pago <= 0:
                btn_ok.setEnabled(True)
                QMessageBox.warning(dialog, "Error", "El monto debe ser mayor a cero")
                return
            try:
                r_f = requests.get(f"{API_URL}/fiados/cliente/{c['id']}", timeout=5)
                if r_f.status_code != 200:
                    btn_ok.setEnabled(True)
                    QMessageBox.critical(dialog, "Error", "No se pudieron obtener los fiados")
                    return
                fiados = sorted(
                    [f for f in r_f.json() if f.get("estado") != "pagado" and float(f.get("saldo", 0)) > 0],
                    key=lambda f: f.get("id", 0)
                )
                _metodo_map = {"💵 Efectivo": "efectivo", "🏦 Transferencia": "transferencia",
                               "📱 QR / Mercado Pago": "mercadopago_qr",
                               "🏧 Débito": "debito", "💳 Tarjeta": "tarjeta"}
                metodo_pago = _metodo_map.get(combo_metodo.currentText(), "efectivo")
                usuario_id = self.usuario_actual.get("id", 1)
                restante = monto_pago
                errores = 0
                for fiado in fiados:
                    if restante <= 0:
                        break
                    pago = min(restante, float(fiado.get("saldo", 0)))
                    try:
                        rp = requests.post(f"{API_URL}/fiados/pagar", json={
                            "fiado_id": fiado["id"],
                            "usuario_id": usuario_id,
                            "monto": pago,
                            "metodo": metodo_pago,
                        }, timeout=5)
                        if rp.status_code == 200:
                            restante -= pago
                        else:
                            errores += 1
                    except Exception:
                        errores += 1
                self.cargar_clientes()
                dialog.accept()
                msg = f"Pago de {_p(monto_pago)} registrado para {c['nombre']}"
                if errores:
                    msg += f"\n⚠️ {errores} cuota(s) no se pudieron registrar"
                QMessageBox.information(self, "✅ Pago registrado", msg)
            except Exception as ex:
                btn_ok.setEnabled(True)
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
