import csv
import os
import requests
try:
    import openpyxl
    TIENE_EXCEL = True
except ImportError:
    TIENE_EXCEL = False
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QFileDialog, QTableWidget,
                             QTableWidgetItem, QHeaderView, QFrame,
                             QMessageBox, QProgressBar)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

API_URL = "http://127.0.0.1:8000"

def _p(v):
    return f"${float(v):,.0f}".replace(",", ".")

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

        desc = QLabel("Subí tu archivo de Excel (.xlsx) o CSV. El sistema detecta automáticamente qué es el Nombre, el Precio y el Código de Barras.")
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
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels(["Código", "Producto", "P. Costo", "P. Venta", "Stock", "Departamento"])
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla.setColumnWidth(0, 130)
        self.tabla.setColumnWidth(2, 100)
        self.tabla.setColumnWidth(3, 100)
        self.tabla.setColumnWidth(4, 80)
        self.tabla.setColumnWidth(5, 140)
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
        ruta, _ = QFileDialog.getOpenFileName(self, "Buscar archivo de productos", "", "Archivos soportados (*.csv *.txt *.xlsx *.xls);;Excel (*.xlsx *.xls);;CSV/TXT (*.csv *.txt)")
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

    def _limpiar_precio(self, texto):
        """Limpia un texto de precio en cualquier formato:
        $23,500.00 → 23500.0
        $23.500,00 → 23500.0  (formato argentino)
        23500 → 23500.0
        None → 0.0
        """
        if texto is None:
            return 0.0
        # Si ya es número (openpyxl devuelve float/int directo)
        if isinstance(texto, (int, float)):
            return float(texto)
        texto = str(texto).replace("$", "").replace(" ", "").strip()
        if not texto or texto.lower() in ("none", "-"):
            return 0.0
        # Detectar formato: si tiene punto Y coma, hay que decidir cuál es decimal
        tiene_coma = "," in texto
        tiene_punto = "." in texto
        if tiene_coma and tiene_punto:
            # "$23,500.00" (US) o "$23.500,00" (AR)
            pos_coma = texto.rfind(",")
            pos_punto = texto.rfind(".")
            if pos_coma > pos_punto:
                # Formato argentino: 23.500,00 → punto es miles, coma es decimal
                texto = texto.replace(".", "").replace(",", ".")
            else:
                # Formato US: 23,500.00 → coma es miles, punto es decimal
                texto = texto.replace(",", "")
        elif tiene_coma:
            # Solo coma: puede ser "1,00" decimal o "1,000" miles
            partes = texto.split(",")
            if len(partes[-1]) == 2:
                # "1.200,00" → coma es decimal
                texto = texto.replace(",", ".")
            else:
                # "1,000" → coma es miles
                texto = texto.replace(",", "")
        # punto solo → ya es formato correcto
        try:
            return float(texto)
        except ValueError:
            return 0.0

    def _detectar_columnas(self, encabezados):
        """Detecta qué columna es cada cosa por el nombre del encabezado."""
        mapa = {"codigo": -1, "nombre": -1, "p_costo": -1, "p_venta": -1, "stock": -1, "depto": -1}
        for i, h in enumerate(encabezados):
            h = str(h).lower().strip()
            if "prod" in h or h == "nombre" or h == "descripcion" or h == "articulo":
                if mapa["nombre"] == -1:
                    mapa["nombre"] = i
            elif "costo" in h or "compra" in h:
                if mapa["p_costo"] == -1:
                    mapa["p_costo"] = i
            elif h.startswith("p") and "venta" in h and "tipo" not in h:
                # "P. Venta", "Precio Venta", "PVenta" — pero NO "Tipo de Venta"
                if mapa["p_venta"] == -1:
                    mapa["p_venta"] = i
            elif "mayor" in h:
                pass  # ignorar mayoreo
            elif h in ("codigo", "código", "cod", "barras", "codigo_barra", "ean", "upc", "sku"):
                mapa["codigo"] = i
            elif "exist" in h or "stock" in h or "cant" in h or "inventario" in h:
                if mapa["stock"] == -1:
                    mapa["stock"] = i
            elif "depart" in h or "categ" in h or "rubro" in h or "familia" in h:
                if mapa["depto"] == -1:
                    mapa["depto"] = i
        # Si no detectó precio de venta, buscar columna que diga "precio" sola
        if mapa["p_venta"] == -1:
            for i, h in enumerate(encabezados):
                h = str(h).lower().strip()
                if "precio" in h and i != mapa["p_costo"] and "tipo" not in h:
                    mapa["p_venta"] = i
                    break
        return mapa

    def leer_archivo(self):
        self.datos_extraidos = []
        try:
            ext = os.path.splitext(self.ruta_archivo)[1].lower()

            if ext in (".xlsx", ".xls"):
                encabezados, filas = self._leer_excel()
            else:
                encabezados, filas = self._leer_csv()

            if not encabezados or not filas:
                QMessageBox.warning(self, "Aviso", "El archivo está vacío o no tiene datos.")
                return

            mapa = self._detectar_columnas(encabezados)

            if mapa["nombre"] == -1 or mapa["p_venta"] == -1:
                QMessageBox.warning(self, "Aviso",
                    f"No se detectaron las columnas obligatorias.\n\n"
                    f"Encabezados encontrados: {', '.join(str(h) for h in encabezados)}\n\n"
                    f"Se necesita al menos: Producto y Precio de Venta")
                return

            for fila in filas:
                if not fila or len(fila) <= max(v for v in mapa.values() if v >= 0):
                    continue

                nombre = str(fila[mapa["nombre"]]).strip() if mapa["nombre"] >= 0 else ""
                p_venta = self._limpiar_precio(fila[mapa["p_venta"]]) if mapa["p_venta"] >= 0 else 0
                p_costo = self._limpiar_precio(fila[mapa["p_costo"]]) if mapa["p_costo"] >= 0 else 0
                codigo = str(fila[mapa["codigo"]]).strip() if mapa["codigo"] >= 0 else ""
                stock = self._limpiar_precio(fila[mapa["stock"]]) if mapa["stock"] >= 0 else 0
                depto = str(fila[mapa["depto"]]).strip() if mapa["depto"] >= 0 else ""

                # Limpiar código (sacar .0 si viene de Excel como número)
                if codigo.endswith(".0"):
                    codigo = codigo[:-2]
                if codigo.lower() in ("none", "0", ""):
                    codigo = ""

                if nombre and nombre.lower() not in ("none", "") and p_venta > 0:
                    self.datos_extraidos.append({
                        "nombre": nombre,
                        "precio": p_venta,
                        "costo": p_costo,
                        "codigo": codigo,
                        "stock": stock,
                        "depto": depto
                    })

            self.datos_extraidos.sort(key=lambda x: x["nombre"].lower())
            self.mostrar_vista_previa()

        except Exception as e:
            QMessageBox.critical(self, "Error de lectura", f"No se pudo leer el archivo.\n\nDetalle: {e}")

    def _leer_csv(self):
        """Lee un archivo CSV/TXT y devuelve (encabezados, filas)."""
        with open(self.ruta_archivo, 'r', encoding='utf-8', errors='ignore') as f:
            lineas = f.readlines()
            if not lineas:
                return [], []
            separador = ';' if ';' in lineas[0] else ',' if ',' in lineas[0] else '\t'
            lector = csv.reader(lineas, delimiter=separador)
            encabezados = next(lector, [])
            return encabezados, list(lector)

    def _leer_excel(self):
        """Lee un archivo .xlsx y devuelve (encabezados, filas)."""
        if not TIENE_EXCEL:
            QMessageBox.warning(self, "Falta librería",
                "Para leer Excel necesitás instalar openpyxl.\n\n"
                "Pegá en la terminal:\npip install openpyxl")
            return [], []
        wb = openpyxl.load_workbook(self.ruta_archivo, read_only=True, data_only=True)
        ws = wb.active
        filas_raw = []
        for row in ws.iter_rows(values_only=True):
            filas_raw.append([c if c is not None else "" for c in row])
        wb.close()
        if not filas_raw:
            return [], []
        return filas_raw[0], filas_raw[1:]

    def mostrar_vista_previa(self):
        self.tabla.setRowCount(len(self.datos_extraidos))
        for i, item in enumerate(self.datos_extraidos):
            item_cod = QTableWidgetItem(item["codigo"] if item["codigo"] else "-")
            if not item["codigo"]:
                item_cod.setForeground(QColor("#888888"))
            self.tabla.setItem(i, 0, item_cod)
            self.tabla.setItem(i, 1, QTableWidgetItem(item["nombre"]))
            self.tabla.setItem(i, 2, QTableWidgetItem(_p(item['costo']) if item["costo"] else "-"))
            self.tabla.setItem(i, 3, QTableWidgetItem(_p(item['precio'])))
            self.tabla.setItem(i, 4, QTableWidgetItem(f"{int(item['stock'])}" if item["stock"] else "0"))
            self.tabla.setItem(i, 5, QTableWidgetItem(item["depto"] if item["depto"] else "-"))

        if self.datos_extraidos:
            self.btn_importar.setEnabled(True)
            self.btn_importar.setText(f"🚀 IMPORTAR {len(self.datos_extraidos)} PRODUCTOS")
        else:
            QMessageBox.warning(self, "Aviso", "No se detectaron productos válidos en el archivo.")

    def importar_datos(self):
        if not self.datos_extraidos:
            return
            
        respuesta = QMessageBox.question(self, "Confirmar", 
            f"¿Importar {len(self.datos_extraidos)} productos?\n\n"
            f"Se cargarán con nombre, código, precio de venta, precio de costo y stock.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
        if respuesta == QMessageBox.StandardButton.Yes:
            self.btn_importar.setEnabled(False)
            self.barra_progreso.show()
            self.barra_progreso.setMaximum(len(self.datos_extraidos))
            self.barra_progreso.setValue(0)
            
            exitos = 0
            errores = 0
            for i, item in enumerate(self.datos_extraidos):
                payload = {
                    "nombre": item["nombre"],
                    "precio_venta": item["precio"],
                    "precio_costo": item.get("costo", 0) or 0,
                    "stock_actual": item.get("stock", 0) or 0,
                    "codigo_barra": item["codigo"] if item["codigo"] else None
                }
                try:
                    r = requests.post(f"{API_URL}/productos/", json=payload, timeout=3)
                    if r.status_code in (200, 201):
                        exitos += 1
                    else:
                        errores += 1
                except:
                    errores += 1
                    
                self.barra_progreso.setValue(i + 1)
            
            msg = f"Se importaron {exitos} de {len(self.datos_extraidos)} productos."
            if errores:
                msg += f"\n\n{errores} productos no se pudieron importar (posible código duplicado)."
            QMessageBox.information(self, "Importación Completada", msg)
            self.datos_extraidos = []
            self.tabla.setRowCount(0)
            self.lbl_archivo.setText("Ningún archivo seleccionado...")
            self.lbl_archivo.setStyleSheet("color: #a0a0b0; font-size: 14px; font-style: italic;")
            self.barra_progreso.hide()
            self.btn_importar.setEnabled(False)
            self.btn_importar.setText("🚀 IMPORTAR A MI SISTEMA")