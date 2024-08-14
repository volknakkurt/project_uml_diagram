from odoo import models, fields, api, _


class ProjectTask(models.Model):
    _inherit = 'project.task'

    @api.model
    def create(self, vals):
        task = super(ProjectTask, self).create(vals)

        if task.project_id:
            nodes = self.env['project.node'].with_context(active_test=False).search([
                ('project_id', '=', task.project_id.id),
                ('code', 'ilike', 'TASK%')
            ])

            highest_number = 0
            for node in nodes:
                if len(node.code) > 4 and node.code[4:].isdigit():
                    code_number = int(node.code[4:])
                    if code_number > highest_number:
                        highest_number = code_number

            new_code = 'TASK' + str(highest_number + 1)

            self.env['project.node'].create({
                'name': task.name,
                'project_id': task.project_id.id,
                'project_task_id': task.id,
                'type': 'normal_node',
                'code': new_code,
                'date': task.date_deadline or task.create_date,
                'global_state': task.stage_id.name,
                'active': False,
            })

        return task

    def unlink(self):
        for task in self:
            node = self.env['project.node'].search([
                ('project_id', '=', task.project_id.id),
                ('name', '=', task.name)
            ], limit=1)

            if node:
                node.unlink()

        return super(ProjectTask, self).unlink()

    def write(self, vals):
        old_name = self.name
        res = super(ProjectTask, self).write(vals)
        if "name" or "date_deadline" in vals:
            node = self.env['project.node'].with_context(active_test=False).search([
                ('project_id', '=', self.project_id.id),
                ('name', '=', old_name),
                ('code', 'ilike', 'TASK%')
            ], limit=1)
            if node and (node.name != self.name or (node.date != self.date_deadline or self.create_date)):
                node.write({
                    'name': self.name,
                    'date': self.date_deadline or self.create_date,
                })
        if 'stage_id' in vals:
            node = self.env['project.node'].with_context(active_test=False).search([
                ('project_id', '=', self.project_id.id),
                ('name', '=', self.name)
            ], limit=1)
            if node:
                node.global_state = self.stage_id.name
        if "milestone_id" in vals:
            parent_node = self.env['project.node'].search([
                ('project_id', '=', self.project_id.id),
                ('name', '=', self.milestone_id.name)
            ], limit=1)

            node.active = True
            node.parent_node = parent_node.id if parent_node else False

        else:
            node.active = False
            node.parent_node = False
        return res
