import flet as ft
import requests
import threading
import json
import os
from datetime import datetime

# ─── Configuración de IP ──────────────────────────────────────────────────────
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mobile_config.json")

def leer_ip():
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH) as f:
                return json.load(f).get("ip", "127.0.0.1")
    except Exception:
        pass
    return "127.0.0.1"

def guardar_ip(ip):
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump({"ip": ip}, f)
    except Exception:
        pass

def get_api_url():
    return f"http://{leer_ip()}:8000"


# ─── Llamadas API en hilo separado (evita freezing en Flet) ──────────────────

def en_hilo(func):
    """Decorator para ejecutar funciones en un hilo separado."""
    def wrapper(*args, **kwargs):
        t = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
        t.start()
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


# ─── APP PRINCIPAL ────────────────────────────────────────────────────────────

def main(page: ft.Page):
    page.title       = "Juana Cash"
    page.theme_mode  = ft.ThemeMode.DARK
    page.bgcolor     = "#080E1C"
    page.padding     = 0
    page.spacing     = 0

    # ── SPLASH SCREEN ────────────────────────────────────────────────────────
    import time
    progress_bar = ft.ProgressBar(value=0, width=float("inf"), height=5,
                                  color="#27AE60", bgcolor="#0d1f35")
    lbl_pct    = ft.Text("0%", size=13, weight="bold", color="#1B9FD4", text_align="center")
    lbl_estado = ft.Text("Iniciando...", size=11, color="#4a7a9a", text_align="center")

    page.add(ft.Container(
        content=ft.Column([
            ft.Container(expand=True),
            ft.Text("$↗", size=60, weight="bold", color="#27AE60", text_align="center"),
            ft.Container(height=6),
            ft.Text("JUANA CA$H", size=36, weight="w900", color="white", text_align="center"),
            ft.Text("GESTIÓN DE CAJA", size=12, weight="bold", color="#27AE60", text_align="center"),
            ft.Container(height=6),
            ft.Divider(color="#1B3A5C"),
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

    for valor, texto in [(0.1,"Verificando configuración..."),(0.25,"Conectando sistema..."),
                         (0.45,"Cargando productos..."),(0.65,"Preparando interfaz..."),
                         (0.85,"Verificando conexión..."),(1.0,"¡Sistema listo!")]:
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
    # Cache local de productos — carga una vez, búsqueda instantánea
    productos_cache  = []
    productos_codigo = {}  # barcode → producto

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
        if hasattr(page, "open"): page.open(dlg)
        else: page.dialog = dlg; dlg.open = True; page.update()

    def cerrar_dlg(dlg):
        if hasattr(page, "close"): page.close(dlg)
        else: dlg.open = False; page.update()

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
    lbl_total    = ft.Text("$ 0.00", size=44, weight="w900", color="#10B981")
    lbl_tickets  = ft.Text("0 tickets hoy", size=14, color="#94A3B8")
    lista_movs   = ft.Column(spacing=8, scroll=ft.ScrollMode.ALWAYS, height=280)
    lbl_dashboard_err = ft.Text("", color="#EF4444", size=12)

    @en_hilo
    def cargar_dashboard(e=None):
        lbl_ip_status.value = f"📡 {leer_ip()}"
        data = api_get("/reportes/hoy")
        if data:
            lbl_total.value   = f"$ {data.get('total_vendido', 0):,.2f}"
            lbl_total.color   = "#10B981"
            cant = data.get("cantidad_ventas", 0)
            lbl_tickets.value = f"{cant} ticket{'s' if cant != 1 else ''} hoy"
            lbl_dashboard_err.value = ""
            lista_movs.controls.clear()
            for v in data.get("ventas", [])[:12]:
                metodo = v.get("metodo_pago", "efectivo").upper()
                total  = float(v.get("total", 0))
                lista_movs.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text("🛍️", size=18),
                            ft.Text(metodo, weight="bold", expand=True, size=13),
                            ft.Text(f"${total:,.0f}", weight="bold", color="#38BDF8", size=15),
                        ]),
                        bgcolor="#1E293B", padding=12, border_radius=10
                    )
                )
        else:
            lbl_total.value   = "Sin conexión"
            lbl_total.color   = "#EF4444"
            lbl_dashboard_err.value = f"No se pudo conectar a {get_api_url()}"
        page.update()

    view_dashboard = ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Text("CAJA DEL DÍA", weight="bold", color="#94A3B8", size=12),
                    lbl_total, lbl_tickets, lbl_dashboard_err
                ], horizontal_alignment="center"),
                padding=20, border_radius=16, bgcolor="#0F172A"
            ),
            ft.Text("Últimos movimientos", weight="w600", size=15),
            lista_movs,
            ft.ElevatedButton(
                "🔄 ACTUALIZAR", on_click=cargar_dashboard,
                width=float("inf"), height=48,
                bgcolor="#3B82F6", color="white",
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
            )
        ], spacing=12),
        padding=16, visible=True, expand=True
    )

    # ── PANTALLA 2: COBRAR ────────────────────────────────────────────────────
    lbl_aviso    = ft.Text("", size=13, weight="bold")
    lista_compra = ft.Column(spacing=8, scroll=ft.ScrollMode.ALWAYS, height=240)
    lbl_total_c  = ft.Text("$ 0.00", size=34, weight="w900", color="#F43F5E")
    in_scan      = ft.TextField(
        label="Escanear o buscar...", filled=True, border_color="transparent",
        border_radius=12, content_padding=16, bgcolor="#1E293B", expand=True
    )
    in_cliente   = inp("Cliente (opcional)", w=160)
    drop_metodo  = ft.Dropdown(
        options=[
            ft.dropdown.Option(key="efectivo",        text="💵 Efectivo"),
            ft.dropdown.Option(key="tarjeta",         text="💳 Tarjeta"),
            ft.dropdown.Option(key="mercadopago_qr",  text="📱 QR/MP"),
            ft.dropdown.Option(key="transferencia",   text="🏦 Transf."),
            ft.dropdown.Option(key="fiado",           text="💸 Fiado"),
        ],
        value="efectivo", width=150, border_radius=10,
        filled=True, bgcolor="#1E293B", border_color="transparent"
    )

    # Cliente seleccionado para fiado
    cliente_fiado = {"id": None, "nombre": ""}
    lbl_cliente_fiado = ft.Text("", size=12, color="#F59E0B")
    panel_buscar_cliente = ft.Container(visible=False)

    def on_metodo_change(e):
        if drop_metodo.value == "fiado":
            panel_buscar_cliente.visible = True
        else:
            panel_buscar_cliente.visible = False
            cliente_fiado["id"] = None
            cliente_fiado["nombre"] = ""
            lbl_cliente_fiado.value = ""
        page.update()

    drop_metodo.on_change = on_metodo_change

    def buscar_cliente(e=None):
        q = in_buscar_cliente.value.strip()
        if not q: return

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
                    deuda = float(c.get("deuda_actual") or 0)
                    txt = f"{nombre}"
                    if deuda > 0:
                        txt += f"  💸 debe ${deuda:,.0f}"
                    lista_clientes.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Text(txt, expand=True, size=12, color="white"),
                            ]),
                            bgcolor="#1E293B", padding=10, border_radius=8,
                            on_click=lambda e, cl=c: seleccionar_cliente(cl),
                        )
                    )
            else:
                lista_clientes.controls.append(
                    ft.Text("Sin resultados", color="#94A3B8", size=12)
                )
            page.update()

        import threading
        threading.Thread(target=_buscar, daemon=True).start()

    def seleccionar_cliente(c):
        cliente_fiado["id"] = c["id"]
        cliente_fiado["nombre"] = c.get("nombre", "")
        lbl_cliente_fiado.value = f"✅ Cliente: {cliente_fiado['nombre']}"
        lista_clientes.controls.clear()
        in_buscar_cliente.value = ""
        page.update()

    in_buscar_cliente = ft.TextField(
        label="Buscar cliente por nombre",
        filled=True, border_color="transparent",
        border_radius=10, content_padding=12,
        bgcolor="#1E293B", expand=True,
        on_submit=buscar_cliente
    )
    lista_clientes = ft.Column(spacing=4, scroll=ft.ScrollMode.ALWAYS, height=150)

    panel_buscar_cliente.content = ft.Column([
        ft.Row([in_buscar_cliente,
                ft.ElevatedButton("🔍", on_click=buscar_cliente,
                    bgcolor="#556EE6", color="white", height=44, width=50)]),
        lbl_cliente_fiado,
        lista_clientes,
    ], spacing=6)
    panel_buscar_cliente.bgcolor = "#0F172A"
    panel_buscar_cliente.border_radius = 10
    panel_buscar_cliente.padding = 10
    btn_recuperar = ft.ElevatedButton("⏳ (0)", bgcolor="#334155", color="white", visible=False)

    def recalc():
        t = sum(i["p"] for i in carrito)
        lbl_total_c.value = f"$ {t:,.0f}"
        page.update()

    def pausar(e):
        if not carrito: return
        nom = in_cliente.value.strip() or f"Cliente {len(tickets_espera)+1}"
        tickets_espera.append({"nombre": nom, "items": list(carrito)})
        carrito.clear(); lista_compra.controls.clear()
        in_cliente.value = ""
        btn_recuperar.text = f"⏳ ({len(tickets_espera)})"
        btn_recuperar.visible = True
        lbl_aviso.value = f"Pausado: {nom}"; lbl_aviso.color = "#F59E0B"
        recalc()

    dlg_pausados = ft.AlertDialog(modal=True)
    def cargar_pausado(t):
        carrito.clear(); lista_compra.controls.clear()
        carrito.extend(t["items"])
        for i in carrito: agregar_ui(i)
        tickets_espera.remove(t)
        btn_recuperar.text    = f"⏳ ({len(tickets_espera)})"
        btn_recuperar.visible = len(tickets_espera) > 0
        cerrar_dlg(dlg_pausados); recalc()

    def ver_pausados(e):
        if not tickets_espera: return
        cols = [ft.ElevatedButton(
            f"🛒 {t['nombre']} ({len(t['items'])} prod)",
            on_click=lambda ev, tk=t: cargar_pausado(tk),
            height=48, width=260, bgcolor="#1E293B", color="white"
        ) for t in tickets_espera]
        dlg_pausados.content = ft.Column(cols, tight=True)
        dlg_pausados.title   = ft.Text("Ventas pausadas")
        dlg_pausados.actions = [ft.TextButton("Cerrar", on_click=lambda ev: cerrar_dlg(dlg_pausados))]
        abrir_dlg(dlg_pausados)

    btn_recuperar.on_click = ver_pausados

    def setval(d, k, v): d[k] = v

    def agregar_ui(data):
        # Inicializar cantidad y precio unitario
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
            in_p.value = f"{data['p']:.0f}"
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
                in_p
            ], spacing=4),
            bgcolor="#1E293B", padding=8, border_radius=12
        )
        lista_compra.controls.append(fila)

    # Panel de resultados de búsqueda (inline, no dialog)
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
                p = matches[0]
                dat = {"n": p["nombre"], "p": float(p.get("precio_venta") or 0), "producto_id": p["id"]}
                carrito.append(dat); agregar_ui(dat)
                in_scan.value = ""; lbl_aviso.value = ""
                ocultar_resultados()
                recalc()
                return

            # Múltiples — mostrar panel inline
            def seleccionar(prod):
                dat = {"n": prod["nombre"], "p": float(prod.get("precio_venta") or 0), "producto_id": prod["id"]}
                carrito.append(dat); agregar_ui(dat)
                in_scan.value = ""; lbl_aviso.value = ""
                ocultar_resultados()
                recalc()

            filas = [
                ft.Container(
                    content=ft.Row([
                        ft.Text(p["nombre"], expand=True, size=12, weight="bold", color="white"),
                        ft.Text(f"${float(p.get('precio_venta') or 0):,.0f}",
                               color="#38BDF8", size=13, weight="bold"),
                    ]),
                    bgcolor="#1E293B", padding=ft.padding.symmetric(horizontal=12, vertical=10),
                    border_radius=8, on_click=lambda e, prod=p: seleccionar(prod),
                )
                for p in matches[:15]
            ]
            filas.append(
                ft.TextButton("✕ Cancelar", on_click=lambda e: ocultar_resultados())
            )

            panel_resultados.content = ft.Column(
                controls=filas, scroll=ft.ScrollMode.ALWAYS,
                spacing=4, height=min(len(matches) * 50, 300)
            )
            panel_resultados.bgcolor = "#0F172A"
            panel_resultados.border_radius = 10
            panel_resultados.padding = 8
            panel_resultados.visible = True
            lbl_aviso.value = f"🔍 {len(matches)} resultados — tocá para agregar"
            lbl_aviso.color = "#94A3B8"
            page.update()

        import threading
        threading.Thread(target=_buscar, daemon=True).start()

    in_scan.on_submit = buscar_prod

    view_cobrar = ft.Container(
        content=ft.Column([
            lbl_aviso,
            ft.Row([in_cliente, ft.ElevatedButton("⏸️", on_click=pausar, bgcolor="#F59E0B", color="black"), btn_recuperar]),
            ft.Row([in_scan, ft.ElevatedButton("➕", on_click=buscar_prod, bgcolor="#10B981", color="white", height=48)]),
            panel_resultados,
            ft.Row([lbl_total_c, drop_metodo], alignment="spaceBetween"),
            ft.ElevatedButton(
                "👤 Vincular cliente para Fiado", bgcolor="#F59E0B", color="black",
                width=float("inf"), height=44,
                on_click=lambda e: (setattr(panel_buscar_cliente, 'visible', not panel_buscar_cliente.visible), page.update())
            ),
            panel_buscar_cliente,
            lista_compra,
            ft.ElevatedButton(
                "🧾 COBRAR", width=float("inf"), height=58,
                bgcolor="#F43F5E", color="white",
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=14)),
                on_click=lambda e: ir_ticket()
            )
        ], spacing=10),
        padding=16, visible=False, expand=True
    )

    # ── PANTALLA 3: CONFIRMAR TICKET ─────────────────────────────────────────
    lista_ticket     = ft.Column(scroll=ft.ScrollMode.ALWAYS, height=180)
    in_pago          = inp("¿Con cuánto paga?", kb="number")
    lbl_vuelto       = ft.Text("$ 0.00", size=28, weight="w900", color="#EF4444")
    lbl_ticket_total = ft.Text("$ 0.00", size=34, weight="w900", color="#F43F5E")
    lbl_cobrar_status = ft.Text("", size=13, weight="bold")
    row_vuelto        = ft.Column(visible=False)

    def calc_vuelto(e):
        try:
            v = float(in_pago.value) - sum(i["p"] for i in carrito)
            lbl_vuelto.value = f"VUELTO: ${v:,.0f}" if v >= 0 else "FALTA PLATA"
            lbl_vuelto.color = "#10B981" if v >= 0 else "#EF4444"
        except: lbl_vuelto.value = "$ 0.00"
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
                "producto_id":   i["producto_id"],
                "cantidad":      i.get("cant", 1),
                "precio_unitario": i.get("precio_unit", i["p"]),
                "descuento":     0
            }
            for i in carrito if i.get("producto_id") and i["producto_id"] != 0
        ]
        if not items_api:
            items_api = [{"producto_id": 1, "cantidad": 1, "precio_unitario": tot, "descuento": 0}]

        lbl_cobrar_status.value = "⏳ Registrando..."
        lbl_cobrar_status.color = "#94A3B8"
        page.update()

        data = api_post("/ventas/", json_data={
            "usuario_id": 1,
            "cliente_id": cliente_fiado["id"] if drop_metodo.value == "fiado" else None,
            "items":      items_api,
            "pagos":      [{"metodo": metodo, "monto": tot}],
            "descuento":  0,
            "origen":     "celular"
        })
        if data:
            num = data.get("numero", "?")
            carrito.clear(); lista_compra.controls.clear()
            in_pago.value = ""; in_cliente.value = ""
            cliente_fiado["id"] = None; cliente_fiado["nombre"] = ""
            lbl_cliente_fiado.value = ""
            panel_buscar_cliente.visible = False
            drop_metodo.value = "efectivo"
            view_ticket.visible  = False
            view_cobrar.visible  = True
            lbl_aviso.value      = f"✅ TICKET #{num} COBRADO!"
            lbl_aviso.color      = "#10B981"
            lbl_cobrar_status.value = ""
            recalc()
            cargar_dashboard()
        else:
            lbl_cobrar_status.value = f"❌ Error — verificá la conexión a {get_api_url()}"
            lbl_cobrar_status.color = "#EF4444"
        page.update()

    view_ticket = ft.Container(
        content=ft.Column([
            ft.Text("🧾 CONFIRMAR VENTA", size=22, weight="w900", color="#94A3B8"),
            ft.Divider(color="#334155"),
            lista_ticket,
            ft.Divider(color="#334155"),
            ft.Row([ft.Text("TOTAL:", weight="bold", size=16), lbl_ticket_total], alignment="spaceBetween"),
            row_vuelto, lbl_cobrar_status,
            ft.Row([
                ft.ElevatedButton("🔙 ATRÁS", expand=True, height=52, bgcolor="#334155", color="white",
                    on_click=lambda _: (setattr(view_ticket, "visible", False), setattr(view_cobrar, "visible", True), page.update())),
                ft.ElevatedButton("✅ COBRAR", expand=True, height=52, bgcolor="#10B981", color="white",
                    on_click=cobrar_final),
            ], spacing=10)
        ], spacing=10),
        padding=16, visible=False, expand=True
    )

    def ir_ticket():
        if not carrito: return
        lista_ticket.controls = [ft.Row([ft.Text(i["n"], expand=True, size=12), ft.Text(f"${i['p']:,.0f}")]) for i in carrito]
        tot = sum(i["p"] for i in carrito)
        lbl_ticket_total.value = f"$ {tot:,.0f}"
        lbl_cobrar_status.value = ""
        row_vuelto.visible = (drop_metodo.value == "efectivo")
        in_pago.value = ""; lbl_vuelto.value = "$ 0.00"
        view_cobrar.visible = False; view_ticket.visible = True
        page.update()

    # ── PANTALLA 4: OFERTAS ───────────────────────────────────────────────────
    lista_ofertas_ui = ft.Column(spacing=8, scroll=ft.ScrollMode.ALWAYS, height=300)
    lbl_oferta_status = ft.Text("", size=13, weight="bold")
    in_texto_oferta   = inp("Texto de la oferta", "Ej: 2x1 en Gaseosas 🎉")
    color_sel         = {"fondo": "#e74c3c", "texto": "#ffffff"}
    lbl_color_preview = ft.Container(
        content=ft.Text("Vista previa del texto", color="#ffffff", weight="bold", text_align="center"),
        bgcolor="#e74c3c", border_radius=10, padding=14, width=float("inf")
    )

    def set_color_fondo(e):
        colores = ["#e74c3c", "#27ae60", "#3498db", "#9b59b6", "#f39c12", "#1abc9c", "#e91e63", "#ff5722"]
        idx = (colores.index(color_sel["fondo"]) + 1) % len(colores) if color_sel["fondo"] in colores else 0
        color_sel["fondo"] = colores[idx]
        btn_color_fondo.bgcolor = colores[idx]
        lbl_color_preview.bgcolor = colores[idx]
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
            in_texto_oferta.value = ""
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
                    preview = o["contenido"][:30] + ("..." if len(o["contenido"]) > 30 else "")
                    texto_item = f"📝  {preview}"
                    color_item = o.get("color_fondo", "#e74c3c")
                else:
                    texto_item = f"📷  {os.path.basename(o['contenido'])}"
                    color_item = "#334155"

                lista_ofertas_ui.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text(texto_item, expand=True, size=12, color="white"),
                            ft.ElevatedButton("🗑", bgcolor="#EF4444", color="white", width=44,
                                height=36, on_click=lambda _, idx=i: borrar_oferta(idx))
                        ]),
                        bgcolor=color_item, padding=ft.padding.symmetric(horizontal=12, vertical=8),
                        border_radius=10
                    )
                )
            if not data:
                lista_ofertas_ui.controls.append(ft.Text("Sin ofertas todavía", color="#94A3B8", size=13))
        else:
            lista_ofertas_ui.controls.append(
                ft.Text(f"Sin conexión — verificá que la PC esté en {get_api_url()}", color="#EF4444", size=12)
            )
        page.update()

    # ── Subida de imágenes con tkinter (compatible con cualquier Flet) ────────
    def seleccionar_y_subir_imagen(e):
        def _pick_and_upload():
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            ruta = filedialog.askopenfilename(
                title="Elegí una imagen para la oferta",
                filetypes=[("Imágenes", "*.jpg *.jpeg *.png *.webp *.bmp")]
            )
            root.destroy()
            if not ruta:
                return

            lbl_oferta_status.value = "⏳ Subiendo imagen..."
            lbl_oferta_status.color = "#94A3B8"
            page.update()
            try:
                with open(ruta, "rb") as f:
                    r = requests.post(
                        f"{get_api_url()}/ofertas/imagen",
                        files={"archivo": (os.path.basename(ruta), f, "image/jpeg")},
                        timeout=15
                    )
                if r.status_code == 200:
                    data = r.json()
                    lbl_oferta_status.value = f"✅ Imagen subida! ({data.get('total', 0)} ofertas)"
                    lbl_oferta_status.color = "#10B981"
                    cargar_lista_ofertas()
                else:
                    lbl_oferta_status.value = f"❌ Error del servidor: {r.status_code}"
                    lbl_oferta_status.color = "#EF4444"
            except Exception as ex:
                lbl_oferta_status.value = f"❌ Error: {ex}"
                lbl_oferta_status.color = "#EF4444"
            page.update()

        threading.Thread(target=_pick_and_upload, daemon=True).start()

    view_ofertas = ft.Container(
        content=ft.Column([
            ft.Text("🏷️ SUBIR OFERTAS A LA PC", size=20, weight="w900"),
            ft.Text("Las ofertas se muestran en la pantalla de ventas", color="#94A3B8", size=12),
            lbl_color_preview,
            in_texto_oferta,
            ft.Row([btn_color_fondo,
                    ft.ElevatedButton("📤 SUBIR TEXTO", bgcolor="#556EE6", color="white",
                        on_click=agregar_oferta_texto, expand=True, height=44)]),
            ft.ElevatedButton(
                "📷 SUBIR IMAGEN", bgcolor="#E91E63", color="white",
                on_click=seleccionar_y_subir_imagen,
                width=float("inf"), height=48,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
            ),
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

    # ── PANTALLA 5: CONFIG ────────────────────────────────────────────────────
    in_ip = ft.TextField(
        label="IP de la PC (ej: 192.168.1.100)",
        value=leer_ip(),
        filled=True, border_color="transparent",
        border_radius=12, content_padding=16, bgcolor="#1E293B",
        keyboard_type=ft.KeyboardType.URL
    )
    lbl_config_status = ft.Text("", size=13)

    @en_hilo
    def guardar_config(e=None):
        ip = in_ip.value.strip().replace("http://", "").replace(":8000", "")
        guardar_ip(ip)
        lbl_config_status.value = "⏳ Probando conexión..."
        lbl_config_status.color = "#94A3B8"
        page.update()
        data = api_get("/")
        if data:
            lbl_config_status.value = f"✅ Conectado a {ip}:8000"
            lbl_config_status.color = "#10B981"
            lbl_ip_status.value = f"📡 {ip}"
        else:
            lbl_config_status.value = f"❌ No se pudo conectar a {ip}:8000\nVerificá que la PC esté encendida y en la misma WiFi"
            lbl_config_status.color = "#EF4444"
        page.update()

    view_config = ft.Container(
        content=ft.Column([
            ft.Text("⚙️ CONFIGURACIÓN", size=20, weight="w900"),
            ft.Text("Ingresá la IP local de la PC donde corre el sistema", color="#94A3B8", size=12),
            ft.Container(
                content=ft.Column([
                    ft.Text("¿Cómo saber la IP de la PC?", weight="bold", color="#38BDF8", size=13),
                    ft.Text("En la PC abrí CMD y escribí:", color="#94A3B8", size=12),
                    ft.Container(
                        content=ft.Text("ipconfig", color="#10B981", font_family="monospace", size=14),
                        bgcolor="#0F172A", padding=10, border_radius=8
                    ),
                    ft.Text("Buscá 'Dirección IPv4' (ej: 192.168.1.100)", color="#94A3B8", size=12),
                ]),
                bgcolor="#1E293B", padding=14, border_radius=12
            ),
            in_ip,
            ft.ElevatedButton(
                "💾 GUARDAR Y PROBAR", on_click=guardar_config,
                width=float("inf"), height=48,
                bgcolor="#556EE6", color="white",
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
            ),
            lbl_config_status,
        ], spacing=12),
        padding=16, visible=False, expand=True
    )

    # ── NAVEGACIÓN ────────────────────────────────────────────────────────────
    vistas = {
        "D": view_dashboard,
        "C": view_cobrar,
        "O": view_ofertas,
        "S": view_config,
    }

    def nav(e):
        key = e.control.data
        for k, v in vistas.items():
            v.visible = (k == key)
        view_ticket.visible = False
        lbl_aviso.value = ""
        if key == "D": cargar_dashboard()
        if key == "O": cargar_lista_ofertas()
        page.update()

    nav_bar = ft.Container(
        content=ft.Row([
            ft.ElevatedButton("📊", data="D", on_click=nav, expand=True, height=56, bgcolor="#1E293B", color="white",
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=0))),
            ft.ElevatedButton("🛒", data="C", on_click=nav, expand=True, height=56, bgcolor="#1E293B", color="white",
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=0))),
            ft.ElevatedButton("🏷️", data="O", on_click=nav, expand=True, height=56, bgcolor="#1E293B", color="white",
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=0))),
            ft.ElevatedButton("⚙️", data="S", on_click=nav, expand=True, height=56, bgcolor="#1E293B", color="white",
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=0))),
        ], spacing=1),
        bgcolor="#0F172A", padding=ft.padding.only(bottom=20)
    )

    all_views = ft.Column(
        [view_dashboard, view_cobrar, view_ticket, view_ofertas, view_config],
        expand=True
    )

    page.add(app_bar, all_views, nav_bar)
    cargar_dashboard()
    cargar_cache_productos()  # Carga productos en background al arrancar


ft.app(target=main)
