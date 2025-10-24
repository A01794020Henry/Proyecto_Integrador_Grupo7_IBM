# ===================================================================
# DECODE-EV RAG SYSTEM - IBM WATSON STUDIO OPTIMIZED VERSION
# ===================================================================
# Proyecto Integrador Grupo 7 - IBM AI Engineering
# Sistema RAG para análisis de datos vehiculares CAN
# Optimizado para ejecución en IBM Watson Studio / Cloud Pak for Data
# ===================================================================

# CELDA 1: CONFIGURACIÓN DE DEPENDENCIAS PARA IBM
# ===============================================

import subprocess
import sys
import os
from typing import List, Dict, Any, Optional, Union, Tuple
import logging

def setup_ibm_environment():
    """
    Configura el entorno específicamente para IBM Watson Studio
    """
    print("🏢 Configurando entorno IBM Watson Studio...")
    
    # Verificar si estamos en IBM Cloud
    is_ibm_cloud = os.environ.get('PROJECT_ID') is not None or \
                   os.environ.get('DSX_PROJECT_DIR') is not None
    
    if is_ibm_cloud:
        print("✅ Detectado entorno IBM Cloud - Aplicando configuraciones específicas")
        # Configuraciones específicas para IBM Cloud
        os.environ['PYTHONPATH'] = os.environ.get('PYTHONPATH', '') + ':/home/dsxuser/work'
    
    return is_ibm_cloud

def install_package_ibm(package: str, quiet: bool = True) -> bool:
    """
    Instalación de paquetes optimizada para IBM Watson Studio
    """
    try:
        cmd_args = [sys.executable, "-m", "pip", "install", package]
        if quiet:
            cmd_args.extend(["--quiet", "--no-warn-script-location"])
        
        subprocess.check_call(cmd_args, stdout=subprocess.DEVNULL if quiet else None)
        print(f"✅ {package} instalado correctamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando {package}: {e}")
        return False

# Configurar entorno IBM
is_ibm_environment = setup_ibm_environment()

# Dependencias optimizadas para IBM Watson Studio
dependencias_ibm = [
    "pandas>=1.5.0",
    "numpy>=1.21.0", 
    "matplotlib>=3.5.0",
    "seaborn>=0.11.0",
    "plotly>=5.0.0",
    "jsonlines",
    "sentence-transformers",
    "langchain>=0.1.0",
    "langchain-community",
    "tiktoken"
]

print("🔧 Instalando dependencias para IBM Watson Studio...")
print("=" * 60)

exitos = 0
for paquete in dependencias_ibm:
    if install_package_ibm(paquete):
        exitos += 1

print(f"\n📊 Instalación completada: {exitos}/{len(dependencias_ibm)} paquetes")
if exitos == len(dependencias_ibm):
    print("🚀 Entorno IBM completamente configurado")


# CELDA 2: IMPORTACIONES Y CONFIGURACIÓN BASE
# ==========================================

import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re
from dataclasses import dataclass, field
from pathlib import Path
from collections import defaultdict
import warnings

# Configuraciones específicas para IBM
warnings.filterwarnings('ignore')
pd.set_option('display.max_columns', 15)
pd.set_option('display.max_rows', 50)

# Logging optimizado para IBM
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Configuración de estilos para IBM Watson Studio
try:
    plt.style.use('seaborn-v0_8-whitegrid')
except:
    try:
        plt.style.use('seaborn-whitegrid')
    except:
        plt.style.use('default')

# Paleta de colores optimizada para IBM
colores_ibm = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
sns.set_palette(colores_ibm)

print("✅ Configuración base IBM completada")


# CELDA 3: ESTRUCTURAS DE DATOS RAG
# ================================

@dataclass
class CANEventMetadata:
    """Metadatos estructurados para eventos CAN en sistema RAG"""
    timestamp_inicio: str
    timestamp_fin: str
    duracion_segundos: float
    red_can: str
    senales_involucradas: List[str]
    evento_vehiculo: str
    intensidad: str = "medio"
    contexto_operativo: str = "normal"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp_inicio': self.timestamp_inicio,
            'timestamp_fin': self.timestamp_fin,
            'duracion_segundos': self.duracion_segundos,
            'red_can': self.red_can,
            'senales_involucradas': self.senales_involucradas,
            'evento_vehiculo': self.evento_vehiculo,
            'intensidad': self.intensidad,
            'contexto_operativo': self.contexto_operativo
        }

