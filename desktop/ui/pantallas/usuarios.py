import requests
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QTableWidget, QTableWidgetItem, QPushButton,
                               QFrame, QHeaderView, QDialog, QLineEdit,
                               QComboBox, QCheckBox, QMessageBox, QFormLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

API_URL = "http://127.0.0.1:8000"

from ui.theme import get_tema as _gt
_T = _gt()
_BG = _T["bg_app"]; _CARD = _T["bg_card"]; _INP = _T["bg_input"]
_TXT = _T["text_main"]; _MUT = _T["text_muted"]; _PRI = _T["primary"]
_DGR = _T["danger"]; _BOR = _T["border"]; _OK = _T["success"]

class UsuarioDialog(QDialog):
    def __init__(self, parent=None, usuario=None):
        super().__init__(parent)
        self.usuario = usuario
        self.setWindowTitle("👤 Gestionar Cajero")
        self.setMinimumWidth(380)
        self.setStyleSheet(f"background-color: {_CARD}; color: {_TXT};")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)
        form = QFormLayout()
        form.setSpacing(10)

        for lbl in [QLabel("Nombre:"), QLabel("PIN:")]:
            lbl.setStyleSheet(f"color: {_MUT}; font-weight: bold; background: transparent;")

        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Nombre o DNI (ej: Fernanda)")
        self.input_nombre.setFixedHeight(42)
        form.addRow(QLabel("Nombre:"), self.input_nombre)

        self.input_pin = QLineEdit()
        self.input_pin.setPlaceholderText("PIN de 4 números")
        self.input_pin.setMaxLength(4)
        self.input_pin.setFixedHeight(42)
        form.addRow(QLabel("PIN:"), self.input_pin)

        layout.addLayout(form)

        btn_guardar = QPushButton("💾 Guardar cajero")
        btn_guardar.setFixedHeight(46)
        btn_guardar.setStyleSheet(f"QPushButton {{ background: {_OK}; color: white; font-weight: bold; border-radius: 10px; font-size: 15px; }} QPushButton:hover {{ background: #059669; }}")
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
        self.setStyleSheet(f"background-color: {_BG}; color: {_TXT};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        header = QHBoxLayout()
        titulo = QLabel("👥 Personal Juana Cash")
        titulo.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        titulo.setStyleSheet(f"color: {_TXT}; background: transparent;")
        header.addWidget(titulo)
        header.addStretch()
        btn_nuevo = QPushButton("➕ Agregar cajero")
        btn_nuevo.setFixedHeight(40)
        btn_nuevo.setStyleSheet(f"QPushButton {{ background: {_PRI}; color: white; padding: 0 16px; font-weight: bold; border-radius: 8px; font-size: 13px; }} QPushButton:hover {{ background: {_T['primary_hover']}; }}")
        btn_nuevo.clicked.connect(self.nuevo_usuario)
        header.addWidget(btn_nuevo)
        layout.addLayout(header)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels(["Nombre / DNI", "Rol", "Acciones"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
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