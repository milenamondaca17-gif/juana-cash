"""
ticket_utils.py — Utilidades para ticket personalizado y WhatsApp
Copiá este archivo a: desktop/ui/pantallas/ticket_utils.py
"""
import os
import webbrowser
from urllib.parse import quote
from datetime import datetime

def _p(v):
    return f"${float(v):,.0f}".replace(",", ".")

# ─── Configuración del negocio (editable) ───────────────────────────────────
# Estas variables se pueden guardar en un archivo config más adelante
NEGOCIO_NOMBRE    = "Juana Cash"
NEGOCIO_DIRECCION = ""
NEGOCIO_TELEFONO  = ""
NEGOCIO_FOOTER    = "¡Gracias por su compra!"


def formatear_ticket_texto(ticket_num, items, total, metodo_pago,
                            descuento=0, vuelto=0, cliente=None):
    """
    Genera el texto del ticket en formato legible.
    Retorna un string listo para imprimir o enviar.
    """
    linea = "─" * 36
    linea_doble = "═" * 36
    ahora = datetime.now().strftime("%d/%m/%Y  %H:%M")

    lines = []
    lines.append(linea_doble)
    lines.append(f"  {NEGOCIO_NOMBRE.upper()}")
    if NEGOCIO_DIRECCION:
        lines.append(f"  {NEGOCIO_DIRECCION}")
    if NEGOCIO_TELEFONO:
        lines.append(f"  Tel: {NEGOCIO_TELEFONO}")
    lines.append(linea_doble)
    lines.append(f"  Ticket: #{ticket_num}")
    lines.append(f"  Fecha:  {ahora}")
    if cliente:
        lines.append(f"  Cliente: {cliente}")
    lines.append(linea)

    for item in items:
        nombre = item.get("nombre", "")[:24]
        cant   = item.get("cantidad", 1)
        precio = float(item.get("precio_unitario", 0))
        sub    = float(item.get("subtotal", precio * cant))

        # Línea del producto
        lines.append(f"  {nombre}")
        linea_cant = f"  {cant} x {_p(precio)}"
        linea_sub  = _p(sub)
        # Alinear subtotal a la derecha
        espacios = max(1, 34 - len(linea_cant) - len(linea_sub))
        lines.append(linea_cant + " " * espacios + linea_sub)

    lines.append(linea)

    if descuento > 0:
        lines.append(f"  Descuento:        -{_p(descuento)}")

    lines.append(f"  TOTAL:          {_p(total)}")
    lines.append(f"  Pago: {metodo_pago}")

    if vuelto > 0:
        lines.append(f"  Vuelto:         {_p(vuelto)}")

    lines.append(linea_doble)
    lines.append(f"  {NEGOCIO_FOOTER}")
    lines.append(linea_doble)

    return "\n".join(lines)


def abrir_whatsapp(numero: str, texto: str):
    """
    Abre WhatsApp Web con el mensaje pre-cargado.
    numero: string con el número (ej: "5491112345678")
    """
    # Limpiar número: solo dígitos
    numero_limpio = "".join(c for c in numero if c.isdigit())
    if not numero_limpio:
        return False

    # Agregar código de país Argentina si no tiene
    if not numero_limpio.startswith("54"):
        if numero_limpio.startswith("0"):
            numero_limpio = "54" + numero_limpio[1:]
        elif numero_limpio.startswith("15"):
            numero_limpio = "549" + numero_limpio[2:]
        else:
            numero_limpio = "549" + numero_limpio

    mensaje_encoded = quote(texto)
    url = f"https://web.whatsapp.com/send?phone={numero_limpio}&text={mensaje_encoded}"
    webbrowser.open(url)
    return True


def ticket_para_whatsapp(ticket_num, items, total, metodo_pago,
                          descuento=0, cliente=None):
    """
    Versión corta del ticket para WhatsApp (sin caracteres especiales).
    """
    ahora = datetime.now().strftime("%d/%m %H:%M")
    lines = [
        f"🧾 *{NEGOCIO_NOMBRE}*",
        f"Ticket #{ticket_num} — {ahora}",
        "─────────────────",
    ]
    for item in items:
        nombre = item.get("nombre", "")[:25]
        cant   = item.get("cantidad", 1)
        sub    = float(item.get("subtotal", 0))
        lines.append(f"• {nombre} x{cant}: {_p(sub)}")

    lines.append("─────────────────")
    if descuento > 0:
        lines.append(f"Descuento: -{_p(descuento)}")
    lines.append(f"*TOTAL: {_p(total)}*")
    lines.append(f"Pago: {metodo_pago}")
    if NEGOCIO_FOOTER:
        lines.append(f"\n_{NEGOCIO_FOOTER}_")

    return "\n".join(lines)


def guardar_config_negocio(nombre, direccion, telefono, footer):
    """Guarda la configuración del negocio en un archivo local."""
    global NEGOCIO_NOMBRE, NEGOCIO_DIRECCION, NEGOCIO_TELEFONO, NEGOCIO_FOOTER
    NEGOCIO_NOMBRE    = nombre
    NEGOCIO_DIRECCION = direccion
    NEGOCIO_TELEFONO  = telefono
    NEGOCIO_FOOTER    = footer

    config_dir = os.path.join(os.path.expanduser("~"), "JuanaCash_Tickets")
    os.makedirs(config_dir, exist_ok=True)
    ruta = os.path.join(config_dir, "config_negocio.txt")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(f"nombre={nombre}\n")
        f.write(f"direccion={direccion}\n")
        f.write(f"telefono={telefono}\n")
        f.write(f"footer={footer}\n")


def cargar_config_negocio():
    """Carga la configuración del negocio desde el archivo."""
    global NEGOCIO_NOMBRE, NEGOCIO_DIRECCION, NEGOCIO_TELEFONO, NEGOCIO_FOOTER
    ruta = os.path.join(os.path.expanduser("~"), "JuanaCash_Tickets", "config_negocio.txt")
    if not os.path.exists(ruta):
        return
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "=" in line:
                    key, val = line.split("=", 1)
                    if key == "nombre":    NEGOCIO_NOMBRE    = val
                    if key == "direccion": NEGOCIO_DIRECCION = val
                    if key == "telefono":  NEGOCIO_TELEFONO  = val
                    if key == "footer":    NEGOCIO_FOOTER    = val
    except Exception:
        pass


# Cargar config al importar
cargar_config_negocio()
