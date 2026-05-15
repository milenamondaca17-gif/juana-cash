import requests
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QLineEdit, QFrame, QMessageBox,
                              QTableWidget, QTableWidgetItem, QHeaderView,
                              QDialog, QFormLayout, QDoubleSpinBox, QSpinBox,
                              QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

API_URL = "http://127.0.0.1:8000"

from ui.theme import get_tema as _gt
_T = _gt()
_BG = _T["bg_app"]; _CARD = _T["bg_card"]; _TXT = _T["text_main"]
_MUT = _T["text_muted"]; _PRI = _T["primary"]; _DGR = _T["danger"]
_BOR = _T["border"]; _OK = _T["success"]

CATEGORIAS = ["General", "Carnicería", "Verdulería", "Panadería", "Fiambrería",
              "Lácteos", "Limpieza", "Bebidas", "Cigarrería", "Confitería"]

class ProductoDialog(QDialog):
    def __init__(self, parent=None, producto=None):
        super().__init__(parent)
        self.producto = producto
        self.setWindowTitle("✏️ Editar producto" if producto else "➕ Nuevo producto")
        self.setMinimumWidth(440)
        self.setStyleSheet(f"background-color: {_CARD}; color: {_TXT};")
        self.extra_codes_inputs = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        titulo = QLabel("📦 Datos del producto")
        titulo.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        titulo.setStyleSheet(f"color: {_PRI}; background: transparent;")
        layout.addWidget(titulo)

        estilo = f"background: {_BG}; border: 1.5px solid {_BOR}; border-radius: 8px; padding: 8px; color: {_TXT}; font-size: 14px;"

        self.form = QFormLayout() # Lo hacemos self para acceder desde otros métodos
        self.form.setSpacing(10)

        self.input_nombre = QLineEdit()
        self.input_nombre.setStyleSheet(f"QLineEdit {{ {estilo} }}")
        self.input_nombre.setFixedHeight(40)
        self.form.addRow("Nombre *:", self.input_nombre)

        # --- SECCIÓN CÓDIGO DE BARRAS CON BOTÓN + ---
        self.barras_layout = QVBoxLayout()
        self.barras_layout.setSpacing(5)
        
        # Fila principal
        fila_principal = QHBoxLayout()
        self.input_codigo = QLineEdit()
        self.input_codigo.setPlaceholderText("Código principal...")
        self.input_codigo.setStyleSheet(f"QLineEdit {{ {estilo} }}")
        self.input_codigo.setFixedHeight(40)
        
        btn_add_code = QPushButton("+")
        btn_add_code.setFixedSize(40, 40)
        btn_add_code.setStyleSheet("QPushButton { background: #3498db; color: white; border-radius: 8px; font-weight: bold; font-size: 18px; }")
        btn_add_code.clicked.connect(lambda: self.agregar_campo_codigo(""))
        
        fila_principal.addWidget(self.input_codigo)
        fila_principal.addWidget(btn_add_code)
        
        self.barras_layout.addLayout(fila_principal)
        self.form.addRow("Código barras:", self.barras_layout)
        # --------------------------------------------

        self.combo_categoria = QComboBox()
        self.combo_categoria.addItems(CATEGORIAS)
        self.combo_categoria.setFixedHeight(40)
        self.combo_categoria.setStyleSheet(f"""
            QComboBox {{ {estilo} }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox QAbstractItemView {{ background: {_CARD}; color: {_TXT}; selection-background-color: {_PRI}; }}
        """)
        self.form.addRow("Categoría:", self.combo_categoria)

        self.input_precio_compra = QDoubleSpinBox()
        self.input_precio_compra.setRange(0, 9999999)
        self.input_precio_compra.setPrefix("$")
        self.input_precio_compra.setFixedHeight(40)
        self.input_precio_compra.setStyleSheet(f"QDoubleSpinBox {{ {estilo} }}")
        self.form.addRow("Precio costo:", self.input_precio_compra)

        self.input_precio_venta = QDoubleSpinBox()
        self.input_precio_venta.setRange(0, 9999999)
        self.input_precio_venta.setPrefix("$")
        self.input_precio_venta.setFixedHeight(40)
        self.input_precio_venta.setStyleSheet(f"QDoubleSpinBox {{ {estilo} }}")
        self.input_precio_venta.valueChanged.connect(self.calcular_margen)
        self.input_precio_compra.valueChanged.connect(self.calcular_margen)
        self.form.addRow("Precio venta:", self.input_precio_venta)

        self.lbl_margen = QLabel("Margen: —")
        self.lbl_margen.setStyleSheet("color: #27ae60; font-size: 13px; font-weight: bold;")
        self.form.addRow("", self.lbl_margen)

        self.input_stock = QDoubleSpinBox()
        self.input_stock.setRange(0, 999999)
        self.input_stock.setFixedHeight(40)
        self.input_stock.setStyleSheet(f"QDoubleSpinBox {{ {estilo} }}")
        self.form.addRow("Stock actual:", self.input_stock)

        self.input_stock_minimo = QDoubleSpinBox()
        self.input_stock_minimo.setRange(0, 999999)
        self.input_stock_minimo.setFixedHeight(40)
        self.input_stock_minimo.setStyleSheet(f"QDoubleSpinBox {{ {estilo} }}")
        self.form.addRow("Stock mínimo:", self.input_stock_minimo)

        self.input_unidad = QLineEdit()
        self.input_unidad.setPlaceholderText("unidad, kg, litro...")
        self.input_unidad.setStyleSheet(f"QLineEdit {{ {estilo} }}")
        self.input_unidad.setFixedHeight(40)
        self.form.addRow("Unidad:", self.input_unidad)

        layout.addLayout(self.form)

        # Llenar datos si es edición
        if self.producto:
            self.input_nombre.setText(self.producto.get("nombre", ""))
            self.input_codigo.setText(self.producto.get("codigo_barra", "") or "")
            self.input_precio_compra.setValue(float(self.producto.get("precio_costo") or 0))
            self.input_precio_venta.setValue(float(self.producto.get("precio_venta") or 0))
            self.input_stock.setValue(float(self.producto.get("stock_actual") or 0))
            self.input_stock_minimo.setValue(float(self.producto.get("stock_minimo") or 0))
            self.input_unidad.setText(self.producto.get("unidad_medida", "") or "")
            
            # Cargar códigos extra si existen
            extras = self.producto.get("codigos_extra", [])
            for ex in extras:
                self.agregar_campo_codigo(ex.get("codigo", ""))

            cat = self.producto.get("categoria", "General")
            idx = self.combo_categoria.findText(cat)
            if idx >= 0: self.combo_categoria.setCurrentIndex(idx)

        btns = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setFixedHeight(44)
        btn_cancelar.setStyleSheet(f"QPushButton {{ background: transparent; color: {_MUT}; border: 1.5px solid {_BOR}; border-radius: 8px; font-weight: bold; }}")
        btn_cancelar.clicked.connect(self.reject)
        btns.addWidget(btn_cancelar)

        btn_guardar = QPushButton("💾 Guardar")
        btn_guardar.setFixedHeight(44)
        btn_guardar.setStyleSheet(f"QPushButton {{ background: {_PRI}; color: white; border-radius: 8px; font-size: 14px; font-weight: bold; }} QPushButton:hover {{ background: {_T['primary_hover']}; }}")
        btn_guardar.clicked.connect(self.guardar)
        btns.addWidget(btn_guardar)
        layout.addLayout(btns)

    def agregar_campo_codigo(self, texto=""):
        fila = QHBoxLayout()
        nuevo_input = QLineEdit()
        nuevo_input.setText(texto)
        nuevo_input.setPlaceholderText("Código extra...")
        nuevo_input.setStyleSheet("background: #0f3460; border: 1px solid #3498db; border-radius: 8px; padding: 8px; color: white;")
        nuevo_input.setFixedHeight(35)
        
        btn_del = QPushButton("✕")
        btn_del.setFixedSize(35, 35)
        btn_del.setStyleSheet("QPushButton { background: #e94560; color: white; border-radius: 8px; }")
        
        fila.addWidget(nuevo_input)
        fila.addWidget(btn_del)
        self.barras_layout.addLayout(fila)
        self.extra_codes_inputs.append((nuevo_input, fila))
        
        btn_del.clicked.connect(lambda: self.remover_campo_codigo(nuevo_input, fila))

    def remover_campo_codigo(self, input_widget, layout_obj):
        for i, (w, l) in enumerate(self.extra_codes_inputs):
            if w == input_widget:
                self.extra_codes_inputs.pop(i)
                input_widget.deleteLater()
                # Limpiar widgets del layout antes de borrarlo
                while layout_obj.count():
                    item = layout_obj.takeAt(0)
                    if item.widget(): item.widget().deleteLater()
                break

    def calcular_margen(self):
        compra = self.input_precio_compra.value()
        venta = self.input_precio_venta.value()
        if compra > 0 and venta > 0:
            margen = ((venta - compra) / compra) * 100
            ganancia = venta - compra
            color = "#27ae60" if margen >= 20 else "#e67e22" if margen >= 10 else "#e94560"
            self.lbl_margen.setText(f"Margen: {margen:.1f}% — Ganancia: ${ganancia:.2f}")
            self.lbl_margen.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: bold;")
        else:
            self.lbl_margen.setText("Margen: —")

    def guardar(self):
        if not self.input_nombre.text().strip():
            QMessageBox.warning(self, "Error", "El nombre es obligatorio")
            return
        if self.input_precio_venta.value() <= 0:
            QMessageBox.warning(self, "Error", "El precio de venta debe ser mayor a $0")
            return
        self.accept()

    def get_datos(self):
        # Recolectamos códigos extra que tengan texto
        codigos_adicionales = []
        for inp, _ in self.extra_codes_inputs:
            txt = inp.text().strip()
            if txt:
                codigos_adicionales.append({"codigo": txt})

        return {
            "nombre": self.input_nombre.text().strip(),
            "codigo_barra": self.input_codigo.text().strip() or None,
            "codigos_extra": codigos_adicionales, # <--- MANDAMOS LA LISTA AL BACKEND
            "categoria": self.combo_categoria.currentText(),
            "precio_costo": self.input_precio_compra.value(),
            "precio_venta": self.input_precio_venta.value(),
            "stock_actual": self.input_stock.value(),
            "stock_minimo": self.input_stock_minimo.value(),
            "unidad_medida": self.input_unidad.text().strip() or "unidad",
            "activo": True
        }


class ProductosScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.productos = []
        self.setup_ui()

    def showEvent(self, event):
        super().showEvent(event)
        self._cargar_resumen()
        self.tabla.setRowCount(0)
        self.tabla.setRowCount(1)
        item = QTableWidgetItem("Escribí al menos 2 letras para buscar un producto")
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tabla.setItem(0, 0, item)
        self.tabla.setSpan(0, 0, 1, 9)

    def setup_ui(self):
        self.setStyleSheet(f"background-color: {_BG}; color: {_TXT};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        header = QHBoxLayout()
        titulo = QLabel("📦 Productos")
        titulo.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        titulo.setStyleSheet(f"color: {_TXT}; background: transparent;")
        header.addWidget(titulo)
        header.addStretch()

        self.input_buscar = QLineEdit()
        self.input_buscar.setPlaceholderText("🔍 Buscar producto...")
        self.input_buscar.setFixedWidth(220)
        self.input_buscar.setFixedHeight(36)
        self.input_buscar.textChanged.connect(self.filtrar)
        header.addWidget(self.input_buscar)

        btn_stock_bajo = QPushButton("⚠️ Stock bajo")
        btn_stock_bajo.setFixedHeight(36)
        btn_stock_bajo.setStyleSheet(f"QPushButton {{ background: {_T['warning']}; color: white; border-radius: 8px; padding: 0 12px; font-weight: bold; }}")
        btn_stock_bajo.clicked.connect(self.ver_stock_bajo)
        header.addWidget(btn_stock_bajo)

        btn_nuevo = QPushButton("➕ Nuevo")
        btn_nuevo.setFixedHeight(36)
        btn_nuevo.setStyleSheet(f"QPushButton {{ background: {_PRI}; color: white; border-radius: 8px; padding: 0 16px; font-weight: bold; }} QPushButton:hover {{ background: {_T['primary_hover']}; }}")
        btn_nuevo.clicked.connect(self.nuevo_producto)
        header.addWidget(btn_nuevo)

        btn_act = QPushButton("🔄")
        btn_act.setFixedSize(36, 36)
        btn_act.setStyleSheet(f"QPushButton {{ background: {_T['primary_light']}; color: {_PRI}; border-radius: 8px; border: 1.5px solid {_PRI}; }} QPushButton:hover {{ background: {_PRI}; color: white; }}")
        btn_act.clicked.connect(self.cargar_productos)
        header.addWidget(btn_act)
        layout.addLayout(header)

        resumen = QHBoxLayout()
        self.card_total     = self.crear_card("📦 Total productos",    "0",  "#2563eb")
        self.card_stock_bajo = self.crear_card("⚠️ Stock bajo",        "0",  "#d97706")
        self.card_sin_stock  = self.crear_card("❌ Sin stock",         "0",  "#dc2626")
        self.card_valor      = self.crear_card("💰 Valor inventario",  "$0", "#16a34a")
        for c in [self.card_total, self.card_stock_bajo, self.card_sin_stock, self.card_valor]:
            resumen.addWidget(c[0])
        layout.addLayout(resumen)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(9)
        self.tabla.setHorizontalHeaderLabels([
            "Nombre", "Código", "Categoría", "Costo",
            "Venta", "Margen", "Stock", "Mín.", "Acciones"
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.tabla)

    def crear_card(self, titulo, valor, color):
        card = QFrame()
        card.setStyleSheet(f"QFrame {{ background: {_CARD}; border-radius: 12px; border-left: 5px solid {color}; border: 1.5px solid {_BOR}; border-left: 5px solid {color}; }}")
        card.setMinimumHeight(80)
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(16, 10, 16, 10)
        lbl_t = QLabel(titulo)
        lbl_t.setStyleSheet("color: #a0a0b0; font-size: 12px;")
        c_layout.addWidget(lbl_t)
        lbl_v = QLabel(valor)
        lbl_v.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        lbl_v.setStyleSheet(f"color: {color};")
        c_layout.addWidget(lbl_v)
        return card, lbl_v

    def _cargar_resumen(self):
        try:
            r = requests.get(f"{API_URL}/productos/resumen", timeout=5)
            if r.status_code == 200:
                d = r.json()
                self.card_total[1].setText(str(d.get("total", "—")))
                self.card_stock_bajo[1].setText(str(d.get("stock_bajo", "—")))
                self.card_sin_stock[1].setText(str(d.get("sin_stock", "—")))
                self.card_valor[1].setText(f"${d.get('valor_inventario', 0):,.0f}".replace(",", "."))
        except Exception:
            pass

    def cargar_productos(self):
        try:
            r = requests.get(f"{API_URL}/productos/", timeout=30)
            if r.status_code == 200:
                self.productos = r.json()
                self.mostrar_productos(self.productos)
                self.actualizar_resumen()
        except requests.exceptions.ConnectionError:
            QMessageBox.critical(self, "Error", "No se puede conectar al servidor")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar productos:\n{str(e)}")

    def actualizar_resumen(self):
        total = len(self.productos)
        stock_bajo = sum(1 for p in self.productos
                        if float(p.get("stock_actual") or 0) <= float(p.get("stock_minimo") or 0)
                        and float(p.get("stock_minimo") or 0) > 0)
        sin_stock = sum(1 for p in self.productos if float(p.get("stock_actual") or 0) <= 0)
        valor = sum(float(p.get("stock_actual") or 0) * float(p.get("precio_costo") or 0)
                   for p in self.productos)
        self.card_total[1].setText(str(total))
        self.card_stock_bajo[1].setText(str(stock_bajo))
        self.card_sin_stock[1].setText(str(sin_stock))
        self.card_valor[1].setText(f"${valor:,.0f}".replace(",", "."))

    def filtrar(self, texto):
        if len(texto) < 2:
            self.tabla.setRowCount(0)
            self.tabla.setRowCount(1)
            item = QTableWidgetItem("Escribí al menos 2 letras para buscar un producto")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla.setItem(0, 0, item)
            self.tabla.setSpan(0, 0, 1, 9)
            self.productos = []
            return
        try:
            r = requests.get(f"{API_URL}/productos/buscar", params={"q": texto}, timeout=5)
            if r.status_code == 200:
                self.productos = r.json()
                self.mostrar_productos(self.productos, es_filtro=True)
        except Exception:
            pass

    def mostrar_productos(self, productos, es_filtro=False):
        MAX_MOSTRAR = 50
        if not es_filtro and len(productos) > MAX_MOSTRAR:
            mostrar = productos[:MAX_MOSTRAR]
            self.lbl_filtro_info = f"Mostrando {MAX_MOSTRAR} de {len(productos)} — Usá el buscador para encontrar productos"
        else:
            mostrar = productos
            self.lbl_filtro_info = ""
        self.tabla.setRowCount(len(mostrar))
        for i, p in enumerate(mostrar):
            self.tabla.setItem(i, 0, QTableWidgetItem(p["nombre"]))
            self.tabla.setItem(i, 1, QTableWidgetItem(p.get("codigo_barra") or "-"))
            self.tabla.setItem(i, 2, QTableWidgetItem(p.get("categoria") or "-"))

            costo = float(p.get("precio_costo") or 0)
            venta = float(p.get("precio_venta") or 0)
            self.tabla.setItem(i, 3, QTableWidgetItem(f"${costo:.2f}"))
            self.tabla.setItem(i, 4, QTableWidgetItem(f"${venta:.2f}"))

            # Margen
            if costo > 0 and venta > 0:
                margen = ((venta - costo) / costo) * 100
                item_margen = QTableWidgetItem(f"{margen:.1f}%")
                if margen >= 20:
                    item_margen.setForeground(Qt.GlobalColor.green)
                elif margen >= 10:
                    item_margen.setForeground(Qt.GlobalColor.yellow)
                else:
                    item_margen.setForeground(Qt.GlobalColor.red)
                self.tabla.setItem(i, 5, item_margen)
            else:
                self.tabla.setItem(i, 5, QTableWidgetItem("—"))

            # Stock
            stock = float(p.get("stock_actual") or 0)
            stock_min = float(p.get("stock_minimo") or 0)
            stock_str = str(int(stock)) if stock == int(stock) else str(stock)
            stock_min_str = str(int(stock_min)) if stock_min == int(stock_min) else str(stock_min)
            item_stock = QTableWidgetItem(stock_str)
            if stock <= 0:
                item_stock.setForeground(Qt.GlobalColor.red)
            elif stock_min > 0 and stock <= stock_min:
                item_stock.setForeground(Qt.GlobalColor.yellow)
            else:
                item_stock.setForeground(Qt.GlobalColor.green)
            self.tabla.setItem(i, 6, item_stock)
            self.tabla.setItem(i, 7, QTableWidgetItem(stock_min_str))

            # Botones
            btn_w = QWidget()
            btn_l = QHBoxLayout(btn_w)
            btn_l.setContentsMargins(1, 1, 1, 1)
            btn_l.setSpacing(2)

            btn_edit = QPushButton("Ed")
            btn_edit.setFixedSize(32, 24)
            btn_edit.setStyleSheet("QPushButton { background: #0f3460; color: white; border-radius: 3px; font-size: 10px; }")
            btn_edit.clicked.connect(lambda _, idx=i: self.editar_producto(idx))
            btn_l.addWidget(btn_edit)

            btn_ajuste = QPushButton("St")
            btn_ajuste.setFixedSize(32, 24)
            btn_ajuste.setStyleSheet("QPushButton { background: #27ae60; color: white; border-radius: 3px; font-size: 10px; }")
            btn_ajuste.clicked.connect(lambda _, idx=i: self.ajustar_stock(idx))
            btn_l.addWidget(btn_ajuste)

            btn_borrar = QPushButton("🗑")
            btn_borrar.setFixedSize(28, 24)
            btn_borrar.setStyleSheet("QPushButton { background: #e74c3c; color: white; border-radius: 3px; font-size: 10px; }")
            btn_borrar.clicked.connect(lambda _, idx=i: self.eliminar_producto(idx))
            btn_l.addWidget(btn_borrar)

            self.tabla.setCellWidget(i, 8, btn_w)

    def nuevo_producto(self):
        dialog = ProductoDialog(self)
        if dialog.exec():
            datos = dialog.get_datos()
            try:
                r = requests.post(f"{API_URL}/productos/", json=datos, timeout=5)
                if r.status_code == 200:
                    self.cargar_productos()
                    QMessageBox.information(self, "✅", "Producto creado correctamente")
                else:
                    QMessageBox.critical(self, "Error", f"No se pudo crear: {r.text}")
            except Exception:
                QMessageBox.critical(self, "Error", "No se puede conectar al servidor")

    def editar_producto(self, idx):
        productos_visibles = self.get_productos_visibles()
        if idx >= len(productos_visibles):
            return
        producto = productos_visibles[idx]
        dialog = ProductoDialog(self, producto)
        if dialog.exec():
            datos = dialog.get_datos()
            try:
                r = requests.put(f"{API_URL}/productos/{producto['id']}", json=datos, timeout=5)
                if r.status_code == 200:
                    self.cargar_productos()
                else:
                    QMessageBox.critical(self, "Error", "No se pudo actualizar")
            except Exception:
                QMessageBox.critical(self, "Error", "No se puede conectar al servidor")

    def ajustar_stock(self, idx):
        productos_visibles = self.get_productos_visibles()
        if idx >= len(productos_visibles):
            return
        p = productos_visibles[idx]

        dialog = QDialog(self)
        dialog.setWindowTitle(f"📊 Ajuste de stock — {p['nombre']}")
        dialog.setMinimumWidth(340)
        dialog.setStyleSheet("background-color: #1a1a2e; color: white;")
        lay = QVBoxLayout(dialog)
        lay.setSpacing(12)

        lbl = QLabel(f"Stock actual: {p.get('stock_actual', 0)}")
        lbl.setStyleSheet("color: #e94560; font-size: 14px; font-weight: bold;")
        lay.addWidget(lbl)

        lbl2 = QLabel("Nuevo stock:")
        lbl2.setStyleSheet("color: #a0a0b0; font-size: 13px;")
        lay.addWidget(lbl2)

        input_stock = QDoubleSpinBox()
        input_stock.setRange(0, 999999)
        input_stock.setValue(float(p.get("stock_actual") or 0))
        input_stock.setDecimals(2)
        input_stock.setFixedHeight(44)
        input_stock.setStyleSheet("QDoubleSpinBox { background: #0f3460; border: 1px solid #e94560; border-radius: 8px; padding: 8px; color: white; font-size: 16px; }")
        lay.addWidget(input_stock)

        lbl3 = QLabel("Motivo del ajuste:")
        lbl3.setStyleSheet("color: #a0a0b0; font-size: 13px;")
        lay.addWidget(lbl3)

        combo_motivo = QComboBox()
        combo_motivo.addItems(["Inventario físico", "Rotura", "Vencimiento", "Error de carga", "Robo", "Donación", "Otro"])
        combo_motivo.setFixedHeight(40)
        combo_motivo.setStyleSheet("""
            QComboBox { background: #0f3460; border: 1px solid #e94560; border-radius: 8px; padding: 8px; color: white; font-size: 14px; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { background: #0f3460; color: white; selection-background-color: #e94560; }
        """)
        lay.addWidget(combo_motivo)

        btns = QHBoxLayout()
        btn_c = QPushButton("Cancelar")
        btn_c.setFixedHeight(40)
        btn_c.setStyleSheet("QPushButton { background: transparent; color: #a0a0b0; border: 1px solid #a0a0b0; border-radius: 8px; }")
        btn_c.clicked.connect(dialog.reject)
        btns.addWidget(btn_c)

        btn_ok = QPushButton("✅ Guardar ajuste")
        btn_ok.setFixedHeight(40)
        btn_ok.setStyleSheet("QPushButton { background: #27ae60; color: white; border-radius: 8px; font-size: 14px; font-weight: bold; }")
        btns.addWidget(btn_ok)
        lay.addLayout(btns)

        def confirmar():
            nuevo_stock = input_stock.value()
            motivo = combo_motivo.currentText()
            datos = dict(p)
            datos["stock_actual"] = nuevo_stock
            try:
                r = requests.put(f"{API_URL}/productos/{p['id']}", json=datos, timeout=5)
                if r.status_code == 200:
                    self.cargar_productos()
                    dialog.accept()
                    QMessageBox.information(self, "✅",
                        f"Stock actualizado a {nuevo_stock}\nMotivo: {motivo}")
            except Exception:
                QMessageBox.critical(dialog, "Error", "No se puede conectar")

        btn_ok.clicked.connect(confirmar)
        dialog.exec()

    def eliminar_producto(self, idx):
        productos_visibles = self.get_productos_visibles()
        if idx >= len(productos_visibles):
            return
        p = productos_visibles[idx]
        resp = QMessageBox.question(self, "Eliminar producto",
            f"¿Eliminar '{p['nombre']}'?\n\nEl producto se desactiva, no se borra definitivamente.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp != QMessageBox.StandardButton.Yes:
            return
        try:
            r = requests.delete(f"{API_URL}/productos/{p['id']}", timeout=10)
            if r.status_code == 200:
                self.cargar_productos()
                QMessageBox.information(self, "✅", f"'{p['nombre']}' eliminado")
            else:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar: {r.text}")
        except Exception:
            QMessageBox.critical(self, "Error", "No se puede conectar al servidor")

    def ver_stock_bajo(self):
        try:
            r = requests.get(f"{API_URL}/reportes/stock-bajo", timeout=5)
            if r.status_code == 200:
                productos = r.json()
                if not productos:
                    QMessageBox.information(self, "✅ Stock", "¡Todos los productos tienen stock suficiente!")
                    return
                msg = "Productos con stock bajo:\n\n"
                for p in productos:
                    msg += f"• {p['nombre']}: {p['stock_actual']} (mín: {p['stock_minimo']})\n"
                QMessageBox.warning(self, f"⚠️ {len(productos)} productos con stock bajo", msg)
        except Exception:
            QMessageBox.critical(self, "Error", "No se puede conectar al servidor")

    def get_productos_visibles(self):
        texto = self.input_buscar.text()
        if not texto:
            return self.productos
        return [p for p in self.productos
                if texto.lower() in p["nombre"].lower()
                or texto in (p.get("codigo_barra") or "")]