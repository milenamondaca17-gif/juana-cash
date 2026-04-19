import requests
import json
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QFrame, QMessageBox, QComboBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

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

        # Intentar cargar usuarios cada 3 segundos hasta que el servidor prenda
        self.timer_reconexion = QTimer()
        self.timer_reconexion.timeout.connect(self.cargar_usuarios_servidor)
        self.timer_reconexion.start(3000)

    def setup_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #050e1a; }
            QFrame#CajaLogin { background-color: #0a1628; border-radius: 20px; border: 2px solid #1a2744; }
            QLabel#Titulo { color: #e63946; font-size: 38px; font-weight: bold; }
            QLineEdit#PinDisplay { background: #050e1a; color: #e63946; border: none; font-size: 45px; font-weight: bold; text-align: center; }
            QPushButton#BtnIngresar { background-color: #34C38F; color: #050e1a; font-weight: bold; font-size: 22px; border-radius: 12px; min-height: 60px; }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        caja = QFrame()
        caja.setObjectName("CajaLogin")
        caja.setFixedSize(400, 740)
        lay_caja = QVBoxLayout(caja)
        lay_caja.setSpacing(8)

        lay_caja.addWidget(QLabel("JUANA CASH", objectName="Titulo",
                                  alignment=Qt.AlignmentFlag.AlignCenter))

        self.lbl_status = QLabel("🔄 Conectando al servidor...")
        self.lbl_status.setStyleSheet("color: #f39c12; font-size: 12px;")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay_caja.addWidget(self.lbl_status)

        self.combo_user = QComboBox()
        self.combo_user.setStyleSheet("""
            QComboBox {
                background: #111d33; color: white;
                padding: 10px; font-size: 16px;
                border-radius: 8px; border: 1px solid #1a2744;
            }
            QComboBox QAbstractItemView {
                background: #111d33; color: white;
                selection-background-color: #e63946;
            }
        """)
        lay_caja.addWidget(self.combo_user)

        self.input_password = QLineEdit()
        self.input_password.setObjectName("PinDisplay")
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password.setReadOnly(True)
        self.input_password.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay_caja.addWidget(self.input_password)

        # Teclado numérico
        grid = QVBoxLayout()
        grid.setSpacing(8)
        btn_style = """
            QPushButton {
                background: #1a2744; color: white;
                font-size: 24px; font-weight: bold;
                border-radius: 12px; min-height: 60px;
                border: 1px solid #263554;
            }
            QPushButton:hover { background: #263554; }
            QPushButton:pressed { background: #e63946; }
        """
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
        b_l = QPushButton("⌫ Borrar")
        b_l.setStyleSheet(btn_style)
        b_l.clicked.connect(self.limpiar)
        b_0 = QPushButton("0")
        b_0.setStyleSheet(btn_style)
        b_0.clicked.connect(lambda: self.tecla("0"))
        f_b.addWidget(b_l)
        f_b.addWidget(b_0)
        grid.addLayout(f_b)
        lay_caja.addLayout(grid)

        self.lbl_intentos = QLabel("")
        self.lbl_intentos.setStyleSheet("color: #e74c3c; font-size: 12px; font-weight: bold;")
        self.lbl_intentos.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay_caja.addWidget(self.lbl_intentos)

        btn_e = QPushButton("ENTRAR", objectName="BtnIngresar")
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
                self.lbl_status.setStyleSheet("color: #27ae60; font-size: 12px;")
                self.timer_reconexion.stop()
        except Exception:
            self.lbl_status.setText("❌ Servidor desconectado (reintentando...)")
            self.lbl_status.setStyleSheet("color: #e74c3c; font-size: 12px;")

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
