# Scripts de Automatización para Configuración RAG IBM watsonx
# Archivo de utilidades para facilitar la configuración paso a paso

Write-Host "🚀 DECODE-EV RAG - Scripts de Configuración Automatizada" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green

# Función para verificar prerrequisitos
function Test-Prerequisites {
    Write-Host "🔍 Verificando prerrequisitos del sistema..." -ForegroundColor Yellow
    
    # Verificar Python
    try {
        $pythonVersion = python --version 2>&1
        if ($pythonVersion -match "Python (\d+)\.(\d+)") {
            $majorVersion = [int]$matches[1]
            $minorVersion = [int]$matches[2]
            if ($majorVersion -ge 3 -and $minorVersion -ge 9) {
                Write-Host "✅ Python $($matches[0]) - OK" -ForegroundColor Green
            } else {
                Write-Host "❌ Python version debe ser 3.9 o superior. Encontrado: $($matches[0])" -ForegroundColor Red
                return $false
            }
        }
    } catch {
        Write-Host "❌ Python no está instalado o no está en PATH" -ForegroundColor Red
        return $false
    }
    
    # Verificar Git
    try {
        $gitVersion = git --version 2>&1
        Write-Host "✅ $gitVersion - OK" -ForegroundColor Green
    } catch {
        Write-Host "❌ Git no está instalado o no está en PATH" -ForegroundColor Red
        return $false
    }
    
    # Verificar pip
    try {
        $pipVersion = pip --version 2>&1
        Write-Host "✅ $pipVersion - OK" -ForegroundColor Green
    } catch {
        Write-Host "❌ pip no está disponible" -ForegroundColor Red
        return $false
    }
    
    # Verificar conectividad
    try {
        Test-Connection -ComputerName "ibm.com" -Count 1 -Quiet | Out-Null
        Write-Host "✅ Conectividad a IBM Cloud - OK" -ForegroundColor Green
    } catch {
        Write-Host "❌ No hay conectividad a IBM Cloud" -ForegroundColor Red
        return $false
    }
    
    return $true
}

# Función para configurar entorno virtual
function New-VirtualEnvironment {
    param(
        [string]$EnvName = "venv_rag_watsonx"
    )
    
    Write-Host "🔧 Configurando entorno virtual: $EnvName" -ForegroundColor Yellow
    
    # Crear entorno virtual
    try {
        python -m venv $EnvName
        Write-Host "✅ Entorno virtual creado: $EnvName" -ForegroundColor Green
    } catch {
        Write-Host "❌ Error creando entorno virtual: $_" -ForegroundColor Red
        return $false
    }
    
    # Activar entorno virtual
    try {
        & ".\$EnvName\Scripts\Activate.ps1"
        Write-Host "✅ Entorno virtual activado" -ForegroundColor Green
    } catch {
        Write-Host "❌ Error activando entorno virtual: $_" -ForegroundColor Red
        return $false
    }
    
    # Actualizar pip
    try {
        python -m pip install --upgrade pip --quiet
        Write-Host "✅ pip actualizado" -ForegroundColor Green
    } catch {
        Write-Host "❌ Error actualizando pip: $_" -ForegroundColor Red
        return $false
    }
    
    return $true
}

# Función para instalar dependencias
function Install-ProjectDependencies {
    Write-Host "📦 Instalando dependencias del proyecto..." -ForegroundColor Yellow
    
    # Verificar requirements.txt
    if (-not (Test-Path "requirements.txt")) {
        Write-Host "❌ Archivo requirements.txt no encontrado" -ForegroundColor Red
        return $false
    }
    
    try {
        pip install -r requirements.txt --quiet
        Write-Host "✅ Dependencias instaladas exitosamente" -ForegroundColor Green
    } catch {
        Write-Host "❌ Error instalando dependencias: $_" -ForegroundColor Red
        return $false
    }
    
    # Verificar instalación de paquetes críticos
    $criticalPackages = @("ibm-watson-machine-learning", "ibm-watson", "langchain", "streamlit")
    
    foreach ($package in $criticalPackages) {
        try {
            pip show $package --quiet
            Write-Host "✅ $package - Instalado" -ForegroundColor Green
        } catch {
            Write-Host "❌ $package - No instalado correctamente" -ForegroundColor Red
            return $false
        }
    }
    
    return $true
}

