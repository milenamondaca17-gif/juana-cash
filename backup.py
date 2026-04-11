# ============================================
# JUANA CASH - Backup automático
# ============================================
import os
import shutil
from datetime import datetime

def hacer_backup():
    """Copia la base de datos a una carpeta de backups"""
    try:
        # Carpeta de backups
        carpeta_backup = os.path.join(os.path.expanduser("~"), "JuanaCash_Backups")
        os.makedirs(carpeta_backup, exist_ok=True)

        # Archivo origen
        db_origen = os.path.join(os.path.dirname(__file__), "juana_cash.db")

        # Nombre con fecha y hora
        fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
        db_destino = os.path.join(carpeta_backup, f"juana_cash_backup_{fecha}.db")

        # Copiar
        shutil.copy2(db_origen, db_destino)

        # Mantener solo los últimos 30 backups
        backups = sorted([
            f for f in os.listdir(carpeta_backup)
            if f.startswith("juana_cash_backup_")
        ])
        while len(backups) > 30:
            os.remove(os.path.join(carpeta_backup, backups.pop(0)))

        print(f"✅ Backup creado: {db_destino}")
        return True, db_destino

    except Exception as e:
        print(f"❌ Error en backup: {e}")
        return False, str(e)

if __name__ == "__main__":
    hacer_backup()