import flet as ft
import requests
import threading
import json
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

def _p(v):
    """Precio en formato argentino: $10.000"""
    return f"${float(v):,.0f}".replace(",", ".")

APP_VERSION = "3.4.7"
APK_URL     = "https://github.com/milenamondaca17-gif/juana-cash/releases/latest/download/JuanaCash.apk"
VERSION_URL = "https://raw.githubusercontent.com/milenamondaca17-gif/juana-cash/main/version.json"

def _version_mayor(v1, v2):
    """True si v1 > v2 (formato X.Y.Z)"""
    try:
        return tuple(int(x) for x in v1.split(".")) > tuple(int(x) for x in v2.split("."))
    except Exception:
        return False

# ─── Configuración de IP ──────────────────────────────────────────────────────
CONFIG_PATH   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mobile_config.json")
OFFLINE_PATH  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ventas_offline.json")
TAILSCALE_IP  = "100.72.212.67"

def leer_config():
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH) as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def guardar_config_data(data):
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        cfg = leer_config()
        cfg.update(data)
        with open(CONFIG_PATH, "w") as f:
            json.dump(cfg, f)
    except Exception:
        pass

def leer_ip():
    return leer_config().get("ip", TAILSCALE_IP)

def guardar_ip(ip):
    guardar_config_data({"ip": ip})

def leer_pin_precios():
    return leer_config().get("pin_precios", "1722")

UDP_PORT = 55555

def _puerto_abierto(ip, timeout=0.5):
    """TCP connect al puerto 8000 — mucho más rápido que una petición HTTP."""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        resultado = s.connect_ex((ip, 8000))
        s.close()
        return resultado == 0
    except Exception:
        return False

def _probar_ip(ip, timeout=2):
    """Verifica que el servidor en esa IP sea el backend de Juana Cash."""
    try:
        r = requests.get(f"http://{ip}:8000/", timeout=timeout)
        if r.status_code != 200:
            return False
        data = r.json()
        return "Juana" in str(data) or "juana" in str(data).lower()
    except Exception:
        return False

def _escuchar_broadcast(timeout=6):
    """
    Escucha el broadcast UDP que emite el backend de la PC cada 2 s.
    Retorna la IP encontrada o None si no hubo señal.
    """
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.settimeout(timeout)
        s.bind(("", UDP_PORT))
        data, addr = s.recvfrom(512)
        s.close()
        info = json.loads(data.decode())
        if info.get("service") == "JuanaCash":
            return info.get("ip", addr[0])
    except Exception:
        pass
    return None

def _obtener_red_local():
    """Devuelve el prefijo /24 de la red local (ej: '192.168.1')."""
    import socket
    intentos = [
        ("8.8.8.8", 80),
        ("1.1.1.1", 80),
        ("192.168.1.1", 80),
    ]
    for host, port in intentos:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(1)
            s.connect((host, port))
            ip = s.getsockname()[0]
            s.close()
            if ip and not ip.startswith("127.") and not ip.startswith("169."):
                return ip.rsplit(".", 1)[0]
        except Exception:
            pass
    return None

# IP activa en memoria
_ip_activa = {"ip": leer_ip()}

def get_api_url():
    return f"http://{_ip_activa['ip']}:8000"

def detectar_mejor_ip(callback_progreso=None):
    """
    Tres estrategias en paralelo, gana la más rápida:
    1. UDP broadcast  — el backend anuncia su IP cada 2 s (instantáneo)
    2. IP guardada    — verificación rápida de la última IP conocida
    3. Escaneo TCP    — prueba puerto 8000 en toda la /24 (fallback)
    Tailscale como último recurso.
    """
    ip_guardada = leer_ip()
    resultado   = [None]
    encontrado  = threading.Event()
    lock        = threading.Lock()

    def _set_result(ip):
        with lock:
            if resultado[0] is None:
                resultado[0] = ip
        encontrado.set()

    def _via_broadcast():
        if callback_progreso:
            callback_progreso("📡 Escuchando broadcast de la PC...")
        ip = _escuchar_broadcast(timeout=7)
        if ip and not encontrado.is_set():
            _set_result(ip)

    def _via_guardada():
        if callback_progreso:
            callback_progreso(f"🔍 Probando {ip_guardada}...")
        if _probar_ip(ip_guardada, 2) and not encontrado.is_set():
            _set_result(ip_guardada)

    def _via_escaneo():
        red = _obtener_red_local()
        if not red:
            return
        if callback_progreso:
            callback_progreso(f"🔎 Escaneando red {red}.x...")
        stop_ev = threading.Event()

        def _probar_tcp(ip):
            if stop_ev.is_set() or encontrado.is_set():
                return
            if _puerto_abierto(ip, 0.4) and _probar_ip(ip, 1.5):
                if not encontrado.is_set():
                    stop_ev.set()
                    _set_result(ip)

        with ThreadPoolExecutor(max_workers=80) as ex:
            candidatos = [f"{red}.{i}" for i in range(1, 255)]
            futs = [ex.submit(_probar_tcp, ip) for ip in candidatos]
            encontrado.wait(timeout=12)
            for f in futs:
                f.cancel()

    # Lanzar las tres estrategias en paralelo
    hilos = [
        threading.Thread(target=_via_broadcast, daemon=True),
        threading.Thread(target=_via_guardada,  daemon=True),
        threading.Thread(target=_via_escaneo,   daemon=True),
    ]
    for h in hilos:
        h.start()

    encontrado.wait(timeout=13)

    if resultado[0]:
        guardar_ip(resultado[0])
        _ip_activa["ip"] = resultado[0]
        return resultado[0]

    # Fallback Tailscale
    if callback_progreso:
        callback_progreso("🌐 Probando Tailscale VPN...")
    if _probar_ip(TAILSCALE_IP, 3):
        _ip_activa["ip"] = TAILSCALE_IP
        return TAILSCALE_IP

    # Sin conexión — mantener última IP conocida
    _ip_activa["ip"] = ip_guardada
    return ip_guardada

def _autoconectar_en_hilo():
    threading.Thread(target=detectar_mejor_ip, daemon=True).start()

# ── Offline ───────────────────────────────────────────────────────────────────
def _leer_offline():
    try:
        with open(OFFLINE_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return []

def _guardar_offline(ventas):
    try:
        with open(OFFLINE_PATH, "w") as f:
            json.dump(ventas, f)
    except Exception:
        pass

def _agregar_venta_offline(venta_data):
    ventas = _leer_offline()
    venta_data["_offline_ts"] = datetime.now().isoformat()
    ventas.append(venta_data)
    _guardar_offline(ventas)

def _contar_pendientes():
    return len(_leer_offline())

def _sincronizar_offline():
    ventas = _leer_offline()
    if not ventas:
        return 0
    ok, resto = 0, []
    for v in ventas:
        data = {k: val for k, val in v.items() if not k.startswith("_")}
        try:
            r = requests.post(f"{get_api_url()}/ventas/", json=data, timeout=8)
            if r.status_code == 200:
                ok += 1
            else:
                resto.append(v)
        except Exception:
            resto.append(v)
    _guardar_offline(resto)
    return ok

# ─── API helpers ──────────────────────────────────────────────────────────────
def en_hilo(func):
    def wrapper(*args, **kwargs):
        threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True).start()
    return wrapper

def api_get(path, params=None, timeout=5):
    try:
        r = requests.get(f"{get_api_url()}{path}", params=params, timeout=timeout)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None

def api_post(path, json_data=None, timeout=8):
    try:
        r = requests.post(f"{get_api_url()}{path}", json=json_data, timeout=timeout)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None

def api_delete(path, timeout=5):
    try:
        r = requests.delete(f"{get_api_url()}{path}", timeout=timeout)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None

def api_put(path, json_data=None, timeout=8):
    try:
        r = requests.put(f"{get_api_url()}{path}", json=json_data, timeout=timeout)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None

# ─── APP PRINCIPAL ────────────────────────────────────────────────────────────
def main(page: ft.Page):
    import traceback
    try:
        _main(page)
    except Exception as _e:
        page.controls.clear()
        page.bgcolor = "#080E1C"
        page.add(ft.Container(
            content=ft.Column([
                ft.Text("ERROR AL INICIAR", size=18, weight="bold", color="#EF4444"),
                ft.Text(str(_e), size=13, color="white", selectable=True),
                ft.Divider(color="#1E293B"),
                ft.Text(traceback.format_exc(), size=10, color="#94A3B8", selectable=True),
            ], scroll=ft.ScrollMode.ALWAYS, spacing=10),
            padding=20, expand=True
        ))
        page.update()

