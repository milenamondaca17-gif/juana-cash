import sys
import os
os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from ui.main_window import MainWindow
from ui.pantallas.splash import SplashScreen

app = QApplication(sys.argv)
app.setApplicationName("Juana Cash")
app.setStyle("Fusion")

# Mostrar splash
splash = SplashScreen()
splash.show()
app.processEvents()

# La ventana principal se crea pero se muestra cuando cierra el splash
main_window = MainWindow()

def mostrar_principal():
    main_window.showMaximized()

splash._terminar_callback = mostrar_principal

# Conectar cierre del splash con apertura de la ventana principal
original_terminar = splash._terminar
def _terminar_con_main():
    splash.lbl_estado.setText("✅ Bienvenido a Juana Cash")
    splash.lbl_estado.setStyleSheet("color: #27AE60; background: transparent; font-weight: bold;")
    QTimer.singleShot(600, lambda: (splash.close(), main_window.showMaximized()))

splash._terminar = _terminar_con_main

sys.exit(app.exec())
