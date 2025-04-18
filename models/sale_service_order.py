from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleServiceOrder(models.Model):
    _name = 'sale.service.order'
    _description = 'Service Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Order Reference',
        required=True,
        readonly=True,
        copy=False,
        default='New'
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True
    )

    salesman_id = fields.Many2one(
        'res.users',
        string='Salesperson',
        default=lambda self: self.env.user,
        required=True
    )

    product_id = fields.Many2one(
        'product.product',
        string='Service Product',
        domain=[('detailed_type', '=', 'service')],
        required=True
    )

    quantity = fields.Float(string='Quantity', required=True, default=1.0)

    price_unit = fields.Monetary(string='Unit Price', required=True)

    amount_total = fields.Monetary(string='Total Amount', compute='_compute_amount_total', store=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    @api.depends('quantity', 'price_unit')
    def _compute_amount_total(self):
        for rec in self:
            rec.amount_total = rec.quantity * rec.price_unit

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('sale.service.order') or _('New')
        return super().create(vals)

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_to_draft(self):
        self.write({'state': 'draft'})


