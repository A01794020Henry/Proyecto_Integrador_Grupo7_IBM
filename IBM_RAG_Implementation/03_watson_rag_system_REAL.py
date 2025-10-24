# IBM Watson RAG System REAL para DECODE-EV
# Sistema completo conectado a servicios IBM Watson reales

import os
import json
import time
import logging
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from ibm_watson_machine_learning import APIClient
from ibm_watson import DiscoveryV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from dataclasses import dataclass

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class WatsonRAGQuery:
    """Consulta para sistema RAG Watson"""
    question: str
    collection_id: str
    max_docs: int = 5
    temperature: float = 0.3
    max_tokens: int = 512

@dataclass 
class WatsonRAGResponse:
    """Respuesta del sistema RAG Watson"""
    answer: str
    source_documents: List[Dict]
    confidence_score: float
    processing_time: float
    watson_metadata: Dict

class DecodeEVWatsonRAG:
    """
    Sistema RAG REAL conectado a IBM Watson
    """
    
    def __init__(self):
        """Inicializa sistema RAG Watson"""
        self.logger = logging.getLogger(__name__)
        
        # Verificar credenciales
        required_vars = ["WATSONX_API_KEY", "WATSONX_PROJECT_ID", "DISCOVERY_API_KEY"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Faltan variables de entorno: {missing_vars}")
        
        # Configuración Watson
        self.watsonx_config = {
            "url": os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com"),
            "apikey": os.getenv("WATSONX_API_KEY"),
            "project_id": os.getenv("WATSONX_PROJECT_ID")
        }
        
        self.discovery_config = {
            "apikey": os.getenv("DISCOVERY_API_KEY"),
            "url": os.getenv("DISCOVERY_URL", "https://api.us-south.discovery.watson.cloud.ibm.com"),
            "version": os.getenv("DISCOVERY_VERSION", "2023-03-31")
        }
        
        # Configuración modelos
        self.models_config = {
            "embedding_model": "ibm/slate-125m-english-rtrvr",
            "generation_model": "ibm/granite-13b-chat-v2",
            "reranker_model": "ibm/slate-125m-english-rtrvr"
        }
        
        # Clientes Watson
        self.wml_client = None
        self.discovery_client = None
        
        # Plantillas de prompt especializadas
        self.prompt_templates = {
            "diagnostico_vehicular": """Como experto en sistemas CAN vehiculares, analiza la siguiente consulta usando los documentos proporcionados.

Consulta: {query}

Documentos relevantes:
{context}

Proporciona un diagnóstico técnico que incluya:
1. Análisis de las señales CAN involucradas
2. Interpretación de valores y patrones
3. Posibles causas de anomalías (si las hay)
4. Recomendaciones técnicas

Respuesta:""",

            "explicacion_tecnica": """Basándote en los datos CAN vehiculares proporcionados, explica de manera técnica pero comprensible:

Pregunta: {query}

Información disponible:
{context}

Tu explicación debe incluir:
- Descripción del comportamiento observado
- Significado técnico de las mediciones
- Contexto operativo del vehículo
- Implicaciones para el funcionamiento

Explicación:""",

            "analisis_tendencias": """Analiza las tendencias y patrones en los datos vehiculares:

Consulta: {query}

Datos históricos:
{context}

Proporciona un análisis que cubra:
- Patrones identificados en las señales
- Evolución temporal de parámetros
- Correlaciones entre subsistemas
- Predicciones y recomendaciones de mantenimiento

Análisis:"""
        }
    
    def initialize_watson_clients(self):
        """Inicializa clientes IBM Watson"""
        try:
            self.logger.info("🔄 Inicializando clientes IBM Watson...")
            
            # Cliente Watson Machine Learning
            self.wml_client = APIClient(self.watsonx_config)
            self.wml_client.set.default_project(self.watsonx_config["project_id"])
            
            # Verificar conexión WML
            project_details = self.wml_client.projects.get_details()
            self.logger.info(f"✅ WML conectado a: {project_details['entity']['name']}")
            
            # Cliente Watson Discovery
            authenticator = IAMAuthenticator(self.discovery_config["apikey"])
            self.discovery_client = DiscoveryV2(
                version=self.discovery_config["version"],
                authenticator=authenticator
            )
            self.discovery_client.set_service_url(self.discovery_config["url"])
            
            # Verificar conexión Discovery
            collections = self.discovery_client.list_collections(
                project_id=self.watsonx_config["project_id"]
            ).get_result()
            self.logger.info(f"✅ Discovery conectado. Colecciones: {len(collections['collections'])}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error inicializando Watson: {e}")
            return False
    
    def search_watson_discovery(self, query: str, collection_id: str, max_docs: int = 5) -> List[Dict]:
        """Busca documentos relevantes en Watson Discovery"""
        try:
            self.logger.info(f"🔍 Buscando en Discovery: '{query[:50]}...'")
            
            # Configurar búsqueda
            search_params = {
                'project_id': self.watsonx_config["project_id"],
                'collection_ids': [collection_id],
                'query': query,
                'count': max_docs,
                'return': ['document_id', 'title', 'text', 'metadata'],
                'highlight': True
            }
            
            # Ejecutar búsqueda
            response = self.discovery_client.query(**search_params).get_result()
            
            # Procesar resultados
            documents = []
            for result in response.get('results', []):
                doc = {
                    'document_id': result.get('document_id'),
                    'title': result.get('title', ''),
                    'text': result.get('text', ''),
                    'metadata': result.get('metadata', {}),
                    'confidence': result.get('result_metadata', {}).get('confidence', 0),
                    'highlights': result.get('highlight', {})
                }
                documents.append(doc)
            
            self.logger.info(f"✅ Encontrados {len(documents)} documentos relevantes")
            return documents
            
        except Exception as e:
            self.logger.error(f"❌ Error en búsqueda Discovery: {e}")
            return []
    
    def generate_with_granite(self, prompt: str, temperature: float = 0.3, max_tokens: int = 512) -> str:
        """Genera respuesta usando IBM Granite"""
        try:
            self.logger.info("🤖 Generando respuesta con IBM Granite...")
            
            generation_params = {
                "model_id": self.models_config["generation_model"],
                "input": prompt,
                "parameters": {
                    "temperature": temperature,
                    "max_new_tokens": max_tokens,
                    "top_p": 0.9,
                    "top_k": 50,
                    "repetition_penalty": 1.1
                }
            }
            
            response = self.wml_client.foundation_models.generate(**generation_params)
            generated_text = response['results'][0]['generated_text']
            
            self.logger.info("✅ Respuesta generada con Granite")
            return generated_text.strip()
            
        except Exception as e:
            self.logger.error(f"❌ Error generación Granite: {e}")
            return f"Error generando respuesta: {str(e)}"
    
    def calculate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Calcula embeddings usando IBM Slate"""
        try:
            self.logger.info(f"🧠 Calculando embeddings para {len(texts)} textos...")
            
            embedding_params = {
                "model_id": self.models_config["embedding_model"],
                "input": texts
            }
            
            response = self.wml_client.foundation_models.embed(**embedding_params)
            embeddings = [result['embedding'] for result in response['results']]
            
            self.logger.info(f"✅ Embeddings calculados (dim: {len(embeddings[0])})")
            return embeddings
            
        except Exception as e:
            self.logger.error(f"❌ Error cálculo embeddings: {e}")
            return []
    
    def select_prompt_template(self, query: str) -> str:
        """Selecciona plantilla de prompt apropiada"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['diagnostico', 'problema', 'error', 'falla', 'anomalia']):
            return "diagnostico_vehicular"
        elif any(word in query_lower for word in ['tendencia', 'patron', 'analisis', 'evolucion', 'historico']):
            return "analisis_tendencias"
        else:
            return "explicacion_tecnica"
    
    def build_context(self, documents: List[Dict]) -> str:
        """Construye contexto a partir de documentos recuperados"""
        context_parts = []
        
        for i, doc in enumerate(documents, 1):
            doc_info = f"[Documento {i}]"
            doc_info += f"\nTipo: {doc.get('metadata', {}).get('document_type', 'N/A')}"
            doc_info += f"\nRed CAN: {doc.get('metadata', {}).get('red_can', 'N/A')}"
            doc_info += f"\nContenido: {doc.get('text', '')[:400]}..."
            
            if doc.get('highlights'):
                highlights = doc['highlights'].get('text', [])
                if highlights:
                    doc_info += f"\nPasajes relevantes: {' | '.join(highlights[:2])}"
            
            context_parts.append(doc_info)
        
        return "\n\n".join(context_parts)
    
    def query_watson_rag(self, query: WatsonRAGQuery) -> WatsonRAGResponse:
        """Ejecuta consulta RAG completa con Watson"""
        start_time = time.time()
        
        try:
            self.logger.info(f"🚀 Procesando consulta RAG: {query.question[:50]}...")
            
            # 1. Buscar documentos relevantes en Discovery
            documents = self.search_watson_discovery(
                query.question, 
                query.collection_id, 
                query.max_docs
            )
            
            if not documents:
                return WatsonRAGResponse(
                    answer="No se encontraron documentos relevantes para tu consulta.",
                    source_documents=[],
                    confidence_score=0.0,
                    processing_time=time.time() - start_time,
                    watson_metadata={'error': 'no_documents_found'}
                )
            
            # 2. Construir contexto
            context = self.build_context(documents)
            
            # 3. Seleccionar plantilla de prompt
            template_key = self.select_prompt_template(query.question)
            prompt_template = self.prompt_templates[template_key]
            
            # 4. Generar prompt final
            final_prompt = prompt_template.format(
                query=query.question,
                context=context
            )
            
            # 5. Generar respuesta con Granite
            answer = self.generate_with_granite(
                final_prompt, 
                query.temperature, 
                query.max_tokens
            )
            
            # 6. Calcular confidence score
            avg_confidence = sum(doc.get('confidence', 0) for doc in documents) / len(documents)
            
            processing_time = time.time() - start_time
            
            return WatsonRAGResponse(
                answer=answer,
                source_documents=documents,
                confidence_score=avg_confidence,
                processing_time=processing_time,
                watson_metadata={
                    'template_used': template_key,
                    'context_length': len(context),
                    'model_used': self.models_config["generation_model"]
                }
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error en consulta RAG: {e}")
            return WatsonRAGResponse(
                answer=f"Error procesando consulta: {str(e)}",
                source_documents=[],
                confidence_score=0.0,
                processing_time=time.time() - start_time,
                watson_metadata={'error': str(e)}
            )
    
    def get_available_collections(self) -> List[Dict]:
        """Obtiene colecciones disponibles en Discovery"""
        try:
            response = self.discovery_client.list_collections(
                project_id=self.watsonx_config["project_id"]
            ).get_result()
            
            return response.get('collections', [])
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo colecciones: {e}")
            return []

# Script de prueba
if __name__ == "__main__":
    print("🚀 Iniciando Sistema RAG Watson REAL para DECODE-EV...")
    
    try:
        # Inicializar sistema RAG
        rag_system = DecodeEVWatsonRAG()
        
        # Conectar con Watson
        if rag_system.initialize_watson_clients():
            print("✅ Sistema RAG Watson inicializado")
            
            # Obtener colecciones disponibles
            collections = rag_system.get_available_collections()
            print(f"📚 Colecciones disponibles: {len(collections)}")
            
            for collection in collections:
                print(f"   • {collection['name']} (ID: {collection['collection_id']})")
            
            # Ejemplo de consulta (necesitas el collection_id real)
            if collections:
                collection_id = collections[0]['collection_id']
                
                test_queries = [
                    "¿Qué información tienes sobre voltaje en el sistema de carga?",
                    "Analiza las tendencias de temperatura en el cargador",
                    "Diagnostica posibles problemas en la corriente del sistema"
                ]
                
                print("\n🔍 Probando consultas de ejemplo:")
                
                for question in test_queries:
                    print(f"\n➤ Consulta: {question}")
                    
                    query = WatsonRAGQuery(
                        question=question,
                        collection_id=collection_id,
                        max_docs=3,
                        temperature=0.3,
                        max_tokens=512
                    )
                    
                    response = rag_system.query_watson_rag(query)
                    
                    print(f"✅ Procesado en {response.processing_time:.2f}s")
                    print(f"📊 Confianza: {response.confidence_score:.2f}")
                    print(f"📄 Documentos: {len(response.source_documents)}")
                    print(f"🤖 Modelo: {response.watson_metadata.get('model_used', 'N/A')}")
                    print(f"📝 Respuesta: {response.answer[:200]}...")
                    
                print("\n🎯 Sistema RAG Watson completamente funcional!")
            else:
                print("⚠️ No hay colecciones disponibles. Ejecuta 01_watsonx_setup_REAL.py primero.")
        else:
            print("❌ Error inicializando sistema RAG Watson")
            
    except ValueError as e:
        print(f"❌ Error de configuración: {e}")
        print("\n📋 Configuración requerida:")
        print("1. Archivo .env con credenciales IBM Watson")
        print("2. Colección creada en Watson Discovery")
        print("3. Documentos subidos a la colección")
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")