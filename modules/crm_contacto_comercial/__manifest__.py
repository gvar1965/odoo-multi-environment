{
    'name': 'CRM Contacto Comercial',
    'version': '16.0.1.0',
    'category': 'Sales/CRM',
    'summary': 'Gestión avanzada de contactos comerciales y leads',
    'description': '''
        Este módulo extiende la funcionalidad CRM de Odoo para permitir
        un seguimiento más detallado de las interacciones con clientes.
        
        Características:
        - Registro de diferentes tipos de interacciones con clientes
        - Seguimiento de visitas, llamadas, presentaciones, etc.
        - Vinculación con oportunidades de venta
    ''',
    'author': 'Equipo de Desarrollo',
    'depends': ['crm', 'sale', 'mail', 'sales_team'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/contacto_comercial_view.xml',
        'views/crm_lead_view.xml',
        'views/crm_lead_productos_solicitados_view.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}