from odoo import models, fields, api, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    node_project_ids = fields.Many2many(
        'project.project',
        'purchase_order_node_project_rel',
        'purchase_order_id',
        'project_id',
        string='Node Projects'
    )

    def _get_global_state(self, status):
        status_map = {
            'draft': 'Draft',
            'sent': 'Sent',
            'to_approve': 'To Approve',
            'purchase': 'Purchase',
            'done': 'Done',
            'cancel': 'Cancelled',
        }
        return status_map.get(status, 'Draft')

    @api.model
    def create(self, vals):
        order = super(PurchaseOrder, self).create(vals)

        new_node_project_ids = set()
        if 'order_line' in vals:
            for line in vals['order_line']:
                if len(line) > 2 and 'analytic_distribution' in line[2]:
                    analytic_distribution = line[2]['analytic_distribution']
                    for keys in analytic_distribution.keys():
                        analytic_account_id = keys
                        project = self.env['project.project'].search([
                            ('analytic_account_id', '=', int(analytic_account_id)),
                        ], limit=1)
                        if project:
                            new_node_project_ids.add(project.id)
                for order_line in self.order_line:
                    if line[1] != order_line.id:
                        if order_line.analytic_distribution:
                            for key in order_line.analytic_distribution.keys():
                                analytic_account_id = key
                                project = self.env['project.project'].search([
                                    ('analytic_account_id', '=', int(analytic_account_id)),
                                ], limit=1)
                                if project:
                                    new_node_project_ids.add(project.id)

        for project_id in list(new_node_project_ids):

            nodes = self.env['project.node'].with_context(active_test=False).search([
                ('project_id', '=', project_id),
                ('code', 'ilike', 'PRCH%')
            ])

            highest_number = 0
            for node in nodes:
                if len(node.code) > 4 and node.code[4:].isdigit():
                    code_number = int(node.code[4:])
                    if code_number > highest_number:
                        highest_number = code_number

            last_node = self.env['project.node'].search([
                ('project_id', '=', project_id),
                ('is_stage_node', '=', True)
            ], order='date desc', limit=1)

            new_code = 'PRCH' + str(highest_number + 1)

            self.env['project.node'].create({
                'name': order.name,
                'project_id': project_id,
                'type': 'hexagon_node',
                'code': new_code,
                'date': order.date_order,
                'global_state': self._get_global_state(order.state),
                'is_stage_node': True,
                'parent_node': last_node.id if last_node else False,
            })

        return order

    def write(self, vals):
        old_node_project_ids = set(self.node_project_ids.ids)
        old_node_name = self.name

        res = super(PurchaseOrder, self).write(vals)

        if "name" or "date" in vals:
            nodes = self.env['project.node'].search([
                ('project_id', 'in', list(old_node_project_ids)),
                ('name', '=', old_node_name),
                ('code', 'ilike', 'PRCH%')
            ])
            for node in nodes:
                if node.name != self.name or node.date != self.date_order:
                    node.write({
                        'name': self.name,
                        'date': self.date_order,
                    })
                if node.global_state != self._get_global_state(self.state):
                    node.write({
                        'global_state': self._get_global_state(self.state)
                    })

        if 'node_project_ids' and "name" or "date" not in vals:
            new_node_project_ids = set()
            if 'order_line' in vals:
                for line in vals['order_line']:
                    if len(line) > 2 and 'analytic_distribution' in line[2]:
                        analytic_distribution = line[2]['analytic_distribution']
                        for keys in analytic_distribution.keys():
                            analytic_account_id = keys
                            project = self.env['project.project'].search([
                                ('analytic_account_id', '=', int(analytic_account_id)),
                            ], limit=1)
                            if project:
                                new_node_project_ids.add(project.id)
                    for order_line in self.order_line:
                        if line[1] != order_line.id:
                            if order_line.analytic_distribution:
                                for key in order_line.analytic_distribution.keys():
                                    analytic_account_id = key
                                    project = self.env['project.project'].search([
                                        ('analytic_account_id', '=', int(analytic_account_id)),
                                    ], limit=1)
                                    if project:
                                        new_node_project_ids.add(project.id)
                removed_node_project_ids = old_node_project_ids - new_node_project_ids
                added_node_project_ids = new_node_project_ids - old_node_project_ids

                if added_node_project_ids or removed_node_project_ids:
                    new_node_projects = self.env['project.project'].search([
                        ('id', 'in', list(new_node_project_ids)),
                    ])
                    if 'node_project_ids' not in vals:
                        self.node_project_ids = new_node_projects

                # Delete nodes for removed projects
                for project_id in removed_node_project_ids:
                    nodes = self.env['project.node'].search([
                        ('project_id', '=', project_id),
                        ('name', '=', self.name),
                        ('code', 'ilike', 'PRCH%')
                    ])
                    nodes.unlink()

                # Create nodes for added projects
                for project_id in added_node_project_ids:
                    project = self.env['project.project'].browse(project_id)
                    if not project:
                        continue

                    nodes = self.env['project.node'].with_context(active_test=False).search([
                        ('project_id', '=', project.id),
                        ('code', 'ilike', 'PRCH%')
                    ])

                    highest_number = 0
                    for node in nodes:
                        if len(node.code) > 4 and node.code[4:].isdigit():
                            code_number = int(node.code[4:])
                            if code_number > highest_number:
                                highest_number = code_number

                    last_node = self.env['project.node'].search([
                        ('project_id', '=', project.id),
                        ('is_stage_node', '=', True)
                    ], order='date desc', limit=1)

                    new_code = 'PRCH' + str(highest_number + 1)

                    self.env['project.node'].create({
                        'name': self.name,
                        'project_id': project.id,
                        'type': 'hexagon_node',
                        'code': new_code,
                        'date': self.date_order,
                        'global_state': self._get_global_state(self.state),
                        'is_stage_node': True,
                        'parent_node': last_node.id if last_node else False,
                    })

        return res

    def unlink(self):
        for order in self:
            for project in order.node_project_ids:
                nodes = self.env['project.node'].search([
                    ('name', '=', order.name),
                    ('project_id', '=', project.id)
                ])
                nodes.unlink()
        return super(PurchaseOrder, self).unlink()
