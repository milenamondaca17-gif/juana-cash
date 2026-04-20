import os
import json
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QFrame, QScrollArea, QDialog,
                             QLineEdit, QSlider, QFileDialog, QMessageBox,
                             QColorDialog, QListWidget, QListWidgetItem,
                             QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QColor, QPalette

OFERTAS_PATH = os.path.join(os.path.expanduser("~"), "JuanaCash_Tickets", "ofertas.json")

BG_MAIN  = "#161925"
BG_PANEL = "#222738"
BORDER   = "#343B54"
TEXT_MAIN = "#F0F0F0"
TEXT_MUTED = "#8D99AE"
ACCENT   = "#556EE6"
ACCENT_OK = "#34C38F"

def leer_ofertas():
    try:
        os.makedirs(os.path.dirname(OFERTAS_PATH), exist_ok=True)
        if os.path.exists(OFERTAS_PATH):
            with open(OFERTAS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return []

def guardar_ofertas(ofertas):
    try:
        os.makedirs(os.path.dirname(OFERTAS_PATH), exist_ok=True)
        with open(OFERTAS_PATH, "w", encoding="utf-8") as f:
            json.dump(ofertas, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error guardando ofertas: {e}")

def leer_intervalo():
    try:
        cfg_path = os.path.join(os.path.dirname(OFERTAS_PATH), "ofertas_config.json")
        if os.path.exists(cfg_path):
            with open(cfg_path, "r") as f:
                return json.load(f).get("intervalo", 5)
    except Exception:
        pass
    return 5

def guardar_intervalo(seg):
    try:
        cfg_path = os.path.join(os.path.dirname(OFERTAS_PATH), "ofertas_config.json")
        os.makedirs(os.path.dirname(cfg_path), exist_ok=True)
        with open(cfg_path, "w") as f:
            json.dump({"intervalo": seg}, f)
    except Exception:
        pass


# ─── WIDGET ROTADOR (se incrusta en VentasScreen) ─────────────────────────────

class OfertasRotator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ofertas = []
        self.indice  = 0
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setup_ui()
        self.cargar()
        self.timer = QTimer()
        self.timer.timeout.connect(self.siguiente)
        self.actualizar_intervalo()
        self.timer.start()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.display = QLabel()
        self.display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.display.setStyleSheet(f"background: {BG_PANEL}; border-radius: 12px;")
        self.display.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.display.setMinimumHeight(200)
        layout.addWidget(self.display)

        nav = QHBoxLayout()
        nav.setSpacing(6)
        nav.setContentsMargins(0, 4, 0, 0)
        self.btn_prev = QPushButton("‹")
        self.btn_prev.setFixedSize(30, 30)
        self.btn_prev.setStyleSheet(f"background: {BG_PANEL}; color: {TEXT_MUTED}; border-radius: 15px; font-size: 18px; border: 1px solid {BORDER};")
        self.btn_prev.clicked.connect(self.anterior)
        self.lbl_num = QLabel("0 / 0")
        self.lbl_num.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        self.lbl_num.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.btn_next = QPushButton("›")
        self.btn_next.setFixedSize(30, 30)
        self.btn_next.setStyleSheet(f"background: {BG_PANEL}; color: {TEXT_MUTED}; border-radius: 15px; font-size: 18px; border: 1px solid {BORDER};")
        self.btn_next.clicked.connect(self.siguiente)
        nav.addStretch()
        nav.addWidget(self.btn_prev)
        nav.addWidget(self.lbl_num)
        nav.addWidget(self.btn_next)
        nav.addStretch()
        layout.addLayout(nav)

    def cargar(self):
        self.ofertas = leer_ofertas()
        self.indice  = 0
        self.mostrar()

    def actualizar_intervalo(self):
        seg = leer_intervalo()
        self.timer.setInterval(seg * 1000)

    def mostrar(self):
        if not self.ofertas:
            self.display.setPixmap(QPixmap())
            self.display.setText("Sin ofertas\nAgregá desde el menú Ofertas")
            self.display.setStyleSheet(f"background: {BG_PANEL}; color: {TEXT_MUTED}; border-radius: 12px; font-size: 14px;")
            self.lbl_num.setText("0 / 0")
            return

        oferta = self.ofertas[self.indice]
        self.lbl_num.setText(f"{self.indice + 1} / {len(self.ofertas)}")

        if oferta["tipo"] == "imagen":
            ruta = oferta["contenido"]
            if os.path.exists(ruta):
                pix = QPixmap(ruta)
                w = self.display.width()  if self.display.width()  > 10 else 340
                h = self.display.height() if self.display.height() > 10 else 500
                pix = pix.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio,
                                  Qt.TransformationMode.SmoothTransformation)
                self.display.setPixmap(pix)
                self.display.setText("")
                self.display.setStyleSheet("background: #000; border-radius: 12px;")
            else:
                self.display.setText(f"Imagen no encontrada:\n{ruta}")
                self.display.setStyleSheet(f"background: {BG_PANEL}; color: #e74c3c; border-radius: 12px; font-size: 12px;")
        else:
            # Oferta de texto
            texto  = oferta["contenido"]
            bg     = oferta.get("color_fondo", "#e74c3c")
            color  = oferta.get("color_texto", "#ffffff")
            size   = oferta.get("tamanio", 28)
            self.display.setPixmap(QPixmap())
            self.display.setText(texto)
            self.display.setStyleSheet(f"""
                background: {bg};
                color: {color};
                border-radius: 12px;
                font-size: {size}px;
                font-weight: bold;
                padding: 20px;
            """)
            self.display.setWordWrap(True)

    def siguiente(self):
        if not self.ofertas: return
        self.actualizar_intervalo()
        self.indice = (self.indice + 1) % len(self.ofertas)
        self.mostrar()

    def anterior(self):
        if not self.ofertas: return
        self.indice = (self.indice - 1) % len(self.ofertas)
        self.mostrar()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.mostrar()


# ─── PANTALLA DE GESTIÓN DE OFERTAS ───────────────────────────────────────────

class OfertasScreen(QWidget):
    oferta_cambiada = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.cargar_lista()

    def setup_ui(self):
        self.setStyleSheet(f"background-color: {BG_MAIN}; color: {TEXT_MAIN};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Título
        titulo = QLabel("🏷️ Gestión de Ofertas")
        titulo.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        titulo.setStyleSheet(f"color: {TEXT_MAIN};")
        layout.addWidget(titulo)

        subtitulo = QLabel("Las ofertas rotan automáticamente en la pantalla de ventas")
        subtitulo.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px;")
        layout.addWidget(subtitulo)

        # Intervalo
        interval_frame = QFrame()
        interval_frame.setStyleSheet(f"QFrame {{ background: {BG_PANEL}; border-radius: 10px; border: 1px solid {BORDER}; }}")
        int_lay = QHBoxLayout(interval_frame)
        int_lay.setContentsMargins(16, 12, 16, 12)
        lbl_int = QLabel("⏱ Rotar cada:")
        lbl_int.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px;")
        int_lay.addWidget(lbl_int)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(2)
        self.slider.setMaximum(15)
        self.slider.setValue(leer_intervalo())
        self.slider.setStyleSheet("QSlider::groove:horizontal { height: 6px; background: #343B54; border-radius: 3px; } QSlider::handle:horizontal { background: #556EE6; width: 18px; height: 18px; border-radius: 9px; margin: -6px 0; }")
        self.slider.valueChanged.connect(self.cambiar_intervalo)
        int_lay.addWidget(self.slider, 1)
        self.lbl_seg = QLabel(f"{self.slider.value()} seg")
        self.lbl_seg.setStyleSheet(f"color: #556EE6; font-size: 14px; font-weight: bold; min-width: 50px;")
        int_lay.addWidget(self.lbl_seg)
        layout.addWidget(interval_frame)

        # Botones agregar
        btns_row = QHBoxLayout()
        btn_foto = QPushButton("📷  Agregar Foto")
        btn_foto.setFixedHeight(46)
        btn_foto.setStyleSheet(f"QPushButton {{ background: {ACCENT}; color: white; border-radius: 10px; font-size: 14px; font-weight: bold; }} QPushButton:hover {{ background: #6d85f5; }}")
        btn_foto.clicked.connect(self.agregar_foto)
        btns_row.addWidget(btn_foto)

        btn_texto = QPushButton("📝  Agregar Texto")
        btn_texto.setFixedHeight(46)
        btn_texto.setStyleSheet(f"QPushButton {{ background: #f39c12; color: {BG_MAIN}; border-radius: 10px; font-size: 14px; font-weight: bold; }} QPushButton:hover {{ background: #f5b041; }}")
        btn_texto.clicked.connect(self.agregar_texto)
        btns_row.addWidget(btn_texto)
        layout.addLayout(btns_row)

        # Lista de ofertas
        lbl_lista = QLabel("Ofertas actuales:")
        lbl_lista.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; letter-spacing: 1px; font-weight: bold;")
        layout.addWidget(lbl_lista)

        self.lista = QListWidget()
        self.lista.setStyleSheet(f"""
            QListWidget {{ background: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 10px; padding: 4px; }}
            QListWidget::item {{ color: {TEXT_MAIN}; padding: 12px; border-bottom: 1px solid {BORDER}; font-size: 14px; border-radius: 6px; }}
            QListWidget::item:selected {{ background: {ACCENT}; color: white; }}
            QListWidget::item:hover {{ background: #2d3450; }}
        """)
        self.lista.setMinimumHeight(300)
        layout.addWidget(self.lista)

        # Botones acción
        acc_row = QHBoxLayout()
        btn_subir = QPushButton("⬆ Subir")
        btn_subir.setFixedHeight(38)
        btn_subir.setStyleSheet(f"QPushButton {{ background: {BG_PANEL}; color: {TEXT_MUTED}; border: 1px solid {BORDER}; border-radius: 8px; font-size: 13px; }} QPushButton:hover {{ background: {BORDER}; color: white; }}")
        btn_subir.clicked.connect(self.mover_arriba)
        acc_row.addWidget(btn_subir)

        btn_bajar = QPushButton("⬇ Bajar")
        btn_bajar.setFixedHeight(38)
        btn_bajar.setStyleSheet(f"QPushButton {{ background: {BG_PANEL}; color: {TEXT_MUTED}; border: 1px solid {BORDER}; border-radius: 8px; font-size: 13px; }} QPushButton:hover {{ background: {BORDER}; color: white; }}")
        btn_bajar.clicked.connect(self.mover_abajo)
        acc_row.addWidget(btn_bajar)

        acc_row.addStretch()

        btn_borrar = QPushButton("🗑 Eliminar")
        btn_borrar.setFixedHeight(38)
        btn_borrar.setStyleSheet(f"QPushButton {{ background: transparent; color: #e74c3c; border: 1px solid #e74c3c; border-radius: 8px; font-size: 13px; font-weight: bold; }} QPushButton:hover {{ background: #e74c3c; color: white; }}")
        btn_borrar.clicked.connect(self.eliminar)
        acc_row.addWidget(btn_borrar)
        layout.addLayout(acc_row)

    def cambiar_intervalo(self, val):
        self.lbl_seg.setText(f"{val} seg")
        guardar_intervalo(val)

    def cargar_lista(self):
        self.lista.clear()
        for o in leer_ofertas():
            if o["tipo"] == "imagen":
                nombre = os.path.basename(o["contenido"])
                item   = QListWidgetItem(f"📷  {nombre}")
            else:
                preview = o["contenido"][:40] + ("..." if len(o["contenido"]) > 40 else "")
                item    = QListWidgetItem(f"📝  {preview}")
            self.lista.addItem(item)

    def agregar_foto(self):
        rutas, _ = QFileDialog.getOpenFileNames(
            self, "Seleccionar imágenes", "",
            "Imágenes (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if not rutas: return
        ofertas = leer_ofertas()
        for ruta in rutas:
            ofertas.append({"tipo": "imagen", "contenido": ruta})
        guardar_ofertas(ofertas)
        self.cargar_lista()
        self.oferta_cambiada.emit()
        QMessageBox.information(self, "✅ Listo", f"{len(rutas)} imagen(es) agregada(s)")

    def agregar_texto(self):
        dialog = TextoOfertaDialog(self)
        if dialog.exec():
            ofertas = leer_ofertas()
            ofertas.append({
                "tipo":        "texto",
                "contenido":   dialog.texto,
                "color_fondo": dialog.color_fondo,
                "color_texto": dialog.color_texto,
                "tamanio":     dialog.tamanio
            })
            guardar_ofertas(ofertas)
            self.cargar_lista()
            self.oferta_cambiada.emit()

    def eliminar(self):
        idx = self.lista.currentRow()
        if idx < 0: return
        resp = QMessageBox.question(self, "Eliminar", "¿Eliminar esta oferta?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp != QMessageBox.StandardButton.Yes: return
        ofertas = leer_ofertas()
        ofertas.pop(idx)
        guardar_ofertas(ofertas)
        self.cargar_lista()
        self.oferta_cambiada.emit()

    def mover_arriba(self):
        idx = self.lista.currentRow()
        if idx <= 0: return
        ofertas = leer_ofertas()
        ofertas[idx], ofertas[idx-1] = ofertas[idx-1], ofertas[idx]
        guardar_ofertas(ofertas)
        self.cargar_lista()
        self.lista.setCurrentRow(idx - 1)
        self.oferta_cambiada.emit()

    def mover_abajo(self):
        idx = self.lista.currentRow()
        ofertas = leer_ofertas()
        if idx < 0 or idx >= len(ofertas) - 1: return
        ofertas[idx], ofertas[idx+1] = ofertas[idx+1], ofertas[idx]
        guardar_ofertas(ofertas)
        self.cargar_lista()
        self.lista.setCurrentRow(idx + 1)
        self.oferta_cambiada.emit()


# ─── DIÁLOGO PARA CREAR OFERTA DE TEXTO ───────────────────────────────────────

class TextoOfertaDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📝 Nueva oferta de texto")
        self.setMinimumWidth(460)
        self.setStyleSheet(f"background-color: {BG_MAIN}; color: {TEXT_MAIN};")
        self.texto       = ""
        self.color_fondo = "#e74c3c"
        self.color_texto = "#ffffff"
        self.tamanio     = 32
        self.setup_ui()

    def setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(14)
        lay.setContentsMargins(20, 20, 20, 20)

        lay.addWidget(QLabel("Texto de la oferta:"))
        self.input_texto = QLineEdit()
        self.input_texto.setPlaceholderText("Ej: 2x1 en Gaseosas 🎉")
        self.input_texto.setFixedHeight(48)
        self.input_texto.setStyleSheet(f"background: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 8px; padding: 10px; font-size: 16px;")
        self.input_texto.textChanged.connect(self.actualizar_preview)
        lay.addWidget(self.input_texto)

        # Tamaño de texto
        row_size = QHBoxLayout()
        row_size.addWidget(QLabel("Tamaño:"))
        self.slider_size = QSlider(Qt.Orientation.Horizontal)
        self.slider_size.setMinimum(18)
        self.slider_size.setMaximum(60)
        self.slider_size.setValue(32)
        self.slider_size.setStyleSheet("QSlider::groove:horizontal { height: 6px; background: #343B54; border-radius: 3px; } QSlider::handle:horizontal { background: #f39c12; width: 18px; height: 18px; border-radius: 9px; margin: -6px 0; }")
        self.slider_size.valueChanged.connect(self.actualizar_preview)
        self.lbl_size = QLabel("32px")
        self.lbl_size.setStyleSheet("color: #f39c12; font-weight: bold; min-width: 40px;")
        row_size.addWidget(self.slider_size, 1)
        row_size.addWidget(self.lbl_size)
        lay.addLayout(row_size)

        # Colores
        row_colores = QHBoxLayout()
        self.btn_fondo = QPushButton("🎨  Color de fondo")
        self.btn_fondo.setFixedHeight(40)
        self.btn_fondo.setStyleSheet(f"background: #e74c3c; color: white; border-radius: 8px; font-weight: bold;")
        self.btn_fondo.clicked.connect(self.elegir_fondo)
        row_colores.addWidget(self.btn_fondo)
        self.btn_texto_color = QPushButton("🔤  Color de texto")
        self.btn_texto_color.setFixedHeight(40)
        self.btn_texto_color.setStyleSheet(f"background: white; color: black; border-radius: 8px; font-weight: bold;")
        self.btn_texto_color.clicked.connect(self.elegir_texto)
        row_colores.addWidget(self.btn_texto_color)
        lay.addLayout(row_colores)

        # Preview
        lay.addWidget(QLabel("Vista previa:"))
        self.preview = QLabel("Tu texto aquí")
        self.preview.setFixedHeight(120)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setWordWrap(True)
        self.preview.setStyleSheet(f"background: #e74c3c; color: white; border-radius: 12px; font-size: 32px; font-weight: bold; padding: 10px;")
        lay.addWidget(self.preview)

        # Botones
        row_btns = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setFixedHeight(42)
        btn_cancelar.setStyleSheet(f"background: transparent; color: {TEXT_MUTED}; border: 1px solid {BORDER}; border-radius: 8px;")
        btn_cancelar.clicked.connect(self.reject)
        row_btns.addWidget(btn_cancelar)
        btn_ok = QPushButton("✅  Agregar oferta")
        btn_ok.setFixedHeight(42)
        btn_ok.setStyleSheet(f"background: {ACCENT_OK}; color: {BG_MAIN}; border-radius: 8px; font-weight: bold; font-size: 14px;")
        btn_ok.clicked.connect(self.confirmar)
        row_btns.addWidget(btn_ok)
        lay.addLayout(row_btns)

    def actualizar_preview(self):
        self.tamanio = self.slider_size.value()
        self.lbl_size.setText(f"{self.tamanio}px")
        texto = self.input_texto.text() or "Tu texto aquí"
        self.preview.setText(texto)
        self.preview.setStyleSheet(f"background: {self.color_fondo}; color: {self.color_texto}; border-radius: 12px; font-size: {self.tamanio}px; font-weight: bold; padding: 10px;")

    def elegir_fondo(self):
        color = QColorDialog.getColor(QColor(self.color_fondo), self, "Color de fondo")
        if color.isValid():
            self.color_fondo = color.name()
            self.btn_fondo.setStyleSheet(f"background: {self.color_fondo}; color: white; border-radius: 8px; font-weight: bold;")
            self.actualizar_preview()

    def elegir_texto(self):
        color = QColorDialog.getColor(QColor(self.color_texto), self, "Color de texto")
        if color.isValid():
            self.color_texto = color.name()
            self.btn_texto_color.setStyleSheet(f"background: {self.color_texto}; color: {'black' if self.color_texto == '#ffffff' else 'white'}; border-radius: 8px; font-weight: bold;")
            self.actualizar_preview()

    def confirmar(self):
        if not self.input_texto.text().strip():
            QMessageBox.warning(self, "Aviso", "Escribí algo en el texto")
            return
        self.texto   = self.input_texto.text().strip()
        self.tamanio = self.slider_size.value()
        self.accept()
