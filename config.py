import os
from dotenv import load_dotenv

load_dotenv()

# ── Google ──────────────────────────────────────────────
GOOGLE_SHEET_ID  = os.getenv('GOOGLE_SHEET_ID')
SHEET_NAME       = os.getenv('SHEET_NAME', 'Notificaciones')
CREDENTIALS_FILE = os.getenv('CREDENTIALS_FILE', 'credenciales-sheet.json')
DRIVE_FOLDER_ID  = os.getenv('DRIVE_FOLDER_ID')

# ── Comunicación con Apps Script ────────────────────────
TOKEN_PROCESO_PYTHON = os.getenv('TOKEN_PROCESO_PYTHON')
URL_WEBAPP           = os.getenv('URL_WEBAPP')           # la URL /exec
URL_PUBLICA          = os.getenv('RENDER_EXTERNAL_URL')  # Render la define sola

# ── Comportamiento ──────────────────────────────────────
HEADLESS       = os.getenv('HEADLESS', 'true').lower() == 'true'
MAX_REINTENTOS = int(os.getenv('MAX_REINTENTOS', 2))
DELAY_SEGUNDOS = int(os.getenv('DELAY_SEGUNDOS', 20))    # pausa entre personas
TIMEOUT_SIMIT  = int(os.getenv('TIMEOUT_SIMIT', 120))
ZONA_HORARIA   = 'America/Bogota'

# ── URLs ────────────────────────────────────────────────
SIMIT_URL           = 'https://www.fcm.org.co/simit/'
SUPERVIGILANCIA_URL = 'https://apo.supervigilancia.gov.co/AcreditaPO/BuscaPersona.aspx'

# ── Columnas de la hoja Notificaciones (base 1, igual que COL_NOTI) ──
COL_ID_NOTIFICACION      = 1
COL_LINK_SIMIT           = 12   # L
COL_LINK_SUPERVIGILANCIA = 13   # M
COL_ESTADO_PYTHON        = 14   # N


def validar_config():
    faltantes = [n for n in ('GOOGLE_SHEET_ID', 'DRIVE_FOLDER_ID',
                             'TOKEN_PROCESO_PYTHON', 'URL_WEBAPP')
                 if not globals().get(n)]
    errores = [f'Falta {n} en las variables de entorno' for n in faltantes]
    if not os.path.exists(CREDENTIALS_FILE):
        errores.append(f'No existe el archivo de credenciales: {CREDENTIALS_FILE}')
    return errores