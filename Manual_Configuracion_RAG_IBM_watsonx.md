# Manual Completo de Configuración RAG con IBM watsonx
## Guía Paso a Paso para DECODE-EV

**Proyecto:** DECODE-EV - Sistema RAG para Análisis de Buses CAN  
**Fecha:** 12 de octubre de 2025  
**Versión:** 1.0  
**Autor:** Proyecto Integrador Grupo 7 IBM  

---

## 📋 Tabla de Contenidos

1. [Prerrequisitos y Preparación](#1-prerrequisitos-y-preparación)
2. [Configuración de IBM Cloud](#2-configuración-de-ibm-cloud)
3. [Configuración de IBM watsonx.ai](#3-configuración-de-ibm-watsonxai)
4. [Configuración de Watson Discovery](#4-configuración-de-watson-discovery)
5. [Configuración del Entorno Local](#5-configuración-del-entorno-local)
6. [Instalación y Configuración del Proyecto](#6-instalación-y-configuración-del-proyecto)
7. [Configuración de Credenciales](#7-configuración-de-credenciales)
8. [Inicialización del Sistema RAG](#8-inicialización-del-sistema-rag)
9. [Validación y Pruebas](#9-validación-y-pruebas)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Prerrequisitos y Preparación

### 1.1 Verificación de Sistemas Base

Antes de comenzar, verifica que tienes los siguientes componentes instalados:

```powershell
# Verificar versión de Python (mínimo 3.9)
python --version

# Verificar Git
git --version

# Verificar pip
pip --version

# Verificar conectividad a internet
ping ibm.com -n 4
```

**Salida esperada:**
```
Python 3.9.x o superior
git version 2.x.x
pip 23.x.x
Respuesta exitosa de ping a ibm.com
```

### 1.2 Cuentas y Licencias Requeridas

Asegúrate de tener acceso a:

- ✅ **IBM Cloud Account** con permisos de administrador
- ✅ **IBM watsonx License** (Plan Lite o superior)
- ✅ **Watson Discovery License** 
- ✅ **Credenciales API** de IBM Cloud
- ✅ **Project ID** de watsonx (se creará en el proceso)

### 1.3 Información de Red y Firewall

Verifica que los siguientes dominios están accesibles:

```powershell
# Verificar acceso a servicios IBM
nslookup us-south.ml.cloud.ibm.com
nslookup api.us-south.discovery.watson.cloud.ibm.com
nslookup cloud.ibm.com
```

---

## 2. Configuración de IBM Cloud

### 2.1 Acceso a IBM Cloud Console

1. **Navegar a IBM Cloud:**
   ```
   Abrir navegador web
   Ir a: https://cloud.ibm.com
   ```

2. **Iniciar Sesión:**
   - Usar credenciales IBM Cloud
   - Seleccionar la cuenta correcta si tienes múltiples cuentas
   - Verificar que estás en la región `us-south` (Dallas)

3. **Verificar Servicios Disponibles:**
   ```
   Dashboard → Catalog
   Buscar: "watsonx"
   Buscar: "watson discovery"
   ```

### 2.2 Configuración de API Keys

1. **Crear API Key Principal:**
   ```
   IBM Cloud Console → Manage → Access (IAM)
   → API keys → Create an IBM Cloud API key
   ```

2. **Configurar Permisos:**
   - **Name:** `DECODE-EV-RAG-Main-Key`
   - **Description:** `API Key para sistema RAG DECODE-EV`
   - **Access groups:** Asignar grupos con permisos para:
     - Watson Machine Learning
     - Watson Discovery
     - Cloud Object Storage

3. **Guardar Credenciales de Forma Segura:**
   ```
   ⚠️ IMPORTANTE: Copiar y guardar la API key inmediatamente
   No será posible verla nuevamente después de cerrar la ventana
   ```

### 2.3 Configuración de Resource Groups

1. **Crear Resource Group para el Proyecto:**
   ```
   IBM Cloud Console → Manage → Account → Resource groups
   → Create resource group
   ```

2. **Configuración del Resource Group:**
   - **Name:** `DECODE-EV-RAG-Resources`
   - **Description:** `Recursos para sistema RAG de análisis vehicular`
   - **Tags:** `decode-ev`, `rag`, `vehicular`, `grupo7`

---

## 3. Configuración de IBM watsonx.ai

### 3.1 Creación del Servicio watsonx.ai

1. **Acceder al Catálogo:**
   ```
   IBM Cloud Console → Catalog
   → AI / Machine Learning → watsonx.ai
   ```

2. **Configurar el Servicio:**
   ```
   Service name: watsonx-decode-ev-rag
   Resource group: DECODE-EV-RAG-Resources
   Location: Dallas (us-south)
   Plan: Lite (o el plan que tengas licenciado)
   ```

3. **Crear el Servicio:**
   ```
   Click "Create"
   Esperar confirmación de creación (1-2 minutos)
   ```

### 3.2 Configuración del Proyecto watsonx

1. **Acceder a watsonx.ai:**
   ```
   Desde IBM Cloud Console → Resource list
   → AI / Machine Learning → watsonx-decode-ev-rag
   → Launch watsonx.ai
   ```

2. **Crear Proyecto:**
   ```
   watsonx.ai Console → Projects → New project
   → Create an empty project
   ```

3. **Configuración del Proyecto:**
   ```
   Name: DECODE-EV-RAG-System
   Description: Sistema RAG para análisis conversacional de datos CAN vehiculares
   Storage: Create new Cloud Object Storage instance
   ```

4. **Obtener Project ID:**
   ```
   Una vez creado el proyecto:
   Project Settings → General → Project ID
   
   📋 COPIAR Y GUARDAR: Project ID (formato: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
   ```

### 3.3 Configuración de Modelos

1. **Verificar Modelos Disponibles:**
   ```
   watsonx.ai → Foundation models → View all models
   ```

2. **Modelos Requeridos para DECODE-EV:**
   ```
   ✅ ibm/granite-13b-chat-v2 (Generación de texto)
   ✅ ibm/slate-125m-english-rtrvr (Embeddings y retrieval)
   ```

3. **Probar Acceso a Modelos:**
   ```
   Foundation models → ibm/granite-13b-chat-v2 → Try now
   Prompt de prueba: "Explica qué es un sistema CAN vehicular"
   ```

---

## 4. Configuración de Watson Discovery

### 4.1 Creación del Servicio Discovery

1. **Acceder al Catálogo:**
   ```
   IBM Cloud Console → Catalog
   → AI / Machine Learning → Watson Discovery
   ```

2. **Configurar el Servicio:**
   ```
   Service name: watson-discovery-decode-ev
   Resource group: DECODE-EV-RAG-Resources
   Location: Dallas (us-south)
   Plan: Lite (o el plan licenciado)
   ```

3. **Crear y Acceder:**
   ```
   Click "Create"
   → Launch Watson Discovery
   ```

### 4.2 Configuración de Collection

1. **Crear Project en Discovery:**
   ```
   Watson Discovery Console → New project
   Project type: Document Retrieval
   Project name: DECODE-EV-RAG-Documents
   ```

2. **Configurar Collection:**
   ```
   Create collection → Upload documents
   Collection name: decode-ev-can-data
   Language: English
   ```

3. **Obtener Credenciales Discovery:**
   ```
   IBM Cloud Console → Resource list → watson-discovery-decode-ev
   → Service credentials → New credential
   
   Name: DECODE-EV-Discovery-Creds
   Role: Manager
   
   📋 COPIAR Y GUARDAR:
   - API Key
   - URL
   - Environment ID
   - Collection ID
   ```

---

## 5. Configuración del Entorno Local

### 5.1 Preparación del Directorio de Trabajo

```powershell
# Navegar al directorio del proyecto
cd "c:\Users\henry\Documents\GitHub\Proyecto_Integrador_Grupo7_IBM"

# Verificar estructura del proyecto
dir

# Navegar a la implementación RAG
cd IBM_RAG_Implementation

# Listar archivos
dir
```

### 5.2 Creación del Entorno Virtual

```powershell
# Crear entorno virtual Python
python -m venv venv_rag_watsonx

# Activar entorno virtual
.\venv_rag_watsonx\Scripts\activate

# Verificar activación (debería mostrar (venv_rag_watsonx) en el prompt)
python -c "import sys; print('Entorno virtual activo:', sys.prefix)"

# Actualizar pip
python -m pip install --upgrade pip
```

### 5.3 Instalación de Dependencias

```powershell
# Instalar dependencias desde requirements.txt
pip install -r requirements.txt

# Verificar instalación de paquetes clave
pip show ibm-watson-machine-learning
pip show ibm-watson
pip show langchain
pip show streamlit
```

**Verificación de Instalación Exitosa:**
```powershell
# Probar importaciones clave
python -c "
import ibm_watson_machine_learning as wml
import ibm_watson
import langchain
import streamlit
print('✅ Todas las dependencias instaladas correctamente')
"
```

---

## 6. Instalación y Configuración del Proyecto

### 6.1 Verificación de Archivos del Proyecto

```powershell
# Verificar que todos los archivos están presentes
dir *.py

# Salida esperada:
# 01_watsonx_setup.py
# 02_dataset_integration.py
# 03_core_rag_system.py
# 04_streamlit_dashboard.py
# 05_testing_suite.py
# 06_deployment_script.py
```

### 6.2 Verificación del Dataset

```powershell
# Verificar dataset en directorio de ingeniería de características
dir "..\Ingenieria_de_Caracteristicas\dataset_rag_decode_ev.jsonl"

# Si el archivo no existe, verificar notebook
dir "..\Ingenieria_de_Caracteristicas\Feature_Engineering_LLM_RAG_DECODE_EV.ipynb"
```

---

## 7. Configuración de Credenciales

### 7.1 Creación del Archivo de Configuración

```powershell
# Crear archivo .env en el directorio IBM_RAG_Implementation
New-Item -Name ".env" -ItemType File

# Abrir archivo para edición
notepad .env
```

### 7.2 Configuración del Archivo .env

**Copiar y pegar la siguiente plantilla en el archivo `.env`:**

```env
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
```

### 7.3 Sustitución de Credenciales Reales

**Reemplazar los siguientes valores con tus credenciales reales:**

1. **WATSONX_API_KEY**: API Key de IBM Cloud
2. **WATSONX_PROJECT_ID**: Project ID del proyecto watsonx.ai
3. **DISCOVERY_API_KEY**: API Key del servicio Watson Discovery
4. **DISCOVERY_ENVIRONMENT_ID**: Environment ID de Watson Discovery
5. **DISCOVERY_COLLECTION_ID**: Collection ID de Watson Discovery

### 7.4 Verificación de Credenciales

```powershell
# Verificar que el archivo .env se creó correctamente
type .env

# Verificar que no hay espacios en blanco extra
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('✅ Arquivo .env carregado')
print('WATSONX_API_KEY configurado:', bool(os.getenv('WATSONX_API_KEY')))
print('WATSONX_PROJECT_ID configurado:', bool(os.getenv('WATSONX_PROJECT_ID')))
"
```

---

## 8. Inicialización del Sistema RAG

### 8.1 Configuración Inicial de watsonx

```powershell
# Ejecutar script de configuración inicial
python 01_watsonx_setup.py
```

**Salida esperada:**
```
🔧 Iniciando configuración de IBM watsonx para DECODE-EV...
✅ watsonx.ai client inicializado correctamente
✅ Watson Discovery client inicializado correctamente
✅ Modelos disponibles verificados
✅ Proyecto DECODE-EV-RAG configurado exitosamente
📋 Project ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

### 8.2 Integración del Dataset

```powershell
# Integrar dataset DECODE-EV en el sistema
python 02_dataset_integration.py --dataset-path "..\Ingenieria_de_Caracteristicas\dataset_rag_decode_ev.jsonl"
```

**Salida esperada:**
```
📊 Iniciando integración del dataset DECODE-EV...
✅ Dataset cargado: 7 documentos
✅ Embeddings generados con ibm/slate-125m-english-rtrvr
✅ Vector store configurado
✅ Watson Discovery collection indexada
📈 Calidad del dataset: 0.751
✅ Integración completada exitosamente
```

### 8.3 Verificación del Sistema Core

```powershell
# Probar el sistema RAG core
python 03_core_rag_system.py
```

**Salida esperada:**
```
🚀 Iniciando sistema RAG DECODE-EV...
✅ Conexión con watsonx.ai establecida
✅ Vector store inicializado
✅ Pipeline RAG configurado
🔍 Ejecutando consulta de prueba...

Consulta: "¿Qué eventos se detectaron en los datos de los buses?"
Respuesta: Los datos analizados muestran múltiples eventos vehiculares incluyendo...
📊 Tiempo de respuesta: 1.23s
📈 Confianza: 0.92
✅ Sistema RAG funcionando correctamente
```

---

## 9. Validación y Pruebas

### 9.1 Ejecución de Suite de Pruebas

```powershell
# Ejecutar todas las pruebas del sistema
python 05_testing_suite.py
```

**Salida esperada:**
```
🧪 Iniciando suite de pruebas DECODE-EV RAG...

Test 1: Conexión IBM watsonx ✅
Test 2: Carga de dataset ✅
Test 3: Generación de embeddings ✅
Test 4: Búsqueda semántica ✅
Test 5: Generación de respuestas ✅
Test 6: Métricas de rendimiento ✅

📊 Resumen de Pruebas:
- Pruebas ejecutadas: 6
- Pruebas exitosas: 6
- Tiempo promedio de respuesta: 1.47s
- Confianza promedio: 0.91

✅ Todas las pruebas pasaron exitosamente
```

### 9.2 Verificación de Componentes Individuales

```powershell
# Probar conexión a watsonx.ai
python -c "
from ibm_watson_machine_learning import APIClient
import os
from dotenv import load_dotenv
load_dotenv()

credentials = {
    'url': os.getenv('WATSONX_URL'),
    'apikey': os.getenv('WATSONX_API_KEY'),
    'project_id': os.getenv('WATSONX_PROJECT_ID')
}

client = APIClient(credentials)
client.set.default_project(credentials['project_id'])
print('✅ Conexión a watsonx.ai verificada')
"

# Probar Watson Discovery
python -c "
from ibm_watson import DiscoveryV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import os
from dotenv import load_dotenv
load_dotenv()

authenticator = IAMAuthenticator(os.getenv('DISCOVERY_API_KEY'))
discovery = DiscoveryV2(version='2023-03-31', authenticator=authenticator)
discovery.set_service_url(os.getenv('DISCOVERY_URL'))
print('✅ Conexión a Watson Discovery verificada')
"
```

---

## 10. Lanzamiento del Dashboard

### 10.1 Iniciar Dashboard Streamlit

```powershell
# Iniciar el dashboard interactivo
streamlit run 04_streamlit_dashboard.py
```

**Salida esperada:**
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.xxx:8501
```

### 10.2 Verificación del Dashboard

1. **Abrir navegador web y navegar a:** `http://localhost:8501`

2. **Verificar elementos del dashboard:**
   - ✅ Página principal carga correctamente
   - ✅ Sección de consultas RAG activa
   - ✅ Métricas del sistema visibles
   - ✅ Historial de consultas funcional

3. **Realizar consulta de prueba:**
   ```
   Consulta: "Explica los eventos detectados en los datos CAN"
   Verificar que la respuesta se genera correctamente
   ```

---

## 10. Troubleshooting

### 10.1 Problemas Comunes de Conexión

#### Error: "Authentication failed"

```powershell
# Verificar credenciales
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('API Key configurada:', bool(os.getenv('WATSONX_API_KEY')))
print('Project ID configurado:', bool(os.getenv('WATSONX_PROJECT_ID')))
"

# Solución: Verificar que las credenciales son correctas y están sin espacios extra
```

#### Error: "Module not found"

```powershell
# Reinstalar dependencias
pip uninstall -r requirements.txt -y
pip install -r requirements.txt

# Verificar instalación
pip list | findstr "ibm"
```

### 10.2 Problemas de Dataset

#### Error: "Dataset not found"

```powershell
# Verificar ruta del dataset
dir "..\Ingenieria_de_Caracteristicas\dataset_rag_decode_ev.jsonl"

# Si no existe, ejecutar el notebook de ingeniería de características
jupyter notebook "..\Ingenieria_de_Caracteristicas\Feature_Engineering_LLM_RAG_DECODE_EV.ipynb"
```

### 10.3 Problemas de Performance

#### Respuestas lentas (>5 segundos)

```powershell
# Verificar configuración de modelos en .env
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('LLM Model:', os.getenv('LLM_MODEL'))
print('Temperature:', os.getenv('TEMPERATURE'))
print('Max Tokens:', os.getenv('MAX_TOKENS'))
"

# Ajustar configuración si es necesario
```

### 10.4 Comandos de Diagnóstico

```powershell
# Verificar estado completo del sistema
python -c "
print('🔍 DIAGNÓSTICO DEL SISTEMA DECODE-EV RAG')
print('=' * 50)

# Verificar Python
import sys
print(f'Python version: {sys.version}')

# Verificar dependencias clave
try:
    import ibm_watson_machine_learning
    print('✅ IBM Watson ML: Instalado')
except ImportError:
    print('❌ IBM Watson ML: No instalado')

try:
    import streamlit
    print('✅ Streamlit: Instalado')
except ImportError:
    print('❌ Streamlit: No instalado')

# Verificar variables de entorno
import os
from dotenv import load_dotenv
load_dotenv()

env_vars = ['WATSONX_API_KEY', 'WATSONX_PROJECT_ID', 'DISCOVERY_API_KEY']
for var in env_vars:
    status = '✅ Configurado' if os.getenv(var) else '❌ No configurado'
    print(f'{var}: {status}')
"
```

---

## 📚 Recursos Adicionales

### Documentación IBM

- **IBM watsonx.ai Documentation**: https://www.ibm.com/docs/en/watsonx-as-a-service
- **Watson Discovery Documentation**: https://cloud.ibm.com/docs/discovery
- **IBM Watson Machine Learning Python SDK**: https://ibm.github.io/watson-machine-learning-sdk/

### Soporte y Comunidad

- **IBM Developer Community**: https://developer.ibm.com/
- **Stack Overflow**: Usar tags `ibm-watsonx`, `watson-discovery`
- **GitHub Issues**: Reportar problemas específicos del proyecto

### Próximos Pasos

Una vez completada la configuración, puedes:

1. **Personalizar consultas** para tu caso de uso específico
2. **Integrar datos CAN reales** de tus vehículos
3. **Configurar alertas automáticas** basadas en patrones detectados
4. **Escalar el sistema** para múltiples vehículos
5. **Implementar en producción** usando los scripts de deployment

---

**🎉 ¡Felicitaciones! Has configurado exitosamente el sistema DECODE-EV RAG con IBM watsonx.**

Para soporte adicional, consulta la documentación técnica del proyecto o contacta al equipo de desarrollo.