from odoo import models


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def action_pos_order_paid(self):
        res = super().action_pos_order_paid()
        if self.partner_id and self.amount_total > 0 and not self.is_refund:
            points_earned = int(self.amount_total // 10000)
            if points_earned > 0:
                self.partner_id.sudo().loyalty_points += points_earned
                self.env['loyalty.point.history'].sudo().create({
                    'partner_id': self.partner_id.id,
                    'pos_order_id': self.id,
                    'points': points_earned,
                    'type': 'earn',
                })
        return res
