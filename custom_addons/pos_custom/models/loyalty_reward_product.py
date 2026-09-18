from odoo import fields, models


class LoyaltyRewardProduct(models.Model):
    _name = 'loyalty.reward.product'
    _description = 'Loyalty Reward Product'
    _order = 'points_required asc'

    product_id = fields.Many2one(
        'product.product', string='Product', required=True, ondelete='cascade'
    )
    points_required = fields.Integer(string='Points Required', required=True, default=1)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('product_unique', 'unique(product_id)', 'Produk ini sudah terdaftar sebagai reward.'),
        ('points_positive', 'CHECK(points_required > 0)', 'Points harus lebih dari 0.'),
    ]
