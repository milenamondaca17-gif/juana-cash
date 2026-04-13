import requests
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QTableWidget, QTableWidgetItem, QPushButton,
                              QFrame, QHeaderView, QDialog, QLineEdit,
                              QComboBox, QCheckBox, QMessageBox, QFormLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

API_URL = "http://127.0.0.1:8000"
ROLES = ["admin", "encargado", "cajero"]

class UsuarioDialog(QDialog):
    def __init__(self, parent=None, usuario=None):
        super().__init__(parent)
        self.usuario = usuario
        self.setWindowTitle("✏️ Editar usuario" if usuario else "➕ Nuevo usuario")
        self.setMinimumWidth(400)
        self.setStyleSheet("background-color: #1a1a2e; color: white;")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        titulo = QLabel("✏️ Editar usuario" if self.usuario else "➕ Nuevo usuario")
        titulo.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        titulo.setStyleSheet("color: #e94560;")
        layout.addWidget(titulo)
        form = QFormLayout()
        form.setSpacing(10)
        estilo_input = "QLineEdit { background: #0f3460; border: 1px solid #e94560; border-radius: 8px; padding: 8px; color: white; font-size: 13px; }"
        self.input_nombre = QLineEdit()
        self.input_nombre.setStyleSheet(estilo_input)
        self.input_nombre.setFixedHeight(38)
        form.addRow(QLabel("Nombre:"), self.input_nombre)
        self.input_email = QLineEdit()
        self.input_email.setStyleSheet(estilo_input)
        self.input_email.setFixedHeight(38)
        form.addRow(QLabel("Email:"), self.input_email)
        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password.setPlaceholderText("Dejar vacío para no cambiar" if self.usuario else "Contraseña")
        self.input_password.setStyleSheet(estilo_input)
        self.input_password.setFixedHeight(38)
        form.addRow(QLabel("Contraseña:"), self.input_password)
        self.input_pin = QLineEdit()
        self.input_pin.setPlaceholderText("PIN de 4 dígitos (opcional)")
        self.input_pin.setStyleSheet(estilo_input)
        self.input_pin.setFixedHeight(38)
        form.addRow(QLabel("PIN:"), self.input_pin)
        self.combo_rol = QComboBox()
        self.combo_rol.addItems(ROLES)
        self.combo_rol.setFixedHeight(38)
        self.combo_rol.setStyleSheet("QComboBox { background: #0f3460; border: 1px solid #e94560; border-radius: 8px; padding: 8px; color: white; font-size: 13px; } QComboBox QAbstractItemView { background: #0f3460; color: white; selection-background-color: #e94560; }")
        form.addRow(QLabel("Rol:"), self.combo_rol)
        self.check_activo = QCheckBox("Usuario activo")
        self.check_activo.setChecked(True)
        self.check_activo.setStyleSheet("color: #a0a0b0;")
        form.addRow("", self.check_activo)
        for lbl in self.findChildren(QLabel):
            lbl.setStyleSheet("color: #a0a0b0; font-size: 13px;")
        layout.addLayout(form)
        if self.usuario:
            self.input_nombre.setText(self.usuario.get("nombre", ""))
            self.input_email.setText(self.usuario.get("email", ""))
            self.input_pin.setText(self.usuario.get("pin", ""))
            rol = self.usuario.get("rol", "cajero")
            if rol in ROLES:
                self.combo_rol.setCurrentText(rol)
            self.check_activo.setChecked(self.usuario.get("activo", True))
        btns = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setFixedHeight(40)
        btn_cancelar.setStyleSheet("QPushButton { background: transparent; color: #a0a0b0; border: 1px solid #a0a0b0; border-radius: 8px; }")
        btn_cancelar.clicked.connect(self.reject)
        btns.addWidget(btn_cancelar)
        btn_guardar = QPushButton("💾 Guardar")
        btn_guardar.setFixedHeight(40)
        btn_guardar.setStyleSheet("QPushButton { background: #e94560; color: white; border-radius: 8px; font-size: 14px; font-weight: bold; }")
        btn_guardar.clicked.connect(self.guardar)
        btns.addWidget(btn_guardar)
        layout.addLayout(btns)

    def guardar(self):
        if not self.input_nombre.text().strip():
            QMessageBox.warning(self, "Error", "El nombre es obligatorio")
            return
        if not self.usuario and not self.input_password.text().strip():
            QMessageBox.warning(self, "Error", "La contraseña es obligatoria para nuevos usuarios")
            return
        self.accept()


class UsuariosScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("background-color: #1a1a2e; color: white;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        header = QHBoxLayout()
        titulo = QLabel("👥 Gestión de Usuarios")
        titulo.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        titulo.setStyleSheet("color: #e94560;")
        header.addWidget(titulo)
        header.addStretch()
        btn_nuevo = QPushButton("➕ Nuevo usuario")
        btn_nuevo.setFixedHeight(36)
        btn_nuevo.setStyleSheet("QPushButton { background: #e94560; color: white; border-radius: 8px; padding: 0 16px; font-size: 13px; font-weight: bold; }")
        btn_nuevo.clicked.connect(self.nuevo_usuario)
        header.addWidget(btn_nuevo)
        layout.addLayout(header)
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels(["ID", "Nombre", "Email", "Rol", "Estado", "Acciones"])
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tabla.setColumnWidth(0, 50)
        self.tabla.setColumnWidth(1, 150)
        self.tabla.setColumnWidth(3, 100)
        self.tabla.setColumnWidth(4, 80)
        self.tabla.setColumnWidth(5, 120)
        self.tabla.setStyleSheet("QTableWidget { background: #16213e; border: 1px solid #0f3460; border-radius: 8px; gridline-color: #0f3460; } QHeaderView::section { background: #0f3460; color: #a0a0b0; padding: 8px; border: none; } QTableWidgetItem { color: white; padding: 6px; }")
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.tabla)
        self.cargar_usuarios()

    def cargar_usuarios(self):
        try:
            r = requests.get(f"{API_URL}/auth/usuarios", timeout=5)
            if r.status_code == 200:
                usuarios = r.json()
                self.tabla.setRowCount(len(usuarios))
                colores_rol = {"admin": "#e94560", "encargado": "#f39c12", "cajero": "#27ae60"}
                for i, u in enumerate(usuarios):
                    self.tabla.setItem(i, 0, QTableWidgetItem(str(u["id"])))
                    self.tabla.setItem(i, 1, QTableWidgetItem(u["nombre"]))
                    self.tabla.setItem(i, 2, QTableWidgetItem(u["email"]))
                    item_rol = QTableWidgetItem(u["rol"])
                    item_rol.setForeground(Qt.GlobalColor.white)
                    self.tabla.setItem(i, 3, item_rol)
                    estado = "✅ Activo" if u["activo"] else "❌ Inactivo"
                    self.tabla.setItem(i, 4, QTableWidgetItem(estado))
                    btn_widget = QWidget()
                    btn_layout = QHBoxLayout(btn_widget)
                    btn_layout.setContentsMargins(4, 2, 4, 2)
                    btn_layout.setSpacing(4)
                    btn_editar = QPushButton("✏️")
                    btn_editar.setFixedSize(32, 28)
                    btn_editar.setStyleSheet("QPushButton { background: #0f3460; color: white; border-radius: 6px; }")
                    btn_editar.clicked.connect(lambda _, usr=u: self.editar_usuario(usr))
                    btn_layout.addWidget(btn_editar)
                    btn_desactivar = QPushButton("🚫")
                    btn_desactivar.setFixedSize(32, 28)
                    btn_desactivar.setStyleSheet("QPushButton { background: #e94560; color: white; border-radius: 6px; }")
                    btn_desactivar.clicked.connect(lambda _, uid=u["id"]: self.desactivar_usuario(uid))
                    btn_layout.addWidget(btn_desactivar)
                    self.tabla.setCellWidget(i, 5, btn_widget)
        except Exception as e:
            print(f"Error: {e}")

    def nuevo_usuario(self):
        dialog = UsuarioDialog(self)
        if dialog.exec():
            try:
                r = requests.post(f"{API_URL}/auth/registro", json={
                    "nombre": dialog.input_nombre.text().strip(),
                    "email": dialog.input_email.text().strip(),
                    "password": dialog.input_password.text().strip(),
                    "rol": dialog.combo_rol.currentText(),
                    "pin": dialog.input_pin.text().strip() or None
                }, timeout=5)
                if r.status_code == 200:
                    QMessageBox.information(self, "✅", "Usuario creado correctamente")
                    self.cargar_usuarios()
                else:
                    QMessageBox.critical(self, "Error", r.json().get("detail", "Error al crear"))
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def editar_usuario(self, usuario):
        dialog = UsuarioDialog(self, usuario)
        if dialog.exec():
            datos = {
                "nombre": dialog.input_nombre.text().strip(),
                "email": dialog.input_email.text().strip(),
                "rol": dialog.combo_rol.currentText(),
                "activo": dialog.check_activo.isChecked(),
                "pin": dialog.input_pin.text().strip() or None
            }
            if dialog.input_password.text().strip():
                datos["password"] = dialog.input_password.text().strip()
            try:
                r = requests.put(f"{API_URL}/auth/usuarios/{usuario['id']}", json=datos, timeout=5)
                if r.status_code == 200:
                    QMessageBox.information(self, "✅", "Usuario actualizado")
                    self.cargar_usuarios()
                else:
                    QMessageBox.critical(self, "Error", "No se pudo actualizar")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def desactivar_usuario(self, uid):
        resp = QMessageBox.question(self, "Confirmar", "¿Desactivar este usuario?")
        if resp == QMessageBox.StandardButton.Yes:
            try:
                r = requests.delete(f"{API_URL}/auth/usuarios/{uid}", timeout=5)
                if r.status_code == 200:
                    self.cargar_usuarios()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))