# Función para crear archivo .env
function New-EnvironmentFile {
    Write-Host "⚙️ Creando archivo de configuración .env..." -ForegroundColor Yellow
    
    $envTemplate = @"
# ===========================================
# CONFIGURACIÓN IBM WATSONX PARA DECODE-EV
# ===========================================

# IBM watsonx.ai Configuration
WATSONX_API_KEY=tu_watsonx_api_key_aqui
WATSONX_PROJECT_ID=tu_project_id_aqui
WATSONX_URL=https://us-south.ml.cloud.ibm.com

# Watson Discovery Configuration
DISCOVERY_API_KEY=tu_discovery_api_key_aqui
DISCOVERY_ENVIRONMENT_ID=tu_environment_id_aqui
DISCOVERY_COLLECTION_ID=tu_collection_id_aqui
DISCOVERY_URL=https://api.us-south.discovery.watson.cloud.ibm.com

# Modelos IBM watsonx
EMBEDDING_MODEL=ibm/slate-125m-english-rtrvr
LLM_MODEL=ibm/granite-13b-chat-v2
RERANKER_MODEL=ibm/slate-125m-english-rtrvr

# Configuración del Sistema
ENVIRONMENT=development
LOG_LEVEL=INFO
MAX_TOKENS=2048
TEMPERATURE=0.3
TOP_K=5
TOP_P=0.9

# Configuración de Vector Store
VECTOR_STORE_TYPE=milvus
VECTOR_DIMENSION=768
SIMILARITY_THRESHOLD=0.7

# Configuración de Dashboard
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=localhost
ENABLE_WIDE_MODE=true

# Configuración de Logging
LOG_FILE=decode_ev_rag.log
LOG_ROTATION=daily
LOG_RETENTION_DAYS=30
"@

    try {
        $envTemplate | Out-File -FilePath ".env" -Encoding UTF8
        Write-Host "✅ Archivo .env creado exitosamente" -ForegroundColor Green
        Write-Host "⚠️  IMPORTANTE: Editar .env con tus credenciales reales" -ForegroundColor Yellow
        return $true
    } catch {
        Write-Host "❌ Error creando archivo .env: $_" -ForegroundColor Red
        return $false
    }
}

# Función para validar credenciales
function Test-Credentials {
    Write-Host "🔐 Validando credenciales..." -ForegroundColor Yellow
    
    try {
        python -c @"
import os
from dotenv import load_dotenv
load_dotenv()

# Verificar variables requeridas
required_vars = [
    'WATSONX_API_KEY',
    'WATSONX_PROJECT_ID',
    'DISCOVERY_API_KEY',
    'DISCOVERY_ENVIRONMENT_ID'
]

missing_vars = []
for var in required_vars:
    if not os.getenv(var) or os.getenv(var) == f'tu_{var.lower()}_aqui':
        missing_vars.append(var)

if missing_vars:
    print('❌ Credenciales faltantes:', ', '.join(missing_vars))
    exit(1)
else:
    print('✅ Todas las credenciales configuradas')
    exit(0)
"@
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Credenciales validadas correctamente" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ Hay credenciales faltantes o incorrectas" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "❌ Error validando credenciales: $_" -ForegroundColor Red
        return $false
    }
}

# Función para ejecutar configuración inicial
function Start-WatsonxSetup {
    Write-Host "🔧 Ejecutando configuración inicial de watsonx..." -ForegroundColor Yellow
    
    try {
        python 01_watsonx_setup.py
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Configuración de watsonx completada" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ Error en configuración de watsonx" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "❌ Error ejecutando setup de watsonx: $_" -ForegroundColor Red
        return $false
    }
}

# Función para integrar dataset
function Start-DatasetIntegration {
    Write-Host "📊 Integrando dataset DECODE-EV..." -ForegroundColor Yellow
    
    $datasetPath = "..\Ingenieria_de_Caracteristicas\dataset_rag_decode_ev.jsonl"
    
    if (-not (Test-Path $datasetPath)) {
        Write-Host "❌ Dataset no encontrado en: $datasetPath" -ForegroundColor Red
        Write-Host "ℹ️  Ejecutar primero el notebook de Feature Engineering" -ForegroundColor Blue
        return $false
    }
    
    try {
        python 02_dataset_integration.py --dataset-path $datasetPath
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Dataset integrado exitosamente" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ Error integrando dataset" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "❌ Error ejecutando integración de dataset: $_" -ForegroundColor Red
        return $false
    }
}

# Función para ejecutar pruebas
function Start-SystemTests {
    Write-Host "🧪 Ejecutando suite de pruebas..." -ForegroundColor Yellow
    
    try {
        python 05_testing_suite.py
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Todas las pruebas pasaron exitosamente" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ Algunas pruebas fallaron" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "❌ Error ejecutando pruebas: $_" -ForegroundColor Red
        return $false
    }
}

