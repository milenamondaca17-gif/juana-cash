import requests
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QLineEdit, QFrame, QMessageBox,
                              QTableWidget, QTableWidgetItem, QHeaderView,
                              QDialog, QDoubleSpinBox, QSpinBox, QComboBox,
                              QCheckBox, QProgressBar, QScrollArea)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

API_URL = "http://127.0.0.1:8000"


class PreviewDialog(QDialog):
    """Vista previa de cómo quedarán los precios antes de aplicar."""
    def __init__(self, parent=None, porcentaje=0, redondeo=0, categoria_id=None):
        super().__init__(parent)
        self.setWindowTitle("👁 Vista previa de precios")
        self.setMinimumSize(580, 480)
        self.setStyleSheet("background-color: #1a1a2e; color: white;")
        self.porcentaje = porcentaje
        self.redondeo = redondeo
        self.categoria_id = categoria_id
        self.setup_ui()
        self.cargar()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        titulo = QLabel(f"Vista previa — +{self.porcentaje:.1f}%"
                        + (f" redondeado a ${self.redondeo}" if self.redondeo else ""))
        titulo.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        titulo.setStyleSheet("color: #f39c12;")
        layout.addWidget(titulo)

        lbl_info = QLabel("Mostrando hasta 20 productos. Los cambios NO se aplicaron aún.")
        lbl_info.setStyleSheet("color: #a0a0b0; font-size: 11px;")
        layout.addWidget(lbl_info)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels(["Producto", "Precio actual", "Precio nuevo"])
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabla.setColumnWidth(1, 120)
        self.tabla.setColumnWidth(2, 120)
        self.tabla.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tabla.setStyleSheet("""
            QTableWidget { background: #16213e; border: 1px solid #0f3460; border-radius: 8px; gridline-color: #0f3460; }
            QHeaderView::section { background: #0f3460; color: #a0a0b0; padding: 6px; border: none; }
            QTableWidgetItem { color: white; padding: 6px; }
        """)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.tabla)

        btns = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setFixedHeight(40)
        btn_cancelar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_cancelar.setStyleSheet("QPushButton { background: transparent; color: #a0a0b0; border: 1px solid #a0a0b0; border-radius: 8px; }")
        btn_cancelar.clicked.connect(self.reject)
        btns.addWidget(btn_cancelar)

        self.btn_aplicar = QPushButton("✅ Aplicar a TODOS los productos")
        self.btn_aplicar.setFixedHeight(40)
        self.btn_aplicar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_aplicar.setStyleSheet("QPushButton { background: #e94560; color: white; border-radius: 8px; font-size: 13px; font-weight: bold; padding: 0 16px; }")
        self.btn_aplicar.clicked.connect(self.accept)
        btns.addWidget(self.btn_aplicar)
        layout.addLayout(btns)

    def cargar(self):
        try:
            params = {"porcentaje": self.porcentaje, "redondeo": self.redondeo}
            if self.categoria_id:
                params["categoria_id"] = self.categoria_id
            r = requests.get(f"{API_URL}/productos/preview-actualizacion",
                             params=params, timeout=5)
            if r.status_code == 200:
                datos = r.json()
                self.tabla.setRowCount(len(datos))
                for i, p in enumerate(datos):
                    self.tabla.setItem(i, 0, QTableWidgetItem(p["nombre"]))
                    self.tabla.setItem(i, 1, QTableWidgetItem(f"${p['precio_actual']:,.2f}"))
                    item_nuevo = QTableWidgetItem(f"${p['precio_nuevo']:,.2f}")
                    item_nuevo.setForeground(QColor("#f39c12"))
                    self.tabla.setItem(i, 2, item_nuevo)
        except Exception:
            pass


class PreciosMasivosScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.categorias = []
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("background-color: #1a1a2e; color: white;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        titulo = QLabel("💰 Actualización Masiva de Precios")
        titulo.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        titulo.setStyleSheet("color: white;")
        layout.addWidget(titulo)

        desc = QLabel("Actualizá los precios de todos tus productos por inflación en segundos.")
        desc.setStyleSheet("color: #a0a0b0; font-size: 13px;")
        layout.addWidget(desc)

        # ── Panel de configuración ────────────────────────────────────────────
        config_frame = QFrame()
        config_frame.setStyleSheet("QFrame { background: #16213e; border-radius: 12px; }")
        config_layout = QVBoxLayout(config_frame)
        config_layout.setContentsMargins(24, 20, 24, 20)
        config_layout.setSpacing(16)

        lbl_config = QLabel("⚙️ Configuración del ajuste")
        lbl_config.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        lbl_config.setStyleSheet("color: #f39c12;")
        config_layout.addWidget(lbl_config)

        fila1 = QHBoxLayout()
        fila1.setSpacing(16)

        # Porcentaje
        col_pct = QVBoxLayout()
        lbl_pct = QLabel("Porcentaje de aumento (%):")
        lbl_pct.setStyleSheet("color: #a0a0b0; font-size: 13px;")
        col_pct.addWidget(lbl_pct)
        self.input_pct = QDoubleSpinBox()
        self.input_pct.setRange(0.1, 999.9)
        self.input_pct.setValue(15.0)
        self.input_pct.setSuffix(" %")
        self.input_pct.setDecimals(1)
        self.input_pct.setFixedHeight(44)
        self.input_pct.setStyleSheet("QDoubleSpinBox { background: #0f3460; border: 1px solid #f39c12; border-radius: 8px; padding: 8px; color: white; font-size: 16px; font-weight: bold; }")
        col_pct.addWidget(self.input_pct)
        fila1.addLayout(col_pct)

        # Redondeo
        col_red = QVBoxLayout()
        lbl_red = QLabel("Redondeo de precios:")
        lbl_red.setStyleSheet("color: #a0a0b0; font-size: 13px;")
        col_red.addWidget(lbl_red)
        self.combo_redondeo = QComboBox()
        self.combo_redondeo.addItems([
            "Sin redondeo",
            "Redondear a $10",
            "Redondear a $50",
            "Redondear a $100",
            "Redondear a $500",
        ])
        self.combo_redondeo.setFixedHeight(44)
        self.combo_redondeo.setStyleSheet("""
            QComboBox { background: #0f3460; border: 1px solid #3498db; border-radius: 8px; padding: 8px; color: white; font-size: 14px; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { background: #0f3460; color: white; selection-background-color: #e94560; }
        """)
        col_red.addWidget(self.combo_redondeo)
        fila1.addLayout(col_red)

        # Categoría
        col_cat = QVBoxLayout()
        lbl_cat = QLabel("Aplicar a:")
        lbl_cat.setStyleSheet("color: #a0a0b0; font-size: 13px;")
        col_cat.addWidget(lbl_cat)
        self.combo_cat = QComboBox()
        self.combo_cat.addItem("📦 Todos los productos", None)
        self.combo_cat.setFixedHeight(44)
        self.combo_cat.setStyleSheet("""
            QComboBox { background: #0f3460; border: 1px solid #9b59b6; border-radius: 8px; padding: 8px; color: white; font-size: 14px; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { background: #0f3460; color: white; selection-background-color: #e94560; }
        """)
        col_cat.addWidget(self.combo_cat)
        fila1.addLayout(col_cat)

        config_layout.addLayout(fila1)

        # Atajos rápidos de porcentaje
        lbl_rapido = QLabel("Atajos rápidos:")
        lbl_rapido.setStyleSheet("color: #a0a0b0; font-size: 12px;")
        config_layout.addWidget(lbl_rapido)

        rapidos = QHBoxLayout()
        rapidos.setSpacing(8)
        for pct in [5, 10, 15, 20, 30, 50, 100]:
            btn = QPushButton(f"+{pct}%")
            btn.setFixedSize(60, 32)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.setStyleSheet("QPushButton { background: #0f3460; color: #f39c12; border: 1px solid #f39c12; border-radius: 6px; font-size: 12px; font-weight: bold; } QPushButton:hover { background: #f39c12; color: white; }")
            btn.clicked.connect(lambda _, p=pct: self.input_pct.setValue(p))
            rapidos.addWidget(btn)
        rapidos.addStretch()
        config_layout.addLayout(rapidos)

        layout.addWidget(config_frame)

        # ── Preview y resultado ────────────────────────────────────────────────
        preview_frame = QFrame()
        preview_frame.setStyleSheet("QFrame { background: #16213e; border-radius: 12px; border: 1px solid #f39c12; }")
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setContentsMargins(20, 16, 20, 16)
        preview_layout.setSpacing(10)

        self.lbl_simulacion = QLabel("Configurá el porcentaje y hacé clic en Vista Previa")
        self.lbl_simulacion.setStyleSheet("color: #a0a0b0; font-size: 13px;")
        preview_layout.addWidget(self.lbl_simulacion)

        btns_accion = QHBoxLayout()
        btn_preview = QPushButton("👁 Vista Previa")
        btn_preview.setFixedHeight(44)
        btn_preview.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_preview.setStyleSheet("QPushButton { background: #3498db; color: white; border-radius: 8px; font-size: 14px; font-weight: bold; padding: 0 20px; } QPushButton:hover { background: #2980b9; }")
        btn_preview.clicked.connect(self.mostrar_preview)
        btns_accion.addWidget(btn_preview)

        btn_aplicar = QPushButton("🚀 Aplicar ahora")
        btn_aplicar.setFixedHeight(44)
        btn_aplicar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_aplicar.setStyleSheet("QPushButton { background: #e94560; color: white; border-radius: 8px; font-size: 14px; font-weight: bold; padding: 0 20px; } QPushButton:hover { background: #c73652; }")
        btn_aplicar.clicked.connect(self.aplicar_con_confirmacion)
        btns_accion.addWidget(btn_aplicar)
        btns_accion.addStretch()
        preview_layout.addLayout(btns_accion)

        layout.addWidget(preview_frame)

        # ── Historial de la sesión ────────────────────────────────────────────
        self.historial_frame = QFrame()
        self.historial_frame.setStyleSheet("QFrame { background: #16213e; border-radius: 12px; }")
        historial_layout = QVBoxLayout(self.historial_frame)
        historial_layout.setContentsMargins(20, 14, 20, 14)
        lbl_h = QLabel("📋 Historial de esta sesión")
        lbl_h.setStyleSheet("color: #a0a0b0; font-size: 12px; font-weight: bold;")
        historial_layout.addWidget(lbl_h)
        self.lbl_historial = QLabel("Sin cambios aplicados aún.")
        self.lbl_historial.setStyleSheet("color: #555; font-size: 12px;")
        self.lbl_historial.setWordWrap(True)
        historial_layout.addWidget(self.lbl_historial)
        layout.addWidget(self.historial_frame)

        layout.addStretch()

        # Cargar categorías
        self.cargar_categorias()

    def cargar_categorias(self):
        try:
            r = requests.get(f"{API_URL}/productos/categorias", timeout=5)
            if r.status_code == 200:
                self.categorias = r.json()
                for cat in self.categorias:
                    self.combo_cat.addItem(f"  {cat['nombre']}", cat["id"])
        except Exception:
            pass

    def get_redondeo(self):
        idx = self.combo_redondeo.currentIndex()
        return [0, 10, 50, 100, 500][idx]

    def mostrar_preview(self):
        pct = self.input_pct.value()
        redondeo = self.get_redondeo()
        cat_id = self.combo_cat.currentData()
        dialog = PreviewDialog(self, pct, redondeo, cat_id)
        if dialog.exec():
            self.aplicar_directo(pct, redondeo, cat_id)

    def aplicar_con_confirmacion(self):
        pct = self.input_pct.value()
        redondeo = self.get_redondeo()
        cat_id = self.combo_cat.currentData()
        cat_nombre = self.combo_cat.currentText().strip()

        msg = f"¿Aplicar +{pct:.1f}% a {cat_nombre}?"
        if redondeo:
            msg += f"\nRedondeando a ${redondeo}"
        msg += "\n\n⚠️ Esta acción no se puede deshacer."

        resp = QMessageBox.question(self, "Confirmar actualización", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp == QMessageBox.StandardButton.Yes:
            self.aplicar_directo(pct, redondeo, cat_id)

    def aplicar_directo(self, pct, redondeo, cat_id):
        try:
            payload = {
                "porcentaje": pct,
                "redondeo": redondeo,
                "categoria_id": cat_id,
                "solo_precio_venta": True
            }
            r = requests.post(f"{API_URL}/productos/actualizacion-masiva",
                              json=payload, timeout=15)
            if r.status_code == 200:
                datos = r.json()
                n = datos["actualizados"]
                red_txt = f" (redondeado a ${redondeo})" if redondeo else ""
                self.lbl_simulacion.setText(
                    f"✅ Se actualizaron {n} productos con +{pct:.1f}%{red_txt}"
                )
                self.lbl_simulacion.setStyleSheet("color: #27ae60; font-size: 14px; font-weight: bold;")
                hist = self.lbl_historial.text()
                if hist == "Sin cambios aplicados aún.":
                    hist = ""
                self.lbl_historial.setText(
                    hist + f"• +{pct:.1f}%{red_txt} → {n} productos\n"
                )
                self.lbl_historial.setStyleSheet("color: #a0a0b0; font-size: 12px;")
                QMessageBox.information(self, "✅ Listo",
                    f"Se actualizaron {n} productos con +{pct:.1f}%{red_txt}")
            else:
                QMessageBox.critical(self, "Error", "No se pudo aplicar la actualización")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se puede conectar al servidor\n{str(e)}")

    def showEvent(self, event):
        super().showEvent(event)
        if not self.categorias:
            self.cargar_categorias()
