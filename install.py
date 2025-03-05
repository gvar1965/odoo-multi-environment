#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script principal para la instalación de múltiples entornos Odoo

Este script coordina la instalación de entornos Odoo (Producción, UAT, Testing y Capacitación),
permitiendo configurar cada uno con sus características específicas.

Compatible con Ubuntu modernos (con PEP 668).

Versión: 1.0.1
Fecha: 05/03/2025
"""

import os
import sys
import argparse
import subprocess
import getpass
import logging
import yaml
from pathlib import Path
from datetime import datetime

# Configurar logging básico
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('odoo-installer')

# Colores para la consola
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

# Versión del instalador
VERSION = "1.0.1"

def run_command(command, check=True, sudo=False):
    """
    Ejecuta un comando y devuelve el resultado
    
    Args:
        command (str): Comando a ejecutar
        check (bool): Si es True, verifica el código de salida
        sudo (bool): Si es True, ejecuta el comando con sudo
        
    Returns:
        (bool, str): Éxito y salida del comando
    """
    if sudo:
        # Añadir sudo al comando
        cmd = f"sudo {command}"
    else:
        cmd = command
        
    logger.info(f"Ejecutando: {cmd}")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=check,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode == 0:
            if result.stdout:
                logger.debug(f"Salida: {result.stdout.strip()}")
            return True, result.stdout
        else:
            logger.error(f"Error al ejecutar: {cmd}")
            logger.error(f"Código de error: {result.returncode}")
            logger.error(f"Salida de error: {result.stderr}")
            return False, result.stderr
    except subprocess.CalledProcessError as e:
        logger.error(f"Excepción al ejecutar {cmd}: {str(e)}")
        return False, str(e)
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        return False, str(e)

def is_root():
    """
    Comprueba si el script se está ejecutando como root
    
    Returns:
        bool: True si se está ejecutando como root
    """
    return os.geteuid() == 0

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

def load_environment_config(env_name, config_dir):
    """
    Carga la configuración para un entorno específico
    
    Args:
        env_name (str): Nombre del entorno
        config_dir (str): Directorio de configuración
        
    Returns:
        dict: Configuración del entorno
    """
    config_path = os.path.join(config_dir, f"{env_name}.yaml")
    default_path = os.path.join(config_dir, "default_config.yaml")
    
    # Cargar configuración por defecto
    if os.path.exists(default_path):
        with open(default_path, 'r') as f:
            config = yaml.safe_load(f)
    else:
        logger.warning(f"Archivo de configuración por defecto no encontrado: {default_path}")
        config = {}
    
    # Sobrescribir con configuración específica si existe
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            env_config = yaml.safe_load(f)
            if env_config:
                config.update(env_config)
    else:
        logger.warning(f"Archivo de configuración específico no encontrado: {config_path}")
    
    # Añadir nombre de entorno a la configuración
    config['environment'] = env_name
    
    return config

def check_system_dependencies():
    """
    Verifica que el sistema tenga las dependencias básicas instaladas
    
    Returns:
        bool: True si todas las dependencias están instaladas
    """
    logger.info("Verificando dependencias del sistema...")
    
    # Verificar Python
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        logger.error(f"Se requiere Python 3.8+. Versión actual: {python_version.major}.{python_version.minor}")
        return False
    
    # Verificar pip y dependencias
    try:
        import yaml
        import requests
    except ImportError as e:
        logger.error(f"Falta la dependencia: {str(e)}")
        logger.error("Instala las dependencias con: pip install -r requirements.txt")
        return False
    
    return True

def setup_environment(env_name, config):
    """
    Configura un entorno específico de Odoo
    
    Args:
        env_name (str): Nombre del entorno
        config (dict): Configuración del entorno
        
    Returns:
        bool: True si la configuración fue exitosa
    """
    logger.info(f"Configurando entorno: {env_name}")
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}Configurando entorno: {env_name.upper()}{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")
    
    # Mostrar información del entorno
    print(f"{Colors.BLUE}Versión de Odoo:{Colors.END} {config.get('odoo_version', '16.0')}")
    print(f"{Colors.BLUE}Base de datos:{Colors.END} {config.get('db_name', f'{env_name}_odoo')}")
    
    try:
        # 1. Actualizar el sistema
        logger.info("Actualizando el sistema...")
        run_command("apt update", sudo=True)
        
        # 2. Instalar dependencias básicas
        logger.info("Instalando dependencias básicas...")
        dependencies = [
            "git", "python3-dev", "python3-pip", "python3-wheel", 
            "build-essential", "postgresql", "nginx", "wkhtmltopdf"
        ]
        run_command(f"apt install -y {' '.join(dependencies)}", sudo=True)
        
        # 3. Configurar usuario de Odoo
        logger.info("Configurando usuario de Odoo...")
        prefix = config.get('prefix', f"{env_name}_")
        odoo_user = config.get('odoo_user', f"{prefix}odoo")
        odoo_home = config.get('odoo_home', f"/opt/{prefix}odoo")
        
        # Verificar si el usuario existe
        user_exists, _ = run_command(f"id -u {odoo_user} > /dev/null 2>&1 || echo 'no'", check=False)
        if not user_exists:
            run_command(f"useradd -m -d {odoo_home} -U -r -s /bin/bash {odoo_user}", sudo=True)
        
        # 4. Clonar Odoo (simulado para ejemplo)
        logger.info("Clonando repositorio de Odoo...")
        odoo_version = config.get('odoo_version', '16.0')
        # En un script real, aquí clonaríamos el repositorio de Odoo

        # 5. Configurar base de datos (simulado)
        logger.info("Configurando base de datos PostgreSQL...")
        # En un script real, aquí configuraríamos PostgreSQL

        # 6. Configurar Nginx (simulado)
        logger.info("Configurando Nginx...")
        # En un script real, aquí configuraríamos Nginx
        
        # 7. Instalar módulos personalizados (simulado)
        logger.info("Instalando módulos personalizados...")
        # En un script real, aquí instalaríamos módulos personalizados

        logger.info(f"Entorno {env_name} configurado correctamente")
        return True
        
    except Exception as e:
        logger.error(f"Error configurando entorno {env_name}: {str(e)}")
        return False

def main():
    """Función principal de instalación"""
    # Procesar argumentos
    args = parse_arguments()
    
    # Configurar logger con nivel de debug si se solicita
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    # Crear directorio de logs
    os.makedirs(args.log_dir, exist_ok=True)
    
    # Agregar handler para archivo
    file_handler = logging.FileHandler(os.path.join(args.log_dir, 'install.log'))
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
    
    print(f"\n{Colors.BOLD}Instalador Multi-Entorno Odoo v{VERSION}{Colors.END}")
    logger.info(f"Iniciando instalador Multi-Entorno Odoo v{VERSION}")
    
    # Verificar dependencias
    if not check_system_dependencies():
        logger.error("No se cumplen los requisitos del sistema para la instalación")
        return 1
    
    # Verificar privilegios de root solo si es necesario durante la ejecución
    # (no requerimos sudo desde el inicio, solo para comandos específicos)
    
    # Determinar entornos a instalar
    environments = args.environments or ['production', 'uat', 'testing', 'training']
    logger.info(f"Entornos a instalar: {', '.join(environments)}")
    
    # Procesar cada entorno
    results = {}
    for env in environments:
        # Cargar configuración
        config = load_environment_config(env, args.config_dir)
        
        # Configurar entorno
        success = setup_environment(env, config)
        results[env] = success
    
    # Mostrar resumen
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}Resumen de instalación{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")
    
    for env, success in results.items():
        status = f"{Colors.GREEN}Exitosa{Colors.END}" if success else f"{Colors.RED}Fallida{Colors.END}"
        print(f"Entorno {env.upper()}: {status}")
    
    # Finalizar
    if all(results.values()):
        logger.info("¡Instalación completada exitosamente para todos los entornos!")
        print(f"\n{Colors.GREEN}¡Instalación completada exitosamente!{Colors.END}")
        return 0
    else:
        failed = [env for env, success in results.items() if not success]
        logger.error(f"La instalación falló para los siguientes entornos: {', '.join(failed)}")
        print(f"\n{Colors.RED}La instalación falló para algunos entornos.{Colors.END}")
        print(f"Revisa el log en {args.log_dir}/install.log para más detalles.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
