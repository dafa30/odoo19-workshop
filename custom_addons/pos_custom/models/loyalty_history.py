from odoo import fields, models


class LoyaltyPointHistory(models.Model):
    _name = 'loyalty.point.history'
    _description = 'Loyalty Point History'
    _order = 'date desc'

    partner_id = fields.Many2one('res.partner', string='Customer', required=True, ondelete='cascade')
    pos_order_id = fields.Many2one('pos.order', string='POS Order', ondelete='set null')
    points = fields.Integer(string='Points', required=True)
    type = fields.Selection([
        ('earn', 'Earn'),
        ('redeem', 'Redeem'),
    ], string='Type', required=True)
    product_id = fields.Many2one('product.product', string='Reward Product', ondelete='set null')
    notes = fields.Char(string='Notes')
    date = fields.Datetime(string='Date', default=fields.Datetime.now)
