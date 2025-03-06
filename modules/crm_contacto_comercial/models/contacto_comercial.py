from odoo import models, fields, api
from odoo.exceptions import UserError

class ContactoComercial(models.Model):
    _name = 'crm.contacto.comercial'
    _description = 'Contacto Comercial'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char('Referencia', required=True, copy=False, default='Nuevo')
    partner_id = fields.Many2one('res.partner', string='Empresa', required=True, tracking=True)
    contact_partner_ids = fields.Many2many(
        'res.partner', 'contacto_comercial_contact_rel', 'contacto_id', 'partner_id', 
        string='Contactos de la empresa',
        domain="[('parent_id', '=', partner_id), ('type', '=', 'contact')]"
    )
    date = fields.Datetime('Fecha y Hora', required=True, default=fields.Datetime.now)
    duration = fields.Float('Duración (horas)', default=1.0)
    tipo = fields.Selection([
        ('visita', 'Visita'),
        ('presentacion', 'Presentación'),
        ('llamada', 'Llamada telefónica'),
        ('seminario', 'Seminario/Webinar'),
        ('exposicion', 'Visita a exposición'),
        ('otro', 'Otro'),
    ], string='Tipo de Contacto', required=True)
    
    user_id = fields.Many2one('res.users', string='Vendedor', default=lambda self: self.env.user, tracking=True)
    participantes_cliente = fields.Text('Participantes del Cliente')
    participantes_internos = fields.Many2many('res.users', string='Equipo Comercial')
    
    # Nuevos campos para registro de intereses
    area_interes = fields.Selection([
        ('producto', 'Interés en producto existente'),
        ('solucion', 'Interés en solución personalizada'),
        ('nuevo_producto', 'Solicitud de producto no existente'),
        ('informacion', 'Solicitud de información'),
        ('otro', 'Otro'),
    ], string='Área de Interés')
    
    producto_solicitado = fields.Char('Producto/Solución solicitada', help='Describir qué producto o solución solicitó el cliente que no tenemos en cartera')
    
    description = fields.Html('Descripción', help='Detalles del contacto comercial')
    resultado = fields.Html('Resultado y próximos pasos')
    
    lead_ids = fields.One2many('crm.lead', 'contacto_comercial_id', string='Oportunidades generadas')
    lead_count = fields.Integer(compute='_compute_lead_count', string='Nº de Oportunidades')
    
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmado'),
        ('done', 'Realizado'),
        ('cancelled', 'Cancelado'),
    ], string='Estado', default='draft', tracking=True)
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'Nuevo') == 'Nuevo':
            vals['name'] = self.env['ir.sequence'].next_by_code('crm.contacto.comercial') or 'Nuevo'
        return super(ContactoComercial, self).create(vals)
    
    def _compute_lead_count(self):
        for record in self:
            record.lead_count = len(record.lead_ids)
    
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        # Limpiar contactos cuando cambia la empresa
        self.contact_partner_ids = False
    
    def action_view_leads(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Oportunidades',
            'res_model': 'crm.lead',
            'view_mode': 'kanban,tree,form',
            'domain': [('contacto_comercial_id', '=', self.id)],
            'context': {'default_contacto_comercial_id': self.id, 'default_partner_id': self.partner_id.id}
        }
    
    def action_create_lead(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Crear Oportunidad',
            'res_model': 'crm.lead',
            'view_mode': 'form',
            'context': {
                'default_contacto_comercial_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_type': 'opportunity',
                'default_name': f'Oportunidad - {self.name}',
                'default_description': self.description,
                'default_user_id': self.user_id.id,
                'default_contact_name': self.contact_partner_ids[0].name if self.contact_partner_ids else '',
                'default_title': self.contact_partner_ids[0].function if self.contact_partner_ids else '',
                'default_mobile': self.contact_partner_ids[0].mobile if self.contact_partner_ids else '',
                'default_email_from': self.contact_partner_ids[0].email if self.contact_partner_ids else '',
                'default_is_producto_solicitado': True if self.area_interes == 'nuevo_producto' else False,
                'default_producto_solicitado': self.producto_solicitado or '',
            }
        }

