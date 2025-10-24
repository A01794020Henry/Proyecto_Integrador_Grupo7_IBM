# DECODE-EV RAG Dashboard - Interfaz Streamlit para IBM watsonx
# Dashboard interactivo completo para consultas RAG vehiculares

import streamlit as st
import pandas as pd
import json
import jsonlines
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any
import time
import os
from pathlib import Path

# Importar sistema RAG local
try:
    from _03_core_rag_system_complete import DecodeEVRAGSystem, RAGQuery, RAGResponse
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

def setup_page_config():
    """Configura página Streamlit"""
    st.set_page_config(
        page_title="DECODE-EV RAG Dashboard",
        page_icon="🚌",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # CSS personalizado
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #1f4e79 0%, #2e86de 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #2e86de;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .response-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .stButton > button {
        background: linear-gradient(90deg, #2e86de 0%, #54a0ff 100%);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    .source-card {
        background: #e8f4fd;
        padding: 1rem;
        border-radius: 5px;
        border-left: 3px solid #2e86de;
        margin-bottom: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

def initialize_session_state():
    """Inicializa estado de la sesión"""
    if 'rag_system' not in st.session_state:
        st.session_state.rag_system = None
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    if 'dataset_loaded' not in st.session_state:
        st.session_state.dataset_loaded = False
    if 'system_stats' not in st.session_state:
        st.session_state.system_stats = {}

def render_header():
    """Renderiza cabecera principal"""
    st.markdown("""
    <div class="main-header">
        <h1>🚌 DECODE-EV RAG Dashboard</h1>
        <p>Sistema de Consultas Conversacionales para Datos CAN Vehiculares</p>
        <p><strong>Proyecto Integrador - Grupo 7 IBM Watson</strong></p>
    </div>
    """, unsafe_allow_html=True)

def load_rag_system():
    """Carga e inicializa el sistema RAG"""
    if st.session_state.rag_system is None:
        with st.spinner("🔄 Inicializando sistema RAG..."):
            try:
                # Inicializar sistema RAG
                rag_system = DecodeEVRAGSystem()
                
                # Buscar dataset procesado
                dataset_path = Path(__file__).parent / "dataset_processed_watsonx.jsonl"
                
                if dataset_path.exists():
                    if rag_system.load_processed_dataset(str(dataset_path)):
                        st.session_state.rag_system = rag_system
                        st.session_state.dataset_loaded = True
                        st.session_state.system_stats = rag_system.get_system_statistics()
                        st.success("✅ Sistema RAG inicializado correctamente")
                        return True
                    else:
                        st.error("❌ Error cargando dataset procesado")
                        return False
                else:
                    st.error(f"❌ Dataset no encontrado: {dataset_path}")
                    return False
                    
            except Exception as e:
                st.error(f"❌ Error inicializando sistema RAG: {e}")
                return False
    return True

def render_sidebar():
    """Renderiza barra lateral con controles"""
    st.sidebar.markdown("## 📊 Estado del Sistema")
    
    if not RAG_AVAILABLE:
        st.sidebar.error("⚠️ Sistema RAG no disponible")
        st.sidebar.markdown("Asegúrate de que el archivo `03_core_rag_system_complete.py` esté en el directorio.")
        return
    
    # Estado del sistema
    if st.session_state.dataset_loaded:
        st.sidebar.success("✅ Sistema activo")
        
        # Estadísticas del sistema
        if st.session_state.system_stats:
            stats = st.session_state.system_stats
            st.sidebar.markdown("### 📈 Estadísticas")
            st.sidebar.metric("Total Documentos", stats.get('total_documents', 0))
            st.sidebar.metric("Palabras Totales", stats.get('total_words', 0))
            st.sidebar.metric("Densidad Técnica", f"{stats.get('average_technical_density', 0):.3f}")
            
            # Distribución de tipos de documento
            if stats.get('document_types'):
                st.sidebar.markdown("### 📋 Tipos de Documentos")
                for doc_type, count in stats['document_types'].items():
                    st.sidebar.write(f"• {doc_type}: {count}")
            
            # Redes CAN disponibles
            if stats.get('redes_can'):
                st.sidebar.markdown("### 🔌 Redes CAN")
                for red_can, count in stats['redes_can'].items():
                    st.sidebar.write(f"• {red_can}: {count}")
    else:
        st.sidebar.warning("⚠️ Sistema no inicializado")
        if st.sidebar.button("🔄 Inicializar Sistema"):
            load_rag_system()
    
    # Configuración de consultas
    st.sidebar.markdown("### ⚙️ Configuración de Consultas")
    max_docs = st.sidebar.slider("Documentos a recuperar", 1, 10, 3)
    temperature = st.sidebar.slider("Temperatura", 0.0, 1.0, 0.3, 0.1)
    max_tokens = st.sidebar.slider("Tokens máximos", 128, 1024, 512, 64)
    
    return {
        'max_docs': max_docs,
        'temperature': temperature, 
        'max_tokens': max_tokens
    }

def render_query_interface(config):
    """Renderiza interfaz principal de consultas"""
    st.markdown("## 🔍 Consulta Conversacional")
    
    # Ejemplos de consultas predefinidas
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query_input = st.text_area(
            "Escribe tu consulta sobre datos CAN vehiculares:",
            height=100,
            placeholder="Ejemplo: ¿Qué información tienes sobre voltaje en el sistema de carga?"
        )
    
    with col2:
        st.markdown("### 💡 Consultas de Ejemplo")
        example_queries = [
            "¿Qué información tienes sobre voltaje en el sistema de carga?",
            "Explica los eventos de corriente en CAN_CUSTOM_31",
            "¿Cuáles son las tendencias de temperatura en el cargador?",
            "Dame información sobre el protocolo J1939",
            "¿Hay alguna anomalía en los datos de batería?",
            "Analiza los patrones de carga del vehículo"
        ]
        
        for i, example in enumerate(example_queries):
            if st.button(f"Ejemplo {i+1}", key=f"example_{i}", help=example):
                st.session_state.current_query = example
                query_input = example
    
    # Botón de consulta
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col2:
        if st.button("🚀 Consultar", type="primary", disabled=not st.session_state.dataset_loaded):
            if query_input.strip():
                execute_query(query_input, config)
            else:
                st.warning("⚠️ Por favor, ingresa una consulta")

def execute_query(query: str, config: Dict):
    """Ejecuta consulta en el sistema RAG"""
    if not st.session_state.rag_system:
        st.error("❌ Sistema RAG no disponible")
        return
    
    # Crear consulta RAG
    rag_query = RAGQuery(
        question=query,
        max_retrieved_docs=config['max_docs'],
        temperature=config['temperature'],
        max_tokens=config['max_tokens']
    )
    
    # Mostrar indicador de progreso
    with st.spinner("🤔 Procesando consulta..."):
        start_time = time.time()
        
        try:
            # Ejecutar consulta
            response = st.session_state.rag_system.query_rag(rag_query)
            processing_time = time.time() - start_time
            
            # Agregar a historial
            st.session_state.query_history.append({
                'timestamp': datetime.now(),
                'query': query,
                'response': response,
                'processing_time': processing_time
            })
            
            # Renderizar respuesta
            render_response(query, response, processing_time)
            
        except Exception as e:
            st.error(f"❌ Error ejecutando consulta: {e}")

def render_response(query: str, response: RAGResponse, processing_time: float):
    """Renderiza respuesta del sistema RAG"""
    st.markdown("## 💬 Respuesta del Sistema")
    
    # Métricas de la consulta
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("⏱️ Tiempo de Respuesta", f"{processing_time:.2f}s")
    
    with col2:
        st.metric("📊 Confianza", f"{response.confidence_score:.2%}")
    
    with col3:
        st.metric("📄 Documentos", len(response.retrieved_documents))
    
    with col4:
        st.metric("📝 Contexto", f"{response.metadata.get('context_length', 0)} chars")
    
    # Respuesta principal
    st.markdown("### 🎯 Respuesta")
    st.markdown(f"""
    <div class="response-card">
        {response.answer}
    </div>
    """, unsafe_allow_html=True)
    
    # Fuentes utilizadas
    if response.retrieved_documents:
        st.markdown("### 📚 Fuentes Utilizadas")
        
        for i, doc in enumerate(response.retrieved_documents):
            with st.expander(f"📄 Documento {i+1}: {doc.get('id', 'N/A')}", expanded=False):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Tipo:** {doc.get('document_type', 'N/A')}")
                    st.markdown(f"**Red CAN:** {doc.get('metadata', {}).get('red_can', 'N/A')}")
                    st.markdown(f"**Evento:** {doc.get('metadata', {}).get('evento_vehiculo', 'N/A')}")
                    st.markdown(f"**Densidad Técnica:** {doc.get('technical_density_score', 0):.3f}")
                
                with col2:
                    st.markdown(f"**Palabras:** {doc.get('word_count', 0)}")
                    st.markdown(f"**Complejidad:** {doc.get('complexity_score', 0):.3f}")
                
                # Contenido del documento (truncado)
                content = doc.get('text', '')
                if len(content) > 500:
                    content = content[:500] + "..."
                
                st.markdown("**Contenido:**")
                st.text(content)

def render_analytics():
    """Renderiza analytics y visualizaciones"""
    if not st.session_state.query_history:
        st.info("📊 No hay consultas en el historial aún")
        return
    
    st.markdown("## 📊 Analytics y Métricas")
    
    # Convertir historial a DataFrame
    history_df = pd.DataFrame([
        {
            'timestamp': item['timestamp'],
            'query': item['query'][:50] + "..." if len(item['query']) > 50 else item['query'],
            'processing_time': item['processing_time'],
            'confidence': item['response'].confidence_score,
            'documents_used': len(item['response'].retrieved_documents)
        }
        for item in st.session_state.query_history
    ])
    
    # Métricas generales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🔍 Total Consultas", len(history_df))
    
    with col2:
        avg_time = history_df['processing_time'].mean()
        st.metric("⏱️ Tiempo Promedio", f"{avg_time:.2f}s")
    
    with col3:
        avg_confidence = history_df['confidence'].mean() 
        st.metric("📊 Confianza Promedio", f"{avg_confidence:.1%}")
    
    with col4:
        avg_docs = history_df['documents_used'].mean()
        st.metric("📄 Docs Promedio", f"{avg_docs:.1f}")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        # Tiempo de procesamiento por consulta
        fig_time = px.line(
            history_df.reset_index(), 
            x='index', 
            y='processing_time',
            title="⏱️ Tiempo de Procesamiento por Consulta",
            labels={'index': 'Consulta #', 'processing_time': 'Tiempo (s)'}
        )
        fig_time.update_layout(showlegend=False)
        st.plotly_chart(fig_time, use_container_width=True)
    
    with col2:
        # Distribución de confianza
        fig_conf = px.histogram(
            history_df, 
            x='confidence',
            title="📊 Distribución de Confianza",
            labels={'confidence': 'Score de Confianza', 'count': 'Frecuencia'},
            nbins=10
        )
        st.plotly_chart(fig_conf, use_container_width=True)
    
    # Historial detallado
    st.markdown("### 📜 Historial de Consultas")
    st.dataframe(
        history_df[['timestamp', 'query', 'processing_time', 'confidence', 'documents_used']],
        use_container_width=True
    )

def render_dataset_explorer():
    """Renderiza explorador del dataset"""
    if not st.session_state.dataset_loaded:
        st.warning("⚠️ Dataset no cargado")
        return
    
    st.markdown("## 🗂️ Explorador del Dataset")
    
    # Cargar datos para exploración
    dataset_path = Path(__file__).parent / "dataset_processed_watsonx.jsonl"
    
    if not dataset_path.exists():
        st.error("❌ Dataset no encontrado")
        return
    
    # Cargar documentos
    documents = []
    with jsonlines.open(dataset_path) as reader:
        for doc in reader:
            documents.append(doc)
    
    # Convertir a DataFrame para análisis
    df_data = []
    for doc in documents:
        metadata = doc.get('metadata', {})
        df_data.append({
            'id': doc.get('id', ''),
            'document_type': doc.get('document_type', ''),
            'text_length': len(doc.get('text', '')),
            'word_count': doc.get('word_count', 0),
            'technical_density': doc.get('technical_density_score', 0),
            'complexity_score': doc.get('complexity_score', 0),
            'red_can': metadata.get('red_can', ''),
            'evento_vehiculo': metadata.get('evento_vehiculo', ''),
            'intensidad': metadata.get('intensidad', '')
        })
    
    df = pd.DataFrame(df_data)
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        doc_types = st.multiselect(
            "Tipo de Documento",
            options=df['document_type'].unique(),
            default=df['document_type'].unique()
        )
    
    with col2:
        redes_can = st.multiselect(
            "Red CAN",
            options=df['red_can'].unique(),
            default=df['red_can'].unique()
        )
    
    with col3:
        eventos = st.multiselect(
            "Evento Vehicular",
            options=df['evento_vehicular'].unique(),
            default=df['evento_vehicular'].unique()
        )
    
    # Filtrar datos
    filtered_df = df[
        (df['document_type'].isin(doc_types)) &
        (df['red_can'].isin(redes_can)) &
        (df['evento_vehiculo'].isin(eventos))
    ]
    
    # Visualizaciones
    col1, col2 = st.columns(2)
    
    with col1:
        # Densidad técnica por tipo de documento
        fig_density = px.box(
            filtered_df,
            x='document_type',
            y='technical_density',
            title="📊 Densidad Técnica por Tipo de Documento"
        )
        st.plotly_chart(fig_density, use_container_width=True)
    
    with col2:
        # Distribución de longitud de texto
        fig_length = px.histogram(
            filtered_df,
            x='text_length',
            title="📝 Distribución de Longitud de Texto",
            nbins=20
        )
        st.plotly_chart(fig_length, use_container_width=True)
    
    # Tabla de documentos
    st.markdown("### 📋 Documentos Filtrados")
    st.dataframe(filtered_df, use_container_width=True)

def main():
    """Función principal del dashboard"""
    # Configuración inicial
    setup_page_config()
    initialize_session_state()
    
    # Renderizar cabecera
    render_header()
    
    # Verificar disponibilidad del sistema RAG
    if not RAG_AVAILABLE:
        st.error("⚠️ Sistema RAG no disponible. Verifica la instalación y archivos requeridos.")
        st.stop()
    
    # Inicializar sistema si es necesario
    if not st.session_state.dataset_loaded:
        load_rag_system()
    
    # Renderizar barra lateral
    config = render_sidebar()
    
    # Pestañas principales
    tab1, tab2, tab3 = st.tabs(["🔍 Consultas", "📊 Analytics", "🗂️ Dataset"])
    
    with tab1:
        render_query_interface(config)
    
    with tab2:
        render_analytics()
    
    with tab3:
        render_dataset_explorer()
    
    # Footer
    st.markdown("""
    ---
    <div style="text-align: center; color: #666; margin-top: 2rem;">
        <small>DECODE-EV RAG Dashboard - Proyecto Integrador Grupo 7 IBM Watson<br>
        Maestría en Inteligencia Artificial Aplicada - Tecnológico de Monterrey</small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()