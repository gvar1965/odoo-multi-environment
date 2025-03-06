#!/usr/bin/env python3
"""
Script directo para instalar Odoo en múltiples entornos
Este script instalará Odoo en cuatro entornos: Production, UAT, Testing y Training
"""

import os
import sys
import subprocess
import time
import logging
import argparse
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("odoo_install.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("odoo-installer")

# Configuración de entornos
ENVIRONMENTS = {
    "production": {
        "prefix": "prod_",
        "port": 8069,
        "domain": "production.example.com",
        "memory_limit": "4G"
    },
    "uat": {
        "prefix": "uat_",
        "port": 8070,
        "domain": "uat.example.com",
        "memory_limit": "2G"
    },
    "testing": {
        "prefix": "test_",
        "port": 8071,
        "domain": "testing.example.com",
        "memory_limit": "2G"
    },
    "training": {
        "prefix": "train_",
        "port": 8072,
        "domain": "training.example.com",
        "memory_limit": "2G"
    }
}

def run_command(cmd, check=True):
    """Ejecuta un comando y registra el resultado"""
    logger.info(f"Ejecutando: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
        if result.stdout:
            logger.info(f"Salida: {result.stdout.strip()}")
        if result.stderr:
            logger.warning(f"Error: {result.stderr.strip()}")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Error ejecutando comando: {e}")
        if not check:
            return ""
        raise

def install_dependencies():
    """Instala dependencias necesarias"""
    logger.info("Instalando dependencias del sistema...")
    
    dependencies = [
        "git", "python3-dev", "python3-pip", "python3-wheel", "python3-venv",
        "build-essential", "postgresql", "postgresql-client", "postgresql-server-dev-all",
        "nginx", "wkhtmltopdf", "xvfb", "libxml2-dev", "libxslt1-dev", 
        "libjpeg-dev", "libldap2-dev", "libsasl2-dev", "libpq-dev", "node-less"
    ]
    
    run_command(f"sudo apt update")
    run_command(f"sudo apt install -y {' '.join(dependencies)}")
    
    return True

def setup_environment(env_name):
    """Configura un entorno específico de Odoo"""
    logger.info(f"Configurando entorno: {env_name}")
    
    env_config = ENVIRONMENTS[env_name]
    prefix = env_config["prefix"]
    port = env_config["port"]
    domain = env_config["domain"]
    
    # 1. Crear usuario del sistema
    odoo_user = f"{prefix}odoo"
    odoo_home = f"/opt/{prefix}odoo"
    
    # Verificar si el usuario ya existe
    user_exists = run_command(f"id -u {odoo_user} > /dev/null 2>&1 || echo 'no'", check=False)
    if user_exists == "no":
        run_command(f"sudo useradd -m -d {odoo_home} -U -r -s /bin/bash {odoo_user}")
        logger.info(f"Usuario {odoo_user} creado correctamente")
    else:
        logger.info(f"Usuario {odoo_user} ya existe")
    
    # 2. Crear directorios
    odoo_log_dir = f"/var/log/{prefix}odoo"
    odoo_config_dir = f"/etc/{prefix}odoo"
    odoo_addons_dir = f"{odoo_home}/addons"
    
    for directory in [odoo_log_dir, odoo_config_dir, odoo_addons_dir]:
        run_command(f"sudo mkdir -p {directory}")
    
    # 3. Clonar Odoo
    odoo_version = "16.0"
    if not os.path.exists(f"{odoo_home}/odoo"):
        run_command(f"sudo git clone -b {odoo_version} --depth 1 https://github.com/odoo/odoo.git {odoo_home}/odoo")
    
    # 4. Crear entorno virtual Python
    venv_dir = f"{odoo_home}/venv"
    if not os.path.exists(venv_dir):
        run_command(f"sudo python3 -m venv {venv_dir}")
        run_command(f"sudo {venv_dir}/bin/pip install --upgrade pip")
        run_command(f"sudo {venv_dir}/bin/pip install -r {odoo_home}/odoo/requirements.txt")
        run_command(f"sudo {venv_dir}/bin/pip install psycopg2-binary")
    
    # 5. Configurar PostgreSQL
    db_user = f"{prefix}odoo"
    db_password = f"odoo_{env_name}_pass"  # En producción usar una contraseña segura
    db_name = f"{prefix}odoo"
    
    # Verificar si el usuario de PostgreSQL ya existe
    pg_user_exists = run_command(f"sudo -u postgres psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname='{db_user}'\" | grep -q 1 || echo 'no'", check=False)
    if pg_user_exists == "no":
        run_command(f"sudo -u postgres createuser -s {db_user}")
        run_command(f"sudo -u postgres psql -c \"ALTER USER {db_user} WITH PASSWORD '{db_password}'\"")
        logger.info(f"Usuario PostgreSQL {db_user} creado correctamente")
    else:
        logger.info(f"Usuario PostgreSQL {db_user} ya existe")
    
    # Crear base de datos
    db_exists = run_command(f"sudo -u postgres psql -lqt | cut -d \\| -f 1 | grep -qw {db_name} || echo 'no'", check=False)
    if db_exists == "no":
        run_command(f"sudo -u postgres createdb --owner={db_user} {db_name}")
        logger.info(f"Base de datos {db_name} creada correctamente")
    else:
        logger.info(f"Base de datos {db_name} ya existe")
    
    # 6. Crear archivo de configuración
    config_file = f"{odoo_config_dir}/odoo.conf"
    if not os.path.exists(config_file):
        config_content = f"""[options]
; This is the password that allows database operations:
admin_passwd = admin_secure_password
db_host = localhost
db_port = 5432
db_user = {db_user}
db_password = {db_password}
dbfilter = {db_name}
addons_path = {odoo_home}/odoo/addons,{odoo_addons_dir}
logfile = {odoo_log_dir}/odoo-server.log
log_level = info
proxy_mode = True
http_port = {port}
longpolling_port = {port + 1000}
workers = 2
limit_memory_hard = 2684354560
limit_memory_soft = 2147483648
limit_time_cpu = 600
limit_time_real = 1200
max_cron_threads = 1
"""
        
        with open("temp_config.conf", "w") as f:
            f.write(config_content)
        
        run_command(f"sudo mv temp_config.conf {config_file}")
        run_command(f"sudo chown {odoo_user}:{odoo_user} {config_file}")
        run_command(f"sudo chmod 640 {config_file}")
        logger.info(f"Archivo de configuración {config_file} creado correctamente")
    else:
        logger.info(f"Archivo de configuración {config_file} ya existe")
    
    # 7. Crear servicio systemd
    service_file = f"/etc/systemd/system/{prefix}odoo.service"
    if not os.path.exists(service_file):
        service_content = f"""[Unit]
Description=Odoo {env_name.capitalize()} Server
Requires=postgresql.service
After=network.target postgresql.service

[Service]
Type=simple
SyslogIdentifier={prefix}odoo
PermissionsStartOnly=true
User={odoo_user}
Group={odoo_user}
ExecStart={venv_dir}/bin/python3 {odoo_home}/odoo/odoo-bin -c {config_file}
StandardOutput=journal+console
RestartSec=5
Restart=always

[Install]
WantedBy=multi-user.target
"""
        
        with open("temp_service.service", "w") as f:
            f.write(service_content)
        
        run_command(f"sudo mv temp_service.service {service_file}")
        run_command(f"sudo chmod 644 {service_file}")
        run_command(f"sudo systemctl daemon-reload")
        run_command(f"sudo systemctl enable {prefix}odoo.service")
        logger.info(f"Servicio {prefix}odoo creado correctamente")
    else:
        logger.info(f"Servicio {prefix}odoo ya existe")
    
    # 8. Configurar Nginx
    nginx_conf = f"/etc/nginx/sites-available/{prefix}odoo"
    if not os.path.exists(nginx_conf):
        nginx_content = f"""upstream {prefix}odoo {{
    server 127.0.0.1:{port};
}}

upstream {prefix}odoo-chat {{
    server 127.0.0.1:{port + 1000};
}}

server {{
    listen 80;
    server_name {domain};

    # Add Headers for odoo proxy mode
    proxy_set_header X-Forwarded-Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Real-IP $remote_addr;

    # Log
    access_log /var/log/nginx/{prefix}odoo-access.log;
    error_log /var/log/nginx/{prefix}odoo-error.log;

    # Redirect longpoll requests to odoo longpolling port
    location /longpolling {{
        proxy_pass http://{prefix}odoo-chat;
    }}

    # Redirect requests to odoo backend server
    location / {{
        proxy_redirect off;
        proxy_pass http://{prefix}odoo;
    }}

    # Cache static files
    location ~* /web/static/ {{
        proxy_cache_valid 200 90m;
        proxy_buffering on;
        expires 864000;
        proxy_pass http://{prefix}odoo;
    }}

    # Gzip
    gzip_types text/css text/less text/plain text/xml application/xml application/json application/javascript;
    gzip on;
}}
"""
        
        with open("temp_nginx.conf", "w") as f:
            f.write(nginx_content)
        
        run_command(f"sudo mv temp_nginx.conf {nginx_conf}")
        run_command(f"sudo ln -sf {nginx_conf} /etc/nginx/sites-enabled/")
        logger.info(f"Configuración Nginx para {prefix}odoo creada correctamente")
    else:
        logger.info(f"Configuración Nginx para {prefix}odoo ya existe")
    
    # 9. Configurar permisos de directorios
    run_command(f"sudo chown -R {odoo_user}:{odoo_user} {odoo_home}")
    run_command(f"sudo chown -R {odoo_user}:{odoo_user} {odoo_log_dir}")
    
    # 10. Instalar módulo CRM personalizado
    # Crear directorio para el módulo
    module_dir = f"{odoo_addons_dir}/crm_contacto_comercial"
    if not os.path.exists(module_dir):
        run_command(f"sudo mkdir -p {module_dir}")
        
        # Crear __init__.py
        with open("temp_init.py", "w") as f:
            f.write("""from . import models
""")
        run_command(f"sudo mv temp_init.py {module_dir}/__init__.py")
        
        # Crear __manifest__.py
        with open("temp_manifest.py", "w") as f:
            f.write("""{
    'name': 'CRM Contacto Comercial',
    'version': '1.0',
    'summary': 'Gestión avanzada de leads',
    'description': 'Módulo personalizado para la gestión avanzada de leads y contactos comerciales',
    'category': 'CRM',
    'author': 'Tu Empresa',
    'website': 'https://www.tuempresa.com',
    'depends': ['crm', 'mail'],
    'data': [
        'views/crm_lead_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
""")
        run_command(f"sudo mv temp_manifest.py {module_dir}/__manifest__.py")
        
        # Crear directorio models
        run_command(f"sudo mkdir -p {module_dir}/models")
        
        # Crear models/__init__.py
        with open("temp_models_init.py", "w") as f:
            f.write("""from . import crm_lead
""")
        run_command(f"sudo mv temp_models_init.py {module_dir}/models/__init__.py")
        
        # Crear models/crm_lead.py
        with open("temp_crm_lead.py", "w") as f:
            f.write("""from odoo import api, fields, models

class CrmLead(models.Model):
    _inherit = 'crm.lead'
    
    # Campos adicionales para gestión avanzada
    sector_id = fields.Many2one('res.partner.industry', string='Sector')
    potential_revenue = fields.Monetary(string='Ingresos Potenciales', currency_field='company_currency')
    decision_maker = fields.Char(string='Tomador de Decisión')
    decision_maker_position = fields.Char(string='Cargo del Tomador de Decisión')
    decision_maker_email = fields.Char(string='Email del Tomador de Decisión')
    decision_maker_phone = fields.Char(string='Teléfono del Tomador de Decisión')
    
    # Campos para seguimiento de interacciones
    last_interaction_date = fields.Date(string='Fecha de Última Interacción')
    last_interaction_type = fields.Selection([
        ('call', 'Llamada'),
        ('meeting', 'Reunión'),
        ('email', 'Email'),
        ('other', 'Otro')
    ], string='Tipo de Última Interacción')
    
    # Campos para análisis de oportunidad
    competitor_ids = fields.Many2many('res.partner', string='Competidores')
    winning_factor = fields.Text(string='Factores para Ganar')
    risk_factor = fields.Text(string='Factores de Riesgo')
""")
        run_command(f"sudo mv temp_crm_lead.py {module_dir}/models/crm_lead.py")
        
        # Crear directorio views
        run_command(f"sudo mkdir -p {module_dir}/views")
        
        # Crear views/crm_lead_views.xml
        with open("temp_crm_lead_views.xml", "w") as f:
            f.write("""<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Extiende la vista de formulario de oportunidades -->
    <record id="crm_case_form_view_oppor_extended" model="ir.ui.view">
        <field name="name">crm.lead.form.opportunity.extended</field>
        <field name="model">crm.lead</field>
        <field name="inherit_id" ref="crm.crm_case_form_view_oppor"/>
        <field name="arch" type="xml">
            <xpath expr="//notebook" position="inside">
                <page string="Información Comercial Avanzada">
                    <group>
                        <group string="Información de Contacto Principal">
                            <field name="decision_maker"/>
                            <field name="decision_maker_position"/>
                            <field name="decision_maker_email" widget="email"/>
                            <field name="decision_maker_phone" widget="phone"/>
                        </group>
                        <group string="Detalles de Negocio">
                            <field name="sector_id"/>
                            <field name="potential_revenue"/>
                            <field name="competitor_ids" widget="many2many_tags"/>
                        </group>
                    </group>
                    <group string="Análisis de Oportunidad">
                        <field name="winning_factor" placeholder="Factores que nos ayudarán a ganar esta oportunidad..."/>
                        <field name="risk_factor" placeholder="Posibles riesgos o obstáculos..."/>
                    </group>
                    <group string="Seguimiento de Interacciones">
                        <field name="last_interaction_date"/>
                        <field name="last_interaction_type"/>
                    </group>
                </page>
            </xpath>
        </field>
    </record>
</odoo>
""")
        run_command(f"sudo mv temp_crm_lead_views.xml {module_dir}/views/crm_lead_views.xml")
        
        # Configurar permisos
        run_command(f"sudo chown -R {odoo_user}:{odoo_user} {module_dir}")
        logger.info(f"Módulo CRM Contacto Comercial instalado correctamente en {module_dir}")
    else:
        logger.info(f"Módulo CRM Contacto Comercial ya existe en {module_dir}")
    
    # 11. Iniciar servicio
    run_command(f"sudo systemctl start {prefix}odoo.service")
    
    # 12. Verificar estado del servicio
    status = run_command(f"sudo systemctl is-active {prefix}odoo.service", check=False)
    if status == "active":
        logger.info(f"Servicio {prefix}odoo está activo")
    else:
        logger.warning(f"Servicio {prefix}odoo no está activo")
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Instalador de Odoo en múltiples entornos')
    parser.add_argument('--environments', '-e', nargs='+', choices=ENVIRONMENTS.keys(),
                        default=ENVIRONMENTS.keys(), help='Entornos a instalar')
    parser.add_argument('--debug', '-d', action='store_true', help='Habilitar modo debug')
    
    args = parser.parse_args()
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    logger.info("Iniciando instalación de Odoo en múltiples entornos")
    
    try:
        # Instalar dependencias
        install_dependencies()
        
        # Recargar servicio Nginx
        run_command("sudo systemctl reload nginx")
        
        # Configurar cada entorno seleccionado
        for env_name in args.environments:
            setup_environment(env_name)
        
        logger.info("¡Instalación completada exitosamente!")
        logger.info("Puedes acceder a los entornos en los siguientes puertos:")
        for env_name in args.environments:
            port = ENVIRONMENTS[env_name]["port"]
            logger.info(f"  - {env_name.capitalize()}: http://localhost:{port}")
        
        return 0
    except Exception as e:
        logger.error(f"Error durante la instalación: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
