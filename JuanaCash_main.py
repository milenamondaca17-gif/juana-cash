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

def _generar_y_enviar_reporte():
    """Genera y envía el reporte nocturno. Se puede llamar directamente o desde el loop."""
    import urllib.request as _ur
    import json as _json
    from datetime import datetime as _dt
    NUMEROS = ["2634670678", "2634633099", "2634633067"]
    ahora = _dt.now()
    try:
                def _p(v): return f"${float(v):,.0f}"

                # Turnos del día con desglose y pagos de empleados
                r_t = _ur.urlopen("http://127.0.0.1:8000/caja/turnos-hoy", timeout=5)
                turnos = _json.loads(r_t.read().decode())

                # Totales acumulados del día
                total_dia            = 0.0
                tickets_dia          = 0
                total_gastos_dia     = 0.0
                total_emp_dia        = 0.0
                cobros_fiado_ef_dia  = 0.0
                desglose_dia  = {"efectivo": 0.0, "debito": 0.0, "tarjeta": 0.0,
                                 "mercadopago_qr": 0.0, "transferencia": 0.0, "fiado": 0.0}

                bloques_turno = ""
                for i, t in enumerate(turnos, 1):
                    cajero   = t.get("cajero", "?")
                    estado   = "🟢 abierto" if t.get("estado") == "abierto" else "🔴 cerrado"
                    ap       = t.get("apertura", "")[-5:]  # HH:MM
                    ci       = t.get("cierre", "")[-5:] or "—"
                    tickets  = t.get("cantidad_ventas", 0)
                    vendido  = float(t.get("total_vendido", 0))
                    gastos_t = float(t.get("total_gastos", 0))
                    desg     = t.get("desglose", {})
                    emp_list = t.get("pagos_empleados", [])
                    total_emp_t = sum(float(e.get("monto", 0)) for e in emp_list)

                    for k in desglose_dia:
                        desglose_dia[k] += float(desg.get(k, 0))
                    total_dia           += vendido
                    tickets_dia         += tickets
                    total_gastos_dia    += gastos_t
                    total_emp_dia       += total_emp_t
                    cobros_fiado_ef_dia += sum(
                        float(cf.get("monto", 0)) for cf in t.get("cobros_fiado", [])
                        if cf.get("metodo", "efectivo") == "efectivo"
                    )

                    lineas_emp_t = ""
                    if emp_list:
                        lineas_emp_t = f"\n  👥 Empleados: " + " | ".join(
                            f"{e['nombre']} {_p(e['monto'])}" for e in emp_list
                        )

                    aportes_t = t.get("aportes", [])
                    _em_map = {"efectivo": "💵", "transferencia": "🏦",
                               "mercadopago_qr": "📱", "debito": "🏧"}
                    lineas_aportes_t = ""
                    if aportes_t:
                        lineas_aportes_t = "\n  💰 Aportes: " + " | ".join(
                            f"{_em_map.get(a.get('metodo','efectivo'),'💰')} {_p(a.get('monto',0))}"
                            for a in aportes_t
                        )

                    cobros_fiado_t = t.get("cobros_fiado", [])
                    lineas_cobros_t = ""
                    if cobros_fiado_t:
                        lineas_cobros_t = "\n  💳 Cobros fiado:"
                        for cf in cobros_fiado_t:
                            _met_cf = cf.get("metodo", "efectivo")
                            _em_cf = _em_map.get(_met_cf, "💰")
                            _dest_cf = "cajón" if _met_cf == "efectivo" else "banco"
                            _canc_cf = " ✅" if cf.get("cancelado") else ""
                            lineas_cobros_t += f"\n    {_em_cf} {cf.get('cliente','?')}: {_p(cf.get('monto',0))} →{_dest_cf}{_canc_cf}"

                    dep_carne_t = 0.0
                    dep_fiamb_t = 0.0
                    try:
                        _ap_full = t.get("apertura", "")
                        _ci_full = t.get("cierre", "") or ahora.strftime("%Y-%m-%dT%H:%M:%S")
                        if _ap_full:
                            _dep_url = (f"http://127.0.0.1:8000/reportes/departamentos"
                                        f"?desde={_ap_full}&hasta={_ci_full}")
                            _r_dep = _ur.urlopen(_dep_url, timeout=5)
                            _dep_data = _json.loads(_r_dep.read().decode())
                            dep_carne_t = float(_dep_data.get("carniceria", 0))
                            dep_fiamb_t = float(_dep_data.get("fiambreria", 0))
                    except Exception:
                        pass
                    lineas_deptos_t = ""
                    if dep_carne_t > 0 or dep_fiamb_t > 0:
                        lineas_deptos_t = f"\n  🥩 Carne: {_p(dep_carne_t)}  🧀 Fiamb: {_p(dep_fiamb_t)}"

                    bloques_turno += (
                        f"\n{'━'*22}"
                        f"\n*Turno {i} — {cajero}* {estado}"
                        f"\n⏰ {ap} → {ci}  |  🎫 {tickets} tickets"
                        f"\n💵 Efect: {_p(desg.get('efectivo',0))}"
                        f"  🏧 Déb: {_p(desg.get('debito',0))}"
                        f"\n💳 Tarj: {_p(desg.get('tarjeta',0))}"
                        f"  📱 QR: {_p(desg.get('mercadopago_qr',0))}"
                        f"\n💸 Fiado: {_p(desg.get('fiado',0))}"
                        f"  🏦 Trans: {_p(desg.get('transferencia',0))}"
                        f"\n📊 Total: {_p(vendido)}"
                        + (f"  |  🧾 Gastos: {_p(gastos_t)}" if gastos_t > 0 else "")
                        + lineas_emp_t
                        + lineas_aportes_t
                        + lineas_cobros_t
                        + lineas_deptos_t
                    )

                # Departamentos del día (solo hoy)
                _hoy_str = ahora.strftime("%Y-%m-%dT00:00:00")
                _ahora_str = ahora.strftime("%Y-%m-%dT%H:%M:%S")
                r2 = _ur.urlopen(
                    f"http://127.0.0.1:8000/reportes/departamentos?desde={_hoy_str}&hasta={_ahora_str}",
                    timeout=5)
                deptos = _json.loads(r2.read().decode())
                carne = deptos.get("carniceria", 0)
                fiamb = deptos.get("fiambreria", 0)

                # Gastos del día (lista detallada)
                r3 = _ur.urlopen("http://127.0.0.1:8000/gastos/hoy", timeout=5)
                datos_gastos = _json.loads(r3.read().decode())
                lista_gastos = datos_gastos.get("gastos", [])
                if lista_gastos:
                    lineas_gastos = "\n\n🧾 *Gastos:*"
                    for g in lista_gastos:
                        lineas_gastos += f"\n  • {g['descripcion']}: {_p(g['monto'])}"
                else:
                    lineas_gastos = ""

                prom_dia = (total_dia / tickets_dia) if tickets_dia > 0 else 0
                neto_dia = total_dia - total_gastos_dia - total_emp_dia
                balance_ef = desglose_dia['efectivo'] + cobros_fiado_ef_dia - total_emp_dia - total_gastos_dia

                ts = ahora.strftime("%d/%m/%Y")
                msg = (
                    f"📊 *RESUMEN DEL DÍA — JUANA CASH*\n"
                    f"📅 {ts}  |  🎫 {tickets_dia} tickets  |  Prom: {_p(prom_dia)}"
                    f"\n{'━'*22}"
                    f"\n💵 Efectivo:   {_p(desglose_dia['efectivo'])}"
                    f"\n🏧 Débito:     {_p(desglose_dia['debito'])}"
                    f"\n💳 Tarjeta:    {_p(desglose_dia['tarjeta'])}"
                    f"\n📱 QR/MP:      {_p(desglose_dia['mercadopago_qr'])}"
                    f"\n🏦 Transfer.:  {_p(desglose_dia['transferencia'])}"
                    f"\n💸 Fiado:      {_p(desglose_dia['fiado'])}"
                    f"\n{'─'*22}"
                    f"\n📊 Total vendido:     {_p(total_dia)}"
                    + (f"\n👥 Empleados:        -{_p(total_emp_dia)}" if total_emp_dia > 0 else "")
                    + (f"\n🧾 Gastos:           -{_p(total_gastos_dia)}" if total_gastos_dia > 0 else "")
                    + (f"\n💳 Cobros fiado ef.: +{_p(cobros_fiado_ef_dia)}" if cobros_fiado_ef_dia > 0 else "")
                    + f"\n📈 *Neto del día:     {_p(neto_dia)}*"
                    f"\n💵 *Balance efectivo: {_p(balance_ef)}*"
                    f"\n🥩 Carnicería: {_p(carne)}  🧀 Fiamb: {_p(fiamb)}"
                    + lineas_gastos
                    + f"\n{'━'*22}"
                    f"\n📋 *DETALLE POR TURNO*"
                    + bloques_turno
                )
                _log_r = os.path.join(DATA_DIR, "reporte_nocturno.log")
                enviados = 0
                for num in NUMEROS:
                    try:
                        payload = _json.dumps({"phone": num, "message": msg}).encode()
                        req = _ur.Request("http://127.0.0.1:3001/send",
                                          data=payload,
                                          headers={"Content-Type": "application/json"})
                        _ur.urlopen(req, timeout=5)
                        enviados += 1
                    except Exception as _we:
                        try:
                            with open(_log_r, "a", encoding="utf-8") as _lf:
                                _lf.write(f"[{ahora}] ERROR enviando a {num}: {_we}\n")
                        except Exception:
                            pass
                try:
                    with open(_log_r, "a", encoding="utf-8") as _lf:
                        _lf.write(f"[{ahora}] Reporte enviado a {enviados}/{len(NUMEROS)} numeros. Total dia: ${total_dia:,.0f}\n")
                except Exception:
                    pass
    except Exception as e:
        try:
            import traceback as _tb2
            with open(os.path.join(DATA_DIR, "reporte_nocturno.log"), "a", encoding="utf-8") as f:
                f.write(f"[{ahora}] ERROR reporte nocturno: {e}\n{_tb2.format_exc()}\n")
        except Exception:
            pass

