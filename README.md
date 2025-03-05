# Instalador Multi-Entorno para Odoo

Este proyecto proporciona un conjunto de scripts para la instalación y configuración de múltiples entornos de Odoo (Producción, UAT, Testing y Capacitación), con funcionalidades avanzadas de CRM y conectividad BI.

## Características

- **Instalación Multi-Entorno**: Configuración de hasta 4 entornos separados
- **Gestión de Contactos Comerciales**: Módulo personalizado para el seguimiento de interacciones con clientes
- **Dashboards y BI**: Integración con Tableau y Power BI para análisis avanzado
- **Logs Detallados**: Sistema de logging avanzado para facilitar debugging
- **Instalación Flexible**: Soporte para instalación local o remota vía SSH

## Requisitos Previos

- Ubuntu 22.04 LTS o Ubuntu 24.04 LTS
- Python 3.10+ 
- Acceso root o sudo
- Conexión a Internet

## Uso

```bash
# Instalar dependencias de Python
pip install -r requirements.txt

# Ejecutar instalación completa (todos los entornos)
sudo python install.py

# O instalar entornos específicos
sudo python install.py --environments production uat
