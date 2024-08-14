from odoo import models, fields, api, _


class ProjectMilestone(models.Model):
    _inherit = 'project.milestone'

    def _get_global_state(self, status):

        status_map = {
            'unreached': 'Unreached',
            'reached': 'Reached',
        }
        return status_map.get(status, 'Unreached')

    @api.model
    def create(self, vals):
        milestone = super(ProjectMilestone, self).create(vals)

        if milestone.project_id:

            nodes = self.env['project.node'].with_context(active_test=False).search([
                ('project_id', '=', milestone.project_id.id),
                ('code', 'ilike', 'MLS%')
            ])

            highest_number = 0
            for node in nodes:
                if len(node.code) > 3 and node.code[3:].isdigit():
                    code_number = int(node.code[3:])
                    if code_number > highest_number:
                        highest_number = code_number

            last_node = self.env['project.node'].search([
                ('project_id', '=', milestone.project_id.id),
                ('is_stage_node', '=', True)
            ], order='date desc', limit=1)

            new_code = 'MLS' + str(highest_number + 1)

            self.env['project.node'].create({
                'name': milestone.name,
                'project_id': milestone.project_id.id,
                'type': 'asymmetric_shape',
                'code': new_code,
                'date': milestone.deadline or milestone.create_date,
                'global_state': 'Reached' if milestone.is_reached else 'Unreached',
                'is_stage_node': True,
                'parent_node': last_node.id if last_node else False,
            })

        return milestone

    def unlink(self):
        for milestone in self:
            node = self.env['project.node'].search([
                ('project_id', '=', milestone.project_id.id),
                ('name', '=', milestone.name)
            ], limit=1)

            if node:
                node.unlink()

        return super(ProjectMilestone, self).unlink()

    def write(self, vals):
        old_name = self.name
        res = super(ProjectMilestone, self).write(vals)

        if "name" or "deadline" in vals:
            node = self.env['project.node'].search([
                ('project_id', '=', self.project_id.id),
                ('name', '=', old_name),
                ('code', 'ilike', 'MLS%')
            ], limit=1)

            if node and (node.name != self.name or (node.date != self.deadline or self.create_date)):
                node.write({
                    'name': self.name,
                    'date': self.deadline,
                })
        if 'is_reached' in vals:
            node = self.env['project.node'].search([
                ('project_id', '=', self.project_id.id),
                ('name', '=', self.name)
            ], limit=1)
            if node:
                node.global_state = 'Reached' if vals['is_reached'] == True else 'Unreached'
        return res
