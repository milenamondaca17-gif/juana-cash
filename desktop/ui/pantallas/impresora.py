from datetime import datetime
import os

def generar_ticket_texto(venta, items, negocio="Mi Kiosco"):
    linea = "=" * 32
    linea_simple = "-" * 32
    ticket = []
    ticket.append(linea)
    ticket.append(f"{'JUANA CASH':^32}")
    ticket.append(f"{negocio:^32}")
    ticket.append(linea)
    ticket.append(f"Ticket: {venta.get('numero', 'N/A')}")
    ticket.append(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    ticket.append(linea_simple)
    ticket.append(f"{'PRODUCTO':<16}{'CANT':>4}{'PRECIO':>6}{'SUB':>6}")
    ticket.append(linea_simple)
    for item in items:
        nombre = item['nombre'][:15]
        cant = str(item['cantidad'])
        precio = f"${item['precio_unitario']:.0f}"
        sub = f"${item['subtotal']:.0f}"
        ticket.append(f"{nombre:<16}{cant:>4}{precio:>6}{sub:>6}")
    ticket.append(linea)
    ticket.append(f"{'TOTAL:':>24} ${venta.get('total', 0):.2f}")
    ticket.append(linea)
    ticket.append(f"{'Gracias por su compra!':^32}")
    ticket.append(f"{'Vuelva pronto':^32}")
    ticket.append(linea)
    return "\n".join(ticket)

def imprimir_ticket(venta, items, negocio="Mi Kiosco"):
    ticket_texto = generar_ticket_texto(venta, items, negocio)
    # Por ahora solo guarda en archivo — cuando tengas impresora configuramos la IP
    try:
        carpeta = os.path.join(os.path.expanduser("~"), "JuanaCash_Tickets")
        os.makedirs(carpeta, exist_ok=True)
        nombre_archivo = f"ticket_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        ruta = os.path.join(carpeta, nombre_archivo)
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(ticket_texto)
        return True, f"Ticket guardado en Documentos/JuanaCash_Tickets"
    except Exception as e:
        return False, str(e)