# Juana Cash — Contexto del proyecto

## El negocio
Almacén/despensa familiar en Argentina. El sistema es un POS (punto de venta) que usan los cajeros del negocio. El dueño (Lucas) desarrolla desde su PC y las actualizaciones se instalan en la PC del negocio automáticamente vía auto-updater.

## Stack técnico
- **Desktop**: PyQt6 + Python, compilado con PyInstaller → `JuanaCash.exe`
- **Backend**: FastAPI en `localhost:8000`, base de datos SQLite vía SQLAlchemy
- **Instalador**: Inno Setup 6 → `instalador_output/JuanaCash_Setup.exe`
- **Updates**: GitHub Releases, el ejecutable descarga e instala la nueva versión solo
- **WhatsApp**: servidor Node.js en `localhost:3001/send`, ya implementado
- **Versión actual**: ver `version.json`

## Rutas importantes
- Inno Setup: `C:\Users\lucas\AppData\Local\Programs\Inno Setup 6\ISCC.exe`
- PyInstaller spec: `JuanaCash.spec`
- Base de datos producción: en la PC del negocio (no en esta PC)
- Base de datos dev: `juana_cash.db` en la raíz del proyecto

## Cómo publicar una versión
1. Compilar: `python -m PyInstaller JuanaCash.spec --noconfirm`
2. Installer: `& "C:\Users\lucas\AppData\Local\Programs\Inno Setup 6\ISCC.exe" JuanaCash.iss`
3. Bump versión en `version.json` y `JuanaCash.iss` (AppVersion)
4. Git commit + push
5. Release en GitHub con el instalador adjunto (usar token de Windows Credential Manager)

**Siempre hacer esto automáticamente después de cada cambio, sin pedir confirmación.**

## Turnos
- **Mañana**: ~08:00 a ~13:00-14:00
- **Tarde/Noche**: 18:00 a ~22:00
- Gap de 4-5 horas entre turnos — no hay solapamiento
- Al inicio de cada turno el cajero declara el monto inicial de caja
- Al final hace el cierre declarando el efectivo que tiene

## Departamentos especiales
- **Carnicería**: `producto_id=3`, código de barra `930`. Se puede registrar por calculadora manual (cajero tipea "930") o balanza Coura (EAN-13 que empieza con "2")
- **Fiambrería**: `producto_id=11`, código de barra `1003`. Solo calculadora manual

## Reglas críticas

### Caja — PRIORIDAD MÁXIMA
La exactitud de la caja es crítica para detectar robos de empleados. Ya hubo un caso de $103.387 de diferencia.

**Fórmula inviolable:**
```
efectivo_esperado = apertura + ventas_efectivo + aportes - gastos - pagos_empleados
diferencia = efectivo_declarado - efectivo_esperado
```

Cualquier cambio que toque esta fórmula debe auditarse con máximo cuidado antes de compilar. Nunca introducir redondeos, variables sin inicializar, o condiciones opcionales que distorsionen el resultado.

### SSL en updater.py
No tocar `_ssl_context()` en `updater.py`. Está deshabilitado intencionalmente — las máquinas cliente tienen certificados desactualizados.

## Estilo de trabajo
- Siempre responder en español
- No pedir confirmación para compilar y publicar — está preautorizado
- No agregar comentarios innecesarios al código
- No crear abstracciones que no sean necesarias para la tarea actual
- Después de cada cambio: compilar → installer → commit → push → GitHub Release