# Función para iniciar dashboard
function Start-Dashboard {
    Write-Host "🌐 Iniciando dashboard Streamlit..." -ForegroundColor Yellow
    
    try {
        Write-Host "📍 Dashboard estará disponible en: http://localhost:8501" -ForegroundColor Cyan
        Write-Host "⏹️  Presionar Ctrl+C para detener el dashboard" -ForegroundColor Yellow
        streamlit run 04_streamlit_dashboard.py
    } catch {
        Write-Host "❌ Error iniciando dashboard: $_" -ForegroundColor Red
        return $false
    }
}

# Función principal de configuración automática
function Start-AutomaticSetup {
    Write-Host "🤖 Iniciando configuración automática completa..." -ForegroundColor Magenta
    Write-Host "=================================================" -ForegroundColor Magenta
    
    # Paso 1: Verificar prerrequisitos
    if (-not (Test-Prerequisites)) {
        Write-Host "❌ Prerrequisitos no cumplidos. Abortando configuración." -ForegroundColor Red
        return
    }
    
    # Paso 2: Configurar entorno virtual
    if (-not (New-VirtualEnvironment)) {
        Write-Host "❌ Error configurando entorno virtual. Abortando." -ForegroundColor Red
        return
    }
    
    # Paso 3: Instalar dependencias
    if (-not (Install-ProjectDependencies)) {
        Write-Host "❌ Error instalando dependencias. Abortando." -ForegroundColor Red
        return
    }
    
    # Paso 4: Crear archivo .env
    if (-not (Test-Path ".env")) {
        New-EnvironmentFile
        Write-Host "⚠️  PAUSA: Edita el archivo .env con tus credenciales reales antes de continuar" -ForegroundColor Yellow
        Write-Host "📝 Presiona cualquier tecla cuando hayas completado la configuración de credenciales..." -ForegroundColor Yellow
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    }
    
    # Paso 5: Validar credenciales
    if (-not (Test-Credentials)) {
        Write-Host "❌ Credenciales no válidas. Por favor, revisa el archivo .env" -ForegroundColor Red
        return
    }
    
    # Paso 6: Configurar watsonx
    if (-not (Start-WatsonxSetup)) {
        Write-Host "❌ Error en configuración de watsonx" -ForegroundColor Red
        return
    }
    
    # Paso 7: Integrar dataset
    if (-not (Start-DatasetIntegration)) {
        Write-Host "⚠️  Dataset no integrado. Puedes hacerlo manualmente después." -ForegroundColor Yellow
    }
    
    # Paso 8: Ejecutar pruebas
    if (-not (Start-SystemTests)) {
        Write-Host "⚠️  Algunas pruebas fallaron. Revisar configuración." -ForegroundColor Yellow
    }
    
    Write-Host "🎉 Configuración automática completada!" -ForegroundColor Green
    Write-Host "📋 Próximos pasos:" -ForegroundColor Cyan
    Write-Host "   1. Ejecutar: Start-Dashboard para iniciar el dashboard" -ForegroundColor White
    Write-Host "   2. Navegar a: http://localhost:8501" -ForegroundColor White
    Write-Host "   3. Realizar consultas de prueba" -ForegroundColor White
}

