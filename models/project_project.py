from odoo import models, fields, api, _


class Project(models.Model):
    _inherit = "project.project"

    sale_order_ids = fields.Many2many(
        'sale.order',
        'sale_order_node_project_rel',
        'project_id',
        'order_id',
        string='Sale Orders'
    )
    purchase_order_ids = fields.Many2many(
        'purchase.order',
        'purchase_order_node_project_rel',
        'project_id',
        'purchase_order_id',
        string='Purchase Orders'
    )
    account_move_ids = fields.Many2many(
        'account.move',
        'account_move_node_project_rel',
        'project_id',
        'move_id',
        string='Account Moves'
    )

    production_ids = fields.Many2many(
        'mrp.production',
        'production_node_project_rel',
        'project_id',
        'production_id',
        string='Manufacturing Orders'
    )

    @api.model
    def create(self, vals):
        project = super(Project, self).create(vals)

        self.env['project.node'].create({
            'name': _('Project Created'),
            'project_id': project.id,
            'type': 'circle',
            'code': 'START',
            'date': project.create_date,
            'is_start_node': True,
            'is_stage_node': True,
        })
        return project

    def write(self, vals):
        res = super(Project, self).write(vals)

        if 'stage_id' in vals:

            new_stage_id = vals.get('stage_id')
            new_stage = self.env['project.project.stage'].browse(new_stage_id)

            if new_stage.fold:

                last_node = self.env['project.node'].search([
                    ('project_id', '=', self.id),
                    ('is_stage_node', '=', True)
                ], order='date desc', limit=1)

                existing_node = self.env['project.node'].search([
                    ('project_id', '=', self.id),
                    ('name', '=', _('Project Finish'))
                ])
                if not existing_node:
                    self.env['project.node'].create({
                        'name': _('Project End'),
                        'project_id': self.id,
                        'type': 'circle',
                        'code': 'END',
                        'date': fields.Datetime.now(),
                        'is_end_node': True,
                        'is_stage_node': True,
                        'parent_node': last_node.id if last_node else False,
                    })
            else:

                existing_node = self.env['project.node'].search([
                    ('project_id', '=', self.id),
                    ('name', '=', _('Project End'))
                ])
                if existing_node:
                    existing_node.unlink()

        return res

    def unlink(self):
        for project in self:
            nodes = self.env['project.node'].search([('project_id', '=', project.id)])
            nodes.unlink()
        return super(Project, self).unlink()
