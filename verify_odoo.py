#!/usr/bin/env python3
"""
Script para verificar la instalación de Odoo en múltiples entornos
"""

import os
import sys
import subprocess
import time
import argparse
from tabulate import tabulate

def run_command(cmd, check=True):
    """Ejecuta un comando y devuelve su salida"""
    print(f"Ejecutando: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        if not check:
            return ""
        print(f"Error al ejecutar el comando: {e}")
        return ""

def check_service(service_name):
    """Verifica si un servicio está activo"""
    status = run_command(f"systemctl is-active {service_name} || echo 'inactive'", check=False)
    return status == "active"

def check_port(port):
    """Verifica si un puerto está en uso"""
    result = run_command(f"ss -tulpn | grep ':{port}' || echo 'no'", check=False)
    return result != "no", result

def check_user(username):
    """Verifica si un usuario existe"""
    result = run_command(f"id {username} 2>/dev/null || echo 'no'", check=False)
    return result != "no"

def check_database(db_name):
    """Verifica si una base de datos existe"""
    result = run_command(f"sudo -u postgres psql -lqt | cut -d \\| -f 1 | grep -qw {db_name} && echo 'yes' || echo 'no'", check=False)
    return result == "yes"

def main():
    # Definir prefijos y puertos para cada entorno
    environments = {
        "production": {"prefix": "prod_", "port": 8069},
        "uat": {"prefix": "uat_", "port": 8070},
        "testing": {"prefix": "test_", "port": 8071},
        "training": {"prefix": "train_", "port": 8072}
    }
    
    parser = argparse.ArgumentParser(description='Verificador de instalación de Odoo')
    parser.add_argument('--environments', '-e', nargs='+', choices=environments.keys(),
                     default=environments.keys(), help='Entornos a verificar')
    
    args = parser.parse_args()
    
    print("===== Verificando instalación de Odoo =====\n")
    
    # Tabla para resultados
    results = []
    
    # Verificar cada entorno
    for env_name in args.environments:
        env_data = environments[env_name]
        prefix = env_data["prefix"]
        port = env_data["port"]
        
        # Verificar servicio
        service_name = f"{prefix}odoo.service"
        service_ok = check_service(service_name)
        
        # Verificar puerto
        port_ok, port_info = check_port(port)
        
        # Verificar usuario
        user_name = f"{prefix}odoo"
        user_ok = check_user(user_name)
        
        # Verificar base de datos
        db_name = f"{prefix}odoo"
        db_ok = check_database(db_name)
        
        # Verificar configuración
        config_file = f"/etc/{prefix}odoo/odoo.conf"
        config_ok = os.path.exists(config_file)
        
        # Verificar nginx
        nginx_file = f"/etc/nginx/sites-enabled/{prefix}odoo"
        nginx_ok = os.path.exists(nginx_file)
        
        # Calcular estado general
        status = "✅ OK" if all([service_ok, port_ok, user_ok, db_ok, config_ok, nginx_ok]) else "❌ Error"
        
        # Añadir a resultados
        results.append([
            env_name.capitalize(),
            "✅" if service_ok else "❌",
            "✅" if port_ok else "❌",
            "✅" if user_ok else "❌",
            "✅" if db_ok else "❌",
            "✅" if config_ok else "❌",
            "✅" if nginx_ok else "❌",
            status
        ])
    
    # Mostrar tabla de resultados
    headers = ["Entorno", "Servicio", "Puerto", "Usuario", "Base de datos", "Config", "Nginx", "Estado"]
    print(tabulate(results, headers=headers, tablefmt="grid"))
    
    # Mostrar instrucciones adicionales
    print("\n===== Acceso a los entornos =====")
    print("Si todos los servicios están activos, puedes acceder a Odoo a través de:")
    
    for env_name in args.environments:
        env_data = environments[env_name]
        port = env_data["port"]
        print(f"  - {env_name.capitalize()}: http://localhost:{port}")
    
    print("\nPara iniciar un servicio inactivo:")
    print("  sudo systemctl start [prefijo]odoo.service")
    print("  Ejemplo: sudo systemctl start prod_odoo.service")

if __name__ == "__main__":
    main()
