"""
Descarga el PDF de SIMIT para una cédula:
  - con valores  → "Guardar estado" → "Descargar PDF"
  - sin valores  → "Descargar paz y salvo" → "Descargar"
Devuelve (ruta_pdf, None) si sale bien, o (None, motivo) si falla.
"""
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
import config

USER_AGENT = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
              '(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36')


def _cerrar_modal_publicitario(page):
    try:
        x = page.locator('span.modal-info-close')
        x.first.wait_for(state='visible', timeout=15000)
        x.first.click()
        print('   ✖ Modal publicitario cerrado')
        page.wait_for_timeout(1000)
    except PWTimeout:
        print('   (no apareció el modal publicitario)')
    except Exception as e:
        print(f'   ⚠️ No se pudo cerrar el modal: {e}')
        page.keyboard.press('Escape')


def descargar_certificado(cedula, ruta_destino):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=config.HEADLESS,
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox',
                  '--disable-dev-shm-usage'],
        )
        context = browser.new_context(
            user_agent=USER_AGENT,
            viewport={'width': 1366, 'height': 768},
            accept_downloads=True,
        )
        page = context.new_page()
        try:
            print(f'🚗 SIMIT: {cedula}')
            try:
                page.goto(config.SIMIT_URL, wait_until='domcontentloaded', timeout=90000)
            except Exception:
                return None, 'página sin respuesta'

            _cerrar_modal_publicitario(page)

            # Buscar la cédula
            campo = page.locator('#txtBusqueda')
            campo.wait_for(state='visible', timeout=30000)
            campo.fill(cedula)
            page.locator('#consultar').click(force=True)

            # Esperar cualquiera de los dos botones posibles
            btn_estado = page.locator('a[data-target="#modal-estado-cuenta"]')
            btn_paz    = page.locator('a:has-text("Descargar paz y salvo")')
            try:
                btn_estado.or_(btn_paz).first.wait_for(state='visible', timeout=60000)
            except PWTimeout:
                page.screenshot(path=f'debug_simit_{cedula}.png')
                return None, 'no encontrado'

            if btn_estado.first.is_visible():
                print('   Tiene valores → Guardar estado')
                btn_estado.first.click()
                modal = page.locator('#modal-estado-cuenta')
                modal.wait_for(state='visible', timeout=15000)
                boton_final = modal.locator('a:has-text("Descargar PDF")').first
            else:
                print('   Sin valores → Paz y salvo')
                btn_paz.first.click()
                boton_final = page.locator(
                    'button.btn-primary:has-text("Descargar"):visible').first
                boton_final.wait_for(state='visible', timeout=15000)

            with page.expect_download(timeout=90000) as info:
                boton_final.click()
            info.value.save_as(ruta_destino)
            print(f'   ✅ PDF SIMIT guardado')
            return ruta_destino, None

        except PWTimeout:
            page.screenshot(path=f'debug_simit_{cedula}.png')
            return None, 'página sin respuesta'
        except Exception as e:
            print(f'   ❌ Error SIMIT: {e}')
            return None, 'error en SIMIT'
        finally:
            browser.close()