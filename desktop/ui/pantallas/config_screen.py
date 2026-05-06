import requests
import json
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QLineEdit, QFrame, QMessageBox,
                              QSpinBox, QCheckBox, QTabWidget, QFormLayout,
                              QComboBox, QScrollArea, QDialog, QTableWidget,
                              QTableWidgetItem, QHeaderView, QFileDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

API_URL = "http://127.0.0.1:8000"

from ui.theme import get_tema as _gt, TEMAS, guardar_tema, get_tema_key, get_qss
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

        # ── TAB: PALETAS DE COLORES ──────────────────────────────────────────────
        tab_paleta = QWidget()
        tab_paleta.setStyleSheet(f"background: {_CARD};")
        pal_layout = QVBoxLayout(tab_paleta)
        pal_layout.setContentsMargins(20, 20, 20, 20)
        pal_layout.setSpacing(10)

        lbl_pal_t = QLabel("🎨 Paleta de colores")
        lbl_pal_t.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        lbl_pal_t.setStyleSheet(f"color: {_TXT}; background: transparent;")
        pal_layout.addWidget(lbl_pal_t)

        lbl_pal_sub = QLabel("Elegí un tema. La app se reinicia automáticamente para aplicarlo.")
        lbl_pal_sub.setStyleSheet(f"color: {_MUT}; font-size: 12px; background: transparent;")
        pal_layout.addWidget(lbl_pal_sub)

        actual = get_tema_key()
        previews = {
            "violeta_calido": ("#7C3AED", "#10B981", "#EEEAFF"),
            "naranja_cielo":  ("#EA580C", "#0EA5E9", "#FFE8D0"),
            "rosa_sage":      ("#DB2777", "#4ADE80", "#FFD6EC"),
            "lila_sol":       ("#9333EA", "#FDE047", "#EDE0FF"),
            "clasico_oscuro": ("#556EE6", "#34C38F", "#050e1a"),
        }

        for key, tema in TEMAS.items():
            cols = previews.get(key, ("#888", "#888", "#fff"))
            es_actual = (key == actual)
            fila = QFrame()
            fila.setStyleSheet(f"QFrame {{ background: {_BG}; border-radius: 12px; border: 2px solid {_PRI if es_actual else _BOR}; }}")
            fila_lay = QHBoxLayout(fila)
            fila_lay.setContentsMargins(14, 10, 14, 10)
            for c in cols:
                dot = QFrame()
                dot.setFixedSize(20, 20)
                dot.setStyleSheet(f"background: {c}; border-radius: 10px; border: 1px solid rgba(0,0,0,0.1);")
                fila_lay.addWidget(dot)
            lbl_n = QLabel(tema["nombre"])
            lbl_n.setStyleSheet(f"color: {_TXT}; font-size: 14px; font-weight: {'bold' if es_actual else 'normal'}; background: transparent; margin-left: 8px;")
            fila_lay.addWidget(lbl_n)
            if es_actual:
                lbl_ok = QLabel("✓ Activo")
                lbl_ok.setStyleSheet(f"color: {_OK}; font-size: 12px; font-weight: bold; background: transparent;")
                fila_lay.addWidget(lbl_ok)
            fila_lay.addStretch()
            btn_ap = QPushButton("Aplicar")
            btn_ap.setFixedHeight(32)
            btn_ap.setEnabled(not es_actual)
            btn_ap.setStyleSheet(f"QPushButton {{ background: {_PRI}; color: white; border-radius: 6px; font-size: 12px; font-weight: bold; padding: 0 14px; }} QPushButton:disabled {{ background: {_BOR}; color: {_MUT}; }} QPushButton:hover {{ background: {_T['primary_hover']}; }}")
            def _aplicar(k=key):
                import traceback
                from PyQt6.QtWidgets import QApplication
                guardar_tema(k)
                app = QApplication.instance()
                for w in app.topLevelWidgets():
                    if hasattr(w, 'recargar_tema'):
                        try:
                            w.recargar_tema(k)
                        except Exception:
                            QMessageBox.critical(None, "Error al cambiar tema",
                                traceback.format_exc())
                        return
                QMessageBox.information(None, "Tema guardado",
                    f"✅ Tema '{TEMAS[k]['nombre']}' guardado.\nCerrá y volvé a abrir la app.")
            btn_ap.clicked.connect(lambda _=None, fn=_aplicar: fn())
            fila_lay.addWidget(btn_ap)
            pal_layout.addWidget(fila)

        pal_layout.addStretch()
        tabs.addTab(tab_paleta, "🎨 Paletas")

        # ── TAB: TICKET ──────────────────────────────────────────────────────
        tab_ticket = QWidget()
        tab_ticket.setStyleSheet(f"background: {_CARD};")
        tkt_main = QHBoxLayout(tab_ticket)
        tkt_main.setContentsMargins(20, 20, 20, 20)
        tkt_main.setSpacing(20)

        # ── Columna izquierda: formulario ─────────────────────────────────
        tkt_form_wrap = QWidget()
        tkt_form_wrap.setMaximumWidth(340)
        tkt_form = QVBoxLayout(tkt_form_wrap)
        tkt_form.setContentsMargins(0, 0, 0, 0)
        tkt_form.setSpacing(10)

        lbl_tkt_t = QLabel("🖨️ Personalización del ticket")
        lbl_tkt_t.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        lbl_tkt_t.setStyleSheet(f"color: {_TXT}; background: transparent;")
        tkt_form.addWidget(lbl_tkt_t)

        lbl_tkt_s = QLabel("El nombre del negocio se toma de la pestaña Negocio.")
        lbl_tkt_s.setWordWrap(True)
        lbl_tkt_s.setStyleSheet(f"color: {_MUT}; font-size: 11px; background: transparent;")
        tkt_form.addWidget(lbl_tkt_s)

        ei = f"QLineEdit {{ background: {_BG}; border: 1.5px solid {_BOR}; border-radius: 8px; padding: 7px; color: {_TXT}; font-size: 13px; }}"

        def _campo(label_txt, placeholder=""):
            lbl = QLabel(label_txt)
            lbl.setStyleSheet(f"color: {_MUT}; font-size: 12px; font-weight: bold; background: transparent;")
            inp = QLineEdit()
            inp.setPlaceholderText(placeholder)
            inp.setFixedHeight(36)
            inp.setStyleSheet(ei)
            return lbl, inp

        lbl_sub, self.tkt_subtitulo = _campo("Sub-título (bajo el nombre):", "Almacén y Carnicería")
        lbl_m1,  self.tkt_msg1      = _campo("Mensaje de cierre 1:", "Gracias por su compra!")
        lbl_m2,  self.tkt_msg2      = _campo("Mensaje de cierre 2:", "Vuelva pronto :)")
        lbl_tel, self.tkt_telefono  = _campo("Teléfono de contacto:", "351 000-0000")
        lbl_wa,  self.tkt_whatsapp  = _campo("WhatsApp:", "351 000-0000")
        lbl_ig,  self.tkt_instagram = _campo("Instagram (sin @):", "mi.negocio")
        lbl_fb,  self.tkt_facebook  = _campo("Facebook:", "Mi Negocio")

        for lbl, inp in [(lbl_sub, self.tkt_subtitulo), (lbl_m1, self.tkt_msg1),
                         (lbl_m2, self.tkt_msg2), (lbl_tel, self.tkt_telefono),
                         (lbl_wa, self.tkt_whatsapp), (lbl_ig, self.tkt_instagram),
                         (lbl_fb, self.tkt_facebook)]:
            tkt_form.addWidget(lbl)
            tkt_form.addWidget(inp)
            inp.textChanged.connect(self._actualizar_preview_ticket)

        btn_tkt = QPushButton("💾 Guardar configuración del ticket")
        btn_tkt.setFixedHeight(40)
        btn_tkt.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_tkt.setStyleSheet(f"QPushButton {{ background: {_OK}; color: white; border-radius: 8px; font-size: 13px; font-weight: bold; }} QPushButton:hover {{ background: #059669; }}")
        btn_tkt.clicked.connect(self._guardar_config_ticket)
        tkt_form.addWidget(btn_tkt)
        tkt_form.addStretch()
        tkt_main.addWidget(tkt_form_wrap)

        # ── Columna derecha: preview ──────────────────────────────────────
        from PyQt6.QtWidgets import QTextEdit
        preview_wrap = QVBoxLayout()
        lbl_prev = QLabel("Vista previa del ticket")
        lbl_prev.setStyleSheet(f"color: {_MUT}; font-size: 11px; font-weight: bold; background: transparent;")
        preview_wrap.addWidget(lbl_prev)
        self.tkt_preview = QTextEdit()
        self.tkt_preview.setReadOnly(True)
        self.tkt_preview.setFont(QFont("Courier New", 10))
        self.tkt_preview.setStyleSheet(f"""
            QTextEdit {{
                background: #f5f5f0; color: #1a1a1a;
                border: 1.5px solid {_BOR}; border-radius: 8px;
                padding: 10px; font-size: 11px;
            }}
        """)
        preview_wrap.addWidget(self.tkt_preview)
        tkt_main.addLayout(preview_wrap, stretch=1)

        tabs.addTab(tab_ticket, "🖨️ Ticket")

        # ── TAB: RESPALDO ────────────────────────────────────────────────────
        tab_resp = QWidget()
        tab_resp.setStyleSheet(f"background: {_CARD};")
        _tab_resp_outer = QVBoxLayout(tab_resp)
        _tab_resp_outer.setContentsMargins(0, 0, 0, 0)
        _tab_resp_outer.setSpacing(0)
        _scroll_resp = QScrollArea()
        _scroll_resp.setWidgetResizable(True)
        _scroll_resp.setStyleSheet(f"QScrollArea {{ background: {_CARD}; border: none; }} QScrollBar:vertical {{ background: {_BG}; width: 6px; border-radius: 3px; }} QScrollBar::handle:vertical {{ background: {_BOR}; border-radius: 3px; }}")
        _inner_resp = QWidget()
        _inner_resp.setStyleSheet(f"background: {_CARD};")
        _scroll_resp.setWidget(_inner_resp)
        _tab_resp_outer.addWidget(_scroll_resp)
        resp_layout = QVBoxLayout(_inner_resp)
        resp_layout.setContentsMargins(20, 20, 20, 20)
        resp_layout.setSpacing(14)

        lbl_resp_t = QLabel("💾 Respaldo y Restauración")
        lbl_resp_t.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        lbl_resp_t.setStyleSheet(f"color: {_TXT}; background: transparent;")
        resp_layout.addWidget(lbl_resp_t)

        # ── Qué incluye ──────────────────────────────────────────────────────
        inc_frame = QFrame()
        inc_frame.setStyleSheet(f"QFrame {{ background: {_BG}; border-radius: 10px; border: 1.5px solid {_BOR}; }}")
        inc_lay = QVBoxLayout(inc_frame)
        inc_lay.setContentsMargins(16, 12, 16, 12)
        inc_lay.setSpacing(4)
        lbl_inc_t = QLabel("📦 El respaldo incluye:")
        lbl_inc_t.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        lbl_inc_t.setStyleSheet(f"color: {_TXT}; background: transparent;")
        inc_lay.addWidget(lbl_inc_t)
        for item in ["✅ Todas las ventas del día y el historial completo",
                     "✅ Productos y cambios de precios",
                     "✅ Clientes y fiados",
                     "✅ Cierres de caja",
                     "✅ Configuración del negocio y del ticket"]:
            l = QLabel(f"  {item}")
            l.setStyleSheet(f"color: {_MUT}; font-size: 12px; background: transparent;")
            inc_lay.addWidget(l)
        resp_layout.addWidget(inc_frame)

        # ── Crear respaldo ────────────────────────────────────────────────────
        exp_frame = QFrame()
        exp_frame.setStyleSheet(f"QFrame {{ background: {_BG}; border-radius: 10px; border: 1.5px solid {_OK}; }}")
        exp_lay = QVBoxLayout(exp_frame)
        exp_lay.setContentsMargins(16, 14, 16, 14)
        exp_lay.setSpacing(8)
        lbl_exp_t = QLabel("⬇️  Crear respaldo manual")
        lbl_exp_t.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        lbl_exp_t.setStyleSheet(f"color: {_OK}; background: transparent;")
        exp_lay.addWidget(lbl_exp_t)
        lbl_exp_s = QLabel("Genera un archivo .zip que podés guardar en un pendrive, OneDrive o mandarte por WhatsApp.\nSi se rompe la PC, con ese archivo recuperás todo en una PC nueva.")
        lbl_exp_s.setWordWrap(True)
        lbl_exp_s.setStyleSheet(f"color: {_MUT}; font-size: 12px; background: transparent;")
        exp_lay.addWidget(lbl_exp_s)
        self.lbl_ultimo_respaldo = QLabel("Último respaldo: nunca")
        self.lbl_ultimo_respaldo.setStyleSheet(f"color: {_MUT}; font-size: 11px; background: transparent;")
        exp_lay.addWidget(self.lbl_ultimo_respaldo)
        btn_exp = QPushButton("📦 Crear respaldo ahora")
        btn_exp.setFixedHeight(42)
        btn_exp.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_exp.setStyleSheet(f"QPushButton {{ background: {_OK}; color: white; border-radius: 8px; font-size: 14px; font-weight: bold; }} QPushButton:hover {{ background: #059669; }}")
        btn_exp.clicked.connect(self._crear_respaldo)
        exp_lay.addWidget(btn_exp)
        resp_layout.addWidget(exp_frame)

        # ── Restaurar ─────────────────────────────────────────────────────────
        rest_frame = QFrame()
        rest_frame.setStyleSheet(f"QFrame {{ background: {_BG}; border-radius: 10px; border: 1.5px solid {_BOR}; }}")
        rest_lay = QVBoxLayout(rest_frame)
        rest_lay.setContentsMargins(16, 14, 16, 14)
        rest_lay.setSpacing(8)
        lbl_rest_t = QLabel("⬆️  Restaurar en esta PC")
        lbl_rest_t.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        lbl_rest_t.setStyleSheet(f"color: {_PRI}; background: transparent;")
        rest_lay.addWidget(lbl_rest_t)
        lbl_rest_s = QLabel("Seleccioná un archivo de respaldo (.zip) para recuperar todos los datos.\nLa app se cierra al terminar — volvé a abrirla para que los cambios tomen efecto.")
        lbl_rest_s.setWordWrap(True)
        lbl_rest_s.setStyleSheet(f"color: {_MUT}; font-size: 12px; background: transparent;")
        rest_lay.addWidget(lbl_rest_s)
        btn_rest = QPushButton("📂 Seleccionar respaldo y restaurar")
        btn_rest.setFixedHeight(42)
        btn_rest.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_rest.setStyleSheet(f"QPushButton {{ background: {_PRI}; color: white; border-radius: 8px; font-size: 14px; font-weight: bold; }} QPushButton:hover {{ background: {_T['primary_hover']}; }}")
        btn_rest.clicked.connect(self._restaurar_respaldo)
        rest_lay.addWidget(btn_rest)
        resp_layout.addWidget(rest_frame)

        # ── Backups automáticos 22:15 ─────────────────────────────────────────
        auto_frame = QFrame()
        auto_frame.setStyleSheet(f"QFrame {{ background: {_BG}; border-radius: 10px; border: 1.5px solid {_BOR}; }}")
        auto_lay = QVBoxLayout(auto_frame)
        auto_lay.setContentsMargins(16, 12, 16, 12)
        auto_lay.setSpacing(6)
        lbl_auto_t = QLabel("🕙 Respaldos automáticos (22:15 cada día)")
        lbl_auto_t.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        lbl_auto_t.setStyleSheet(f"color: {_TXT}; background: transparent;")
        auto_lay.addWidget(lbl_auto_t)
        self.lbl_auto_lista = QLabel("Cargando...")
        self.lbl_auto_lista.setStyleSheet(f"color: {_MUT}; font-size: 12px; background: transparent;")
        self.lbl_auto_lista.setWordWrap(True)
        auto_lay.addWidget(self.lbl_auto_lista)
        btn_auto_exp = QPushButton("📦 Exportar un auto-respaldo")
        btn_auto_exp.setFixedHeight(36)
        btn_auto_exp.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_auto_exp.setStyleSheet(f"QPushButton {{ background: transparent; color: {_PRI}; border: 1.5px solid {_PRI}; border-radius: 8px; font-size: 12px; font-weight: bold; }} QPushButton:hover {{ background: {_PRI}; color: white; }}")
        btn_auto_exp.clicked.connect(self._exportar_auto_respaldo)
        auto_lay.addWidget(btn_auto_exp)
        resp_layout.addWidget(auto_frame)

        resp_layout.addStretch()
        tabs.addTab(tab_resp, "💾 Respaldo")

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
                # Sincronizar nombre del negocio al config del ticket
                try:
                    from ui.pantallas.impresora import guardar_config_ticket
                    guardar_config_ticket({"nombre_negocio": datos["negocio_nombre"]})
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

    # ─── Respaldo ────────────────────────────────────────────────────────────

    def _data_dir(self):
        return os.path.join(os.path.expanduser("~"), "JuanaCash_Data")

    def _crear_respaldo(self):
        import zipfile
        from datetime import datetime
        data_dir = self._data_dir()
        db_path  = os.path.join(data_dir, "juana_cash.db")

        fecha = datetime.now().strftime("%Y%m%d_%H%M")
        nombre_default = f"JuanaCash_Respaldo_{fecha}.zip"
        escritorio = os.path.join(os.path.expanduser("~"), "Desktop")
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar respaldo",
            os.path.join(escritorio, nombre_default),
            "Archivos ZIP (*.zip)"
        )
        if not ruta:
            return
        try:
            with zipfile.ZipFile(ruta, "w", zipfile.ZIP_DEFLATED) as zf:
                if os.path.exists(db_path):
                    zf.write(db_path, "juana_cash.db")
                for cfg in ["ticket_config.json", "email_config.json", "version_installed.json"]:
                    p = os.path.join(data_dir, cfg)
                    if os.path.exists(p):
                        zf.write(p, cfg)
            tam = os.path.getsize(ruta) // 1024
            QMessageBox.information(self, "✅ Respaldo creado",
                f"Respaldo guardado correctamente ({tam} KB):\n\n{ruta}\n\n"
                "Guardalo en un pendrive o mandátelo por WhatsApp\npara tenerlo seguro.")
            self._actualizar_estado_respaldo()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo crear el respaldo:\n{e}")

    def _restaurar_respaldo(self):
        import zipfile
        escritorio = os.path.join(os.path.expanduser("~"), "Desktop")
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar archivo de respaldo",
            escritorio,
            "Archivos ZIP (*.zip)"
        )
        if not ruta:
            return

        resp = QMessageBox.question(self, "⚠️ Confirmar restauración",
            f"Archivo seleccionado:\n{os.path.basename(ruta)}\n\n"
            "Esto va a REEMPLAZAR todos los datos actuales\n(ventas, productos, clientes, caja).\n\n"
            "La app se cierra al terminar — volvé a abrirla.\n\n"
            "¿Confirmar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resp != QMessageBox.StandardButton.Yes:
            return

        try:
            data_dir = self._data_dir()
            os.makedirs(data_dir, exist_ok=True)
            with zipfile.ZipFile(ruta, "r") as zf:
                zf.extractall(data_dir)
            QMessageBox.information(self, "✅ Restaurado",
                "Datos restaurados correctamente.\n\nCerrá y volvé a abrir la app.")
            from PyQt6.QtWidgets import QApplication
            QApplication.instance().quit()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo restaurar:\n{e}")

    def _exportar_auto_respaldo(self):
        import zipfile
        data_dir   = self._data_dir()
        backup_dir = os.path.join(data_dir, "backups")
        if not os.path.exists(backup_dir):
            QMessageBox.information(self, "Sin respaldos",
                "Todavía no hay respaldos automáticos.\nSe generan todos los días a las 22:15.")
            return
        archivos = sorted(
            [f for f in os.listdir(backup_dir) if f.endswith(".db")],
            reverse=True
        )
        if not archivos:
            QMessageBox.information(self, "Sin respaldos",
                "No se encontraron respaldos automáticos.")
            return
        # Exportar el más reciente
        db_auto = os.path.join(backup_dir, archivos[0])
        fecha   = archivos[0].replace("juana_cash_", "").replace(".db", "")
        nombre  = f"JuanaCash_AutoRespaldo_{fecha}.zip"
        escritorio = os.path.join(os.path.expanduser("~"), "Desktop")
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar auto-respaldo",
            os.path.join(escritorio, nombre),
            "Archivos ZIP (*.zip)"
        )
        if not ruta:
            return
        try:
            with zipfile.ZipFile(ruta, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.write(db_auto, "juana_cash.db")
                for cfg in ["ticket_config.json", "email_config.json"]:
                    p = os.path.join(data_dir, cfg)
                    if os.path.exists(p):
                        zf.write(p, cfg)
            QMessageBox.information(self, "✅", f"Auto-respaldo exportado:\n{ruta}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _actualizar_estado_respaldo(self):
        data_dir   = self._data_dir()
        backup_dir = os.path.join(data_dir, "backups")
        # Último respaldo manual (buscar .zip en Desktop)
        escritorio = os.path.join(os.path.expanduser("~"), "Desktop")
        try:
            zips = [f for f in os.listdir(escritorio) if f.startswith("JuanaCash_Respaldo_") and f.endswith(".zip")]
            if zips:
                ultimo = sorted(zips)[-1]
                fecha_str = ultimo.replace("JuanaCash_Respaldo_", "").replace(".zip", "")
                self.lbl_ultimo_respaldo.setText(f"Último respaldo: {fecha_str[:8][:4]}-{fecha_str[:8][4:6]}-{fecha_str[:8][6:]} {fecha_str[9:11]}:{fecha_str[11:13]}")
                self.lbl_ultimo_respaldo.setStyleSheet(f"color: {_OK}; font-size: 11px; background: transparent;")
        except Exception:
            pass
        # Lista de auto-backups
        try:
            if os.path.exists(backup_dir):
                archivos = sorted(
                    [f for f in os.listdir(backup_dir) if f.endswith(".db")],
                    reverse=True
                )
                if archivos:
                    lista = "\n".join(
                        f"  • {f.replace('juana_cash_','').replace('.db','')}"
                        for f in archivos[:7]
                    )
                    self.lbl_auto_lista.setText(f"Últimos respaldos automáticos:\n{lista}")
                else:
                    self.lbl_auto_lista.setText("Todavía no hay respaldos automáticos (se generan a las 22:15).")
            else:
                self.lbl_auto_lista.setText("Todavía no hay respaldos automáticos (se generan a las 22:15).")
        except Exception:
            pass

    # ─── Ticket ──────────────────────────────────────────────────────────────

    def _cargar_config_ticket(self):
        try:
            from ui.pantallas.impresora import leer_config_ticket
            cfg = leer_config_ticket()
            self.tkt_subtitulo.setText(cfg.get("subtitulo", ""))
            self.tkt_msg1.setText(cfg.get("mensaje1", "Gracias por su compra!"))
            self.tkt_msg2.setText(cfg.get("mensaje2", "Vuelva pronto :)"))
            self.tkt_telefono.setText(cfg.get("telefono", ""))
            self.tkt_whatsapp.setText(cfg.get("whatsapp", ""))
            self.tkt_instagram.setText(cfg.get("instagram", ""))
            self.tkt_facebook.setText(cfg.get("facebook", ""))
        except Exception:
            pass
        self._actualizar_preview_ticket()

    def _actualizar_preview_ticket(self):
        try:
            from ui.pantallas.impresora import leer_config_ticket
            cfg = leer_config_ticket()
        except Exception:
            cfg = {}

        nombre   = cfg.get("nombre_negocio", self.inp_nombre.text().strip() or "JUANA CASH")
        subtitulo = self.tkt_subtitulo.text().strip()
        msg1     = self.tkt_msg1.text().strip() or "Gracias por su compra!"
        msg2     = self.tkt_msg2.text().strip() or "Vuelva pronto :)"
        telefono = self.tkt_telefono.text().strip()
        whatsapp = self.tkt_whatsapp.text().strip()
        instagram = self.tkt_instagram.text().strip()
        facebook  = self.tkt_facebook.text().strip()

        A = 32
        def c(t): return str(t).center(A)
        def lr(l, r):
            sp = A - len(str(l)) - len(str(r))
            return str(l) + " " * max(1, sp) + str(r)

        lineas = []
        lineas.append("=" * A)
        lineas.append(c(nombre.upper()))
        if subtitulo:
            lineas.append(c(subtitulo))
        lineas.append("=" * A)
        lineas.append("Ticket N: 0001")
        lineas.append(f"Fecha: {__import__('datetime').datetime.now().strftime('%d/%m/%Y %H:%M')}")
        lineas.append("-" * A)
        lineas.append("CANT DESCRIPCION        TOTAL")
        lineas.append("-" * A)
        lineas.append(lr("2x  Coca Cola 500ml", "$1200"))
        lineas.append(lr("1x  Pan lactal", "$800"))
        lineas.append(lr("3x  Alfajor", "$1050"))
        lineas.append("-" * A)
        lineas.append(lr("TOTAL A PAGAR:", "$3050"))
        lineas.append(lr("Pago:", "Efectivo"))
        lineas.append(lr("Vuelto:", "$950"))
        lineas.append("=" * A)
        lineas.append(c(msg1))
        lineas.append(c(msg2))
        if telefono:
            lineas.append(c(f"Tel: {telefono}"))
        if whatsapp:
            lineas.append(c(f"WA:  {whatsapp}"))
        if instagram:
            lineas.append(c(f"IG:  @{instagram.lstrip('@')}"))
        if facebook:
            lineas.append(c(f"FB:  {facebook}"))

        self.tkt_preview.setPlainText("\n".join(lineas))

    def _guardar_config_ticket(self):
        try:
            from ui.pantallas.impresora import guardar_config_ticket
            datos = {
                "subtitulo": self.tkt_subtitulo.text().strip(),
                "mensaje1":  self.tkt_msg1.text().strip() or "Gracias por su compra!",
                "mensaje2":  self.tkt_msg2.text().strip() or "Vuelva pronto :)",
                "telefono":  self.tkt_telefono.text().strip(),
                "whatsapp":  self.tkt_whatsapp.text().strip(),
                "instagram": self.tkt_instagram.text().strip(),
                "facebook":  self.tkt_facebook.text().strip(),
            }
            if guardar_config_ticket(datos):
                QMessageBox.information(self, "✅", "Configuración del ticket guardada")
            else:
                QMessageBox.critical(self, "Error", "No se pudo guardar el archivo de configuración")
        except Exception as ex:
            QMessageBox.critical(self, "Error", str(ex))

    def showEvent(self, event):
        super().showEvent(event)
        self.cargar_config()
        self._cargar_config_ticket()
        self._actualizar_estado_respaldo()
