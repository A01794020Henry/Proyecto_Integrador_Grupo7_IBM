# IBM Watson Installation Script para DECODE-EV
# Instala dependencias y configura ambiente

Write-Host "INSTALACION COMPLETA IBM WATSON PARA DECODE-EV" -ForegroundColor Cyan
Write-Host "=" -ForegroundColor Cyan

# Variables
$pythonExe = "C:/Users/henry/AppData/Local/Programs/Python/Python313/python.exe"

# PASO 1: INSTALAR DEPENDENCIAS
Write-Host "`nPASO 1: Instalando dependencias Python..." -ForegroundColor Green

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
        & $pythonExe -m pip install $package --quiet
        Write-Host "   OK $package instalado" -ForegroundColor Green
    }
    catch {
        Write-Host "   ERROR instalando $package" -ForegroundColor Red
    }
}

# PASO 2: CREAR TEMPLATE .ENV
Write-Host "`nPASO 2: Creando template de configuracion..." -ForegroundColor Green

$envContent = @"
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

# Configuracion adicional
IBM_CLOUD_REGION=us-south
LOG_LEVEL=INFO
"@

$envFile = ".\.env.template"
$envContent | Out-File -FilePath $envFile -Encoding UTF8
Write-Host "   OK Creado $envFile" -ForegroundColor Green

# PASO 3: VERIFICAR DATASET
Write-Host "`nPASO 3: Verificando dataset procesado..." -ForegroundColor Green

$datasetPath = ".\dataset_processed_watsonx.jsonl"
if (Test-Path $datasetPath) {
    $lineCount = (Get-Content $datasetPath | Measure-Object -Line).Lines
    Write-Host "   OK Dataset encontrado: $lineCount documentos" -ForegroundColor Green
} else {
    Write-Host "   AVISO Dataset no encontrado. Ejecutando Feature Engineering..." -ForegroundColor Yellow
    try {
        & $pythonExe test_feature_engineering.py
        Write-Host "   OK Dataset procesado generado" -ForegroundColor Green
    }
    catch {
        Write-Host "   ERROR generando dataset" -ForegroundColor Red
    }
}

# PASO 4: CREAR SCRIPTS AUXILIARES
Write-Host "`nPASO 4: Creando scripts auxiliares..." -ForegroundColor Green

# Script de prueba Watson
$testWatsonContent = @"
import os
import sys
from pathlib import Path

def test_imports():
    try:
        from dotenv import load_dotenv
        from ibm_watson_machine_learning import APIClient
        from ibm_watson import DiscoveryV2
        print("OK Librerias IBM Watson importadas correctamente")
        return True
    except ImportError as e:
        print(f"ERROR importando librerias: {e}")
        return False

def test_credentials():
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ['WATSONX_API_KEY', 'DISCOVERY_API_KEY']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"ERROR Faltan variables de entorno: {missing}")
        return False
    
    print("OK Credenciales cargadas correctamente")
    return True

def test_dataset():
    dataset_path = Path('dataset_processed_watsonx.jsonl')
    if not dataset_path.exists():
        print("ERROR Dataset procesado no encontrado")
        return False
    
    import jsonlines
    with jsonlines.open(dataset_path) as reader:
        docs = list(reader)
    
    print(f"OK Dataset cargado: {len(docs)} documentos")
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
        print(f"\nProbando {name}...")
        if test_func():
            passed += 1
        else:
            print(f"ERROR Fallo: {name}")
    
    print(f"\nResumen: {passed}/{len(tests)} pruebas pasaron")
    
    if passed == len(tests):
        print("OK Sistema listo para IBM Watson!")
        print("Ejecuta: python setup_watson.py")
    else:
        print("AVISO Revisa la configuracion antes de continuar")

if __name__ == "__main__":
    main()
"@

$testWatsonContent | Out-File -FilePath ".\test_watson_setup.py" -Encoding UTF8
Write-Host "   OK Creado test_watson_setup.py" -ForegroundColor Green

# Script de configuración Watson
$setupWatsonContent = @"
import os
import sys
from pathlib import Path

def check_env_file():
    env_path = Path('.env')
    if not env_path.exists():
        print("ERROR Archivo .env no encontrado")
        print("Pasos para crear .env:")
        print("1. Renombra .env.template a .env")
        print("2. Completa tus credenciales IBM Watson")
        return False
    
    content = env_path.read_text()
    required_vars = ['WATSONX_API_KEY', 'DISCOVERY_API_KEY']
    
    for var in required_vars:
        if f"{var}=tu_" in content:
            print(f"AVISO Variable {var} no configurada en .env")
            return False
    
    print("OK Archivo .env configurado correctamente")
    return True

def main():
    print("Configuracion inicial IBM Watson para DECODE-EV")
    print("=" * 50)
    
    if not check_env_file():
        sys.exit(1)
    
    try:
        print("\nEjecutando configuracion Watson...")
        os.system("python 01_watsonx_setup_REAL.py")
        
        print("\nProbando sistema RAG...")
        os.system("python 03_watson_rag_system_REAL.py")
        
        print("\nOK Configuracion completada!")
        print("Siguiente paso: ejecutar dashboard con 'streamlit run streamlit_dashboard_watson.py'")
        
    except Exception as e:
        print(f"ERROR en configuracion: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
"@

$setupWatsonContent | Out-File -FilePath ".\setup_watson.py" -Encoding UTF8
Write-Host "   OK Creado setup_watson.py" -ForegroundColor Green

# PASO 5: RESUMEN
Write-Host "`nPASO 5: Resumen de instalacion" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Cyan

Write-Host "`nINSTALACION COMPLETADA" -ForegroundColor Green
Write-Host "Dependencias Python instaladas" -ForegroundColor White
Write-Host "Template de configuracion creado" -ForegroundColor White
Write-Host "Scripts de inicializacion creados" -ForegroundColor White

Write-Host "`nPROXIMOS PASOS MANUALES:" -ForegroundColor Yellow
Write-Host "1. Ve a https://cloud.ibm.com/ y crea servicios Watson" -ForegroundColor White
Write-Host "2. Renombra .env.template a .env y completa credenciales" -ForegroundColor White
Write-Host "3. Ejecuta: python test_watson_setup.py" -ForegroundColor White
Write-Host "4. Ejecuta: python setup_watson.py" -ForegroundColor White

Write-Host "`nARCHIVOS CREADOS:" -ForegroundColor Cyan
Write-Host ".env.template - Template de credenciales" -ForegroundColor White
Write-Host "setup_watson.py - Configuracion inicial" -ForegroundColor White  
Write-Host "test_watson_setup.py - Pruebas del sistema" -ForegroundColor White

Write-Host "`nEl sistema DECODE-EV esta listo para Watson!" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Cyan

# Verificacion final
Write-Host "`nVERIFICACION FINAL:" -ForegroundColor Yellow
$files = @("01_watsonx_setup_REAL.py", "03_watson_rag_system_REAL.py", ".env.template", "setup_watson.py", "test_watson_setup.py")
foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "   OK $file" -ForegroundColor Green
    } else {
        Write-Host "   ERROR $file faltante" -ForegroundColor Red
    }
}