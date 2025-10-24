# Script de Deployment para DECODE-EV RAG
# Automatización del proceso de deployment en múltiples entornos

import os
import sys
import json
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import argparse

class DecodeEVDeployment:
    """
    Sistema de deployment automatizado para DECODE-EV RAG
    """
    
    def __init__(self, environment: str = "development"):
        """
        Inicializa deployment manager
        
        Args:
            environment: Entorno de deployment (development, staging, production)
        """
        self.environment = environment
        self.project_root = Path(__file__).parent
        self.deployment_config = self._load_deployment_config()
        
    def _load_deployment_config(self) -> Dict:
        """Carga configuración específica del entorno"""
        configs = {
            "development": {
                "port": 8501,
                "host": "localhost",
                "debug": True,
                "workers": 1,
                "memory": "512M",
                "instances": 1
            },
            "staging": {
                "port": 8502,
                "host": "0.0.0.0", 
                "debug": False,
                "workers": 2,
                "memory": "1G",
                "instances": 2
            },
            "production": {
                "port": 8080,
                "host": "0.0.0.0",
                "debug": False,
                "workers": 4,
                "memory": "2G",
                "instances": 3
            }
        }
        
        return configs.get(self.environment, configs["development"])
    
    def validate_environment(self) -> bool:
        """
        Valida que el entorno esté listo para deployment
        """
        print(f"🔍 Validando entorno {self.environment}...")
        
        checks = []
        
        # 1. Verificar Python
        try:
            result = subprocess.run([sys.executable, "--version"], 
                                  capture_output=True, text=True)
            python_version = result.stdout.strip()
            print(f"   ✅ {python_version}")
            checks.append(True)
        except Exception as e:
            print(f"   ❌ Error verificando Python: {e}")
            checks.append(False)
        
        # 2. Verificar dependencias
        try:
            import streamlit
            import pandas
            import plotly
            print(f"   ✅ Dependencias principales instaladas")
            checks.append(True)
        except ImportError as e:
            print(f"   ❌ Dependencias faltantes: {e}")
            checks.append(False)
        
        # 3. Verificar archivos core
        core_files = [
            "01_watsonx_setup.py",
            "02_dataset_integration.py", 
            "03_core_rag_system.py",
            "04_streamlit_dashboard.py",
            "requirements.txt"
        ]
        
        for file_path in core_files:
            if (self.project_root / file_path).exists():
                print(f"   ✅ {file_path}")
                checks.append(True)
            else:
                print(f"   ❌ Archivo faltante: {file_path}")
                checks.append(False)
        
        # 4. Verificar variables de entorno
        required_vars = ["WATSONX_API_KEY", "WATSONX_PROJECT_ID", "DISCOVERY_API_KEY"]
        
        for var in required_vars:
            if os.getenv(var):
                print(f"   ✅ Variable {var} configurada")
                checks.append(True)
            else:
                print(f"   ⚠️  Variable {var} no configurada")
                checks.append(False)
        
        success_rate = sum(checks) / len(checks)
        print(f"📊 Validación completada: {success_rate:.1%} exitosa")
        
        return success_rate >= 0.8  # 80% de checks exitosos
    
    def create_deployment_package(self) -> Path:
        """
        Crea paquete de deployment
        """
        print("📦 Creando paquete de deployment...")
        
        # Crear directorio de deployment
        deploy_dir = self.project_root / f"deploy_{self.environment}"
        if deploy_dir.exists():
            shutil.rmtree(deploy_dir)
        deploy_dir.mkdir()
        
        # Archivos a incluir
        files_to_copy = [
            "01_watsonx_setup.py",
            "02_dataset_integration.py",
            "03_core_rag_system.py", 
            "04_streamlit_dashboard.py",
            "05_testing_suite.py",
            "requirements.txt",
            "README.md"
        ]
        
        # Copiar archivos
        for file_name in files_to_copy:
            src = self.project_root / file_name
            if src.exists():
                shutil.copy2(src, deploy_dir / file_name)
                print(f"   ✅ Copiado: {file_name}")
            else:
                print(f"   ⚠️  No encontrado: {file_name}")
        
        # Crear archivo de configuración
        self._create_deployment_configs(deploy_dir)
        
        print(f"📦 Paquete creado en: {deploy_dir}")
        return deploy_dir
    
    def _create_deployment_configs(self, deploy_dir: Path):
        """Crea archivos de configuración específicos"""
        
        # 1. Dockerfile
        dockerfile_content = f"""
FROM python:3.9-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Configurar variables
ENV ENVIRONMENT={self.environment}
ENV PORT={self.deployment_config['port']}

# Exponer puerto
EXPOSE {self.deployment_config['port']}

# Comando de inicio
CMD ["streamlit", "run", "04_streamlit_dashboard.py", \\
     "--server.port={self.deployment_config['port']}", \\
     "--server.address={self.deployment_config['host']}", \\
     "--server.enableCORS=false", \\
     "--server.enableXsrfProtection=false"]
"""
        
        with open(deploy_dir / "Dockerfile", "w") as f:
            f.write(dockerfile_content)
        
        # 2. Docker Compose
        compose_content = f"""
version: '3.8'

services:
  decode-ev-rag:
    build: .
    ports:
      - "{self.deployment_config['port']}:{self.deployment_config['port']}"
    environment:
      - ENVIRONMENT={self.environment}
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: {self.deployment_config['memory']}
        reservations:
          memory: 256M

  # Servicio de monitoreo (opcional)
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    restart: unless-stopped
"""
        
        with open(deploy_dir / "docker-compose.yml", "w") as f:
            f.write(compose_content)
        
        # 3. Kubernetes manifests
        k8s_content = f"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: decode-ev-rag-{self.environment}
  labels:
    app: decode-ev-rag
    environment: {self.environment}
