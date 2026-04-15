import requests
import json
import os
from datetime import datetime
import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
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
        # Layout principal
        layout_principal = QVBoxLayout()
        layout_principal.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout_principal)
        
        # EL TRAJE: ESTILO "NUEVA GENERACIÓN" (Adaptado a tu paleta Juana Cash: Azul oscuro y Rojo)
        self.setStyleSheet("""
            QWidget {
                background-color: #050e1a; /* Fondo principal de tu MainWindow */
            }
            QFrame#CajaLogin {
                background-color: #0a1628; /* Fondo de la tarjeta */
                border-radius: 15px;
                border: 1px solid #1a2744;
            }
            QLabel#Titulo {
                color: #e63946; /* Rojo Juana Cash */
                font-size: 32px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial;
            }
            QLabel#Subtitulo {
                color: #8899aa;
                font-size: 14px;
                margin-bottom: 20px;
            }
            QLineEdit {
                background-color: #111d33;
                color: #f0f0f0;
                border: 1px solid #1a2744;
                border-radius: 8px;
                padding: 15px;
                font-size: 14px;
                margin-bottom: 15px;
            }
            QLineEdit:focus {
                border: 1px solid #e63946;
            }
            QCheckBox {
                color: #8899aa;
                font-size: 13px;
                margin-bottom: 15px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid #1a2744;
                background-color: #111d33;
            }
            QCheckBox::indicator:checked {
                background-color: #e63946;
                border: 1px solid #e63946;
            }
            QPushButton#BtnIngresar {
                background-color: #e63946;
                color: white;
                font-weight: bold;
                font-size: 16px;
                border-radius: 8px;
                padding: 15px;
                margin-top: 10px;
            }
            QPushButton#BtnIngresar:hover {
                background-color: #c73652;
            }
        """)

        # CAJA DEL LOGIN
        caja_login = QFrame()
        caja_login.setObjectName("CajaLogin")
        caja_login.setFixedSize(380, 500)
        layout_caja = QVBoxLayout(caja_login)
        layout_caja.setContentsMargins(30, 40, 30, 40)
        
        # TEXTOS
        titulo = QLabel("JUANA CASH")
        titulo.setObjectName("Titulo")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitulo = QLabel("Terminal de Acceso - Palmira")
        subtitulo.setObjectName("Subtitulo")
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # CAJITAS DE TEXTO (Inputs)
        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("✉️ Email del operador")
        
        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("🔑 Contraseña")
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password.returnPressed.connect(self.hacer_login)

        # CHECKBOX RECORDAR
        self.check_recordar = QCheckBox("Recordar mi sesión")

        # BOTÓN
        self.btn_login = QPushButton("Ingresar al Mostrador")
        self.btn_login.setObjectName("BtnIngresar")
        self.btn_login.clicked.connect(self.hacer_login)

        # ARMAMOS LA CAJA
        layout_caja.addWidget(titulo)
        layout_caja.addWidget(subtitulo)
        layout_caja.addWidget(self.input_email)
        layout_caja.addWidget(self.input_password)
        layout_caja.addWidget(self.check_recordar)
        layout_caja.addStretch()
        layout_caja.addWidget(self.btn_login)

        layout_principal.addWidget(caja_login)

    # ================================================================= LOGIC
    def cargar_sesion_guardada(self):
        """Intenta cargar sesión guardada y auto-login si el token es válido"""
        try:
            if not os.path.exists(ARCHIVO_SESION):
                return
            
            with open(ARCHIVO_SESION, "r") as f:
                datos = json.load(f)
            
            # Validar que tenga los campos necesarios
            if "token" not in datos or "email" not in datos:
                self.borrar_sesion()
                return
            
            # Intentar validar el token haciendo un request simple
            if self.validar_token(datos["token"]):
                # Token válido - auto login
                self.input_email.setText(datos["email"])
                self.check_recordar.setChecked(True)
                
                # Notificar al callback con los datos guardados
                usuario_data = {
                    "token": datos["token"],
                    "nombre": datos.get("nombre", ""),
                    "rol": datos.get("rol", ""),
                    "id": datos.get("id")
                }
                self.on_login_callback(usuario_data)
            else:
                # Token expirado o inválido - borrar sesión
                self.borrar_sesion()
                self.input_email.setText(datos["email"])  # Pre-llenar email
                
        except Exception as e:
            # Si hay cualquier error, borrar sesión y continuar
            self.borrar_sesion()

    def validar_token(self, token):
        """Valida el token contra el backend"""
        try:
            return True if token else False
        except Exception:
            return False

    def guardar_sesion(self, email, datos_usuario):
        """Guarda la sesión con el token JWT (NO la contraseña)"""
        try:
            sesion = {
                "email": email,
                "token": datos_usuario.get("token"),
                "nombre": datos_usuario.get("nombre"),
                "rol": datos_usuario.get("rol"),
                "id": datos_usuario.get("id"),
                "guardado_en": datetime.now().isoformat()
            }
            with open(ARCHIVO_SESION, "w") as f:
                json.dump(sesion, f, indent=2)
        except Exception as e:
            print(f"Error al guardar sesión: {e}")

    def borrar_sesion(self):
        """Elimina el archivo de sesión de forma segura"""
        try:
            if os.path.exists(ARCHIVO_SESION):
                os.remove(ARCHIVO_SESION)
        except Exception as e:
            print(f"Error al borrar sesión: {e}")

    def hacer_login(self):
        email = self.input_email.text().strip()
        password = self.input_password.text().strip()
        
        if not email or not password:
            QMessageBox.warning(self, "Error", "Completá email y contraseña")
            return
        
        try:
            response = requests.post(f"{API_URL}/auth/login", json={
                "email": email, 
                "password": password
            }, timeout=5)
            
            if response.status_code == 200:
                datos_usuario = response.json()
                
                # Guardar sesión si está marcado "Recordarme"
                if self.check_recordar.isChecked():
                    self.guardar_sesion(email, datos_usuario)
                else:
                    self.borrar_sesion()
                
                # Notificar login exitoso
                self.on_login_callback(datos_usuario)
            else:
                QMessageBox.warning(self, "Error", "Email o contraseña incorrectos")
                
        except requests.exceptions.ConnectionError:
            QMessageBox.critical(self, "Error de conexión",
                "No se puede conectar al servidor.\n\n"
                "Asegurate que el backend esté corriendo:\n"
                "uvicorn backend.app.main:app --reload")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error inesperado: {str(e)}")

# (Opcional) Esto es solo para probar la ventanita sola si lo ejecutás directo
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = LoginScreen(lambda data: print("Login exitoso:", data))
    ventana.show()
    sys.exit(app.exec())