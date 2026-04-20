import sys, os, threading, time
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
    sys.path.insert(0, os.path.join(APP_DIR, '_internal'))
    sys.path.insert(0, APP_DIR)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(APP_DIR, 'juana_cash.db')}"

def run_backend():
    try:
        import uvicorn
        from backend.app.main import app as fastapi_app
        uvicorn.run(fastapi_app, host="127.0.0.1", port=8000, log_level="error", access_log=False)
    except Exception as e:
        print(f"Backend error: {e}")

threading.Thread(target=run_backend, daemon=True).start()
time.sleep(3)

app = QApplication(sys.argv)
app.setApplicationName("Juana Cash")
app.setStyle("Fusion")

from ui.pantallas.splash import SplashScreen
from ui.main_window import MainWindow

splash = SplashScreen()
splash.show()
app.processEvents()
main_window = MainWindow()

def _terminar():
    splash.lbl_estado.setText("Bienvenido a Juana Cash")
    splash.lbl_estado.setStyleSheet("color: #27AE60; background: transparent; font-weight: bold;")
    QTimer.singleShot(600, lambda: (splash.close(), main_window.show()))

splash._terminar = _terminar
sys.exit(app.exec())
