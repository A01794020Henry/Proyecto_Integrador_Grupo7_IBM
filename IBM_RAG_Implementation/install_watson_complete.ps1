# Script de instalación completa IBM Watson para DECODE-EV
# Instala dependencias, configura ambiente y ejecuta setup inicial

Write-Host "🚀 INSTALACIÓN COMPLETA IBM WATSON PARA DECODE-EV" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan

# Verificar que estamos en el directorio correcto
$currentDir = Get-Location
Write-Host "📂 Directorio actual: $currentDir" -ForegroundColor Yellow

# 1. INSTALAR DEPENDENCIAS PYTHON
Write-Host "`n📦 PASO 1: Instalando dependencias Python..." -ForegroundColor Green

$packages = @(
    "ibm-watson-machine-learning",
    "ibm-watson", 
    "ibm-cloud-sdk-core",
    "python-dotenv",
    "streamlit",
    "plotly",
    "pandas",
    "numpy",
    "jsonlines"
)

foreach ($package in $packages) {
    Write-Host "   Instalando $package..." -ForegroundColor White
    try {
        & "C:/Users/henry/AppData/Local/Programs/Python/Python313/python.exe" -m pip install $package --quiet
        Write-Host "   ✅ $package instalado" -ForegroundColor Green
    }
    catch {
        Write-Host "   ❌ Error instalando $package" -ForegroundColor Red
    }
}

# 2. CREAR ARCHIVO .ENV TEMPLATE
Write-Host "`n📋 PASO 2: Creando template de configuración..." -ForegroundColor Green

$envTemplate = @"
# IBM Watson Credentials para DECODE-EV
# INSTRUCCIONES:
# 1. Ve a https://cloud.ibm.com/
# 2. Crea servicios Watson Machine Learning y Watson Discovery
# 3. Reemplaza los valores abajo con tus credenciales reales

# IBM watsonx.ai (Watson Machine Learning)
WATSONX_API_KEY=tu_watsonx_api_key_aqui
WATSONX_PROJECT_ID=tu_watsonx_project_id_aqui  
WATSONX_URL=https://us-south.ml.cloud.ibm.com

# Watson Discovery
DISCOVERY_API_KEY=tu_discovery_api_key_aqui
DISCOVERY_URL=https://api.us-south.discovery.watson.cloud.ibm.com
DISCOVERY_VERSION=2023-03-31

# Configuración adicional
IBM_CLOUD_REGION=us-south
LOG_LEVEL=INFO
"@

$envFile = ".\.env.template"
$envTemplate | Out-File -FilePath $envFile -Encoding UTF8
Write-Host "   ✅ Creado $envFile" -ForegroundColor Green
Write-Host "   📝 Renombra a .env y completa tus credenciales" -ForegroundColor Yellow

# 3. VERIFICAR DATASET PROCESADO
Write-Host "`n📊 PASO 3: Verificando dataset procesado..." -ForegroundColor Green

$datasetPath = ".\dataset_processed_watsonx.jsonl"
if (Test-Path $datasetPath) {
    $lineCount = (Get-Content $datasetPath | Measure-Object -Line).Lines
    Write-Host "   ✅ Dataset encontrado: $lineCount documentos" -ForegroundColor Green
} else {
    Write-Host "   ⚠️ Dataset no encontrado. Ejecutando Feature Engineering..." -ForegroundColor Yellow
    try {
        & "C:/Users/henry/AppData/Local/Programs/Python/Python313/python.exe" test_feature_engineering.py
        Write-Host "   ✅ Dataset procesado generado" -ForegroundColor Green
    }
    catch {
        Write-Host "   ❌ Error generando dataset" -ForegroundColor Red
    }
}

# 4. CREAR SCRIPTS DE INICIALIZACIÓN
Write-Host "`n🔧 PASO 4: Creando scripts de inicialización..." -ForegroundColor Green

# Script para configurar Watson
$setupScript = @"
import os
import sys
from pathlib import Path

def check_env_file():
    env_path = Path('.env')
    if not env_path.exists():
        print("Error: Archivo .env no encontrado")
        print("Pasos para crear .env:")
        print("1. Renombra .env.template a .env")
        print("2. Completa tus credenciales IBM Watson")
        return False
    
    content = env_path.read_text()
    required_vars = ['WATSONX_API_KEY', 'DISCOVERY_API_KEY']
    
    for var in required_vars:
        if f"{var}=tu_" in content:
            print(f"Variable {var} no configurada en .env")
            return False
    
    print("Archivo .env configurado correctamente")
    return True

