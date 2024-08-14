from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    node_project_ids = fields.Many2many(
        'project.project',
        'production_node_project_rel',
        'production_id',
        'project_id',
        string='Node Projects'
    )

    def _get_global_state(self, status):

        status_map = {
            'draft': 'Draft',
            'confirmed': 'Confirmed',
            'progress': 'In Progress',
            'to_close': 'To Close',
            'done': 'Done',
            'cancel': 'Cancelled',
        }
        return status_map.get(status, 'Draft')

    @api.model
    def create(self, vals):
        production = super(MrpProduction, self).create(vals)
        project_ids = []
        analytic_distribution = vals.get('analytic_distribution', {})
        if analytic_distribution:
            project_ids = [int(pid) for pid in analytic_distribution.keys()]

        project_records = self.env['project.project'].browse(project_ids)
        production.write({"node_project_ids": [(6, 0, list(project_records.ids))]})

        for project_id in project_ids:

            nodes = self.env['project.node'].with_context(active_test=False).search([
                ('project_id', '=', project_id),
                ('code', 'ilike', 'MRP%')
            ])

            highest_number = 0
            for node in nodes:
                if len(node.code) > 3 and node.code[3:].isdigit():
                    code_number = int(node.code[3:])
                    if code_number > highest_number:
                        highest_number = code_number
            if production.origin:
                order_id = self.env['sale.order'].search([
                    ('name', '=', production.origin)
                ])
                last_node = self.env['project.node'].search([
                    ('project_id', '=', project_id),
                    ('name', '=', order_id.name),
                    ('is_stage_node', '=', True)
                ], order='date desc', limit=1)
            else:
                last_node = self.env['project.node'].search([
                    ('project_id', '=', project_id),
                    ('is_stage_node', '=', True)
                ], order='date desc', limit=1)

            new_code = 'MRP' + str(highest_number + 1)

            self.env['project.node'].create({
                'name': production.name,
                'project_id': project_id,
                'type': 'stadium_shaped',
                'code': new_code,
                'date': production.date_start,
                'global_state': self._get_global_state(production.state),
                'is_stage_node': True,
                'parent_node': last_node.id if last_node else False,
            })

        return production

    def write(self, vals):
        # TODO : Burada iptal ettiğimde hala gözüküyor sebebini anlamadım çünkü self boş geliyor iptal ederken
        old_node_project_ids = set(self.node_project_ids.ids)
        res = super(MrpProduction, self).write(vals)
        if "date_start" in vals:
            nodes = self.env['project.node'].with_context(active_test=False).search([
                ('project_id', '=', list(old_node_project_ids)),
                ('name', '=', self.name),
                ('code', 'ilike', 'MRP%')
            ])
            for node in nodes:
                if node.date != self.date_start:
                    node.write({
                        'date': self.date_start
                    })
        if "state" in vals:
            nodes = self.env['project.node'].with_context(active_test=False).search([
                ('project_id', '=', list(old_node_project_ids)),
                ('name', '=', self.name),
                ('code', 'ilike', 'MRP%')
            ])
            for node in nodes:
                if self.state == 'cancel':
                    node.write({
                        'global_state': self._get_global_state(self.state),
                        'active': False
                    })
                else:
                    node.write({
                        'global_state': self._get_global_state(self.state),
                        'active': True
                    })

        if 'node_project_ids' not in vals:
            new_node_project_ids = set()
            if "analytic_distribution" in vals:
                analytic_distribution = vals.get('analytic_distribution')
                if analytic_distribution:
                    for analytic_account_id in analytic_distribution.keys():
                        new_node_project_ids.add(int(analytic_account_id))

                removed_node_project_ids = old_node_project_ids - new_node_project_ids
                added_node_project_ids = new_node_project_ids - old_node_project_ids

                if added_node_project_ids or removed_node_project_ids:
                    new_node_projects = self.env['project.project'].search([
                        ('id', 'in', list(new_node_project_ids)),
                    ])
                    if 'node_project_ids' not in vals:
                        self.node_project_ids = new_node_projects

                for project_id in removed_node_project_ids:
                    nodes = self.env['project.node'].search([
                        ('project_id', '=', project_id),
                        ('name', '=', self.name),
                        ('code', 'ilike', 'MRP%')
                    ])
                    nodes.unlink()
                for project_id in added_node_project_ids:
                    project = self.env['project.project'].browse(project_id)
                    if not project:
                        continue

                    nodes = self.env['project.node'].with_context(active_test=False).search([
                        ('project_id', '=', project.id),
                        ('code', 'ilike', 'MRP%')
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

                    new_code = 'MRP' + str(highest_number + 1)

                    self.env['project.node'].create({
                        'name': self.name,
                        'project_id': project.id,
                        'type': 'hexagon_node',
                        'code': new_code,
                        'date': self.date_start,
                        'global_state': self._get_global_state(self.state),
                        'is_stage_node': True,
                        'parent_node': last_node.id if last_node else False,
                    })
        return res

    def unlink(self):
        for production in self:
            for project in production.node_project_ids:
                nodes = self.env['project.node'].search([
                    ('name', '=', production.name),
                    ('project_id', '=', project.id)
                ])
                nodes.unlink()
        return super(MrpProduction, self).unlink()