def _reporte_nocturno():
    """A las 22:20 llama a _generar_y_enviar_reporte()."""
    from datetime import datetime as _dt
    enviado_hoy = None
    while True:
        ahora = _dt.now()
        if ahora.hour == 22 and ahora.minute == 20 and enviado_hoy != ahora.date():
            _generar_y_enviar_reporte()
            enviado_hoy = ahora.date()
        time.sleep(30)

def _reporte_semanal():
    """Los lunes a las 9:00 envía el resumen de la semana anterior a los 3 números."""
    import urllib.request as _ur
    import json as _json
    from datetime import datetime as _dt, timedelta as _td
    NUMEROS = ["2634670678", "2634633099", "2634633067"]
    enviado_semana = None
    while True:
        ahora = _dt.now()
        # weekday() 0 = lunes
        if ahora.weekday() == 0 and ahora.hour == 9 and ahora.minute == 0 and enviado_semana != ahora.date():
            try:
                hoy = ahora.date()
                lunes_esta = hoy - _td(days=hoy.weekday())
                dom_ant    = lunes_esta - _td(days=1)
                lun_ant    = dom_ant   - _td(days=6)
                desde = lun_ant.isoformat()
                hasta = dom_ant.isoformat()

                r = _ur.urlopen(f"http://127.0.0.1:8000/reportes/rango?desde={desde}&hasta={hasta}", timeout=5)
                datos = _json.loads(r.read().decode())
                total   = float(datos.get("total_vendido", 0))
                tickets = int(datos.get("cantidad_ventas", 0))
                prom    = (total / tickets) if tickets > 0 else 0

                desglose = {}
                for v in datos.get("ventas", []):
                    if v.get("estado") != "completada":
                        continue
                    m = v.get("metodo_pago", "efectivo")
                    desglose[m] = desglose.get(m, 0.0) + float(v["total"])

                # Semana anterior para comparar
                lun_ante2 = lun_ant - _td(days=7)
                dom_ante2 = lun_ant - _td(days=1)
                r2 = _ur.urlopen(f"http://127.0.0.1:8000/reportes/rango?desde={lun_ante2}&hasta={dom_ante2}", timeout=5)
                datos2 = _json.loads(r2.read().decode())
                total_ant = float(datos2.get("total_vendido", 0))
                variacion = ((total - total_ant) / total_ant * 100) if total_ant > 0 else 0
                flecha = "↑" if variacion >= 0 else "↓"
                color_var = f"({flecha} {abs(variacion):.1f}% vs sem. anterior)"

                def _p(v): return f"${float(v):,.0f}"

                msg = (
                    f"📅 *RESUMEN SEMANAL — JUANA CASH*\n"
                    f"🗓 {lun_ant.strftime('%d/%m')} al {dom_ant.strftime('%d/%m/%Y')}\n"
                    f"\n🎫 Tickets: {tickets}  |  Prom: {_p(prom)}"
                    f"\n{'─'*24}"
                    f"\n💵 Efectivo:    {_p(desglose.get('efectivo', 0))}"
                    f"\n🏧 Débito:      {_p(desglose.get('debito', 0))}"
                    f"\n💳 Tarjeta:     {_p(desglose.get('tarjeta', 0))}"
                    f"\n📱 QR/MP:       {_p(desglose.get('mercadopago_qr', 0))}"
                    f"\n🏦 Transfer.:   {_p(desglose.get('transferencia', 0))}"
                    f"\n💸 Fiado:       {_p(desglose.get('fiado', 0))}"
                    f"\n{'─'*24}"
                    f"\n📊 *Total semana: {_p(total)}*"
                    f"\n{color_var}"
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
                enviado_semana = ahora.date()
            except Exception as e:
                try:
                    with open(os.path.join(DATA_DIR, "debug.log"), "a", encoding="utf-8") as f:
                        f.write(f"[{ahora}] ERROR reporte semanal: {e}\n")
                except Exception:
                    pass
        time.sleep(30)

# ── Modo --solo-reporte: arranca el backend, envía el reporte y cierra ────────
if '--solo-reporte' in sys.argv:
    threading.Thread(target=run_backend, daemon=True).start()
    time.sleep(5)  # esperar que el backend esté listo
    _generar_y_enviar_reporte()
    time.sleep(2)
    sys.exit(0)
# ─────────────────────────────────────────────────────────────────────────────

threading.Thread(target=run_backend, daemon=True).start()
threading.Thread(target=_udp_broadcaster, daemon=True).start()
threading.Thread(target=_auto_backup, daemon=True).start()
threading.Thread(target=_reporte_nocturno, daemon=True).start()
threading.Thread(target=_reporte_semanal, daemon=True).start()
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
