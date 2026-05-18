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

os.environ['DATABASE_URL'] = "sqlite:///" + DB_PATH.replace("\\", "/")

def run_backend():
    import socket as _socket
    for _ in range(20):
        try:
            _s = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
            _s.bind(("0.0.0.0", 8000))
            _s.close()
            break
        except OSError:
            time.sleep(0.5)
    try:
        from backend.app.main import app as fastapi_app
        import uvicorn
        uvicorn.run(fastapi_app, host="0.0.0.0", port=8000, log_level="error", access_log=False)
    except Exception as e:
        try:
            with open(os.path.join(DATA_DIR, "debug.log"), "a", encoding="utf-8") as f:
                import traceback
                f.write(f"ERROR BACKEND: {e}\n")
                f.write(traceback.format_exc())
        except:
            pass

def _udp_broadcaster():
    """Transmite la IP de la PC por UDP broadcast cada 2 s para que el celular la encuentre."""
    import socket as _socket, json as _json
    while True:
        try:
            # Obtener IP local real (la de la red WiFi/LAN)
            tmp = _socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM)
            tmp.settimeout(1)
            tmp.connect(("8.8.8.8", 80))
            my_ip = tmp.getsockname()[0]
            tmp.close()

            s = _socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM)
            s.setsockopt(_socket.SOL_SOCKET, _socket.SO_BROADCAST, 1)
            s.settimeout(1)
            msg = _json.dumps({"service": "JuanaCash", "ip": my_ip, "port": 8000}).encode()
            s.sendto(msg, ("<broadcast>", 55555))
            s.close()
        except Exception:
            pass
        time.sleep(2)

def _auto_backup():
    """Copia la base de datos a backups/ todos los días a las 22:15."""
    import shutil
    from datetime import datetime
    BACKUP_DIR = os.path.join(DATA_DIR, "backups")
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backup_hecho_hoy = None
    while True:
        ahora = datetime.now()
        if ahora.hour == 22 and ahora.minute == 15 and backup_hecho_hoy != ahora.date():
            try:
                nombre = f"juana_cash_{ahora.strftime('%Y%m%d')}_2215.db"
                destino = os.path.join(BACKUP_DIR, nombre)
                shutil.copy2(DB_PATH, destino)
                backup_hecho_hoy = ahora.date()
                # Mantener solo los últimos 7 backups
                archivos = sorted(
                    [f for f in os.listdir(BACKUP_DIR) if f.startswith("juana_cash_") and f.endswith(".db")],
                    reverse=True
                )
                for viejo in archivos[7:]:
                    try:
                        os.remove(os.path.join(BACKUP_DIR, viejo))
                    except Exception:
                        pass
                try:
                    with open(os.path.join(DATA_DIR, "debug.log"), "a", encoding="utf-8") as f:
                        f.write(f"[{ahora}] Backup automático: {nombre}\n")
                except Exception:
                    pass
            except Exception as e:
                try:
                    with open(os.path.join(DATA_DIR, "debug.log"), "a", encoding="utf-8") as f:
                        f.write(f"[{ahora}] ERROR backup: {e}\n")
                except Exception:
                    pass
        time.sleep(30)

def _reporte_nocturno():
    """A las 22:20 envía el resumen del día completo a los 3 números de WhatsApp."""
    import urllib.request as _ur
    import json as _json
    from datetime import datetime as _dt
    NUMEROS = ["2634670678", "2634633099", "2634633067"]
    enviado_hoy = None
    while True:
        ahora = _dt.now()
        if ahora.hour == 22 and ahora.minute == 20 and enviado_hoy != ahora.date():
            try:
                # Totales del día completo (sin filtro de apertura)
                r = _ur.urlopen("http://127.0.0.1:8000/reportes/hoy", timeout=5)
                datos = _json.loads(r.read().decode())
                desglose = datos.get("desglose_metodos", {})
                total    = float(datos.get("total_vendido", 0))
                tickets  = int(datos.get("tickets_hoy", 0))
                prom     = float(datos.get("ticket_promedio", 0))

                def _p(v): return f"${float(v):,.0f}"

                # Categorías del día completo
                r2 = _ur.urlopen("http://127.0.0.1:8000/reportes/por-categoria", timeout=5)
                cats = _json.loads(r2.read().decode())
                carne = next((c["total"] for c in cats if "carn" in c["categoria"].lower()), 0)
                fiamb = next((c["total"] for c in cats if "fiamb" in c["categoria"].lower()), 0)

                # Gastos del día completo
                r3 = _ur.urlopen("http://127.0.0.1:8000/gastos/hoy", timeout=5)
                datos_gastos = _json.loads(r3.read().decode())
                lista_gastos = datos_gastos.get("gastos", [])
                total_gastos = float(datos_gastos.get("total", 0))
                neto = total - total_gastos

                if lista_gastos:
                    lineas_gastos = "\n\n🧾 *Gastos del día:*"
                    for g in lista_gastos:
                        lineas_gastos += f"\n  • {g['descripcion']}: {_p(g['monto'])}"
                    lineas_gastos += f"\n  Total: {_p(total_gastos)}"
                else:
                    lineas_gastos = f"\n\n🧾 Gastos: {_p(0)}"

                ts = ahora.strftime("%d/%m/%Y")
                msg = (
                    f"📊 *RESUMEN DEL DÍA — JUANA CASH*\n"
                    f"📅 {ts}\n"
                    f"\n🎫 Tickets: {tickets}  |  Prom: {_p(prom)}"
                    f"\n{'─'*24}"
                    f"\n💵 Efectivo:    {_p(desglose.get('efectivo', 0))}"
                    f"\n🏧 Débito:      {_p(desglose.get('debito', 0))}"
                    f"\n💳 Tarjeta:     {_p(desglose.get('tarjeta', 0))}"
                    f"\n📱 QR/MP:       {_p(desglose.get('mercadopago_qr', 0))}"
                    f"\n🏦 Transfer.:   {_p(desglose.get('transferencia', 0))}"
                    f"\n💸 Fiado:       {_p(desglose.get('fiado', 0))}"
                    f"\n{'─'*24}"
                    f"\n📊 Total vendido: {_p(total)}"
                    f"\n📉 Gastos:        -{_p(total_gastos)}"
                    f"\n📈 *Neto del día:  {_p(neto)}*"
                    + lineas_gastos +
                    f"\n\n🥩 *Por departamento:*"
                    f"\n  Carnicería:   {_p(carne)}"
                    f"\n  Fiambrería:   {_p(fiamb)}"
                )
                for num in NUMEROS:
                    try:
                        payload = _json.dumps({"phone": num, "message": msg}).encode()
                        req = _ur.Request("http://127.0.0.1:3001/send",
                                          data=payload,
                                          headers={"Content-Type": "application/json"})
                        _ur.urlopen(req, timeout=5)
                    except Exception:
                        pass
                enviado_hoy = ahora.date()
            except Exception as e:
                try:
                    with open(os.path.join(DATA_DIR, "debug.log"), "a", encoding="utf-8") as f:
                        f.write(f"[{ahora}] ERROR reporte nocturno: {e}\n")
                except Exception:
                    pass
        time.sleep(30)

threading.Thread(target=run_backend, daemon=True).start()
threading.Thread(target=_udp_broadcaster, daemon=True).start()
threading.Thread(target=_auto_backup, daemon=True).start()
threading.Thread(target=_reporte_nocturno, daemon=True).start()
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
