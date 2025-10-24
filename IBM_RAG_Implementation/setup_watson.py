import os
import sys
from pathlib import Path

def check_env_file():
    """Verifica que el archivo .env exista y tenga credenciales"""
    env_path = Path('.env')
    if not env_path.exists():
        print("❌ Archivo .env no encontrado")
        print("📋 Pasos para crear .env:")
        print("1. Renombra .env.template a .env")
        print("2. Completa tus credenciales IBM Watson")
        return False
    
    content = env_path.read_text()
    required_vars = ['WATSONX_API_KEY', 'DISCOVERY_API_KEY']
    
    for var in required_vars:
        if f"{var}=tu_" in content:
            print(f"⚠️ Variable {var} no configurada en .env")
            return False
    
    print("✅ Archivo .env configurado correctamente")
    return True

def main():
    print("🚀 Configuración inicial IBM Watson para DECODE-EV")
    print("=" * 50)
    
    if not check_env_file():
        sys.exit(1)
    
    try:
        print("\n🔄 Ejecutando configuración Watson...")
        result1 = os.system("python 01_watsonx_setup_REAL.py")
        
        print("\n🔄 Probando sistema RAG...")
        result2 = os.system("python 03_watson_rag_system_REAL.py")
        
        if result1 == 0 and result2 == 0:
            print("\n✅ Configuración completada!")
            print("🎯 Siguiente paso: ejecutar dashboard con 'streamlit run streamlit_dashboard_watson.py'")
        else:
            print("\n⚠️ Hubo algunos errores en la configuración")
            print("💡 Revisa los logs anteriores para más detalles")
        
    except Exception as e:
        print(f"❌ Error en configuración: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()