spec:
  replicas: {self.deployment_config['instances']}
  selector:
    matchLabels:
      app: decode-ev-rag
      environment: {self.environment}
  template:
    metadata:
      labels:
        app: decode-ev-rag
        environment: {self.environment}
    spec:
      containers:
      - name: rag-app
        image: decode-ev-rag:{self.environment}
        ports:
        - containerPort: {self.deployment_config['port']}
        env:
        - name: ENVIRONMENT
          value: "{self.environment}"
        - name: WATSONX_API_KEY
          valueFrom:
            secretKeyRef:
              name: watsonx-secrets
              key: api-key
        - name: WATSONX_PROJECT_ID
          valueFrom:
            secretKeyRef:
              name: watsonx-secrets
              key: project-id
        - name: DISCOVERY_API_KEY
          valueFrom:
            secretKeyRef:
              name: watsonx-secrets
              key: discovery-key
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "{self.deployment_config['memory']}"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /
            port: {self.deployment_config['port']}
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /
            port: {self.deployment_config['port']}
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: decode-ev-rag-service-{self.environment}
spec:
  selector:
    app: decode-ev-rag
    environment: {self.environment}
  ports:
  - port: 80
    targetPort: {self.deployment_config['port']}
  type: LoadBalancer
"""
        
        # Crear directorio k8s
        k8s_dir = deploy_dir / "k8s"
        k8s_dir.mkdir()
        
        with open(k8s_dir / "deployment.yaml", "w") as f:
            f.write(k8s_content)
        
        # 4. Script de inicio
        start_script = f"""#!/bin/bash

# Script de inicio para DECODE-EV RAG - {self.environment}

echo "🚀 Iniciando DECODE-EV RAG en entorno {self.environment}"

# Verificar variables de entorno
if [ -z "$WATSONX_API_KEY" ]; then
    echo "❌ WATSONX_API_KEY no configurada"
    exit 1
fi

# Ejecutar tests si no es producción
if [ "{self.environment}" != "production" ]; then
    echo "🧪 Ejecutando tests..."
    python 05_testing_suite.py
    if [ $? -ne 0 ]; then
        echo "❌ Tests fallaron"
        exit 1
    fi
fi

# Iniciar aplicación
echo "▶️  Iniciando dashboard Streamlit..."
streamlit run 04_streamlit_dashboard.py \\
    --server.port={self.deployment_config['port']} \\
    --server.address={self.deployment_config['host']} \\
    --server.enableCORS=false \\
    --server.enableXsrfProtection=false
"""
        
        start_script_path = deploy_dir / "start.sh"
        with open(start_script_path, "w") as f:
            f.write(start_script)
        
        # Hacer executable
        os.chmod(start_script_path, 0o755)
        
        print("   ✅ Archivos de configuración creados")
    
    def deploy_local(self, deploy_dir: Path) -> bool:
        """
        Deployment local usando Streamlit directamente
        """
        print(f"🚀 Desplegando localmente en {self.environment}...")
        
        try:
            os.chdir(deploy_dir)
            
            # Comando de inicio
            cmd = [
                sys.executable, "-m", "streamlit", "run", "04_streamlit_dashboard.py",
                "--server.port", str(self.deployment_config['port']),
                "--server.address", self.deployment_config['host']
            ]
            
            if not self.deployment_config['debug']:
                cmd.extend(["--server.headless", "true"])
            
            print(f"📡 Ejecutando: {' '.join(cmd)}")
            print(f"🌐 Accesible en: http://{self.deployment_config['host']}:{self.deployment_config['port']}")
            
            # Ejecutar (bloquea hasta Ctrl+C)
            subprocess.run(cmd, check=True)
            return True
            
        except KeyboardInterrupt:
            print("\n⏹️  Deployment detenido por usuario")
            return True
        except Exception as e:
            print(f"❌ Error en deployment local: {e}")
            return False
    
    def deploy_docker(self, deploy_dir: Path) -> bool:
        """
        Deployment usando Docker
        """
        print(f"🐳 Desplegando con Docker en {self.environment}...")
        
        try:
            os.chdir(deploy_dir)
            
            # Build imagen
            build_cmd = [
                "docker", "build", 
                "-t", f"decode-ev-rag:{self.environment}",
                "."
            ]
            
            print("🔨 Building Docker image...")
            result = subprocess.run(build_cmd, check=True, capture_output=True, text=True)
            print("   ✅ Imagen Docker creada")
            
            # Run container
            run_cmd = [
                "docker", "run", 
                "-p", f"{self.deployment_config['port']}:{self.deployment_config['port']}",
                "--env-file", ".env",
                "--name", f"decode-ev-rag-{self.environment}",
                "--rm",
                f"decode-ev-rag:{self.environment}"
            ]
            
            print(f"🚀 Iniciando container...")
            print(f"🌐 Accesible en: http://localhost:{self.deployment_config['port']}")
            
            subprocess.run(run_cmd, check=True)
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error en deployment Docker: {e}")
            return False
        except KeyboardInterrupt:
            print("\n⏹️  Container detenido por usuario")
            return True
    
    def deploy_cloud(self, deploy_dir: Path, platform: str = "ibm") -> bool:
        """
        Deployment en plataforma cloud
        """
        print(f"☁️  Desplegando en {platform} cloud...")
        
        if platform.lower() == "ibm":
            return self._deploy_ibm_cloud(deploy_dir)
        else:
            print(f"❌ Plataforma {platform} no soportada")
            return False
    
    def _deploy_ibm_cloud(self, deploy_dir: Path) -> bool:
        """Deployment específico para IBM Cloud"""
        try:
            os.chdir(deploy_dir)
            
            # Crear manifest.yml para Cloud Foundry
            manifest_content = f"""
