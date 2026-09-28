#!/usr/bin/env python3
"""
SIMIT Automation - Consulta masiva de comparendos
Versión: 2.0 (con 2Captcha)
"""

import sys
import config
from scraper import SimitScraper

def mostrar_banner():
    """Muestra el banner del script"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        🚗 SIMIT AUTOMATION - Playwright + 2Captcha 🤖       ║
║                                                              ║
║              Consulta automática de comparendos             ║
║                      Versión 2.0                            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)

def mostrar_configuracion():
    """Muestra la configuración actual"""
    print("\n⚙️  CONFIGURACIÓN:")
    print(f"   📊 Google Sheet ID: {config.GOOGLE_SHEET_ID[:20]}...")
    print(f"   📄 Hoja: {config.SHEET_NAME}")
    print(f"   🔐 2Captcha: {'✅ Configurado' if config.CAPTCHA_API_KEY else '❌ No configurado'}")
    print(f"   ⏱️  Delay entre consultas: {config.DELAY_MINUTOS} minutos")
    print(f"   👁️  Navegador visible: {'No (headless)' if config.HEADLESS else 'Sí'}")
    print(f"   🔄 Reintentos máximos: {config.MAX_REINTENTOS}")

def main():
    """Función principal"""
    try:
        mostrar_banner()
        
        # Validar configuración
        print("\n🔍 Validando configuración...")
        if not config.validar_config():
            print("\n❌ La configuración tiene errores. Por favor corrige el archivo .env")
            sys.exit(1)
        
        print("✅ Configuración válida")
        
        mostrar_configuracion()
        
        # Confirmar ejecución
        print("\n" + "─" * 60)
        respuesta = input("\n¿Deseas iniciar el proceso? (s/n): ").strip().lower()
        
        if respuesta != 's':
            print("\n👋 Proceso cancelado")
            sys.exit(0)
        
        print("\n🚀 Iniciando proceso de scraping...\n")
        
        # Crear scraper y procesar
        scraper = SimitScraper()
        scraper.procesar_cedulas()
        
        print("\n✅ Proceso finalizado correctamente")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso interrumpido por el usuario")
        print("💡 Los datos procesados hasta ahora se guardaron correctamente")
        print("💡 Puedes reiniciar el script para continuar desde donde quedó")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        print("\n💡 SOLUCIONES COMUNES:")
        print("   1. Verifica tu conexión a Internet")
        print("   2. Confirma que el archivo .env esté configurado correctamente")
        print("   3. Verifica que credenciales-sheet.json exista")
        print("   4. Confirma que tienes saldo en 2Captcha")
        sys.exit(1)

if __name__ == "__main__":
    main()