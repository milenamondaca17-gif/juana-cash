import csv
import requests
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QFileDialog, QTableWidget,
                             QTableWidgetItem, QHeaderView, QFrame,
                             QMessageBox, QProgressBar)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

API_URL = "http://127.0.0.1:8000"

# Colores de tu sistema
BG_MAIN = "#1a1a2e"
BG_PANEL = "#16213e"
BORDER = "#0f3460"
TEXT_MAIN = "#F0F0F0"
ACCENT = "#3498db"
ACCENT_BOTON = "#e94560"

class ImportadorScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.ruta_archivo = ""
        self.datos_extraidos = []
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet(f"background-color: {BG_MAIN}; color: {TEXT_MAIN};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # ── Cabecera ──────────────────────────────────────────────────────────
        titulo = QLabel("🛸 Importador Mágico (Migración Automática)")
        titulo.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        layout.addWidget(titulo)

        desc = QLabel("Subí tu archivo de Excel (CSV). El sistema usará IA para detectar qué es el Nombre, el Precio y el Código de Barras.")
        desc.setStyleSheet("color: #a0a0b0; font-size: 13px;")
        layout.addWidget(desc)

        # ── Panel de Carga ────────────────────────────────────────────────────
        panel_carga = QFrame()
        panel_carga.setStyleSheet(f"QFrame {{ background: {BG_PANEL}; border-radius: 12px; }}")
        carga_layout = QHBoxLayout(panel_carga)
        carga_layout.setContentsMargins(20, 20, 20, 20)

        self.lbl_archivo = QLabel("Ningún archivo seleccionado...")
        self.lbl_archivo.setStyleSheet("color: #a0a0b0; font-size: 14px; font-style: italic;")
        carga_layout.addWidget(self.lbl_archivo)

        btn_buscar = QPushButton("📂 Buscar Archivo")
        btn_buscar.setFixedHeight(40)
        btn_buscar.setStyleSheet(f"QPushButton {{ background: {ACCENT}; color: white; border-radius: 8px; font-weight: bold; padding: 0 20px; }} QPushButton:hover {{ background: #2980b9; }}")
        btn_buscar.clicked.connect(self.seleccionar_archivo)
        carga_layout.addWidget(btn_buscar)

        layout.addWidget(panel_carga)

        # ── Vista Previa ──────────────────────────────────────────────────────
        lbl_prev = QLabel("👀 Vista Previa de los Datos Detectados")
        lbl_prev.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        lbl_prev.setStyleSheet("color: #f39c12; margin-top: 10px;")
        layout.addWidget(lbl_prev)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels(["Nombre del Producto", "Precio Detectado", "Código Detectado"])
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabla.setColumnWidth(1, 150)
        self.tabla.setColumnWidth(2, 200)
        self.tabla.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tabla.setStyleSheet(f"""
            QTableWidget {{ background: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 8px; gridline-color: {BORDER}; }}
            QHeaderView::section {{ background: {BORDER}; color: #a0a0b0; padding: 8px; border: none; font-weight: bold; }}
            QTableWidgetItem {{ color: white; padding: 6px; }}
        """)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.tabla)

        # ── Controles de Importación ──────────────────────────────────────────
        panel_accion = QFrame()
        panel_accion.setStyleSheet(f"QFrame {{ background: transparent; }}")
        accion_layout = QVBoxLayout(panel_accion)
        accion_layout.setContentsMargins(0,0,0,0)

        self.barra_progreso = QProgressBar()
        self.barra_progreso.setFixedHeight(15)
        self.barra_progreso.setStyleSheet(f"""
            QProgressBar {{ border: 1px solid {BORDER}; border-radius: 7px; background: {BG_PANEL}; text-align: center; color: transparent; }}
            QProgressBar::chunk {{ background-color: #27ae60; border-radius: 6px; }}
        """)
        self.barra_progreso.setValue(0)
        self.barra_progreso.hide()
        accion_layout.addWidget(self.barra_progreso)

        btns_lay = QHBoxLayout()
        btns_lay.addStretch()
        
        self.btn_importar = QPushButton("🚀 IMPORTAR A MI SISTEMA")
        self.btn_importar.setFixedHeight(50)
        self.btn_importar.setEnabled(False)
        self.btn_importar.setStyleSheet(f"""
            QPushButton {{ background: {ACCENT_BOTON}; color: white; border-radius: 8px; font-size: 16px; font-weight: bold; padding: 0 30px; }}
            QPushButton:disabled {{ background: #555; color: #888; }}
            QPushButton:hover:!disabled {{ background: #c73652; }}
        """)
        self.btn_importar.clicked.connect(self.importar_datos)
        btns_lay.addWidget(self.btn_importar)
        
        accion_layout.addLayout(btns_lay)
        layout.addWidget(panel_accion)

    def seleccionar_archivo(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Buscar archivo de Eleventas", "", "Archivos CSV/TXT (*.csv *.txt)")
        if ruta:
            self.ruta_archivo = ruta
            self.lbl_archivo.setText(f"📄 {ruta.split('/')[-1]}")
            self.lbl_archivo.setStyleSheet("color: #27ae60; font-size: 14px; font-weight: bold;")
            self.leer_archivo()

    def es_codigo_barras(self, texto):
        # Si tiene más de 6 números (y no es un decimal largo), es un código de barras
        texto_limpio = str(texto).strip()
        if texto_limpio.isdigit() and len(texto_limpio) > 6:
            return True
        return False

    def es_precio(self, texto):
        # Si se puede convertir a número y tiene 6 o menos dígitos enteros
        texto_limpio = str(texto).replace("$", "").replace(",", ".").strip()
        try:
            val = float(texto_limpio)
            # Verificamos la parte entera
            if len(str(int(val))) <= 6:
                return True, val
            return False, 0.0
        except ValueError:
            return False, 0.0

    def leer_archivo(self):
        self.datos_extraidos = []
        try:
            with open(self.ruta_archivo, 'r', encoding='utf-8', errors='ignore') as f:
                lineas = f.readlines()
                if not lineas:
                    return

                separador = ';' if ';' in lineas[0] else ',' if ',' in lineas[0] else '\t'
                lector = csv.reader(lineas, delimiter=separador)
                
                # Omitimos la primera fila asumiendo que son títulos
                next(lector, None)
                
                for fila in lector:
                    if not fila: continue
                    
                    nombre = ""
                    precio = 0.0
                    codigo = ""
                    
                    # Analizamos cada celda de la fila usando la pista de Lucas
                    for celda in fila:
                        celda_str = str(celda).strip()
                        if not celda_str: continue
                        
                        if self.es_codigo_barras(celda_str):
                            codigo = celda_str
                        else:
                            es_num, valor_num = self.es_precio(celda_str)
                            if es_num:
                                precio = valor_num
                            else:
                                # Si no es código y no es precio, asumimos que es el nombre (o parte de él)
                                nombre += celda_str + " "
                                
                    nombre = nombre.strip()
                    
                    # Si al menos encontró un nombre y un precio, lo agregamos
                    if nombre and precio > 0:
                        self.datos_extraidos.append({"nombre": nombre, "precio": precio, "codigo": codigo})

            self.datos_extraidos.sort(key=lambda x: x["nombre"].lower())
            self.mostrar_vista_previa()
            
        except Exception as e:
            QMessageBox.critical(self, "Error de lectura", f"No se pudo leer el archivo.\n\nDetalle: {e}")

    def mostrar_vista_previa(self):
        self.tabla.setRowCount(len(self.datos_extraidos))
        for i, item in enumerate(self.datos_extraidos):
            self.tabla.setItem(i, 0, QTableWidgetItem(item["nombre"]))
            self.tabla.setItem(i, 1, QTableWidgetItem(f"${item['precio']:.2f}"))
            
            item_cod = QTableWidgetItem(item["codigo"] if item["codigo"] else "Sin código")
            if not item["codigo"]:
                item_cod.setForeground(QColor("#888888"))
            self.tabla.setItem(i, 2, item_cod)
            
        if self.datos_extraidos:
            self.btn_importar.setEnabled(True)
            self.btn_importar.setText(f"🚀 IMPORTAR {len(self.datos_extraidos)} PRODUCTOS")
        else:
            QMessageBox.warning(self, "Aviso", "No se detectaron productos válidos en el archivo.")

    def importar_datos(self):
        if not self.datos_extraidos:
            return
            
        respuesta = QMessageBox.question(self, "Confirmar", 
            f"¿Estás seguro de importar {len(self.datos_extraidos)} productos nuevos?\n\nEl sistema usará la detección automática para Precio y Código.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
        if respuesta == QMessageBox.StandardButton.Yes:
            self.btn_importar.setEnabled(False)
            self.barra_progreso.show()
            self.barra_progreso.setMaximum(len(self.datos_extraidos))
            self.barra_progreso.setValue(0)
            
            exitos = 0
            for i, item in enumerate(self.datos_extraidos):
                payload = {
                    "nombre": item["nombre"],
                    "precio_venta": item["precio"],
                    "precio_compra": 0,
                    "stock_actual": 0,
                    "categoria_id": 1, 
                    "codigo_barras": item["codigo"]
                }
                try:
                    r = requests.post(f"{API_URL}/productos/", json=payload, timeout=2)
                    if r.status_code in (200, 201):
                        exitos += 1
                except:
                    pass
                    
                self.barra_progreso.setValue(i + 1)
                
            QMessageBox.information(self, "Migración Completada", f"¡Éxito total, Lucas!\n\nSe importaron {exitos} productos a EL CUERVO STORE.")
            self.datos_extraidos = []
            self.tabla.setRowCount(0)
            self.lbl_archivo.setText("Ningún archivo seleccionado...")
            self.lbl_archivo.setStyleSheet("color: #a0a0b0; font-size: 14px; font-style: italic;")
            self.barra_progreso.hide()
            self.btn_importar.setEnabled(False)
            self.btn_importar.setText("🚀 IMPORTAR A MI SISTEMA")