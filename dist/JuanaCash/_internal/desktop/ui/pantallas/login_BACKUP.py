import requests
import json
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel,
                              QLineEdit, QPushButton, QFrame, QMessageBox, QCheckBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

API_URL = "http://127.0.0.1:8000"
ARCHIVO_SESION = os.path.join(os.path.expanduser("~"), ".juanacash_sesion.json")

class LoginScreen(QWidget):
    def __init__(self, on_login_callback):
        super().__init__()
        self.on_login_callback = on_login_callback
        self.setup_ui()
        self.cargar_sesion_guardada()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)
        self.setStyleSheet("background-color: #1a1a2e;")

        titulo = QLabel("💰 JUANA CASH")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setFont(QFont("Arial", 36, QFont.Weight.Bold))
        titulo.setStyleSheet("color: #e94560; margin-bottom: 10px;")
        layout.addWidget(titulo)

        subtitulo = QLabel("Sistema POS Profesional")
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitulo.setFont(QFont("Arial", 14))
        subtitulo.setStyleSheet("color: #a0a0b0; margin-bottom: 40px;")
        layout.addWidget(subtitulo)

        card = QFrame()
        card.setMaximumWidth(400)
        card.setStyleSheet("""
            QFrame {
                background-color: #16213e;
                border-radius: 12px;
                padding: 30px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(16)

        lbl_email = QLabel("Email")
        lbl_email.setStyleSheet("color: #a0a0b0; font-size: 13px;")
        card_layout.addWidget(lbl_email)

        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("tu@email.com")
        self.input_email.setStyleSheet("""
            QLineEdit {
                background: #0f3460;
                border: 1px solid #e94560;
                border-radius: 8px;
                padding: 12px;
                color: white;
                font-size: 14px;
            }
        """)
        card_layout.addWidget(self.input_email)

        lbl_pass = QLabel("Contraseña")
        lbl_pass.setStyleSheet("color: #a0a0b0; font-size: 13px;")
        card_layout.addWidget(lbl_pass)

        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("••••••••")
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password.setStyleSheet("""
            QLineEdit {
                background: #0f3460;
                border: 1px solid #e94560;
                border-radius: 8px;
                padding: 12px;
                color: white;
                font-size: 14px;
            }
        """)
        self.input_password.returnPressed.connect(self.hacer_login)
        card_layout.addWidget(self.input_password)

        self.check_recordar = QCheckBox("Recordarme")
        self.check_recordar.setStyleSheet("color: #a0a0b0; font-size: 13px;")
        card_layout.addWidget(self.check_recordar)

        btn_login = QPushButton("INGRESAR")
        btn_login.setFixedHeight(48)
        btn_login.setStyleSheet("""
            QPushButton {
                background-color: #e94560;
                color: white;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #c73652; }
        """)
        btn_login.clicked.connect(self.hacer_login)
        card_layout.addWidget(btn_login)

        layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)

    def cargar_sesion_guardada(self):
        try:
            if os.path.exists(ARCHIVO_SESION):
                with open(ARCHIVO_SESION, "r") as f:
                    datos = json.load(f)
                    self.input_email.setText(datos.get("email", ""))
                    self.input_password.setText(datos.get("password", ""))
                    self.check_recordar.setChecked(True)
        except Exception:
            pass

    def guardar_sesion(self, email, password):
        try:
            with open(ARCHIVO_SESION, "w") as f:
                json.dump({"email": email, "password": password}, f)
        except Exception:
            pass

    def borrar_sesion(self):
        try:
            if os.path.exists(ARCHIVO_SESION):
                os.remove(ARCHIVO_SESION)
        except Exception:
            pass

    def hacer_login(self):
        email = self.input_email.text().strip()
        password = self.input_password.text().strip()
        if not email or not password:
            QMessageBox.warning(self, "Error", "Completá email y contraseña")
            return
        try:
            response = requests.post(f"{API_URL}/auth/login", json={
                "email": email, "password": password
            }, timeout=5)
            if response.status_code == 200:
                if self.check_recordar.isChecked():
                    self.guardar_sesion(email, password)
                else:
                    self.borrar_sesion()
                self.on_login_callback(response.json())
            else:
                QMessageBox.warning(self, "Error", "Email o contraseña incorrectos")
        except Exception:
            QMessageBox.critical(self, "Error de conexión",
                "No se puede conectar al servidor.\nAsegurate que el backend esté corriendo.")