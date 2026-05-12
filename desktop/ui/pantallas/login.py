import requests
import json
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QFrame, QMessageBox, QComboBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from ui.theme import get_tema

_T = get_tema()

API_URL = "http://127.0.0.1:8000"
ARCHIVO_SESION = os.path.join(os.path.expanduser("~"), ".juanacash_sesion.json")
MAX_INTENTOS = 5

class LoginScreen(QWidget):
    def __init__(self, on_login_callback):
        super().__init__()
        self.on_login_callback = on_login_callback
        self.pin_acumulado = ""
        self.intentos_fallidos = 0
        self.bloqueado = False
        self.setup_ui()

        self.timer_reconexion = QTimer()
        self.timer_reconexion.timeout.connect(self.cargar_usuarios_servidor)
        self.timer_reconexion.start(3000)

    def setup_ui(self):
        self.setStyleSheet(f"QWidget {{ background-color: {_T['bg_app']}; }}")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Card central
        caja = QFrame()
        caja.setStyleSheet(f"""
            QFrame {{
                background-color: {_T['bg_card']};
                border-radius: 20px;
                border: 1.5px solid {_T['border_card']};
            }}
        """)
        caja.setFixedSize(400, 640)
        lay_caja = QVBoxLayout(caja)
        lay_caja.setSpacing(6)
        lay_caja.setContentsMargins(28, 16, 28, 16)

        # Logo / título
        lbl_logo = QLabel("JUANA CASH")
        lbl_logo.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_logo.setStyleSheet(f"color: {_T['logo_color']}; background: transparent; border: none; letter-spacing: 2px;")
        lay_caja.addWidget(lbl_logo)

        lbl_sub = QLabel("Sistema de punto de venta")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_sub.setStyleSheet(f"color: {_T['text_muted']}; font-size: 13px; background: transparent; border: none; margin-bottom: 8px;")
        lay_caja.addWidget(lbl_sub)

        # Status servidor
        self.lbl_status = QLabel("🔄 Conectando al servidor...")
        self.lbl_status.setStyleSheet(f"color: {_T['warning']}; font-size: 12px; background: transparent; border: none;")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay_caja.addWidget(self.lbl_status)

        # Separador
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {_T['border']}; border: none;")
        lay_caja.addWidget(sep)

        # Usuario
        lbl_user = QLabel("Usuario")
        lbl_user.setStyleSheet(f"color: {_T['text_muted']}; font-size: 12px; font-weight: bold; background: transparent; border: none; margin-top: 6px;")
        lay_caja.addWidget(lbl_user)

        self.combo_user = QComboBox()
        self.combo_user.setFixedHeight(44)
        self.combo_user.setStyleSheet(f"""
            QComboBox {{
                background: {_T['bg_input']};
                color: {_T['text_main']};
                padding: 8px 14px;
                font-size: 15px;
                border-radius: 10px;
                border: 1.5px solid {_T['border']};
            }}
            QComboBox:focus {{ border-color: {_T['primary']}; }}
            QComboBox::drop-down {{ border: none; width: 28px; }}
            QComboBox QAbstractItemView {{
                background: {_T['bg_card']};
                color: {_T['text_main']};
                selection-background-color: {_T['primary']};
                selection-color: white;
                border: 1px solid {_T['border']};
                border-radius: 8px;
            }}
        """)
        lay_caja.addWidget(self.combo_user)

        # PIN display
        lbl_pin = QLabel("PIN")
        lbl_pin.setStyleSheet(f"color: {_T['text_muted']}; font-size: 12px; font-weight: bold; background: transparent; border: none; margin-top: 4px;")
        lay_caja.addWidget(lbl_pin)

        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password.setReadOnly(True)
        self.input_password.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input_password.setFixedHeight(48)
        self.input_password.setStyleSheet(f"""
            QLineEdit {{
                background: {_T['bg_input']};
                color: {_T['primary']};
                border: 1.5px solid {_T['border']};
                border-radius: 10px;
                font-size: 32px;
                font-weight: bold;
                letter-spacing: 8px;
                padding: 0 12px;
            }}
            QLineEdit:focus {{ border-color: {_T['primary']}; }}
        """)
        lay_caja.addWidget(self.input_password)

        # Teclado numérico
        btn_style = f"""
            QPushButton {{
                background: {_T['bg_input']};
                color: {_T['text_main']};
                font-size: 18px;
                font-weight: bold;
                border-radius: 10px;
                min-height: 44px;
                border: 1.5px solid {_T['border']};
            }}
            QPushButton:hover {{ background: {_T['bg_hover']}; border-color: {_T['primary']}; }}
            QPushButton:pressed {{ background: {_T['primary']}; color: white; border-color: {_T['primary']}; }}
        """

        grid = QVBoxLayout()
        grid.setSpacing(8)
        for fila in [["1","2","3"], ["4","5","6"], ["7","8","9"]]:
            h = QHBoxLayout()
            h.setSpacing(8)
            for n in fila:
                b = QPushButton(n)
                b.setStyleSheet(btn_style)
                b.clicked.connect(lambda _, x=n: self.tecla(x))
                h.addWidget(b)
            grid.addLayout(h)

        f_b = QHBoxLayout()
        f_b.setSpacing(8)
        b_l = QPushButton("⌫")
        b_l.setStyleSheet(btn_style)
        b_l.clicked.connect(self.limpiar)
        b_0 = QPushButton("0")
        b_0.setStyleSheet(btn_style)
        b_0.clicked.connect(lambda: self.tecla("0"))
        f_b.addWidget(b_l)
        f_b.addWidget(b_0)
        grid.addLayout(f_b)
        lay_caja.addLayout(grid)

        # Intentos fallidos
        self.lbl_intentos = QLabel("")
        self.lbl_intentos.setStyleSheet(f"color: {_T['danger']}; font-size: 12px; font-weight: bold; background: transparent; border: none;")
        self.lbl_intentos.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay_caja.addWidget(self.lbl_intentos)

        # Botón ingresar
        btn_e = QPushButton("INGRESAR")
        btn_e.setFixedHeight(44)
        btn_e.setStyleSheet(f"""
            QPushButton {{
                background: {_T['primary']};
                color: white;
                font-size: 15px;
                font-weight: bold;
                border-radius: 10px;
                border: none;
            }}
            QPushButton:hover {{ background: {_T['primary_hover']}; }}
            QPushButton:pressed {{ background: {_T['primary_hover']}; }}
        """)
        btn_e.clicked.connect(self.hacer_login)
        lay_caja.addWidget(btn_e)

        layout.addWidget(caja)

    def tecla(self, n):
        if self.bloqueado:
            return
        if len(self.pin_acumulado) < 6:
            self.pin_acumulado += n
            self.input_password.setText(self.pin_acumulado)

    def limpiar(self):
        self.pin_acumulado = ""
        self.input_password.clear()

    def cargar_usuarios_servidor(self):
        try:
            r = requests.get(f"{API_URL}/auth/usuarios", timeout=2)
            if r.status_code == 200:
                usuarios = r.json()
                self.combo_user.clear()
                for u in usuarios:
                    if u.get("activo", True):
                        self.combo_user.addItem(u["nombre"], u["email"])
                self.lbl_status.setText("✅ Servidor conectado")
                self.lbl_status.setStyleSheet(f"color: {_T['success']}; font-size: 12px; background: transparent; border: none;")
                self.timer_reconexion.stop()
        except Exception:
            self.lbl_status.setText("❌ Servidor desconectado (reintentando...)")
            self.lbl_status.setStyleSheet(f"color: {_T['danger']}; font-size: 12px; background: transparent; border: none;")

    def hacer_login(self):
        if self.bloqueado:
            return
        email = self.combo_user.currentData()
        if not email:
            QMessageBox.warning(self, "Aviso", "Seleccioná un usuario")
            return
        if not self.pin_acumulado:
            QMessageBox.warning(self, "Aviso", "Ingresá tu PIN")
            return
        try:
            r = requests.post(f"{API_URL}/auth/login",
                json={"email": email, "password": self.pin_acumulado}, timeout=5)
            if r.status_code == 200:
                self.intentos_fallidos = 0
                self.lbl_intentos.setText("")
                datos = r.json()
                try:
                    with open(ARCHIVO_SESION, "w") as f:
                        json.dump(datos, f)
                except Exception:
                    pass
                self.on_login_callback(datos)
            else:
                self._registrar_intento_fallido()
        except Exception:
            QMessageBox.critical(self, "Error de conexión",
                "No se puede conectar al servidor.\nVerificá que el backend esté corriendo.")

    def _registrar_intento_fallido(self):
        self.intentos_fallidos += 1
        restantes = MAX_INTENTOS - self.intentos_fallidos
        self.limpiar()
        if self.intentos_fallidos >= MAX_INTENTOS:
            self._bloquear()
        else:
            self.lbl_intentos.setText(f"❌ PIN incorrecto — {restantes} intento(s) restante(s)")

    def _bloquear(self):
        self.bloqueado = True
        self.lbl_intentos.setText("🔒 Bloqueado por 60 segundos")
        QTimer.singleShot(60000, self._desbloquear)

    def _desbloquear(self):
        self.bloqueado = False
        self.intentos_fallidos = 0
        self.lbl_intentos.setText("")
