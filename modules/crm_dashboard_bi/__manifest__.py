{
    'name': 'CRM Dashboard y Conectividad BI',
    'version': '16.0.1.0',
    'category': 'Sales/CRM',
    'summary': 'Dashboards y conectividad con herramientas BI',
    'description': '''
        Este módulo proporciona dashboards avanzados y conectividad
        con herramientas de Business Intelligence como Power BI y Tableau.
    ''',
    'author': 'Equipo de Desarrollo',
    'depends': ['crm', 'sale', 'web', 'crm_contacto_comercial'],
    'data': [
        'security/ir.model.access.csv',
        'views/dashboard_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
