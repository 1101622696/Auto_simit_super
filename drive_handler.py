from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import config

SCOPES = ['https://www.googleapis.com/auth/drive']


class DriveHandler:
    def __init__(self):
        creds = Credentials.from_service_account_file(config.CREDENTIALS_FILE, scopes=SCOPES)
        self.service = build('drive', 'v3', credentials=creds, cache_discovery=False)

    def subir_pdf(self, ruta_local, nombre):
        """Sube el PDF a la carpeta de la unidad compartida y devuelve el link."""
        metadata = {'name': nombre, 'parents': [config.DRIVE_FOLDER_ID]}
        media = MediaFileUpload(ruta_local, mimetype='application/pdf', resumable=False)
        archivo = self.service.files().create(
            body=metadata,
            media_body=media,
            fields='id, webViewLink',
            supportsAllDrives=True,   # obligatorio para unidades compartidas
        ).execute()
        print(f'☁️  Subido a Drive: {nombre}')
        return archivo['webViewLink']