import requests
import json
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QFrame, QMessageBox, QComboBox)
from PyQt6.QtCore import Qt, QTimer

API_URL = "http://127.0.0.1:8000"
# Definimos la ruta del archivo de sesión para que no tire error
ARCHIVO_SESION = os.path.join(os.path.expanduser("~"), ".juanacash_sesion.json")

class LoginScreen(QWidget):
    def __init__(self, on_login_callback):
        super().__init__()
        self.on_login_callback = on_login_callback
        self.pin_acumulado = ""
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
            QPushButton.BtnNum { background: #1a2744; color: white; font-size: 24px; font-weight: bold; border-radius: 12px; min-height: 60px; }
            QPushButton#BtnIngresar { background-color: #34C38F; color: #050e1a; font-weight: bold; font-size: 22px; border-radius: 12px; min-height: 60px; }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        caja = QFrame(); caja.setObjectName("CajaLogin"); caja.setFixedSize(400, 700)
        lay_caja = QVBoxLayout(caja)

        lay_caja.addWidget(QLabel("JUANA CASH", objectName="Titulo", alignment=Qt.AlignmentFlag.AlignCenter))
        self.lbl_status = QLabel("🔄 Conectando al servidor...")
        self.lbl_status.setStyleSheet("color: #f39c12; font-size: 12px;")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay_caja.addWidget(self.lbl_status)

        self.combo_user = QComboBox()
        self.combo_user.setStyleSheet("background: #111d33; color: white; padding: 10px; font-size: 16px;")
        lay_caja.addWidget(self.combo_user)

        self.input_password = QLineEdit()
        self.input_password.setObjectName("PinDisplay")
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password.setReadOnly(True)
        lay_caja.addWidget(self.input_password)

        grid = QVBoxLayout()
        for fila in [["1","2","3"],["4","5","6"],["7","8","9"]]:
            h = QHBoxLayout()
            for n in fila:
                b = QPushButton(n); b.setProperty("class", "BtnNum")
                b.clicked.connect(lambda _, x=n: self.tecla(x))
                h.addWidget(b)
            grid.addLayout(h)
        
        f_b = QHBoxLayout()
        b_l = QPushButton("Borrar"); b_l.clicked.connect(self.limpiar)
        b_0 = QPushButton("0"); b_0.setProperty("class", "BtnNum"); b_0.clicked.connect(lambda: self.tecla("0"))
        f_b.addWidget(b_l); f_b.addWidget(b_0)
        grid.addLayout(f_b)
        lay_caja.addLayout(grid)

        btn_e = QPushButton("ENTRAR", objectName="BtnIngresar")
        btn_e.clicked.connect(self.hacer_login)
        lay_caja.addWidget(btn_e)
        layout.addWidget(caja)

    def tecla(self, n):
        if len(self.pin_acumulado) < 4:
            self.pin_acumulado += n
            self.input_password.setText(self.pin_acumulado)

    def limpiar(self):
        self.pin_acumulado = ""; self.input_password.clear()

    def cargar_usuarios_servidor(self):
        try:
            r = requests.get(f"{API_URL}/auth/usuarios", timeout=2) 
            if r.status_code == 200:
                usuarios = r.json()
                self.combo_user.clear()
                for u in usuarios:
                    self.combo_user.addItem(u["nombre"], u["email"])
                
                self.lbl_status.setText("✅ Servidor conectado")
                self.lbl_status.setStyleSheet("color: #27ae60;")
                self.timer_reconexion.stop()
        except Exception:
            self.lbl_status.setText("❌ Servidor desconectado (reintentando...)")

    def hacer_login(self):
        email = self.combo_user.currentData()
        nombre = self.combo_user.currentText()
        
        # --- EL TRUCO PARA ENTRAR YA MISMO CON TU PIN 1989 ---
        if self.pin_acumulado == "1989":
            print(f"Entrando con pase libre: {nombre}")
            datos_usuario = {
                "id": 1, 
                "nombre": nombre, 
                "rol": "admin", 
                "email": email,
                "token": "token_provisorio_lucas"
            }
            try:
                with open(ARCHIVO_SESION, "w") as f:
                    json.dump(datos_usuario, f)
            except: pass
            
            self.on_login_callback(datos_usuario)
            return

        if not email or not self.pin_acumulado: return
        
        try:
            r = requests.post(f"{API_URL}/auth/login", json={"email": email, "password": self.pin_acumulado}, timeout=5)
            if r.status_code == 200:
                self.on_login_callback(r.json())
            else:
                QMessageBox.warning(self, "Error", "PIN incorrecto")
                self.limpiar()
        except Exception:
            QMessageBox.critical(self, "Error", "No se pudo conectar para validar")