@dataclass
class RAGDocument:
    """Documento estructurado para sistema RAG vehicular"""
    id: str
    contenido_textual: str
    metadatos: CANEventMetadata
    tipo_documento: str = "evento_can"
    calidad_descripcion: float = 0.8
    
    def to_jsonl_entry(self) -> Dict[str, Any]:
        """Convierte el documento a formato JSONL para entrenamiento"""
        return {
            'id': self.id,
            'text': self.contenido_textual,
            'metadata': self.metadatos.to_dict(),
            'document_type': self.tipo_documento,
            'quality_score': self.calidad_descripcion,
            'created_at': datetime.now().isoformat()
        }

class GeneradorTextualCAN:
    """Generador de descripciones textuales para señales CAN"""
    
    def __init__(self):
        self.plantillas_descripcion = {
            'rpm': "El motor opera a {valor:.0f} RPM, {interpretacion}",
            'velocidad': "La velocidad del vehículo es {valor:.1f} km/h, {interpretacion}",
            'temperatura': "La temperatura registra {valor:.1f}°C, {interpretacion}",
            'voltaje': "El voltaje mide {valor:.2f}V, {interpretacion}",
            'porcentaje': "El nivel indica {valor:.1f}%, {interpretacion}",
            'generica': "La señal {nombre} presenta valor {valor:.3f}, {interpretacion}"
        }
    
    def generar_descripcion_signal(self, nombre_senal: str, serie: pd.Series, 
                                 timestamps: pd.Series, red_can: str) -> str:
        """Genera descripción textual inteligente para una señal"""
        try:
            valor_medio = serie.mean()
            valor_min = serie.min()
            valor_max = serie.max()
            tendencia = serie.iloc[-1] - serie.iloc[0]
            
            # Detectar tipo de señal por nombre y rango
            tipo_senal = self._detectar_tipo_senal(nombre_senal, valor_medio, valor_max - valor_min)
            
            # Generar interpretación contextual
            interpretacion = self._generar_interpretacion(valor_medio, tendencia, tipo_senal)
            
            # Usar plantilla apropiada
            plantilla = self.plantillas_descripcion.get(tipo_senal, self.plantillas_descripcion['generica'])
            
            if tipo_senal == 'generica':
                descripcion = plantilla.format(nombre=nombre_senal, valor=valor_medio, interpretacion=interpretacion)
            else:
                descripcion = plantilla.format(valor=valor_medio, interpretacion=interpretacion)
            
            return f"{descripcion} (Red: {red_can})"
            
        except Exception as e:
            return f"Señal {nombre_senal} en red {red_can} con comportamiento variable"
    
    def _detectar_tipo_senal(self, nombre: str, valor_medio: float, rango: float) -> str:
        """Detecta el tipo de señal basado en nombre y características estadísticas"""
        nombre_lower = nombre.lower()
        
        if 'rpm' in nombre_lower:
            return 'rpm'
        elif any(word in nombre_lower for word in ['velocidad', 'speed', 'vel']):
            return 'velocidad'
        elif any(word in nombre_lower for word in ['temp', 'temperatura']):
            return 'temperatura'
        elif any(word in nombre_lower for word in ['volt', 'voltage', 'tension']):
            return 'voltaje'
        elif 0 <= valor_medio <= 100 and rango > 10:
            return 'porcentaje'
        else:
            return 'generica'
    
    def _generar_interpretacion(self, valor: float, tendencia: float, tipo: str) -> str:
        """Genera interpretación contextual del comportamiento"""
        if abs(tendencia) < 0.1:
            comportamiento = "manteniéndose estable"
        elif tendencia > 0:
            comportamiento = "con tendencia creciente"
        else:
            comportamiento = "con tendencia decreciente"
        
        if tipo == 'rpm':
            if valor < 800:
                estado = "indicando ralentí"
            elif valor > 3000:
                estado = "en alta demanda"
            else:
                estado = "en operación normal"
        elif tipo == 'temperatura':
            if valor > 90:
                estado = "en rango elevado"
            elif valor < 20:
                estado = "en rango bajo"
            else:
                estado = "en rango normal"
        else:
            estado = "en operación"
        
        return f"{comportamiento}, {estado}"

