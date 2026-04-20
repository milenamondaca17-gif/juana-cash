"""
Importador directo — carga productos del Excel a la DB sin pasar por la API.
Ejecutar desde la raíz del proyecto con el sistema CERRADO.
"""
import sqlite3
import os
import openpyxl

# === CONFIGURACIÓN ===
ARCHIVO_EXCEL = "Nuevo_Hoja_de_cálculo_de_Microsoft_Excel.xlsx"
DB_PATH = "juana_cash.db"

def limpiar_precio(texto):
    if texto is None: return 0.0
    if isinstance(texto, (int, float)): return float(texto)
    texto = str(texto).replace("$", "").replace(" ", "").strip()
    if not texto or texto.lower() in ("none", "-"): return 0.0
    tiene_coma = "," in texto
    tiene_punto = "." in texto
    if tiene_coma and tiene_punto:
        if texto.rfind(",") > texto.rfind("."):
            texto = texto.replace(".", "").replace(",", ".")
        else:
            texto = texto.replace(",", "")
    elif tiene_coma:
        partes = texto.split(",")
        if len(partes[-1]) == 2:
            texto = texto.replace(",", ".")
        else:
            texto = texto.replace(",", "")
    try: return float(texto)
    except: return 0.0

# Buscar el archivo Excel
if not os.path.exists(ARCHIVO_EXCEL):
    # Buscar en Downloads
    alt = os.path.join(os.path.expanduser("~"), "Downloads", ARCHIVO_EXCEL)
    if os.path.exists(alt):
        ARCHIVO_EXCEL = alt
    else:
        print(f"❌ No se encontró {ARCHIVO_EXCEL}")
        print(f"   Copiá el Excel a la carpeta del proyecto o a Downloads")
        input("Presioná Enter para salir...")
        exit(1)

print(f"📂 Leyendo: {ARCHIVO_EXCEL}")
wb = openpyxl.load_workbook(ARCHIVO_EXCEL, read_only=True, data_only=True)
ws = wb.active

filas = []
for row in ws.iter_rows(values_only=True):
    filas.append([c if c is not None else "" for c in row])
wb.close()

if len(filas) < 2:
    print("❌ El archivo está vacío")
    exit(1)

headers = [str(h).lower().strip() for h in filas[0]]
print(f"📊 Encabezados: {filas[0]}")
print(f"📊 Total filas: {len(filas) - 1}")

# Detectar columnas
col_codigo = -1
col_nombre = -1
col_costo = -1
col_venta = -1
col_stock = -1
col_depto = -1

for i, h in enumerate(headers):
    if "prod" in h or h == "nombre" or h == "descripcion":
        if col_nombre == -1: col_nombre = i
    elif "costo" in h or "compra" in h:
        if col_costo == -1: col_costo = i
    elif h.startswith("p") and "venta" in h and "tipo" not in h:
        if col_venta == -1: col_venta = i
    elif h in ("codigo", "código", "cod", "barras", "codigo_barra", "ean", "upc", "sku"):
        col_codigo = i
    elif "exist" in h or "stock" in h or "cant" in h:
        if col_stock == -1: col_stock = i
    elif "depart" in h or "categ" in h:
        if col_depto == -1: col_depto = i

# Fallback: buscar "precio" si no encontró p_venta
if col_venta == -1:
    for i, h in enumerate(headers):
        if "precio" in h and i != col_costo and "tipo" not in h:
            col_venta = i
            break

print(f"\n🔍 Columnas detectadas:")
print(f"   Código: {col_codigo} | Nombre: {col_nombre} | Costo: {col_costo}")
print(f"   Venta: {col_venta} | Stock: {col_stock} | Depto: {col_depto}")

if col_nombre == -1 or col_venta == -1:
    print("❌ No se detectaron columnas de Nombre y Precio de Venta")
    exit(1)

# Conectar a la DB
if not os.path.exists(DB_PATH):
    print(f"❌ No se encontró {DB_PATH}")
    exit(1)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Leer códigos existentes para evitar duplicados
existentes = set()
for row in cursor.execute("SELECT codigo_barra FROM productos WHERE codigo_barra IS NOT NULL"):
    existentes.add(row[0])
print(f"\n📦 Productos existentes en DB: {cursor.execute('SELECT COUNT(*) FROM productos').fetchone()[0]}")
print(f"   Códigos ya cargados: {len(existentes)}")

# Importar
exitos = 0
duplicados = 0
sin_precio = 0
errores = 0

for fila in filas[1:]:
    try:
        if len(fila) <= max(v for v in [col_codigo, col_nombre, col_costo, col_venta, col_stock, col_depto] if v >= 0):
            continue

        nombre = str(fila[col_nombre]).strip() if col_nombre >= 0 else ""
        p_venta = limpiar_precio(fila[col_venta]) if col_venta >= 0 else 0
        p_costo = limpiar_precio(fila[col_costo]) if col_costo >= 0 else 0
        codigo = str(fila[col_codigo]).strip() if col_codigo >= 0 else ""
        stock = limpiar_precio(fila[col_stock]) if col_stock >= 0 else 0
        depto = str(fila[col_depto]).strip() if col_depto >= 0 else ""

        # Limpiar código
        if codigo.endswith(".0"): codigo = codigo[:-2]
        if codigo.lower() in ("none", "0", ""): codigo = None

        if not nombre or nombre.lower() in ("none", ""):
            continue
        if p_venta <= 0:
            sin_precio += 1
            continue

        # Verificar duplicado
        if codigo and codigo in existentes:
            duplicados += 1
            continue

        cursor.execute(
            "INSERT INTO productos (nombre, codigo_barra, precio_venta, precio_costo, stock_actual, activo) VALUES (?, ?, ?, ?, ?, 1)",
            (nombre, codigo, p_venta, p_costo, stock)
        )
        if codigo:
            existentes.add(codigo)
        exitos += 1

    except Exception as e:
        errores += 1

conn.commit()
conn.close()

print(f"\n{'='*50}")
print(f"✅ IMPORTACIÓN COMPLETADA")
print(f"{'='*50}")
print(f"   Importados:  {exitos}")
print(f"   Duplicados:  {duplicados} (ya existían)")
print(f"   Sin precio:  {sin_precio} (precio $0)")
print(f"   Errores:     {errores}")
print(f"{'='*50}")
input("\nPresioná Enter para salir...")
