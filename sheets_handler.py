import gspread
from gspread.utils import rowcol_to_a1
import config

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
]


class SheetsHandler:
    def __init__(self):
        client = gspread.service_account(filename=config.CREDENTIALS_FILE, scopes=SCOPES)
        self.sheet = client.open_by_key(config.GOOGLE_SHEET_ID).worksheet(config.SHEET_NAME)

    def buscar_fila(self, id_notificacion):
        """Devuelve el número de fila (base 1) del ID, o None si no existe."""
        ids = self.sheet.col_values(config.COL_ID_NOTIFICACION)
        objetivo = str(id_notificacion).strip()
        for i, valor in enumerate(ids, start=1):
            if str(valor).strip() == objetivo:
                return i
        return None

    def escribir_resultado(self, id_notificacion, link_simit, link_super, estado):
        """Escribe LINK_SIMIT, LINK_SUPERVIGILANCIA y ESTADO_PYTHON en una sola llamada."""
        fila = self.buscar_fila(id_notificacion)
        if not fila:
            raise ValueError(f'No se encontró {id_notificacion} en la hoja')

        inicio = rowcol_to_a1(fila, config.COL_LINK_SIMIT)
        fin    = rowcol_to_a1(fila, config.COL_ESTADO_PYTHON)
        self.sheet.update(
            range_name=f'{inicio}:{fin}',
            values=[[link_simit, link_super, estado]],
            value_input_option='RAW',
        )
        print(f'💾 {id_notificacion} (fila {fila}) → {estado}')