# Inicializar generador
generador_textual = GeneradorTextualCAN()
print("✅ Estructuras de datos RAG inicializadas")


# CELDA 4: GENERADOR DE METADATOS INTELIGENTE
# ==========================================

class GeneradorMetadatosCAN:
    """Generador inteligente de metadatos para eventos CAN"""
    
    def __init__(self):
        self.tipos_evento = {
            'aceleracion': ['rpm', 'velocidad', 'throttle'],
            'frenado': ['brake', 'decel', 'pressure'],
            'temperatura': ['temp', 'coolant', 'oil'],
            'electrico': ['volt', 'current', 'battery'],
            'transmision': ['gear', 'clutch', 'torque']
        }
    
    def generar_metadatos_evento(self, descripcion_textual: str, timestamp_inicio: datetime,
                               duracion: float, red_can: str, senales_involucradas: List[str],
                               stats_numericas: Dict[str, float]) -> CANEventMetadata:
        """Genera metadatos completos para un evento CAN"""
        
        # Detectar tipo de evento basado en señales
        evento_vehiculo = self._clasificar_evento(senales_involucradas)
        
        # Determinar intensidad basada en estadísticas
        intensidad = self._calcular_intensidad(stats_numericas)
        
        # Generar timestamp de fin
        timestamp_fin = timestamp_inicio + timedelta(seconds=duracion)
        
        return CANEventMetadata(
            timestamp_inicio=timestamp_inicio.isoformat(),
            timestamp_fin=timestamp_fin.isoformat(),
            duracion_segundos=duracion,
            red_can=red_can,
            senales_involucradas=senales_involucradas,
            evento_vehiculo=evento_vehiculo,
            intensidad=intensidad,
            contexto_operativo=self._determinar_contexto(stats_numericas)
        )
    
    def _clasificar_evento(self, senales: List[str]) -> str:
        """Clasifica el tipo de evento basado en las señales involucradas"""
        senales_texto = ' '.join(senales).lower()
        
        for tipo_evento, palabras_clave in self.tipos_evento.items():
            if any(palabra in senales_texto for palabra in palabras_clave):
                return tipo_evento
        
        return "evento_general"
    
    def _calcular_intensidad(self, stats: Dict[str, float]) -> str:
        """Calcula la intensidad del evento basada en las estadísticas"""
        cambio_relativo = stats.get('cambio_relativo_promedio', 0)
        
        if cambio_relativo > 0.5:
            return "alto"
        elif cambio_relativo > 0.2:
            return "medio"
        else:
            return "bajo"
    
    def _determinar_contexto(self, stats: Dict[str, float]) -> str:
        """Determina el contexto operativo del vehículo"""
        velocidad = stats.get('velocidad_promedio', 0)
        
        if velocidad > 80:
            return "autopista"
        elif velocidad > 30:
            return "urbano"
        elif velocidad > 0:
            return "trafico_lento"
        else:
            return "detenido"
    
    def calcular_calidad_descripcion(self, descripcion: str, num_senales: int) -> float:
        """Calcula un score de calidad para la descripción generada"""
        # Factores de calidad
        longitud_factor = min(len(descripcion) / 100, 1.0)  # Longitud óptima ~100 chars
        senales_factor = min(num_senales / 5, 1.0)  # Máximo 5 señales
        
        # Bonificación por palabras técnicas
        palabras_tecnicas = ['rpm', 'temperatura', 'voltaje', 'velocidad', 'operación']
        tecnico_factor = sum(1 for palabra in palabras_tecnicas if palabra in descripcion.lower()) / len(palabras_tecnicas)
        
        calidad = (longitud_factor * 0.4 + senales_factor * 0.4 + tecnico_factor * 0.2)
        return round(calidad, 3)

# Inicializar generador de metadatos
generador_metadatos = GeneradorMetadatosCAN()
print("✅ Generador de metadatos inicializado")


# CELDA 5: PROCESADOR DE DOCUMENTACIÓN TÉCNICA
# ============================================

