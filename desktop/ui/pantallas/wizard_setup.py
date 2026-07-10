import requests
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QMessageBox, QStackedWidget, QWidget
)
from PyQt6.QtCore import Qt

API_URL = "http://127.0.0.1:8000"


class WizardSetup(QDialog):
    """Wizard de configuración inicial. Solo aparece cuando no hay usuarios en la DB."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración inicial — Juana Cash")
        self.setFixedSize(580, 540)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint)
        self.setStyleSheet("background: #0f172a; color: #e2e8f0;")
        self._paso = 0
        self._datos = {}
        self._setup_ui()

    # ── helpers de estilo ─────────────────────────────────────────────────────
    def _inp(self, placeholder="", password=False):
        e = QLineEdit()
        e.setPlaceholderText(placeholder)
        e.setFixedHeight(44)
        if password:
            e.setEchoMode(QLineEdit.EchoMode.Password)
        e.setStyleSheet(
            "QLineEdit { background: #1e293b; border: 1.5px solid #334155;"
            " border-radius: 8px; padding: 10px 14px; color: #e2e8f0; font-size: 14px; }"
            "QLineEdit:focus { border-color: #3b82f6; }"
        )
        return e

    def _lbl(self, texto, size=13, bold=False, color="#94a3b8"):
        l = QLabel(texto)
        l.setStyleSheet(
            f"color: {color}; font-size: {size}px;"
            f" font-weight: {'bold' if bold else 'normal'}; background: transparent;"
        )
        l.setWordWrap(True)
        return l

    # ── estructura base ───────────────────────────────────────────────────────
    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        hdr = QFrame()
        hdr.setFixedHeight(76)
        hdr.setStyleSheet("background: #1e293b; border-bottom: 2px solid #334155;")
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(36, 0, 36, 0)
        lbl_logo = QLabel(
            "<span style='color:#3b82f6;font-weight:900;font-size:22px;'>JUANA</span>"
            "<span style='color:#64748b;font-weight:300;font-size:22px;'> CASH</span>"
            "<span style='color:#10b981;font-weight:900;font-size:20px;'>$</span>"
            "<span style='color:#64748b;font-size:13px;'>  —  Configuración inicial</span>"
        )
        lbl_logo.setStyleSheet("background: transparent;")
        hdr_lay.addWidget(lbl_logo)
        hdr_lay.addStretch()
        self.lbl_paso_hdr = QLabel("Paso 1 de 3")
        self.lbl_paso_hdr.setStyleSheet(
            "color: #64748b; font-size: 12px; background: transparent;"
        )
        hdr_lay.addWidget(self.lbl_paso_hdr)
        root.addWidget(hdr)

        # Stack de pasos
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent;")
        self.stack.addWidget(self._paso1_widget())
        self.stack.addWidget(self._paso2_widget())
        self.stack.addWidget(self._paso3_widget())
        root.addWidget(self.stack, 1)

        # Footer con botones
        footer = QFrame()
        footer.setFixedHeight(72)
        footer.setStyleSheet("background: #1e293b; border-top: 1.5px solid #334155;")
        ft_lay = QHBoxLayout(footer)
        ft_lay.setContentsMargins(36, 0, 36, 0)
        ft_lay.setSpacing(12)

        self.btn_ant = QPushButton("← Anterior")
        self.btn_ant.setFixedSize(120, 42)
        self.btn_ant.setStyleSheet(
            "QPushButton { background: transparent; color: #64748b;"
            " border: 1.5px solid #334155; border-radius: 8px; font-size: 13px; }"
            "QPushButton:hover { color: #e2e8f0; border-color: #64748b; }"
        )
        self.btn_ant.hide()
        self.btn_ant.clicked.connect(self._anterior)
        ft_lay.addWidget(self.btn_ant)
        ft_lay.addStretch()

        self.btn_sig = QPushButton("Siguiente →")
        self.btn_sig.setFixedSize(150, 42)
        self.btn_sig.setStyleSheet(
            "QPushButton { background: #3b82f6; color: white; border: none;"
            " border-radius: 8px; font-size: 13px; font-weight: bold; }"
            "QPushButton:hover { background: #2563eb; }"
        )
        self.btn_sig.clicked.connect(self._siguiente)
        ft_lay.addWidget(self.btn_sig)
        root.addWidget(footer)

    def _seccion(self, titulo, subtitulo):
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(40, 28, 40, 16)
        lay.setSpacing(6)
        lay.addWidget(self._lbl(titulo, 19, True, "#f1f5f9"))
        lay.addWidget(self._lbl(subtitulo, 12, False, "#64748b"))
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #334155; border: none; margin: 10px 0 8px 0;")
        lay.addWidget(sep)
        return w, lay

    # ── paso 1: datos del negocio ─────────────────────────────────────────────
    def _paso1_widget(self):
        w, lay = self._seccion(
            "🏪  Datos del negocio",
            "Esta información aparecerá en los tickets y reportes enviados por WhatsApp."
        )
        lay.addWidget(self._lbl("Nombre de fantasía  *"))
        self.p1_nombre = self._inp("Ej: Almacén Don Pepe")
        lay.addWidget(self.p1_nombre)
        lay.addSpacing(10)
        lay.addWidget(self._lbl("Dirección"))
        self.p1_dir = self._inp("Ej: Av. San Martín 456, San Rafael")
        lay.addWidget(self.p1_dir)
        lay.addSpacing(10)
        lay.addWidget(self._lbl("Teléfono / WhatsApp de atención al cliente"))
        self.p1_tel = self._inp("Ej: 2604123456")
        lay.addWidget(self.p1_tel)
        lay.addStretch()
        return w

    # ── paso 2: números de reportes ───────────────────────────────────────────
    def _paso2_widget(self):
        w, lay = self._seccion(
            "📱  WhatsApp para reportes",
            "Estos números van a recibir los reportes de cierre de turno,\n"
            "retiros y el resumen automático de las 22:20."
        )
        lay.addWidget(self._lbl(
            "Número principal  *  (sin 0, sin 15 — solo dígitos, ej: 2634123456)"
        ))
        self.p2_num1 = self._inp("Ej: 2634123456")
        lay.addWidget(self.p2_num1)
        lay.addSpacing(10)
        lay.addWidget(self._lbl("Número 2  (opcional)"))
        self.p2_num2 = self._inp("Ej: 2634654321")
        lay.addWidget(self.p2_num2)
        lay.addSpacing(10)
        lay.addWidget(self._lbl("Número 3  (opcional)"))
        self.p2_num3 = self._inp("Ej: 2634111222")
        lay.addWidget(self.p2_num3)
        lay.addStretch()
        return w

    # ── paso 3: crear administrador ───────────────────────────────────────────
    def _paso3_widget(self):
        w, lay = self._seccion(
            "👤  Crear administrador",
            "Este usuario tendrá acceso completo al sistema."
        )
        lay.addWidget(self._lbl("Nombre completo  *"))
        self.p3_nombre = self._inp("Ej: Juan García")
        lay.addWidget(self.p3_nombre)
        lay.addSpacing(10)
        lay.addWidget(self._lbl("Email  *  (se usa para iniciar sesión)"))
        self.p3_email = self._inp("Ej: admin@mialmacan.com")
        lay.addWidget(self.p3_email)
        lay.addSpacing(10)
        lay.addWidget(self._lbl("Contraseña  *"))
        self.p3_pass = self._inp("Mínimo 4 caracteres", password=True)
        lay.addWidget(self.p3_pass)
        lay.addSpacing(10)
        lay.addWidget(self._lbl("Confirmar contraseña  *"))
        self.p3_pass2 = self._inp("Repetí la contraseña", password=True)
        lay.addWidget(self.p3_pass2)
        lay.addStretch()
        return w

    # ── navegación ────────────────────────────────────────────────────────────
    def _anterior(self):
        self._paso -= 1
        self.stack.setCurrentIndex(self._paso)
        self.lbl_paso_hdr.setText(f"Paso {self._paso + 1} de 3")
        self.btn_ant.setVisible(self._paso > 0)
        self.btn_sig.setText("Siguiente →")

    def _siguiente(self):
        if self._paso == 0:
            nombre = self.p1_nombre.text().strip()
            if not nombre:
                QMessageBox.warning(self, "Campo requerido",
                                    "El nombre del negocio es obligatorio.")
                self.p1_nombre.setFocus()
                return
            self._datos["nombre"]    = nombre
            self._datos["direccion"] = self.p1_dir.text().strip()
            self._datos["telefono"]  = self.p1_tel.text().strip()
            self._avanzar(1, "Siguiente →")

        elif self._paso == 1:
            num1 = self.p2_num1.text().strip()
            if not num1:
                QMessageBox.warning(self, "Campo requerido",
                                    "El número principal es obligatorio.")
                self.p2_num1.setFocus()
                return
            self._datos["numeros"] = [
                n for n in [
                    num1,
                    self.p2_num2.text().strip(),
                    self.p2_num3.text().strip()
                ] if n
            ]
            self._avanzar(2, "✅  Finalizar")

        elif self._paso == 2:
            nombre = self.p3_nombre.text().strip()
            email  = self.p3_email.text().strip()
            pwd    = self.p3_pass.text()
            pwd2   = self.p3_pass2.text()
            if not nombre or not email or not pwd:
                QMessageBox.warning(self, "Campos requeridos",
                                    "Completá todos los campos obligatorios.")
                return
            if pwd != pwd2:
                QMessageBox.warning(self, "Contraseñas distintas",
                                    "Las contraseñas no coinciden.")
                self.p3_pass2.setFocus()
                return
            if len(pwd) < 4:
                QMessageBox.warning(self, "Contraseña muy corta",
                                    "La contraseña debe tener al menos 4 caracteres.")
                return
            self._datos["admin_nombre"] = nombre
            self._datos["admin_email"]  = email
            self._datos["admin_pass"]   = pwd
            self._finalizar()

    def _avanzar(self, paso, texto_btn):
        self._paso = paso
        self.stack.setCurrentIndex(paso)
        self.lbl_paso_hdr.setText(f"Paso {paso + 1} de 3")
        self.btn_ant.show()
        self.btn_sig.setText(texto_btn)

    # ── guardado final ────────────────────────────────────────────────────────
    def _finalizar(self):
        # 1. Guardar datos del negocio en la API y en ticket_config.json
        try:
            requests.put(f"{API_URL}/config/", json={
                "negocio_nombre":    self._datos["nombre"],
                "negocio_direccion": self._datos.get("direccion", ""),
                "negocio_telefono":  self._datos.get("telefono", ""),
            }, timeout=5)
        except Exception:
            pass

        try:
            from ui.pantallas.impresora import guardar_config_ticket
            guardar_config_ticket({
                "nombre_negocio": self._datos["nombre"],
                "telefono":       self._datos.get("telefono", ""),
            })
        except Exception:
            pass

        # 2. Guardar números de reporte en app_config.json
        try:
            from ui.pantallas.negocio_config import guardar_numeros_reporte
            guardar_numeros_reporte(self._datos["numeros"])
        except Exception:
            pass

        # 3. Crear usuario administrador
        try:
            r = requests.post(f"{API_URL}/auth/registro", json={
                "nombre":   self._datos["admin_nombre"],
                "email":    self._datos["admin_email"],
                "password": self._datos["admin_pass"],
                "rol":      "admin",
                "pin":      "1234",
            }, timeout=5)
            if r.status_code not in (200, 201):
                detail = r.json().get("detail", "Error desconocido")
                QMessageBox.critical(self, "Error al crear usuario",
                                     f"No se pudo crear el administrador:\n{detail}")
                return
        except Exception as e:
            QMessageBox.critical(self, "Error de conexión",
                                 f"No se pudo conectar al servidor:\n{e}")
            return

        QMessageBox.information(
            self, "✅  Configuración completa",
            f"¡Todo listo!\n\n"
            f"Negocio: {self._datos['nombre']}\n"
            f"Admin: {self._datos['admin_nombre']}\n"
            f"Email: {self._datos['admin_email']}\n\n"
            "Ya podés iniciar sesión con tu email y contraseña.\n"
            "El PIN de acceso rápido inicial es: 1234\n"
            "(podés cambiarlo desde Configuración → Usuarios)"
        )
        self.accept()
