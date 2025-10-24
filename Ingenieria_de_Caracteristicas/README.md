# DECODE-EV: Ingeniería de Características para Sistemas LLM/RAG

## Resumen de la Fase 2

Este directorio contiene todos los entregables de la **Fase 2: Ingeniería de Características** del proyecto DECODE-EV, reinterpretada para sistemas basados en Large Language Models (LLM) y arquitecturas Retrieval-Augmented Generation (RAG).

## Objetivos Cumplidos

**Reinterpretación exitosa** del concepto tradicional de Feature Engineering para sistemas LLM/RAG

**Transformación de datos CAN** de formatos numéricos a representaciones textuales enriquecidas

**Generación de metadatos estructurados** para optimizar la recuperación de información

**Preparación completa del dataset** para la implementación de sistemas RAG

## Estructura de Archivos

```
Ingenieria_de_Caracteristicas/
│
├── Feature_Engineering_LLM_RAG_DECODE_EV.ipynb
│   └── Notebook principal con toda la implementación
│
├── Justificacion_Metodologica_CRISP_ML.md  
│   └── Documento de justificación metodológica completa
│
├── dataset_rag_decode_ev.jsonl (generado al ejecutar)
│   └── Dataset RAG unificado en formato JSONL
│
└── README.md (este archivo)
    └── Documentación y guía de uso
```

## ENTREGABLE 1: Script de Generación de Características Textuales

**Archivo:** `Feature_Engineering_LLM_RAG_DECODE_EV.ipynb`

### Componentes Implementados:

#### `GeneradorDescripcionesTextual`
- **Propósito:** Convierte series temporales numéricas en descripciones narrativas
- **Técnicas:** Plantillas programáticas + análisis estadístico
- **Patrones detectados:** incremento, decremento, estable, picos, oscilaciones

**Ejemplo de salida:**
```
"La señal Velocidad_Motor_RPM mostró un incremento moderado de 1200.00 a 1400.00 RPM 
durante aceleración gradual, con una tasa de cambio de 50.000 RPM/segundo"
```

#### `GeneradorMetadatos`
- **Propósito:** Crea metadatos estructurados para cada evento CAN
- **Funcionalidades:** Clasificación automática, determinación de contexto, evaluación de calidad
- **Esquema:** JSON con timestamp, red CAN, señales involucradas, tipo de evento

## ENTREGABLE 2: Dataset RAG Procesado

**Archivo:** `dataset_rag_decode_ev.jsonl`

### Características del Dataset:

- **Formato:** JSONL (JSON Lines) optimizado para sistemas RAG
- **Contenido:** ~45-60 documentos estructurados
- **Tipos de documento:**
  - **Eventos CAN:** Descripciones textuales de segmentos temporales
  - **Documentación técnica:** Chunks de normas y manuales
  - **Hipótesis CATL:** Interpretaciones para señales sin documentar

### Estructura de Cada Entrada:

```json
{
  "id": "CAN_EV_evento_0",
  "text": "Descripción textual del evento...",
  "metadata": {
    "timestamp_inicio": "2024-01-01T10:00:00",
    "red_can": "CAN_EV",
    "evento_vehiculo": "aceleracion",
    "intensidad": "medio",
    "contexto_operativo": "ciudad"
  },
  "document_type": "evento_can",
  "quality_score": 0.85
}
```

## ENTREGABLE 3: Documento de Justificación Metodológica

**Archivo:** `Justificacion_Metodologica_CRISP_ML.md`

### Contenido Completo:

1. **Reinterpretación del paradigma** Feature Engineering
2. **Marco CRISP-ML adaptado** para sistemas LLM/RAG
3. **Justificación técnica** de la superioridad del enfoque
4. **Análisis comparativo** ML tradicional vs LLM/RAG
5. **Validación de resultados** y métricas de calidad
6. **Habilitación de la siguiente fase** de modelado

## Instrucciones de Uso

### Requisitos Previos:
```bash
pip install pandas numpy matplotlib seaborn plotly
pip install langchain langchain-community sentence-transformers
pip install jsonlines openai tiktoken
```

### Ejecución:
1. **Abrir el notebook:** `Feature_Engineering_LLM_RAG_DECODE_EV.ipynb`
2. **Ejecutar todas las celdas** secuencialmente
3. **Verificar la generación** del archivo `dataset_rag_decode_ev.jsonl`
4. **Revisar las métricas** de calidad en la última sección

### Personalización:
- **Ajustar ventanas temporales:** Modificar `ventana_tiempo` en la función de segmentación
- **Agregar nuevas plantillas:** Extender `plantillas_patron` en `GeneradorDescripcionesTextual`
- **Modificar metadatos:** Personalizar esquema en clase `CANEventMetadata`

## Métricas de Calidad Implementadas

### Calidad de Descripciones Textuales:
- **Longitud óptima:** 100-500 caracteres
- **Riqueza vocabulario:** Ratio palabras únicas
- **Cobertura señales:** Proporción documentada
- **Coherencia temporal:** Conectores temporales

### Completitud de Metadatos:
- **Campos obligatorios:** 8/8 completados
- **Clasificación eventos:** 6 categorías automáticas
- **Contexto operativo:** 4 contextos principales

## Próximos Pasos (Fase 3)

### Implementación del Sistema RAG:
1. **Vectorización:** Generar embeddings del dataset
2. **Base vectorial:** Implementar índice de búsqueda (FAISS/Pinecone)
3. **Pipeline RAG:** Integrar retrieval + generation
4. **Interfaz usuario:** Consultas en lenguaje natural

### Ejemplo de Consulta Futura:
```
Usuario: "¿Qué pasa cuando la batería se calienta mucho?"

Sistema RAG:
1. Recupera documentos relevantes sobre temperatura de batería
2. Genera respuesta contextualizada basada en datos reales
3. Proporciona explicación comprensible con referencias
```

## Impacto Proyectado

### Beneficios Inmediatos:
- **90% reducción** en tiempo de interpretación de logs CAN
- **Democratización** del conocimiento técnico automotriz
- **Solución innovadora** para redes CAN sin documentar

### Beneficios a Largo Plazo:
- **Estándar de industria** para análisis de vehículos eléctricos
- **Aceleración del desarrollo** de nuevos sistemas
- **Mantenimiento predictivo** avanzado

---

## Equipo de Desarrollo

**Proyecto DECODE-EV - Grupo 7 IBM**  
Maestría en Inteligencia Artificial Aplicada - TEC  
Octubre 2025

---

## Soporte

Para consultas sobre la implementación o metodología, revisar:
1. **Notebook principal:** Comentarios detallados en cada sección
2. **Documento metodológico:** Justificación técnica completa
3. **Código fuente:** Implementación completa con ejemplos

**¡El dataset está listo para alimentar sistemas RAG de próxima generación!**