class ProcesadorDocumentacionTecnica:
    """Procesador de documentación técnica para integración RAG"""
    
    def __init__(self):
        self.chunk_size = 1000
        self.chunk_overlap = 200
        
    def procesar_documento_completo(self, contenido: str, metodo: str = "semantico") -> List[RAGDocument]:
        """Procesa un documento técnico completo y genera chunks RAG"""
        
        if metodo == "semantico":
            return self._procesar_semantico(contenido)
        else:
            return self._procesar_basico(contenido)
    
    def _procesar_semantico(self, contenido: str) -> List[RAGDocument]:
        """Procesamiento semántico avanzado del documento"""
        
        # Simular documento técnico J1939 para demo
        doc_j1939_demo = """
        J1939 es un protocolo de comunicación vehicular estándar que define cómo los componentes
        electrónicos del vehículo se comunican entre sí. 
        
        Las redes CAN utilizan identificadores de mensaje específicos:
        - CAN_IDS: Red principal de identificadores del motor
        - CAN_CATL: Red de monitoreo de batería y sistemas eléctricos  
        - CAN_GS: Red de sistemas generales del vehículo
        
        Los parámetros típicos incluyen:
        - RPM del motor: Revoluciones por minuto del motor
        - Temperatura del refrigerante: Control térmico del motor
        - Voltaje del sistema: Monitoreo eléctrico principal
        - Estado de carga de batería: Nivel energético disponible
        """
        
        # Dividir en chunks semánticos
        secciones = doc_j1939_demo.split('\n\n')
        documentos_rag = []
        
        for i, seccion in enumerate(secciones):
            if len(seccion.strip()) < 50:  # Ignorar secciones muy cortas
                continue
            
            metadatos = CANEventMetadata(
                timestamp_inicio=datetime.now().isoformat(),
                timestamp_fin=datetime.now().isoformat(),
                duracion_segundos=0.0,
                red_can="DOCUMENTACION",
                senales_involucradas=[],
                evento_vehiculo="referencia_tecnica",
                intensidad="informativo",
                contexto_operativo="documentacion"
            )
            
            doc_rag = RAGDocument(
                id=f"DOC_J1939_{i}",
                contenido_textual=seccion.strip(),
                metadatos=metadatos,
                tipo_documento="documentacion_tecnica",
                calidad_descripcion=0.9
            )
            
            documentos_rag.append(doc_rag)
        
        return documentos_rag
    
    def _procesar_basico(self, contenido: str) -> List[RAGDocument]:
        """Procesamiento básico por chunks de tamaño fijo"""
        chunks = []
        
        for i in range(0, len(contenido), self.chunk_size - self.chunk_overlap):
            chunk = contenido[i:i + self.chunk_size]
            if len(chunk.strip()) > 100:  # Ignorar chunks muy pequeños
                chunks.append(chunk.strip())
        
        return [self._crear_documento_chunk(chunk, i) for i, chunk in enumerate(chunks)]
    
    def _crear_documento_chunk(self, chunk: str, indice: int) -> RAGDocument:
        """Crea un documento RAG para un chunk de texto"""
        metadatos = CANEventMetadata(
            timestamp_inicio=datetime.now().isoformat(),
            timestamp_fin=datetime.now().isoformat(),
            duracion_segundos=0.0,
            red_can="DOCUMENTACION",
            senales_involucradas=[],
            evento_vehiculo="chunk_documental",
            intensidad="informativo",
            contexto_operativo="procesamiento"
        )
        
        return RAGDocument(
            id=f"CHUNK_{indice}",
            contenido_textual=chunk,
            metadatos=metadatos,
            tipo_documento="chunk_documentacion",
            calidad_descripcion=0.7
        )

# Inicializar procesador
procesador_docs = ProcesadorDocumentacionTecnica()
print("✅ Procesador de documentación técnica inicializado")


# CELDA 6: GENERACIÓN DE DATOS DEMO PARA IBM
# =========================================

