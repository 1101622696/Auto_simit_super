"""
Prueba una persona sin servidor ni Apps Script.
Uso:  python probar_local.py NOTI-0010 1062308342
Agrega --callback al final si quieres que también avise a Apps Script.
"""
import sys
import config
from worker import procesar_trabajo

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Uso: python probar_local.py NOTI-0010 1062308342 [--callback]')
        sys.exit(1)
    errores = config.validar_config()
    if errores:
        print('\n'.join(errores))
        sys.exit(1)
    procesar_trabajo(
        {'id_notificacion': sys.argv[1], 'cedula': sys.argv[2]},
        hacer_callback='--callback' in sys.argv,
    )