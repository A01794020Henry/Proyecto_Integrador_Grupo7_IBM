# Script de prueba para Feature Engineering DECODE-EV en IBM watsonx
# Este script ejecuta el pipeline completo de transformación de datos

import sys
import os
from pathlib import Path

# Agregar la ruta del proyecto al sys.path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from dataset_integration_advanced import DatasetRAGFeatureEngineering, FeatureEngineeringConfig

def main():
    """
    Función principal que ejecuta el pipeline de Feature Engineering
    """
    print("=" * 80)
    print("🚀 DECODE-EV: Feature Engineering para IBM watsonx")
    print("   Proyecto Integrador - Grupo 7 IBM Watson")
    print("=" * 80)
    
    # Configuración del pipeline
    config = FeatureEngineeringConfig(
        chunk_size=512,
        chunk_overlap=50,
        quality_threshold=0.6,
        min_text_length=100,
        max_text_length=2000
    )
    
    print(f"📋 Configuración del pipeline:")
    print(f"   • Tamaño de chunk: {config.chunk_size}")
    print(f"   • Overlap de chunk: {config.chunk_overlap}")
    print(f"   • Umbral de calidad: {config.quality_threshold}")
    print(f"   • Longitud mínima texto: {config.min_text_length}")
    print(f"   • Longitud máxima texto: {config.max_text_length}")
    print()
    
    # Inicializar procesador
    processor = DatasetRAGFeatureEngineering(wml_client=None, config=config)
    
    # Rutas de archivos
    dataset_path = Path(project_root).parent / "Ingenieria_de_Caracteristicas" / "dataset_rag_decode_ev.jsonl"
    output_path = project_root / "dataset_processed_watsonx.jsonl"
    report_path = project_root / "feature_engineering_report.json"
    
    print(f"📁 Rutas de archivos:")
    print(f"   • Dataset original: {dataset_path}")
    print(f"   • Dataset procesado: {output_path}")
    print(f"   • Reporte: {report_path}")
    print()
    
    # Verificar que existe el dataset original
    if not dataset_path.exists():
        print(f"❌ Error: No se encontró el dataset original en {dataset_path}")
        print("   Asegúrate de haber generado el dataset con el notebook de Feature Engineering")
        return False
    
    # PASO 1: Cargar dataset original
    print("🔄 PASO 1: Cargando dataset original...")
    if not processor.load_decode_ev_dataset(str(dataset_path)):
        print("❌ Error: No se pudo cargar el dataset original")
        return False
    
    print()
    
    # PASO 2: Aplicar Feature Engineering
    print("🔧 PASO 2: Aplicando pipeline de Feature Engineering...")
    if not processor.apply_feature_engineering_pipeline():
        print("❌ Error: Falló el pipeline de Feature Engineering")
        return False
    
    print()
    
    # PASO 3: Exportar dataset procesado
    print("💾 PASO 3: Exportando dataset procesado...")
    if not processor.export_for_watsonx(str(output_path)):
        print("❌ Error: No se pudo exportar el dataset procesado")
        return False
    
    # PASO 4: Generar reporte
    print("📊 PASO 4: Generando reporte de Feature Engineering...")
    try:
        report = processor.generate_feature_report()
        
        import json
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ Reporte guardado en: {report_path}")
    except Exception as e:
        print(f"⚠️ Advertencia: Error generando reporte: {e}")
    
    # PASO 5: Mostrar resumen de resultados
    print()
    print("=" * 80)
    print("📈 RESUMEN DE RESULTADOS")
    print("=" * 80)
    
    if processor.feature_statistics:
        stats = processor.feature_statistics
        
        print(f"📊 Estadísticas del dataset:")
        print(f"   • Total de registros procesados: {stats.get('total_records', 'N/A')}")
        
        if 'quality_filtering' in stats:
            quality_stats = stats['quality_filtering']
            print(f"   • Registros antes del filtrado: {quality_stats.get('records_before', 'N/A')}")
            print(f"   • Registros después del filtrado: {quality_stats.get('records_after', 'N/A')}")
            print(f"   • Tasa de retención: {quality_stats.get('retention_rate', 0):.2%}")
        
        if 'document_types' in stats:
            print(f"   • Tipos de documentos:")
            for doc_type, count in stats['document_types'].items():
                print(f"     - {doc_type}: {count}")
        
        if 'redes_can' in stats:
            print(f"   • Redes CAN encontradas:")
            for red, count in stats['redes_can'].items():
                print(f"     - {red}: {count}")
        
        if 'text_length_stats' in stats:
            text_stats = stats['text_length_stats']
            print(f"   • Estadísticas de longitud de texto:")
            print(f"     - Promedio: {text_stats.get('mean', 0):.1f} caracteres")
            print(f"     - Mínimo: {text_stats.get('min', 0)} caracteres")
            print(f"     - Máximo: {text_stats.get('max', 0)} caracteres")
    
    print()
    print("🎯 PRÓXIMOS PASOS:")
    print("   1. Revisar el dataset procesado en:", str(output_path))
    print("   2. Analizar el reporte de Feature Engineering en:", str(report_path))
    print("   3. Integrar el dataset con IBM watsonx Discovery")
    print("   4. Configurar el sistema RAG principal")
    print()
    print("✅ Feature Engineering completado exitosamente!")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)