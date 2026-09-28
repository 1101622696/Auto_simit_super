"""
Busca la cédula en Supervigilancia y genera el PDF de lo que muestra el botón Imprimir.
El diálogo de impresión del navegador no se puede cliquear, así que se anula
window.print y se genera el PDF con page.pdf() (equivale a "Guardar como PDF").
page.pdf() solo funciona en modo headless, por eso este navegador siempre es headless.
"""
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
import config

ANULAR_IMPRESION = 'window.print = function(){}; window.close = function(){};'


def descargar_certificado(cedula, ruta_destino):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True,
                                    args=['--no-sandbox', '--disable-dev-shm-usage'])
        context = browser.new_context(ignore_https_errors=True,
                                      viewport={'width': 1366, 'height': 768})
        context.add_init_script(ANULAR_IMPRESION)   # aplica también a la pestaña nueva
        page = context.new_page()
        try:
            print(f'🛡️  Supervigilancia: {cedula}')
            try:
                page.goto(config.SUPERVIGILANCIA_URL, wait_until='domcontentloaded',
                          timeout=90000)
            except Exception:
                return None, 'página sin respuesta'

            campo = page.locator('#ctl00_contentMaster_TxIdn')
            campo.wait_for(state='visible', timeout=30000)
            campo.fill(cedula)
            page.locator('#ctl00_contentMaster_BtBuscar').click()

            btn_imprimir = page.locator('button.buttons-print')
            try:
                btn_imprimir.first.wait_for(state='visible', timeout=45000)
            except PWTimeout:
                page.screenshot(path=f'debug_super_{cedula}.png')
                return None, 'página sin respuesta'
            page.wait_for_timeout(3000)   # que termine de pintar la tabla

            with context.expect_page(timeout=30000) as info:
                btn_imprimir.first.click()
            popup = info.value
            # Refuerzo por si el init script no alcanzó a aplicarse
            try:
                popup.evaluate(ANULAR_IMPRESION)
            except Exception:
                pass
            popup.wait_for_load_state('load')
            popup.wait_for_timeout(2000)

            destino = popup if not popup.is_closed() else page
            if destino is page:
                print('   ⚠️ La pestaña de impresión se cerró, se imprime la página principal')
                page.emulate_media(media='print')

            destino.pdf(
                path=ruta_destino,
                format='Letter',
                landscape=True,          # la tabla es ancha; cambia a False si prefieres vertical
                print_background=True,
                margin={'top': '1cm', 'bottom': '1cm', 'left': '1cm', 'right': '1cm'},
            )
            print('   ✅ PDF Supervigilancia guardado')
            return ruta_destino, None

        except PWTimeout:
            page.screenshot(path=f'debug_super_{cedula}.png')
            return None, 'página sin respuesta'
        except Exception as e:
            print(f'   ❌ Error Supervigilancia: {e}')
            return None, 'error en Supervigilancia'
        finally:
            browser.close()