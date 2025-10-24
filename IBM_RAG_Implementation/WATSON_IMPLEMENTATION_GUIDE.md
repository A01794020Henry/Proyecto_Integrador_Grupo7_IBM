# Guía de Configuración IBM Watson para DECODE-EV
# Paso a paso para implementación real

## 1. OBTENER CREDENCIALES IBM WATSON

### A. Crear cuenta IBM Cloud
1. Ve a https://cloud.ibm.com/
2. Crea una cuenta gratuita IBM Cloud
3. Verifica tu email

### B. Crear servicios Watson
1. **Watson Machine Learning (watsonx.ai)**:
   - En IBM Cloud Console → "Create resource"
   - Busca "Watson Machine Learning"
   - Selecciona plan gratuito (Lite)
   - Anota: API Key, Service URL, Project ID

2. **Watson Discovery**:
   - En IBM Cloud Console → "Create resource"
   - Busca "Watson Discovery"
   - Selecciona plan gratuito (Lite)
   - Anota: API Key, Service URL, Environment ID

### C. Configurar variables de entorno
Crea un archivo `.env` en el directorio IBM_RAG_Implementation:

```env
# IBM Watson Credentials
WATSONX_API_KEY=tu_watsonx_api_key_aqui
WATSONX_PROJECT_ID=tu_project_id_aqui
WATSONX_URL=https://us-south.ml.cloud.ibm.com

# Watson Discovery Credentials  
DISCOVERY_API_KEY=tu_discovery_api_key_aqui
DISCOVERY_URL=https://api.us-south.discovery.watson.cloud.ibm.com
DISCOVERY_VERSION=2023-03-31
DISCOVERY_ENVIRONMENT_ID=tu_environment_id_aqui
```

## 2. INSTALAR DEPENDENCIAS WATSON

Instala las librerías necesarias:

```bash
pip install ibm-watson-machine-learning
pip install ibm-watson
pip install ibm-cloud-sdk-core
pip install python-dotenv
```

## 3. ARCHIVOS A MODIFICAR

### A. 01_watsonx_setup.py - CONFIGURACIÓN REAL
- Descomentar imports de IBM Watson
- Cargar credenciales desde .env
- Implementar conexión real

### B. 02_dataset_integration.py - SUBIDA A WATSON DISCOVERY
- Crear colección en Watson Discovery
- Subir documentos procesados
- Configurar índices para búsqueda

### C. 03_core_rag_system.py - INTEGRACIÓN CON GRANITE
- Conectar con modelo IBM Granite
- Usar embeddings de IBM Slate
- Implementar RAG real con Watson

### D. 04_streamlit_dashboard.py - DASHBOARD CON WATSON REAL
- Interfaz conectada a servicios reales
- Métricas en tiempo real
- Visualizaciones de Watson Discovery

## 4. ESTRUCTURA DE DATOS WATSON

### Formato de documentos para Watson Discovery:
```json
{
  "document_id": "CAN_CUSTOM_31_evento_0",
  "title": "Evento CAN - Voltaje y Corriente",
  "text": "contenido procesado...",
  "metadata": {
    "red_can": "CAN_CUSTOM_31",
    "evento_vehiculo": "carga",
    "technical_density_score": 0.032,
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

## 5. CONFIGURACIÓN WATSONX.AI

### Modelos recomendados:
- **Embeddings**: ibm/slate-125m-english-rtrvr
- **Generación**: ibm/granite-13b-chat-v2  
- **Reranking**: ibm/slate-125m-english-rtrvr

### Parámetros optimizados:
```python
generation_params = {
    "temperature": 0.3,
    "max_new_tokens": 512,
    "top_p": 0.9,
    "top_k": 50
}
```

## 6. FLUJO DE IMPLEMENTACIÓN

1. **Configurar credenciales** → Paso 1
2. **Modificar código** → Pasos 2-3  
3. **Subir datos a Watson** → Paso 4
4. **Probar sistema RAG** → Paso 5
5. **Deploy dashboard** → Paso 6

¿Quieres que empecemos con algún paso específico?