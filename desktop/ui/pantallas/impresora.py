import os
import json
from datetime import datetime

_TICKET_CFG_PATH = os.path.join(os.path.expanduser("~"), "JuanaCash_Data", "ticket_config.json")

_DEFAULTS = {
    "nombre_negocio": "JUANA CASH",
    "subtitulo":      "",
    "telefono":       "",
    "instagram":      "",
    "facebook":       "",
    "whatsapp":       "",
    "mensaje1":       "Gracias por su compra!",
    "mensaje2":       "Vuelva pronto :)",
}

def leer_config_ticket():
    cfg = dict(_DEFAULTS)
    try:
        if os.path.exists(_TICKET_CFG_PATH):
            with open(_TICKET_CFG_PATH, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
    except Exception:
        pass
    # fallback: leer nombre desde el archivo viejo si no tiene config nueva
    if cfg["nombre_negocio"] == "JUANA CASH":
        try:
            ruta_vieja = os.path.join(os.path.expanduser("~"), "JuanaCash_Tickets", "config_negocio.txt")
            if os.path.exists(ruta_vieja):
                with open(ruta_vieja, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("nombre="):
                            n = line.split("=", 1)[1].strip()
                            if n:
                                cfg["nombre_negocio"] = n
        except Exception:
            pass
    return cfg

def guardar_config_ticket(datos: dict):
    try:
        os.makedirs(os.path.dirname(_TICKET_CFG_PATH), exist_ok=True)
        cfg = leer_config_ticket()
        cfg.update(datos)
        with open(_TICKET_CFG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def formatear_ticket(venta, items, metodo_pago="", descuento=0, vuelto=0, cliente=None, recargo=0, recargo_pct=0):
    ANCHO = 32
    cfg   = leer_config_ticket()

    def centrar(texto):
        texto = str(texto)
        if len(texto) > ANCHO:
            texto = texto[:ANCHO]
        return texto.center(ANCHO)

    def izq_der(izq, der):
        espacios = ANCHO - len(str(izq)) - len(str(der))
        if espacios < 1:
            espacios = 1
        return str(izq) + (" " * espacios) + str(der)

    lineas = []
    lineas.append("=" * ANCHO)
    lineas.append(centrar(cfg["nombre_negocio"].upper()))
    if cfg.get("subtitulo"):
        lineas.append(centrar(cfg["subtitulo"]))
    lineas.append("=" * ANCHO)

    lineas.append(f"Ticket N: {venta.get('numero', '0001')}")
    lineas.append(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    if cliente:
        lineas.append(f"Cliente: {str(cliente)[:22]}")
    lineas.append("-" * ANCHO)
    lineas.append("CANT DESCRIPCION        TOTAL")
    lineas.append("-" * ANCHO)

    for item in items:
        cant     = float(item.get("cantidad", 1))
        nombre   = str(item.get("nombre", ""))[:16]
        subtotal = float(item.get("subtotal", 0))
        lineas.append(izq_der(f"{cant:g}x {nombre}", f"${subtotal:,.0f}"))

    lineas.append("-" * ANCHO)

    if descuento and float(descuento) > 0:
        lineas.append(izq_der("Descuento:", f"-${float(descuento):,.0f}"))

    if recargo and float(recargo) > 0:
        lineas.append(izq_der(f"Recargo credito {float(recargo_pct):.0f}%:", f"+${float(recargo):,.0f}"))

    total = float(venta.get("total", 0))
    lineas.append(izq_der("TOTAL A PAGAR:", f"${total:,.0f}"))

    if metodo_pago:
        nombres_m = {
            "efectivo":       "Efectivo",
            "tarjeta":        "Tarjeta",
            "mercadopago_qr": "QR / Mercado Pago",
            "transferencia":  "Transferencia",
            "fiado":          "Fiado",
        }
        lineas.append(izq_der("Pago:", nombres_m.get(metodo_pago, metodo_pago)))

    if vuelto and float(vuelto) > 0:
        lineas.append(izq_der("Vuelto:", f"${float(vuelto):,.0f}"))

    lineas.append("=" * ANCHO)

    if cfg.get("mensaje1"):
        lineas.append(centrar(cfg["mensaje1"]))
    if cfg.get("mensaje2"):
        lineas.append(centrar(cfg["mensaje2"]))

    # Datos de contacto
    contacto = []
    if cfg.get("telefono"):
        contacto.append(f"Tel: {cfg['telefono']}")
    if cfg.get("whatsapp"):
        contacto.append(f"WA:  {cfg['whatsapp']}")
    if cfg.get("instagram"):
        contacto.append(f"IG:  @{cfg['instagram'].lstrip('@')}")
    if cfg.get("facebook"):
        contacto.append(f"FB:  {cfg['facebook']}")
    for c in contacto:
        lineas.append(centrar(c))

    lineas.append("\n\n\n\n")  # espacio guillotina

    return "\n".join(lineas)


def imprimir_ticket(venta, items, metodo_pago="", descuento=0, vuelto=0, cliente=None, recargo=0, recargo_pct=0):
    texto = formatear_ticket(venta, items, metodo_pago, descuento, vuelto, cliente, recargo, recargo_pct)

    try:
        import win32print
        impresora = win32print.GetDefaultPrinter()
        hPrinter  = win32print.OpenPrinter(impresora)
        try:
            hJob = win32print.StartDocPrinter(hPrinter, 1, ("Ticket_JuanaCash", None, "RAW"))
            try:
                win32print.StartPagePrinter(hPrinter)
                win32print.WritePrinter(hPrinter, texto.encode("cp850", errors="replace"))
                win32print.EndPagePrinter(hPrinter)
            finally:
                win32print.EndDocPrinter(hPrinter)
        finally:
            win32print.ClosePrinter(hPrinter)
        return True, f"Impreso en: {impresora}"

    except ImportError:
        _guardar_txt(texto, venta.get("numero", "0"))
        return False, "pywin32 no instalado — corrí: pip install pywin32"

    except Exception as e:
        _guardar_txt(texto, venta.get("numero", "0"))
        return False, f"Error impresora: {str(e)[:80]}"


def _guardar_txt(texto, numero):
    try:
        carpeta = os.path.join(os.path.expanduser("~"), "JuanaCash_Tickets")
        os.makedirs(carpeta, exist_ok=True)
        with open(os.path.join(carpeta, f"ticket_{numero}.txt"), "w", encoding="utf-8") as f:
            f.write(texto)
    except Exception:
        pass
