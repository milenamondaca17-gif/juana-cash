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


class ConfigScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.config = {}
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("background-color: #1a1a2e; color: white;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        header = QHBoxLayout()
        titulo = QLabel("⚙️ Configuración del Sistema")
        titulo.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        titulo.setStyleSheet("color: white;")
        header.addWidget(titulo)
        header.addStretch()
        btn_guardar = QPushButton("💾 Guardar todo")
        btn_guardar.setFixedHeight(36)
        btn_guardar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_guardar.setStyleSheet("QPushButton { background: #27ae60; color: white; border-radius: 8px; font-size: 13px; font-weight: bold; padding: 0 16px; } QPushButton:hover { background: #1e8449; }")
        btn_guardar.clicked.connect(self.guardar_config)
        header.addWidget(btn_guardar)
        layout.addLayout(header)

        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #0f3460; background: #16213e; border-radius: 8px; }
            QTabBar::tab { background: #0f3460; color: #a0a0b0; padding: 8px 16px; border-radius: 4px; margin-right: 4px; }
            QTabBar::tab:selected { background: #e94560; color: white; }
        """)

        # ── Tab 1: Datos del negocio ──────────────────────────────────────
        tab_negocio = QWidget()
        tab_negocio.setStyleSheet("background: transparent;")
        neg_layout = QFormLayout(tab_negocio)
        neg_layout.setContentsMargins(20, 20, 20, 20)
        neg_layout.setSpacing(12)
        neg_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        estilo_input = "QLineEdit { background: #0f3460; border: 1px solid #e94560; border-radius: 8px; padding: 8px; color: white; font-size: 13px; }"

        self.inp_nombre      = QLineEdit(); self.inp_nombre.setStyleSheet(estilo_input); self.inp_nombre.setFixedHeight(38)
        self.inp_direccion   = QLineEdit(); self.inp_direccion.setStyleSheet(estilo_input); self.inp_direccion.setFixedHeight(38)
        self.inp_telefono    = QLineEdit(); self.inp_telefono.setStyleSheet(estilo_input); self.inp_telefono.setFixedHeight(38)
        self.inp_cuit        = QLineEdit(); self.inp_cuit.setStyleSheet(estilo_input); self.inp_cuit.setFixedHeight(38); self.inp_cuit.setPlaceholderText("XX-XXXXXXXX-X")
        self.inp_iibb        = QLineEdit(); self.inp_iibb.setStyleSheet(estilo_input); self.inp_iibb.setFixedHeight(38)
        self.inp_inicio_act  = QLineEdit(); self.inp_inicio_act.setStyleSheet(estilo_input); self.inp_inicio_act.setFixedHeight(38); self.inp_inicio_act.setPlaceholderText("DD/MM/AAAA")

        self.combo_iva = QComboBox()
        self.combo_iva.addItems(["Responsable Inscripto", "Monotributista", "Exento", "Consumidor Final"])
        self.combo_iva.setFixedHeight(38)
        self.combo_iva.setStyleSheet("QComboBox { background: #0f3460; border: 1px solid #e94560; border-radius: 8px; padding: 8px; color: white; font-size: 13px; } QComboBox::drop-down { border: none; } QComboBox QAbstractItemView { background: #0f3460; color: white; selection-background-color: #e94560; }")

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
            lbl.setStyleSheet("color: #a0a0b0; font-size: 13px;")
            neg_layout.addRow(lbl, widget)

        tabs.addTab(tab_negocio, "🏪 Negocio")

        # ── Tab 2: Sucursales ─────────────────────────────────────────────
        tab_suc = QWidget()
        tab_suc.setStyleSheet("background: transparent;")
        suc_layout = QVBoxLayout(tab_suc)
        suc_layout.setContentsMargins(20, 20, 20, 20)
        suc_layout.setSpacing(12)

        suc_header = QHBoxLayout()
        lbl_suc = QLabel("Sucursales del negocio")
        lbl_suc.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        suc_header.addWidget(lbl_suc)
        suc_header.addStretch()
        btn_nueva_suc = QPushButton("+ Nueva sucursal")
        btn_nueva_suc.setFixedHeight(32)
        btn_nueva_suc.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_nueva_suc.setStyleSheet("QPushButton { background: #e94560; color: white; border-radius: 6px; font-size: 12px; padding: 0 12px; }")
        btn_nueva_suc.clicked.connect(self.nueva_sucursal)
        suc_header.addWidget(btn_nueva_suc)
        suc_layout.addLayout(suc_header)

        self.tabla_suc = QTableWidget()
        self.tabla_suc.setColumnCount(3)
        self.tabla_suc.setHorizontalHeaderLabels(["ID", "Nombre", "Dirección"])
        self.tabla_suc.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla_suc.setColumnWidth(0, 60)
        self.tabla_suc.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tabla_suc.setStyleSheet("QTableWidget { background: #0f3460; border: 1px solid #16213e; border-radius: 8px; color: white; } QHeaderView::section { background: #16213e; color: #a0a0b0; padding: 6px; border: none; } QTableWidgetItem { color: white; padding: 6px; }")
        self.tabla_suc.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        suc_layout.addWidget(self.tabla_suc)

        lbl_suc_actual = QLabel("Sucursal activa:")
        lbl_suc_actual.setStyleSheet("color: #a0a0b0; font-size: 13px;")
        suc_layout.addWidget(lbl_suc_actual)
        self.combo_suc_actual = QComboBox()
        self.combo_suc_actual.setFixedHeight(38)
        self.combo_suc_actual.setStyleSheet("QComboBox { background: #0f3460; border: 1px solid #3498db; border-radius: 8px; padding: 8px; color: white; font-size: 13px; } QComboBox::drop-down { border: none; } QComboBox QAbstractItemView { background: #0f3460; color: white; selection-background-color: #e94560; }")
        suc_layout.addWidget(self.combo_suc_actual)
        suc_layout.addStretch()

        tabs.addTab(tab_suc, "🏬 Sucursales")

        # ── Tab 3: Sistema ────────────────────────────────────────────────
        tab_sis = QWidget()
        tab_sis.setStyleSheet("background: transparent;")
        sis_layout = QVBoxLayout(tab_sis)
        sis_layout.setContentsMargins(20, 20, 20, 20)
        sis_layout.setSpacing(16)

        # Timeout
        timeout_frame = QFrame()
        timeout_frame.setStyleSheet("QFrame { background: #0f3460; border-radius: 10px; }")
        tf_lay = QVBoxLayout(timeout_frame)
        tf_lay.setContentsMargins(16, 12, 16, 12)
        lbl_to = QLabel("⏱ Timeout de sesión automático")
        lbl_to.setStyleSheet("color: white; font-size: 13px; font-weight: bold;")
        tf_lay.addWidget(lbl_to)
        lbl_to_desc = QLabel("Cierra la sesión automáticamente después de X minutos sin actividad.")
        lbl_to_desc.setStyleSheet("color: #a0a0b0; font-size: 12px;")
        tf_lay.addWidget(lbl_to_desc)
        to_fila = QHBoxLayout()
        lbl_min = QLabel("Minutos de inactividad:")
        lbl_min.setStyleSheet("color: #a0a0b0; font-size: 13px;")
        to_fila.addWidget(lbl_min)
        self.spin_timeout = QSpinBox()
        self.spin_timeout.setRange(1, 480)
        self.spin_timeout.setValue(30)
        self.spin_timeout.setSuffix(" min")
        self.spin_timeout.setFixedHeight(38)
        self.spin_timeout.setFixedWidth(120)
        self.spin_timeout.setStyleSheet("QSpinBox { background: #1a1a2e; border: 1px solid #e94560; border-radius: 8px; padding: 6px; color: white; font-size: 14px; }")
        to_fila.addWidget(self.spin_timeout)
        to_fila.addStretch()
        tf_lay.addLayout(to_fila)
        sis_layout.addWidget(timeout_frame)

        # Modo offline
        offline_frame = QFrame()
        offline_frame.setStyleSheet("QFrame { background: #0f3460; border-radius: 10px; }")
        of_lay = QVBoxLayout(offline_frame)
        of_lay.setContentsMargins(16, 12, 16, 12)
        lbl_of = QLabel("📡 Modo offline robusto")
        lbl_of.setStyleSheet("color: white; font-size: 13px; font-weight: bold;")
        of_lay.addWidget(lbl_of)
        lbl_of_desc = QLabel("Cuando el servidor no responde, las ventas se guardan localmente\ny se sincronizan automáticamente cuando vuelve la conexión.")
        lbl_of_desc.setStyleSheet("color: #a0a0b0; font-size: 12px;")
        of_lay.addWidget(lbl_of_desc)
        self.chk_offline = QCheckBox("Activar modo offline")
        self.chk_offline.setStyleSheet("QCheckBox { color: white; font-size: 13px; } QCheckBox::indicator { width: 18px; height: 18px; }")
        self.chk_offline.setChecked(True)
        of_lay.addWidget(self.chk_offline)
        sis_layout.addWidget(offline_frame)

        # AFIP
        afip_frame = QFrame()
        afip_frame.setStyleSheet("QFrame { background: #0f3460; border-radius: 10px; border: 1px solid #3498db; }")
        af_lay = QVBoxLayout(afip_frame)
        af_lay.setContentsMargins(16, 12, 16, 12)
        lbl_af = QLabel("🧾 Facturación ARCA/AFIP")
        lbl_af.setStyleSheet("color: #3498db; font-size: 13px; font-weight: bold;")
        af_lay.addWidget(lbl_af)
        lbl_af_desc = QLabel("Generá tickets fiscales B para consumidor final.\nRequiere CUIT cargado y punto de venta configurado.")
        lbl_af_desc.setStyleSheet("color: #a0a0b0; font-size: 12px;")
        af_lay.addWidget(lbl_af_desc)

        af_fila = QHBoxLayout()
        lbl_pv = QLabel("Punto de venta:")
        lbl_pv.setStyleSheet("color: #a0a0b0; font-size: 13px;")
        af_fila.addWidget(lbl_pv)
        self.inp_punto_venta = QLineEdit()
        self.inp_punto_venta.setPlaceholderText("0001")
        self.inp_punto_venta.setFixedWidth(80)
        self.inp_punto_venta.setFixedHeight(36)
        self.inp_punto_venta.setStyleSheet("QLineEdit { background: #1a1a2e; border: 1px solid #3498db; border-radius: 6px; padding: 6px; color: white; font-size: 13px; }")
        af_fila.addWidget(self.inp_punto_venta)
        af_fila.addStretch()
        af_lay.addLayout(af_fila)

        self.chk_afip = QCheckBox("Activar facturación (genera comprobantes B)")
        self.chk_afip.setStyleSheet("QCheckBox { color: white; font-size: 13px; } QCheckBox::indicator { width: 18px; height: 18px; }")
        af_lay.addWidget(self.chk_afip)
        sis_layout.addWidget(afip_frame)
        sis_layout.addStretch()

        tabs.addTab(tab_sis, "🖥️ Sistema")
        layout.addWidget(tabs)

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
        dialog.setStyleSheet("background-color: #1a1a2e; color: white;")
        lay = QVBoxLayout(dialog)
        lay.setSpacing(10)
        lay.setContentsMargins(20, 20, 20, 20)

        estilo = "QLineEdit { background: #0f3460; border: 1px solid #e94560; border-radius: 8px; padding: 8px; color: white; font-size: 13px; }"

        lbl_id = QLabel("ID de sucursal (ej: 2):")
        lbl_id.setStyleSheet("color: #a0a0b0;")
        lay.addWidget(lbl_id)
        inp_id = QLineEdit(); inp_id.setFixedHeight(38); inp_id.setStyleSheet(estilo)
        lay.addWidget(inp_id)

        lbl_nom = QLabel("Nombre:")
        lbl_nom.setStyleSheet("color: #a0a0b0;")
        lay.addWidget(lbl_nom)
        inp_nom = QLineEdit(); inp_nom.setFixedHeight(38); inp_nom.setStyleSheet(estilo)
        lay.addWidget(inp_nom)

        lbl_dir = QLabel("Dirección:")
        lbl_dir.setStyleSheet("color: #a0a0b0;")
        lay.addWidget(lbl_dir)
        inp_dir = QLineEdit(); inp_dir.setFixedHeight(38); inp_dir.setStyleSheet(estilo)
        lay.addWidget(inp_dir)

        btns = QHBoxLayout()
        btn_c = QPushButton("Cancelar"); btn_c.setFixedHeight(38)
        btn_c.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_c.setStyleSheet("QPushButton { background: transparent; color: #a0a0b0; border: 1px solid #a0a0b0; border-radius: 8px; }")
        btn_c.clicked.connect(dialog.reject)
        btns.addWidget(btn_c)
        btn_ok = QPushButton("Agregar"); btn_ok.setFixedHeight(38)
        btn_ok.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_ok.setStyleSheet("QPushButton { background: #e94560; color: white; border-radius: 8px; font-weight: bold; }")
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
