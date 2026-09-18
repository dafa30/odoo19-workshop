from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    loyalty_points = fields.Integer(string='Loyalty Points', default=0)

    def action_redeem_points(self):
        self.ensure_one()
        return {
            'name': 'Redeem Loyalty Points',
            'type': 'ir.actions.act_window',
            'res_model': 'loyalty.redeem.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_partner_id': self.id},
        }
