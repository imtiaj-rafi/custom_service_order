from odoo import api, fields, models, _
from odoo.exceptions import UserError
import base64
from io import BytesIO
import xlsxwriter


class SaleServiceOrder(models.Model):
    _name = 'sale.service.order'
    _description = 'Service Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Name',required=True,readonly=True,copy=False,tracking=True,default='New')
    company_id = fields.Many2one('res.company',string='Company',default=lambda self: self.env.company,required=True)
    currency_id = fields.Many2one('res.currency',string='Currency',default=lambda self: self.env.company.currency_id,required=True)
    salesman_id = fields.Many2one('res.users',string='Salesperson',default=lambda self: self.env.user,tracking=True,required=True)
    product_id = fields.Many2one('product.product',string='Product',tracking=True,domain=[('detailed_type', '=', 'service'),])
    quantity = fields.Float(string='Quantity', tracking=True,required=True, default=1.0)
    price_unit = fields.Monetary(string='Unit Price', required=True,tracking=True)
    amount_total = fields.Monetary(string='Total Amount', tracking=True,compute='_compute_amount_total', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ], tracking=True,string='Status', default='draft')

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
        for record in self:
            record.state = 'confirmed'
            record.message_post(body=_("Order Confirmed."))

    def action_cancel(self):
        for record in self:
            record.state = 'cancelled'
            record.message_post(body=_("Order Cancelled."))

    def action_reset_to_draft(self):
        for record in self:
            record.state = 'draft'
            record.message_post(body=_("Reset to Draft."))

    def action_add_from_history(self):
        return {
            'name': _('Service Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.service.order',
            'view_id': self.env.ref('custom_service_order.view_sale_service_order_tree_modal').id,
            'view_mode': 'tree',
            'target': 'new',
            'domain': [('id', '!=', self.id)],
            'context': {
                'active_id': self.id,
                'source_order_id': self.id,
            },
            'flags': {
                'action_buttons': False,
                'headless': True,
                'tree': {'create': False, 'edit': False, 'delete': False},
            }
        }

    def action_add_selected(self):
        source_order_id = (
                self.env.context.get('source_order_id') or
                self.env.context.get('default_source_order_id') or
                self._context.get('params', {}).get('id')
        )
        active_id = (
                self.env.context.get('active_id') or
                self.env.context.get('default_active_id') or
                self.env.context.get('params', {}).get('id')
        )
        if not active_id:
            raise UserError(_('No active order to update.'))

        if len(self) != 1:
            raise UserError(_('Please select exactly one history record to apply.'))

        selected = self[0]  # Get the first selected record
        current_order = self.env['sale.service.order'].browse(source_order_id)
        current_order.write({
            'product_id': selected.product_id.id,
            'quantity': selected.quantity,
            'price_unit': selected.price_unit,
        })
        current_order._compute_amount_total()
        current_order.message_post(body=_("Updated from history order: %s") % selected.name)

        return {'type': 'ir.actions.act_window_close'}

    def action_export_all(self):
        records = self.search([])

        if not records:
            raise UserError("No records to export!")

        # Create Excel file in memory
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet("Service Orders")

        # Define headers
        headers = [
            "Name", "Product", "Quantity",
            "Unit Price", "Total Amount"
        ]

        # Write headers (bold)
        bold = workbook.add_format({'bold': True})
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, bold)

        # Write data
        for row, record in enumerate(records, start=1):
            worksheet.write(row, 0, record.name)
            worksheet.write(row, 1, record.product_id.display_name)
            worksheet.write(row, 2, record.quantity)
            worksheet.write(row, 3, record.price_unit)
            worksheet.write(row, 4, record.amount_total)

        workbook.close()
        output.seek(0)
        excel_data = base64.b64encode(output.read())
        output.close()

        # Create an attachment
        attachment = self.env['ir.attachment'].create({
            'name': 'Service_Orders_Export.xlsx',
            'datas': excel_data,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'type': 'binary',
        })

        # Return download action
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

class InheritedSaleServiceOrder(models.Model):
    _inherit = 'sale.service.order'

    source_order_id = fields.Many2one(
        'sale.service.order',
        string="Source Order",
        invisible=True
    )