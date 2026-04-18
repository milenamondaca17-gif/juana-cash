import sqlite3
import os

# Buscamos el archivo juana_cash.db
# Probamos en la carpeta actual y en la carpeta 'app'
posibles_rutas = ['juana_cash.db', 'app/juana_cash.db']

for ruta in posibles_rutas:
    if os.path.exists(ruta):
        try:
            conn = sqlite3.connect(ruta)
            cursor = conn.cursor()
            # Actualizamos el PIN a 1989 para Lucas
            cursor.execute("UPDATE usuarios SET pin='1989' WHERE nombre LIKE '%Lucas%'")
            conn.commit()
            if cursor.rowcount > 0:
                print(f"✅ ¡ÉXITO! PIN 1989 asignado en {ruta}")
            else:
                print("⚠️ No se encontró el usuario 'Lucas' en la tabla.")
            conn.close()
            exit()
        except Exception as e:
            print(f"❌ Error al conectar: {e}")

print("❌ No se encontró el archivo juana_cash.db en ninguna ruta.")