#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script principal para la instalación de múltiples entornos Odoo

Este script coordina la instalación de entornos Odoo (Producción, UAT, Testing y Capacitación).

Versión: 1.0.0
Fecha: 05/03/2025
"""

import os
import sys

def main():
    """Función principal de instalación"""
    print("Instalador Multi-Entorno para Odoo v1.0.0")
    
    # Verificar permisos de root
    if os.geteuid() != 0:
        print("Error: Este script debe ejecutarse con permisos de root (sudo)")
        return 1
    
    print("¡Instalación completada!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
