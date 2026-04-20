import sys
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QLabel, QScrollArea, 
                             QDialog, QMessageBox, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor

# ---------- 1. MOTOR DEL PDF (ACEPTA VARIOS PRODUCTOS) ----------
def fabricar_pdf_mixto(lista_productos):
    """Genera una hoja A4 llenando las etiquetas según la lista que le pases"""
    ruta_segura = os.path.abspath("Etiquetas_JuanaCash_Impresion.pdf")
    
    c = canvas.Canvas(ruta_segura, pagesize=A4)
    ancho_pagina, alto_pagina = A4
    
    margen_x = 10 * mm
    margen_y = 15 * mm
    columnas = 3
    filas = 5 
    
    ancho_etiqueta = (ancho_pagina - (margen_x * 2)) / columnas
    alto_etiqueta = (alto_pagina - (margen_y * 2)) / filas
    
    # Recorremos los 15 lugares de la hoja
    for i in range(15):
        col_actual = i % columnas
        fila_actual = i // columnas
        
        x = margen_x + (col_actual * ancho_etiqueta)
        y = alto_pagina - margen_y - ((fila_actual + 1) * alto_etiqueta)
        
        # Si hay un producto para este lugar, lo dibujamos
        if i < len(lista_productos):
            prod = lista_productos[i]
            nombre = prod["nombre"]
            precio = prod["precio"]
            
            c.setFillColor(HexColor("#ffffff"))
            c.setStrokeColor(HexColor("#000000"))
            c.setLineWidth(1)
            c.rect(x + 2*mm, y + 2*mm, ancho_etiqueta - 4*mm, alto_etiqueta - 4*mm, fill=1, stroke=1)
            
            c.setFillColor(HexColor("#000000")) 
            c.setFont("Helvetica-Bold", 12)
            c.drawCentredString(x + (ancho_etiqueta / 2), y + alto_etiqueta - 10*mm, "JUANA CASH")
            
            c.setFont("Helvetica", 12)
            nombre_corto = nombre[:30] + "..." if len(nombre) > 30 else nombre
            c.drawCentredString(x + (ancho_etiqueta / 2), y + alto_etiqueta - 20*mm, nombre_corto)
            
            c.setFont("Helvetica-Bold", 36)
            c.drawCentredString(x + (ancho_etiqueta / 2), y + 15*mm, f"${precio:,.2f}")
        else:
            # Si el lugar está vacío, dibujamos solo un borde gris muy clarito como guía de recorte
            c.setStrokeColor(HexColor("#dddddd"))
            c.rect(x + 2*mm, y + 2*mm, ancho_etiqueta - 4*mm, alto_etiqueta - 4*mm, fill=0, stroke=1)

    c.save()
    return ruta_segura


# ---------- 2. VENTANA PARA INGRESAR EL PRECIO ----------
class DialogoPrecioEtiqueta(QDialog):
    def __init__(self, nombre_producto, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ingresar Precio")
        self.setFixedSize(400, 200)
        self.setStyleSheet("background-color: #050e1a; color: white; border: 2px solid #1a2744; border-radius: 8px;")
        
        layout = QVBoxLayout(self)
        
        lbl = QLabel(f"¿A qué precio publicamos:\n{nombre_producto}?")
        lbl.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("border: none;")
        layout.addWidget(lbl)
        
        self.input_precio = QLineEdit()
        self.input_precio.setPlaceholderText("$ 0.00")
        self.input_precio.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        self.input_precio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input_precio.setStyleSheet("background-color: #111d33; color: #00ff7f; padding: 10px; border: 2px solid #e63946;")
        self.input_precio.setFocus()
        self.input_precio.returnPressed.connect(self.accept)
        layout.addWidget(self.input_precio)
        
        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet("background-color: transparent; color: #8899aa; border: 1px solid #8899aa; padding: 10px; font-weight: bold;")
        btn_cancel.clicked.connect(self.reject)
        
        btn_ok = QPushButton("Agregar a la hoja")
        btn_ok.setStyleSheet("background-color: #e63946; color: white; padding: 10px; font-weight: bold; border: none;")
        btn_ok.clicked.connect(self.accept)
        
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_ok)
        layout.addLayout(btn_layout)
        
    def get_precio(self):
        try:
            texto = self.input_precio.text().replace("$", "").replace(" ", "").replace(",", ".").strip()
            return float(texto)
        except ValueError:
            return 0.0


