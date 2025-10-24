import os
import sys
from pathlib import Path

def test_imports():
    """Prueba imports de Watson"""
    try:
        from dotenv import load_dotenv
        from ibm_watson_machine_learning import APIClient
        from ibm_watson import DiscoveryV2
        print("✅ Librerías IBM Watson importadas correctamente")
        return True
    except ImportError as e:
        print(f"❌ Error importando librerías: {e}")
        print("💡 Ejecuta: pip install ibm-watson-machine-learning ibm-watson ibm-cloud-sdk-core python-dotenv")
        return False

def test_credentials():
    """Prueba credenciales básicas"""
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ['WATSONX_API_KEY', 'DISCOVERY_API_KEY']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"❌ Faltan variables de entorno: {missing}")
        print("💡 Configura el archivo .env con tus credenciales IBM Watson")
        return False
    
    print("✅ Credenciales cargadas correctamente")
    return True

def test_dataset():
    """Prueba dataset procesado"""
    dataset_path = Path('dataset_processed_watsonx.jsonl')
    if not dataset_path.exists():
        print("❌ Dataset procesado no encontrado")
        print("💡 Ejecuta: python test_feature_engineering.py")
        return False
    
    try:
        import jsonlines
        with jsonlines.open(dataset_path) as reader:
            docs = list(reader)
        
        print(f"✅ Dataset cargado: {len(docs)} documentos")
        return True
    except Exception as e:
        print(f"❌ Error cargando dataset: {e}")
        return False

def main():
    print("🧪 PRUEBAS SISTEMA DECODE-EV WATSON")
    print("=" * 40)
    
    tests = [
        ("Imports Watson", test_imports),
        ("Dataset", test_dataset),
        ("Credenciales", test_credentials)
    ]
    
    passed = 0
    for name, test_func in tests:
        print(f"\n🔍 Probando {name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ Falló: {name}")
    
    print(f"\n📊 Resumen: {passed}/{len(tests)} pruebas pasaron")
    
    if passed == len(tests):
        print("✅ Sistema listo para IBM Watson!")
        print("🚀 Ejecuta: python setup_watson.py")
    else:
        print("⚠️ Revisa la configuración antes de continuar")
        
        # Ayuda específica
        print("\n💡 SIGUIENTE PASO:")
        if passed == 0:
            print("1. Instala las dependencias: pip install ibm-watson-machine-learning ibm-watson")
        elif passed == 1:
            print("1. Configura archivo .env con credenciales IBM Watson")
        elif passed == 2:
            print("1. Instala Watson SDK: pip install ibm-watson-machine-learning ibm-watson")

if __name__ == "__main__":
    main()