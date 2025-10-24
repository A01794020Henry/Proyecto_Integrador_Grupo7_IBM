# IBM watsonx RAG Setup para DECODE-EV
# Configuración inicial y conexión con servicios IBM

import os
from ibm_watson_machine_learning import APIClient
from ibm_watson import DiscoveryV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import pandas as pd
import json
from typing import Dict, List, Any

class WatsonxRAGConfig:
    """
    Configuración inicial para implementación RAG en IBM watsonx
    para el proyecto DECODE-EV
    """
    
    def __init__(self):
        """
        Inicializa configuración con credenciales IBM watsonx
        """
        # Configuración watsonx.ai
        self.watsonx_credentials = {
            "url": "https://us-south.ml.cloud.ibm.com",
            "apikey": os.getenv("WATSONX_API_KEY"),  # Configurar en variables de entorno
            "project_id": os.getenv("WATSONX_PROJECT_ID")
        }
        
        # Configuración Watson Discovery
        self.discovery_credentials = {
            "apikey": os.getenv("DISCOVERY_API_KEY"),
            "url": "https://api.us-south.discovery.watson.cloud.ibm.com",
            "version": "2023-03-31"
        }
        
        # Configuración específica para DECODE-EV
        self.decode_ev_config = {
            "embedding_model": "ibm/slate-125m-english-rtrvr",  # Modelo IBM para embeddings
            "llm_model": "ibm/granite-13b-chat-v2",            # Modelo Granite para generación
            "reranker_model": "ibm/slate-125m-english-rtrvr",  # Modelo para reranking
            "vector_store": "watsonx_data_milvus",             # Vector store integrado
            "max_tokens": 2048,
            "temperature": 0.3  # Baja temperatura para respuestas técnicas precisas
        }
        
        self.wml_client = None
        self.discovery_client = None
        
    def initialize_clients(self):
        """
        Inicializa clientes de IBM watsonx y Watson Discovery
        """
        try:
            # Cliente watsonx.ai
            self.wml_client = APIClient(self.watsonx_credentials)
            self.wml_client.set.default_project(self.watsonx_credentials["project_id"])
            print("✅ watsonx.ai client inicializado correctamente")
            
            # Cliente Watson Discovery
            authenticator = IAMAuthenticator(self.discovery_credentials["apikey"])
            self.discovery_client = DiscoveryV2(
                version=self.discovery_credentials["version"],
                authenticator=authenticator
            )
            self.discovery_client.set_service_url(self.discovery_credentials["url"])
            print("✅ Watson Discovery client inicializado correctamente")
            
            return True
            
        except Exception as e:
            print(f"❌ Error inicializando clientes IBM: {e}")
            return False
    
    def create_decode_ev_project(self, project_name: str = "DECODE-EV-RAG"):
        """
        Crea proyecto específico para DECODE-EV en watsonx
        """
        try:
            project_metadata = {
                "name": project_name,
                "description": "Sistema RAG para análisis conversacional de datos CAN vehiculares - Proyecto Integrador Grupo 7 IBM",
                "tags": ["RAG", "CAN", "vehicular", "electric-bus", "colombia"]
            }
            
            # Crear proyecto en watsonx
            project = self.wml_client.projects.create(project_metadata)
            project_id = project["metadata"]["guid"]
            
            print(f"✅ Proyecto {project_name} creado exitosamente")
            print(f"   Project ID: {project_id}")
            
            return project_id
            
        except Exception as e:
            print(f"❌ Error creando proyecto: {e}")
            return None
    
    def list_available_models(self):
        """
        Lista modelos disponibles para embedding y generación
        """
        try:
            # Modelos de embedding
            embedding_models = self.wml_client.foundation_models.get_supported_models(
                model_type="embedding"
            )
            
            # Modelos de generación
            generation_models = self.wml_client.foundation_models.get_supported_models(
                model_type="text_generation"
            )
            
            print("📊 Modelos de Embedding disponibles:")
            for model in embedding_models["supported_models"]:
                print(f"   - {model['model_id']}: {model.get('description', 'N/A')}")
            
            print("\n🤖 Modelos de Generación disponibles:")
            for model in generation_models["supported_models"]:
                print(f"   - {model['model_id']}: {model.get('description', 'N/A')}")
                
        except Exception as e:
            print(f"❌ Error listando modelos: {e}")

# Ejemplo de uso
if __name__ == "__main__":
    print("🚀 Configurando IBM watsonx para DECODE-EV RAG...")
    
    # Inicializar configuración
    config = WatsonxRAGConfig()
    
    # Inicializar clientes
    if config.initialize_clients():
        # Listar modelos disponibles
        config.list_available_models()
        
        # Crear proyecto DECODE-EV
        project_id = config.create_decode_ev_project()
        
        if project_id:
            print(f"\n✅ Configuración inicial completada")
            print(f"   Siguiente paso: Subir dataset RAG generado")
            print(f"   Project ID: {project_id}")
    else:
        print("❌ Error en configuración inicial")
        print("   Verificar credenciales en variables de entorno:")
        print("   - WATSONX_API_KEY")
        print("   - WATSONX_PROJECT_ID") 
        print("   - DISCOVERY_API_KEY")