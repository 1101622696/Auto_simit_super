from playwright.sync_api import sync_playwright
import time
import config
from sheets_handler import SheetsHandler
from captcha_solver import CaptchaSolver

class SimitScraper:
    def __init__(self):
        """Inicializa el scraper"""
        self.sheets = SheetsHandler()
        self.captcha_solver = CaptchaSolver()
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.pagina_cargada = False
    
    def iniciar_navegador(self):
        """Inicia el navegador de Playwright"""
        print("🌐 Iniciando navegador...")
        
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=config.HEADLESS,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        self.context = self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
            viewport={'width': 1366, 'height': 768}
        )
        
        self.page = self.context.new_page()
        print("✅ Navegador iniciado")
    
    def cerrar_navegador(self):
        """Cierra el navegador"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        print("🔒 Navegador cerrado")
    
    def cargar_pagina_inicial(self):
        """Carga la página de SIMIT solo la primera vez"""
        if self.pagina_cargada:
            print("♻️  Reutilizando página ya cargada")
            return
        
        print("🌐 Cargando página de SIMIT por primera vez...")
        try:
            self.page.goto(config.SIMIT_URL, wait_until='domcontentloaded', timeout=90000)
            print("✅ Página cargada")
            time.sleep(3)
            
            print("\n" + "═" * 60)
            print("⚠️  ATENCIÓN: Cierra manualmente el modal publicitario")
            print("   (Dale click en la X del anuncio)")
            print("   Esperando 15 segundos...")
            print("═" * 60 + "\n")
            
            time.sleep(15)
            
            self.pagina_cargada = True
            print("✅ Listo para procesar cédulas\n")
            
        except Exception as e:
            print(f"⚠️  Error cargando página: {e}")
            print("🔄 Reintentando...")
            self.page.goto(config.SIMIT_URL, timeout=90000)
            time.sleep(15)
            self.pagina_cargada = True
    
    def limpiar_campo_busqueda(self):
        """Limpia el campo de búsqueda para nueva consulta"""
        try:
            input_cedula = self.page.locator('#txtBusqueda')
            input_cedula.fill('')
            time.sleep(0.5)
        except:
            pass
    
    def consultar_cedula(self, cedula):
        """
        Consulta una cédula en SIMIT (sin recargar página)
        
        Args:
            cedula: Número de cédula a consultar
            
        Returns:
            dict: Datos extraídos o None si hay error
        """
        try:
            print(f"🔍 Consultando cédula: {cedula}")
            
            # 1. Cargar página solo la primera vez
            self.cargar_pagina_inicial()
            
            # 2. Limpiar campo de búsqueda
            if self.pagina_cargada:
                self.limpiar_campo_busqueda()
            
            # 3. Ingresar cédula
            try:
                self.page.wait_for_selector('#txtBusqueda', timeout=10000)
                input_cedula = self.page.locator('#txtBusqueda')
                input_cedula.fill(cedula)
                print("✅ Cédula ingresada")
                time.sleep(1)
            except Exception as e:
                print(f"⚠️  Error llenando cédula: {e}")
                return None
            
            # 4. Click en buscar (ID diferente según contexto)
            try:
                if not self.pagina_cargada or self.page.locator('#consultar').count() > 0:
                    btn_id = '#consultar'
                else:
                    btn_id = '#btnNumDocPlaca'
                
                btn_buscar = self.page.locator(btn_id)
                self.page.wait_for_selector(btn_id, timeout=10000)
                btn_buscar.click(force=True)
                print(f"✅ Click en buscar (botón: {btn_id})")
                time.sleep(3)
                
            except Exception as e:
                print(f"⚠️  Error haciendo click: {e}")
                try:
                    js_code = """
                        if (document.getElementById('consultar')) {
                            document.getElementById('consultar').click();
                        } else if (document.getElementById('btnNumDocPlaca')) {
                            document.getElementById('btnNumDocPlaca').click();
                        }
                    """
                    self.page.evaluate(js_code)
                    print("✅ Click ejecutado vía JavaScript")
                    time.sleep(3)
                except:
                    return None
            
            # 5. Detectar y resolver captcha
            if self._hay_captcha():
                print("🔐 Captcha detectado, resolviendo...")
                respuesta_captcha = self.captcha_solver.resolver_captcha(self.page)
                
                if respuesta_captcha:
                    self._ingresar_captcha(respuesta_captcha)
                    time.sleep(5)
                else:
                    print("❌ No se pudo resolver el captcha")
                    return None
            
            # 6. Esperar y extraer datos
            print("⏳ Esperando resultados...")
            time.sleep(8)
            
            datos = self._extraer_datos()
            return datos
            
        except Exception as e:
            print(f"❌ Error en consulta: {e}")
            return None
    
    def _hay_captcha(self):
        """Detecta si hay un captcha en la página"""
        try:
            time.sleep(2)
            
            captcha_img = self.page.locator('img[src*="captcha"], img[alt*="captcha"]').count()
            captcha_input = self.page.locator('input[name="captcha"], input[id="captcha"]').count()
            captcha_div = self.page.locator('#captcha, .captcha-container').count()
            
            tiene_captcha = (captcha_img > 0 or captcha_input > 0 or captcha_div > 0)
            
            if tiene_captcha:
                print("🔐 Captcha detectado")
            else:
                print("✅ Sin captcha")
            
            return tiene_captcha
            
        except Exception as e:
            print(f"⚠️  Error detectando captcha: {e}")
            return False
    
    def _ingresar_captcha(self, respuesta):
        """Ingresa la respuesta del captcha"""
        try:
            input_captcha = self.page.locator('input[name*="captcha"], input[id*="captcha"]').first
            input_captcha.fill(respuesta)
            
            btn_enviar = self.page.locator('button:has-text("Enviar"), button:has-text("Validar"), button[type="submit"]').first
            btn_enviar.click()
            
            print("✅ Captcha ingresado y enviado")
            
        except Exception as e:
            print(f"⚠️  Error ingresando captcha: {e}")
    
    def _extraer_datos(self):
        """Extrae los datos de multas de la página"""
        try:
            print("📊 Extrayendo datos...")
            
            time.sleep(5)
            
            try:
                self.page.wait_for_selector('text=/Comparendos/', timeout=15000)
                print("✅ Resumen encontrado")
            except Exception as e:
                print(f"⚠️  Timeout esperando resumen: {e}")
                self.page.screenshot(path=f'debug_timeout_{int(time.time())}.png')
                return None
            
            try:
                comparendos_elem = self.page.locator('text=/Comparendos:/').first
                multas_elem = self.page.locator('text=/Multas:/').first
                total_elem = self.page.locator('text=/Total:/').first
                
                # Extraer números de <span>
                try:
                    num_comparendos_span = comparendos_elem.locator('..').locator('span').first.text_content().strip()
                    num_multas_span = multas_elem.locator('..').locator('span').first.text_content().strip()
                    
                    comp_digitos = ''.join(filter(str.isdigit, num_comparendos_span))
                    mult_digitos = ''.join(filter(str.isdigit, num_multas_span))
                    
                    num_comparendos = int(comp_digitos) if comp_digitos else 0
                    num_multas = int(mult_digitos) if mult_digitos else 0
                    
                except:
                    comparendos_text = comparendos_elem.locator('..').text_content()
                    multas_text = multas_elem.locator('..').text_content()
                    
                    comp_parte = comparendos_text.split(':')[1].strip() if ':' in comparendos_text else '0'
                    mult_parte = multas_text.split(':')[1].strip() if ':' in multas_text else '0'
                    
                    comp_digitos = ''.join(filter(str.isdigit, comp_parte))
                    mult_digitos = ''.join(filter(str.isdigit, mult_parte))
                    
                    num_comparendos = int(comp_digitos) if comp_digitos else 0
                    num_multas = int(mult_digitos) if mult_digitos else 0
                
                print(f"✅ Comparendos: {num_comparendos}, Multas: {num_multas}")
                
                # Extraer total
                try:
                    total_span = total_elem.locator('..').locator('span').first.text_content().strip()
                    total = total_span if total_span.startswith('$') else '$ ' + total_span
                except:
                    total_text = total_elem.locator('..').text_content()
                    total = total_text.split(':')[1].strip() if ':' in total_text else '$0'
                    if not total.startswith('$'):
                        total = '$ ' + total
                
                print(f"✅ Total: {total}")
                
                # Buscar acuerdos de pago
                num_acuerdos = 0
                try:
                    acuerdos_elem = self.page.locator('text=/Acuerdos de pago:/').first
                    
                    try:
                        acuerdos_span = acuerdos_elem.locator('..').locator('span').first.text_content().strip()
                        acu_digitos = ''.join(filter(str.isdigit, acuerdos_span))
                    except:
                        acuerdos_text = acuerdos_elem.locator('..').text_content()
                        acu_parte = acuerdos_text.split(':')[1].strip() if ':' in acuerdos_text else '0'
                        acu_digitos = ''.join(filter(str.isdigit, acu_parte))
                    
                    num_acuerdos = int(acu_digitos) if acu_digitos else 0
                    if num_acuerdos > 0:
                        print(f"✅ Acuerdos de pago: {num_acuerdos}")
                except:
                    pass
                
                # CASO 1: Sin nada
                if num_comparendos == 0 and num_multas == 0 and num_acuerdos == 0:
                    return {
                        'estado': '✅ Procesado',
                        'comparendos': 0,
                        'multas': 0,
                        'acuerdos': 0,
                        'descripciones': 'Sin comparendos ni multas',
                        'valores': '-',
                        'total': total
                    }
                
                # CASO 2: Hay acuerdos de pago
                if num_acuerdos > 0:
                    descripciones = []
                    valores = []
                    
                    try:
                        self.page.wait_for_selector('table tbody tr', timeout=5000)
                        filas = self.page.locator('table tbody tr').all()
                        
                        for i, fila in enumerate(filas[:num_acuerdos], 1):
                            try:
                                celdas = fila.locator('td').all()
                                
                                if len(celdas) >= 3:
                                    secretaria = celdas[1].text_content().strip()
                                    valor = celdas[-1].text_content().strip()
                                    
                                    descripciones.append(f"Acuerdo {i}: {secretaria}")
                                    valores.append(valor)
                            except:
                                continue
                    
                    except Exception as e:
                        print(f"⚠️  No se pudieron extraer detalles")
                    
                    if not descripciones:
                        descripciones = [f'Acuerdo {i+1}' for i in range(num_acuerdos)]
                        valores = ['Ver SIMIT'] * num_acuerdos
                    
                    return {
                        'estado': '✅ Procesado',
                        'comparendos': num_comparendos,
                        'multas': num_multas,
                        'acuerdos': num_acuerdos,
                        'descripciones': ' | '.join(descripciones),
                        'valores': ' | '.join(valores),
                        'total': total
                    }
                
                # CASO 3: Hay comparendos/multas normales
                if num_comparendos > 0 or num_multas > 0:
                    return {
                        'estado': '✅ Procesado',
                        'comparendos': num_comparendos,
                        'multas': num_multas,
                        'acuerdos': num_acuerdos,
                        'descripciones': f'{num_comparendos} comparendos, {num_multas} multas',
                        'valores': 'Ver detalle en SIMIT',
                        'total': total
                    }
                
            except Exception as e:
                print(f"⚠️  Error extrayendo datos: {e}")
                
                try:
                    mensaje = self.page.locator('text=/no posee.*multas/i').first.text_content()
                    
                    return {
                        'estado': '✅ Procesado',
                        'comparendos': 0,
                        'multas': 0,
                        'acuerdos': 0,
                        'descripciones': 'Sin multas pendientes',
                        'valores': '-',
                        'total': '$0'
                    }
                except:
                    pass
                
                self.page.screenshot(path=f'debug_{int(time.time())}.png')
                raise
            
        except Exception as e:
            print(f"❌ Error extrayendo datos: {e}")
            return None
    
    def procesar_cedulas(self):
        """Procesa todas las cédulas pendientes"""
        try:
            balance = self.captcha_solver.verificar_balance()
            if balance is None or balance < 0.50:
                print("\n❌ ERROR: Saldo insuficiente en 2Captcha")
                print("👉 Recarga en: https://2captcha.com")
                return
            
            cedulas = self.sheets.obtener_cedulas_pendientes()
            
            if not cedulas:
                print("\n✅ No hay cédulas pendientes para procesar")
                return
            
            total = len(cedulas)
            print(f"\n📋 Total de cédulas pendientes: {total}")
            
            self.iniciar_navegador()
            
            for i, item in enumerate(cedulas, 1):
                fila = item['fila']
                cedula = item['cedula']
                
                print(f"\n{'━' * 60}")
                print(f"[{i}/{total}] Cédula: {cedula} (Fila {fila})")
                print(f"{'━' * 60}")
                
                self.sheets.actualizar_estado(fila, '⏳ Procesando...')
                
                datos = self.consultar_cedula(cedula)
                
                if datos:
                    self.sheets.guardar_resultados(fila, datos)
                    print(f"✅ Procesada exitosamente")
                else:
                    self.sheets.marcar_error(fila, 'Error en consulta')
                    print(f"❌ Error procesando")
                
                progreso = self.sheets.obtener_progreso()
                print(f"\n📊 Progreso: {progreso['procesadas']}/{progreso['total']} ({progreso['porcentaje']}%)")
                
                if i < total:
                    delay_seg = config.DELAY_MINUTOS * 60
                    print(f"⏳ Esperando {config.DELAY_MINUTOS} min...\n")
                    time.sleep(delay_seg)
            
            print(f"\n{'═' * 60}")
            print("🎉 PROCESO COMPLETADO")
            print(f"{'═' * 60}")
            
            progreso_final = self.sheets.obtener_progreso()
            print(f"\n📊 RESUMEN FINAL:")
            print(f"   ✅ Procesadas: {progreso_final['procesadas']}")
            print(f"   ⏳ Pendientes: {progreso_final['pendientes']}")
            print(f"   📈 Completado: {progreso_final['porcentaje']}%")
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Proceso interrumpido")
            print("💡 Puedes reiniciar y continuará desde donde quedó")
        except Exception as e:
            print(f"\n❌ Error general: {e}")
        finally:
            self.cerrar_navegador()