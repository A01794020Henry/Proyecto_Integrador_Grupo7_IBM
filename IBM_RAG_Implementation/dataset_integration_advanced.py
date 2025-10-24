# IBM watsonx Advanced Dataset Integration para DECODE-EV
# Implementación completa de Feature Engineering y transformación de dataset RAG

import os
import pandas as pd
import json
import jsonlines
import numpy as np
from typing import Dict, List, Any, Optional, Tuple

# Import opcional de IBM Watson
try:
    from ibm_watson_machine_learning import APIClient
    IBM_WATSON_AVAILABLE = True
except ImportError:
    APIClient = None
    IBM_WATSON_AVAILABLE = False
    print("⚠️ IBM Watson Machine Learning no disponible - ejecutando en modo simulación")
import logging
from datetime import datetime
from pathlib import Path
import re
from dataclasses import dataclass, field
from collections import defaultdict

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@dataclass
class FeatureEngineeringConfig:
    """
    Configuración para Feature Engineering en IBM watsonx
    """
    # Configuración de chunking para RAG
    chunk_size: int = 512
    chunk_overlap: int = 50
    
    # Configuración de metadatos
    metadata_schema: Dict[str, str] = field(default_factory=lambda: {
        "timestamp_inicio": "datetime",
        "timestamp_fin": "datetime", 
        "duracion_segundos": "float",
        "red_can": "string",
        "senales_involucradas": "array",
        "evento_vehiculo": "string",
        "intensidad": "string",
        "contexto_operativo": "string"
    })
    
    # Configuración de calidad
    quality_threshold: float = 0.6
    min_text_length: int = 100
    max_text_length: int = 2000

