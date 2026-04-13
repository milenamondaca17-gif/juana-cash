import requests
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QLineEdit, QPushButton, QFrame, QMessageBox,
                              QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

API_URL = "http://127.0.0.1:8000"
TURNOS = ["Mañana (06:00 - 14:00)", "Tarde (14:00 - 22:00)", "Noche (22:00 - 06:00)"]

class TurnoScreen(QWidget):
    def __init__(self, on_turno_callback, admin_usuario):
        super().__init__()
        self.on_turno_callback = on_turno_callback
        self.admin_usuario = admin_usuario
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("background-color: #1a1a2e;")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo = QLabel("👤 Identificación de cajero")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        titulo.setStyleSheet("color: #e94560; margin-bottom: 8px;")
        layout.addWidget(titulo)
        sub = QLabel("Ingresá tus datos para comenzar el turno")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color: #a0a0b0; font-size: 14px; margin-bottom: 30px;")
        layout.addWidget(sub)
        card = QFrame()
        card.setMaximumWidth(440)
        card.setStyleSheet("QFrame { background: #16213e; border-radius: 12px; padding: 20px; }")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(14)
        lbl_nombre = QLabel("Tu nombre")
        lbl_nombre.setStyleSheet("color: #a0a0b0; font-size: 13px;")
        card_layout.addWidget(lbl_nombre)
        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Ej: María González")
        self.input_nombre.setFixedHeight(44)
        self.input_nombre.setStyleSheet("QLineEdit { background: #0f3460; border: 1px solid #e94560; border-radius: 8px; padding: 10px; color: white; font-size: 14px; }")
        card_layout.addWidget(self.input_nombre)
        lbl_turno = QLabel("Turno")
        lbl_turno.setStyleSheet("color: #a0a0b0; font-size: 13px;")
        card_layout.addWidget(lbl_turno)
        self.combo_turno = QComboBox()
        self.combo_turno.addItems(TURNOS)
        self.combo_turno.setFixedHeight(44)
        self.combo_turno.setStyleSheet("QComboBox { background: #0f3460; border: 1px solid #e94560; border-radius: 8px; padding: 10px; color: white; font-size: 14px; } QComboBox::drop-down { border: none; } QComboBox QAbstractItemView { background: #0f3460; color: white; selection-background-color: #e94560; }")
        card_layout.addWidget(self.combo_turno)
        lbl_pin = QLabel("Tu contraseña o PIN")
        lbl_pin.setStyleSheet("color: #a0a0b0; font-size: 13px;")
        card_layout.addWidget(lbl_pin)
        self.input_pin = QLineEdit()
        self.input_pin.setPlaceholderText("••••••••")
        self.input_pin.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_pin.setFixedHeight(44)
        self.input_pin.setStyleSheet("QLineEdit { background: #0f3460; border: 1px solid #e94560; border-radius: 8px; padding: 10px; color: white; font-size: 14px; }")
        self.input_pin.returnPressed.connect(self.confirmar)
        card_layout.addWidget(self.input_pin)
        btns = QHBoxLayout()
        btn_volver = QPushButton("← Volver")
        btn_volver.setFixedHeight(44)
        btn_volver.setStyleSheet("QPushButton { background: transparent; color: #a0a0b0; border: 1px solid #a0a0b0; border-radius: 8px; font-size: 14px; }")
        btn_volver.clicked.connect(lambda: self.on_turno_callback(None))
        btns.addWidget(btn_volver)
        btn_confirmar = QPushButton("✅ Comenzar turno")
        btn_confirmar.setFixedHeight(44)
        btn_confirmar.setStyleSheet("QPushButton { background: #e94560; color: white; border-radius: 8px; font-size: 15px; font-weight: bold; } QPushButton:hover { background: #c73652; }")
        btn_confirmar.clicked.connect(self.confirmar)
        btns.addWidget(btn_confirmar)
        card_layout.addLayout(btns)
        lbl_admin = QLabel(f"Admin: {self.admin_usuario.get('nombre', '')} | Sesión activa")
        lbl_admin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_admin.setStyleSheet("color: #a0a0b0; font-size: 12px; margin-top: 10px;")
        card_layout.addWidget(lbl_admin)
        layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)

    def confirmar(self):
        nombre = self.input_nombre.text().strip()
        pin = self.input_pin.text().strip()
        turno = self.combo_turno.currentText()
        if not nombre:
            QMessageBox.warning(self, "Error", "Ingresá tu nombre")
            return
        if not pin:
            QMessageBox.warning(self, "Error", "Ingresá tu contraseña o PIN")
            return
        cajero = {
            "nombre": nombre,
            "turno": turno,
            "rol": "cajero",
            "id": self.admin_usuario.get("id", 1)
        }
        try:
            requests.post(f"{API_URL}/sesiones/registrar", json={
                "usuario_id": cajero["id"],
                "nombre_cajero": nombre,
                "turno": turno,
                "accion": "APERTURA_TURNO",
                "detalle": f"Turno iniciado: {turno}"
            }, timeout=3)
        except Exception:
            pass
        self.on_turno_callback(cajero)