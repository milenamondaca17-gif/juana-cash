import os
from datetime import datetime

def formatear_ticket(venta, items):
    # Ancho típico de impresora térmica de 58mm (32 caracteres máximo)
    ANCHO = 32
    
    lineas = []
    
    # Herramientas para centrar y alinear los precios a la derecha
    def centrar(texto):
        return texto.center(ANCHO)
        
    def izq_der(izq, der):
        espacios = ANCHO - len(izq) - len(der)
        if espacios < 1: espacios = 1
        return izq + (" " * espacios) + der

    # --- ENCABEZADO ---
    lineas.append(centrar("================================"))
    lineas.append(centrar("AU SANVALENTIN"))
    lineas.append(centrar("================================"))
    lineas.append(f"Ticket N°: {venta.get('numero', '10001')}")
    lineas.append(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    lineas.append("-" * ANCHO)
    
    # --- ENCABEZADOS DE TABLA ---
    lineas.append("CANT DESCRIPCION           TOTAL")
    lineas.append("-" * ANCHO)
    
    # --- LISTA DE PRODUCTOS ---
    for item in items:
        # Extraemos los datos de la venta
        cant = float(item.get("cantidad", 1))
        nombre = str(item.get("nombre", ""))[:14] # Cortamos nombres muy largos para que no rompan el papel
        subtotal = float(item.get("subtotal", 0))
        
        # Formato de la línea: Ej: "2x Coca Cola          $3000.00"
        linea_izq = f"{cant:g}x {nombre}"
        linea_der = f"${subtotal:,.2f}"
        
        lineas.append(izq_der(linea_izq, linea_der))
        
    lineas.append("-" * ANCHO)
    
    # --- TOTALES ---
    str_total = f"${float(venta.get('total', 0)):,.2f}"
    lineas.append(izq_der("TOTAL A PAGAR:", str_total))
    
    # --- DESPEDIDA ---
    lineas.append(centrar("================================"))
    lineas.append(centrar("¡Gracias por su compra!"))
    lineas.append(centrar("Vuelva pronto"))
    lineas.append("\n\n\n\n") # Espacios extra abajo para que la guillotina corte bien el papel
    
    return "\n".join(lineas)

def imprimir_ticket(venta, items):
    texto_ticket = formatear_ticket(venta, items)
    
    # Intentamos conectarnos a la impresora de Windows
    try:
        import win32print
        impresora_predeterminada = win32print.GetDefaultPrinter()
        
        # Si la encuentra, manda el texto crudo
        hPrinter = win32print.OpenPrinter(impresora_predeterminada)
        try:
            hJob = win32print.StartDocPrinter(hPrinter, 1, ("Ticket_ElCuervo", None, "RAW"))
            try:
                win32print.StartPagePrinter(hPrinter)
                # La térmica entiende el texto en formato 'cp850' o 'utf-8'
                win32print.WritePrinter(hPrinter, texto_ticket.encode("cp850", errors="replace"))
                win32print.EndPagePrinter(hPrinter)
            finally:
                win32print.EndDocPrinter(hPrinter)
        finally:
            win32print.ClosePrinter(hPrinter)
            
        return True, texto_ticket
        
    except Exception as e:
        # Si no hay impresora conectada o falta la librería, devuelve False 
        # pero IGUAL te pasa el texto para que lo veas en la pantalla de la caja
        return False, texto_ticket