# Función de diagnóstico del sistema
function Get-SystemDiagnosis {
    Write-Host "🔍 DIAGNÓSTICO DEL SISTEMA DECODE-EV RAG" -ForegroundColor Cyan
    Write-Host "=======================================" -ForegroundColor Cyan
    
    # Información del sistema
    Write-Host "💻 Sistema Operativo: $((Get-CimInstance Win32_OperatingSystem).Caption)" -ForegroundColor White
    Write-Host "🐍 Versión Python: $(python --version 2>&1)" -ForegroundColor White
    
    # Estado del entorno virtual
    if ($env:VIRTUAL_ENV) {
        Write-Host "🌐 Entorno Virtual: Activo ($env:VIRTUAL_ENV)" -ForegroundColor Green
    } else {
        Write-Host "🌐 Entorno Virtual: No activo" -ForegroundColor Yellow
    }
    
    # Verificar archivos del proyecto
    $projectFiles = @("01_watsonx_setup.py", "02_dataset_integration.py", "03_core_rag_system.py", "04_streamlit_dashboard.py", "05_testing_suite.py", "requirements.txt", ".env")
    
    Write-Host "📁 Archivos del Proyecto:" -ForegroundColor White
    foreach ($file in $projectFiles) {
        if (Test-Path $file) {
            Write-Host "   ✅ $file" -ForegroundColor Green
        } else {
            Write-Host "   ❌ $file" -ForegroundColor Red
        }
    }
    
    # Verificar dependencias críticas
    if ($env:VIRTUAL_ENV) {
        Write-Host "📦 Dependencias Críticas:" -ForegroundColor White
        $criticalPackages = @("ibm-watson-machine-learning", "ibm-watson", "langchain", "streamlit")
        
        foreach ($package in $criticalPackages) {
            try {
                pip show $package --quiet 2>$null
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "   ✅ $package" -ForegroundColor Green
                } else {
                    Write-Host "   ❌ $package" -ForegroundColor Red
                }
            } catch {
                Write-Host "   ❌ $package" -ForegroundColor Red
            }
        }
    }
    
    # Verificar configuración
    if (Test-Path ".env") {
        try {
            python -c @"
import os
from dotenv import load_dotenv
load_dotenv()

required_vars = ['WATSONX_API_KEY', 'WATSONX_PROJECT_ID', 'DISCOVERY_API_KEY']
print('⚙️  Configuración:')
for var in required_vars:
    value = os.getenv(var)
    if value and value != f'tu_{var.lower()}_aqui':
        print(f'   ✅ {var}')
    else:
        print(f'   ❌ {var}')
"@
        } catch {
            Write-Host "⚙️  Configuración: ❌ Error leyendo .env" -ForegroundColor Red
        }
    } else {
        Write-Host "⚙️  Configuración: ❌ Archivo .env no encontrado" -ForegroundColor Red
    }
}

# Menú principal interactivo
function Show-MainMenu {
    while ($true) {
        Clear-Host
        Write-Host "🚀 DECODE-EV RAG - IBM watsonx Configuration" -ForegroundColor Green
        Write-Host "============================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Selecciona una opción:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "1.  🔍 Verificar prerrequisitos" -ForegroundColor White
        Write-Host "2.  🔧 Configurar entorno virtual" -ForegroundColor White
        Write-Host "3.  📦 Instalar dependencias" -ForegroundColor White
        Write-Host "4.  ⚙️  Crear archivo .env" -ForegroundColor White
        Write-Host "5.  🔐 Validar credenciales" -ForegroundColor White
        Write-Host "6.  🛠️  Configurar watsonx" -ForegroundColor White
        Write-Host "7.  📊 Integrar dataset" -ForegroundColor White
        Write-Host "8.  🧪 Ejecutar pruebas" -ForegroundColor White
        Write-Host "9.  🌐 Iniciar dashboard" -ForegroundColor White
        Write-Host "10. 🤖 Configuración automática completa" -ForegroundColor Magenta
        Write-Host "11. 🔍 Diagnóstico del sistema" -ForegroundColor Cyan
        Write-Host "0.  ❌ Salir" -ForegroundColor Red
        Write-Host ""
        
        $choice = Read-Host "Ingresa tu opción (0-11)"
        
        switch ($choice) {
            "1" { Test-Prerequisites; Read-Host "Presiona Enter para continuar" }
            "2" { New-VirtualEnvironment; Read-Host "Presiona Enter para continuar" }
            "3" { Install-ProjectDependencies; Read-Host "Presiona Enter para continuar" }
            "4" { New-EnvironmentFile; Read-Host "Presiona Enter para continuar" }
            "5" { Test-Credentials; Read-Host "Presiona Enter para continuar" }
            "6" { Start-WatsonxSetup; Read-Host "Presiona Enter para continuar" }
            "7" { Start-DatasetIntegration; Read-Host "Presiona Enter para continuar" }
            "8" { Start-SystemTests; Read-Host "Presiona Enter para continuar" }
            "9" { Start-Dashboard }
            "10" { Start-AutomaticSetup; Read-Host "Presiona Enter para continuar" }
            "11" { Get-SystemDiagnosis; Read-Host "Presiona Enter para continuar" }
            "0" { Write-Host "👋 ¡Hasta luego!" -ForegroundColor Green; break }
            default { Write-Host "❌ Opción inválida. Intenta de nuevo." -ForegroundColor Red; Start-Sleep 2 }
        }
    }
}

# Ejecutar menú principal si el script se ejecuta directamente
if ($MyInvocation.InvocationName -ne '.') {
    Show-MainMenu
}