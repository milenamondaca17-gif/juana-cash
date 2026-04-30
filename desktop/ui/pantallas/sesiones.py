import requests
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QTableWidget, QTableWidgetItem, QPushButton,
                              QFrame, QHeaderView, QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

API_URL = "http://127.0.0.1:8000"

from ui.theme import get_tema as _gt
_T = _gt()
_BG   = _T["bg_app"];  _CARD = _T["bg_card"]; _INP = _T["bg_input"]
_TXT  = _T["text_main"]; _MUT = _T["text_muted"]; _PRI = _T["primary"]
_DGR  = _T["danger"];  _BOR = _T["border"]

class SesionesScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet(f"background-color: {_BG}; color: {_TXT};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)
        titulo = QLabel("📋 Log de Sesiones")
        titulo.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        titulo.setStyleSheet(f"color: {_TXT}; background: transparent;")
        layout.addWidget(titulo)
        filtros = QHBoxLayout()
        self.combo_dias = QComboBox()
        self.combo_dias.addItems(["Hoy", "Últimos 3 días", "Última semana", "Último mes"])
        self.combo_dias.setFixedHeight(38)
        filtros.addWidget(self.combo_dias)
        btn_actualizar = QPushButton("🔄 Actualizar")
        btn_actualizar.setFixedHeight(38)
        btn_actualizar.setStyleSheet(f"QPushButton {{ background: {_PRI}; color: white; border-radius: 8px; padding: 0 16px; font-size: 13px; font-weight: bold; }} QPushButton:hover {{ background: {_T['primary_hover']}; }}")
        btn_actualizar.clicked.connect(self.cargar_sesiones)
        filtros.addWidget(btn_actualizar)
        filtros.addStretch()
        layout.addLayout(filtros)
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["Fecha/Hora", "Cajero", "Turno", "Acción", "Detalle"])
        self.tabla.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.tabla.setColumnWidth(0, 150)
        self.tabla.setColumnWidth(1, 150)
        self.tabla.setColumnWidth(2, 180)
        self.tabla.setColumnWidth(3, 130)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.tabla)
        self.lbl_total = QLabel("")
        self.lbl_total.setStyleSheet(f"color: {_MUT}; font-size: 12px; background: transparent;")
        layout.addWidget(self.lbl_total)

    def cargar_sesiones(self):
        dias_map = {"Hoy": 1, "Últimos 3 días": 3, "Última semana": 7, "Último mes": 30}
        dias = dias_map.get(self.combo_dias.currentText(), 1)
        try:
            if dias == 1:
                r = requests.get(f"{API_URL}/sesiones/hoy", timeout=5)
            else:
                r = requests.get(f"{API_URL}/sesiones/historial", params={"dias": dias}, timeout=5)
            if r.status_code == 200:
                sesiones = r.json()
                self.tabla.setRowCount(len(sesiones))
                for i, s in enumerate(sesiones):
                    fecha = s.get("fecha") or s.get("hora", "")
                    accion = s.get("accion", "")
                    self.tabla.setItem(i, 0, QTableWidgetItem(fecha))
                    self.tabla.setItem(i, 1, QTableWidgetItem(s.get("cajero", "")))
                    self.tabla.setItem(i, 2, QTableWidgetItem(s.get("turno", "") or ""))
                    self.tabla.setItem(i, 3, QTableWidgetItem(accion))
                    self.tabla.setItem(i, 4, QTableWidgetItem(s.get("detalle", "") or ""))
                self.lbl_total.setText(f"Total: {len(sesiones)} registros")
        except Exception as e:
            self.lbl_total.setText(f"Error: {str(e)}")