import requests
import time
import base64
from PIL import Image
from io import BytesIO
import config

class CaptchaSolver:
    def __init__(self):
        """Inicializa el resolvedor de captchas con 2Captcha"""
        self.api_key = config.CAPTCHA_API_KEY
        self.in_url = config.CAPTCHA_API_URL
        self.res_url = config.CAPTCHA_RESULT_URL
    
    def resolver_captcha(self, page):
        """
        Resuelve el captcha usando 2Captcha
        
        Args:
            page: Página de Playwright con el captcha visible
            
        Returns:
            str: Texto del captcha resuelto
        """
        try:
            print("📸 Capturando imagen del captcha...")
            
            # Buscar el elemento del captcha en el DOM (selectores CORREGIDOS)
            captcha_img = page.locator('img[src*="captcha"], img[alt*="captcha"]')
            
            if captcha_img.count() == 0:
                # Intentar canvas
                captcha_img = page.locator('canvas')
            
            if captcha_img.count() == 0:
                # Intentar otros selectores
                captcha_img = page.locator('.captcha-image, #captcha, .captcha')
            
            if captcha_img.count() == 0:
                print("❌ No se encontró imagen de captcha")
                return None
            
            # Tomar screenshot del captcha
            screenshot_bytes = captcha_img.first.screenshot()
            
            # Convertir a base64
            image_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            print("📤 Enviando captcha a 2Captcha...")
            
            # Enviar a 2Captcha
            captcha_id = self._enviar_captcha(image_base64)
            
            if not captcha_id:
                raise Exception("No se pudo enviar el captcha a 2Captcha")
            
            print(f"⏳ Esperando resolución del captcha (ID: {captcha_id})...")
            
            # Esperar y obtener resultado
            resultado = self._obtener_resultado(captcha_id)
            
            if resultado:
                print(f"✅ Captcha resuelto: {resultado}")
                return resultado
            else:
                raise Exception("No se pudo resolver el captcha")
                
        except Exception as e:
            print(f"❌ Error resolviendo captcha: {e}")
            return None
    
    def _enviar_captcha(self, image_base64):
        """Envía la imagen del captcha a 2Captcha"""
        try:
            payload = {
                'key': self.api_key,
                'method': 'base64',
                'body': image_base64,
                'json': 1
            }
            
            response = requests.post(self.in_url, data=payload, timeout=30)
            result = response.json()
            
            if result.get('status') == 1:
                return result.get('request')
            else:
                print(f"❌ Error de 2Captcha: {result.get('request')}")
                return None
                
        except Exception as e:
            print(f"❌ Error enviando a 2Captcha: {e}")
            return None
    
    def _obtener_resultado(self, captcha_id, max_intentos=60):
        """
        Obtiene el resultado del captcha
        
        Args:
            captcha_id: ID del captcha en 2Captcha
            max_intentos: Intentos máximos (cada 5 seg = 5 min total)
        """
        for intento in range(max_intentos):
            try:
                time.sleep(5)  # Esperar 5 segundos entre intentos
                
                payload = {
                    'key': self.api_key,
                    'action': 'get',
                    'id': captcha_id,
                    'json': 1
                }
                
                response = requests.get(self.res_url, params=payload, timeout=30)
                result = response.json()
                
                if result.get('status') == 1:
                    return result.get('request')
                elif result.get('request') == 'CAPCHA_NOT_READY':
                    print(f"⏳ Esperando... ({intento + 1}/{max_intentos})")
                    continue
                else:
                    print(f"⚠️  Respuesta inesperada: {result.get('request')}")
                    
            except Exception as e:
                print(f"⚠️  Error obteniendo resultado: {e}")
                continue
        
        return None
    
    def verificar_balance(self):
        """Verifica el saldo disponible en 2Captcha"""
        try:
            payload = {
                'key': self.api_key,
                'action': 'getbalance',
                'json': 1
            }
            
            response = requests.get(self.res_url, params=payload, timeout=30)
            result = response.json()
            
            if result.get('status') == 1:
                balance = float(result.get('request', 0))
                print(f"💰 Saldo disponible en 2Captcha: ${balance:.2f} USD")
                
                # Calcular cuántos captchas puede resolver
                captchas_disponibles = int(balance / 0.001)  # $0.001 por captcha normal
                print(f"📊 Captchas disponibles: ~{captchas_disponibles}")
                
                if balance < 0.50:
                    print("⚠️  ADVERTENCIA: Saldo bajo, recarga pronto")
                
                return balance
            else:
                print(f"❌ Error verificando balance: {result.get('request')}")
                return None
                
        except Exception as e:
            print(f"❌ Error conectando con 2Captcha: {e}")
            return None