def _main(page: ft.Page):
    import time

    page.title      = "Juana Cash"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor    = "#080E1C"
    page.padding    = 0
    page.spacing    = 0

    # ── SPLASH ───────────────────────────────────────────────────────────────
    progress_bar = ft.ProgressBar(value=0, expand=True, height=5,
                                  color="#27AE60", bgcolor="#0d1f35")
    lbl_pct    = ft.Text("0%", size=13, weight="bold", color="#1B9FD4", text_align="center")
    lbl_estado = ft.Text("Iniciando...", size=11, color="#4a7a9a", text_align="center")

    page.add(ft.Container(
        content=ft.Column([
            ft.Container(expand=True),
            ft.Image(src="/assets/splash.png", width=260, fit="contain"),
            ft.Container(height=18),
            progress_bar,
            ft.Container(height=10),
            ft.Row([lbl_pct], alignment="center"),
            ft.Container(height=4),
            ft.Row([lbl_estado], alignment="center"),
            ft.Container(expand=True),
            ft.Text("CAMMUS_25  //  DIGITAL CREATOR", size=9, color="#2a4a6a", text_align="center"),
            ft.Container(height=20),
        ], horizontal_alignment="center", spacing=0),
        bgcolor="#080E1C", expand=True, padding=40
    ))
    page.update()

    for valor, texto in [
        (0.10, "Verificando configuración..."),
        (0.25, "Conectando sistema..."),
        (0.45, "Cargando productos..."),
        (0.65, "Preparando interfaz..."),
        (0.85, "Verificando conexión..."),
        (1.00, "¡Sistema listo!"),
    ]:
        time.sleep(0.28)
        progress_bar.value = valor
        lbl_pct.value = f"{int(valor*100)}%"
        lbl_estado.value = texto
        if valor == 1.0:
            lbl_estado.color = "#27AE60"
        page.update()

    time.sleep(0.5)
    page.controls.clear()
    page.bgcolor = "#0B1120"
    page.update()
    # ── FIN SPLASH ────────────────────────────────────────────────────────────

    carrito        = []
    tickets_espera = []
    productos_cache  = []
    productos_codigo = {}

    lbl_oferta_status = ft.Text("", size=13, weight="bold")

    @en_hilo
    def cargar_cache_productos(e=None):
        data = api_get("/productos/")
        if data:
            productos_cache.clear()
            productos_cache.extend(data)
            productos_codigo.clear()
            productos_codigo.update({
                str(p["codigo_barra"]): p
                for p in data if p.get("codigo_barra")
            })

    def abrir_dlg(dlg):
        if hasattr(page, "open"):
            page.open(dlg)
        else:
            page.dialog = dlg
            dlg.open = True
            page.update()

    def cerrar_dlg(dlg):
        if hasattr(page, "close"):
            page.close(dlg)
        else:
            dlg.open = False
            page.update()

    # ── Barra superior ────────────────────────────────────────────────────────
    lbl_ip_status = ft.Text("", size=11, color="#94A3B8")
    app_bar = ft.Container(
        content=ft.Row([
            ft.Text("JUANA CASH", weight="w900", size=20, color="#F43F5E"),
            ft.Container(expand=True),
            lbl_ip_status,
        ], alignment="spaceBetween"),
        padding=ft.padding.symmetric(horizontal=16, vertical=12),
        bgcolor="#0F172A"
    )

    def inp(label, hint="", w=None, kb="text"):
        return ft.TextField(
            label=label, hint_text=hint, width=w,
            filled=True, border_color="transparent",
            border_radius=12, content_padding=16,
            bgcolor="#1E293B", keyboard_type=kb
        )

    # ── PANTALLA 1: DASHBOARD ─────────────────────────────────────────────────
    lbl_total    = ft.Text("$0", size=44, weight="w900", color="#10B981")
    lbl_tickets  = ft.Text("0 tickets hoy", size=14, color="#94A3B8")
    lbl_mes      = ft.Text("", size=13, color="#94A3B8")
    lbl_metodo   = ft.Text("", size=12, color="#38BDF8")
    lbl_top_prod = ft.Text("", size=12, color="#F59E0B")
    lbl_offline_badge = ft.Text("", size=12, color="#F59E0B")

    @en_hilo
    def sincronizar_manual(e=None):
        n = _contar_pendientes()
        if n == 0:
            lbl_offline_badge.value = "✅ Sin ventas pendientes"
            lbl_offline_badge.color = "#10B981"
            page.update()
            return
        lbl_offline_badge.value = f"⏳ Sincronizando {n} venta(s)..."
        lbl_offline_badge.color = "#94A3B8"
        page.update()
        ok    = _sincronizar_offline()
        resto = _contar_pendientes()
        if resto == 0:
            lbl_offline_badge.value = f"✅ {ok} venta(s) sincronizadas!"
            lbl_offline_badge.color = "#10B981"
        else:
            lbl_offline_badge.value = f"⚠️ {ok} OK, {resto} aún pendientes"
            lbl_offline_badge.color = "#F59E0B"
        page.update()

    def _actualizar_badge():
        n = _contar_pendientes()
        if n > 0:
            lbl_offline_badge.value = f"📴 {n} venta{'s' if n!=1 else ''} offline — tocá para sincronizar"
            lbl_offline_badge.color = "#F59E0B"
        else:
            lbl_offline_badge.value = ""
        page.update()

    lista_movs        = ft.Column(spacing=8, scroll=ft.ScrollMode.ALWAYS, height=200)
    lbl_dashboard_err = ft.Text("", color="#EF4444", size=12)

    @en_hilo
    def cargar_dashboard(e=None):
        _ip_activa["ip"] = detectar_mejor_ip()
        lbl_ip_status.value = f"📡 {_ip_activa['ip']}"
        data     = api_get("/reportes/hoy")
        data_mes = api_get("/reportes/mes")
        if data:
            lbl_total.value   = _p(data.get('total_vendido', 0))
            lbl_total.color   = "#10B981"
            cant = data.get("cantidad_ventas", 0)
            lbl_tickets.value = f"{cant} ticket{'s' if cant != 1 else ''} hoy"
            lbl_dashboard_err.value = ""
            ventas  = data.get("ventas", [])
            metodos = {}
            for v in ventas:
                m = v.get("metodo_pago", "efectivo")
                metodos[m] = metodos.get(m, 0) + 1
            if metodos:
                top_m = max(metodos, key=metodos.get)
                nombres_m = {
                    "efectivo": "💵 Efectivo", "tarjeta": "💳 Tarjeta",
                    "mercadopago_qr": "📱 QR/MP", "transferencia": "🏦 Transf.",
                    "fiado": "💸 Fiado"
                }
                lbl_metodo.value = f"Más usado: {nombres_m.get(top_m, top_m)}"
            top_prods = data.get("top_productos", [])
            if top_prods:
                lbl_top_prod.value = f"🏆 {top_prods[0].get('nombre', '?')}"
            lista_movs.controls.clear()
            for v in ventas[:10]:
                metodo = v.get("metodo_pago", "efectivo").upper()
                total  = float(v.get("total", 0))
                estado = v.get("estado", "")
                color  = "#EF4444" if estado == "anulada" else "#38BDF8"
                lista_movs.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text("🛍️", size=16),
                            ft.Text(metodo, weight="bold", expand=True, size=12),
                            ft.Text(_p(total), weight="bold", color=color, size=14),
                        ]),
                        bgcolor="#1E293B", padding=10, border_radius=10
                    )
                )
        else:
            lbl_total.value   = "Sin conexión"
            lbl_total.color   = "#EF4444"
            lbl_dashboard_err.value = f"No se pudo conectar a {get_api_url()}"
        if data_mes:
            lbl_mes.value = f"Este mes: {_p(data_mes.get('total_vendido', 0))}"
        page.update()

    view_dashboard = ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Text("CAJA DEL DÍA", weight="bold", color="#94A3B8", size=12),
                    lbl_total, lbl_tickets,
                    ft.Row([lbl_mes, lbl_metodo], alignment="spaceBetween"),
                    lbl_top_prod,
                    lbl_dashboard_err,
                ], horizontal_alignment="center"),
                padding=16, border_radius=16, bgcolor="#0F172A"
            ),
            ft.GestureDetector(
                content=ft.Container(
                    content=lbl_offline_badge,
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    border_radius=8, bgcolor="#1E293B",
                ),
                on_tap=sincronizar_manual,
            ),
            ft.Text("Últimos movimientos", weight="w600", size=15),
            lista_movs,
            ft.ElevatedButton(
                "🔄 ACTUALIZAR", on_click=cargar_dashboard,
                expand=True, height=48,
                bgcolor="#3B82F6", color="white",
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
            )
        ], spacing=12),
        padding=16, visible=True, expand=True
    )

    # ── PANTALLA 2: COBRAR ────────────────────────────────────────────────────
    lbl_aviso    = ft.Text("", size=13, weight="bold")
    lista_compra = ft.Column(spacing=8, scroll=ft.ScrollMode.ALWAYS, height=160)
    lbl_total_c  = ft.Text("$0", size=34, weight="w900", color="#F43F5E")
    in_scan = ft.TextField(
        label="Escanear o buscar...", filled=True, border_color="transparent",
        border_radius=12, content_padding=16, bgcolor="#1E293B", expand=True
    )
    in_cliente  = inp("Cliente (opcional)", w=160)
    drop_metodo = ft.Dropdown(
        options=[
            ft.dropdown.Option(key="efectivo",       text="💵 Efectivo"),
            ft.dropdown.Option(key="tarjeta",        text="💳 Tarjeta"),
            ft.dropdown.Option(key="mercadopago_qr", text="📱 QR/MP"),
            ft.dropdown.Option(key="transferencia",  text="🏦 Transf."),
            ft.dropdown.Option(key="fiado",          text="💸 Fiado"),
        ],
        value="efectivo", width=150, border_radius=10,
        filled=True, bgcolor="#1E293B", border_color="transparent"
    )

    cliente_fiado     = {"id": None, "nombre": ""}
    lbl_cliente_fiado = ft.Text("", size=12, color="#F59E0B")
    panel_buscar_cliente = ft.Container(visible=False)

    btn_vincular_fiado = ft.ElevatedButton(
        "👤 Vincular cliente para Fiado", bgcolor="#F59E0B", color="black",
        expand=True, height=44, visible=False,
        on_click=lambda e: (
            setattr(panel_buscar_cliente, "visible", not panel_buscar_cliente.visible),
            page.update()
        )
    )

    def on_metodo_change(e):
        if drop_metodo.value == "fiado":
            panel_buscar_cliente.visible = True
            btn_vincular_fiado.visible   = True
        else:
            panel_buscar_cliente.visible = False
            btn_vincular_fiado.visible   = False
            cliente_fiado["id"]          = None
            cliente_fiado["nombre"]      = ""
            lbl_cliente_fiado.value      = ""
        page.update()

    drop_metodo.on_change = on_metodo_change

    lista_clientes = ft.Column(spacing=4, scroll=ft.ScrollMode.ALWAYS, height=120)

    def seleccionar_cliente(c):
        cliente_fiado["id"]     = c["id"]
        cliente_fiado["nombre"] = c.get("nombre", "")
        lbl_cliente_fiado.value = f"✅ Cliente: {cliente_fiado['nombre']}"
        lista_clientes.controls.clear()
        in_buscar_cliente.value = ""
        page.update()

    def buscar_cliente(e=None):
        q = in_buscar_cliente.value.strip()
        if not q:
            return

        def _buscar():
            data = api_get("/clientes/", params={"q": q}, timeout=8)
            if not data:
                data = api_get("/clientes/", timeout=8)
                if data:
                    q_lower = q.lower()
                    data = [c for c in data if q_lower in c.get("nombre", "").lower()]
            lista_clientes.controls.clear()
            if data:
                for c in data[:10]:
                    nombre = c.get("nombre", "")
                    deuda  = float(c.get("deuda_actual") or 0)
                    txt    = nombre + (f"  💸 debe {_p(deuda)}" if deuda > 0 else "")
                    lista_clientes.controls.append(
                        ft.Container(
                            content=ft.Text(txt, expand=True, size=12, color="white"),
                            bgcolor="#1E293B", padding=10, border_radius=8,
                            on_click=lambda e, cl=c: seleccionar_cliente(cl),
                        )
                    )
            else:
                lista_clientes.controls.append(
                    ft.Text("Sin resultados", color="#94A3B8", size=12)
                )
            page.update()

        threading.Thread(target=_buscar, daemon=True).start()

    in_buscar_cliente = ft.TextField(
        label="Buscar cliente por nombre",
        filled=True, border_color="transparent", border_radius=10,
        content_padding=12, bgcolor="#1E293B", expand=True,
        on_submit=buscar_cliente
    )

    panel_buscar_cliente.content = ft.Column([
        ft.Row([
            in_buscar_cliente,
            ft.ElevatedButton("🔍", on_click=buscar_cliente,
                bgcolor="#556EE6", color="white", height=44, width=50)
        ]),
        lbl_cliente_fiado,
        lista_clientes,
    ], spacing=6)
    panel_buscar_cliente.bgcolor       = "#0F172A"
    panel_buscar_cliente.border_radius = 10
    panel_buscar_cliente.padding       = 10

    btn_recuperar = ft.ElevatedButton(
        "⏳ (0)", bgcolor="#334155", color="white", visible=False
    )

    def recalc():
        t = sum(i["p"] for i in carrito)
        lbl_total_c.value = _p(t)
        page.update()

    def pausar(e):
        if not carrito:
            return
        nom = in_cliente.value.strip() or f"Cliente {len(tickets_espera)+1}"
        tickets_espera.append({"nombre": nom, "items": list(carrito)})
        carrito.clear()
        lista_compra.controls.clear()
        in_cliente.value      = ""
        btn_recuperar.text    = f"⏳ ({len(tickets_espera)})"
        btn_recuperar.visible = True
        lbl_aviso.value = f"Pausado: {nom}"
        lbl_aviso.color = "#F59E0B"
        recalc()

    dlg_pausados = ft.AlertDialog(modal=True)

    def cargar_pausado(t):
        carrito.clear()
        lista_compra.controls.clear()
        carrito.extend(t["items"])
        for i in carrito:
            agregar_ui(i)
        tickets_espera.remove(t)
        btn_recuperar.text    = f"⏳ ({len(tickets_espera)})"
        btn_recuperar.visible = len(tickets_espera) > 0
        cerrar_dlg(dlg_pausados)
        recalc()

    def ver_pausados(e):
        if not tickets_espera:
            return
        cols = [
            ft.ElevatedButton(
                f"🛒 {t['nombre']} ({len(t['items'])} prod)",
                on_click=lambda ev, tk=t: cargar_pausado(tk),
                height=48, width=260, bgcolor="#1E293B", color="white"
            ) for t in tickets_espera
        ]
        dlg_pausados.content = ft.Column(cols, tight=True)
        dlg_pausados.title   = ft.Text("Ventas pausadas")
        dlg_pausados.actions = [
            ft.TextButton("Cerrar", on_click=lambda ev: cerrar_dlg(dlg_pausados))
        ]
        abrir_dlg(dlg_pausados)

    btn_recuperar.on_click = ver_pausados

    def setval(d, k, v):
        d[k] = v

    def agregar_ui(data):
        data.setdefault("cant", 1)
        data.setdefault("precio_unit", data["p"])

        lbl_cant = ft.Text(f"x{data['cant']}", width=28, text_align="center",
                           weight="bold", size=13, color="#F1B44C")
        in_p = ft.TextField(
            value=f"{data['p']:.0f}", width=80, text_align="right",
            bgcolor="#0F172A", border_color="transparent",
            filled=True, border_radius=8, content_padding=4,
            on_change=lambda e: (setval(data, "p", float(e.control.value or 0)), recalc())
        )

        def cambiar_cant(delta):
            nueva = max(1, data["cant"] + delta)
            data["cant"] = nueva
            data["p"]    = round(data["precio_unit"] * nueva, 2)
            lbl_cant.value = f"x{nueva}"
            in_p.value     = f"{data['p']:.0f}"
            recalc()

        fila = ft.Container(
            content=ft.Row([
                ft.ElevatedButton("❌",
                    on_click=lambda _, d=data: (
                        carrito.remove(d),
                        lista_compra.controls.remove(fila),
                        recalc()
                    ),
                    bgcolor="#EF4444", color="white", width=38, height=36),
                ft.Text(data["n"], expand=True, size=11, weight="bold"),
                ft.ElevatedButton("-",
                    on_click=lambda _: cambiar_cant(-1),
                    bgcolor="#334155", color="white", width=34, height=34),
                lbl_cant,
                ft.ElevatedButton("+",
                    on_click=lambda _: cambiar_cant(1),
                    bgcolor="#10B981", color="white", width=34, height=34),
                in_p,
            ], spacing=4),
            bgcolor="#1E293B", padding=8, border_radius=12
        )
        lista_compra.controls.append(fila)

    panel_resultados = ft.Container(visible=False)

    def ocultar_resultados():
        panel_resultados.visible = False
        panel_resultados.content = None
        page.update()

    def buscar_prod(e=None):
        v = in_scan.value.strip()
        if not v:
            ocultar_resultados()
            return
        lbl_aviso.value = "🔍..."
        lbl_aviso.color = "#94A3B8"
        page.update()

        def _buscar():
            matches = []
            if productos_cache:
                if v in productos_codigo:
                    matches = [productos_codigo[v]]
                else:
                    v_lower = v.lower()
                    matches = [x for x in productos_cache if v_lower in x["nombre"].lower()]
            if not matches:
                data = api_get("/productos/buscar", params={"q": v}, timeout=8)
                if data:
                    matches = data

            if not matches:
                lbl_aviso.value = f"❌ '{v}' no encontrado"
                lbl_aviso.color = "#EF4444"
                page.update()
                return

            if len(matches) == 1:
                p   = matches[0]
                dat = {"n": p["nombre"], "p": float(p.get("precio_venta") or 0), "producto_id": p["id"]}
                carrito.append(dat)
                agregar_ui(dat)
                in_scan.value = ""
                lbl_aviso.value = ""
                ocultar_resultados()
                recalc()
                return

            def seleccionar(prod):
                dat = {"n": prod["nombre"], "p": float(prod.get("precio_venta") or 0), "producto_id": prod["id"]}
                carrito.append(dat)
                agregar_ui(dat)
                in_scan.value = ""
                lbl_aviso.value = ""
                ocultar_resultados()
                recalc()

            filas = [
                ft.Container(
                    content=ft.Row([
                        ft.Text(p["nombre"], expand=True, size=12, weight="bold", color="white"),
                        ft.Text(_p(p.get('precio_venta') or 0),
                               color="#38BDF8", size=13, weight="bold"),
                    ]),
                    bgcolor="#1E293B",
                    padding=ft.padding.symmetric(horizontal=12, vertical=10),
                    border_radius=8,
                    on_click=lambda e, prod=p: seleccionar(prod),
                )
                for p in matches[:15]
            ]
            filas.append(ft.TextButton("✕ Cancelar", on_click=lambda e: ocultar_resultados()))

            panel_resultados.content      = ft.Column(
                controls=filas, scroll=ft.ScrollMode.ALWAYS,
                spacing=4, height=min(len(matches) * 50, 300)
            )
            panel_resultados.bgcolor       = "#0F172A"
            panel_resultados.border_radius = 10
            panel_resultados.padding       = 8
            panel_resultados.visible       = True
            lbl_aviso.value = f"🔍 {len(matches)} resultados — tocá para agregar"
            lbl_aviso.color = "#94A3B8"
            page.update()

        threading.Thread(target=_buscar, daemon=True).start()

    in_scan.on_submit = buscar_prod

    btn_cobrar = ft.ElevatedButton(
        "🧾 COBRAR", expand=True, height=58,
        bgcolor="#F43F5E", color="white",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=14)),
        on_click=lambda e: ir_ticket()
    )

    btn_ir_fiados = ft.ElevatedButton(
        "💸 COBRAR FIADO", expand=True, height=44,
        bgcolor="#1E293B", color="#EF4444",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
        on_click=lambda e: _ir_fiados()
    )

    view_cobrar = ft.Container(
        content=ft.Column([
            ft.Column([
                lbl_aviso,
                ft.Row([in_cliente,
                        ft.ElevatedButton("⏸️", on_click=pausar, bgcolor="#F59E0B", color="black"),
                        btn_recuperar]),
                ft.Row([in_scan,
                        ft.ElevatedButton("➕", on_click=buscar_prod, bgcolor="#10B981", color="white", height=48)]),
                panel_resultados,
                ft.Row([lbl_total_c, drop_metodo], alignment="spaceBetween"),
                btn_vincular_fiado,
                panel_buscar_cliente,
                lista_compra,
            ], spacing=10, scroll=ft.ScrollMode.AUTO, expand=True),
            btn_ir_fiados,
            btn_cobrar,
        ], spacing=8),
        padding=16, visible=False, expand=True
    )

    # ── PANTALLA 3: CONFIRMAR TICKET ─────────────────────────────────────────
    lista_ticket      = ft.Column(scroll=ft.ScrollMode.ALWAYS, height=180)
    in_pago           = inp("¿Con cuánto paga?", kb="number")
    lbl_vuelto        = ft.Text("$0", size=28, weight="w900", color="#EF4444")
    lbl_ticket_total  = ft.Text("$0", size=34, weight="w900", color="#F43F5E")
    lbl_cobrar_status = ft.Text("", size=13, weight="bold")
    row_vuelto        = ft.Column(visible=False)

    # ── Pago mixto ────────────────────────────────────────────────────────────
    sw_mixto      = ft.Switch(label="Pago mixto", value=False, active_color="#F43F5E")
    panel_mixto   = ft.Column(visible=False, spacing=6)
    pagos_mixto   = []   # lista de {"metodo": str, "monto": float, "in_monto": TextField}
    lbl_pendiente = ft.Text("", size=13, color="#F59E0B", weight="bold")

    MNAMES = {
        "efectivo": "💵 Efectivo", "tarjeta": "💳 Tarjeta",
        "mercadopago_qr": "📱 QR/MP", "transferencia": "🏦 Transf.", "fiado": "💸 Fiado"
    }

    def _recalc_pendiente():
        tot    = sum(i["p"] for i in carrito)
        pagado = sum(float(p["in_monto"].value or 0) for p in pagos_mixto)
        resto  = tot - pagado
        if resto <= 0:
            lbl_pendiente.value = f"✅ Cubierto (exceso: {_p(abs(resto))})"
            lbl_pendiente.color = "#10B981"
        else:
            lbl_pendiente.value = f"Pendiente: {_p(resto)}"
            lbl_pendiente.color = "#F59E0B"
        page.update()

    def _agregar_pago_mixto(metodo="efectivo"):
        in_m = ft.TextField(
            label=MNAMES.get(metodo, metodo),
            keyboard_type=ft.KeyboardType.NUMBER,
            filled=True, border_color="transparent", border_radius=8,
            content_padding=10, bgcolor="#0F172A", expand=True,
            on_change=lambda e: _recalc_pendiente()
        )
        entry = {"metodo": metodo, "in_monto": in_m}
        pagos_mixto.append(entry)

        drop_m = ft.Dropdown(
            options=[ft.dropdown.Option(key=k, text=v) for k, v in MNAMES.items()],
            value=metodo, width=130, border_radius=8,
            filled=True, bgcolor="#0F172A", border_color="transparent",
        )
        def _on_drop(e, ent=entry):
            ent["metodo"] = drop_m.value

        drop_m.on_change = _on_drop

        def _quitar(e, ent=entry, row=None):
            pagos_mixto.remove(ent)
            panel_mixto.controls.remove(row_ref[0])
            _recalc_pendiente()

        fila = ft.Row([drop_m, in_m], spacing=6)
        row_ref = [fila]
        fila.controls.append(
            ft.ElevatedButton("✕", bgcolor="#EF4444", color="white", width=36, height=36,
                on_click=lambda e: _quitar(e))
        )
        panel_mixto.controls.insert(len(panel_mixto.controls) - 1, fila)
        _recalc_pendiente()

    def _on_mixto_change(e):
        panel_mixto.visible = sw_mixto.value
        row_vuelto.visible  = not sw_mixto.value and (drop_metodo.value == "efectivo")
        if sw_mixto.value and not pagos_mixto:
            _agregar_pago_mixto("efectivo")
            _agregar_pago_mixto("tarjeta")
        elif not sw_mixto.value:
            pagos_mixto.clear()
            panel_mixto.controls.clear()
            panel_mixto.controls.append(btn_agregar_pago)
            panel_mixto.controls.append(lbl_pendiente)
        page.update()

    sw_mixto.on_change = _on_mixto_change

    btn_agregar_pago = ft.ElevatedButton(
        "+ Agregar método de pago", bgcolor="#334155", color="white",
        expand=True, height=38,
        on_click=lambda e: _agregar_pago_mixto("efectivo")
    )
    panel_mixto.controls = [btn_agregar_pago, lbl_pendiente]

    def calc_vuelto(e):
        try:
            v = float(in_pago.value) - sum(i["p"] for i in carrito)
            lbl_vuelto.value = f"VUELTO: {_p(v)}" if v >= 0 else "FALTA PLATA"
            lbl_vuelto.color = "#10B981" if v >= 0 else "#EF4444"
        except Exception:
            lbl_vuelto.value = "$0"
        page.update()

    in_pago.on_change = calc_vuelto
    row_vuelto.controls = [
        ft.Divider(color="#334155"),
        ft.Row([ft.Text("SU PAGO:"), in_pago], alignment="spaceBetween"),
        ft.Row([ft.Text("VUELTO:", weight="bold"), lbl_vuelto], alignment="spaceBetween"),
    ]

    @en_hilo
    def cobrar_final(e=None):
        tot    = sum(i["p"] for i in carrito)
        metodo = drop_metodo.value or "efectivo"
        items_api = [
            {
                "producto_id":     i["producto_id"],
                "cantidad":        i.get("cant", 1),
                "precio_unitario": i.get("precio_unit", i["p"]),
                "descuento":       0
            }
            for i in carrito if i.get("producto_id") and i["producto_id"] != 0
        ]
        if not items_api:
            items_api = [{"producto_id": 1, "cantidad": 1, "precio_unitario": tot, "descuento": 0}]

        # Armar lista de pagos
        if sw_mixto.value and pagos_mixto:
            pagos_api = [
                {"metodo": p["metodo"], "monto": float(p["in_monto"].value or 0)}
                for p in pagos_mixto if float(p["in_monto"].value or 0) > 0
            ]
            if not pagos_api:
                lbl_cobrar_status.value = "⚠️ Ingresá los montos del pago mixto"
                lbl_cobrar_status.color = "#F59E0B"
                page.update()
                return
        else:
            pagos_api = [{"metodo": metodo, "monto": tot}]

        lbl_cobrar_status.value = "⏳ Registrando..."
        lbl_cobrar_status.color = "#94A3B8"
        page.update()

        cliente_id_enviar = None
        if metodo == "fiado" and not sw_mixto.value:
            cliente_id_enviar = cliente_fiado["id"]
        elif sw_mixto.value:
            tiene_fiado = any(p["metodo"] == "fiado" for p in pagos_api)
            if tiene_fiado:
                cliente_id_enviar = cliente_fiado["id"]

        data = api_post("/ventas/", json_data={
            "usuario_id": 1,
            "cliente_id": cliente_id_enviar,
            "items":      items_api,
            "pagos":      pagos_api,
            "descuento":  0,
            "origen":     "celular"
        })

        def _limpiar_ticket():
            carrito.clear()
            lista_compra.controls.clear()
            in_pago.value = ""
            in_cliente.value = ""
            cliente_fiado["id"] = None
            cliente_fiado["nombre"] = ""
            lbl_cliente_fiado.value = ""
            panel_buscar_cliente.visible = False
            btn_vincular_fiado.visible   = False
            drop_metodo.value = "efectivo"
            sw_mixto.value    = False
            pagos_mixto.clear()
            panel_mixto.controls.clear()
            panel_mixto.controls.append(btn_agregar_pago)
            panel_mixto.controls.append(lbl_pendiente)
            panel_mixto.visible  = False
            lbl_cobrar_status.value = ""
            recalc()

        if data:
            pendientes = _contar_pendientes()
            if pendientes > 0:
                sync = _sincronizar_offline()
                if sync > 0:
                    lbl_aviso.value = f"✅ TICKET #{data.get('numero','?')} + {sync} offline!"
                    lbl_aviso.color = "#10B981"
                    page.update()
            num = data.get("numero", "?")
            _limpiar_ticket()
            view_ticket.visible = False
            view_cobrar.visible = True
            lbl_aviso.value = f"✅ TICKET #{num} COBRADO!"
            lbl_aviso.color = "#10B981"
            cargar_dashboard()
        else:
            _agregar_venta_offline({
                "usuario_id": 1,
                "cliente_id": cliente_id_enviar,
                "items":  items_api,
                "pagos":  pagos_api,
                "descuento": 0,
                "origen": "celular_offline"
            })
            n = _contar_pendientes()
            _limpiar_ticket()
            lbl_aviso.value = f"📴 Sin conexión — guardado offline ({n} pendiente{'s' if n!=1 else ''})"
            lbl_aviso.color = "#F59E0B"
            view_ticket.visible = False
            view_cobrar.visible = True
        page.update()

    view_ticket = ft.Container(
        content=ft.Column([
            ft.Text("🧾 CONFIRMAR VENTA", size=22, weight="w900", color="#94A3B8"),
            ft.Divider(color="#334155"),
            lista_ticket,
            ft.Divider(color="#334155"),
            ft.Row([ft.Text("TOTAL:", weight="bold", size=16), lbl_ticket_total], alignment="spaceBetween"),
            sw_mixto,
            panel_mixto,
            row_vuelto,
            lbl_cobrar_status,
            ft.Row([
                ft.ElevatedButton("🔙 ATRÁS", expand=True, height=52, bgcolor="#334155", color="white",
                    on_click=lambda _: (
                        setattr(view_ticket, "visible", False),
                        setattr(view_cobrar, "visible", True),
                        page.update()
                    )),
                ft.ElevatedButton("✅ COBRAR", expand=True, height=52, bgcolor="#10B981", color="white",
                    on_click=cobrar_final),
            ], spacing=10)
        ], spacing=10),
        padding=16, visible=False, expand=True
    )

    def ir_ticket():
        if not carrito:
            return
        if drop_metodo.value == "fiado" and not cliente_fiado["id"] and not sw_mixto.value:
            lbl_aviso.value = "⚠️ Fiado requiere vincular un cliente"
            lbl_aviso.color = "#EF4444"
            panel_buscar_cliente.visible = True
            page.update()
            return
        lista_ticket.controls = [
            ft.Row([
                ft.Text(i["n"], expand=True, size=12),
                ft.Text(f"x{i.get('cant',1)}", size=11, color="#94A3B8", width=28),
                ft.Text(_p(i['p']), size=13, weight="bold"),
            ])
            for i in carrito
        ]
        tot = sum(i["p"] for i in carrito)
        lbl_ticket_total.value = _p(tot)
        lbl_cobrar_status.value = ""
        row_vuelto.visible = (drop_metodo.value == "efectivo") and not sw_mixto.value
        in_pago.value = ""
        lbl_vuelto.value = "$0"
        view_cobrar.visible = False
        view_ticket.visible = True
        page.update()

    # ── PANTALLA 4: OFERTAS ───────────────────────────────────────────────────
    lista_ofertas_ui  = ft.Column(spacing=8, scroll=ft.ScrollMode.ALWAYS, height=300)
    in_texto_oferta   = inp("Texto de la oferta", "Ej: 2x1 en Gaseosas 🎉")
    color_sel         = {"fondo": "#e74c3c", "texto": "#ffffff"}
    lbl_color_preview = ft.Container(
        content=ft.Text("Vista previa del texto", color="#ffffff", weight="bold", text_align="center"),
        bgcolor="#e74c3c", border_radius=10, padding=14, expand=True
    )

    def set_color_fondo(e):
        colores = ["#e74c3c", "#27ae60", "#3498db", "#9b59b6", "#f39c12",
                   "#1abc9c", "#e91e63", "#ff5722"]
        idx = (colores.index(color_sel["fondo"]) + 1) % len(colores) \
              if color_sel["fondo"] in colores else 0
        color_sel["fondo"]         = colores[idx]
        btn_color_fondo.bgcolor    = colores[idx]
        lbl_color_preview.bgcolor  = colores[idx]
        page.update()

    btn_color_fondo = ft.ElevatedButton(
        "🎨 Color fondo", bgcolor="#e74c3c", color="white",
        on_click=set_color_fondo, expand=True, height=44
    )

    def actualizar_preview(e):
        lbl_color_preview.content.value = in_texto_oferta.value or "Vista previa"
        page.update()

    in_texto_oferta.on_change = actualizar_preview

    @en_hilo
    def agregar_oferta_texto(e=None):
        texto = in_texto_oferta.value.strip()
        if not texto:
            lbl_oferta_status.value = "⚠️ Escribí algo primero"
            lbl_oferta_status.color = "#F59E0B"
            page.update()
            return
        lbl_oferta_status.value = "⏳ Subiendo..."
        lbl_oferta_status.color = "#94A3B8"
        page.update()
        data = api_post("/ofertas/texto", json_data={
            "contenido":   texto,
            "color_fondo": color_sel["fondo"],
            "color_texto": color_sel["texto"],
            "tamanio":     32
        })
        if data:
            in_texto_oferta.value   = ""
            lbl_oferta_status.value = f"✅ Oferta subida! ({data.get('total', 0)} en total)"
            lbl_oferta_status.color = "#10B981"
            cargar_lista_ofertas()
        else:
            lbl_oferta_status.value = f"❌ Error de conexión — {get_api_url()}"
            lbl_oferta_status.color = "#EF4444"
        page.update()

    @en_hilo
    def borrar_oferta(idx):
        data = api_delete(f"/ofertas/{idx}")
        if data:
            lbl_oferta_status.value = "🗑 Oferta eliminada"
            lbl_oferta_status.color = "#94A3B8"
            cargar_lista_ofertas()
        page.update()

    @en_hilo
    def cargar_lista_ofertas(e=None):
        data = api_get("/ofertas/")
        lista_ofertas_ui.controls.clear()
        if data:
            for i, o in enumerate(data):
                if o["tipo"] == "texto":
                    preview    = o["contenido"][:30] + ("..." if len(o["contenido"]) > 30 else "")
                    texto_item = f"📝  {preview}"
                    color_item = o.get("color_fondo", "#e74c3c")
                else:
                    texto_item = f"📷  {os.path.basename(o['contenido'])}"
                    color_item = "#334155"
                lista_ofertas_ui.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text(texto_item, expand=True, size=12, color="white"),
                            ft.ElevatedButton("🗑", bgcolor="#EF4444", color="white",
                                width=44, height=36,
                                on_click=lambda _, idx=i: borrar_oferta(idx))
                        ]),
                        bgcolor=color_item,
                        padding=ft.padding.symmetric(horizontal=12, vertical=8),
                        border_radius=10
                    )
                )
            if not data:
                lista_ofertas_ui.controls.append(
                    ft.Text("Sin ofertas todavía", color="#94A3B8", size=13)
                )
        else:
            lista_ofertas_ui.controls.append(
                ft.Text(f"Sin conexión — {get_api_url()}", color="#EF4444", size=12)
            )
        page.update()

    in_url_imagen = ft.TextField(
        label="URL de imagen (pegá el link)",
        hint_text="https://...",
        filled=True, border_color="transparent", border_radius=12,
        content_padding=14, bgcolor="#1E293B", expand=True,
        keyboard_type=ft.KeyboardType.URL,
    )

    @en_hilo
    def subir_imagen_por_url(e=None):
        url = in_url_imagen.value.strip()
        if not url:
            lbl_oferta_status.value = "⚠️ Pegá una URL de imagen primero"
            lbl_oferta_status.color = "#F59E0B"
            page.update()
            return
        lbl_oferta_status.value = "⏳ Descargando imagen..."
        lbl_oferta_status.color = "#94A3B8"
        page.update()
        data = api_post("/ofertas/imagen-url", json_data={"url": url})
        if data and data.get("ok"):
            in_url_imagen.value = ""
            lbl_oferta_status.value = f"✅ Imagen subida ({data.get('total', 0)} ofertas)"
            lbl_oferta_status.color = "#10B981"
            cargar_lista_ofertas()
        else:
            detalle = data.get("detail", "Error desconocido") if data else "Sin conexión"
            lbl_oferta_status.value = f"❌ {detalle}"
            lbl_oferta_status.color = "#EF4444"
        page.update()

    view_ofertas = ft.Container(
        content=ft.Column([
            ft.Text("🏷️ SUBIR OFERTAS A LA PC", size=20, weight="w900"),
            ft.Text("Las ofertas se muestran en la pantalla de ventas", color="#94A3B8", size=12),
            lbl_color_preview,
            in_texto_oferta,
            ft.Row([
                btn_color_fondo,
                ft.ElevatedButton("📤 SUBIR TEXTO", bgcolor="#556EE6", color="white",
                    on_click=agregar_oferta_texto, expand=True, height=44)
            ]),
            ft.Divider(color="#334155"),
            ft.Text("📷 Subir imagen por URL", weight="bold", size=13, color="#E91E63"),
            ft.Text(
                "Abrí la imagen en el cel → compartir → copiar link → pegalo acá",
                color="#94A3B8", size=11
            ),
            ft.Row([
                in_url_imagen,
                ft.ElevatedButton("📤", on_click=subir_imagen_por_url,
                    bgcolor="#E91E63", color="white", height=48, width=50),
            ], spacing=8),
            lbl_oferta_status,
            ft.Divider(color="#334155"),
            ft.Row([
                ft.Text("Ofertas en la PC:", weight="bold", size=13, expand=True),
                ft.ElevatedButton("🔄", on_click=cargar_lista_ofertas,
                    bgcolor="#1E293B", color="white", width=44, height=36)
            ]),
            lista_ofertas_ui,
        ], spacing=10),
        padding=16, visible=False, expand=True
    )

    # ── PANTALLA 5: VENTAS DEL PERÍODO ───────────────────────────────────────
    hoy_str        = datetime.now().strftime("%Y-%m-%d")
    in_desde = ft.TextField(label="Desde", hint_text="YYYY-MM-DD", value=hoy_str,
        filled=True, border_color="transparent", border_radius=12,
        content_padding=14, bgcolor="#1E293B", expand=True)
    in_hasta = ft.TextField(label="Hasta", hint_text="YYYY-MM-DD", value=hoy_str,
        filled=True, border_color="transparent", border_radius=12,
        content_padding=14, bgcolor="#1E293B", expand=True)
    lbl_ventas_total   = ft.Text("$0", size=32, weight="w900", color="#10B981")
    lbl_ventas_resumen = ft.Text("", size=12, color="#94A3B8")
    lbl_ventas_err     = ft.Text("", color="#EF4444", size=12)
    lista_ventas_ui    = ft.Column(spacing=6, scroll=ft.ScrollMode.ALWAYS, height=370)

    def ver_detalle_venta(venta_id):
        if not venta_id:
            return

        def _fetch():
            data = api_get(f"/ventas/{venta_id}")
            if not data:
                return
            items = data.get("items", [])

            # ── Diálogo de anulación ───────────────────────────────────────
            lbl_anular_status = ft.Text("", size=12, color="#EF4444")
            in_anular_pass    = ft.TextField(
                label="Contraseña admin", password=True,
                filled=True, border_color="transparent", border_radius=8,
                content_padding=10, bgcolor="#0F172A"
            )
            in_motivo = ft.TextField(
                label="Motivo", value="Anulación desde móvil",
                filled=True, border_color="transparent", border_radius=8,
                content_padding=10, bgcolor="#0F172A"
            )
            # Selector de usuario admin
            usuarios_admin = [{"id": 1, "nombre": "Admin"}]
            drop_usuario   = ft.Dropdown(
                options=[], value=None, border_radius=8,
                filled=True, bgcolor="#0F172A", border_color="transparent",
                label="Usuario"
            )

            def _cargar_usuarios():
                us = api_get("/usuarios") or []
                admins = [u for u in us if u.get("rol") in ("admin", "encargado") and u.get("activo")]
                if admins:
                    usuarios_admin.clear()
                    usuarios_admin.extend(admins)
                    drop_usuario.options = [
                        ft.dropdown.Option(key=str(u["id"]), text=f"{u['nombre']} ({u['rol']})")
                        for u in admins
                    ]
                    drop_usuario.value = str(admins[0]["id"])
                    page.update()

            threading.Thread(target=_cargar_usuarios, daemon=True).start()

            dlg_anular = ft.AlertDialog(
                modal=True,
                title=ft.Text("🚫 Anular venta", color="#EF4444", weight="bold"),
                content=ft.Column([
                    ft.Text(f"Venta #{data.get('numero','?')} — {_p(data.get('total',0))}",
                            size=13, color="#94A3B8"),
                    drop_usuario,
                    in_anular_pass,
                    in_motivo,
                    lbl_anular_status,
                ], tight=True, spacing=8, width=300),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: cerrar_dlg(dlg_anular)),
                    ft.ElevatedButton("🚫 ANULAR", bgcolor="#EF4444", color="white",
                        on_click=lambda e: _confirmar_anulacion()),
                ],
                bgcolor="#1E293B",
            )

            def _confirmar_anulacion():
                uid = drop_usuario.value
                pw  = in_anular_pass.value.strip()
                mot = in_motivo.value.strip() or "Anulación desde móvil"
                if not uid or not pw:
                    lbl_anular_status.value = "⚠️ Completá todos los campos"
                    lbl_anular_status.color = "#F59E0B"
                    page.update()
                    return
                lbl_anular_status.value = "⏳ Procesando..."
                lbl_anular_status.color = "#94A3B8"
                page.update()

                def _anular():
                    r = api_post(f"/ventas/{venta_id}/anular", json_data={
                        "motivo":         mot,
                        "password_admin": pw,
                        "usuario_id":     int(uid)
                    })
                    if r and "anulada" in r.get("mensaje", ""):
                        cerrar_dlg(dlg_anular)
                        cerrar_dlg(dlg)
                        lbl_ventas_err.value = f"✅ Venta #{data.get('numero','?')} anulada"
                        lbl_ventas_err.color = "#10B981"
                        cargar_ventas()
                    else:
                        msg = r.get("detail", "Contraseña incorrecta o sin permisos") if r else "Sin conexión"
                        lbl_anular_status.value = f"❌ {msg}"
                        lbl_anular_status.color = "#EF4444"
                    page.update()

                threading.Thread(target=_anular, daemon=True).start()

            estado = data.get("estado", "completada")
            acciones = [ft.TextButton("Cerrar", on_click=lambda e: cerrar_dlg(dlg))]
            if estado != "anulada":
                acciones.append(
                    ft.ElevatedButton("🚫 Anular", bgcolor="#EF4444", color="white",
                        on_click=lambda e: (cerrar_dlg(dlg), abrir_dlg(dlg_anular)))
                )

            dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text(
                    f"Ticket #{data.get('numero','?')}  {'❌ ANULADA' if estado=='anulada' else ''}",
                    weight="bold"
                ),
                content=ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(i.get("nombre", "?"), expand=True, size=12),
                            ft.Text(f"x{i.get('cantidad', 1)}", size=12, color="#94A3B8"),
                            ft.Text(_p(i.get('subtotal', 0)), size=13,
                                    weight="bold", color="#38BDF8"),
                        ]) for i in items
                    ] + [
                        ft.Divider(color="#334155"),
                        ft.Row([
                            ft.Text("TOTAL", weight="bold", expand=True),
                            ft.Text(_p(data.get('total', 0)),
                                    weight="bold", size=16, color="#10B981"),
                        ])
                    ], spacing=6, scroll=ft.ScrollMode.ALWAYS),
                    height=300
                ),
                actions=acciones,
                bgcolor="#1E293B",
            )
            abrir_dlg(dlg)

        threading.Thread(target=_fetch, daemon=True).start()

    @en_hilo
    def cargar_ventas(e=None):
        desde = in_desde.value.strip() or hoy_str
        hasta = in_hasta.value.strip() or hoy_str
        lbl_ventas_err.value = "⏳ Cargando..."
        lbl_ventas_err.color = "#94A3B8"
        lista_ventas_ui.controls.clear()
        page.update()
        data = api_get("/reportes/rango", params={"desde": desde, "hasta": hasta})
        lbl_ventas_err.value = ""
        if data:
            cant   = data.get("cantidad_ventas", 0)
            total  = float(data.get("total_vendido", 0))
            ventas = data.get("ventas", [])
            lbl_ventas_total.value   = _p(total)
            lbl_ventas_resumen.value = f"{cant} venta{'s' if cant!=1 else ''} — {desde} al {hasta}"
            MCOLOR = {"efectivo": "#10B981", "tarjeta": "#3B82F6",
                      "mercadopago_qr": "#9333EA", "transferencia": "#F59E0B", "fiado": "#EF4444"}
            MICON  = {"efectivo": "💵", "tarjeta": "💳",
                      "mercadopago_qr": "📱", "transferencia": "🏦", "fiado": "💸"}
            for v in ventas:
                metodo = v.get("metodo_pago", "efectivo").lower()
                estado = v.get("estado", "completada")
                color  = MCOLOR.get(metodo, "#94A3B8") if estado != "anulada" else "#475569"
                fecha  = str(v.get("fecha", ""))
                hora   = fecha[11:16] if len(fecha) >= 16 else ""
                lista_ventas_ui.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text(MICON.get(metodo, "💰"), size=20),
                            ft.Column([
                                ft.Text(f"#{v.get('numero','?')}  {hora}", size=12,
                                        weight="bold", color="white"),
                                ft.Text(metodo.upper(), size=10, color=color),
                            ], spacing=0, expand=True),
                            ft.Column([
                                ft.Text(_p(v.get('total',0)), size=15,
                                        weight="w900", color=color),
                                ft.Text(estado, size=9,
                                        color="#EF4444" if estado=="anulada" else "#94A3B8"),
                            ], spacing=0, horizontal_alignment="end"),
                        ]),
                        bgcolor="#1E293B", padding=12, border_radius=12,
                        on_click=lambda e, vid=v.get("id"): ver_detalle_venta(vid)
                    )
                )
            if not ventas:
                lista_ventas_ui.controls.append(
                    ft.Text("Sin ventas en ese período", color="#94A3B8",
                            size=13, text_align="center")
                )
        else:
            lbl_ventas_total.value = "$ 0.00"
            lbl_ventas_err.value   = f"Sin conexión — {get_api_url()}"
        page.update()

    def _v_hoy(e):
        h = datetime.now().strftime("%Y-%m-%d")
        in_desde.value = h
        in_hasta.value = h
        cargar_ventas()

    def _v_mes(e):
        hoy = datetime.now()
        in_desde.value = hoy.strftime("%Y-%m-01")
        in_hasta.value = hoy.strftime("%Y-%m-%d")
        cargar_ventas()

    view_ventas = ft.Container(
        content=ft.Column([
            ft.Text("📋 VENTAS DEL PERÍODO", size=20, weight="w900"),
            ft.Row([in_desde, in_hasta], spacing=8),
            ft.Row([
                ft.ElevatedButton("Hoy", on_click=_v_hoy, expand=True, height=40,
                    bgcolor="#1E293B", color="white"),
                ft.ElevatedButton("Mes", on_click=_v_mes, expand=True, height=40,
                    bgcolor="#1E293B", color="white"),
                ft.ElevatedButton("🔍 Ver", on_click=cargar_ventas, expand=True, height=40,
                    bgcolor="#3B82F6", color="white"),
            ], spacing=6),
            ft.Container(
                content=ft.Column([lbl_ventas_total, lbl_ventas_resumen],
                    horizontal_alignment="center", spacing=2),
                bgcolor="#0F172A", padding=14, border_radius=14),
            lbl_ventas_err,
            lista_ventas_ui,
        ], spacing=10),
        padding=16, visible=False, expand=True
    )

    # ── PANTALLA: FIADOS ──────────────────────────────────────────────────────
    lista_fiados_ui   = ft.Column(spacing=8, scroll=ft.ScrollMode.ALWAYS, height=420)
    lbl_fiados_status = ft.Text("", size=12, color="#94A3B8")

    @en_hilo
    def cargar_fiados(e=None):
        lbl_fiados_status.value = "⏳ Cargando..."
        lista_fiados_ui.controls.clear()
        page.update()
        data = api_get("/clientes/")
        lbl_fiados_status.value = ""
        if data:
            con_deuda = [c for c in data if float(c.get("deuda_actual") or 0) > 0]
            con_deuda.sort(key=lambda c: float(c.get("deuda_actual") or 0), reverse=True)
            if not con_deuda:
                lista_fiados_ui.controls.append(
                    ft.Text("✅ Sin deudas pendientes", color="#10B981", size=14, text_align="center")
                )
            for c in con_deuda:
                deuda = float(c.get("deuda_actual") or 0)
                in_pago_fiado = ft.TextField(
                    label="Pago parcial $", keyboard_type=ft.KeyboardType.NUMBER,
                    filled=True, border_color="transparent", border_radius=8,
                    content_padding=8, bgcolor="#0F172A", width=130
                )

                def _registrar_pago(ev, cli=c, inp=in_pago_fiado):
                    try:
                        monto = float(inp.value)
                    except Exception:
                        return

                    def _put():
                        r = api_post("/fiados/pago", json_data={
                            "cliente_id": cli["id"], "monto": monto
                        })
                        if r:
                            lbl_fiados_status.value = f"✅ Pago de {_p(monto)} registrado para {cli['nombre']}"
                            lbl_fiados_status.color = "#10B981"
                            cargar_fiados()
                        else:
                            lbl_fiados_status.value = "❌ Error al registrar pago"
                            lbl_fiados_status.color = "#EF4444"
                        page.update()

                    threading.Thread(target=_put, daemon=True).start()

                lista_fiados_ui.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text(c.get("nombre", "?"), weight="bold",
                                        expand=True, size=14, color="white"),
                                ft.Text(_p(deuda), size=16, weight="w900", color="#EF4444"),
                            ]),
                            ft.Row([
                                in_pago_fiado,
                                ft.ElevatedButton("💳 Pagar", bgcolor="#10B981", color="white",
                                    height=40, on_click=_registrar_pago),
                            ], spacing=8),
                        ], spacing=6),
                        bgcolor="#1E293B", padding=14, border_radius=12
                    )
                )
        else:
            lbl_fiados_status.value = f"Sin conexión — {get_api_url()}"
            lbl_fiados_status.color = "#EF4444"
        page.update()

    view_fiados = ft.Container(
        content=ft.Column([
            ft.Text("💸 DEUDAS DE FIADOS", size=20, weight="w900"),
            ft.Text("Clientes con saldo pendiente", color="#94A3B8", size=12),
            ft.ElevatedButton("🔄 Actualizar", on_click=cargar_fiados,
                expand=True, height=40, bgcolor="#1E293B", color="white"),
            lbl_fiados_status,
            lista_fiados_ui,
        ], spacing=10),
        padding=16, visible=False, expand=True
    )

    # ── PANTALLA 6: MODIFICAR PRECIOS ────────────────────────────────────────
    in_buscar_precio  = ft.TextField(
        label="Buscar producto...", filled=True, border_color="transparent",
        border_radius=12, content_padding=14, bgcolor="#1E293B", expand=True
    )
    lista_precios_ui  = ft.Column(spacing=6, scroll=ft.ScrollMode.ALWAYS, height=420)
    lbl_precio_status = ft.Text("", size=12, color="#94A3B8")

    def _buscar_para_precio(e=None):
        q = in_buscar_precio.value.strip()
        lista_precios_ui.controls.clear()
        if not q:
            page.update()
            return

        def _buscar():
            if productos_cache:
                q_lower = q.lower()
                matches = [p for p in productos_cache if q_lower in p["nombre"].lower()][:20]
            else:
                matches = api_get("/productos/buscar", params={"q": q}) or []

            lista_precios_ui.controls.clear()
            for p in matches:
                precio_actual = float(p.get("precio_venta") or 0)
                in_nuevo = ft.TextField(
                    value=f"{precio_actual:.0f}",
                    width=110, text_align="right",
                    bgcolor="#0F172A", border_color="transparent",
                    filled=True, border_radius=8, content_padding=8,
                    keyboard_type=ft.KeyboardType.NUMBER
                )
                in_pin = ft.TextField(
                    label="PIN", password=True, max_length=6,
                    width=80, bgcolor="#0F172A", border_color="transparent",
                    filled=True, border_radius=8, content_padding=8,
                )

                def _guardar(ev, prod=p, inp=in_nuevo, pinf=in_pin):
                    if pinf.value.strip() != leer_pin_precios():
                        lbl_precio_status.value = "❌ PIN incorrecto"
                        lbl_precio_status.color = "#EF4444"
                        page.update()
                        return
                    try:
                        nuevo = float(inp.value)
                    except Exception:
                        lbl_precio_status.value = "❌ Precio inválido"
                        lbl_precio_status.color = "#EF4444"
                        page.update()
                        return

                    def _put():
                        r = api_post(f"/productos/{prod['id']}/cambiar-precio", json_data={
                            "precio_nuevo": nuevo,
                            "usuario": "mobile"
                        })
                        if r and r.get("ok"):
                            lbl_precio_status.value = "⏳ Actualizando precios..."
                            lbl_precio_status.color = "#94A3B8"
                            page.update()
                            # Esperar a que el cache se actualice antes de confirmar
                            data = api_get("/productos/")
                            if data:
                                productos_cache.clear()
                                productos_cache.extend(data)
                                productos_codigo.clear()
                                productos_codigo.update({
                                    str(p2["codigo_barra"]): p2
                                    for p2 in data if p2.get("codigo_barra")
                                })
                            lbl_precio_status.value = f"✅ {prod['nombre']} → {_p(nuevo)} (cache actualizado)"
                            lbl_precio_status.color = "#10B981"
                        else:
                            error_msg = r.get("error", "Error") if r else "Sin conexión"
                            lbl_precio_status.value = f"❌ {error_msg}"
                            lbl_precio_status.color = "#EF4444"
                        page.update()

                    threading.Thread(target=_put, daemon=True).start()

                lista_precios_ui.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text(p["nombre"], size=12, weight="bold", color="white"),
                            ft.Row([
                                ft.Text(f"Actual: {_p(precio_actual)}", size=11,
                                        color="#94A3B8", expand=True),
                                in_pin,
                                in_nuevo,
                                ft.ElevatedButton("✓", bgcolor="#10B981", color="white",
                                    width=44, height=40, on_click=_guardar),
                            ], spacing=4),
                        ], spacing=4),
                        bgcolor="#1E293B", padding=12, border_radius=12
                    )
                )
            if not matches:
                lista_precios_ui.controls.append(
                    ft.Text("Sin resultados", color="#94A3B8", size=13, text_align="center")
                )
            page.update()

        threading.Thread(target=_buscar, daemon=True).start()

    in_buscar_precio.on_submit = _buscar_para_precio

    view_precios_mobile = ft.Container(
        content=ft.Column([
            ft.Text("💰 MODIFICAR PRECIOS", size=20, weight="w900"),
            ft.Text("PIN requerido — la PC recibirá la alerta", color="#94A3B8", size=11),
            ft.Row([
                in_buscar_precio,
                ft.ElevatedButton("🔍", on_click=_buscar_para_precio,
                    bgcolor="#3B82F6", color="white", height=48, width=50)
            ], spacing=8),
            lbl_precio_status,
            lista_precios_ui,
        ], spacing=10),
        padding=16, visible=False, expand=True
    )

    # ── PANTALLA 7: CAJA ─────────────────────────────────────────────────────
    MCOLOR = {"efectivo": "#10B981", "tarjeta": "#3B82F6",
               "mercadopago_qr": "#9333EA", "transferencia": "#F59E0B", "fiado": "#EF4444"}
    MICON  = {"efectivo": "💵", "tarjeta": "💳",
               "mercadopago_qr": "📱", "transferencia": "🏦", "fiado": "💸"}

    # ── Cabecera: total del día + delta + turno ───────────────────────────────
    lbl_caja_total    = ft.Text("$0", size=32, weight="w900", color="#F43F5E")
    lbl_caja_delta    = ft.Text("", size=13, color="#94A3B8")
    lbl_caja_ventas   = ft.Text("0 ventas", size=12, color="#94A3B8")
    lbl_caja_ticket   = ft.Text("Ticket: $0", size=12, color="#94A3B8")
    lbl_turno_badge   = ft.Text("", size=11, weight="bold")
    ctn_turno_badge   = ft.Container(
        content=lbl_turno_badge, border_radius=8, padding=ft.padding.symmetric(4, 10)
    )

    # Chips semana / mes
    lbl_sem_total  = ft.Text("$0", size=14, weight="bold", color="white")
    lbl_sem_ventas = ft.Text("0 ventas", size=10, color="#94A3B8")
    lbl_mes_total  = ft.Text("$0", size=14, weight="bold", color="white")
    lbl_mes_ventas = ft.Text("0 ventas", size=10, color="#94A3B8")

    ctn_cabecera = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Column([
                    ft.Text("HOY", size=10, weight="bold", color="#94A3B8"),
                    lbl_caja_total,
                    ft.Row([lbl_caja_delta], spacing=4),
                    ft.Row([lbl_caja_ventas, ft.Text("·", color="#334155"), lbl_caja_ticket], spacing=6),
                ], spacing=2, expand=True),
                ctn_turno_badge,
            ], alignment="spaceBetween"),
            ft.Divider(color="#1E293B", height=12),
            ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Text("7 DÍAS", size=9, color="#94A3B8"),
                        lbl_sem_total, lbl_sem_ventas,
                    ], spacing=1, horizontal_alignment="center"),
                    bgcolor="#1E293B", border_radius=10, padding=10, expand=True
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text("ESTE MES", size=9, color="#94A3B8"),
                        lbl_mes_total, lbl_mes_ventas,
                    ], spacing=1, horizontal_alignment="center"),
                    bgcolor="#1E293B", border_radius=10, padding=10, expand=True
                ),
            ], spacing=8),
        ], spacing=6),
        bgcolor="#0F172A", padding=14, border_radius=14
    )

    # ── Tabs HOY / HISTORIAL / CIERRES ───────────────────────────────────────
    vista_caja   = {"sel": "hoy"}
    lbl_caja_status = ft.Text("", size=12, color="#94A3B8")
    lista_caja_ui   = ft.Column(spacing=8, scroll=ft.ScrollMode.ALWAYS, expand=True)

    _TABS_CAJA = [("hoy", "Hoy"), ("historial", "Historial"), ("cierres", "Cierres")]
    _btns_caja = {}
    def _mk_tab_btn_caja(key, label):
        btn = ft.ElevatedButton(
            label,
            bgcolor="#F43F5E" if key == "hoy" else "#1E293B",
            color="white", expand=True, height=36,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
        )
        def _click(e, k=key): _sel_caja_tab(k)
        btn.on_click = _click
        return btn
    for _k, _lbl in _TABS_CAJA:
        _btns_caja[_k] = _mk_tab_btn_caja(_k, _lbl)

    def _sel_caja_tab(key):
        vista_caja["sel"] = key
        for k, b in _btns_caja.items():
            b.bgcolor = "#F43F5E" if k == key else "#1E293B"
        cargar_caja()

    # ── Helpers de renderizado ────────────────────────────────────────────────
    def _card_dia(dia):
        fecha   = dia.get("fecha", "")
        total   = float(dia.get("total", 0))
        cant    = int(dia.get("cantidad", 0))
        ticket  = float(dia.get("ticket_promedio", 0))
        barras  = []
        max_val = max((float(dia.get(m, 0)) for m in MICON), default=1) or 1
        for m, icon in MICON.items():
            val = float(dia.get(m, 0))
            if val <= 0:
                continue
            pct = val / max_val
            barras.append(
                ft.Row([
                    ft.Text(f"{icon}", size=12, width=22),
                    ft.Container(
                        width=max(4, int(120 * pct)),
                        height=10, bgcolor=MCOLOR[m], border_radius=4
                    ),
                    ft.Text(_p(val), size=11, color=MCOLOR[m], weight="bold"),
                ], spacing=6, vertical_alignment="center")
            )
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(fecha, weight="bold", size=13, color="white", expand=True),
                    ft.Text(_p(total), weight="bold", size=14, color="#F43F5E"),
                ]),
                ft.Row([
                    ft.Text(f"{cant} ventas", size=10, color="#94A3B8"),
                    ft.Text("·", color="#334155", size=10),
                    ft.Text(f"Ticket {_p(ticket)}", size=10, color="#94A3B8"),
                ], spacing=6),
                ft.Column(barras, spacing=3) if barras else ft.Text("Sin ventas", color="#334155", size=11),
            ], spacing=6),
            bgcolor="#1E293B", padding=12, border_radius=12
        )

    def _card_turno(t):
        apertura   = t.get("apertura", "")
        cierre     = t.get("cierre", "")
        calculado  = float(t.get("monto_cierre_calculado", 0))
        declarado  = float(t.get("monto_cierre_declarado", 0))
        diferencia = float(t.get("diferencia", 0))
        color_dif  = "#10B981" if abs(diferencia) < 1 else ("#F59E0B" if abs(diferencia) < 500 else "#EF4444")
        icono_dif  = "✓" if abs(diferencia) < 1 else ("⚠" if abs(diferencia) < 500 else "✗")
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(f"🕐 {apertura}", size=11, color="#94A3B8", expand=True),
                    ft.Text(f"→ {cierre}", size=11, color="#64748B"),
                ]),
                ft.Row([
                    ft.Column([
                        ft.Text("Calculado", size=10, color="#94A3B8"),
                        ft.Text(_p(calculado), size=15, weight="bold", color="#10B981"),
                    ], spacing=2, expand=True),
                    ft.Column([
                        ft.Text("Declarado", size=10, color="#94A3B8"),
                        ft.Text(_p(declarado), size=15, weight="bold", color="#38BDF8"),
                    ], spacing=2, expand=True),
                    ft.Column([
                        ft.Text("Diferencia", size=10, color="#94A3B8"),
                        ft.Text(f"{icono_dif} {('+' if diferencia >= 0 else '') + _p(diferencia)}", size=15, weight="bold", color=color_dif),
                    ], spacing=2, expand=True),
                ]),
            ], spacing=8),
            bgcolor="#1E293B", padding=12, border_radius=12
        )

    # ── Carga principal ───────────────────────────────────────────────────────
    @en_hilo
    def cargar_caja(e=None):
        lbl_caja_status.value = "⏳ Cargando..."
        lista_caja_ui.controls.clear()
        page.update()

        # Una sola llamada para todo el encabezado
        resumen = api_get("/caja/resumen-rapido")
        if resumen:
            h = resumen.get("hoy", {})
            delta = float(resumen.get("delta_pct", 0))
            sem   = resumen.get("semana", {})
            mes   = resumen.get("mes", {})
            turno = resumen.get("turno", {})

            lbl_caja_total.value  = _p(h.get('total', 0))
            lbl_caja_ventas.value = f"{h.get('cantidad', 0)} ventas"
            lbl_caja_ticket.value = f"Ticket: {_p(h.get('ticket_promedio', 0))}"

            if delta > 0:
                lbl_caja_delta.value = f"↑ {delta:+.1f}% vs ayer"
                lbl_caja_delta.color = "#10B981"
            elif delta < 0:
                lbl_caja_delta.value = f"↓ {delta:.1f}% vs ayer"
                lbl_caja_delta.color = "#EF4444"
            else:
                lbl_caja_delta.value = "= igual que ayer"
                lbl_caja_delta.color = "#94A3B8"

            lbl_sem_total.value  = _p(sem.get('total', 0))
            lbl_sem_ventas.value = f"{sem.get('cantidad', 0)} ventas"
            lbl_mes_total.value  = _p(mes.get('total', 0))
            lbl_mes_ventas.value = f"{mes.get('cantidad', 0)} ventas"

            if turno.get("abierto"):
                lbl_turno_badge.value  = "● CAJA ABIERTA"
                lbl_turno_badge.color  = "#10B981"
                ctn_turno_badge.bgcolor = "#052E16"
            else:
                lbl_turno_badge.value  = "○ CERRADA"
                lbl_turno_badge.color  = "#94A3B8"
                ctn_turno_badge.bgcolor = "#1E293B"

        lbl_caja_status.value = ""

        sel = vista_caja["sel"]

        if sel == "hoy":
            resumen_hoy_data = resumen.get("hoy", {}) if resumen else None
            if resumen_hoy_data:
                # ── Card efectivo en caja ─────────────────────────────────
                gastos_data  = api_get("/gastos/hoy") or {}
                total_gastos = float(gastos_data.get("total", 0))
                apertura     = float((resumen.get("turno") or {}).get("monto_apertura", 0))
                ef_ventas    = float(resumen_hoy_data.get("efectivo", 0))
                efectivo_caja = apertura + ef_ventas - total_gastos
                lista_caja_ui.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text("💵 EFECTIVO EN CAJA", size=11, weight="bold", color="#94A3B8"),
                            ft.Row([ft.Text("Apertura", size=12, color="#94A3B8", expand=True),
                                    ft.Text(f"+{_p(apertura)}", size=12, color="#94A3B8")]),
                            ft.Row([ft.Text("+ Ventas efectivo", size=12, color="#10B981", expand=True),
                                    ft.Text(f"+{_p(ef_ventas)}", size=12, color="#10B981")]),
                            ft.Row([ft.Text("- Gastos del día", size=12, color="#EF4444", expand=True),
                                    ft.Text(f"-{_p(total_gastos)}", size=12, color="#EF4444")]),
                            ft.Divider(color="#334155", height=6),
                            ft.Row([ft.Text("EN CAJA AHORA", size=14, weight="bold", color="white", expand=True),
                                    ft.Text(_p(efectivo_caja), size=18, weight="w900", color="#10B981")]),
                        ], spacing=5),
                        bgcolor="#0F172A", padding=14, border_radius=12,
                        border=ft.border.all(1, "#10B981"),
                    )
                )
                # Desglose de hoy: una barra por método
                total_hoy = float(resumen_hoy_data.get("total", 0))
                for m, icon in MICON.items():
                    val = float(resumen_hoy_data.get(m, 0))
                    if val <= 0:
                        continue
                    pct_txt = f"{val/total_hoy*100:.0f}%" if total_hoy > 0 else "0%"
                    lista_caja_ui.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Text(icon, size=20, width=32),
                                ft.Column([
                                    ft.Row([
                                        ft.Text(m.replace("_", " ").title(), size=12,
                                                color="white", expand=True, weight="bold"),
                                        ft.Text(pct_txt, size=11, color="#94A3B8"),
                                    ]),
                                    ft.Container(
                                        content=ft.Container(
                                            width=max(6, int(260 * (val / total_hoy))),
                                            height=8, bgcolor=MCOLOR[m], border_radius=4
                                        ),
                                        bgcolor="#0F172A", border_radius=4, height=8, expand=True
                                    ),
                                    ft.Text(_p(val), size=16, weight="bold", color=MCOLOR[m]),
                                ], spacing=4, expand=True),
                            ], spacing=10, vertical_alignment="center"),
                            bgcolor="#1E293B", padding=ft.padding.symmetric(12, 14),
                            border_radius=12
                        )
                    )
                if not any(float(resumen_hoy_data.get(m, 0)) > 0 for m in MICON):
                    lista_caja_ui.controls.append(
                        ft.Container(
                            ft.Text("Sin ventas registradas hoy", color="#94A3B8",
                                    size=13, text_align="center"),
                            padding=24
                        )
                    )
            else:
                lbl_caja_status.value = f"Sin conexión — {get_api_url()}"
                lbl_caja_status.color = "#EF4444"

        elif sel == "historial":
            data = api_get("/caja/historial-efectivo", params={"dias": 30})
            if data:
                # Agrupar por semana
                from datetime import datetime as _dt, timedelta as _td
                semana_actual = None
                sem_total = 0.0
                for i, dia in enumerate(data):
                    try:
                        fecha_dt = _dt.strptime(dia.get("fecha", ""), "%Y-%m-%d")
                        lunes = fecha_dt - _td(days=fecha_dt.weekday())
                        sem_label = f"Semana del {lunes.strftime('%d/%m')}"
                    except Exception:
                        sem_label = "—"
                        lunes = None

                    if lunes and sem_label != semana_actual:
                        if semana_actual is not None:
                            lista_caja_ui.controls.append(
                                ft.Container(
                                    ft.Row([
                                        ft.Text("SUBTOTAL SEMANA", size=10, color="#64748B", expand=True),
                                        ft.Text(_p(sem_total), size=11, weight="bold", color="#64748B"),
                                    ]),
                                    padding=ft.padding.only(left=8, bottom=4)
                                )
                            )
                        semana_actual = sem_label
                        sem_total = 0.0
                        lista_caja_ui.controls.append(
                            ft.Container(
                                ft.Text(sem_label, size=10, weight="bold", color="#475569"),
                                padding=ft.padding.only(top=6, bottom=2)
                            )
                        )

                    sem_total += float(dia.get("total", 0))
                    lista_caja_ui.controls.append(_card_dia(dia))

                if semana_actual is not None:
                    lista_caja_ui.controls.append(
                        ft.Container(
                            ft.Row([
                                ft.Text("SUBTOTAL SEMANA", size=10, color="#64748B", expand=True),
                                ft.Text(_p(sem_total), size=11, weight="bold", color="#64748B"),
                            ]),
                            padding=ft.padding.only(left=8, bottom=4)
                        )
                    )
            else:
                lbl_caja_status.value = f"Sin conexión — {get_api_url()}"
                lbl_caja_status.color = "#EF4444"

        else:  # cierres
            # Estado del turno actual
            if resumen and resumen.get("turno", {}).get("abierto"):
                t = resumen["turno"]
                lista_caja_ui.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text("TURNO ACTIVO", size=10, weight="bold", color="#10B981"),
                                ft.Text(f"Abierto: {t.get('apertura', '')}", size=12, color="white"),
                                ft.Text(f"Apertura: {_p(t.get('monto_apertura', 0))}", size=11, color="#94A3B8"),
                            ], spacing=3, expand=True),
                            ft.Container(
                                ft.Text("EN CURSO", size=10, weight="bold", color="#10B981"),
                                bgcolor="#052E16", border_radius=8,
                                padding=ft.padding.symmetric(4, 10)
                            ),
                        ]),
                        bgcolor="#0F2918", border=ft.border.all(1, "#10B981"),
                        padding=12, border_radius=12
                    )
                )

            data = api_get("/caja/historial", params={"limite": 30})
            if data:
                for t in data:
                    lista_caja_ui.controls.append(_card_turno(t))
                if not data:
                    lista_caja_ui.controls.append(
                        ft.Container(
                            ft.Text("Sin cierres registrados", color="#94A3B8",
                                    size=13, text_align="center"),
                            padding=24
                        )
                    )
            else:
                lbl_caja_status.value = f"Sin conexión — {get_api_url()}"
                lbl_caja_status.color = "#EF4444"

        page.update()

    view_caja = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("🏦 CAJA", size=20, weight="w900", expand=True),
                ft.IconButton(
                    "refresh", icon_color="#94A3B8",
                    icon_size=20, tooltip="Actualizar",
                    on_click=cargar_caja
                ),
            ]),
            ctn_cabecera,
            ft.Row([_btns_caja[k] for k, _ in _TABS_CAJA], spacing=6),
            lbl_caja_status,
            lista_caja_ui,
        ], spacing=10),
        padding=16, visible=False, expand=True
    )

    # ── PANTALLA 8: CONFIG ────────────────────────────────────────────────────
    in_ip = ft.TextField(
        label="IP de la PC (ej: 192.168.1.100)",
        value=leer_ip(),
        filled=True, border_color="transparent",
        border_radius=12, content_padding=16, bgcolor="#1E293B",
        keyboard_type=ft.KeyboardType.URL
    )
    in_pin_config = ft.TextField(
        label="PIN para modificar precios",
        value=leer_pin_precios(),
        password=True, max_length=8,
        filled=True, border_color="transparent",
        border_radius=12, content_padding=16, bgcolor="#1E293B",
        keyboard_type=ft.KeyboardType.NUMBER
    )
    lbl_config_status = ft.Text("", size=13)

    @en_hilo
    def detectar_auto(e=None):
        lbl_config_status.value = "⏳ Escaneando la red..."
        lbl_config_status.color = "#94A3B8"
        page.update()

        def _progreso(msg):
            lbl_config_status.value = f"⏳ {msg}"
            page.update()

        ip = detectar_mejor_ip(callback_progreso=_progreso)
        if _probar_ip(ip):
            in_ip.value = ip
            guardar_ip(ip)
            _ip_activa["ip"] = ip
            lbl_ip_status.value   = f"📡 {ip}"
            lbl_config_status.value = f"✅ Encontrado en {ip}"
            lbl_config_status.color = "#10B981"
        else:
            lbl_config_status.value = "❌ No encontrado. Ingresá la IP manualmente."
            lbl_config_status.color = "#EF4444"
        page.update()

    @en_hilo
    def guardar_config(e=None):
        ip  = in_ip.value.strip().replace("http://", "").replace(":8000", "")
        pin = in_pin_config.value.strip()
        guardar_ip(ip)
        if pin:
            guardar_config_data({"pin_precios": pin})
        _ip_activa["ip"] = ip
        lbl_config_status.value = "⏳ Probando conexión..."
        lbl_config_status.color = "#94A3B8"
        page.update()
        data = api_get("/")
        if data:
            lbl_config_status.value = f"✅ Conectado a {ip}:8000"
            lbl_config_status.color = "#10B981"
            lbl_ip_status.value     = f"📡 {ip}"
        else:
            lbl_config_status.value = (
                f"❌ No se pudo conectar a {ip}:8000\n"
                "Verificá que la PC esté encendida y en la misma WiFi"
            )
            lbl_config_status.color = "#EF4444"
        page.update()

    view_config = ft.Container(
        content=ft.Column([
            ft.Text("⚙️ CONFIGURACIÓN", size=20, weight="w900"),
            ft.Text("Ingresá la IP de la PC o detectala automáticamente",
                    color="#94A3B8", size=12),
            ft.Container(
                content=ft.Column([
                    ft.Text("¿Cómo saber la IP de la PC?", weight="bold",
                            color="#38BDF8", size=13),
                    ft.Text("En la PC abrí CMD y escribí:", color="#94A3B8", size=12),
                    ft.Container(
                        content=ft.Text("ipconfig", color="#10B981",
                                        font_family="monospace", size=14),
                        bgcolor="#0F172A", padding=10, border_radius=8
                    ),
                    ft.Text("Buscá 'Dirección IPv4' (ej: 192.168.1.100)",
                            color="#94A3B8", size=12),
                ]),
                bgcolor="#1E293B", padding=14, border_radius=12
            ),
            ft.ElevatedButton(
                "🔍 DETECTAR AUTOMÁTICAMENTE", on_click=detectar_auto,
                expand=True, height=44,
                bgcolor="#0F172A", color="#38BDF8",
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
            ),
            in_ip,
            ft.Divider(color="#334155"),
            ft.Text("PIN para modificar precios", size=13, color="#94A3B8"),
            in_pin_config,
            ft.ElevatedButton(
                "💾 GUARDAR Y PROBAR", on_click=guardar_config,
                expand=True, height=48,
                bgcolor="#556EE6", color="white",
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
            ),
            lbl_config_status,
        ], spacing=12),
        padding=16, visible=False, expand=True
    )

    # ── NAVEGACIÓN CON TAB ACTIVO ─────────────────────────────────────────────
    vistas = {
        "D": view_dashboard,
        "C": view_cobrar,
        "O": view_ofertas,
        "V": view_ventas,
        "P": view_precios_mobile,
        "F": view_fiados,
        "K": view_caja,
        "S": view_config,
    }

    COLOR_INACTIVO = "#1E293B"
    COLOR_ACTIVO   = "#F43F5E"

    nav_btns = {}

    def nav(e):
        key = e.control.data
        for k, v in vistas.items():
            v.visible = (k == key)
        view_ticket.visible = False
        lbl_aviso.value     = ""
        # Actualizar colores de la barra
        for k, btn in nav_btns.items():
            btn.bgcolor = COLOR_ACTIVO if k == key else COLOR_INACTIVO
        if key == "D": cargar_dashboard()
        if key == "C": cargar_cache_productos()
        if key == "O": cargar_lista_ofertas()
        if key == "V": cargar_ventas()
        if key == "F": cargar_fiados()
        if key == "K": cargar_caja()
        if key == "P": cargar_cache_productos()
        page.update()

    TABS = [
        ("D", "📊"), ("C", "🛒"), ("O", "🏷️"), ("V", "📋"),
        ("P", "💰"), ("F", "💸"), ("K", "🏦"), ("S", "⚙️"),
    ]

    nav_row_controls = []
    for key, icon in TABS:
        btn = ft.ElevatedButton(
            icon, data=key, on_click=nav,
            expand=True, height=56,
            bgcolor=COLOR_ACTIVO if key == "D" else COLOR_INACTIVO,
            color="white",
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=0))
        )
        nav_btns[key] = btn
        nav_row_controls.append(btn)

    nav_bar = ft.Container(
        content=ft.Row(nav_row_controls, spacing=1),
        bgcolor="#0F172A",
        padding=ft.padding.only(bottom=40)
    )

    # ── Banner de actualización disponible ───────────────────────────────────
    lbl_update_version = ft.Text("", size=13, color="white", expand=True)
    banner_update = ft.Container(
        content=ft.Row([
            ft.Text("🆕", size=16),
            lbl_update_version,
            ft.ElevatedButton(
                "Descargar", height=32,
                bgcolor="#10B981", color="white",
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                on_click=lambda e: page.launch_url(APK_URL),
            ),
        ], spacing=8, vertical_alignment="center"),
        bgcolor="#1E3A2E", padding=ft.padding.symmetric(horizontal=16, vertical=8),
        visible=False,
    )

    @en_hilo
    def verificar_actualizacion(e=None):
        try:
            r = requests.get(VERSION_URL, timeout=8)
            data = r.json()
            nueva = data.get("version", "")
            if nueva and _version_mayor(nueva, APP_VERSION):
                lbl_update_version.value = f"Nueva versión {nueva} disponible"
                banner_update.visible = True
                page.update()
        except Exception:
            pass

    all_views = ft.Column(
        [view_dashboard, view_cobrar, view_ticket, view_ofertas,
         view_ventas, view_precios_mobile, view_fiados, view_caja, view_config],
        expand=True
    )

    def _ir_fiados():
        for k, v in vistas.items():
            v.visible = (k == "F")
        view_ticket.visible = False
        lbl_aviso.value = ""
        for k, btn in nav_btns.items():
            btn.bgcolor = COLOR_ACTIVO if k == "F" else COLOR_INACTIVO
        cargar_fiados()
        page.update()

    page.add(app_bar, banner_update, all_views, nav_bar)
    page.update()
    cargar_dashboard()
    cargar_cache_productos()
    _actualizar_badge()
    _autoconectar_en_hilo()
    verificar_actualizacion()


ft.app(target=main)