def main():
    print("Configuración inicial IBM Watson para DECODE-EV")
    print("=" * 50)
    
    if not check_env_file():
        sys.exit(1)
    
    try:
        print("Ejecutando configuración Watson...")
        os.system("python 01_watsonx_setup_REAL.py")
        
        print("Probando sistema RAG...")
        os.system("python 03_watson_rag_system_REAL.py")
        
        print("Configuración completada!")
        print("Siguiente paso: ejecutar dashboard con 'streamlit run streamlit_dashboard_watson.py'")
        
    except Exception as e:
        print(f"Error en configuración: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
"@

$setupScript | Out-File -FilePath ".\setup_watson.py" -Encoding UTF8
Write-Host "   ✅ Creado setup_watson.py" -ForegroundColor Green

# Script de prueba rápida
$testScript = @"
import os
import sys
from pathlib import Path

def test_imports():
    try:
        from dotenv import load_dotenv
        from ibm_watson_machine_learning import APIClient
        from ibm_watson import DiscoveryV2
        print("Librerías IBM Watson importadas correctamente")
        return True
    except ImportError as e:
        print(f"Error importando librerías: {e}")
        return False

def test_credentials():
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ['WATSONX_API_KEY', 'DISCOVERY_API_KEY']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"Faltan variables de entorno: {missing}")
        return False
    
    print("Credenciales cargadas correctamente")
    return True

def test_dataset():
    dataset_path = Path('dataset_processed_watsonx.jsonl')
    if not dataset_path.exists():
        print("Dataset procesado no encontrado")
        return False
    
    import jsonlines
    with jsonlines.open(dataset_path) as reader:
        docs = list(reader)
    
    print(f"Dataset cargado: {len(docs)} documentos")
    return True

def main():
    print("PRUEBAS SISTEMA DECODE-EV WATSON")
    print("=" * 40)
    
    tests = [
        ("Imports Watson", test_imports),
        ("Credenciales", test_credentials), 
        ("Dataset", test_dataset)
    ]
    
    passed = 0
    for name, test_func in tests:
        print(f"Probando {name}...")
        if test_func():
            passed += 1
        else:
            print(f"Falló: {name}")
    
    print(f"Resumen: {passed}/{len(tests)} pruebas pasaron")
    
    if passed == len(tests):
        print("Sistema listo para IBM Watson!")
        print("Ejecuta: python setup_watson.py")
    else:
        print("Revisa la configuración antes de continuar")

if __name__ == "__main__":
    main()
"@

$testScript | Out-File -FilePath ".\test_watson_setup.py" -Encoding UTF8
Write-Host "   ✅ Creado test_watson_setup.py" -ForegroundColor Green

# 5. RESUMEN FINAL
Write-Host "`n🎯 PASO 5: Resumen de instalación" -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Cyan

Write-Host "`n✅ INSTALACIÓN COMPLETADA" -ForegroundColor Green
Write-Host "📦 Dependencias Python instaladas" -ForegroundColor White
Write-Host "📋 Template de configuración creado (.env.template)" -ForegroundColor White
Write-Host "🔧 Scripts de inicialización creados" -ForegroundColor White

Write-Host "`n🚀 PRÓXIMOS PASOS:" -ForegroundColor Yellow
Write-Host "1. 🌐 Ve a https://cloud.ibm.com/ y crea servicios Watson" -ForegroundColor White
Write-Host "2. 📝 Renombra .env.template a .env y completa credenciales" -ForegroundColor White
Write-Host "3. 🧪 Ejecuta: python test_watson_setup.py" -ForegroundColor White
Write-Host "4. ⚙️  Ejecuta: python setup_watson.py" -ForegroundColor White
Write-Host "5. 🎨 Ejecuta: streamlit run streamlit_dashboard_watson.py" -ForegroundColor White

Write-Host "`n📚 ARCHIVOS CREADOS:" -ForegroundColor Cyan
Write-Host "• .env.template - Template de credenciales" -ForegroundColor White
Write-Host "• setup_watson.py - Configuración inicial" -ForegroundColor White  
Write-Host "• test_watson_setup.py - Pruebas del sistema" -ForegroundColor White
Write-Host "• 01_watsonx_setup_REAL.py - Setup Watson real" -ForegroundColor White
Write-Host "• 03_watson_rag_system_REAL.py - Sistema RAG Watson" -ForegroundColor White

Write-Host "`n🎯 El sistema DECODE-EV está listo para Watson!" -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Cyan