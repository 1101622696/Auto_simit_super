"""
Servidor que recibe las peticiones de Apps Script.
Local:   uvicorn server:app --port 8000
Render:  lo arranca el Dockerfile
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

import config
import worker


@asynccontextmanager
async def lifespan(app):
    errores = config.validar_config()
    if errores:
        print('\n'.join('❌ ' + e for e in errores))
    worker.iniciar()
    print('🚀 Servidor listo')
    yield


app = FastAPI(lifespan=lifespan)


@app.get('/health')
def health():
    return {'ok': True, 'en_cola': worker.tamano_cola()}


@app.post('/procesar')
async def procesar(request: Request):
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({'recibido': False, 'error': 'JSON inválido'}, status_code=400)

    if data.get('token') != config.TOKEN_PROCESO_PYTHON:
        return JSONResponse({'recibido': False, 'error': 'No autorizado'}, status_code=401)

    id_noti = str(data.get('id_notificacion', '')).strip()
    cedula = str(data.get('cedula', '')).strip()
    if not id_noti or not cedula:
        return JSONResponse({'recibido': False, 'error': 'Faltan id_notificacion o cedula'},
                            status_code=400)

    nuevo = worker.encolar({**data, 'id_notificacion': id_noti, 'cedula': cedula})
    return JSONResponse({'recibido': True, 'duplicado': not nuevo}, status_code=202)