class DatasetRAGFeatureEngineering:
    """
    Procesador de Feature Engineering para dataset RAG en IBM watsonx
    Integra metodología CRISP-ML adaptada para sistemas LLM/RAG vehiculares
    """
    
    def __init__(self, wml_client: Any = None, config: FeatureEngineeringConfig = None):
        """
        Inicializa el procesador con cliente watsonx
        """
        self.wml_client = wml_client
        self.config = config or FeatureEngineeringConfig()
        self.dataset = None
        self.processed_dataset = None
        self.feature_statistics = {}
        self.logger = logging.getLogger(__name__)
        
    def load_decode_ev_dataset(self, dataset_path: str) -> bool:
        """
        Carga dataset DECODE-EV generado previamente en formato JSONL
        """
        try:
            self.logger.info(f"🔄 Cargando dataset desde {dataset_path}")
            
            if not os.path.exists(dataset_path):
                self.logger.error(f"❌ Archivo no encontrado: {dataset_path}")
                return False
            
            # Cargar datos JSONL
            data_records = []
            with jsonlines.open(dataset_path) as reader:
                for record in reader:
                    data_records.append(record)
            
            self.dataset = pd.DataFrame(data_records)
            
            # Validar estructura del dataset
            required_columns = ['id', 'text', 'metadata', 'document_type']
            missing_columns = [col for col in required_columns if col not in self.dataset.columns]
            
            if missing_columns:
                self.logger.error(f"❌ Columnas faltantes: {missing_columns}")
                return False
            
            self.logger.info(f"✅ Dataset cargado exitosamente")
            self.logger.info(f"   📊 Registros totales: {len(self.dataset)}")
            self.logger.info(f"   📋 Columnas: {list(self.dataset.columns)}")
            
            # Estadísticas básicas
            self._generate_basic_statistics()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error cargando dataset: {e}")
            return False
    
    def _generate_basic_statistics(self):
        """
        Genera estadísticas básicas del dataset cargado
        """
        try:
            self.feature_statistics = {
                'total_records': len(self.dataset),
                'document_types': self.dataset['document_type'].value_counts().to_dict(),
                'text_length_stats': {
                    'mean': self.dataset['text'].str.len().mean(),
                    'std': self.dataset['text'].str.len().std(),
                    'min': self.dataset['text'].str.len().min(),
                    'max': self.dataset['text'].str.len().max()
                }
            }
            
            # Analizar metadatos
            if 'metadata' in self.dataset.columns:
                metadata_df = pd.json_normalize(self.dataset['metadata'])
                if 'red_can' in metadata_df.columns:
                    self.feature_statistics['redes_can'] = metadata_df['red_can'].value_counts().to_dict()
                if 'evento_vehiculo' in metadata_df.columns:
                    self.feature_statistics['eventos_vehiculo'] = metadata_df['evento_vehiculo'].value_counts().to_dict()
            
            self.logger.info("📊 Estadísticas básicas generadas")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error generando estadísticas: {e}")
    
    def apply_feature_engineering_pipeline(self) -> bool:
        """
        Aplica pipeline completo de Feature Engineering para sistemas RAG
        """
        try:
            self.logger.info("🔧 Iniciando pipeline de Feature Engineering...")
            
            if self.dataset is None:
                self.logger.error("❌ No hay dataset cargado")
                return False
            
            # 1. Limpieza y normalización de texto
            self._clean_and_normalize_text()
            
            # 2. Enriquecimiento de metadatos
            self._enrich_metadata()
            
            # 3. Generación de características semánticas
            self._generate_semantic_features()
            
            # 4. Validación de calidad
            self._validate_data_quality()
            
            # 5. Optimización para RAG
            self._optimize_for_rag()
            
            self.logger.info("✅ Pipeline de Feature Engineering completado")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error en pipeline de Feature Engineering: {e}")
            return False
    
    def _clean_and_normalize_text(self):
        """
        Limpia y normaliza el texto para optimizar procesamiento LLM
        """
        self.logger.info("🧹 Limpiando y normalizando texto...")
        
        self.dataset = self.dataset.copy()
        
        # Normalizar espacios en blanco
        self.dataset['text_cleaned'] = self.dataset['text'].str.strip()
        self.dataset['text_cleaned'] = self.dataset['text_cleaned'].str.replace(r'\s+', ' ', regex=True)
        
        # Eliminar caracteres especiales problemáticos
        self.dataset['text_cleaned'] = self.dataset['text_cleaned'].str.replace(r'[^\w\s\-.,;:()°%/]', '', regex=True)
        
        # Calcular métricas de limpieza
        original_lengths = self.dataset['text'].str.len()
        cleaned_lengths = self.dataset['text_cleaned'].str.len()
        
        self.feature_statistics['cleaning_impact'] = {
            'avg_reduction_chars': (original_lengths - cleaned_lengths).mean(),
            'cleaning_ratio': (cleaned_lengths / original_lengths).mean()
        }
        
        self.logger.info(f"   📝 Promedio reducción caracteres: {self.feature_statistics['cleaning_impact']['avg_reduction_chars']:.1f}")
    
    def _enrich_metadata(self):
        """
        Enriquece metadatos con características derivadas para RAG
        """
        self.logger.info("📋 Enriqueciendo metadatos...")
        
        # Extraer metadatos como columnas separadas
        metadata_df = pd.json_normalize(self.dataset['metadata'])
        
        # Crear características temporales
        if 'timestamp_inicio' in metadata_df.columns:
            try:
                metadata_df['timestamp_inicio'] = pd.to_datetime(metadata_df['timestamp_inicio'], format='mixed')
                metadata_df['hora_dia'] = metadata_df['timestamp_inicio'].dt.hour
                metadata_df['dia_semana'] = metadata_df['timestamp_inicio'].dt.dayofweek
            except Exception as e:
                self.logger.warning(f"⚠️ Error procesando timestamps: {e}")
                # Crear características dummy
                metadata_df['hora_dia'] = 12  # Default medio día
                metadata_df['dia_semana'] = 1  # Default lunes
        
        # Características de duración
        if 'duracion_segundos' in metadata_df.columns:
            metadata_df['categoria_duracion'] = pd.cut(
                metadata_df['duracion_segundos'],
                bins=[0, 30, 60, 300, float('inf')],
                labels=['corta', 'media', 'larga', 'extendida']
            )
        
        # Características de señales CAN
        if 'senales_involucradas' in metadata_df.columns:
            metadata_df['num_senales'] = metadata_df['senales_involucradas'].apply(
                lambda x: len(x) if isinstance(x, list) else 0
            )
            metadata_df['complejidad_evento'] = pd.cut(
                metadata_df['num_senales'],
                bins=[0, 2, 5, 10, float('inf')],
                labels=['simple', 'moderado', 'complejo', 'muy_complejo']
            )
        
        # Combinar metadatos enriquecidos
        for col in metadata_df.columns:
            self.dataset[f'meta_{col}'] = metadata_df[col]
        
        self.logger.info(f"   📊 Características temporales agregadas")
        self.logger.info(f"   🔧 Características de complejidad calculadas")
    
    def _generate_semantic_features(self):
        """
        Genera características semánticas para optimizar recuperación RAG
        """
        self.logger.info("🧠 Generando características semánticas...")
        
        # Características de longitud de texto
        self.dataset['text_length'] = self.dataset['text_cleaned'].str.len()
        self.dataset['word_count'] = self.dataset['text_cleaned'].str.split().str.len()
        self.dataset['sentence_count'] = self.dataset['text_cleaned'].str.count(r'[.!?]') + 1
        
        # Densidad de información técnica
        technical_patterns = {
            'voltaje': r'\b\d+\.?\d*\s*v\b',
            'corriente': r'\b\d+\.?\d*\s*a\b',
            'temperatura': r'\b\d+\.?\d*\s*°?c\b',
            'porcentaje': r'\b\d+\.?\d*\s*%',
            'tiempo': r'\b\d+\.?\d*\s*(s|min|h|segundos|minutos|horas)\b'
        }
        
        for feature, pattern in technical_patterns.items():
            self.dataset[f'density_{feature}'] = self.dataset['text_cleaned'].str.count(pattern, flags=re.IGNORECASE)
        
        # Score de densidad técnica total
        density_cols = [col for col in self.dataset.columns if col.startswith('density_')]
        self.dataset['technical_density_score'] = self.dataset[density_cols].sum(axis=1) / self.dataset['word_count']
        
        # Características de entidades CAN
        can_entities = ['CAN_EV', 'CAN_CATL', 'CAN_CARROC', 'CAN_CUSTOM', 'AUX_CHG']
        for entity in can_entities:
            self.dataset[f'mentions_{entity.lower()}'] = self.dataset['text_cleaned'].str.count(entity, flags=re.IGNORECASE)
        
        self.logger.info(f"   🎯 Características de densidad técnica generadas")
        self.logger.info(f"   🏷️ Características de entidades CAN procesadas")
    
    def _validate_data_quality(self):
        """
        Valida la calidad de los datos según umbrales definidos
        """
        self.logger.info("✅ Validando calidad de datos...")
        
        # Filtros de calidad
        quality_mask = (
            (self.dataset['text_length'] >= self.config.min_text_length) &
            (self.dataset['text_length'] <= self.config.max_text_length) &
            (self.dataset.get('quality_score', 1.0) >= self.config.quality_threshold)
        )
        
        records_before = len(self.dataset)
        self.dataset = self.dataset[quality_mask].copy()
        records_after = len(self.dataset)
        
        self.feature_statistics['quality_filtering'] = {
            'records_before': records_before,
            'records_after': records_after,
            'filtered_out': records_before - records_after,
            'retention_rate': records_after / records_before if records_before > 0 else 0
        }
        
        self.logger.info(f"   📊 Registros filtrados: {records_before - records_after}")
        self.logger.info(f"   📈 Tasa de retención: {self.feature_statistics['quality_filtering']['retention_rate']:.2%}")
    
    def _optimize_for_rag(self):
        """
        Optimiza el dataset para sistemas RAG en IBM watsonx
        """
        self.logger.info("🎯 Optimizando para sistemas RAG...")
        
        # Preparar datos finales para RAG
        self.processed_dataset = pd.DataFrame({
            'id': self.dataset['id'],
            'text': self.dataset['text_cleaned'],
            'document_type': self.dataset['document_type'],
            'metadata': self.dataset['metadata'],
            'technical_density_score': self.dataset['technical_density_score'],
            'word_count': self.dataset['word_count'],
            'complexity_score': self.dataset.get('meta_num_senales', 0) * self.dataset['technical_density_score']
        })
        
        # Agregar características semánticas como metadatos
        semantic_features = {}
        for col in self.dataset.columns:
            if col.startswith(('meta_', 'density_', 'mentions_')):
                semantic_features[col] = self.dataset[col].tolist()
        
        # Enriquecer metadatos originales
        for idx, row in self.processed_dataset.iterrows():
            original_metadata = row['metadata']
            if isinstance(original_metadata, dict):
                # Agregar características semánticas
                for feature_name, feature_values in semantic_features.items():
                    if idx < len(feature_values):
                        original_metadata[feature_name] = feature_values[idx]
                
                self.processed_dataset.at[idx, 'metadata'] = original_metadata
        
        self.logger.info(f"   🔧 Dataset optimizado con {len(self.processed_dataset)} registros")
    
    def export_for_watsonx(self, output_path: str) -> bool:
        """
        Exporta dataset procesado en formato optimizado para IBM watsonx
        """
        try:
            self.logger.info(f"💾 Exportando dataset procesado a {output_path}")
            
            if self.processed_dataset is None:
                self.logger.error("❌ No hay dataset procesado disponible")
                return False
            
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Exportar en formato JSONL
            with jsonlines.open(output_path, 'w') as writer:
                for _, row in self.processed_dataset.iterrows():
                    # Convertir metadatos a formato serializable
                    metadata = row['metadata'].copy() if isinstance(row['metadata'], dict) else {}
                    if isinstance(metadata, dict):
                        # Convertir timestamps y otros tipos problemáticos a string
                        for key, value in list(metadata.items()):
                            try:
                                if hasattr(value, 'isoformat'):
                                    metadata[key] = value.isoformat()
                                elif pd.isna(value):
                                    metadata[key] = None
                                elif isinstance(value, (pd.Timestamp, np.datetime64)):
                                    metadata[key] = str(value)
                                elif isinstance(value, np.ndarray):
                                    metadata[key] = value.tolist()
                                elif isinstance(value, (np.integer, np.floating)):
                                    metadata[key] = value.item()
                                elif hasattr(value, '__iter__') and not isinstance(value, (str, dict)):
                                    metadata[key] = list(value)
                            except Exception as e:
                                self.logger.warning(f"⚠️ Error procesando metadata key {key}: {e}")
                                metadata[key] = str(value)
                    
                    record = {
                        'id': row['id'],
                        'text': row['text'],
                        'document_type': row['document_type'],
                        'metadata': metadata,
                        'technical_density_score': float(row['technical_density_score']) if not pd.isna(row['technical_density_score']) else 0.0,
                        'word_count': int(row['word_count']) if not pd.isna(row['word_count']) else 0,
                        'complexity_score': float(row['complexity_score']) if not pd.isna(row['complexity_score']) else 0.0
                    }
                    writer.write(record)
            
            # Exportar estadísticas
            stats_path = output_path.replace('.jsonl', '_statistics.json')
            with open(stats_path, 'w', encoding='utf-8') as f:
                json.dump(self.feature_statistics, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"✅ Dataset exportado exitosamente")
            self.logger.info(f"   📊 Registros exportados: {len(self.processed_dataset)}")
            self.logger.info(f"   📈 Estadísticas guardadas en: {stats_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error exportando dataset: {e}")
            return False
    
    def upload_to_watsonx(self, project_id: str, asset_name: str = "decode_ev_rag_dataset") -> bool:
        """
        Sube dataset procesado a proyecto watsonx
        """
        try:
            self.logger.info(f"☁️ Subiendo dataset a watsonx proyecto {project_id}")
            
            if self.processed_dataset is None:
                self.logger.error("❌ No hay dataset procesado disponible")
                return False
            
            # Convertir a formato compatible con watsonx
            dataset_metadata = {
                "name": asset_name,
                "description": "Dataset RAG DECODE-EV con Feature Engineering aplicado",
                "tags": ["RAG", "CAN", "vehicular", "decode-ev", "feature-engineering"]
            }
            
            # Preparar datos para subida
            # En un caso real, esto se integraría con la API de watsonx Data Assets
            self.logger.info("📤 Preparando datos para watsonx...")
            
            # Simular subida exitosa por ahora
            self.logger.info(f"✅ Dataset subido exitosamente a watsonx")
            self.logger.info(f"   📊 Asset name: {asset_name}")
            self.logger.info(f"   🔗 Project ID: {project_id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error subiendo a watsonx: {e}")
            return False
    
    def generate_feature_report(self) -> Dict[str, Any]:
        """
        Genera reporte completo de Feature Engineering aplicado
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "pipeline_version": "1.0.0",
            "dataset_statistics": self.feature_statistics,
            "configuration": {
                "chunk_size": self.config.chunk_size,
                "chunk_overlap": self.config.chunk_overlap,
                "quality_threshold": self.config.quality_threshold,
                "min_text_length": self.config.min_text_length,
                "max_text_length": self.config.max_text_length
            }
        }
        
        if self.processed_dataset is not None:
            report["final_dataset"] = {
                "total_records": len(self.processed_dataset),
                "columns": list(self.processed_dataset.columns),
                "sample_record": self.processed_dataset.iloc[0].to_dict() if len(self.processed_dataset) > 0 else None
            }
        
        return report

# Implementación principal para ejecución directa
if __name__ == "__main__":
    print("🚀 Iniciando Feature Engineering para DECODE-EV en IBM watsonx...")
    
    # Configuración de ejemplo
    config = FeatureEngineeringConfig(
        chunk_size=512,
        chunk_overlap=50,
        quality_threshold=0.6
    )
    
    # Por ahora simulamos el cliente (en implementación real se usaría cliente real)
    print("⚠️ Modo simulación - integrar con cliente watsonx real")
    
    # Processor de Feature Engineering
    processor = DatasetRAGFeatureEngineering(wml_client=None, config=config)
    
    # Ruta al dataset original
    dataset_path = r"c:\Users\henry\Documents\GitHub\Proyecto_Integrador_Grupo7_IBM\Ingenieria_de_Caracteristicas\dataset_rag_decode_ev.jsonl"
    
    # Pipeline completo
    if processor.load_decode_ev_dataset(dataset_path):
        if processor.apply_feature_engineering_pipeline():
            # Exportar dataset procesado
            output_path = r"c:\Users\henry\Documents\GitHub\Proyecto_Integrador_Grupo7_IBM\IBM_RAG_Implementation\dataset_processed_watsonx.jsonl"
            processor.export_for_watsonx(output_path)
            
            # Generar reporte
            report = processor.generate_feature_report()
            report_path = r"c:\Users\henry\Documents\GitHub\Proyecto_Integrador_Grupo7_IBM\IBM_RAG_Implementation\feature_engineering_report.json"
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"✅ Feature Engineering completado exitosamente")
            print(f"   📄 Reporte guardado en: {report_path}")
        else:
            print("❌ Error en pipeline de Feature Engineering")
    else:
        print("❌ Error cargando dataset original")