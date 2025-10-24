# Dataset Integration para watsonx RAG
# Integración del dataset DECODE-EV con IBM watsonx Discovery

import os
import json
import jsonlines
from typing import Dict, List, Any, Optional
from pathlib import Path
import pandas as pd
from datetime import datetime

class DecodeEVDatasetIntegrator:
    """
    Integrador del dataset DECODE-EV con IBM watsonx RAG
    Convierte los JSONL generados por el notebook mejorado a formato watsonx
    """
    
    def __init__(self, config: 'WatsonxRAGConfig'):
        """
        Inicializa integrador con configuración watsonx
        
        Args:
            config: Configuración watsonx inicializada
        """
        self.config = config
        self.dataset_stats = {}
        
    def load_decode_ev_dataset(self, dataset_path: str) -> List[Dict]:
        """
        Carga dataset DECODE-EV desde archivos JSONL
        
        Args:
            dataset_path: Ruta al directorio con archivos JSONL
            
        Returns:
            Lista de documentos procesados
        """
        documents = []
        dataset_dir = Path(dataset_path)
        
        if not dataset_dir.exists():
            print(f"❌ Directorio de dataset no encontrado: {dataset_path}")
            return documents
            
        # Buscar archivos JSONL
        jsonl_files = list(dataset_dir.glob("*.jsonl"))
        
        if not jsonl_files:
            print(f"❌ No se encontraron archivos JSONL en: {dataset_path}")
            return documents
            
        print(f"📂 Encontrados {len(jsonl_files)} archivos JSONL")
        
        for file_path in jsonl_files:
            print(f"   Procesando: {file_path.name}")
            
            try:
                with jsonlines.open(file_path, 'r') as reader:
                    file_docs = list(reader)
                    documents.extend(file_docs)
                    print(f"     ✅ {len(file_docs)} documentos cargados")
                    
            except Exception as e:
                print(f"     ❌ Error procesando {file_path.name}: {e}")
                
        print(f"\n📊 Total documentos cargados: {len(documents)}")
        self.dataset_stats["total_documents"] = len(documents)
        
        return documents
    
    def transform_to_watsonx_format(self, documents: List[Dict]) -> List[Dict]:
        """
        Transforma documentos DECODE-EV a formato watsonx Discovery
        
        Args:
            documents: Lista de documentos DECODE-EV
            
        Returns:
            Documentos transformados para watsonx
        """
        watsonx_documents = []
        
        for i, doc in enumerate(documents):
            try:
                # Estructura base watsonx Discovery
                watsonx_doc = {
                    "document_id": f"decode_ev_{i:06d}",
                    "title": f"Evento CAN: {doc.get('tipo_evento', 'Desconocido')}",
                    "text": doc.get("descripcion_textual", ""),
                    "metadata": {
                        # Metadatos técnicos del evento
                        "event_type": doc.get("tipo_evento"),
                        "timestamp": doc.get("timestamp"),
                        "vehicle_id": doc.get("vehiculo_id", "unknown"),
                        "signal_type": doc.get("tipo_senal"),
                        "severity": doc.get("severidad", "medium"),
                        
                        # Metadatos estadísticos
                        "valor_promedio": doc.get("valor_promedio"),
                        "desviacion_estandar": doc.get("desviacion_estandar"),
                        "valor_maximo": doc.get("valor_maximo"),
                        "valor_minimo": doc.get("valor_minimo"),
                        
                        # Contexto temporal
                        "duracion_evento": doc.get("duracion_evento"),
                        "frecuencia_muestreo": doc.get("frecuencia_muestreo"),
                        
                        # Clasificación RAG
                        "source": "decode_ev_dataset",
                        "domain": "vehicular_can_data",
                        "language": "es",
                        "quality_score": doc.get("puntuacion_calidad", 0.0),
                        
                        # Fechas de procesamiento
                        "created_at": datetime.now().isoformat(),
                        "processed_by": "decode_ev_feature_engineering"
                    }
                }
                
                # Agregar contexto adicional si existe
                if "contexto_tecnico" in doc:
                    watsonx_doc["metadata"]["technical_context"] = doc["contexto_tecnico"]
                
                if "recomendaciones" in doc:
                    watsonx_doc["metadata"]["recommendations"] = doc["recomendaciones"]
                
                watsonx_documents.append(watsonx_doc)
                
            except Exception as e:
                print(f"❌ Error transformando documento {i}: {e}")
                continue
        
        print(f"✅ {len(watsonx_documents)} documentos transformados exitosamente")
        self.dataset_stats["transformed_documents"] = len(watsonx_documents)
        
        return watsonx_documents
    
    def create_discovery_collection(self, collection_name: str = "decode-ev-rag") -> Optional[str]:
        """
        Crea colección en Watson Discovery para dataset DECODE-EV
        
        Args:
            collection_name: Nombre de la colección
            
        Returns:
            ID de la colección creada
        """
        try:
            # Configuración de la colección
            collection_config = {
                "name": collection_name,
                "description": "Dataset RAG DECODE-EV: Datos CAN vehiculares transformados para análisis conversacional",
                "language": "es",
                "enrichments": [
                    {
                        "enrichment_id": "natural_language_understanding",
                        "fields": ["text"]
                    }
                ]
            }
            
            # Crear colección usando Discovery API
            environment_id = os.getenv("DISCOVERY_ENVIRONMENT_ID")
            
            response = self.config.discovery_client.create_collection(
                environment_id=environment_id,
                **collection_config
            ).get_result()
            
            collection_id = response["collection_id"]
            print(f"✅ Colección '{collection_name}' creada exitosamente")
            print(f"   Collection ID: {collection_id}")
            
            return collection_id
            
        except Exception as e:
            print(f"❌ Error creando colección Discovery: {e}")
            return None
    
    def upload_documents_to_discovery(self, documents: List[Dict], collection_id: str) -> bool:
        """
        Sube documentos transformados a Watson Discovery
        
        Args:
            documents: Documentos en formato watsonx
            collection_id: ID de la colección de destino
            
        Returns:
            True si la carga fue exitosa
        """
        try:
            environment_id = os.getenv("DISCOVERY_ENVIRONMENT_ID")
            successful_uploads = 0
            
            print(f"📤 Iniciando carga de {len(documents)} documentos...")
            
            for i, doc in enumerate(documents):
                try:
                    # Convertir documento a JSON
                    doc_json = json.dumps(doc, ensure_ascii=False, indent=2)
                    
                    # Subir documento individual
                    response = self.config.discovery_client.add_document(
                        environment_id=environment_id,
                        collection_id=collection_id,
                        file=doc_json.encode('utf-8'),
                        filename=f"{doc['document_id']}.json",
                        file_content_type='application/json'
                    ).get_result()
                    
                    successful_uploads += 1
                    
                    if (i + 1) % 50 == 0:
                        print(f"   📊 Progreso: {i + 1}/{len(documents)} documentos")
                        
                except Exception as e:
                    print(f"   ❌ Error subiendo documento {i}: {e}")
                    continue
            
            print(f"✅ Carga completada: {successful_uploads}/{len(documents)} documentos exitosos")
            self.dataset_stats["uploaded_documents"] = successful_uploads
            
            return successful_uploads > 0
            
        except Exception as e:
            print(f"❌ Error general en carga de documentos: {e}")
            return False
    
    def generate_dataset_report(self, output_path: str = "dataset_integration_report.json"):
        """
        Genera reporte de integración del dataset
        
        Args:
            output_path: Ruta para guardar el reporte
        """
        report = {
            "decode_ev_integration_report": {
                "timestamp": datetime.now().isoformat(),
                "dataset_statistics": self.dataset_stats,
                "integration_status": "completed" if self.dataset_stats.get("uploaded_documents", 0) > 0 else "failed",
                "configuration": {
                    "embedding_model": self.config.decode_ev_config["embedding_model"],
                    "llm_model": self.config.decode_ev_config["llm_model"],
                    "vector_store": self.config.decode_ev_config["vector_store"]
                },
                "next_steps": [
                    "Configurar pipeline de embeddings",
                    "Implementar sistema de retrieval",
                    "Configurar modelo de generación", 
                    "Ejecutar pruebas de RAG"
                ]
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        print(f"📄 Reporte de integración guardado en: {output_path}")

# Función principal de integración
def integrate_decode_ev_dataset(dataset_path: str, config: 'WatsonxRAGConfig'):
    """
    Función principal para integrar dataset DECODE-EV con watsonx
    
    Args:
        dataset_path: Ruta al dataset DECODE-EV
        config: Configuración watsonx
    """
    print("🔄 Iniciando integración dataset DECODE-EV con IBM watsonx...")
    
    # Inicializar integrador
    integrator = DecodeEVDatasetIntegrator(config)
    
    # Cargar dataset
    documents = integrator.load_decode_ev_dataset(dataset_path)
    
    if not documents:
        print("❌ No se pudieron cargar documentos")
        return False
    
    # Transformar a formato watsonx
    watsonx_documents = integrator.transform_to_watsonx_format(documents)
    
    # Crear colección Discovery
    collection_id = integrator.create_discovery_collection()
    
    if not collection_id:
        print("❌ No se pudo crear colección Discovery")
        return False
    
    # Subir documentos
    success = integrator.upload_documents_to_discovery(watsonx_documents, collection_id)
    
    # Generar reporte
    integrator.generate_dataset_report()
    
    if success:
        print("✅ Integración dataset DECODE-EV completada exitosamente")
        print(f"   Collection ID: {collection_id}")
        print(f"   Documentos procesados: {len(watsonx_documents)}")
        return True
    else:
        print("❌ Error en integración dataset")
        return False

if __name__ == "__main__":
    # Ejemplo de uso
    print("📋 Para ejecutar integración:")
    print("   1. Configurar variables de entorno IBM")
    print("   2. Ejecutar: python 01_watsonx_setup.py") 
    print("   3. Ejecutar integración con ruta al dataset DECODE-EV")