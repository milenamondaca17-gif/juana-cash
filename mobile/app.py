import flet as ft
import requests
from datetime import datetime

API_URL = "http://127.0.0.1:8000"

def main(page: ft.Page):
    page.title = "Juana Cash Mobile"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0B1120"
    page.padding = 0
    page.spacing = 0

    carrito = []
    tickets_espera = []

    def abrir_ventana(dlg):
        if hasattr(page, 'open'): page.open(dlg)
        else: page.dialog = dlg; dlg.open = True; page.update()

    def cerrar_ventana(dlg):
        if hasattr(page, 'close'): page.close(dlg)
        else: dlg.open = False; page.update()

    def api_get(path, params=None):
        try:
            r = requests.get(f"{API_URL}{path}", params=params, timeout=5)
            if r.status_code == 200:
                return r.json(), None
            return None, f"Error {r.status_code}"
        except Exception as e:
            return None, str(e)

    def api_post(path, json=None):
        try:
            r = requests.post(f"{API_URL}{path}", json=json, timeout=8)
            if r.status_code == 200:
                return r.json(), None
            return None, r.text
        except Exception as e:
            return None, str(e)

    def api_put(path, json=None):
        try:
            r = requests.put(f"{API_URL}{path}", json=json, timeout=5)
            if r.status_code == 200:
                return r.json(), None
            return None, r.text
        except Exception as e:
            return None, str(e)

    # ─── BARRA SUPERIOR ────────────────────────────────────────────────────────

    app_bar = ft.Container(
        content=ft.Row(
            [ft.Text("JUANA CASH", weight="w900", size=22, color="#F43F5E")],
            alignment="center"
        ),
        padding=20, bgcolor="#0F172A"
    )

    def estilo_input(label, hint="", w=None):
        return {
            "label": label, "hint_text": hint, "width": w,
            "filled": True, "border_color": "transparent",
            "border_radius": 12, "content_padding": 20,
            "bgcolor": "#1E293B"
        }

    # ─── PANTALLA 1: DASHBOARD ─────────────────────────────────────────────────

    lbl_total_hoy   = ft.Text("$ 0.00", size=45, weight="w900", color="#10B981")
    lbl_tickets_hoy = ft.Text("0 tickets", size=16, color="#94A3B8")
    lista_movimientos = ft.Column(spacing=10, scroll=ft.ScrollMode.ALWAYS, height=300)

    def refrescar_ventas(e=None):
        data, err = api_get("/reportes/hoy")
        if err or not data:
            lbl_total_hoy.value = "Sin conexión"
            lbl_total_hoy.color = "#EF4444"
            page.update()
            return

        lbl_total_hoy.value  = f"$ {data.get('total_vendido', 0):,.2f}"
        lbl_total_hoy.color  = "#10B981"
        cant = data.get("cantidad_ventas", 0)
        lbl_tickets_hoy.value = f"{cant} ticket{'s' if cant != 1 else ''}"

        lista_movimientos.controls.clear()
        for v in data.get("ventas", [])[:10]:
            metodo = v.get("metodo_pago", "efectivo").upper()
            total  = float(v.get("total", 0))
            lista_movimientos.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text("🛍️", size=20),
                        ft.Text(metodo, weight="bold", expand=True),
                        ft.Text(f"${total:,.2f}", size=16, weight="bold", color="#38BDF8")
                    ]),
                    bgcolor="#1E293B", padding=15, border_radius=12
                )
            )
        page.update()

    view_ventas = ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Column(
                    [ft.Text("CAJA DEL DÍA", weight="bold", color="#94A3B8"),
                     lbl_total_hoy, lbl_tickets_hoy],
                    horizontal_alignment="center"
                ),
                padding=20, border_radius=20, bgcolor="#0F172A"
            ),
            ft.Text("Últimos movimientos", weight="w600", size=16),
            lista_movimientos,
            ft.ElevatedButton(
                "🔄 ACTUALIZAR DATOS", on_click=refrescar_ventas,
                width=float("inf"), height=50,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                bgcolor="#3B82F6", color="white"
            )
        ]), padding=20, visible=True, expand=True
    )

    # ─── PANTALLA 2: COBRAR ────────────────────────────────────────────────────

    lbl_aviso_caja    = ft.Text("", size=14, weight="bold")
    lista_compra_ui   = ft.Column(spacing=10, scroll=ft.ScrollMode.ALWAYS, height=250)
    lbl_tot_caja      = ft.Text("$ 0.00", size=35, weight="w900", color="#F43F5E")
    in_scanner        = ft.TextField(**estilo_input("Escanear o buscar..."), expand=True)
    in_cliente        = ft.TextField(**estilo_input("Nombre Cliente", w=160), dense=True)
    drop_metodo       = ft.Dropdown(
        options=[
            ft.dropdown.Option("efectivo"),
            ft.dropdown.Option("tarjeta"),
            ft.dropdown.Option("mercadopago_qr"),
            ft.dropdown.Option("transferencia")
        ],
        value="efectivo", width=160, border_radius=12,
        filled=True, bgcolor="#1E293B", border_color="transparent"
    )

    def calcular_total_caja():
        t = sum(item["p"] for item in carrito)
        lbl_tot_caja.value = f"$ {t:,.2f}"
        page.update()

    # --- PAUSA ---
    btn_recuperar = ft.ElevatedButton("⏳ (0)", bgcolor="#334155", color="white", visible=False)

    def pausar_venta(e):
        if not carrito: return
        nom = in_cliente.value.strip() or f"Cliente {len(tickets_espera)+1}"
        tickets_espera.append({"nombre": nom, "items": carrito.copy()})
        carrito.clear(); lista_compra_ui.controls.clear(); in_cliente.value = ""
        btn_recuperar.text = f"⏳ ({len(tickets_espera)})"; btn_recuperar.visible = True
        lbl_aviso_caja.value = f"Venta de {nom} pausada"; lbl_aviso_caja.color = "#F59E0B"
        calcular_total_caja()

    dlg_espera = ft.AlertDialog(modal=True)

    def cargar_pausado(t):
        carrito.clear(); lista_compra_ui.controls.clear(); carrito.extend(t["items"])
        for i in carrito: agregar_item_ui(i)
        tickets_espera.remove(t)
        btn_recuperar.text = f"⏳ ({len(tickets_espera)})"
        btn_recuperar.visible = len(tickets_espera) > 0
        cerrar_ventana(dlg_espera); calcular_total_caja()

    def ver_pausados(e):
        if not tickets_espera: return
        cols = [
            ft.ElevatedButton(
                f"🛒 {t['nombre']} ({len(t['items'])} prod)",
                on_click=lambda ev, tk=t: cargar_pausado(tk),
                height=50, width=250, bgcolor="#1E293B", color="white"
            )
            for t in tickets_espera
        ]
        dlg_espera.content = ft.Column(cols, tight=True)
        dlg_espera.title   = ft.Text("Ventas Pausadas")
        dlg_espera.actions = [ft.TextButton("Cerrar", on_click=lambda ev: cerrar_ventana(dlg_espera))]
        abrir_ventana(dlg_espera)

    btn_recuperar.on_click = ver_pausados
    btn_pausa = ft.ElevatedButton("⏸️", on_click=pausar_venta, bgcolor="#F59E0B", color="black")

    # --- BALANZA ---
    dlg_granel    = ft.AlertDialog(modal=True)
    in_gramos     = ft.TextField(**estilo_input("Gramos (Ej: 250)"), keyboard_type="number")
    lbl_granel_res = ft.Text("$ 0.00", size=30, weight="bold", color="#10B981")
    item_granel   = None; input_precio_granel = None

    def calc_g(e):
        try: lbl_granel_res.value = f"$ {((float(in_gramos.value) * item_granel['p_kg']) / 1000):.2f}"
        except: lbl_granel_res.value = "$ 0.00"
        page.update()

    in_gramos.on_change = calc_g

    def ok_g(e):
        if item_granel and input_precio_granel:
            try:
                val = lbl_granel_res.value.replace("$ ", "")
                item_granel["p"] = float(val)
                input_precio_granel.value = val
                calcular_total_caja()
            except: pass
        cerrar_ventana(dlg_granel)

    dlg_granel.actions = [
        ft.TextButton("Cancelar", on_click=lambda e: cerrar_ventana(dlg_granel)),
        ft.TextButton("Confirmar", on_click=ok_g)
    ]

    def abrir_granel(n, p_kg, data, ui):
        nonlocal item_granel, input_precio_granel
        item_granel = data; item_granel["p_kg"] = p_kg; input_precio_granel = ui
        dlg_granel.title   = ft.Text(f"Balanza: {n}", size=18)
        dlg_granel.content = ft.Column(
            [ft.Text(f"Precio x KG: ${p_kg:,.2f}", color="#94A3B8"), in_gramos, lbl_granel_res],
            tight=True
        )
        in_gramos.value = ""; lbl_granel_res.value = "$ 0.00"
        abrir_ventana(dlg_granel)

    def setitem(d, k, v): d[k] = v

    def agregar_item_ui(data):
        in_p = ft.TextField(
            value=f"{data['p']:.2f}", width=80, text_align="right",
            bgcolor="#0F172A", border_color="transparent", filled=True,
            border_radius=8, content_padding=5,
            on_change=lambda e: (setitem(data, "p", float(e.control.value or 0)), calcular_total_caja())
        )
        fila = ft.Container(
            content=ft.Row([
                ft.ElevatedButton(
                    "❌",
                    on_click=lambda _: (carrito.remove(data), lista_compra_ui.controls.remove(fila), calcular_total_caja()),
                    bgcolor="#EF4444", color="white", width=50
                ),
                ft.Text(data["n"], expand=True, weight="bold", size=12),
                ft.ElevatedButton(
                    "⚖️",
                    on_click=lambda _: abrir_granel(data["n"], data["p"], data, in_p),
                    bgcolor="#38BDF8", color="white", width=50
                ),
                in_p
            ]),
            bgcolor="#1E293B", padding=10, border_radius=15
        )
        lista_compra_ui.controls.append(fila)

    def sumar_prod(e):
        lbl_aviso_caja.value = ""
        v = in_scanner.value.strip()
        if not v: return

        data, err = api_get("/productos/buscar", params={"q": v})
        if err:
            lbl_aviso_caja.value = f"⚠️ Sin conexión al servidor"
            lbl_aviso_caja.color = "#EF4444"
        elif data:
            p = data[0]
            dat = {
                "n":           p["nombre"],
                "p":           float(p["precio_venta"] or 0),
                "producto_id": p["id"],
                "pesable":     bool(p.get("pesable", False))
            }
            carrito.append(dat)
            agregar_item_ui(dat)
            in_scanner.value = ""
            in_scanner.focus()
            calcular_total_caja()
        else:
            lbl_aviso_caja.value = f"❌ '{v}' no encontrado."
            lbl_aviso_caja.color = "#EF4444"
        page.update()

    in_scanner.on_submit = sumar_prod

    view_cobrar = ft.Container(
        content=ft.Column([
            lbl_aviso_caja,
            ft.Row([in_cliente, btn_pausa, btn_recuperar], alignment="spaceBetween"),
            ft.Row([in_scanner, ft.ElevatedButton("➕", on_click=sumar_prod, bgcolor="#10B981", color="white", height=50)]),
            lista_compra_ui,
            ft.Row([lbl_tot_caja, drop_metodo], alignment="spaceBetween"),
            ft.ElevatedButton(
                "🧾 GENERAR TICKET", width=float("inf"), height=60,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15)),
                bgcolor="#F43F5E", color="white",
                on_click=lambda e: ir_ticket(e)
            )
        ]), padding=20, visible=False, expand=True
    )

    # ─── PANTALLA 3: TICKET ────────────────────────────────────────────────────

    lista_ticket     = ft.Column(scroll=ft.ScrollMode.ALWAYS, height=200)
    in_pago          = ft.TextField(**estilo_input("¿Con cuánto paga?", w=150), keyboard_type="number", text_align="right")
    lbl_vuelto       = ft.Text("$ 0.00", size=30, weight="w900", color="#EF4444")
    lbl_ticket_total = ft.Text("$ 0.00", size=35, weight="w900", color="#F43F5E")
    row_vuelto       = ft.Column(visible=False)
    lbl_cobrar_status = ft.Text("", size=14, weight="bold")

    def cal_vuelto(e):
        try:
            v = float(in_pago.value) - sum(item["p"] for item in carrito)
            lbl_vuelto.value, lbl_vuelto.color = (
                (f"VUELTO: ${v:,.2f}", "#10B981") if v >= 0 else ("FALTA PLATA", "#EF4444")
            )
        except: lbl_vuelto.value = "$ 0.00"
        page.update()

    in_pago.on_change = cal_vuelto
    row_vuelto.controls = [
        ft.Divider(color="#334155"),
        ft.Row([ft.Text("SU PAGO:"), in_pago], alignment="spaceBetween"),
        ft.Row([ft.Text("VUELTO:", weight="bold"), lbl_vuelto], alignment="spaceBetween")
    ]

    def cobrar_final(e):
        tot    = sum(item["p"] for item in carrito)
        metodo = drop_metodo.value or "efectivo"

        # Armar los items para la API — solo los que tienen producto_id real
        items_api = [
            {
                "producto_id": item["producto_id"],
                "cantidad":    1,
                "precio_unitario": item["p"],
                "descuento":   0
            }
            for item in carrito if item.get("producto_id") and item["producto_id"] != 0
        ]

        # Si no hay items con ID (ej: todo ingresado manual), usar el producto 1 como genérico
        if not items_api:
            items_api = [{"producto_id": 1, "cantidad": 1, "precio_unitario": tot, "descuento": 0}]

        pagos_api = [{"metodo": metodo, "monto": tot}]

        payload = {
            "usuario_id": 1,
            "items":      items_api,
            "pagos":      pagos_api,
            "descuento":  0
        }

        lbl_cobrar_status.value = "⏳ Registrando..."
        lbl_cobrar_status.color = "#94A3B8"
        page.update()

        data, err = api_post("/ventas/", json=payload)

        if err:
            lbl_cobrar_status.value = f"❌ Error: {err[:80]}"
            lbl_cobrar_status.color = "#EF4444"
            page.update()
            return

        # Éxito
        ticket_num = data.get("numero", "?")
        carrito.clear(); lista_compra_ui.controls.clear()
        in_pago.value = ""; in_cliente.value = ""
        view_ticket.visible = False; view_cobrar.visible = True
        lbl_aviso_caja.value = f"✅ TICKET #{ticket_num} COBRADO!"
        lbl_aviso_caja.color = "#10B981"
        lbl_cobrar_status.value = ""
        calcular_total_caja()
        refrescar_ventas()

    view_ticket = ft.Container(
        content=ft.Column([
            ft.Text("🧾 RESUMEN DE VENTA", size=24, weight="w900", color="#94A3B8"),
            ft.Divider(color="#334155"),
            lista_ticket,
            ft.Divider(color="#334155"),
            ft.Row([ft.Text("TOTAL:", weight="bold"), lbl_ticket_total], alignment="spaceBetween"),
            row_vuelto,
            lbl_cobrar_status,
            ft.Container(height=10),
            ft.Row([
                ft.ElevatedButton(
                    "🔙 ATRÁS",
                    on_click=lambda _: (
                        setattr(view_ticket, "visible", False),
                        setattr(view_cobrar, "visible", True),
                        page.update()
                    ),
                    expand=True, height=55, bgcolor="#334155", color="white"
                ),
                ft.ElevatedButton(
                    "✅ FINALIZAR",
                    on_click=cobrar_final,
                    expand=True, height=55, bgcolor="#10B981", color="white"
                )
            ], spacing=10)
        ]), padding=20, visible=False, expand=True
    )

    def ir_ticket(e):
        if not carrito: return
        lista_ticket.controls = [
            ft.Row([ft.Text(i["n"], expand=True), ft.Text(f"${i['p']:.2f}")])
            for i in carrito
        ]
        tot_ticket = sum(i["p"] for i in carrito)
        lbl_ticket_total.value = f"$ {tot_ticket:,.2f}"
        lbl_cobrar_status.value = ""

        if drop_metodo.value == "efectivo":
            row_vuelto.visible = True; in_pago.value = ""; lbl_vuelto.value = "$ 0.00"
        else:
            row_vuelto.visible = False

        view_cobrar.visible = False; view_ticket.visible = True
        page.update()

    # ─── PANTALLA 4: PRECIOS ───────────────────────────────────────────────────

    lbl_stk   = ft.Text("", weight="bold")
    in_b      = ft.TextField(**estilo_input("Buscar producto para PC"))
    in_c      = ft.TextField(**estilo_input("Código"), read_only=True)
    in_n      = ft.TextField(**estilo_input("Nombre"), read_only=True)
    in_p_edit = ft.TextField(**estilo_input("Precio $"), keyboard_type="number")
    item_edit = {"id": None, "c": "", "n": ""}

    def bus_edit(e):
        q = in_b.value.strip()
        if not q: return
        data, err = api_get("/productos/buscar", params={"q": q})
        if err:
            lbl_stk.value = f"⚠️ Sin conexión"; lbl_stk.color = "#EF4444"
        elif data:
            p = data[0]
            item_edit["id"] = p["id"]
            item_edit["c"]  = p.get("codigo_barra") or ""
            item_edit["n"]  = p["nombre"]
            in_c.value      = item_edit["c"]
            in_n.value      = item_edit["n"]
            in_p_edit.value = str(float(p["precio_venta"]))
            lbl_stk.value   = f"Editando: {p['nombre']}"
            lbl_stk.color   = "#38BDF8"
        else:
            lbl_stk.value = "No encontrado"; lbl_stk.color = "#EF4444"
        page.update()

    in_b.on_submit = bus_edit

    def update_pc(e):
        if not item_edit["id"]:
            lbl_stk.value = "⚠️ Buscá un producto primero"
            lbl_stk.color = "#F59E0B"
            page.update()
            return
        try:
            nuevo_precio = float(in_p_edit.value or 0)
        except ValueError:
            lbl_stk.value = "⚠️ Precio inválido"; lbl_stk.color = "#EF4444"
            page.update()
            return

        # Usar el endpoint de ajuste individual
        data, err = api_put(f"/productos/{item_edit['id']}", json={
            "nombre":       item_edit["n"],
            "precio_venta": nuevo_precio
        })
        if err:
            lbl_stk.value = f"❌ Error: {err[:60]}"; lbl_stk.color = "#EF4444"
        else:
            lbl_stk.value = "✅ ¡Actualizado!"; lbl_stk.color = "#10B981"
            in_b.value = ""; in_p_edit.value = ""; in_c.value = ""; in_n.value = ""
            item_edit["id"] = None
        page.update()

    view_stock = ft.Container(
        content=ft.Column([
            ft.Text("ACTUALIZAR GÓNDOLA", size=24, weight="w900"),
            in_b,
            ft.ElevatedButton(
                "🔍 BUSCAR", on_click=bus_edit,
                height=50, width=float("inf"), bgcolor="#1E293B", color="white"
            ),
            ft.Divider(color="#334155"),
            lbl_stk, in_c, in_n, in_p_edit,
            ft.Container(height=10),
            ft.ElevatedButton(
                "💾 GUARDAR EN PC", on_click=update_pc,
                width=float("inf"), height=60,
                bgcolor="#F43F5E", color="white"
            )
        ]), padding=20, visible=False, expand=True
    )

    # ─── NAVEGACIÓN ────────────────────────────────────────────────────────────

    def nav(e):
        t = e.control.data
        view_ventas.visible  = (t == "V")
        view_cobrar.visible  = (t == "C")
        view_stock.visible   = (t == "S")
        view_ticket.visible  = False
        lbl_aviso_caja.value = ""
        lbl_stk.value        = ""
        if t == "V": refrescar_ventas()
        page.update()

    nav_bar = ft.Container(
        content=ft.Row([
            ft.ElevatedButton(
                "📊 VENTAS", data="V", on_click=nav, expand=True, height=60,
                bgcolor="#1E293B", color="white",
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=0))
            ),
            ft.ElevatedButton(
                "🛒 COBRAR", data="C", on_click=nav, expand=True, height=60,
                bgcolor="#1E293B", color="white",
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=0))
            ),
            ft.ElevatedButton(
                "📝 PRECIOS", data="S", on_click=nav, expand=True, height=60,
                bgcolor="#1E293B", color="white",
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=0))
            )
        ], spacing=2),
        bgcolor="#0F172A", padding=0
    )

    page.add(
        app_bar,
        ft.Column([view_ventas, view_cobrar, view_ticket, view_stock], expand=True),
        nav_bar
    )
    refrescar_ventas()

ft.app(target=main)
