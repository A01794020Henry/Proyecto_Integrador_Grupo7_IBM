# IBM watsonx Core RAG System para DECODE-EV
# Sistema principal de Retrieval-Augmented Generation integrado con dataset procesado

import os
import json
import jsonlines
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime
from pathlib import Path
import re
from dataclasses import dataclass, field
import time

# Importación condicional de librerías IBM
try:
    from ibm_watson_machine_learning import APIClient
    from ibm_watson import DiscoveryV2
    from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
    IBM_WATSON_AVAILABLE = True
except ImportError:
    APIClient = None
    DiscoveryV2 = None
    IAMAuthenticator = None
    IBM_WATSON_AVAILABLE = False
    print("⚠️ IBM Watson no disponible - ejecutando en modo simulación")

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@dataclass
class RAGQuery:
    """Estructura para consultas RAG"""
    question: str
    context_filters: Dict[str, Any] = field(default_factory=dict)
    max_retrieved_docs: int = 5
    temperature: float = 0.3
    max_tokens: int = 512

@dataclass
class RAGResponse:
    """Estructura para respuestas RAG"""
    answer: str
    retrieved_documents: List[Dict]
    confidence_score: float
    processing_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)

class DecodeEVRAGSystem:
    """
    Sistema RAG principal para DECODE-EV integrado con IBM watsonx
    Permite consultas conversacionales sobre datos CAN vehiculares
    """
    
    def __init__(self, wml_client: Any = None, discovery_client: Any = None):
        """
        Inicializa el sistema RAG con clientes IBM watsonx
        """
        self.wml_client = wml_client
        self.discovery_client = discovery_client
        self.logger = logging.getLogger(__name__)
        
        # Dataset procesado cargado en memoria
        self.documents = []
        self.vector_index = {}
        
        # Configuración del modelo RAG
        self.rag_config = {
            "embedding_model": "ibm/slate-125m-english-rtrvr",
            "llm_model": "ibm/granite-13b-chat-v2",
            "max_context_length": 4096,
            "top_k_retrieval": 3,
            "temperature": 0.3,
            "max_new_tokens": 512
        }
        
        # Plantillas de prompt especializadas
        self.prompt_templates = {
            "diagnostico_can": """Basándote en la siguiente información técnica de redes CAN vehiculares, 
proporciona un diagnóstico detallado sobre: {query}

Contexto técnico relevante:
{context}

Instrucciones:
- Usa terminología técnica precisa del protocolo CAN
- Incluye valores numéricos específicos cuando estén disponibles
- Proporciona interpretación práctica para técnicos automotrices
- Si detectas anomalías, menciona posibles causas

Diagnóstico:""",
            
            "explicacion_evento": """Explica el siguiente evento vehicular basado en datos CAN reales: {query}

Información de eventos CAN:
{context}

Proporciona una explicación que incluya:
- Descripción del comportamiento observado
- Significado de las señales CAN involucradas
- Interpretación de valores y tendencias
- Contexto operativo del vehículo

Explicación:""",
            
            "analisis_tendencias": """Analiza las tendencias en los datos vehiculares para: {query}

Datos históricos relevantes:
{context}

Análisis requerido:
- Patrones identificados en las señales
- Evolución temporal de parámetros
- Correlaciones entre subsistemas
- Implicaciones para el mantenimiento

Análisis:"""
        }
    
    def load_processed_dataset(self, dataset_path: str) -> bool:
        """
        Carga el dataset procesado por Feature Engineering
        """
        try:
            self.logger.info(f"🔄 Cargando dataset procesado desde {dataset_path}")
            
            if not os.path.exists(dataset_path):
                self.logger.error(f"❌ Dataset no encontrado: {dataset_path}")
                return False
            
            # Cargar documentos procesados
            self.documents = []
            with jsonlines.open(dataset_path) as reader:
                for doc in reader:
                    self.documents.append(doc)
            
            self.logger.info(f"✅ Cargados {len(self.documents)} documentos procesados")
            
            # Generar índice simple por tipo de documento
            self._build_simple_index()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error cargando dataset: {e}")
            return False
    
    def _build_simple_index(self):
        """
        Construye índice simple de documentos por categorías
        """
        self.vector_index = {
            'eventos_can': [],
            'documentacion_tecnica': [],
            'por_red_can': {},
            'por_intensidad': {},
            'por_evento': {}
        }
        
        for i, doc in enumerate(self.documents):
            doc_type = doc.get('document_type', 'unknown')
            metadata = doc.get('metadata', {})
            
            # Índice por tipo de documento
            if doc_type == 'evento_can':
                self.vector_index['eventos_can'].append(i)
            elif doc_type == 'documentacion_tecnica':
                self.vector_index['documentacion_tecnica'].append(i)
            
            # Índice por red CAN
            red_can = metadata.get('red_can', 'unknown')
            if red_can not in self.vector_index['por_red_can']:
                self.vector_index['por_red_can'][red_can] = []
            self.vector_index['por_red_can'][red_can].append(i)
            
            # Índice por intensidad
            intensidad = metadata.get('intensidad', 'unknown')
            if intensidad not in self.vector_index['por_intensidad']:
                self.vector_index['por_intensidad'][intensidad] = []
            self.vector_index['por_intensidad'][intensidad].append(i)
            
            # Índice por tipo de evento
            evento = metadata.get('evento_vehiculo', 'unknown')
            if evento not in self.vector_index['por_evento']:
                self.vector_index['por_evento'][evento] = []
            self.vector_index['por_evento'][evento].append(i)
        
        self.logger.info("📊 Índice de documentos construido")
        
    def retrieve_relevant_documents(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Recupera documentos relevantes basado en la consulta
        """
        try:
            # Análisis simple de la consulta para determinar categoría
            query_lower = query.lower()
            relevant_docs = []
            
            # Estrategia de recuperación basada en palabras clave
            if any(keyword in query_lower for keyword in ['voltaje', 'voltage', 'v']):
                # Buscar documentos con densidad de voltaje
                for i, doc in enumerate(self.documents):
                    if doc.get('metadata', {}).get('density_voltaje', 0) > 0:
                        relevant_docs.append((i, doc))
            
            elif any(keyword in query_lower for keyword in ['corriente', 'current', 'amper']):
                # Buscar documentos con densidad de corriente
                for i, doc in enumerate(self.documents):
                    if doc.get('metadata', {}).get('density_corriente', 0) > 0:
                        relevant_docs.append((i, doc))
            
            elif any(keyword in query_lower for keyword in ['temperatura', 'temperature', 'calor']):
                # Buscar documentos con densidad de temperatura
                for i, doc in enumerate(self.documents):
                    if doc.get('metadata', {}).get('density_temperatura', 0) > 0:
                        relevant_docs.append((i, doc))
            
            elif any(keyword in query_lower for keyword in ['carga', 'charging', 'bateria']):
                # Buscar eventos de carga
                for i, doc in enumerate(self.documents):
                    if doc.get('metadata', {}).get('evento_vehiculo') == 'carga':
                        relevant_docs.append((i, doc))
            
            elif any(keyword in query_lower for keyword in ['j1939', 'protocol', 'standard']):
                # Buscar documentación técnica
                indices = self.vector_index.get('documentacion_tecnica', [])
                for i in indices:
                    relevant_docs.append((i, self.documents[i]))
            
            else:
                # Recuperación general - documentos con mayor densidad técnica
                for i, doc in enumerate(self.documents):
                    density_score = doc.get('technical_density_score', 0)
                    if density_score > 0:
                        relevant_docs.append((i, doc))
            
            # Ordenar por relevancia (densidad técnica o score de complejidad)
            relevant_docs.sort(key=lambda x: (
                x[1].get('technical_density_score', 0) + 
                x[1].get('complexity_score', 0)
            ), reverse=True)
            
            # Retornar top-k documentos
            return [doc for _, doc in relevant_docs[:top_k]]
            
        except Exception as e:
            self.logger.error(f"❌ Error en recuperación de documentos: {e}")
            return []
    
    def generate_context_prompt(self, query: str, documents: List[Dict]) -> str:
        """
        Genera el contexto para el prompt basado en documentos recuperados
        """
        context_parts = []
        
        for i, doc in enumerate(documents):
            doc_text = doc.get('text', '')
            metadata = doc.get('metadata', {})
            
            # Información del documento
            doc_info = f"[Documento {i+1}]\n"
            doc_info += f"Tipo: {doc.get('document_type', 'N/A')}\n"
            
            if metadata.get('red_can'):
                doc_info += f"Red CAN: {metadata['red_can']}\n"
            if metadata.get('evento_vehiculo'):
                doc_info += f"Evento: {metadata['evento_vehiculo']}\n"
            if metadata.get('intensidad'):
                doc_info += f"Intensidad: {metadata['intensidad']}\n"
            
            doc_info += f"Contenido: {doc_text[:500]}...\n"
            context_parts.append(doc_info)
        
        return "\n".join(context_parts)
    
    def select_prompt_template(self, query: str) -> str:
        """
        Selecciona la plantilla de prompt más apropiada basada en la consulta
        """
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in ['diagnostico', 'diagnostic', 'problema', 'error', 'falla']):
            return "diagnostico_can"
        elif any(keyword in query_lower for keyword in ['evento', 'event', 'que paso', 'explicar']):
            return "explicacion_evento"  
        elif any(keyword in query_lower for keyword in ['tendencia', 'trend', 'patron', 'analisis', 'analysis']):
            return "analisis_tendencias"
        else:
            return "explicacion_evento"  # Default
    
    def query_rag_system(self, query: str, max_tokens: int = 512) -> Dict[str, Any]:
        """
        Ejecuta consulta completa en el sistema RAG
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"🔍 Procesando consulta: {query[:100]}...")
            
            # 1. Recuperar documentos relevantes
            relevant_docs = self.retrieve_relevant_documents(query, top_k=self.rag_config["top_k_retrieval"])
            
            if not relevant_docs:
                return {
                    "response": "Lo siento, no encontré información relevante para tu consulta sobre datos CAN vehiculares.",
                    "sources": [],
                    "query": query,
                    "success": False,
                    "processing_time": time.time() - start_time
                }
            
            # 2. Generar contexto
            context = self.generate_context_prompt(query, relevant_docs)
            
            # 3. Seleccionar plantilla de prompt
            template_key = self.select_prompt_template(query)
            prompt_template = self.prompt_templates[template_key]
            
            # 4. Generar prompt final
            final_prompt = prompt_template.format(query=query, context=context)
            
            # 5. Generar respuesta (simulada por ahora)
            response = self._generate_response_simulation(query, relevant_docs, context)
            
            # 6. Preparar fuentes
            sources = []
            for doc in relevant_docs:
                source_info = {
                    "id": doc.get('id', 'N/A'),
                    "type": doc.get('document_type', 'N/A'),
                    "red_can": doc.get('metadata', {}).get('red_can', 'N/A'),
                    "technical_density": doc.get('technical_density_score', 0)
                }
                sources.append(source_info)
            
            processing_time = time.time() - start_time
            
            return {
                "response": response,
                "sources": sources,
                "query": query,
                "success": True,
                "prompt_template": template_key,
                "context_length": len(context),
                "processing_time": processing_time
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error en consulta RAG: {e}")
            return {
                "response": f"Error procesando la consulta: {str(e)}",
                "sources": [],
                "query": query,
                "success": False,
                "processing_time": time.time() - start_time
            }
    
    def query_rag(self, query: RAGQuery) -> RAGResponse:
        """
        Ejecuta consulta usando estructura de datos RAG formal
        """
        start_time = time.time()
        
        try:
            # 1. Recuperar documentos relevantes
            relevant_docs = self.retrieve_relevant_documents(query.question, top_k=query.max_retrieved_docs)
            
            # 2. Generar contexto
            context = self.generate_context_prompt(query.question, relevant_docs)
            
            # 3. Generar respuesta
            response = self._generate_response_simulation(query.question, relevant_docs, context)
            
            # 4. Calcular confidence score
            confidence = self._calculate_confidence_score(query.question, relevant_docs)
            
            processing_time = time.time() - start_time
            
            return RAGResponse(
                answer=response,
                retrieved_documents=relevant_docs,
                confidence_score=confidence,
                processing_time=processing_time,
                metadata={
                    "template_used": self.select_prompt_template(query.question),
                    "context_length": len(context),
                    "documents_retrieved": len(relevant_docs)
                }
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error en consulta RAG formal: {e}")
            return RAGResponse(
                answer=f"Error procesando la consulta: {str(e)}",
                retrieved_documents=[],
                confidence_score=0.0,
                processing_time=time.time() - start_time,
                metadata={"error": str(e)}
            )
    
    def _calculate_confidence_score(self, query: str, documents: List[Dict]) -> float:
        """
        Calcula score de confianza basado en la relevancia de documentos
        """
        if not documents:
            return 0.0
        
        # Score basado en densidad técnica promedio y número de documentos
        avg_density = sum(doc.get('technical_density_score', 0) for doc in documents) / len(documents)
        coverage_bonus = min(len(documents) / 3.0, 1.0)  # Bonus por cobertura
        
        return min((avg_density * 10 + coverage_bonus) / 2, 1.0)
    
    def _generate_response_simulation(self, query: str, docs: List[Dict], context: str) -> str:
        """
        Genera respuesta simulada basada en los documentos recuperados
        (En implementación real se usaría IBM Granite)
        """
        response_parts = []
        
        # Análisis de la consulta
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in ['voltaje', 'voltage']):
            response_parts.append("📊 **Análisis de Voltaje en Sistema CAN:**")
            
            for doc in docs:
                metadata = doc.get('metadata', {})
                if metadata.get('density_voltaje', 0) > 0:
                    red_can = metadata.get('red_can', 'N/A')
                    evento = metadata.get('evento_vehiculo', 'N/A')
                    response_parts.append(f"- En red {red_can}: Evento de {evento} con mediciones de voltaje registradas")
                    
                    # Extraer valores del texto
                    text = doc.get('text', '')
                    voltage_matches = re.findall(r'(\d+\.?\d*)\s*v', text.lower())
                    if voltage_matches:
                        response_parts.append(f"  Valores detectados: {', '.join(voltage_matches)} V")
        
        elif any(keyword in query_lower for keyword in ['corriente', 'current']):
            response_parts.append("⚡ **Análisis de Corriente en Sistema CAN:**")
            
            for doc in docs:
                metadata = doc.get('metadata', {})
                if metadata.get('density_corriente', 0) > 0:
                    red_can = metadata.get('red_can', 'N/A')
                    response_parts.append(f"- Red {red_can}: Registros de corriente disponibles")
                    
                    text = doc.get('text', '')
                    current_matches = re.findall(r'(\d+\.?\d*)\s*a', text.lower())
                    if current_matches:
                        response_parts.append(f"  Valores: {', '.join(current_matches)} A")
        
        elif any(keyword in query_lower for keyword in ['temperatura', 'temperature']):
            response_parts.append("🌡️ **Análisis de Temperatura en Sistema CAN:**")
            
            for doc in docs:
                metadata = doc.get('metadata', {})
                if metadata.get('density_temperatura', 0) > 0:
                    red_can = metadata.get('red_can', 'N/A')
                    response_parts.append(f"- Red {red_can}: Mediciones de temperatura registradas")
                    
                    text = doc.get('text', '')
                    temp_matches = re.findall(r'(\d+\.?\d*)\s*°?c', text.lower())
                    if temp_matches:
                        response_parts.append(f"  Temperaturas: {', '.join(temp_matches)} °C")
        
        else:
            response_parts.append("🔍 **Información General del Sistema CAN:**")
            
            for doc in docs:
                metadata = doc.get('metadata', {})
                doc_type = doc.get('document_type', 'N/A')
                
                if doc_type == 'evento_can':
                    red_can = metadata.get('red_can', 'N/A')
                    evento = metadata.get('evento_vehiculo', 'N/A')
                    intensidad = metadata.get('intensidad', 'N/A')
                    response_parts.append(f"- Red {red_can}: Evento de {evento} (intensidad: {intensidad})")
                    
                elif doc_type == 'documentacion_tecnica':
                    response_parts.append("- Documentación técnica J1939 disponible")
        
        # Agregar recomendaciones técnicas
        response_parts.append("\n💡 **Recomendaciones Técnicas:**")
        response_parts.append("- Monitorear continuamente las señales CAN para detectar anomalías")
        response_parts.append("- Verificar que los valores estén dentro de rangos operativos normales")
        response_parts.append("- Considerar correlaciones entre diferentes subsistemas vehiculares")
        
        return "\n".join(response_parts)
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del sistema RAG
        """
        stats = {
            "total_documents": len(self.documents),
            "document_types": {},
            "redes_can": {},
            "average_technical_density": 0,
            "total_words": 0
        }
        
        total_density = 0
        total_words = 0
        
        for doc in self.documents:
            # Contar tipos de documento
            doc_type = doc.get('document_type', 'unknown')
            stats["document_types"][doc_type] = stats["document_types"].get(doc_type, 0) + 1
            
            # Contar redes CAN
            red_can = doc.get('metadata', {}).get('red_can', 'unknown')
            stats["redes_can"][red_can] = stats["redes_can"].get(red_can, 0) + 1
            
            # Densidad técnica promedio
            density = doc.get('technical_density_score', 0)
            total_density += density
            
            # Total de palabras
            words = doc.get('word_count', 0)
            total_words += words
        
        if self.documents:
            stats["average_technical_density"] = total_density / len(self.documents)
        stats["total_words"] = total_words
        
        return stats

# Implementación principal
if __name__ == "__main__":
    print("🚀 Iniciando Sistema RAG DECODE-EV para IBM watsonx...")
    
    # Inicializar sistema RAG
    rag_system = DecodeEVRAGSystem()
    
    # Cargar dataset procesado
    dataset_path = Path(__file__).parent / "dataset_processed_watsonx.jsonl"
    
    if rag_system.load_processed_dataset(str(dataset_path)):
        print("✅ Sistema RAG inicializado correctamente")
        
        # Mostrar estadísticas del sistema
        stats = rag_system.get_system_statistics()
        print(f"📊 Estadísticas del sistema:")
        print(f"   • Total documentos: {stats['total_documents']}")
        print(f"   • Tipos de documento: {stats['document_types']}")
        print(f"   • Redes CAN: {stats['redes_can']}")
        print(f"   • Densidad técnica promedio: {stats['average_technical_density']:.3f}")
        print(f"   • Total palabras: {stats['total_words']}")
        
        # Ejemplos de consultas con estructura formal
        test_queries = [
            "¿Qué información tienes sobre voltaje en el sistema de carga?",
            "Explica los eventos de corriente en CAN_CUSTOM_31",
            "¿Cuáles son las tendencias de temperatura en el cargador?",
            "Dame información sobre el protocolo J1939"
        ]
        
        print("\n🔍 Probando consultas de ejemplo:")
        for question in test_queries:
            print(f"\n➤ Consulta: {question}")
            
            # Usar estructura formal RAGQuery
            query = RAGQuery(
                question=question,
                max_retrieved_docs=3,
                temperature=0.3,
                max_tokens=512
            )
            
            result = rag_system.query_rag(query)
            
            print(f"✅ Respuesta generada en {result.processing_time:.2f}s")
            print(f"📊 Confianza: {result.confidence_score:.2f}")
            print(f"📄 Documentos utilizados: {len(result.retrieved_documents)}")
            print(f"📝 Respuesta: {result.answer[:200]}...")
        
        print("\n🎯 Sistema RAG listo para consultas interactivas!")
    else:
        print("❌ Error inicializando sistema RAG")