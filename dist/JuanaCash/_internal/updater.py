"""
updater.py — Auto-updater para Juana Cash
Se llama al arrancar el programa. Compara la versión local con GitHub.
Si hay actualización, descarga e instala. Si no hay internet, arranca normal.
"""
import os
import sys
import json
import threading
import subprocess
import tempfile
import time

# ─── CONFIGURACIÓN ────────────────────────────────────────────────────────────
GITHUB_USER    = "milenamondaca17-gif"
GITHUB_REPO    = "juana-cash"
VERSION_FILE   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "version.json")
INTENTOS_RED   = 2
TIMEOUT_RED    = 3  # segundos por intento

def leer_version_local():
    """Lee la versión instalada del archivo version.json."""
    try:
        if os.path.exists(VERSION_FILE):
            with open(VERSION_FILE, "r") as f:
                return json.load(f).get("version", "0.0.0")
    except Exception:
        pass
    return "0.0.0"

def guardar_version_local(version):
    """Guarda la versión instalada."""
    try:
        with open(VERSION_FILE, "w") as f:
            json.dump({"version": version}, f)
    except Exception:
        pass

def obtener_version_github():
    """Consulta la versión disponible en GitHub. Devuelve None si no hay internet."""
    import urllib.request
    url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/version.json"
    for intento in range(INTENTOS_RED):
        try:
            req = urllib.request.urlopen(url, timeout=TIMEOUT_RED)
            data = json.loads(req.read().decode())
            return data.get("version"), data.get("installer_url", "")
        except Exception:
            if intento < INTENTOS_RED - 1:
                time.sleep(1)
    return None, None

def version_mayor(v_nueva, v_actual):
    """Devuelve True si v_nueva es mayor que v_actual."""
    try:
        def partes(v): return [int(x) for x in v.split(".")]
        return partes(v_nueva) > partes(v_actual)
    except Exception:
        return False

def descargar_instalar(installer_url, version_nueva, callback_ok=None, callback_error=None):
    """Descarga el instalador y lo ejecuta en segundo plano."""
    import urllib.request
    try:
        # Descargar a carpeta temporal
        tmp = tempfile.mktemp(suffix=".exe", prefix="JuanaCash_Update_")
        urllib.request.urlretrieve(installer_url, tmp)
        
        # Guardar versión nueva antes de instalar
        guardar_version_local(version_nueva)
        
        # Ejecutar instalador silencioso
        subprocess.Popen([tmp, "/SILENT", "/NORESTART"])
        
        if callback_ok:
            callback_ok(version_nueva)
    except Exception as e:
        if callback_error:
            callback_error(str(e))


class Updater:
    """
    Uso:
        updater = Updater()
        updater.verificar(
            on_actualizado=lambda v: print(f"Actualizado a {v}"),
            on_sin_internet=lambda: print("Sin internet, arrancando normal"),
            on_no_hay_update=lambda: print("Ya tenés la última versión")
        )
    """
    def __init__(self):
        self.version_local = leer_version_local()

    def verificar(self, on_actualizado=None, on_sin_internet=None, on_no_hay_update=None, on_descargando=None):
        """Verifica en segundo plano. No bloquea el arranque."""
        def _check():
            version_github, installer_url = obtener_version_github()
            
            if version_github is None:
                # Sin internet — arranca normal
                if on_sin_internet:
                    on_sin_internet()
                return
            
            if not version_mayor(version_github, self.version_local):
                # Ya tiene la última versión
                if on_no_hay_update:
                    on_no_hay_update()
                return
            
            # Hay actualización disponible
            if on_descargando:
                on_descargando(version_github)
            
            if installer_url:
                descargar_instalar(
                    installer_url, version_github,
                    callback_ok=on_actualizado,
                    callback_error=lambda e: print(f"Error update: {e}")
                )
            else:
                # Sin URL de instalador — solo notificar
                if on_actualizado:
                    on_actualizado(version_github)

        threading.Thread(target=_check, daemon=True).start()
