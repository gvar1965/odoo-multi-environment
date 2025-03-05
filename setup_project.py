#!/usr/bin/env python3
"""
Script para configurar automáticamente el proyecto odoo-multi-environment
Este script creará todos los archivos necesarios en las ubicaciones correctas
"""

import os
import sys

# Contenido para cada archivo
FILES = {
    'install.py': '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script principal para la instalación de múltiples entornos Odoo

Este script coordina la instalación de entornos Odoo (Producción, UAT, Testing y Capacitación),
permitiendo configurar cada uno con sus características específicas y ejecutar
la instalación en servidores locales o remotos.

Autor: Equipo de Desarrollo
Versión: 1.0.0
Fecha: 05/03/2025
"""

import os
import sys
import argparse
import yaml
from pathlib import Path

# Importar módulos propios
from lib.logger import setup_logger, get_logger
from lib.environment import Environment
from lib.installer import validate_requirements
from lib.utils import print_banner, print_summary

# Versión del instalador
VERSION = "1.0.0"

def parse_arguments():
    """Procesa los argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description=f'Instalador Multi-Entorno Odoo v{VERSION}',
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # Argumentos generales
    parser.add_argument('--environments', '-e', nargs='+', 
                     choices=['production', 'uat', 'testing', 'training'],
                     help='Entornos a instalar (por defecto: todos)')
    parser.add_argument('--remote', '-r', action='store_true',
                     help='Habilitar instalación en servidores remotos')
    parser.add_argument('--config-dir', '-c', default='./config',
                     help='Directorio con archivos de configuración YAML')
    parser.add_argument('--log-dir', '-l', default='./logs',
                     help='Directorio para archivos de log')
    parser.add_argument('--debug', '-d', action='store_true',
                     help='Habilitar modo debug (logs detallados)')
    parser.add_argument('--version', '-v', action='store_true',
                     help='Muestra la versión y sale')
    
    args = parser.parse_args()
    
    # Mostrar versión y salir
    if args.version:
        print(f"Instalador Multi-Entorno Odoo v{VERSION}")
        sys.exit(0)
        
    return args

def load_configuration(args):
    """Carga la configuración desde archivos YAML"""
    config_path = Path(args.config_dir)
    environments = args.environments or ['production', 'uat', 'testing', 'training']
    
    # Verificar que exista el directorio de configuración
    if not config_path.exists():
        print(f"Error: Directorio de configuración no encontrado: {config_path}")
        sys.exit(1)
    
    # Cargar configuración por defecto
    default_config_file = config_path / 'default_config.yaml'
    if not default_config_file.exists():
        print(f"Error: Archivo de configuración por defecto no encontrado: {default_config_file}")
        sys.exit(1)
    
    with open(default_config_file, 'r') as f:
        default_config = yaml.safe_load(f)
    
    # Cargar configuración específica para cada entorno
    configs = {}
    for env in environments:
        env_config_file = config_path / f'{env}.yaml'
        
        # Si no existe config específica, usar default con valores básicos
        if not env_config_file.exists():
            logger.warning(f"Archivo de configuración no encontrado para {env}, usando valores por defecto")
            configs[env] = default_config.copy()
            configs[env]['environment'] = env
            continue
            
        # Cargar y combinar con default
        with open(env_config_file, 'r') as f:
            env_config = yaml.safe_load(f)
            
        # Combinar con configuración por defecto
        config = default_config.copy()
        config.update(env_config)
        config['environment'] = env
        configs[env] = config
    
    return configs

def setup_environments(configs, args):
    """Crea instancias de Environment para cada entorno a instalar"""
    environments = []
    
    for env_name, config in configs.items():
        # Configurar logger específico para este entorno
        env_log_file = os.path.join(args.log_dir, f"{env_name}.log")
        env_logger = setup_logger(env_name, env_log_file, args.debug)
        
        # Crear instancia de entorno
        environment = Environment(
            name=env_name,
            config=config,
            logger=env_logger,
            remote=args.remote
        )
        environments.append(environment)
    
    return environments

def main():
    """Función principal de instalación"""
    # Procesar argumentos
    args = parse_arguments()
    
    # Configurar logger principal
    os.makedirs(args.log_dir, exist_ok=True)
    setup_logger('main', os.path.join(args.log_dir, 'main.log'), args.debug)
    logger = get_logger('main')
    
    logger.info(f"Iniciando instalador Multi-Entorno Odoo v{VERSION}")
    
    # Validar requisitos del sistema
    if not validate_requirements(logger):
        logger.error("No se cumplen los requisitos del sistema para la instalación")
        sys.exit(1)
    
    # Cargar configuración
    try:
        configs = load_configuration(args)
        logger.info(f"Configuración cargada para {len(configs)} entornos: {', '.join(configs.keys())}")
    except Exception as e:
        logger.error(f"Error cargando configuración: {str(e)}")
        sys.exit(1)
    
    # Configurar entornos
    environments = setup_environments(configs, args)
    
    # Mostrar banner con información de la instalación
    print_banner(environments)
    
    # Ejecutar instalación para cada entorno
    results = {}
    for env in environments:
        logger.info(f"Iniciando instalación de entorno: {env.name}")
        try:
            success = env.install()
            results[env.name] = success
            status = "exitosa" if success else "fallida"
            logger.info(f"Instalación de {env.name} {status}")
        except Exception as e:
            logger.error(f"Error durante la instalación de {env.name}: {str(e)}", exc_info=True)
            results[env.name] = False
    
    # Mostrar resumen de la instalación
    print_summary(environments, results)
    
    # Finalizar
    if all(results.values()):
        logger.info("¡Instalación completada exitosamente para todos los entornos!")
        return 0
    else:
        failed = [env for env, success in results.items() if not success]
        logger.error(f"La instalación falló para los siguientes entornos: {', '.join(failed)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
''',

    'lib/logger.py': '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo para configuración y gestión de logs

Este módulo proporciona funciones para configurar y obtener loggers
específicos para cada componente y entorno de la instalación.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
import sys

# Diccionario global de loggers
_loggers = {}

def setup_logger(name, log_file, debug_mode=False):
    """
    Configura un logger con un nombre y archivo específicos
    
    Args:
        name (str): Nombre del logger
        log_file (str): Ruta al archivo de log
        debug_mode (bool): Si es True, configura el nivel de log a DEBUG
    
    Returns:
        logging.Logger: El logger configurado
    """
    if name in _loggers:
        return _loggers[name]
    
    # Crear directorio para logs si no existe
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Crear y configurar logger
    logger = logging.getLogger(name)
    
    # Configurar nivel de log
    level = logging.DEBUG if debug_mode else logging.INFO
    logger.setLevel(level)
    
    # Evitar duplicación de handlers
    if logger.handlers:
        return logger
    
    # Crear handler para archivo con rotación
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5
    )
    
    # Crear handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Configurar formato
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Añadir handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Guardar referencia al logger
    _loggers[name] = logger
    
    return logger

def get_logger(name):
    """
    Obtiene un logger previamente configurado
    
    Args:
        name (str): Nombre del logger
    
    Returns:
        logging.Logger: El logger si existe, o un logger básico si no existe
    """
    if name in _loggers:
        return _loggers[name]
    
    # Crear un logger básico si no existe
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Verificar si ya tiene handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def create_subprocess_logger(parent_logger):
    """
    Crea un logger adaptado para capturar la salida de subprocesos
    
    Args:
        parent_logger (logging.Logger): Logger padre
    
    Returns:
        callable: Función que recibe líneas de texto y las registra en el logger
    """
    def log_output(pipe, level=logging.INFO):
        for line in iter(pipe.readline, b''):
            line = line.decode('utf-8').rstrip()
            if line:
                parent_logger.log(level, line)
    
    return log_output
''',

    'lib/environment.py': '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo para la gestión de entornos Odoo

Este módulo define la clase Environment que encapsula toda la lógica
de instalación y configuración de un entorno específico de Odoo.
"""

import os
import sys
import tempfile
from pathlib import Path

from .database import PostgresManager
from .odoo import OdooManager
from .web import NginxManager
from .module_installer import ModuleInstaller
from .remote import RemoteExecutor

class Environment:
    """
    Clase que encapsula la configuración y gestión de un entorno de Odoo
    """
    
    def __init__(self, name, config, logger, remote=False):
        """
        Inicializa un entorno con su configuración
        
        Args:
            name (str): Nombre del entorno (production, uat, testing, training)
            config (dict): Configuración del entorno
            logger: Logger configurado para este entorno
            remote (bool): Si es True, la instalación se realizará en un servidor remoto
        """
        self.name = name
        self.config = config
        self.logger = logger
        self.remote = remote
        
        # Configurar ejecutor (local o remoto)
        if remote:
            self.executor = RemoteExecutor(
                host=self.config.get('remote_host', 'localhost'),
                port=self.config.get('remote_port', 22),
                username=self.config.get('remote_user', 'root'),
                password=self.config.get('remote_password'),
                ssh_key=self.config.get('remote_ssh_key'),
                logger=self.logger
            )
        else:
            # Si es local, usar None como ejecutor y las funciones locales tomarán el control
            self.executor = None
        
        # Asignar nombres de variables específicos del entorno si no están en config
        if 'prefix' not in self.config:
            self.config['prefix'] = self._get_default_prefix()
            
        if 'domain' not in self.config:
            self.config['domain'] = f"{self.name}.example.com"
            
        self._validate_config()
            
        self.logger.info(f"Entorno {name} inicializado con prefijo: {self.config['prefix']}")
    
    def _validate_config(self):
        """Valida que la configuración contenga todas las claves necesarias"""
        required_keys = [
            'odoo_version',
            'port', 
            'prefix'
        ]
        
        for key in required_keys:
            if key not in self.config:
                self.logger.error(f"Falta la clave de configuración '{key}' para el entorno {self.name}")
                raise ValueError(f"Configuración incompleta para el entorno {self.name}: falta '{key}'")
    
    def _get_default_prefix(self):
        """Obtiene el prefijo por defecto basado en el nombre del entorno"""
        prefixes = {
            'production': 'prod_',
            'uat': 'uat_',
            'testing': 'test_',
            'training': 'train_'
        }
        return prefixes.get(self.name, f"{self.name}_")
    
    def install(self):
        """
        Realiza la instalación completa del entorno
        
        Returns:
            bool: True si la instalación fue exitosa, False en caso contrario
        """
        try:
            self.logger.info(f"Iniciando instalación del entorno {self.name}")
            
            # 1. Preparar el sistema (dependencias, usuarios, directorios)
            self._prepare_system()
            
            # 2. Configurar base de datos
            self._setup_database()
            
            # 3. Instalar Odoo
            self._install_odoo()
            
            # 4. Instalar módulos personalizados
            self._install_custom_modules()
            
            # 5. Configurar servidor web
            self._setup_web_server()
            
            # 6. Configurar firewall
            self._setup_firewall()
            
            # 7. Iniciar servicios
            self._start_services()
            
            self.logger.info(f"Instalación del entorno {self.name} completada correctamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error durante la instalación del entorno {self.name}: {str(e)}", exc_info=True)
            return False
    
    def _prepare_system(self):
        """Prepara el sistema para la instalación"""
        self.logger.info("Preparando el sistema...")
        
        # Instalar dependencias del sistema
        dependencies = [
            "git", "python3-dev", "python3-pip", "python3-venv", "build-essential",
            "postgresql", "nginx", "nodejs", "npm", "wkhtmltopdf", "xvfb"
        ]
        
        if self.executor:
            # Ejecutar comandos en el servidor remoto
            self.executor.run_command(f"apt-get update")
            self.executor.run_command(f"apt-get install -y {' '.join(dependencies)}")
        else:
            # Ejecutar comandos localmente
            import subprocess
            subprocess.run(["apt-get", "update"], check=True)
            subprocess.run(["apt-get", "install", "-y"] + dependencies, check=True)
        
        # Crear usuario del sistema para Odoo
        odoo_user = self.config.get('odoo_user', f"{self.config['prefix']}odoo")
        odoo_home = self.config.get('odoo_home', f"/opt/{self.config['prefix']}odoo")
        
        cmd = f"id -u {odoo_user} > /dev/null 2>&1 || useradd -m -d {odoo_home} -U -r -s /bin/bash {odoo_user}"
        
        if self.executor:
            self.executor.run_command(cmd)
        else:
            import subprocess
            subprocess.run(cmd, shell=True, check=True)
            
        self.logger.info(f"Sistema preparado correctamente")
    
    def _setup_database(self):
        """Configura la base de datos PostgreSQL"""
        self.logger.info("Configurando base de datos PostgreSQL...")
        
        # Crear instancia del gestor de base de datos
        db_manager = PostgresManager(
            env_name=self.name,
            config=self.config,
            logger=self.logger,
            executor=self.executor
        )
        
        # Configurar PostgreSQL
        db_manager.setup()
        
        self.logger.info("Base de datos PostgreSQL configurada correctamente")
    
    def _install_odoo(self):
        """Instala y configura Odoo"""
        self.logger.info("Instalando Odoo...")
        
        # Crear instancia del gestor de Odoo
        odoo_manager = OdooManager(
            env_name=self.name,
            config=self.config,
            logger=self.logger,
            executor=self.executor
        )
        
        # Clonar el repositorio y configurar
        odoo_manager.clone_odoo()
        odoo_manager.create_odoo_config()
        odoo_manager.setup_service()
        
        self.logger.info("Odoo instalado y configurado correctamente")
    
    def _install_custom_modules(self):
        """Instala los módulos personalizados"""
        self.logger.info("Instalando módulos personalizados...")
        
        # Crear instancia del instalador de módulos
        module_installer = ModuleInstaller(
            env_name=self.name,
            config=self.config,
            logger=self.logger,
            executor=self.executor
        )
        
        # Instalar módulos necesarios
        module_installer.install_crm_contacto_comercial()
        module_installer.install_crm_dashboard_bi()
        
        self.logger.info("Módulos personalizados instalados correctamente")
    
    def _setup_web_server(self):
        """Configura el servidor web (Nginx)"""
        self.logger.info("Configurando servidor web Nginx...")
        
        # Crear instancia del gestor de Nginx
        nginx_manager = NginxManager(
            env_name=self.name,
            config=self.config,
            logger=self.logger,
            executor=self.executor
        )
        
        # Configurar Nginx
        nginx_manager.setup()
        
        self.logger.info("Servidor web Nginx configurado correctamente")
    
    def _setup_firewall(self):
        """Configura el firewall"""
        self.logger.info("Configurando firewall...")
        
        # Reglas básicas de firewall (UFW)
        port = self.config.get('port', 8069)
        
        commands = [
            "ufw allow 22/tcp",             # SSH
            "ufw allow 80/tcp",             # HTTP
            "ufw allow 443/tcp",            # HTTPS
            f"ufw allow {port}/tcp",        # Puerto específico de Odoo
        ]
        
        # Ejecutar comandos
        if self.executor:
            for cmd in commands:
                self.executor.run_command(cmd)
        else:
            import subprocess
            for cmd in commands:
                subprocess.run(cmd, shell=True)
        
        self.logger.info("Firewall configurado correctamente")
    
    def _start_services(self):
        """Inicia los servicios necesarios"""
        self.logger.info("Iniciando servicios...")
        
        # Servicio de Odoo
        odoo_service = f"{self.config['prefix']}odoo"
        
        commands = [
            f"systemctl enable {odoo_service}",
            f"systemctl start {odoo_service}",
            "systemctl restart nginx"
        ]
        
        # Ejecutar comandos
        if self.executor:
            for cmd in commands:
                self.executor.run_command(cmd)
        else:
            import subprocess
            for cmd in commands:
                subprocess.run(cmd, shell=True)
        
        self.logger.info("Servicios iniciados correctamente")
    
    def status(self):
        """
        Verifica el estado actual del entorno
        
        Returns:
            dict: Información sobre el estado de los servicios y componentes
        """
        self.logger.info(f"Verificando estado del entorno {self.name}")
        
        odoo_service = f"{self.config['prefix']}odoo"
        
        commands = {
            "odoo_service": f"systemctl is-active {odoo_service}",
            "nginx": "systemctl is-active nginx",
            "postgres": "systemctl is-active postgresql"
        }
        
        status = {}
        
        for service, cmd in commands.items():
            try:
                if self.executor:
                    output = self.executor.run_command(cmd, check=False)
                    status[service] = output.strip() == "active"
                else:
                    import subprocess
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    status[service] = result.stdout.strip() == "active"
            except Exception:
                status[service] = False
        
        return status
''',

    'config/default_config.yaml': '''# Configuración por defecto para todos los entornos Odoo
---
# Versión de Odoo a instalar
odoo_version: "16.0"

# Configuración de base de datos
db_host: "localhost"
db_port: 5432
create_db_user: true
db_password_auto_generate: true

# Configuración de directorios
base_path: "/opt"
logs_path: "/var/log"

# Configuración Web
install_nginx: true
use_ssl: false
use_letsencrypt: false
redirect_www: true

# Configuración del servidor
setup_firewall: true
allowed_countries: []  # Lista de países permitidos (códigos ISO), vacío = todos

# Rendimiento y recursos
workers: 0  # 0 = Automático basado en CPUs
max_cron_threads: 2
limit_memory_hard: 2684354560  # ~2.5GB
limit_memory_soft: 2147483648  # ~2GB
limit_time_cpu: 600
limit_time_real: 1200

# Módulos adicionales
install_modules:
  - crm_contacto_comercial
  - crm_dashboard_bi

# Configuración de backup
setup_backups: true
backup_frequency: "daily"  # daily, weekly, hourly
backup_retention: 7  # Días
backup_path: "/opt/odoo_backups"

# Configuración extra
install_wkhtmltopdf: true
setup_smtp: false
smtp_server: ""
smtp_port: 587
smtp_user: ""
smtp_password: ""
smtp_security: "starttls"  # none, ssl, starttls

# Admin
create_admin_user: true
admin_password_auto_generate: true
''',

    'README.md': '''# Instalador Multi-Entorno para Odoo

Este proyecto proporciona un conjunto de scripts para la instalación y configuración de múltiples entornos de Odoo (Producción, UAT, Testing y Capacitación), con funcionalidades avanzadas de CRM y conectividad BI.

## Características

- **Instalación Multi-Entorno**: Configuración de hasta 4 entornos separados (Producción, UAT, Testing, Capacitación)
- **Gestión de Contactos Comerciales**: Módulo personalizado para el seguimiento de interacciones con clientes
- **Dashboards y BI**: Integración con Tableau y Power BI para análisis avanzado
- **Logs Detallados**: Sistema de logging avanzado para facilitar debugging
- **Instalación Flexible**: Soporte para instalación local o remota vía SSH
- **Arquitectura Modular**: Código organizado para facilitar mantenimiento y extensión

## Requisitos Previos

- Ubuntu 22.04 LTS o Ubuntu 24.04 LTS
- Python 3.10+ 
- Acceso root o sudo
- Conexión a Internet

## Instalación Rápida

```bash
# Clonar el repositorio
git clone https://github.com/empresa/odoo-multi-environment.git
cd odoo-multi-environment

# Instalar dependencias de Python
pip install -r requirements.txt

# Ejecutar instalación completa (todos los entornos)
sudo python install.py

# O instalar entornos específicos
sudo python install.py --environments production uat
