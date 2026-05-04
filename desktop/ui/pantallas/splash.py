import sys
import os
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QBrush, QLinearGradient

class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.progress_value = 0
        self.setup_ui()
        self.iniciar_carga()

    def setup_ui(self):
        self.setFixedSize(680, 400)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.SplashScreen
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Centrar en pantalla
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width()  - self.width())  // 2,
            (screen.height() - self.height()) // 2
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 45, 60, 40)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ── Ícono ─────────────────────────────────────────────────────────────
        lbl_icon = QLabel("$↗")
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_icon.setFont(QFont("Arial", 52, QFont.Weight.Bold))
        lbl_icon.setStyleSheet("color: #27AE60; background: transparent;")
        layout.addWidget(lbl_icon)
        layout.addSpacing(8)

        # ── Nombre ────────────────────────────────────────────────────────────
        lbl_titulo = QLabel("JUANA CA$H")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_titulo.setFont(QFont("Arial", 46, QFont.Weight.Bold))
        lbl_titulo.setStyleSheet("color: white; background: transparent; letter-spacing: 6px;")
        layout.addWidget(lbl_titulo)

        lbl_sub = QLabel("GESTIÓN DE CAJA")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_sub.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        lbl_sub.setStyleSheet("color: #27AE60; background: transparent; letter-spacing: 8px;")
        layout.addWidget(lbl_sub)

        layout.addSpacing(8)

        # ── Línea decorativa ──────────────────────────────────────────────────
        lbl_linea = QLabel("─" * 42)
        lbl_linea.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_linea.setStyleSheet("color: #1B3A5C; background: transparent; font-size: 10px;")
        layout.addWidget(lbl_linea)

        layout.addSpacing(16)

        # ── Barra de progreso ─────────────────────────────────────────────────
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFixedHeight(5)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                background: #0d1f35;
                border-radius: 3px;
                border: none;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1B9FD4,
                    stop:0.5 #27AE60,
                    stop:1 #1B9FD4);
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress)
        layout.addSpacing(10)

        # ── Estado ────────────────────────────────────────────────────────────
        self.lbl_estado = QLabel("Iniciando sistema...")
        self.lbl_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_estado.setFont(QFont("Arial", 10))
        self.lbl_estado.setStyleSheet("color: #4a7a9a; background: transparent;")
        layout.addWidget(self.lbl_estado)

        layout.addSpacing(14)

        # ── Porcentaje ────────────────────────────────────────────────────────
        self.lbl_pct = QLabel("0%")
        self.lbl_pct.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_pct.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.lbl_pct.setStyleSheet("color: #1B9FD4; background: transparent;")
        layout.addWidget(self.lbl_pct)

        layout.addSpacing(10)

        # ── Usuario ───────────────────────────────────────────────────────────
        lbl_user = QLabel("CAMMUS_25  //  DIGITAL CREATOR")
        lbl_user.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_user.setFont(QFont("Arial", 9))
        lbl_user.setStyleSheet("color: #2a4a6a; background: transparent; letter-spacing: 2px;")
        layout.addWidget(lbl_user)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Fondo principal oscuro
        painter.setBrush(QBrush(QColor(8, 14, 28)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 14, 14)

        # Borde exterior azul
        pen = QPen(QColor(27, 159, 212, 120))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(1, 1, self.width()-2, self.height()-2, 13, 13)

        # Borde interior verde muy sutil
        pen2 = QPen(QColor(39, 174, 96, 40))
        pen2.setWidth(1)
        painter.setPen(pen2)
        painter.drawRoundedRect(3, 3, self.width()-6, self.height()-6, 12, 12)

        # Circuitos decorativos esquina superior derecha
        pen3 = QPen(QColor(27, 159, 212, 30))
        pen3.setWidth(1)
        painter.setPen(pen3)
        for i in range(6):
            y = 18 + i * 9
            painter.drawLine(self.width() - 130 + i*12, y, self.width() - 25, y)
        painter.drawLine(self.width() - 25, 18, self.width() - 25, 18 + 5*9)

        # Circuitos decorativos esquina inferior izquierda
        for i in range(5):
            y = self.height() - 18 - i * 9
            painter.drawLine(25, y, 110 - i*10, y)
        painter.drawLine(25, self.height()-18, 25, self.height() - 18 - 4*9)

        # Puntos de circuito
        painter.setBrush(QBrush(QColor(39, 174, 96, 80)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(self.width() - 28, 16, 6, 6)
        painter.drawEllipse(self.width() - 40, 26, 4, 4)
        painter.drawEllipse(25, self.height() - 20, 6, 6)
        painter.drawEllipse(35, self.height() - 30, 4, 4)

        # Hexágonos decorativos (esquinas)
        pen4 = QPen(QColor(27, 159, 212, 15))
        pen4.setWidth(1)
        painter.setPen(pen4)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for x, y, r in [(45, 45, 20), (self.width()-45, self.height()-45, 20),
                        (self.width()-60, 40, 14), (55, self.height()-50, 14)]:
            painter.drawEllipse(x-r, y-r, r*2, r*2)

    def iniciar_carga(self):
        self.pasos = [
            (8,   "Verificando configuración..."),
            (18,  "Conectando base de datos..."),
            (32,  "Buscando actualizaciones..."),
            (45,  "Cargando productos..."),
            (58,  "Inicializando módulos..."),
            (70,  "Cargando interfaz..."),
            (82,  "Preparando reportes..."),
            (92,  "Casi listo..."),
            (100, "¡Sistema listo!"),
        ]
        self.paso_actual = 0
        self._update_msg = None
        self.timer = QTimer()
        self.timer.timeout.connect(self._avanzar)
        self.timer.start(220)

        # Verificar actualizaciones en segundo plano
        try:
            import sys, os
            # Buscar updater en distintas ubicaciones
            for ruta in [
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "updater.py"),
                os.path.join(os.path.dirname(sys.executable), "updater.py"),
                "updater.py",
            ]:
                ruta = os.path.normpath(ruta)
                if os.path.exists(ruta):
                    sys.path.insert(0, os.path.dirname(ruta))
                    break

            from updater import Updater
            u = Updater()

            def _cerrar_app_qt():
                from PyQt6.QtWidgets import QApplication
                from PyQt6.QtCore import QTimer
                self._set_update_msg("🔄 Instalando actualización... cerrando")
                QTimer.singleShot(2500, QApplication.instance().quit)

            u.verificar(
                on_preguntar=lambda v: True,
                on_descargando=lambda v: self._set_update_msg(f"⬇️ Descargando v{v}..."),
                on_actualizado=lambda v: self._set_update_msg(f"✅ v{v} descargada — instalando..."),
                on_sin_internet=lambda: None,
                on_no_hay_update=lambda: None,
                on_cerrar_app=_cerrar_app_qt,
            )
        except Exception as e:
            try:
                import traceback
                _log_path = os.path.join(os.path.expanduser("~"), "JuanaCash_Data", "juana_update.log")
                os.makedirs(os.path.dirname(_log_path), exist_ok=True)
                with open(_log_path, "a", encoding="utf-8") as f:
                    f.write(f"[SPLASH ERROR] {e}\n{traceback.format_exc()}\n")
            except Exception:
                pass

    def _set_update_msg(self, msg):
        self._update_msg = msg
        QTimer.singleShot(0, lambda: (
            self.lbl_estado.setText(msg),
            self.lbl_estado.setStyleSheet("color: #F59E0B; background: transparent;")
        ))

    def _avanzar(self):
        if self.paso_actual >= len(self.pasos):
            self.timer.stop()
            QTimer.singleShot(400, self._terminar)
            return
        valor, texto = self.pasos[self.paso_actual]
        self.progress.setValue(valor)
        self.lbl_estado.setText(texto)
        self.lbl_pct.setText(f"{valor}%")
        self.paso_actual += 1

    def _terminar(self):
        self.lbl_estado.setText("✅ Bienvenido a Juana Cash")
        self.lbl_estado.setStyleSheet("color: #27AE60; background: transparent; font-weight: bold;")
        QTimer.singleShot(600, self.close)
