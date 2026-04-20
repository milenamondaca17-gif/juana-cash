import requests
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QTableWidget, QTableWidgetItem, QPushButton,
                              QFrame, QHeaderView, QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

API_URL = "http://127.0.0.1:8000"

class SesionesScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("background-color: #1a1a2e; color: white;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        titulo = QLabel("📋 Log de Sesiones")
        titulo.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        titulo.setStyleSheet("color: #e94560;")
        layout.addWidget(titulo)
        filtros = QHBoxLayout()
        self.combo_dias = QComboBox()
        self.combo_dias.addItems(["Hoy", "Últimos 3 días", "Última semana", "Último mes"])
        self.combo_dias.setFixedHeight(36)
        self.combo_dias.setStyleSheet("QComboBox { background: #0f3460; border: 1px solid #e94560; border-radius: 8px; padding: 6px; color: white; font-size: 13px; } QComboBox QAbstractItemView { background: #0f3460; color: white; selection-background-color: #e94560; }")
        filtros.addWidget(self.combo_dias)
        btn_actualizar = QPushButton("🔄 Actualizar")
        btn_actualizar.setFixedHeight(36)
        btn_actualizar.setStyleSheet("QPushButton { background: #e94560; color: white; border-radius: 8px; padding: 0 16px; font-size: 13px; font-weight: bold; }")
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
        self.tabla.setStyleSheet("QTableWidget { background: #16213e; border: 1px solid #0f3460; border-radius: 8px; gridline-color: #0f3460; } QHeaderView::section { background: #0f3460; color: #a0a0b0; padding: 8px; border: none; } QTableWidgetItem { color: white; padding: 6px; }")
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.tabla)
        self.lbl_total = QLabel("")
        self.lbl_total.setStyleSheet("color: #a0a0b0; font-size: 12px;")
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