import requests
from datetime import datetime

WHATSAPP_SERVER = "http://127.0.0.1:3001"


def servidor_activo():
    try:
        r = requests.get(f"{WHATSAPP_SERVER}/status", timeout=2)
        return r.json().get("ok", False)
    except Exception:
        return False


def formatear_ticket_whatsapp(venta, items, metodo_pago="", descuento=0,
                               vuelto=0, cliente=None, recargo=0):
    cfg = {}
    try:
        from ui.pantallas.impresora import leer_config_ticket
        cfg = leer_config_ticket()
    except Exception:
        pass

    nombre_negocio = "AUTOSERVICIO SAN VALENTIN"
    mensaje1 = cfg.get("mensaje1", "Gracias por su compra!")
    mensaje2 = cfg.get("mensaje2", "Vuelva pronto :)")

    ahora  = datetime.now().strftime("%d/%m/%Y - %H:%M")
    numero = str(venta.get("numero", "")).zfill(4)
    total  = float(venta.get("total", sum(
        float(i.get("subtotal", i.get("p", 0))) for i in items
    )))

    nombres_metodo = {
        "efectivo":       "Efectivo",
        "debito":         "Debito",
        "tarjeta":        "Tarjeta",
        "mercadopago_qr": "QR/Mercado Pago",
        "transferencia":  "Transferencia",
        "fiado":          "Fiado",
    }
    metodo_str = nombres_metodo.get(metodo_pago, metodo_pago.capitalize())

    def _p(v):
        return f"${float(v):,.0f}".replace(",", ".")

    lineas = [
        f"*{nombre_negocio}*",
        f"Ticket #{numero} - {ahora}",
        "",
        "*PRODUCTOS*",
        "--------------------",
    ]

    for item in items:
        nombre = item.get("nombre", item.get("n", "Producto"))
        cant   = float(item.get("cantidad", item.get("cant", 1)))
        precio = float(item.get("subtotal", item.get("p", 0)))
        cant_s = f"x{int(cant)}" if cant == int(cant) else f"x{cant}"
        lineas.append(f"- {nombre} {cant_s}  {_p(precio)}")

    lineas.append("--------------------")

    if descuento and float(descuento) > 0:
        lineas.append(f"Descuento: -{_p(descuento)}")
    if recargo and float(recargo) > 0:
        lineas.append(f"Recargo: +{_p(recargo)}")

    lineas.append(f"*TOTAL: {_p(total)}*")
    lineas.append(f"Pago: {metodo_str}")

    if metodo_pago == "efectivo" and vuelto and float(vuelto) > 0:
        lineas.append(f"Vuelto: {_p(vuelto)}")

    if cliente:
        lineas.append(f"Cliente: {cliente}")

    lineas += [
        "--------------------",
        f"_{mensaje1}_",
        f"_{mensaje2}_",
        "",
        "_Juana Cash_",
    ]

    return "\n".join(lineas)


def enviar_ticket_whatsapp(telefono, mensaje):
    try:
        r = requests.post(
            f"{WHATSAPP_SERVER}/send",
            json={"phone": telefono, "message": mensaje, "logo": True},
            timeout=10
        )
        data = r.json()
        return data.get("ok", False), data.get("mensaje", data.get("error", "Error"))
    except Exception as e:
        return False, f"No se pudo conectar al servidor WhatsApp\n{e}"