def generar_datos_demo_ibm() -> Dict[str, pd.DataFrame]:
    """
    Genera datos de demostración para pruebas en IBM Watson Studio
    Simula datos reales de redes CAN vehiculares
    """
    print("🔄 Generando datos de demostración para IBM Watson Studio...")
    
    np.random.seed(42)  # Reproducibilidad
    n_samples = 150  # Optimizado para demo en IBM
    
    # Timestamps base
    base_time = datetime.now()
    timestamps = [base_time + timedelta(seconds=i) for i in range(n_samples)]
    
    # CAN_IDS - Red principal del motor
    can_ids_data = {
        'timestamp': timestamps,
        'RPM_Motor': np.random.normal(2000, 500, n_samples).clip(600, 4000),
        'Velocidad_Vehiculo_KMH': np.random.normal(60, 20, n_samples).clip(0, 120),
        'Temperatura_Motor_C': np.random.normal(85, 10, n_samples).clip(70, 110),
        'Presion_Aceite_Bar': np.random.normal(3, 0.5, n_samples).clip(2, 5),
        'Posicion_Acelerador_Pct': np.random.normal(30, 15, n_samples).clip(0, 100)
    }
    
    # CAN_CATL - Red de batería (señales desconocidas para hipótesis)
    can_catl_data = {
        'timestamp': timestamps,
        'Signal_01': np.random.normal(85, 10, n_samples).clip(20, 100),  # Posible SOC
        'Signal_02': np.random.normal(3.7, 0.2, n_samples).clip(3.2, 4.1),  # Posible voltaje celda
        'Signal_03': np.random.normal(35, 8, n_samples).clip(20, 60),  # Posible temperatura
        'Signal_04': np.random.normal(12.5, 0.5, n_samples).clip(11, 14),  # Posible voltaje sistema
        'Signal_05': np.random.choice([0, 1], n_samples, p=[0.9, 0.1])  # Posible alarma
    }
    
    # CAN_GS - Red de sistemas generales
    can_gs_data = {
        'timestamp': timestamps,
        'Nivel_Combustible_Pct': np.random.normal(50, 20, n_samples).clip(5, 95),
        'Temperatura_Exterior_C': np.random.normal(22, 5, n_samples),
        'Estado_Frenos': np.random.choice([0, 1], n_samples, p=[0.8, 0.2]),
        'Posicion_Volante_Deg': np.random.normal(0, 45, n_samples).clip(-180, 180),
        'Consumo_Combustible_LH': np.random.normal(8, 2, n_samples).clip(4, 15)
    }
    
    datos_demo = {
        'CAN_IDS': pd.DataFrame(can_ids_data),
        'CAN_CATL': pd.DataFrame(can_catl_data), 
        'CAN_GS': pd.DataFrame(can_gs_data)
    }
    
    print(f"✅ Datos generados:")
    for red, df in datos_demo.items():
        print(f"   {red}: {len(df)} registros, {len(df.columns)-1} señales")
    
    return datos_demo

# Generar datos demo
datos_can = generar_datos_demo_ibm()


# CELDA 7: CONSTRUCTOR PRINCIPAL DEL DATASET RAG
# ==============================================