# ---------- 3. PANTALLA PRINCIPAL (CON CONTADOR) ----------
class GeneradorEtiquetasScreen(QWidget):
    def __init__(self):
        super().__init__()
        # Acá guardamos los productos que vas eligiendo
        self.etiquetas_en_espera = []
        
        self.setWindowTitle("Generador de Etiquetas")
        self.setStyleSheet("background-color: transparent;")
        
        main_layout = QVBoxLayout(self)
        
        titulo = QLabel("🖨️ FÁBRICA DE ETIQUETAS A4")
        titulo.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        titulo.setStyleSheet("color: #e63946;")
        main_layout.addWidget(titulo)
        
        # --- BUSCADOR ---
        search_layout = QHBoxLayout()
        self.input_buscar = QLineEdit()
        self.input_buscar.setPlaceholderText("🔍 Buscar producto para sumar a la hoja...")
        self.input_buscar.setFont(QFont("Arial", 16))
        self.input_buscar.setFixedHeight(60)
        self.input_buscar.setStyleSheet("background-color: #0a1628; color: white; border: 2px solid #1a2744; border-radius: 8px; padding: 0 15px;")
        self.input_buscar.returnPressed.connect(self.buscar_producto)
        search_layout.addWidget(self.input_buscar)
        
        btn_buscar = QPushButton("BUSCAR")
        btn_buscar.setFixedHeight(60)
        btn_buscar.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        btn_buscar.setStyleSheet("background-color: #e63946; color: white; border-radius: 8px; padding: 0 25px;")
        btn_buscar.clicked.connect(self.buscar_producto)
        search_layout.addWidget(btn_buscar)
        main_layout.addLayout(search_layout)
        
        # --- RESULTADOS DE BÚSQUEDA ---
        self.scroll = QScrollArea()
        self.scroll.setFixedHeight(120)
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none; background: transparent;")
        
        self.contenedor_resultados = QWidget()
        self.layout_resultados = QHBoxLayout(self.contenedor_resultados)
        self.layout_resultados.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.scroll.setWidget(self.contenedor_resultados)
        main_layout.addWidget(self.scroll)
        
        main_layout.addStretch()
        
        # --- PANEL INFERIOR (CONTADOR Y FINALIZAR) ---
        panel_inferior = QFrame()
        panel_inferior.setStyleSheet("background-color: #0a1628; border: 2px solid #1a2744; border-radius: 12px;")
        panel_inferior.setFixedHeight(100)
        layout_inferior = QHBoxLayout(panel_inferior)
        layout_inferior.setContentsMargins(20, 10, 20, 10)
        
        self.lbl_contador = QLabel("📄 Etiquetas en la hoja: 0 / 15")
        self.lbl_contador.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.lbl_contador.setStyleSheet("color: #8899aa; border: none;")
        layout_inferior.addWidget(self.lbl_contador)
        
        layout_inferior.addStretch()
        
        btn_limpiar = QPushButton("Limpiar Hoja")
        btn_limpiar.setFixedHeight(60)
        btn_limpiar.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        btn_limpiar.setStyleSheet("background-color: transparent; color: #e63946; border: 2px solid #e63946; border-radius: 8px; padding: 0 20px; margin-right: 15px;")
        btn_limpiar.clicked.connect(self.limpiar_memoria)
        layout_inferior.addWidget(btn_limpiar)
        
        self.btn_fabricar = QPushButton("✔️ FINALIZAR Y FABRICAR")
        self.btn_fabricar.setFixedHeight(60)
        self.btn_fabricar.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.btn_fabricar.setStyleSheet("""
            QPushButton { background-color: #27ae60; color: white; border-radius: 8px; padding: 0 30px; }
            QPushButton:disabled { background-color: #1a2744; color: #8899aa; }
        """)
        self.btn_fabricar.clicked.connect(self.fabricar_ahora)
        self.btn_fabricar.setEnabled(False) # Arranca apagado porque hay 0
        layout_inferior.addWidget(self.btn_fabricar)
        
        main_layout.addWidget(panel_inferior)

    def limpiar_resultados(self):
        for i in reversed(range(self.layout_resultados.count())): 
            w = self.layout_resultados.itemAt(i).widget()
            self.layout_resultados.removeWidget(w)
            w.setParent(None)

    def buscar_producto(self):
        texto = self.input_buscar.text().strip().upper()
        if not texto: return
        self.limpiar_resultados()
        
        # Simulamos base de datos
        opciones = [f"{texto} (COMÚN)", f"{texto} (PREMIUM)", f"{texto} (SUELTO)"]
        
        for prod in opciones:
            btn = QPushButton(prod)
            btn.setFixedHeight(80)
            btn.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            btn.setStyleSheet("""
                QPushButton { background-color: #111d33; color: white; border: 2px solid #8899aa; border-radius: 8px; padding: 0 20px; margin-right: 15px;}
                QPushButton:hover { border-color: #00ff7f; color: #00ff7f; }
            """)
            btn.clicked.connect(lambda checked, p=prod: self.preguntar_y_agregar(p))
            self.layout_resultados.addWidget(btn)

    def preguntar_y_agregar(self, nombre_producto):
        if len(self.etiquetas_en_espera) >= 15:
            QMessageBox.warning(self, "Hoja Llena", "¡Ya metiste 15 etiquetas! Fabricá esta hoja primero para poder armar otra nueva.")
            return

        dialogo = DialogoPrecioEtiqueta(nombre_producto, self)
        if dialogo.exec():
            precio = dialogo.get_precio()
            if precio > 0:
                # LO AGREGAMOS A LA MEMORIA
                self.etiquetas_en_espera.append({"nombre": nombre_producto, "precio": precio})
                self.actualizar_panel()
                
                self.limpiar_resultados()
                self.input_buscar.clear()
                self.input_buscar.setFocus()

    def actualizar_panel(self):
        cantidad = len(self.etiquetas_en_espera)
        
        # Color verde si ya hay etiquetas
        color = "#00ff7f" if cantidad > 0 else "#8899aa"
        self.lbl_contador.setStyleSheet(f"color: {color}; border: none;")
        self.lbl_contador.setText(f"📄 Etiquetas en la hoja: {cantidad} / 15")
        
        self.btn_fabricar.setEnabled(cantidad > 0)

    def limpiar_memoria(self):
        self.etiquetas_en_espera = []
        self.actualizar_panel()
        self.input_buscar.setFocus()

    def fabricar_ahora(self):
        try:
            ruta_pdf = fabricar_pdf_mixto(self.etiquetas_en_espera)
            os.startfile(ruta_pdf)
            # Una vez impreso, limpiamos la hoja para la próxima tanda
            self.limpiar_memoria()
        except Exception as e:
            QMessageBox.critical(self, "Error grave", f"No se pudo fabricar el PDF.\n\nDetalle: {e}")

# Solo para probar la ventana suelta
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = GeneradorEtiquetasScreen()
    ventana.show()
    sys.exit(app.exec())