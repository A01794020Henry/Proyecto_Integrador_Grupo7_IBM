# IBM watsonx Setup REAL para DECODE-EV
# Configuración con credenciales reales IBM Watson

import os
from dotenv import load_dotenv
from ibm_watson_machine_learning import APIClient
from ibm_watson import DiscoveryV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import pandas as pd
import json
from typing import Dict, List, Any
import logging

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WatsonxRAGConfigReal:
    """
    Configuración REAL para implementación RAG en IBM watsonx
    """
    
    def __init__(self):
        """
        Inicializa configuración con credenciales REALES
        """
        # Verificar que las credenciales existan
        required_vars = [
            "WATSONX_API_KEY", "WATSONX_PROJECT_ID", "WATSONX_URL",
            "DISCOVERY_API_KEY", "DISCOVERY_URL", "DISCOVERY_VERSION"
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Faltan variables de entorno: {missing_vars}")
        
        # Configuración watsonx.ai REAL
        self.watsonx_credentials = {
            "url": os.getenv("WATSONX_URL"),
            "apikey": os.getenv("WATSONX_API_KEY"),
            "project_id": os.getenv("WATSONX_PROJECT_ID")
        }
        
        # Configuración Watson Discovery REAL
        self.discovery_credentials = {
            "apikey": os.getenv("DISCOVERY_API_KEY"),
            "url": os.getenv("DISCOVERY_URL"),
            "version": os.getenv("DISCOVERY_VERSION")
        }
        
        # Configuración específica para DECODE-EV
        self.decode_ev_config = {
            "embedding_model": "ibm/slate-125m-english-rtrvr",
            "llm_model": "ibm/granite-13b-chat-v2",
            "reranker_model": "ibm/slate-125m-english-rtrvr",
            "max_tokens": 2048,
            "temperature": 0.3,
            "top_p": 0.9,
            "top_k": 50
        }
        
        self.wml_client = None
        self.discovery_client = None
        
    def initialize_clients(self):
        """
        Inicializa clientes REALES de IBM watsonx y Watson Discovery
        """
        try:
            logger.info("🔄 Conectando con IBM watsonx.ai...")
            
            # Cliente watsonx.ai REAL
            self.wml_client = APIClient(self.watsonx_credentials)
            self.wml_client.set.default_project(self.watsonx_credentials["project_id"])
            
            # Verificar conexión
            project_details = self.wml_client.projects.get_details()
            logger.info(f"✅ Conectado a proyecto: {project_details['entity']['name']}")
            
            logger.info("🔄 Conectando con Watson Discovery...")
            
            # Cliente Watson Discovery REAL
            authenticator = IAMAuthenticator(self.discovery_credentials["apikey"])
            self.discovery_client = DiscoveryV2(
                version=self.discovery_credentials["version"],
                authenticator=authenticator
            )
            self.discovery_client.set_service_url(self.discovery_credentials["url"])
            
            # Verificar conexión
            collections = self.discovery_client.list_collections(
                project_id=self.watsonx_credentials["project_id"]
            ).get_result()
            logger.info(f"✅ Watson Discovery conectado. Colecciones: {len(collections['collections'])}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error conectando con IBM Watson: {e}")
            return False
    
    def create_discovery_collection(self, collection_name: str = "decode-ev-can-data"):
        """
        Crea colección en Watson Discovery para datos DECODE-EV
        """
        try:
            logger.info(f"🔄 Creando colección '{collection_name}' en Watson Discovery...")
            
            collection_config = {
                'name': collection_name,
                'description': 'Colección de datos CAN vehiculares DECODE-EV procesados con Feature Engineering',
                'language': 'es'  # Español
            }
            
            result = self.discovery_client.create_collection(
                project_id=self.watsonx_credentials["project_id"],
                **collection_config
            ).get_result()
            
            collection_id = result['collection_id']
            logger.info(f"✅ Colección creada exitosamente")
            logger.info(f"   Collection ID: {collection_id}")
            
            return collection_id
            
        except Exception as e:
            logger.error(f"❌ Error creando colección: {e}")
            return None
    
    def upload_documents_to_discovery(self, collection_id: str, documents: List[Dict]):
        """
        Sube documentos procesados a Watson Discovery
        """
        try:
            logger.info(f"📤 Subiendo {len(documents)} documentos a Watson Discovery...")
            
            uploaded_count = 0
            failed_count = 0
            
            for doc in documents:
                try:
                    # Preparar documento para Watson Discovery
                    discovery_doc = {
                        "document_id": doc.get('id'),
                        "title": f"Documento CAN - {doc.get('document_type', 'N/A')}",
                        "text": doc.get('text', ''),
                        "metadata": doc.get('metadata', {})
                    }
                    
                    # Subir documento
                    result = self.discovery_client.add_document(
                        project_id=self.watsonx_credentials["project_id"],
                        collection_id=collection_id,
                        file=json.dumps(discovery_doc).encode('utf-8'),
                        filename=f"{doc.get('id')}.json",
                        file_content_type='application/json'
                    ).get_result()
                    
                    uploaded_count += 1
                    
                except Exception as doc_error:
                    logger.warning(f"⚠️ Error subiendo documento {doc.get('id')}: {doc_error}")
                    failed_count += 1
            
            logger.info(f"✅ Documentos subidos: {uploaded_count}")
            logger.info(f"❌ Documentos fallidos: {failed_count}")
            
            return uploaded_count > 0
            
        except Exception as e:
            logger.error(f"❌ Error subiendo documentos: {e}")
            return False
    
    def test_granite_generation(self, prompt: str):
        """
        Prueba generación con modelo IBM Granite
        """
        try:
            logger.info("🤖 Probando generación con IBM Granite...")
            
            generation_params = {
                "prompt": prompt,
                "model_id": self.decode_ev_config["llm_model"],
                "parameters": {
                    "temperature": self.decode_ev_config["temperature"],
                    "max_new_tokens": 256,
                    "top_p": self.decode_ev_config["top_p"],
                    "top_k": self.decode_ev_config["top_k"]
                }
            }
            
            response = self.wml_client.foundation_models.generate_text(**generation_params)
            generated_text = response['results'][0]['generated_text']
            
            logger.info("✅ Generación con Granite exitosa")
            logger.info(f"📝 Respuesta: {generated_text[:100]}...")
            
            return generated_text
            
        except Exception as e:
            logger.error(f"❌ Error con generación Granite: {e}")
            return None
    
    def test_slate_embeddings(self, texts: List[str]):
        """
        Prueba embeddings con modelo IBM Slate
        """
        try:
            logger.info("🧠 Probando embeddings con IBM Slate...")
            
            embedding_params = {
                "input": texts,
                "model_id": self.decode_ev_config["embedding_model"]
            }
            
            response = self.wml_client.foundation_models.generate_embeddings(**embedding_params)
            embeddings = response['results']
            
            logger.info(f"✅ Embeddings generados para {len(texts)} textos")
            logger.info(f"📊 Dimensión: {len(embeddings[0]['embedding'])}")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"❌ Error con embeddings Slate: {e}")
            return None

