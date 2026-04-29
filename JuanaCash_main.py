import sys, os, threading, time

if getattr(sys, 'frozen', False):
    APP_DIR  = os.path.dirname(sys.executable)
    INTERNAL = sys._MEIPASS
    if sys.stdout is None:
        sys.stdout = open(os.devnull, 'w')
    if sys.stderr is None:
        sys.stderr = open(os.devnull, 'w')
else:
    APP_DIR  = os.path.dirname(os.path.abspath(__file__))
    INTERNAL = APP_DIR

sys.path.insert(0, INTERNAL)
sys.path.insert(0, APP_DIR)

# ── Base de datos en carpeta del usuario (escribible siempre) ─────────────────
DATA_DIR = os.path.join(os.path.expanduser("~"), "JuanaCash_Data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH  = os.path.join(DATA_DIR, "juana_cash.db")

# Migrar base de datos vieja si existe en APP_DIR
_db_vieja = os.path.join(APP_DIR, "juana_cash.db")
if os.path.exists(_db_vieja) and not os.path.exists(DB_PATH):
    import shutil
    shutil.copy2(_db_vieja, DB_PATH)

os.environ['DATABASE_URL'] = f"sqlite:///{DB_PATH}"

def run_backend():
    try:
        from backend.app.main import app as fastapi_app
        import uvicorn
        uvicorn.run(fastapi_app, host="127.0.0.1", port=8000, log_level="error", access_log=False)
    except Exception as e:
        try:
            with open(os.path.join(DATA_DIR, "debug.log"), "a") as f:
                import traceback
                f.write(f"ERROR BACKEND: {e}\n")
                f.write(traceback.format_exc())
        except:
            pass

threading.Thread(target=run_backend, daemon=True).start()
time.sleep(3)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
sys.path.insert(0, os.path.join(INTERNAL, 'desktop'))
from ui.pantallas.splash import SplashScreen
from ui.main_window import MainWindow

app = QApplication(sys.argv)
app.setApplicationName("Juana Cash")
app.setStyle("Fusion")
try:
    from ui.theme import get_qss
    app.setStyleSheet(get_qss())
except Exception:
    pass
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
