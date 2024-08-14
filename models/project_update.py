from odoo import models, fields, api, _


class ProjectUpdate(models.Model):
    _inherit = 'project.update'

    def _get_global_state(self, status):

        status_map = {
            'on_track': 'On Track',
            'at_risk': 'At Risk',
            'off_track': 'Off Track',
            'on_hold': 'On Hold',
            'done': 'Done'
        }
        return status_map.get(status, 'Draft')

    @api.model
    def create(self, vals):
        update = super(ProjectUpdate, self).create(vals)

        if update.project_id:

            nodes = self.env['project.node'].with_context(active_test=False).search([
                ('project_id', '=', update.project_id.id),
                ('code', 'ilike', 'UPT%')
            ])

            highest_number = 0
            for node in nodes:
                if len(node.code) > 3 and node.code[3:].isdigit():
                    code_number = int(node.code[3:])
                    if code_number > highest_number:
                        highest_number = code_number

            last_node = self.env['project.node'].search([
                ('project_id', '=', update.project_id.id),
                ('is_stage_node', '=', True)
            ], order='date desc', limit=1)

            new_code = 'UPT' + str(highest_number + 1)

            self.env['project.node'].create({
                'name': update.name,
                'project_id': update.project_id.id,
                'type': 'rhombus',
                'code': new_code,
                'date': update.date,
                'global_state': self._get_global_state(update.status),
                'is_stage_node': True,
                'parent_node': last_node.id if last_node else False,
            })

        return update

    def unlink(self):
        for update in self:
            node = self.env['project.node'].search([
                ('project_id', '=', update.project_id.id),
                ('name', '=', update.name)
            ], limit=1)

            if node:
                node.unlink()

        return super(ProjectUpdate, self).unlink()

    def write(self, vals):
        old_name = self.name
        res = super(ProjectUpdate, self).write(vals)

        if "name" or "date" in vals:
            node = self.env['project.node'].search([
                ('project_id', '=', self.project_id.id),
                ('name', '=', old_name),
                ('code', 'ilike', 'UPT%')
            ], limit=1)

            if node and (node.name != self.name or node.date != self.date):
                node.write({
                    'name': self.name,
                    'date': self.date,
                })
        if 'status' in vals:
            node = self.env['project.node'].search([
                ('project_id', '=', self.project_id.id),
                ('name', '=', self.name)
            ], limit=1)
            if node:
                node.global_state = self._get_global_state(vals['status'])
        return res
