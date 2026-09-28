"""
Cola de trabajos: procesa una persona a la vez, en segundo plano.
"""
import os
import queue
import tempfile
import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

import config
import simit
import supervigilancia
from drive_handler import DriveHandler
from sheets_handler import SheetsHandler

_cola = queue.Queue()
_ids_activos = set()          # evita duplicados si Apps Script reenvía
_lock = threading.Lock()
_trabajando = threading.Event()


# ── API pública ─────────────────────────────────────────
def encolar(trabajo):
    """Devuelve False si ese ID ya está en cola o procesándose."""
    id_noti = trabajo['id_notificacion']
    with _lock:
        if id_noti in _ids_activos:
            return False
        _ids_activos.add(id_noti)
    _cola.put(trabajo)
    print(f'📥 Encolado {id_noti} (en cola: {_cola.qsize()})')
    return True


def tamano_cola():
    return _cola.qsize() + (1 if _trabajando.is_set() else 0)


def iniciar():
    threading.Thread(target=_bucle, daemon=True, name='worker').start()
    threading.Thread(target=_mantener_despierto, daemon=True, name='keepalive').start()


# ── Internos ────────────────────────────────────────────
def _bucle():
    while True:
        trabajo = _cola.get()
        _trabajando.set()
        try:
            procesar_trabajo(trabajo)
        except Exception as e:
            print(f'❌ Error no controlado en {trabajo.get("id_notificacion")}: {e}')
        finally:
            with _lock:
                _ids_activos.discard(trabajo['id_notificacion'])
            _trabajando.clear()
            _cola.task_done()
        if not _cola.empty():
            time.sleep(config.DELAY_SEGUNDOS)


def _mantener_despierto():
    """En el plan gratis de Render, evita que se duerma mientras hay trabajo."""
    while True:
        time.sleep(240)
        if config.URL_PUBLICA and (_trabajando.is_set() or not _cola.empty()):
            try:
                requests.get(f'{config.URL_PUBLICA}/health', timeout=20)
            except Exception:
                pass


def _intentar(funcion, cedula, ruta):
    motivo = None
    for intento in range(1, config.MAX_REINTENTOS + 1):
        resultado, motivo = funcion(cedula, ruta)
        if resultado:
            return resultado, None
        print(f'   ↻ Intento {intento}/{config.MAX_REINTENTOS} falló: {motivo}')
    return None, motivo


def _subir(drive, ruta, nombre):
    try:
        return drive.subir_pdf(ruta, nombre), True
    except Exception as e:
        print(f'   ❌ Error subiendo {nombre}: {e}')
        return 'error subiendo a Drive', False
    finally:
        if os.path.exists(ruta):
            os.remove(ruta)


def procesar_trabajo(trabajo, hacer_callback=True):
    id_noti = trabajo['id_notificacion']
    cedula = str(trabajo['cedula']).strip()
    fecha = datetime.now(ZoneInfo(config.ZONA_HORARIA)).strftime('%Y-%m-%d')
    carpeta = tempfile.mkdtemp()
    print(f'\n{"━" * 50}\n▶ {id_noti} | cédula {cedula}\n{"━" * 50}')

    drive = DriveHandler()

    # 1. SIMIT
    nombre_simit = f'SIMIT_{cedula}_{id_noti}_{fecha}.pdf'
    ruta, motivo = _intentar(simit.descargar_certificado, cedula,
                             os.path.join(carpeta, nombre_simit))
    if ruta:
        link_simit, ok_simit = _subir(drive, ruta, nombre_simit)
    else:
        link_simit, ok_simit = motivo, False

    # 2. Supervigilancia
    nombre_super = f'SUPERVIGILANCIA_{cedula}_{id_noti}_{fecha}.pdf'
    ruta, motivo = _intentar(supervigilancia.descargar_certificado, cedula,
                             os.path.join(carpeta, nombre_super))
    if ruta:
        link_super, ok_super = _subir(drive, ruta, nombre_super)
    else:
        link_super, ok_super = motivo, False

    # 3. Estado
    exitos = ok_simit + ok_super
    estado = 'ok' if exitos == 2 else 'parcial' if exitos == 1 else 'error'

    # 4. Escribir en la hoja
    try:
        SheetsHandler().escribir_resultado(id_noti, link_simit, link_super, estado)
    except Exception as e:
        # Si no se pudo escribir, la fila sigue en "pendiente" y el trigger la reenvía
        print(f'❌ No se pudo escribir en la hoja: {e}')
        return

    # 5. Avisar a Apps Script
    if hacer_callback:
        _callback(id_noti)


def _callback(id_noti):
    payload = {
        'token': config.TOKEN_PROCESO_PYTHON,
        'accion': 'python_terminado',
        'id_notificacion': id_noti,
    }
    for intento in range(3):
        try:
            r = requests.post(config.URL_WEBAPP, json=payload, timeout=120)
            print(f'📨 Callback {id_noti}: {r.status_code} {r.text[:200]}')
            return
        except Exception as e:
            print(f'⚠️ Callback falló ({intento + 1}/3): {e}')
            time.sleep(10)