applications:
- name: decode-ev-rag-{self.environment}
  memory: {self.deployment_config['memory']}
  instances: {self.deployment_config['instances']}
  buildpack: python_buildpack
  command: streamlit run 04_streamlit_dashboard.py --server.port=$PORT --server.address=0.0.0.0
  env:
    ENVIRONMENT: {self.environment}
"""
            
            with open("manifest.yml", "w") as f:
                f.write(manifest_content)
            
            # Push a IBM Cloud
            push_cmd = ["ibmcloud", "cf", "push"]
            
            print("📤 Desplegando a IBM Cloud...")
            result = subprocess.run(push_cmd, check=True, capture_output=True, text=True)
            
            print("✅ Deployment exitoso en IBM Cloud")
            print(f"🌐 URL: https://decode-ev-rag-{self.environment}.mybluemix.net")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error desplegando en IBM Cloud: {e}")
            return False
    
    def generate_deployment_report(self, deploy_dir: Path, success: bool):
        """Genera reporte de deployment"""
        report = {
            "deployment_report": {
                "timestamp": datetime.now().isoformat(),
                "environment": self.environment,
                "status": "SUCCESS" if success else "FAILED",
                "configuration": self.deployment_config,
                "deployment_directory": str(deploy_dir),
                "endpoints": {
                    "dashboard": f"http://{self.deployment_config['host']}:{self.deployment_config['port']}",
                    "health": f"http://{self.deployment_config['host']}:{self.deployment_config['port']}/health"
                },
                "next_steps": [
                    "Verificar acceso al dashboard",
                    "Ejecutar tests de integración",
                    "Configurar monitoreo",
                    "Documentar URLs de acceso"
                ]
            }
        }
        
        report_path = deploy_dir / "deployment_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Reporte de deployment: {report_path}")

def main():
    """Función principal de deployment"""
    parser = argparse.ArgumentParser(description="DECODE-EV RAG Deployment Tool")
    parser.add_argument("--environment", "-e", 
                       choices=["development", "staging", "production"],
                       default="development",
                       help="Entorno de deployment")
    parser.add_argument("--method", "-m",
                       choices=["local", "docker", "cloud"],
                       default="local", 
                       help="Método de deployment")
    parser.add_argument("--cloud-platform", "-p",
                       choices=["ibm", "aws", "gcp"],
                       default="ibm",
                       help="Plataforma cloud (solo para --method cloud)")
    parser.add_argument("--validate-only", "-v",
                       action="store_true",
                       help="Solo validar entorno sin desplegar")
    
    args = parser.parse_args()
    
    print("🚀 DECODE-EV RAG Deployment Tool")
    print("=" * 50)
    
    # Inicializar deployment manager
    deployer = DecodeEVDeployment(args.environment)
    
    # Validar entorno
    if not deployer.validate_environment():
        print("❌ Validación fallida. Corregir errores antes de continuar.")
        sys.exit(1)
    
    if args.validate_only:
        print("✅ Validación completada exitosamente")
        sys.exit(0)
    
    # Crear paquete de deployment
    deploy_dir = deployer.create_deployment_package()
    
    # Ejecutar deployment según método
    success = False
    
    if args.method == "local":
        success = deployer.deploy_local(deploy_dir)
    elif args.method == "docker":
        success = deployer.deploy_docker(deploy_dir)
    elif args.method == "cloud":
        success = deployer.deploy_cloud(deploy_dir, args.cloud_platform)
    
    # Generar reporte
    deployer.generate_deployment_report(deploy_dir, success)
    
    if success:
        print("✅ Deployment completado exitosamente")
        sys.exit(0)
    else:
        print("❌ Deployment falló")
        sys.exit(1)

if __name__ == "__main__":
    main()