# Script de configuración inicial
if __name__ == "__main__":
    print("🚀 Configurando IBM Watson REAL para DECODE-EV...")
    
    try:
        # Inicializar configuración
        config = WatsonxRAGConfigReal()
        
        # Conectar con servicios Watson
        if config.initialize_clients():
            print("✅ Conexión con IBM Watson establecida")
            
            # Crear colección Discovery
            collection_id = config.create_discovery_collection()
            
            if collection_id:
                print(f"✅ Colección creada: {collection_id}")
                
                # Cargar dataset procesado para subir
                import jsonlines
                from pathlib import Path
                
                dataset_path = Path(__file__).parent / "dataset_processed_watsonx.jsonl"
                
                if dataset_path.exists():
                    documents = []
                    with jsonlines.open(dataset_path) as reader:
                        for doc in reader:
                            documents.append(doc)
                    
                    # Subir documentos
                    if config.upload_documents_to_discovery(collection_id, documents):
                        print("✅ Documentos subidos a Watson Discovery")
                        
                        # Probar generación con Granite
                        test_prompt = "Explica el comportamiento del voltaje en sistemas CAN vehiculares."
                        response = config.test_granite_generation(test_prompt)
                        
                        if response:
                            print("✅ Sistema Watson completamente configurado")
                            print(f"🎯 Collection ID para usar: {collection_id}")
                        else:
                            print("⚠️ Sistema parcialmente configurado (sin generación)")
                    else:
                        print("❌ Error subiendo documentos")
                else:
                    print("❌ Dataset procesado no encontrado")
            else:
                print("❌ Error creando colección")
        else:
            print("❌ Error conectando con IBM Watson")
            
    except ValueError as e:
        print(f"❌ Error de configuración: {e}")
        print("\n📋 Para resolver:")
        print("1. Crea un archivo .env en este directorio")
        print("2. Agrega tus credenciales IBM Watson:")
        print("   WATSONX_API_KEY=tu_api_key")
        print("   WATSONX_PROJECT_ID=tu_project_id") 
        print("   WATSONX_URL=https://us-south.ml.cloud.ibm.com")
        print("   DISCOVERY_API_KEY=tu_discovery_key")
        print("   DISCOVERY_URL=https://api.us-south.discovery.watson.cloud.ibm.com")
        print("   DISCOVERY_VERSION=2023-03-31")

    except Exception as e:
        print(f"❌ Error inesperado: {e}")