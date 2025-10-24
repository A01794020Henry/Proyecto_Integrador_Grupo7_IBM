# 🚀 Guía de Inicio Rápido - RAG IBM watsonx (15 minutos)

## ⚡ Setup Express para DECODE-EV

**¿Tienes prisa?** Esta guía te permite configurar el sistema RAG en 15 minutos si ya tienes todas las credenciales.

---

## 📋 Checklist Previo (2 minutos)

### ✅ Verificación Rápida
```powershell
# Ejecutar este bloque completo para verificar todo
python --version  # Debe ser 3.9+
git --version
pip --version
ping ibm.com -n 2
```

### ✅ Credenciales Requeridas
- [ ] **WATSONX_API_KEY**: Tu API key de IBM Cloud
- [ ] **WATSONX_PROJECT_ID**: Project ID de watsonx.ai
- [ ] **DISCOVERY_API_KEY**: API key de Watson Discovery
- [ ] **DISCOVERY_ENVIRONMENT_ID**: Environment ID de Discovery
- [ ] **DISCOVERY_COLLECTION_ID**: Collection ID de Discovery

---

## 🏃‍♂️ Configuración Express (8 minutos)

### Paso 1: Clonar y Navegar (30 segundos)
```powershell
cd "c:\Users\henry\Documents\GitHub\Proyecto_Integrador_Grupo7_IBM\IBM_RAG_Implementation"
```

### Paso 2: Entorno Virtual (1 minuto)
```powershell
python -m venv venv_rag_express
.\venv_rag_express\Scripts\activate
python -m pip install --upgrade pip
```

### Paso 3: Instalar Dependencias (3 minutos)
```powershell
pip install -r requirements.txt
```

### Paso 4: Configurar Credenciales (2 minutos)
```powershell
# Crear archivo .env
@"
WATSONX_API_KEY=TU_API_KEY_AQUI
WATSONX_PROJECT_ID=TU_PROJECT_ID_AQUI
WATSONX_URL=https://us-south.ml.cloud.ibm.com
DISCOVERY_API_KEY=TU_DISCOVERY_API_KEY_AQUI
DISCOVERY_ENVIRONMENT_ID=TU_ENVIRONMENT_ID_AQUI
DISCOVERY_COLLECTION_ID=TU_COLLECTION_ID_AQUI
DISCOVERY_URL=https://api.us-south.discovery.watson.cloud.ibm.com
EMBEDDING_MODEL=ibm/slate-125m-english-rtrvr
LLM_MODEL=ibm/granite-13b-chat-v2
ENVIRONMENT=development
LOG_LEVEL=INFO
MAX_TOKENS=2048
TEMPERATURE=0.3
"@ | Out-File -FilePath ".env" -Encoding UTF8
```

**⚠️ IMPORTANTE:** Editar `.env` con tus credenciales reales.

### Paso 5: Inicialización Rápida (1.5 minutos)
```powershell
# Configurar watsonx
python 01_watsonx_setup.py

# Integrar dataset (si existe)
python 02_dataset_integration.py --dataset-path "..\Ingenieria_de_Caracteristicas\dataset_rag_decode_ev.jsonl"
```

---

## 🎯 Prueba Rápida (3 minutos)

### Opción A: Dashboard Web (Recomendado)
```powershell
streamlit run 04_streamlit_dashboard.py
```
**→ Abrir:** http://localhost:8501

### Opción B: Test Directo
```powershell
python 05_testing_suite.py
```

### Opción C: Script Automatizado
```powershell
# Usar el script de automatización incluido
PowerShell -ExecutionPolicy Bypass -File "..\setup_rag_automation.ps1"
# Seleccionar opción 10 (Configuración automática completa)
```

---

## 🔧 Troubleshooting Rápido (2 minutos)

### ❌ Error: "Authentication failed"
```powershell
# Verificar credenciales
notepad .env
# Asegurar que no hay espacios extra en las API keys
```

### ❌ Error: "Module not found"
```powershell
# Reinstalar dependencias
pip install --upgrade -r requirements.txt
```

### ❌ Error: "Dataset not found"
```powershell
# Verificar dataset
dir "..\Ingenieria_de_Caracteristicas\dataset_rag_decode_ev.jsonl"
# Si no existe, ejecutar el notebook de Feature Engineering primero
```

### ❌ Dashboard no carga
```powershell
# Verificar puerto
netstat -an | findstr :8501
# Si está ocupado, usar puerto diferente:
streamlit run 04_streamlit_dashboard.py --server.port 8502
```

---

## ✅ Verificación de Éxito (1 minuto)

### Indicadores de Configuración Exitosa:

1. **Dashboard carga sin errores** ✅
2. **Consulta de prueba funciona** ✅
   ```
   Prueba: "¿Qué eventos se detectaron en los datos?"
   ```
3. **Métricas visibles** ✅
   - Tiempo respuesta < 3s
   - Confianza > 0.8
4. **Sin errores en consola** ✅

---

## 🎉 ¡Éxito! ¿Qué hacer ahora?

### 📝 Consultas de Ejemplo para Probar:
```
"Explica los eventos CAN detectados"
"¿Cuáles son los patrones de conducción más comunes?"
"Muestra un resumen de la eficiencia energética"
"¿Qué sensores reportan anomalías?"
```

### 🔄 Próximos Pasos:
1. **Personalizar consultas** para tu caso específico
2. **Integrar datos reales** de tus vehículos
3. **Configurar alertas** automáticas
4. **Escalar para múltiples buses**

---

## 📞 Soporte Rápido

### Si algo no funciona:
1. **Revisar el manual completo:** `Manual_Configuracion_RAG_IBM_watsonx.md`
2. **Ejecutar diagnóstico:** Script de automatización → Opción 11
3. **Verificar logs:** Buscar archivos `.log` en el directorio

### Comandos de Diagnóstico Rápido:
```powershell
# Estado del sistema
python -c "
import sys, os
from dotenv import load_dotenv
load_dotenv()
print('Python:', sys.version[:6])
print('API Key configurada:', bool(os.getenv('WATSONX_API_KEY')))
print('Project ID configurado:', bool(os.getenv('WATSONX_PROJECT_ID')))
"

# Test de conectividad
python -c "
from ibm_watson_machine_learning import APIClient
import os
from dotenv import load_dotenv
load_dotenv()
try:
    client = APIClient({'url': os.getenv('WATSONX_URL'), 'apikey': os.getenv('WATSONX_API_KEY')})
    print('✅ Conexión a watsonx: OK')
except Exception as e:
    print('❌ Conexión a watsonx: Error')
"
```

---

**⏱️ Tiempo Total:** ~15 minutos  
**✅ Resultado:** Sistema RAG funcional con IBM watsonx  
**🎯 Objetivo:** Consultas conversacionales sobre datos CAN vehiculares