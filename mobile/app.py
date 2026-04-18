import flet as ft
import sqlite3
import os
from datetime import datetime

# --- CONEXIÓN A LA BASE DE DATOS CENTRAL ---
def get_db_path():
    actual = os.path.dirname(os.path.abspath(__file__))
    raiz = os.path.dirname(actual)
    return os.path.join(raiz, "juana_cash.db")

def ejecutar(sql, params=(), fetch=False):
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute(sql, params)
        res = cursor.fetchall() if fetch else None
        conn.commit()
        conn.close()
        return res, None
    except Exception as e:
        return None, str(e)

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

    # --- DISEÑO: BARRA SUPERIOR FIJA ---
    app_bar = ft.Container(
        content=ft.Row([ft.Text("JUANA CASH", weight="w900", size=22, color="#F43F5E")], alignment="center"),
        padding=20, bgcolor="#0F172A"
    )

    def estilo_input(label, hint="", w=None):
        return {"label": label, "hint_text": hint, "width": w, "filled": True, "border_color": "transparent", "border_radius": 12, "content_padding": 20, "bgcolor": "#1E293B"}

    # --- PANTALLA 1: DASHBOARD ---
    lbl_total_hoy = ft.Text("$ 0.00", size=45, weight="w900", color="#10B981")
    lista_movimientos = ft.Column(spacing=10, scroll=ft.ScrollMode.ALWAYS, height=300)
    
    def refrescar_ventas(e=None):
        res, _ = ejecutar("SELECT SUM(total) FROM ventas WHERE date(fecha) = date('now')", fetch=True)
        total = res[0][0] if res and res[0][0] else 0.0
        lbl_total_hoy.value = f"$ {total:,.2f}"

        lista_movimientos.controls.clear()
        res_rank, _ = ejecutar("SELECT metodo_pago, total, origen FROM ventas WHERE date(fecha) = date('now') ORDER BY id DESC LIMIT 10", fetch=True)
        if res_rank:
            for r in res_rank:
                lista_movimientos.controls.append(
                    ft.Container(
                        content=ft.Row([ft.Text("🛍️", size=20), ft.Text(f"{r[0].upper()}", weight="bold", expand=True), ft.Text(f"${r[1]:,.2f}", size=16, weight="bold", color="#38BDF8")]),
                        bgcolor="#1E293B", padding=15, border_radius=12
                    )
                )
        page.update()

    view_ventas = ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Column([ft.Text("CAJA DEL DÍA", weight="bold", color="#94A3B8"), lbl_total_hoy], horizontal_alignment="center"),
                padding=20, border_radius=20, bgcolor="#0F172A" 
            ),
            ft.Text("Últimos movimientos", weight="w600", size=16),
            lista_movimientos,
            ft.ElevatedButton("🔄 ACTUALIZAR DATOS", on_click=refrescar_ventas, width=float("inf"), height=50, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)), bgcolor="#3B82F6", color="white")
        ]), padding=20, visible=True, expand=True
    )
    # --- PANTALLA 2: COBRAR ---
    lbl_aviso_caja = ft.Text("", size=14, weight="bold")
    lista_compra_ui = ft.Column(spacing=10, scroll=ft.ScrollMode.ALWAYS, height=250)
    lbl_tot_caja = ft.Text("$ 0.00", size=35, weight="w900", color="#F43F5E")
    
    in_scanner = ft.TextField(**estilo_input("Escanear o buscar..."), expand=True)
    in_cliente = ft.TextField(**estilo_input("Nombre Cliente", w=160), dense=True)
    drop_metodo = ft.Dropdown(options=[ft.dropdown.Option("Efectivo"), ft.dropdown.Option("Tarjeta"), ft.dropdown.Option("QR"), ft.dropdown.Option("Transferencia")], value="Efectivo", width=140, border_radius=12, filled=True, bgcolor="#1E293B", border_color="transparent")

    def calcular_total_caja():
        t = sum(item['p'] for item in carrito)
        lbl_tot_caja.value = f"$ {t:,.2f}"
        page.update()

    # --- LÓGICA DE PAUSA (ESPERA) ---
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
        carrito.clear(); lista_compra_ui.controls.clear(); carrito.extend(t['items'])
        for i in carrito: agregar_item_ui(i)
        tickets_espera.remove(t)
        btn_recuperar.text = f"⏳ ({len(tickets_espera)})"
        btn_recuperar.visible = len(tickets_espera) > 0
        cerrar_ventana(dlg_espera); calcular_total_caja()

    def ver_pausados(e):
        if not tickets_espera: return
        cols = [ft.ElevatedButton(f"🛒 {t['nombre']} ({len(t['items'])} prod)", on_click=lambda ev, tk=t: cargar_pausado(tk), height=50, width=250, bgcolor="#1E293B", color="white") for t in tickets_espera]
        dlg_espera.content = ft.Column(cols, tight=True)
        dlg_espera.title = ft.Text("Ventas Pausadas")
        dlg_espera.actions = [ft.TextButton("Cerrar", on_click=lambda ev: cerrar_ventana(dlg_espera))]
        abrir_ventana(dlg_espera)
    
    btn_recuperar.on_click = ver_pausados
    btn_pausa = ft.ElevatedButton("⏸️", on_click=pausar_venta, bgcolor="#F59E0B", color="black")

    # --- BALANZA DIGITAL ---
    dlg_granel = ft.AlertDialog(modal=True)
    in_gramos = ft.TextField(**estilo_input("Gramos (Ej: 250)"), keyboard_type="number")
    lbl_granel_res = ft.Text("$ 0.00", size=30, weight="bold", color="#10B981")
    item_granel = None; input_precio = None

    def calc_g(e):
        try: lbl_granel_res.value = f"$ {((float(in_gramos.value) * item_granel['p_kg']) / 1000):.2f}"
        except: lbl_granel_res.value = "$ 0.00"
        page.update()
    in_gramos.on_change = calc_g

    def ok_g(e):
        if item_granel and input_precio:
            try:
                val = lbl_granel_res.value.replace("$ ", "")
                item_granel['p'] = float(val); input_precio.value = val; calcular_total_caja()
            except: pass
        cerrar_ventana(dlg_granel)

    dlg_granel.actions = [ft.TextButton("Cancelar", on_click=lambda e: cerrar_ventana(dlg_granel)), ft.TextButton("Confirmar", on_click=ok_g)]

    def abrir_granel(n, p_kg, data, ui):
        nonlocal item_granel, input_precio
        item_granel = data; item_granel['p_kg'] = p_kg; input_precio = ui
        dlg_granel.title = ft.Text(f"Balanza: {n}", size=18)
        dlg_granel.content = ft.Column([ft.Text(f"Precio x KG: ${p_kg:,.2f}", color="#94A3B8"), in_gramos, lbl_granel_res], tight=True)
        in_gramos.value = ""; lbl_granel_res.value = "$ 0.00"; abrir_ventana(dlg_granel)

    def agregar_item_ui(data):
        in_p = ft.TextField(value=f"{data['p']:.2f}", width=80, text_align="right", bgcolor="#0F172A", border_color="transparent", filled=True, border_radius=8, content_padding=5, on_change=lambda e: (setitem(data, 'p', float(e.control.value or 0)), calcular_total_caja()))
        fila = ft.Container(
            content=ft.Row([
                ft.ElevatedButton("❌", on_click=lambda _: (carrito.remove(data), lista_compra_ui.controls.remove(fila), calcular_total_caja()), bgcolor="#EF4444", color="white", width=50),
                ft.Text(data['n'], expand=True, weight="bold", size=12),
                ft.ElevatedButton("⚖️", on_click=lambda _: abrir_granel(data['n'], data['p'], data, in_p), bgcolor="#38BDF8", color="white", width=50),
                in_p
            ]), bgcolor="#1E293B", padding=10, border_radius=15
        )
        lista_compra_ui.controls.append(fila)

    def setitem(d, k, v): d[k] = v

    def sumar_prod(e):
        lbl_aviso_caja.value = ""; v = in_scanner.value.strip()
        if not v: return
        r, err = ejecutar("SELECT nombre, precio_venta FROM productos WHERE codigo_barra = ? OR nombre LIKE ?", (v, f"%{v}%"), fetch=True)
        if err: lbl_aviso_caja.value, lbl_aviso_caja.color = f"⚠️ {err}", "red"
        elif r:
            dat = {"n": r[0][0], "p": float(r[0][1] or 0)}; carrito.append(dat); agregar_item_ui(dat)
            in_scanner.value = ""; in_scanner.focus(); calcular_total_caja()
        else: lbl_aviso_caja.value, lbl_aviso_caja.color = f"❌ '{v}' no encontrado.", "red"
        page.update()
    
    in_scanner.on_submit = sumar_prod

    view_cobrar = ft.Container(
        content=ft.Column([
            lbl_aviso_caja,
            ft.Row([in_cliente, btn_pausa, btn_recuperar], alignment="spaceBetween"),
            ft.Row([in_scanner, ft.ElevatedButton("➕", on_click=sumar_prod, bgcolor="#10B981", color="white", height=50)]),
            lista_compra_ui,
            ft.Row([lbl_tot_caja, drop_metodo], alignment="spaceBetween"),
            ft.ElevatedButton("🧾 GENERAR TICKET", width=float("inf"), height=60, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15)), bgcolor="#F43F5E", color="white", on_click=lambda e: ir_ticket(e))
        ]), padding=20, visible=False, expand=True
    )
    # --- PANTALLA 3: TICKET ---
    lista_ticket = ft.Column(scroll=ft.ScrollMode.ALWAYS, height=200)
    in_pago = ft.TextField(**estilo_input("¿Con cuánto paga?", w=150), keyboard_type="number", text_align="right")
    lbl_vuelto = ft.Text("$ 0.00", size=30, weight="w900", color="#EF4444")
    
    # NUEVO: Cartel de total exclusivo para el ticket
    lbl_ticket_total = ft.Text("$ 0.00", size=35, weight="w900", color="#F43F5E") 
    row_vuelto = ft.Column(visible=False)

    def cal_vuelto(e):
        try:
            v = float(in_pago.value) - sum(item['p'] for item in carrito)
            lbl_vuelto.value, lbl_vuelto.color = (f"VUELTO: ${v:,.2f}", "#10B981") if v >= 0 else ("FALTA PLATA", "#EF4444")
        except: lbl_vuelto.value = "$ 0.00"
        page.update()
    in_pago.on_change = cal_vuelto

    row_vuelto.controls = [ft.Divider(color="#334155"), ft.Row([ft.Text("SU PAGO:"), in_pago], alignment="spaceBetween"), ft.Row([ft.Text("VUELTO:", weight="bold"), lbl_vuelto], alignment="spaceBetween")]

    def cobrar_final(e):
        tot = sum(item['p'] for item in carrito); met = drop_metodo.value
        num, _ = ejecutar("SELECT MAX(CAST(numero AS INTEGER)) FROM ventas", fetch=True)
        n_num = (num[0][0] or 0) + 1
        
        ejecutar("ALTER TABLE ventas ADD COLUMN origen TEXT DEFAULT 'mostrador'")
        ejecutar("ALTER TABLE ventas ADD COLUMN metodo_pago TEXT DEFAULT 'Efectivo'")
        ejecutar("ALTER TABLE ventas ADD COLUMN estado TEXT DEFAULT 'completada'")
        
        # Arreglo ninja para las ventas de prueba que te quedaron "anuladas"
        ejecutar("UPDATE ventas SET estado = 'completada' WHERE estado IS NULL")
        
        # ACÁ ESTÁ LA CORRECCIÓN: Le pasamos 'estado' y 'completada' a la base de datos
        ejecutar("INSERT INTO ventas (numero, total, subtotal, fecha, origen, metodo_pago, usuario_id, estado) VALUES (?, ?, ?, ?, 'celular', ?, 1, 'completada')", (n_num, tot, tot, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), met))
        
        carrito.clear(); lista_compra_ui.controls.clear(); in_pago.value = ""
        view_ticket.visible = False; view_cobrar.visible = True
        lbl_aviso_caja.value = f"✅ TICKET COBRADO!"; lbl_aviso_caja.color="green"
        refrescar_ventas()
        
        # ACTUALIZAMOS EL CARRITO PRINCIPAL A CERO
        calcular_total_caja() 
        
        view_ticket.visible = False; view_cobrar.visible = True
        lbl_aviso_caja.value = f"✅ TICKET COBRADO!"; lbl_aviso_caja.color="green"
        refrescar_ventas()

    view_ticket = ft.Container(
        content=ft.Column([
            ft.Text("🧾 RESUMEN DE VENTA", size=24, weight="w900", color="#94A3B8"), ft.Divider(color="#334155"),
            lista_ticket, ft.Divider(color="#334155"),
            ft.Row([ft.Text("TOTAL:", weight="bold"), lbl_ticket_total], alignment="spaceBetween"),
            row_vuelto, ft.Container(height=10),
            ft.Row([
                ft.ElevatedButton("🔙 ATRÁS", on_click=lambda _: (setattr(view_ticket, 'visible', False), setattr(view_cobrar, 'visible', True), page.update()), expand=True, height=55, bgcolor="#334155", color="white"),
                ft.ElevatedButton("✅ FINALIZAR", on_click=cobrar_final, expand=True, height=55, bgcolor="#10B981", color="white")
            ], spacing=10)
        ]), padding=20, visible=False, expand=True
    )

    def ir_ticket(e):
        if not carrito: return
        lista_ticket.controls = [ft.Row([ft.Text(i['n'], expand=True), ft.Text(f"${i['p']:.2f}")]) for i in carrito]
        
        # ACTUALIZAMOS EL TOTAL DEL TICKET ANTES DE ABRIRLO
        tot_ticket = sum(i['p'] for i in carrito)
        lbl_ticket_total.value = f"$ {tot_ticket:,.2f}"

        if drop_metodo.value == "Efectivo":
            row_vuelto.visible = True; in_pago.value = ""; lbl_vuelto.value = "$ 0.00"
        else: row_vuelto.visible = False
        view_cobrar.visible = False; view_ticket.visible = True; page.update()

    # --- PANTALLA 4: PRECIOS ---
    lbl_stk = ft.Text("", weight="bold")
    in_b = ft.TextField(**estilo_input("Buscar producto para PC"))
    in_c = ft.TextField(**estilo_input("Código"), read_only=True)
    in_n = ft.TextField(**estilo_input("Nombre"))
    in_p = ft.TextField(**estilo_input("Precio $"), keyboard_type="number")
    item_edit = {"c": "", "n": ""}

    def bus_edit(e):
        r, _ = ejecutar("SELECT codigo_barra, nombre, precio_venta FROM productos WHERE codigo_barra=? OR nombre LIKE ?", (in_b.value, f"%{in_b.value}%"), fetch=True)
        if r:
            item_edit["c"], item_edit["n"] = r[0][0] or "", r[0][1] or ""
            in_c.value, in_n.value, in_p.value = item_edit["c"], item_edit["n"], str(r[0][2])
            lbl_stk.value = f"Editando: {r[0][1]}"; lbl_stk.color = "#38BDF8"
        else: lbl_stk.value = "No encontrado"; lbl_stk.color = "red"
        page.update()
    
    in_b.on_submit = bus_edit

    def update_pc(e):
        p = float(in_p.value or 0)
        if item_edit["c"]: ejecutar("UPDATE productos SET precio_venta=? WHERE codigo_barra=?", (p, item_edit["c"]))
        else: ejecutar("UPDATE productos SET precio_venta=? WHERE nombre=?", (p, item_edit["n"]))
        lbl_stk.value = "¡Actualizado en PC!"; lbl_stk.color = "green"
        in_b.value = ""; in_p.value = ""; in_c.value = ""; in_n.value = ""; page.update()

    view_stock = ft.Container(
        content=ft.Column([
            ft.Text("ACTUALIZAR GÓNDOLA", size=24, weight="w900"), in_b,
            ft.ElevatedButton("🔍 BUSCAR", on_click=bus_edit, height=50, width=float("inf"), bgcolor="#1E293B", color="white"),
            ft.Divider(color="#334155"), lbl_stk, in_c, in_n, in_p, ft.Container(height=10),
            ft.ElevatedButton("💾 GUARDAR EN PC", on_click=update_pc, width=float("inf"), height=60, bgcolor="#F43F5E", color="white")
        ]), padding=20, visible=False, expand=True
    )

    # --- NAVEGACIÓN TIPO APP NATIVA ---
    def nav(e):
        t = e.control.data
        view_ventas.visible = (t == "V"); view_cobrar.visible = (t == "C"); view_stock.visible = (t == "S"); view_ticket.visible = False
        lbl_aviso_caja.value = ""; lbl_stk.value = ""
        if t == "V": refrescar_ventas()
        page.update()

    nav_bar = ft.Container(
        content=ft.Row([
            ft.ElevatedButton("📊 VENTAS", data="V", on_click=nav, expand=True, height=60, bgcolor="#1E293B", color="white", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=0))),
            ft.ElevatedButton("🛒 COBRAR", data="C", on_click=nav, expand=True, height=60, bgcolor="#1E293B", color="white", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=0))),
            ft.ElevatedButton("📝 PRECIOS", data="S", on_click=nav, expand=True, height=60, bgcolor="#1E293B", color="white", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=0)))
        ], spacing=2),
        bgcolor="#0F172A", padding=0
    )

    page.add(app_bar, ft.Column([view_ventas, view_cobrar, view_ticket, view_stock], expand=True), nav_bar)
    refrescar_ventas()

ft.app(target=main)