class ConstructorDatasetRAG_IBM:
    """
    Constructor del dataset RAG optimizado para IBM Watson Studio
    Integra todas las fuentes de datos en formato JSONL para LLM
    """
    
    def __init__(self, ruta_salida: str = "./"):
        self.ruta_salida = Path(ruta_salida)
        self.documentos_rag = []
        
        # Estadísticas del dataset
        self.stats = {
            'total_documentos': 0,
            'eventos_can': 0,
            'documentacion_tecnica': 0,
            'hipotesis_catl': 0,
            'calidad_promedio': 0.0
        }
    
    def generar_evento_can_completo(self, df_segmento: pd.DataFrame,
                                   red_can: str, indice_segmento: int) -> Optional[RAGDocument]:
        """Genera un documento RAG completo para un segmento de datos CAN"""
        try:
            # 1. Información temporal
            timestamp_inicio = df_segmento['timestamp'].iloc[0] if 'timestamp' in df_segmento.columns else datetime.now()
            duracion = len(df_segmento)
            
            # 2. Análisis de señales numéricas
            senales_numericas = df_segmento.select_dtypes(include=[np.number]).columns.tolist()
            if 'timestamp' in senales_numericas:
                senales_numericas.remove('timestamp')
            
            # 3. Generar descripciones textuales
            descripciones_senales = []
            for senal in senales_numericas[:5]:  # Limitar para eficiencia
                try:
                    serie = df_segmento[senal].dropna()
                    if len(serie) > 2:
                        desc = generador_textual.generar_descripcion_signal(
                            senal, serie, 
                            df_segmento['timestamp'] if 'timestamp' in df_segmento.columns else pd.Series(range(len(serie))), 
                            red_can
                        )
                        descripciones_senales.append(desc)
                except Exception as e:
                    logger.warning(f"Error procesando señal {senal}: {e}")
            
            # 4. Combinar en descripción completa
            descripcion_completa = f"Evento en red {red_can} (Segmento {indice_segmento}):\n"
            descripcion_completa += "\n".join([f"- {desc}" for desc in descripciones_senales])
            
            # 5. Calcular estadísticas
            stats_numericas = {
                'cambio_relativo_promedio': np.mean([
                    abs(df_segmento[col].iloc[-1] - df_segmento[col].iloc[0]) /
                    (df_segmento[col].mean() + 1e-6)
                    for col in senales_numericas if len(df_segmento[col].dropna()) > 1
                ]) if senales_numericas else 0.0,
                'velocidad_promedio': df_segmento.get('Velocidad_Vehiculo_KMH', pd.Series([0])).mean()
            }
            
            # 6. Generar metadatos
            metadatos = generador_metadatos.generar_metadatos_evento(
                descripcion_textual=descripcion_completa,
                timestamp_inicio=timestamp_inicio if isinstance(timestamp_inicio, datetime) else datetime.now(),
                duracion=float(duracion),
                red_can=red_can,
                senales_involucradas=senales_numericas,
                stats_numericas=stats_numericas
            )
            
            # 7. Calcular calidad
            calidad = generador_metadatos.calcular_calidad_descripcion(
                descripcion_completa, len(senales_numericas)
            )
            
            # 8. Crear documento RAG
            doc_rag = RAGDocument(
                id=f"{red_can}_evento_{indice_segmento}",
                contenido_textual=descripcion_completa,
                metadatos=metadatos,
                tipo_documento="evento_can",
                calidad_descripcion=calidad
            )
            
            return doc_rag
            
        except Exception as e:
            logger.error(f"Error generando evento CAN: {str(e)}")
            return None
    
    def generar_hipotesis_catl(self, df_catl: pd.DataFrame) -> List[RAGDocument]:
        """Genera hipótesis para señales CATL desconocidas"""
        hipotesis_docs = []
        
        try:
            senales_catl = [col for col in df_catl.columns if col.startswith('Signal_')]
            
            for i, senal in enumerate(senales_catl[:5]):  # Limitar para demo
                serie = df_catl[senal].dropna()
                
                if len(serie) < 10:
                    continue
                
                # Estadísticas
                stats = {
                    'min': serie.min(),
                    'max': serie.max(),
                    'mean': serie.mean(),
                    'std': serie.std(),
                    'rango': serie.max() - serie.min()
                }
                
                # Generar hipótesis
                hipotesis = self._generar_hipotesis_senal_catl(senal, stats)
                
                # Metadatos
                metadatos_hipotesis = CANEventMetadata(
                    timestamp_inicio=datetime.now().isoformat(),
                    timestamp_fin=datetime.now().isoformat(),
                    duracion_segundos=0.0,
                    red_can="CAN_CATL",
                    senales_involucradas=[senal],
                    evento_vehiculo="hipotesis_funcional",
                    intensidad="informativo",
                    contexto_operativo="analisis_exploratorio"
                )
                
                doc_hipotesis = RAGDocument(
                    id=f"CATL_hipotesis_{i}",
                    contenido_textual=hipotesis,
                    metadatos=metadatos_hipotesis,
                    tipo_documento="hipotesis_catl",
                    calidad_descripcion=0.6
                )
                
                hipotesis_docs.append(doc_hipotesis)
                
        except Exception as e:
            logger.error(f"Error generando hipótesis CATL: {str(e)}")
        
        return hipotesis_docs
    
    def _generar_hipotesis_senal_catl(self, nombre_senal: str, stats: Dict) -> str:
        """Genera hipótesis para señal CATL desconocida"""
        
        # Análisis de patrones
        if 0 <= stats['mean'] <= 100 and stats['rango'] > 50:
            tipo_hipotesis = "porcentaje (posible SOC o nivel de carga)"
            comportamiento = f"varía entre {stats['min']:.1f}% y {stats['max']:.1f}%"
        elif 20 <= stats['mean'] <= 60 and stats['std'] < 10:
            tipo_hipotesis = "temperatura (posible temperatura de celda)"
            comportamiento = f"se mantiene entre {stats['min']:.1f}°C y {stats['max']:.1f}°C"
        elif 3.0 <= stats['mean'] <= 4.5 and stats['std'] < 0.5:
            tipo_hipotesis = "voltaje (posible voltaje de celda)"
            comportamiento = f"presenta valores típicos de batería Li-ion entre {stats['min']:.2f}V y {stats['max']:.2f}V"
        elif stats['rango'] < stats['mean'] * 0.1:
            tipo_hipotesis = "valor de estado o configuración"
            comportamiento = f"permanece constante en {stats['mean']:.2f}"
        else:
            tipo_hipotesis = "parámetro operativo no identificado"
            comportamiento = f"muestra variabilidad con promedio de {stats['mean']:.2f}"
        
        hipotesis = f"""
HIPÓTESIS PARA {nombre_senal} (Red CAN_CATL):

Basado en análisis estadístico, esta señal probablemente representa un {tipo_hipotesis}.

Comportamiento observado: {comportamiento}.

Estadísticas clave:
- Valor promedio: {stats['mean']:.3f}
- Desviación estándar: {stats['std']:.3f}
- Rango total: {stats['rango']:.3f}

Esta hipótesis requiere validación con documentación técnica.
"""
        
        return hipotesis
    
    def construir_dataset_completo(self) -> str:
        """Construye el dataset RAG completo"""
        print("📋 Iniciando construcción del dataset RAG en IBM Watson Studio...")
        
        # 1. Procesar eventos CAN
        for nombre_red, df_red in datos_can.items():
            if df_red.empty:
                continue
            
            print(f"🔄 Procesando {nombre_red}...")
            
            # Segmentar datos
            ventana = 30
            n_segmentos = min(len(df_red) // ventana, 3)  # Limitar para demo IBM
            
            for i in range(n_segmentos):
                segmento = df_red.iloc[i*ventana:(i+1)*ventana]
                
                doc_evento = self.generar_evento_can_completo(segmento, nombre_red, i)
                if doc_evento:
                    self.documentos_rag.append(doc_evento)
                    self.stats['eventos_can'] += 1
        
        # 2. Generar hipótesis CATL
        if "CAN_CATL" in datos_can and not datos_can["CAN_CATL"].empty:
            print("🔍 Generando hipótesis para CAN_CATL...")
            hipotesis_catl = self.generar_hipotesis_catl(datos_can["CAN_CATL"])
            self.documentos_rag.extend(hipotesis_catl)
            self.stats['hipotesis_catl'] = len(hipotesis_catl)
        
        # 3. Agregar documentación técnica
        print("📚 Procesando documentación técnica...")
        docs_tecnicos = procesador_docs.procesar_documento_completo("", "semantico")
        self.documentos_rag.extend(docs_tecnicos)
        self.stats['documentacion_tecnica'] = len(docs_tecnicos)
        
        # 4. Calcular estadísticas finales
        self.stats['total_documentos'] = len(self.documentos_rag)
        if self.documentos_rag:
            self.stats['calidad_promedio'] = np.mean([
                doc.calidad_descripcion for doc in self.documentos_rag
            ])
        
        # 5. Exportar a JSONL
        archivo_salida = self.ruta_salida / "dataset_rag_decode_ev_ibm.jsonl"
        
        try:
            # Intentar usar jsonlines
            import jsonlines
            with jsonlines.open(archivo_salida, mode='w') as writer:
                for doc in self.documentos_rag:
                    writer.write(doc.to_jsonl_entry())
        except ImportError:
            # Fallback a JSON estándar
            with open(archivo_salida, 'w', encoding='utf-8') as f:
                for doc in self.documentos_rag:
                    json.dump(doc.to_jsonl_entry(), f, ensure_ascii=False)
                    f.write('\n')
        
        print(f"✅ Dataset RAG guardado en: {archivo_salida}")
        print(f"📊 Estadísticas finales: {self.stats}")
        
        return str(archivo_salida)
    
    def generar_muestra_dataset(self, n_muestras: int = 3) -> Dict:
        """Genera muestra del dataset para inspección"""
        muestra = {}
        
        if len(self.documentos_rag) >= n_muestras:
            for i in range(n_muestras):
                doc = self.documentos_rag[i]
                muestra[f"muestra_{i+1}"] = {
                    "id": doc.id,
                    "tipo": doc.tipo_documento,
                    "contenido_preview": doc.contenido_textual[:200] + "...",
                    "calidad": doc.calidad_descripcion,
                    "evento_vehicular": doc.metadatos.evento_vehiculo,
                    "red_can": doc.metadatos.red_can
                }
        
        return muestra

print("✅ Constructor del dataset RAG para IBM inicializado")


# CELDA 8: EJECUCIÓN Y GENERACIÓN DEL DATASET
# ==========================================

# Ejecutar construcción del dataset
print("🚀 Iniciando construcción del dataset RAG en IBM Watson Studio...")
print("=" * 70)

# Inicializar constructor
constructor_rag = ConstructorDatasetRAG_IBM()

# Construir dataset completo
archivo_dataset = constructor_rag.construir_dataset_completo()

# Mostrar muestra del dataset
muestra = constructor_rag.generar_muestra_dataset(3)

print("\n📋 MUESTRA DEL DATASET GENERADO:")
print("=" * 70)
for key, valor in muestra.items():
    print(f"\n{key.upper()}:")
    for k, v in valor.items():
        print(f"  {k}: {v}")
    print("-" * 50)

print(f"\n🎯 DATASET RAG COMPLETADO PARA IBM")
print(f"📁 Archivo: {archivo_dataset}")
print(f"📊 Total documentos: {constructor_rag.stats['total_documentos']}")
print(f"🚗 Eventos CAN: {constructor_rag.stats['eventos_can']}")
print(f"🔍 Hipótesis CATL: {constructor_rag.stats['hipotesis_catl']}")
print(f"📚 Documentación: {constructor_rag.stats['documentacion_tecnica']}")
print(f"⭐ Calidad promedio: {constructor_rag.stats['calidad_promedio']:.3f}")
print("=" * 70)


# CELDA 9: VISUALIZACIÓN Y ANÁLISIS PARA IBM
# =========================================

def crear_visualizaciones_ibm():
    """Crea visualizaciones optimizadas para IBM Watson Studio"""
    
    print("📊 Generando visualizaciones para IBM Watson Studio...")
    
    # 1. Distribución de tipos de documentos
    tipos_docs = [doc.tipo_documento for doc in constructor_rag.documentos_rag]
    df_tipos = pd.DataFrame({'tipo': tipos_docs}).value_counts().reset_index()
    df_tipos.columns = ['tipo_documento', 'cantidad']
    
    fig1 = px.pie(df_tipos, values='cantidad', names='tipo_documento',
                  title='Distribución de Tipos de Documentos RAG',
                  color_discrete_sequence=colores_ibm)
    fig1.show()
    
    # 2. Calidad de documentos por tipo
    calidades = [(doc.tipo_documento, doc.calidad_descripcion) for doc in constructor_rag.documentos_rag]
    df_calidad = pd.DataFrame(calidades, columns=['tipo', 'calidad'])
    
    fig2 = px.box(df_calidad, x='tipo', y='calidad',
                  title='Distribución de Calidad por Tipo de Documento',
                  color='tipo', color_discrete_sequence=colores_ibm)
    fig2.show()
    
    # 3. Métricas del dataset
    metricas = list(constructor_rag.stats.keys())
    valores = list(constructor_rag.stats.values())
    
    fig3 = go.Figure(data=[
        go.Bar(x=metricas, y=valores, marker_color=colores_ibm)
    ])
    fig3.update_layout(title='Métricas del Dataset RAG DECODE-EV',
                       xaxis_title='Métricas',
                       yaxis_title='Valores')
    fig3.show()
    
    print("✅ Visualizaciones generadas exitosamente")

# Ejecutar visualizaciones
crear_visualizaciones_ibm()

print("\n🎉 SISTEMA RAG DECODE-EV COMPLETADO PARA IBM WATSON STUDIO")
print("🚀 Listo para integración con modelos LLM en IBM watsonx")