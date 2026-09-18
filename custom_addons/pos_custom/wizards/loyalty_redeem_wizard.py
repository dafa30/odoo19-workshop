from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class LoyaltyRedeemWizard(models.TransientModel):
    _name = 'loyalty.redeem.wizard'
    _description = 'Redeem Loyalty Points Wizard'

    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    loyalty_points = fields.Integer(related='partner_id.loyalty_points', string='Available Points')
    reward_product_id = fields.Many2one(
        'loyalty.reward.product', string='Reward Product', required=True,
        domain="[('points_required', '<=', loyalty_points), ('active', '=', True)]"
    )
    product_name = fields.Char(related='reward_product_id.product_id.name', string='Product')
    points_required = fields.Integer(related='reward_product_id.points_required', string='Points Required')
    points_after = fields.Integer(compute='_compute_points_after', string='Points After Redeem')
    notes = fields.Char(string='Notes')

    @api.depends('loyalty_points', 'points_required')
    def _compute_points_after(self):
        for rec in self:
            rec.points_after = rec.loyalty_points - (rec.points_required or 0)

    def action_confirm(self):
        self.ensure_one()
        if not self.reward_product_id:
            raise UserError(_('Pilih produk reward terlebih dahulu.'))
        if self.partner_id.loyalty_points < self.reward_product_id.points_required:
            raise ValidationError(_(
                'Poin tidak cukup. Dibutuhkan %(required)s poin, tersedia %(available)s poin.',
                required=self.reward_product_id.points_required,
                available=self.partner_id.loyalty_points,
            ))
        self.env['loyalty.point.history'].sudo().create({
            'partner_id': self.partner_id.id,
            'points': self.reward_product_id.points_required,
            'type': 'redeem',
            'product_id': self.reward_product_id.product_id.id,
            'notes': self.notes or (_('Redeem: %s') % self.reward_product_id.product_id.name),
        })
        self.partner_id.sudo().loyalty_points -= self.reward_product_id.points_required
        return {'type': 'ir.actions.act_window_close'}
