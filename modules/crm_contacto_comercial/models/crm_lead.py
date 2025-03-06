from odoo import models, fields, api
from odoo.exceptions import UserError

class CrmLead(models.Model):
    _inherit = 'crm.lead'
    
    contacto_comercial_id = fields.Many2one('crm.contacto.comercial', string='Contacto Comercial Origen')
    origin_type = fields.Selection([
        ('contacto', 'Contacto Comercial'),
        ('licitacion', 'Licitación'),
        ('proveedor', 'Llamado de Proveedor'),
        ('web', 'Sitio Web'),
        ('otro', 'Otro'),
    ], string='Origen', default='otro')
    
    licitacion_ref = fields.Char('Referencia de Licitación')
    proveedor_id = fields.Many2one('res.partner', string='Proveedor')
    
    # Campos para análisis de productos no disponibles
    is_producto_solicitado = fields.Boolean('Producto/Solución no disponible', help='Marcar si el cliente solicitó un producto o solución que no tenemos en cartera')
    producto_solicitado = fields.Char('Descripción de producto/solución', help='Detallar el producto o solución que solicitó el cliente')
    
    @api.constrains('origin_type', 'contacto_comercial_id')
    def _check_origin(self):
        for lead in self:
            if lead.origin_type == 'contacto' and not lead.contacto_comercial_id:
                raise UserError('Si el origen es un Contacto Comercial, debe especificar cuál.')
    
    @api.model
    def create(self, vals):
        # Si se está creando sin contacto comercial y el origen no es "contacto", mostrar advertencia en log
        if not vals.get('contacto_comercial_id') and vals.get('origin_type') != 'contacto':
            self.env['mail.message'].create({
                'body': '<p><strong>Advertencia:</strong> Esta oportunidad se ha creado sin un contacto comercial previo.</p>',
                'model': 'crm.lead',
                'res_id': 0,  # Se actualizará después
                'message_type': 'notification',
                'author_id': self.env.user.partner_id.id,
                'subtype_id': self.env.ref('mail.mt_note').id,
            })
        
        lead = super(CrmLead, self).create(vals)
        
        # Actualizar el mensaje con el ID correcto
        if not vals.get('contacto_comercial_id') and vals.get('origin_type') != 'contacto':
            mensaje = self.env['mail.message'].search([
                ('model', '=', 'crm.lead'),
                ('res_id', '=', 0),
                ('author_id', '=', self.env.user.partner_id.id)
            ], limit=1)
            if mensaje:
                mensaje.write({'res_id': lead.id})
        
        return lead
    
    def action_warn_no_contacto(self):
        """Acción para mostrar advertencia al intentar crear un lead directamente"""
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Recomendación',
                'message': 'Idealmente, las oportunidades deberían generarse a partir de contactos comerciales. ¿Está seguro de que desea crear una oportunidad directamente?',
                'sticky': False,
                'type': 'warning',
                'next': {
                    'type': 'ir.actions.act_window',
                    'res_model': 'crm.lead',
                    'view_mode': 'form',
                    'context': self.env.context,
                }
            }
        }

