import requests
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QScrollArea, QFrame, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

API_URL = "http://localhost:8000"

class AlertasPrecioScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.cargar_alertas)
        self.timer.start(30000)  # Refresca cada 30 segundos

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        titulo = QLabel("🔔 ALERTAS DE CAMBIO DE PRECIOS")
        titulo.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        titulo.setStyleSheet("color: white;")
        header.addWidget(titulo)
        header.addStretch()

        self.lbl_pendientes = QLabel("")
        self.lbl_pendientes.setStyleSheet(
            "background: #e74c3c; color: white; border-radius: 12px; "
            "padding: 4px 12px; font-weight: bold; font-size: 13px;"
        )
        header.addWidget(self.lbl_pendientes)

        btn_todas = QPushButton("✅ Marcar todas como vistas")
        btn_todas.setFixedHeight(36)
        btn_todas.setStyleSheet(
            "QPushButton { background: #27ae60; color: white; border-radius: 8px; "
            "font-weight: bold; padding: 0 14px; }"
            "QPushButton:hover { background: #2ecc71; }"
        )
        btn_todas.clicked.connect(self.marcar_todas_vistas)
        header.addWidget(btn_todas)

        btn_ref = QPushButton("🔄")
        btn_ref.setFixedSize(36, 36)
        btn_ref.setStyleSheet(
            "QPushButton { background: #16213e; color: white; border-radius: 8px; font-size: 16px; }"
        )
        btn_ref.clicked.connect(self.cargar_alertas)
        header.addWidget(btn_ref)

        layout.addLayout(header)

        # Subtítulo
        sub = QLabel("Cada vez que se modifica un precio desde cualquier dispositivo, queda registrado aquí.")
        sub.setStyleSheet("color: #606880; font-size: 12px;")
        layout.addWidget(sub)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #0f3460; border: none;")
        layout.addWidget(sep)

        # Scroll de alertas
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.contenedor = QWidget()
        self.contenedor.setStyleSheet("background: transparent;")
        self.lista_layout = QVBoxLayout(self.contenedor)
        self.lista_layout.setSpacing(8)
        self.lista_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.contenedor)
        layout.addWidget(self.scroll)

        self.setStyleSheet("background-color: #1a1a2e; color: white;")

    def showEvent(self, event):
        super().showEvent(event)
        self.cargar_alertas()

    def cargar_alertas(self):
        try:
            r = requests.get(f"{API_URL}/alertas-precio/", timeout=5)
            alertas = r.json() if r.status_code == 200 else []
        except Exception:
            alertas = []

        # Limpiar lista
        while self.lista_layout.count():
            item = self.lista_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        pendientes = sum(1 for a in alertas if not a.get("visto"))
        if pendientes > 0:
            self.lbl_pendientes.setText(f"  {pendientes} pendiente{'s' if pendientes > 1 else ''}  ")
            self.lbl_pendientes.show()
        else:
            self.lbl_pendientes.hide()

        if not alertas:
            lbl = QLabel("✅ Sin alertas de precios por el momento")
            lbl.setStyleSheet("color: #606880; font-size: 14px; padding: 40px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.lista_layout.addWidget(lbl)
            return

        for a in alertas:
            self._agregar_fila(a)

    def _agregar_fila(self, a):
        fondo = "#16213e" if a.get("visto") else "#1a1a3e"
        borde = "#334155" if a.get("visto") else "#e74c3c"

        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: {fondo}; border-radius: 10px; "
            f"border-left: 4px solid {borde}; }}"
        )
        card.setFixedHeight(64)
        row = QHBoxLayout(card)
        row.setContentsMargins(16, 8, 12, 8)
        row.setSpacing(12)

        # Ícono estado
        icono = QLabel("✅" if a.get("visto") else "🔔")
        icono.setFixedWidth(24)
        icono.setStyleSheet("font-size: 18px; background: transparent; border: none;")
        row.addWidget(icono)

        # Nombre producto
        col_nombre = QVBoxLayout()
        col_nombre.setSpacing(2)
        lbl_nombre = QLabel(a.get("nombre_producto", "Desconocido"))
        lbl_nombre.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        lbl_nombre.setStyleSheet(
            f"color: {'#a0a0b0' if a.get('visto') else 'white'}; "
            "background: transparent; border: none;"
        )
        lbl_fecha = QLabel(str(a.get("creado_en", ""))[:16].replace("T", " ") +
                           f"  —  por {a.get('usuario','?')}")
        lbl_fecha.setStyleSheet("color: #606880; font-size: 11px; background: transparent; border: none;")
        col_nombre.addWidget(lbl_nombre)
        col_nombre.addWidget(lbl_fecha)
        row.addLayout(col_nombre)
        row.addStretch()

        # Precios
        ant = float(a.get("precio_anterior", 0))
        nvo = float(a.get("precio_nuevo", 0))
        diff = nvo - ant
        color_diff = "#27ae60" if diff > 0 else "#e74c3c"
        signo = "+" if diff >= 0 else ""

        col_precios = QVBoxLayout()
        col_precios.setSpacing(2)
        col_precios.setAlignment(Qt.AlignmentFlag.AlignRight)
        lbl_nvo = QLabel(f"${nvo:,.2f}")
        lbl_nvo.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        lbl_nvo.setStyleSheet(f"color: {color_diff}; background: transparent; border: none;")
        lbl_nvo.setAlignment(Qt.AlignmentFlag.AlignRight)
        lbl_ant = QLabel(f"antes: ${ant:,.2f}  ({signo}{diff:,.2f})")
        lbl_ant.setStyleSheet("color: #606880; font-size: 11px; background: transparent; border: none;")
        lbl_ant.setAlignment(Qt.AlignmentFlag.AlignRight)
        col_precios.addWidget(lbl_nvo)
        col_precios.addWidget(lbl_ant)
        row.addLayout(col_precios)

        # Botón marcar visto (solo si no está visto)
        if not a.get("visto"):
            btn_v = QPushButton("✓")
            btn_v.setFixedSize(32, 32)
            btn_v.setStyleSheet(
                "QPushButton { background: #0f3460; color: #27ae60; border-radius: 6px; "
                "font-size: 16px; font-weight: bold; border: none; }"
                "QPushButton:hover { background: #27ae60; color: white; }"
            )
            btn_v.setToolTip("Marcar como visto")
            btn_v.clicked.connect(lambda _, aid=a["id"]: self.marcar_visto(aid))
            row.addWidget(btn_v)

        self.lista_layout.addWidget(card)

    def marcar_visto(self, alerta_id):
        try:
            requests.post(f"{API_URL}/alertas-precio/{alerta_id}/visto", timeout=5)
            self.cargar_alertas()
        except Exception:
            pass

    def marcar_todas_vistas(self):
        try:
            requests.post(f"{API_URL}/alertas-precio/marcar-todas-vistas", timeout=5)
            self.cargar_alertas()
        except Exception:
            QMessageBox.critical(self, "Error", "No se pudo conectar al servidor")
