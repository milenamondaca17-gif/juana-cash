import requests
import json
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QLineEdit, QFrame, QMessageBox,
                              QSpinBox, QCheckBox, QTabWidget, QFormLayout,
                              QComboBox, QScrollArea, QDialog, QTableWidget,
                              QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

API_URL = "http://127.0.0.1:8000"

from ui.theme import get_tema as _gt
_T = _gt()
_BG = _T["bg_app"]; _CARD = _T["bg_card"]; _TXT = _T["text_main"]
_MUT = _T["text_muted"]; _PRI = _T["primary"]; _BOR = _T["border"]
_OK = _T["success"]; _DGR = _T["danger"]; _INP = _T["bg_input"]

class ConfigScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.config = {}
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet(f"background-color: {_BG}; color: {_TXT};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        header = QHBoxLayout()
        titulo = QLabel("⚙️ Configuración del Sistema")
        titulo.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        titulo.setStyleSheet(f"color: {_TXT}; background: transparent;")
        header.addWidget(titulo)
        header.addStretch()
        btn_guardar = QPushButton("💾 Guardar todo")
        btn_guardar.setFixedHeight(38)
        btn_guardar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_guardar.setStyleSheet(f"QPushButton {{ background: {_OK}; color: white; border-radius: 8px; font-size: 13px; font-weight: bold; padding: 0 16px; }} QPushButton:hover {{ background: #059669; }}")
        btn_guardar.clicked.connect(self.guardar_config)
        header.addWidget(btn_guardar)
        layout.addLayout(header)

        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1.5px solid {_BOR}; background: {_CARD}; border-radius: 10px; }}
            QTabBar::tab {{ background: {_BG}; color: {_MUT}; padding: 8px 16px; border-radius: 0px; border-bottom: 2px solid transparent; font-weight: bold; }}
            QTabBar::tab:selected {{ color: {_PRI}; border-bottom: 2px solid {_PRI}; background: {_CARD}; }}
            QTabBar::tab:hover {{ color: {_TXT}; background: {_T['bg_hover']}; }}
        """)

        tab_negocio = QWidget()
        tab_negocio.setStyleSheet(f"background: {_CARD};")
        neg_layout = QFormLayout(tab_negocio)
        neg_layout.setContentsMargins(20, 20, 20, 20)
        neg_layout.setSpacing(12)
        neg_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        estilo_input = f"QLineEdit {{ background: {_BG}; border: 1.5px solid {_BOR}; border-radius: 8px; padding: 8px; color: {_TXT}; font-size: 13px; }}"

        self.inp_nombre      = QLineEdit(); self.inp_nombre.setStyleSheet(estilo_input); self.inp_nombre.setFixedHeight(38)
        self.inp_direccion   = QLineEdit(); self.inp_direccion.setStyleSheet(estilo_input); self.inp_direccion.setFixedHeight(38)
        self.inp_telefono    = QLineEdit(); self.inp_telefono.setStyleSheet(estilo_input); self.inp_telefono.setFixedHeight(38)
        self.inp_cuit        = QLineEdit(); self.inp_cuit.setStyleSheet(estilo_input); self.inp_cuit.setFixedHeight(38); self.inp_cuit.setPlaceholderText("XX-XXXXXXXX-X")
        self.inp_iibb        = QLineEdit(); self.inp_iibb.setStyleSheet(estilo_input); self.inp_iibb.setFixedHeight(38)
        self.inp_inicio_act  = QLineEdit(); self.inp_inicio_act.setStyleSheet(estilo_input); self.inp_inicio_act.setFixedHeight(38); self.inp_inicio_act.setPlaceholderText("DD/MM/AAAA")

        self.combo_iva = QComboBox()
        self.combo_iva.addItems(["Responsable Inscripto", "Monotributista", "Exento", "Consumidor Final"])
        self.combo_iva.setFixedHeight(38)
        self.combo_iva.setStyleSheet(f"QComboBox {{ background: {_BG}; border: 1.5px solid {_BOR}; border-radius: 8px; padding: 8px; color: {_TXT}; font-size: 13px; }} QComboBox::drop-down {{ border: none; }} QComboBox QAbstractItemView {{ background: {_CARD}; color: {_TXT}; selection-background-color: {_PRI}; }}")

        for label, widget in [
            ("Nombre del negocio *:", self.inp_nombre),
            ("Dirección:", self.inp_direccion),
            ("Teléfono:", self.inp_telefono),
            ("CUIT:", self.inp_cuit),
            ("IIBB:", self.inp_iibb),
            ("Inicio de actividades:", self.inp_inicio_act),
            ("Condición IVA:", self.combo_iva),
        ]:
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {_MUT}; font-size: 13px;")
            neg_layout.addRow(lbl, widget)

        tabs.addTab(tab_negocio, "🏪 Negocio")

        # ── Tab 2: Sucursales ─────────────────────────────────────────────
        tab_suc = QWidget()
        tab_suc.setStyleSheet(f"background: {_CARD};")
        suc_layout = QVBoxLayout(tab_suc)
        suc_layout.setContentsMargins(20, 20, 20, 20)
        suc_layout.setSpacing(12)

        suc_header = QHBoxLayout()
        lbl_suc = QLabel("Sucursales del negocio")
        lbl_suc.setStyleSheet(f"color: {_TXT}; font-size: 14px; font-weight: bold;")
        suc_header.addWidget(lbl_suc)
        suc_header.addStretch()
        btn_nueva_suc = QPushButton("+ Nueva sucursal")
        btn_nueva_suc.setFixedHeight(32)
        btn_nueva_suc.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_nueva_suc.setStyleSheet(f"QPushButton {{ background: {_PRI}; color: white; border-radius: 6px; font-size: 12px; padding: 0 12px; }} QPushButton:hover {{ background: {_T['primary_hover']}; }}")
        btn_nueva_suc.clicked.connect(self.nueva_sucursal)
        suc_header.addWidget(btn_nueva_suc)
        suc_layout.addLayout(suc_header)

        self.tabla_suc = QTableWidget()
        self.tabla_suc.setColumnCount(3)
        self.tabla_suc.setHorizontalHeaderLabels(["ID", "Nombre", "Dirección"])
        self.tabla_suc.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla_suc.setColumnWidth(0, 60)
        self.tabla_suc.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tabla_suc.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        suc_layout.addWidget(self.tabla_suc)

        lbl_suc_actual = QLabel("Sucursal activa:")
        lbl_suc_actual.setStyleSheet(f"color: {_MUT}; font-size: 13px;")
        suc_layout.addWidget(lbl_suc_actual)
        self.combo_suc_actual = QComboBox()
        self.combo_suc_actual.setFixedHeight(38)
        self.combo_suc_actual.setStyleSheet(f"QComboBox {{ background: {_BG}; border: 1.5px solid {_BOR}; border-radius: 8px; padding: 8px; color: {_TXT}; font-size: 13px; }} QComboBox::drop-down {{ border: none; }} QComboBox QAbstractItemView {{ background: {_CARD}; color: {_TXT}; selection-background-color: {_PRI}; }}")
        suc_layout.addWidget(self.combo_suc_actual)
        suc_layout.addStretch()

        tabs.addTab(tab_suc, "🏬 Sucursales")

        # ── Tab 3: Sistema ────────────────────────────────────────────────
        tab_sis = QWidget()
        tab_sis.setStyleSheet(f"background: {_CARD};")
        sis_layout = QVBoxLayout(tab_sis)
        sis_layout.setContentsMargins(20, 20, 20, 20)
        sis_layout.setSpacing(16)

        # Timeout
        timeout_frame = QFrame()
        timeout_frame.setStyleSheet(f"QFrame {{ background: {_BG}; border-radius: 10px; border: 1.5px solid {_BOR}; }}")
        tf_lay = QVBoxLayout(timeout_frame)
        tf_lay.setContentsMargins(16, 12, 16, 12)
        lbl_to = QLabel("⏱ Timeout de sesión automático")
        lbl_to.setStyleSheet(f"color: {_TXT}; font-size: 13px; font-weight: bold;")
        tf_lay.addWidget(lbl_to)
        lbl_to_desc = QLabel("Cierra la sesión automáticamente después de X minutos sin actividad.")
        lbl_to_desc.setStyleSheet(f"color: {_MUT}; font-size: 12px;")
        tf_lay.addWidget(lbl_to_desc)
        to_fila = QHBoxLayout()
        lbl_min = QLabel("Minutos de inactividad:")
        lbl_min.setStyleSheet(f"color: {_MUT}; font-size: 13px;")
        to_fila.addWidget(lbl_min)
        self.spin_timeout = QSpinBox()
        self.spin_timeout.setRange(1, 480)
        self.spin_timeout.setValue(30)
        self.spin_timeout.setSuffix(" min")
        self.spin_timeout.setFixedHeight(38)
        self.spin_timeout.setFixedWidth(120)
        self.spin_timeout.setStyleSheet(f"QSpinBox {{ background: {_BG}; border: 1.5px solid {_BOR}; border-radius: 8px; padding: 6px; color: {_TXT}; font-size: 14px; }}")
        to_fila.addWidget(self.spin_timeout)
        to_fila.addStretch()
        tf_lay.addLayout(to_fila)
        sis_layout.addWidget(timeout_frame)

        # Modo offline
        offline_frame = QFrame()
        offline_frame.setStyleSheet(f"QFrame {{ background: {_BG}; border-radius: 10px; border: 1.5px solid {_BOR}; }}")
        of_lay = QVBoxLayout(offline_frame)
        of_lay.setContentsMargins(16, 12, 16, 12)
        lbl_of = QLabel("📡 Modo offline robusto")
        lbl_of.setStyleSheet(f"color: {_TXT}; font-size: 13px; font-weight: bold;")
        of_lay.addWidget(lbl_of)
        lbl_of_desc = QLabel("Cuando el servidor no responde, las ventas se guardan localmente\ny se sincronizan automáticamente cuando vuelve la conexión.")
        lbl_of_desc.setStyleSheet(f"color: {_MUT}; font-size: 12px;")
        of_lay.addWidget(lbl_of_desc)
        self.chk_offline = QCheckBox("Activar modo offline")
        self.chk_offline.setStyleSheet(f"QCheckBox {{ color: {_TXT}; font-size: 13px; }} QCheckBox::indicator {{ width: 18px; height: 18px; }}")
        self.chk_offline.setChecked(True)
        of_lay.addWidget(self.chk_offline)
        sis_layout.addWidget(offline_frame)

        # AFIP
        afip_frame = QFrame()
        afip_frame.setStyleSheet(f"QFrame {{ background: {_BG}; border-radius: 10px; border: 1.5px solid {_PRI}; }}")
        af_lay = QVBoxLayout(afip_frame)
        af_lay.setContentsMargins(16, 12, 16, 12)
        lbl_af = QLabel("🧾 Facturación ARCA/AFIP")
        lbl_af.setStyleSheet(f"color: {_PRI}; font-size: 13px; font-weight: bold;")
        af_lay.addWidget(lbl_af)
        lbl_af_desc = QLabel("Generá tickets fiscales B para consumidor final.\nRequiere CUIT cargado y punto de venta configurado.")
        lbl_af_desc.setStyleSheet(f"color: {_MUT}; font-size: 12px;")
        af_lay.addWidget(lbl_af_desc)

        af_fila = QHBoxLayout()
        lbl_pv = QLabel("Punto de venta:")
        lbl_pv.setStyleSheet(f"color: {_MUT}; font-size: 13px;")
        af_fila.addWidget(lbl_pv)
        self.inp_punto_venta = QLineEdit()
        self.inp_punto_venta.setPlaceholderText("0001")
        self.inp_punto_venta.setFixedWidth(80)
        self.inp_punto_venta.setFixedHeight(36)
        self.inp_punto_venta.setStyleSheet(f"QLineEdit {{ background: {_BG}; border: 1.5px solid {_PRI}; border-radius: 6px; padding: 6px; color: {_TXT}; font-size: 13px; }}")
        af_fila.addWidget(self.inp_punto_venta)
        af_fila.addStretch()
        af_lay.addLayout(af_fila)

        self.chk_afip = QCheckBox("Activar facturación (genera comprobantes B)")
        self.chk_afip.setStyleSheet(f"QCheckBox {{ color: {_TXT}; font-size: 13px; }} QCheckBox::indicator {{ width: 18px; height: 18px; }}")
        af_lay.addWidget(self.chk_afip)
        sis_layout.addWidget(afip_frame)
        sis_layout.addStretch()

        tabs.addTab(tab_sis, "🖥️ Sistema")

        # ── TAB: BORRADO DE VENTAS ───────────────────────────────────────────
        tab_borrado = QWidget()
        tab_borrado.setStyleSheet(f"background: {_CARD};")
        bor_layout = QVBoxLayout(tab_borrado)
        bor_layout.setContentsMargins(20, 20, 20, 20)
        bor_layout.setSpacing(16)

        # Advertencia
        warn_frame = QFrame()
        warn_frame.setStyleSheet("QFrame { background: #3d0000; border-radius: 10px; border-left: 4px solid #e74c3c; }")
        warn_lay = QVBoxLayout(warn_frame)
        warn_lay.setContentsMargins(16, 14, 16, 14)
        lbl_warn1 = QLabel("⚠️  ZONA DE PELIGRO")
        lbl_warn1.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        lbl_warn1.setStyleSheet("color: #e74c3c; background: transparent; border: none;")
        lbl_warn2 = QLabel("Esta acción elimina PERMANENTEMENTE todas las ventas, anulaciones\ny datos procesados. Los productos NO se eliminan.")
        lbl_warn2.setStyleSheet("color: #ffaaaa; font-size: 12px; background: transparent; border: none;")
        lbl_warn2.setWordWrap(True)
        warn_lay.addWidget(lbl_warn1)
        warn_lay.addWidget(lbl_warn2)
        bor_layout.addWidget(warn_frame)

        # Qué se borra
        info_frame = QFrame()
        info_frame.setStyleSheet(f"QFrame {{ background: {_BG}; border-radius: 10px; border: 1.5px solid {_BOR}; }}")
        info_lay = QVBoxLayout(info_frame)
        info_lay.setContentsMargins(16, 14, 16, 14)
        info_lay.setSpacing(6)
        lbl_info_t = QLabel("📋 Se eliminará:")
        lbl_info_t.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        lbl_info_t.setStyleSheet(f"color: {_TXT}; background: transparent; border: none;")
        info_lay.addWidget(lbl_info_t)
        for item in ["✅ Todas las ventas completadas",
                     "❌ Todas las anulaciones",
                     "📦 Items de ventas",
                     "💳 Pagos registrados",
                     "🏧 Historial de turnos de caja",
                     "📋 Registro de sesiones y auditoria"]:
            l = QLabel(f"  {item}")
            l.setStyleSheet(f"color: {_MUT}; font-size: 12px; background: transparent; border: none;")
            info_lay.addWidget(l)
        lbl_no_borra = QLabel("\n🔒 NO se eliminará: Productos, clientes, usuarios, configuración")
        lbl_no_borra.setStyleSheet(f"color: {_OK}; font-size: 12px; font-weight: bold; background: transparent; border: none;")
        info_lay.addWidget(lbl_no_borra)
        bor_layout.addWidget(info_frame)

        # PIN y botón
        pin_frame = QFrame()
        pin_frame.setStyleSheet(f"QFrame {{ background: {_BG}; border-radius: 10px; border: 1.5px solid {_BOR}; }}")
        pin_lay = QVBoxLayout(pin_frame)
        pin_lay.setContentsMargins(16, 14, 16, 14)
        pin_lay.setSpacing(10)
        lbl_pin = QLabel("🔐 Ingresá el PIN de administrador para continuar:")
        lbl_pin.setStyleSheet(f"color: {_MUT}; font-size: 13px; background: transparent; border: none;")
        pin_lay.addWidget(lbl_pin)
        pin_row = QHBoxLayout()
        self.input_pin_borrado = QLineEdit()
        self.input_pin_borrado.setPlaceholderText("PIN (4 dígitos)")
        self.input_pin_borrado.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_pin_borrado.setMaxLength(6)
        self.input_pin_borrado.setFixedHeight(42)
        self.input_pin_borrado.setFixedWidth(160)
        self.input_pin_borrado.setStyleSheet(
            f"QLineEdit {{ background: {_BG}; border: 2px solid #e74c3c; border-radius: 8px; "
            f"padding: 8px; color: {_TXT}; font-size: 18px; letter-spacing: 4px; }}")
        pin_row.addWidget(self.input_pin_borrado)
        pin_row.addStretch()
        pin_lay.addLayout(pin_row)
        self.lbl_pin_error = QLabel("")
        self.lbl_pin_error.setStyleSheet("color: #e74c3c; font-size: 12px; background: transparent; border: none;")
        pin_lay.addWidget(self.lbl_pin_error)
        bor_layout.addWidget(pin_frame)

        btn_borrar = QPushButton("🗑️  BORRAR TODOS LOS DATOS DE VENTAS")
        btn_borrar.setFixedHeight(52)
        btn_borrar.setStyleSheet(
            "QPushButton { background: #7f1d1d; color: #fca5a5; border-radius: 10px; "
            "font-size: 14px; font-weight: bold; border: 2px solid #e74c3c; }"
            "QPushButton:hover { background: #e74c3c; color: white; }")
        btn_borrar.clicked.connect(self.ejecutar_borrado_ventas)
        bor_layout.addWidget(btn_borrar)
        bor_layout.addStretch()

        tabs.addTab(tab_borrado, "🗑️ Borrado")
        layout.addWidget(tabs)

    def ejecutar_borrado_ventas(self):
        PIN_ADMIN = "1722"
        pin = self.input_pin_borrado.text().strip()
        if pin != PIN_ADMIN:
            self.lbl_pin_error.setText("❌ PIN incorrecto")
            self.input_pin_borrado.clear()
            return
        self.lbl_pin_error.setText("")

        confirm = QMessageBox(self)
        confirm.setWindowTitle("⚠️ Confirmar borrado")
        confirm.setText("¿Estás SEGURO que querés borrar TODOS los datos de ventas?\n\nEsta acción NO se puede deshacer.")
        confirm.setIcon(QMessageBox.Icon.Warning)
        confirm.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        confirm.setDefaultButton(QMessageBox.StandardButton.No)
        confirm.button(QMessageBox.StandardButton.Yes).setText("Sí, borrar todo")
        confirm.button(QMessageBox.StandardButton.No).setText("Cancelar")
        confirm.setStyleSheet("QMessageBox { background: #1a1a2e; color: white; } QLabel { color: white; } QPushButton { background: #16213e; color: white; border-radius: 6px; padding: 6px 14px; }")
        if confirm.exec() != QMessageBox.StandardButton.Yes:
            return

        try:
            r = requests.post(f"{API_URL}/ventas/reset-ventas", json={"pin": PIN_ADMIN}, timeout=15)
            if r.status_code == 200:
                data = r.json()
                self.input_pin_borrado.clear()
                QMessageBox.information(self, "✅ Borrado exitoso",
                    f"Datos eliminados correctamente:\n\n"
                    f"🧾 Ventas: {data.get('ventas', 0)}\n"
                    f"📦 Items: {data.get('items', 0)}\n"
                    f"💳 Pagos: {data.get('pagos', 0)}\n"
                    f"🏧 Turnos de caja: {data.get('turnos', 0)}\n"
                    f"📋 Sesiones: {data.get('sesiones', 0)}")
            else:
                QMessageBox.critical(self, "Error", f"Error del servidor: {r.status_code}")
        except Exception as ex:
            QMessageBox.critical(self, "Error", f"No se pudo conectar al servidor:\n{ex}")

    def cargar_config(self):
        try:
            r = requests.get(f"{API_URL}/config/", timeout=5)
            if r.status_code == 200:
                self.config = r.json()
                self.inp_nombre.setText(self.config.get("negocio_nombre", ""))
                self.inp_direccion.setText(self.config.get("negocio_direccion", ""))
                self.inp_telefono.setText(self.config.get("negocio_telefono", ""))
                self.inp_cuit.setText(self.config.get("negocio_cuit", ""))
                self.inp_iibb.setText(self.config.get("negocio_iibb", ""))
                self.inp_inicio_act.setText(self.config.get("negocio_inicio_actividades", ""))
                iva = self.config.get("negocio_condicion_iva", "Responsable Inscripto")
                idx = self.combo_iva.findText(iva)
                if idx >= 0:
                    self.combo_iva.setCurrentIndex(idx)
                self.spin_timeout.setValue(self.config.get("timeout_minutos", 30))
                self.chk_offline.setChecked(self.config.get("modo_offline", True))
                self.chk_afip.setChecked(self.config.get("afip_habilitado", False))
                self.inp_punto_venta.setText(self.config.get("punto_venta", "0001"))

                # Sucursales
                sucursales = self.config.get("sucursales", [])
                self.tabla_suc.setRowCount(len(sucursales))
                self.combo_suc_actual.clear()
                for i, s in enumerate(sucursales):
                    self.tabla_suc.setItem(i, 0, QTableWidgetItem(s.get("id", "")))
                    self.tabla_suc.setItem(i, 1, QTableWidgetItem(s.get("nombre", "")))
                    self.tabla_suc.setItem(i, 2, QTableWidgetItem(s.get("direccion", "")))
                    self.combo_suc_actual.addItem(f"{s.get('id')} - {s.get('nombre')}", s.get("id"))
                suc_actual = self.config.get("sucursal_actual", "1")
                for i in range(self.combo_suc_actual.count()):
                    if self.combo_suc_actual.itemData(i) == suc_actual:
                        self.combo_suc_actual.setCurrentIndex(i)
                        break
        except Exception:
            pass

    def guardar_config(self):
        datos = {
            "negocio_nombre": self.inp_nombre.text().strip(),
            "negocio_direccion": self.inp_direccion.text().strip(),
            "negocio_telefono": self.inp_telefono.text().strip(),
            "negocio_cuit": self.inp_cuit.text().strip(),
            "negocio_iibb": self.inp_iibb.text().strip(),
            "negocio_inicio_actividades": self.inp_inicio_act.text().strip(),
            "negocio_condicion_iva": self.combo_iva.currentText(),
            "timeout_minutos": self.spin_timeout.value(),
            "modo_offline": self.chk_offline.isChecked(),
            "afip_habilitado": self.chk_afip.isChecked(),
            "punto_venta": self.inp_punto_venta.text().strip() or "0001",
            "sucursal_actual": self.combo_suc_actual.currentData() or "1",
        }
        try:
            r = requests.put(f"{API_URL}/config/", json=datos, timeout=5)
            if r.status_code == 200:
                QMessageBox.information(self, "✅", "Configuración guardada correctamente")
                # Actualizar ticket_utils si existe
                try:
                    from ui.pantallas.ticket_utils import guardar_config_negocio
                    guardar_config_negocio(
                        datos["negocio_nombre"],
                        datos["negocio_direccion"],
                        datos["negocio_telefono"],
                        "¡Gracias por su compra!"
                    )
                except Exception:
                    pass
            else:
                QMessageBox.critical(self, "Error", "No se pudo guardar")
        except Exception:
            QMessageBox.critical(self, "Error", "No se puede conectar al servidor")

    def nueva_sucursal(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Nueva sucursal")
        dialog.setMinimumWidth(360)
        dialog.setStyleSheet(f"background-color: {_CARD}; color: {_TXT};")
        lay = QVBoxLayout(dialog)
        lay.setSpacing(10)
        lay.setContentsMargins(20, 20, 20, 20)

        estilo = f"QLineEdit {{ background: {_BG}; border: 1.5px solid {_BOR}; border-radius: 8px; padding: 8px; color: {_TXT}; font-size: 13px; }}"

        lbl_id = QLabel("ID de sucursal (ej: 2):")
        lbl_id.setStyleSheet(f"color: {_MUT};")
        lay.addWidget(lbl_id)
        inp_id = QLineEdit(); inp_id.setFixedHeight(38); inp_id.setStyleSheet(estilo)
        lay.addWidget(inp_id)

        lbl_nom = QLabel("Nombre:")
        lbl_nom.setStyleSheet(f"color: {_MUT};")
        lay.addWidget(lbl_nom)
        inp_nom = QLineEdit(); inp_nom.setFixedHeight(38); inp_nom.setStyleSheet(estilo)
        lay.addWidget(inp_nom)

        lbl_dir = QLabel("Dirección:")
        lbl_dir.setStyleSheet(f"color: {_MUT};")
        lay.addWidget(lbl_dir)
        inp_dir = QLineEdit(); inp_dir.setFixedHeight(38); inp_dir.setStyleSheet(estilo)
        lay.addWidget(inp_dir)

        btns = QHBoxLayout()
        btn_c = QPushButton("Cancelar"); btn_c.setFixedHeight(38)
        btn_c.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_c.setStyleSheet(f"QPushButton {{ background: transparent; color: {_MUT}; border: 1px solid {_BOR}; border-radius: 8px; }}")
        btn_c.clicked.connect(dialog.reject)
        btns.addWidget(btn_c)
        btn_ok = QPushButton("Agregar"); btn_ok.setFixedHeight(38)
        btn_ok.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_ok.setStyleSheet(f"QPushButton {{ background: {_PRI}; color: white; border-radius: 8px; font-weight: bold; }} QPushButton:hover {{ background: {_T['primary_hover']}; }}")
        btns.addWidget(btn_ok)
        lay.addLayout(btns)

        def confirmar():
            if not inp_id.text().strip() or not inp_nom.text().strip():
                QMessageBox.warning(dialog, "Error", "ID y nombre son obligatorios")
                return
            try:
                r = requests.post(f"{API_URL}/config/sucursales", json={
                    "id": inp_id.text().strip(),
                    "nombre": inp_nom.text().strip(),
                    "direccion": inp_dir.text().strip()
                }, timeout=5)
                if r.status_code == 200:
                    dialog.accept()
                    self.cargar_config()
                else:
                    msg = r.json().get("detail", "Error")
                    QMessageBox.critical(dialog, "Error", msg)
            except Exception:
                QMessageBox.critical(dialog, "Error", "No se puede conectar")

        btn_ok.clicked.connect(confirmar)
        dialog.exec()

    def showEvent(self, event):
        super().showEvent(event)
        self.cargar_config()
