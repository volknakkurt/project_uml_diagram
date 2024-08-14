from odoo import models, fields, api, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _get_global_state(self, status):
        status_map = {
            'draft': 'Draft',
            'waiting': 'Waiting',
            'confirmed': 'Confirmed',
            'assigned': 'Ready',
            'done': 'Done',
            'cancel': 'Cancelled'
        }
        return status_map.get(status, 'Draft')

    @api.model
    def create(self, vals):
        picking = super(StockPicking, self).create(vals)

        current_picking = picking
        visited_picking_names = []

        while current_picking:
            origin = current_picking.origin
            if origin.startswith('Return of '):
                origin = origin[len('Return of '):]

            if origin in visited_picking_names:
                break

            visited_picking_names.append(origin)
            next_picking = self.env['stock.picking'].search([
                ('name', '=', origin)
            ], limit=1)

            if next_picking:
                if next_picking == current_picking:
                    break
                current_picking = next_picking
            else:
                break
        order_id = self.env['sale.order'].search([
            ('name', '=', current_picking.origin)
        ], limit=1)

        if not order_id:
            order_id = self.env['purchase.order'].search([
                ('name', '=', current_picking.origin)
            ], limit=1)

        project_ids = order_id.node_project_ids.ids
        last_visited_picking_name = visited_picking_names[0]
        code_prefix = ''
        if picking.picking_type_id.code == 'outgoing':
            code_prefix = 'OUT'
        elif picking.picking_type_id.code == 'incoming':
            code_prefix = 'INN'

        for project_id in project_ids:
            project = self.env['project.project'].browse(project_id)
            if not project:
                continue

            nodes = self.env['project.node'].with_context(active_test=False).search([
                ('project_id', '=', project.id),
                ('code', 'ilike', code_prefix + '%'),
            ])

            highest_number = 0
            for node in nodes:
                if len(node.code) > len(code_prefix) and node.code[len(code_prefix):].isdigit():
                    code_number = int(node.code[len(code_prefix):])
                    if code_number > highest_number:
                        highest_number = code_number

            new_code = code_prefix + str(highest_number + 1)

            parent_node = self.env['project.node'].search([
                ('project_id', '=', project.id),
                ('name', '=', last_visited_picking_name),
            ])

            self.env['project.node'].create({
                'name': picking.display_name,
                'project_id': project.id,
                'type': 'round_edges_node',
                'code': new_code,
                'date': picking.create_date,
                'global_state': self._get_global_state(picking.state),
                'is_stage_node': False,
                'parent_node': parent_node.id,
            })

        return picking
    # TODO: Burada hata var
    def write(self, vals):
        res = super(StockPicking, self).write(vals)
        for picking in self:

            current_picking = picking
            visited_picking_names = set()

            while current_picking:
                origin = current_picking.origin
                if origin.startswith('Return of '):
                    origin = origin[len('Return of '):]

                if origin in visited_picking_names:
                    break

                visited_picking_names.add(origin)
                next_picking = self.env['stock.picking'].search([
                    ('name', '=', origin)
                ], limit=1)

                if next_picking:
                    if next_picking == current_picking:
                        break
                    current_picking = next_picking
                else:
                    break

            order_id = self.env['sale.order'].search([
                ('name', '=', current_picking.origin)
            ], limit=1)

            if not order_id:
                order_id = self.env['purchase.order'].search([
                    ('name', '=', current_picking.origin)
                ], limit=1)

            project_ids = order_id.node_project_ids

            for project in project_ids:
                if not project:
                    continue

                code_prefix = 'OUT' if picking.picking_type_id.code == 'outgoing' else 'INN'

                nodes = self.env['project.node'].search([
                    ('project_id', '=', project.id),
                    ('parent_node.name', '=', order_id.name),
                    ('code', 'ilike', code_prefix + '%')
                ])
                backorder_picking = self.env['stock.picking'].search([
                    ('backorder_id', '=', picking.id)
                ])
                for node in nodes:
                    if picking.state == 'cancel':
                        node.write({
                            'global_state': self._get_global_state(picking.state),
                            'active': False
                        })
                    if node.name == backorder_picking.display_name:
                        node.write({
                            'global_state': self._get_global_state('draft'),
                        })
                    else:
                        node.write({
                            'global_state': self._get_global_state(picking.state),
                        })
        return res
