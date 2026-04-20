import sys, os, threading, time

if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
    INTERNAL = sys._MEIPASS
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    INTERNAL = APP_DIR

LOG = os.path.join(APP_DIR, "debug.log")

def log(msg):
    with open(LOG, "a") as f:
        f.write(msg + "\n")

log(f"APP_DIR: {APP_DIR}")
log(f"INTERNAL: {INTERNAL}")
log(f"sys.path: {sys.path}")

sys.path.insert(0, INTERNAL)
sys.path.insert(0, APP_DIR)

os.environ['DATABASE_URL'] = f"sqlite:///{os.path.join(APP_DIR, 'juana_cash.db')}"

def run_backend():
    try:
        log("Intentando importar backend...")
        from backend.app.main import app as fastapi_app
        log("Backend importado OK")
        import uvicorn
        uvicorn.run(fastapi_app, host="127.0.0.1", port=8000, log_level="error", access_log=False)
    except Exception as e:
        log(f"ERROR BACKEND: {e}")
        import traceback
        log(traceback.format_exc())

threading.Thread(target=run_backend, daemon=True).start()
time.sleep(3)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
sys.path.insert(0, os.path.join(INTERNAL, 'desktop'))
from ui.pantallas.splash import SplashScreen
from ui.main_window import MainWindow

app = QApplication(sys.argv)
splash = SplashScreen()
splash.show()
app.processEvents()
main_window = MainWindow()

def _terminar():
    splash.lbl_estado.setText("Bienvenido")
    QTimer.singleShot(600, lambda: (splash.close(), main_window.show()))

splash._terminar = _terminar
sys.exit(app.exec())
