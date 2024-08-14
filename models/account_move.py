from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = "account.move"

    node_project_ids = fields.Many2many(
        'project.project',
        'account_move_node_project_rel',
        'move_id',
        'project_id',
        string='Node Projects'
    )

    def _get_global_state(self, status):

        status_map = {
            'not_paid': 'Not Paid',
            'in_payment': 'In Payment',
            'paid': 'Paid',
            'partial': 'Partial',
            'reversed': 'Reversed',
            'invoicing_legacy': 'Invoicing App Legacy',
        }
        return status_map.get(status, 'Not Paid')

    @api.model
    def create(self, vals):
        move = super(AccountMove, self).create(vals)
        if move.invoice_origin:
            related_orders = self._get_related_orders(move.invoice_origin)
            for order in related_orders:
                self._create_project_node(order, move)
        else:
            project_ids = set()
            if 'order_line' in vals:
                for line_vals in vals['order_line']:
                    if isinstance(line_vals, (list, tuple)) and len(line_vals) > 2:
                        line_data = line_vals[2]
                        if 'analytic_distribution' in line_data:
                            for analytic_account_id in line_data['analytic_distribution']:
                                analytic = self.env['account.analytic.account'].search([
                                    ('id', '=', analytic_account_id)
                                ], limit=1)
                                if analytic and analytic.project_ids:
                                    for project in analytic.project_ids:
                                        project_ids.add(project.id)

            move.write({"node_project_ids": [(6, 0, list(project_ids))]})
        return move

    def write(self, vals):
        res = super(AccountMove, self).write(vals)
        if 'state' in vals and self.invoice_origin:
            related_orders = self._get_related_orders(self.invoice_origin)
            for order in related_orders:
                self._create_project_node(order, self)
        return res

    def _get_related_orders(self, origin):
        related_orders = self.env['sale.order'].browse() | self.env['purchase.order'].browse()
        origin_refs = origin.split(',')
        for ref in origin_refs:
            sale_order = self.env['sale.order'].search([('name', '=', ref.strip())], limit=1)
            if sale_order:
                related_orders |= sale_order
            else:
                purchase_order = self.env['purchase.order'].search([('name', '=', ref.strip())], limit=1)
                if purchase_order:
                    related_orders |= purchase_order
        return related_orders

    def _create_project_node(self, order, move):
        project_ids = order.node_project_ids.ids
        for project_id in project_ids:

            parent_node = self.env['project.node'].search([
                ('name', '=', order.name)
            ], limit=1)

            nodes = self.env['project.node'].search([
                ('project_id', '=', project_id),
                ('code', 'ilike', 'INV%')
            ])

            highest_number = 0
            for node in nodes:
                if len(node.code) > 3 and node.code[3:].isdigit():
                    code_number = int(node.code[3:])
                    if code_number > highest_number:
                        highest_number = code_number

            new_code = 'INV' + str(highest_number + 1)

            self.env['project.node'].create({
                'name': move.name,
                'project_id': project_id.id,
                'type': 'parallelogram',
                'code': new_code,
                'date': move.create_date,
                'global_state': self._get_global_state(move.payment_state),
                'parent_node': parent_node.id if parent_node else False,
            })
