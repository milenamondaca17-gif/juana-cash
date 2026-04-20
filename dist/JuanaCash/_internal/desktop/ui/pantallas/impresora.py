import os
from datetime import datetime

# Lee el nombre del negocio del config guardado
def _leer_nombre_negocio():
    try:
        ruta = os.path.join(os.path.expanduser("~"), "JuanaCash_Tickets", "config_negocio.txt")
        if os.path.exists(ruta):
            with open(ruta, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("nombre="):
                        nombre = line.split("=", 1)[1].strip()
                        if nombre:
                            return nombre
    except Exception:
        pass
    return "JUANA CASH"

def formatear_ticket(venta, items, metodo_pago="", descuento=0, vuelto=0, cliente=None):
    ANCHO   = 32
    NEGOCIO = _leer_nombre_negocio()

    def centrar(texto):
        return texto.center(ANCHO)

    def izq_der(izq, der):
        espacios = ANCHO - len(izq) - len(der)
        if espacios < 1: espacios = 1
        return izq + (" " * espacios) + der

    lineas = []
    lineas.append("=" * ANCHO)
    lineas.append(centrar(NEGOCIO.upper()))
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
        linea_izq = f"{cant:g}x {nombre}"
        linea_der = f"${subtotal:,.0f}"
        lineas.append(izq_der(linea_izq, linea_der))

    lineas.append("-" * ANCHO)

    if descuento and float(descuento) > 0:
        lineas.append(izq_der("Descuento:", f"-${float(descuento):,.0f}"))

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
    lineas.append(centrar("Gracias por su compra!"))
    lineas.append(centrar("Vuelva pronto :)"))
    lineas.append("\n\n\n\n")  # Espacio para guillotina

    return "\n".join(lineas)


def imprimir_ticket(venta, items, metodo_pago="", descuento=0, vuelto=0, cliente=None):
    texto = formatear_ticket(venta, items, metodo_pago, descuento, vuelto, cliente)

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
        return False, "pywin32 no instalado.\nCorré: pip install pywin32"

    except Exception as e:
        _guardar_txt(texto, venta.get("numero", "0"))
        return False, f"Error impresora: {str(e)[:60]}"


def _guardar_txt(texto, numero):
    """Respaldo: guarda el ticket como .txt si no hay impresora."""
    try:
        carpeta = os.path.join(os.path.expanduser("~"), "JuanaCash_Tickets")
        os.makedirs(carpeta, exist_ok=True)
        with open(os.path.join(carpeta, f"ticket_{numero}.txt"), "w", encoding="utf-8") as f:
            f.write(texto)
    except Exception:
        pass
