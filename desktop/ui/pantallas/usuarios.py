import requests
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QTableWidget, QTableWidgetItem, QPushButton,
                               QFrame, QHeaderView, QDialog, QLineEdit,
                               QComboBox, QCheckBox, QMessageBox, QFormLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

API_URL = "http://127.0.0.1:8000"

class UsuarioDialog(QDialog):
    def __init__(self, parent=None, usuario=None):
        super().__init__(parent)
        self.usuario = usuario
        self.setWindowTitle("👤 Gestionar Cajero")
        self.setMinimumWidth(350)
        self.setStyleSheet("background-color: #050e1a; color: white;")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        estilo_input = "QLineEdit { background: #111d33; border: 1px solid #e63946; border-radius: 8px; padding: 10px; color: white; }"
        
        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Nombre o DNI (ej: Fernanda)")
        self.input_nombre.setStyleSheet(estilo_input)
        form.addRow(QLabel("Nombre:"), self.input_nombre)

        self.input_pin = QLineEdit()
        self.input_pin.setPlaceholderText("PIN de 4 números")
        self.input_pin.setMaxLength(4)
        self.input_pin.setStyleSheet(estilo_input)
        form.addRow(QLabel("PIN:"), self.input_pin)

        layout.addLayout(form)

        btn_guardar = QPushButton("💾 GUARDAR CAJERO")
        btn_guardar.setFixedHeight(45)
        btn_guardar.setStyleSheet("background: #34C38F; color: #050e1a; font-weight: bold; border-radius: 8px;")
        btn_guardar.clicked.connect(self.accept)
        layout.addWidget(btn_guardar)

        if self.usuario:
            self.input_nombre.setText(self.usuario.get("nombre", ""))
            self.input_pin.setText(self.usuario.get("pin", ""))

class UsuariosScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("background-color: #050e1a; color: white;")
        layout = QVBoxLayout(self)
        
        header = QHBoxLayout()
        titulo = QLabel("👥 Personal Juana Cash")
        titulo.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header.addWidget(titulo)
        
        btn_nuevo = QPushButton("➕ AGREGAR CAJERO")
        btn_nuevo.setStyleSheet("background: #e63946; padding: 10px; font-weight: bold; border-radius: 5px;")
        btn_nuevo.clicked.connect(self.nuevo_usuario)
        header.addWidget(btn_nuevo)
        layout.addLayout(header)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels(["Nombre / DNI", "Rol", "Acciones"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.setStyleSheet("QTableWidget { background: #0a1628; gridline-color: #1a2744; }")
        layout.addWidget(self.tabla)
        self.cargar_usuarios()

    def cargar_usuarios(self):
        try:
            r = requests.get(f"{API_URL}/auth/usuarios", timeout=5)
            if r.status_code == 200:
                usuarios = r.json()
                self.tabla.setRowCount(len(usuarios))
                for i, u in enumerate(usuarios):
                    self.tabla.setItem(i, 0, QTableWidgetItem(u["nombre"]))
                    self.tabla.setItem(i, 1, QTableWidgetItem(u["rol"].upper()))
                    
                    btn_del = QPushButton("❌ Borrar")
                    btn_del.setStyleSheet("background: #334155; padding: 5px;")
                    btn_del.clicked.connect(lambda _, uid=u["id"]: self.borrar_usuario(uid))
                    self.tabla.setCellWidget(i, 2, btn_del)
        except Exception:
            pass

    def nuevo_usuario(self):
        dialog = UsuarioDialog(self)
        if dialog.exec():
            nombre = dialog.input_nombre.text().strip()
            pin = dialog.input_pin.text().strip()
            # Creamos un email falso para que el servidor no de error
            email_falso = f"{nombre.lower()}@juana.cash"
            
            try:
                requests.post(f"{API_URL}/auth/registro", json={
                    "nombre": nombre,
                    "email": email_falso,
                    "password": pin,
                    "rol": "cajero",
                    "pin": pin
                })
                self.cargar_usuarios()
            except:
                QMessageBox.critical(self, "Error", "No se pudo conectar con el servidor")

    def borrar_usuario(self, uid):
        if QMessageBox.question(self, "Confirmar", "¿Eliminar este cajero?") == QMessageBox.StandardButton.Yes:
            requests.delete(f"{API_URL}/auth/usuarios/{uid}")
            self.cargar_usuarios()