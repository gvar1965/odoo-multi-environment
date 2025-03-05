#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo para configuración y gestión de logs
"""

import logging
import os

def setup_logger(name, log_file, debug_mode=False):
    """Configura un logger con un nombre y archivo específicos"""
    # Crear directorio para logs si no existe
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Crear y configurar logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)
    
    # Evitar duplicación de handlers
    if logger.handlers:
        return logger
    
    # Crear handler para archivo
    file_handler = logging.FileHandler(log_file)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

def get_logger(name):
    """Obtiene un logger previamente configurado"""
    return logging.getLogger(name)
