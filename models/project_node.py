# Copyright 2024 Akkurt Volkan
# License AGPL-3.0.

from odoo import models, fields, api

code_to_model_map = {
    'START': {'model': 'project.project', 'xml_id': 'project.act_project_project_2_project_task_all',
              'menu_id': 'project.menu_projects'},
    'UPT': {'model': 'project.update', 'xml_id': 'project.project_update_all_action',
            'menu_id': 'project.menu_projects'},
    'MLS': {'model': 'project.milestone', 'xml_id': 'project.action_project_milestone',
            'menu_id': 'project.menu_projects'},
    'TASK': {'model': 'project.task', 'xml_id': 'project.act_project_project_2_project_task_all',
             'menu_id': 'project.menu_project_task'},
    'SALE': {'model': 'sale.order', 'xml_id': 'sale.action_quotations_with_onboarding',
             'menu_id': 'sale.menu_sale_quotations'},
    'PRCH': {'model': 'purchase.order', 'xml_id': 'purchase.purchase_rfq', 'menu_id': 'purchase.menu_purchase_rfq'},
    'INN': {'model': 'stock.picking', 'xml_id': 'stock.menu_purchase_rfq',
            'menu_id': 'stock.menu_purchase_rfq'},
    'OUT': {'model': 'stock.picking', 'xml_id': 'stock.action_picking_tree_all',
            'menu_id': 'stock.menu_sale_quotations'},
    'MRP': {'model': 'mrp.production', 'xml_id': 'mrp.mrp_production_action',
            'menu_id': 'mrp.menu_manufacturing_order'},
    'MVINN': {'model': 'account.move', 'xml_id': 'account.action_move_in_invoice_type',
              'menu_id': 'account.menu_action_move_in_invoice_type'},
    'MVOUT': {'model': 'account.move', 'xml_id': 'account.action_move_out_invoice_type',
              'menu_id': 'account.menu_action_move_out_invoice_type'},
    'FINISH': {'model': 'project.project', 'xml_id': 'project.act_project_project_2_project_task_all',
               'menu_id': 'project.menu_projects'}
}


class ProjectNode(models.Model):
    _name = 'project.node'
    _description = 'Project Node'
    _rec_name = 'name'

    project_task_id = fields.Many2one('project.task', string="Project Task")
    active = fields.Boolean(default=True)
    name = fields.Char(string="Name", required=True)
    date = fields.Date(string="Date", required=True, default=lambda self: fields.Date.today())
    global_state = fields.Char(string="Global State")
    type = fields.Selection([
        ("circle", "Circle"),
        ("normal_node", "Normal Node"),
        ("round_edges_node", "Round Edges Node"),
        ("stadium_shaped", "Stadium Shaped"),
        ("asymmetric_shape", "Asymmetric Shape"),
        ("rhombus", "Rhombus"),
        ("hexagon_node", "Hexagon Node"),
        ("parallelogram", "Parallelogram"),
    ], string="Type", help="Circle: (())\n"
                           "Normal Node: []\n"
                           "Round Edges Node: ()\n"
                           "Stadium Shaped: ([])\n"
                           "Asymmetric Shape: >]\n"
                           "Rhombus: {}\n"
                           "Hexagon Node: {{}}\n"
                           "Parallelogram: [//]")
    code = fields.Char(string='Short Code', size=6, readonly=False, store=True, required=True)
    project_id = fields.Many2one("project.project", string="Project")
    parent_node = fields.Many2one('project.node', string="Parent Node")
    is_start_node = fields.Boolean(string="Start Node", default=False)
    is_end_node = fields.Boolean(string="End Node", default=False)
    is_stage_node = fields.Boolean(string="Stage Node", default=False)

    def _get_action_id(self, model_name, action_xml_id=None):

        domain = [('res_model', '=', model_name)]

        if action_xml_id:
            domain.append(('xml_id', '=', action_xml_id))

        action = self.env['ir.actions.act_window'].search(domain, limit=1)

        return action.id if action else None

    def _get_menu_id(self, menu_xml_id):
        menu = self.env['ir.ui.menu'].search([('name', '=', menu_xml_id)], limit=1)
        return menu.id if menu else None

    def _generate_mermaid_data(self, project_id=None):
        nodes = self.search([('active', '=', True), ('project_id', '=', project_id)])

        node_lines = []
        edge_lines = []
        click_lines = []
        style_lines = []

        for node in nodes:
            # Define node shapes
            if node.type == 'circle':
                if node.code.startswith('START'):
                    node_lines.append(f'{node.code}((fa:fa-play {node.name}))')
                elif node.code.startswith('END'):
                    node_lines.append(f'{node.code}((fa:fa-stop {node.name}))')
                else:
                    node_lines.append(f'{node.code}(({node.name}))')

            elif node.type == 'normal_node':
                if node.code.startswith('TASK'):
                    node_lines.append(f'{node.code}[fa:fa-tasks {node.name}]')
                else:
                    node_lines.append(f'{node.code}[fa:fa-tasks {node.name}]')

            elif node.type == 'round_edges_node':
                if node.code.startswith('INN'):
                    node_lines.append(f'{node.code}(fa:fa-truck fa:fa-sign-in {node.name})')
                elif node.code.startswith('OUT'):
                    node_lines.append(f'{node.code}(fa:fa-truck fa:fa-sign-out {node.name})')
                else:
                    node_lines.append(f'{node.code}({node.name})')

            elif node.type == 'stadium_shaped':
                if node.code.startswith('MRP'):
                    node_lines.append(f'{node.code}([fa:fa-cogs {node.name}])')

            elif node.type == 'asymmetric_shape':
                if node.code.startswith('MLS'):
                    if node.global_state == 'Reached':
                        node_lines.append(f'{node.code}>fa:fa-trophy {node.name}]')
                    else:
                        node_lines.append(f'{node.code}>fa:fa-flag-checkered {node.name}]')
                else:
                    node_lines.append(f'{node.code}>{node.name}]')

            elif node.type == 'rhombus':
                if node.code.startswith('UPT'):
                    node_lines.append(f'{node.code}{{fa:fa-refresh {node.name}}}')
                else:
                    node_lines.append(f'{node.code}{{{node.name}}}')

            elif node.type == 'hexagon_node':
                if node.code.startswith('PRCH'):
                    node_lines.append(f'{node.code}{{{{fa:fa-shopping-cart {node.name}}}}}')
                elif node.code.startswith('SALE'):
                    node_lines.append(f'{node.code}{{{{fa:fa-tags {node.name}}}}}')
                else:
                    node_lines.append(f'{node.code}{{{{{node.name}}}}}')

            elif node.type == 'parallelogram':
                if node.global_state == 'Not Paid':
                    node_lines.append(f'{node.code}[/fa:fa-square-o {node.name}/]')
                elif node.global_state == 'In Payment':
                    node_lines.append(f'{node.code}[/fa:fa-check-square {node.name}/]')
                elif node.global_state == 'Paid':
                    node_lines.append(f'{node.code}[/fa:fa-check-square {node.name}/]')
                elif node.global_state == 'Partial':
                    node_lines.append(f'{node.code}[/fa:fa-check-square-o {node.name}/]')
                else:
                    node_lines.append(f'{node.code}[/{node.name}/]')

            else:
                node_lines.append(f'{node.code}({node.name})')

            if node.parent_node:
                edge_lines.append(f'{node.parent_node.code} --> {node.code}')

            if node.code.startswith('START'):
                style_lines.append(f'class {node.code} project_start_node_style' + '\n')
                style_lines.append('classDef project_start_node_style fill:#FCDBA6,stroke:#FCDBA6,stroke-width:2px;' + '\n')

            elif node.code.startswith('MLS'):
                if node.global_state == 'Reached':
                    style_lines.append(f'class {node.code} reached_node_style' + '\n')
                    style_lines.append(
                        'classDef reached_node_style fill:#FCD6B3,stroke:#F7B97C,stroke-width:2px;' + '\n')
                else:
                    style_lines.append(f'class {node.code} unreached_node_style')
                    style_lines.append(
                        'classDef unreached_node_style fill:#FCD6B3,stroke:#F7B97C,stroke-width:2px;')

            elif node.code.startswith('UPT'):
                style_lines.append(f'class {node.code} update_node_style')
                style_lines.append('classDef update_node_style fill:#95C5D4,stroke:#7FA2B3,stroke-width:2px;')

            elif node.code.startswith('TASK'):
                style_lines.append(f'class {node.code} task_node_style')
                style_lines.append('classDef task_node_style fill:#F8E4DB,stroke:#E4C1B0,stroke-width:2px;')

            elif node.code.startswith('SALE'):
                if node.global_state == 'Draft':
                    style_lines.append(f'class {node.code} sale_draft_node_style')
                    style_lines.append(
                        'classDef sale_draft_node_style fill:#B7DAE4,stroke:#B7DAE4,stroke-width:2px;')
                elif node.global_state == 'Sale Order':
                    style_lines.append(f'class {node.code} sale_order_node_style')
                    style_lines.append(
                        'classDef sale_order_node_style fill:#00FF00,stroke:#00CC00,stroke-width:2px;')
                elif node.global_state == 'Cancelled':
                    style_lines.append(f'class {node.code} sale_cancel_node_style')
                    style_lines.append(
                        'classDef sale_cancel_node_style fill:#C75552,stroke:#C75552,stroke-width:2px;')
                else:
                    style_lines.append(f'class {node.code} sale_other_node_style')
                    style_lines.append(
                        'classDef sale_other_node_style fill:#B0B57E,stroke:#B0B57E,stroke-width:2px;')

            elif node.code.startswith('PRCH'):
                if node.global_state == 'Draft':
                    style_lines.append(f'class {node.code} purchase_draft_node_style')
                    style_lines.append(
                        'classDef purchase_draft_node_style fill:#B7DAE4,stroke:#B7DAE4,stroke-width:2px;')
                elif node.global_state == 'Purchase':
                    style_lines.append(f'class {node.code} purchase_order_node_style')
                    style_lines.append(
                        'classDef purchase_order_node_style fill:#00FF00,stroke:#00CC00,stroke-width:2px;')
                elif node.global_state == 'Cancelled':
                    style_lines.append(f'class {node.code} purchase_cancel_node_style')
                    style_lines.append(
                        'classDef purchase_cancel_node_style fill:#C75552,stroke:#C75552,stroke-width:2px;')
                else:
                    style_lines.append(f'class {node.code} purchase_other_node_style')
                    style_lines.append(
                        'classDef purchase_other_node_style fill:#C8B592,stroke:#C8B592,stroke-width:2px;')

            elif node.code.startswith('MOVE'):
                if node.global_state == 'Not Paid':
                    style_lines.append(f'class {node.code} move_not_paid_node_style')
                    style_lines.append(
                        'classDef move_not_paid_node_style fill:#E6ECF2,stroke:#E6ECF2,stroke-width:2px;')
                elif node.global_state == 'Partial':
                    style_lines.append(f'class {node.code} move_partial_node_style')
                    style_lines.append(
                        'classDef move_partial_node_style fill:#00FF00,stroke:#00CC00,stroke-width:2px;')
                elif node.global_state == 'Paid':
                    style_lines.append(f'class {node.code} move_paid_node_style')
                    style_lines.append(
                        'classDef move_paid_node_style fill:#B0B57E,stroke:#B0B57E,stroke-width:2px;')
                else:
                    style_lines.append(f'class {node.code} move_other_node_style')
                    style_lines.append(
                        'classDef move_other_node_style fill:#E6ECF2,stroke:#E6ECF2,stroke-width:2px;')

            elif node.code.startswith('INN'):
                if node.global_state == 'Draft':
                    style_lines.append(f'class {node.code} stock_in_draft_node_style')
                    style_lines.append(
                        'classDef stock_in_draft_node_style fill:#E6ECF2,stroke:#B7DAE4,stroke-width:2px;')
                elif node.global_state == 'Confirmed':
                    style_lines.append(f'class {node.code} stock_in_confirmed_node_style')
                    style_lines.append(
                        'classDef stock_in_confirmed_node_style fill:#B7DAE4,stroke:#B7DAE4,stroke-width:2px;')
                elif node.global_state == 'Done':
                    style_lines.append(f'class {node.code} stock_in_done_node_style')
                    style_lines.append(
                        'classDef stock_in_done_node_style fill:#00FF00,stroke:#00CC00,stroke-width:2px;')
                elif node.global_state == 'Cancelled':
                    style_lines.append(f'class {node.code} stock_in_cancel_node_style')
                    style_lines.append(
                        'classDef stock_in_cancel_node_style fill:#C75552,stroke:#C75552,stroke-width:2px;')
                else:
                    style_lines.append(f'class {node.code} stock_in_other_node_style')
                    style_lines.append(
                        'classDef stock_in_other_node_style fill:#B7DAE4,stroke:#B7DAE4,stroke-width:2px;')

            elif node.code.startswith('OUT'):
                if node.global_state == 'Draft':
                    style_lines.append(f'class {node.code} stock_out_draft_node_style')
                    style_lines.append(
                        'classDef stock_out_draft_node_style fill:#E6ECF2,stroke:#B7DAE4,stroke-width:2px;')
                elif node.global_state == 'Confirmed':
                    style_lines.append(f'class {node.code} stock_out_confirmed_node_style')
                    style_lines.append(
                        'classDef stock_out_confirmed_node_style fill:#E6ECF2,stroke:#E6ECF2,stroke-width:2px;')
                elif node.global_state == 'Done':
                    style_lines.append(f'class {node.code} stock_out_done_node_style')
                    style_lines.append(
                        'classDef stock_out_done_node_style fill:#00FF00,stroke:#00CC00,stroke-width:2px;')
                elif node.global_state == 'Cancelled':
                    style_lines.append(f'class {node.code} stock_out_cancel_node_style')
                    style_lines.append(
                        'classDef stock_out_cancel_node_style fill:#C75552,stroke:#C75552,stroke-width:2px;')
                else:
                    style_lines.append(f'class {node.code} stock_out_other_node_style')
                    style_lines.append(
                        'classDef stock_out_other_node_style fill:#E6ECF2,stroke:#E6ECF2,stroke-width:2px;')

            elif node.code.startswith('MRP'):
                if node.global_state == 'Draft':
                    style_lines.append(f'class {node.code} mrp_draft_node_style')
                    style_lines.append(
                        'classDef mrp_draft_node_style fill:#B7DAE4,stroke:#B7DAE4,stroke-width:2px;')
                elif node.global_state == 'Confirmed':
                    style_lines.append(f'class {node.code} mrp_confirmed_node_style')
                    style_lines.append(
                        'classDef mrp_confirmed_node_style fill:#ECD7A9,stroke:#ECD7A9,stroke-width:2px;')
                elif node.global_state == 'In Progress':
                    style_lines.append(f'class {node.code} mrp_in_progress_node_style')
                    style_lines.append(
                        'classDef mrp_in_progress_node_style fill:#ECD7A9,stroke:#ECD7A9,stroke-width:2px;')
                elif node.global_state == 'Done':
                    style_lines.append(f'class {node.code} mrp_done_node_style')
                    style_lines.append(
                        'classDef mrp_done_node_style fill:#00FF00,stroke:#00CC00,stroke-width:2px;')
                elif node.global_state == 'Cancel':
                    style_lines.append(f'class {node.code} mrp_cancel_node_style')
                    style_lines.append(
                        'classDef mrp_cancel_node_style fill:#C75552,stroke:#C75552,stroke-width:2px;')
                else:
                    style_lines.append(f'class {node.code} mrp_other_node_style')
                    style_lines.append(
                        'classDef mrp_other_node_style fill:#ECD7A9,stroke:#ECD7A9,stroke-width:2px;')

            elif node.code.startswith('END'):
                style_lines.append(f'class {node.code} project_end_node_style')
                style_lines.append('classDef project_end_node_style fill:#FCDBA6,stroke:#FCDBA6,stroke-width:2px;')
                # Create URL and click lines

        for node in nodes:
            mapping = next(
                (mapping for code, mapping in code_to_model_map.items() if node.code.startswith(code)),
                {'model': 'project.project', 'xml_id': 'project.act_project_project_2_project_task_all',
                 'menu_id': 'project.menu_projects'})
            model_name = mapping['model']
            xml_id = mapping['xml_id']
            menu_xml_id = mapping['menu_id']

            if node.name:
                object_ref = self.env[model_name].search([('name', '=', node.name)], limit=1)
            else:
                object_ref = False

            action_id = self._get_action_id(model_name, xml_id)
            menu_id = self._get_menu_id(menu_xml_id)

            if action_id and object_ref:
                record_url = f"http://localhost:8070/web#id={object_ref.id}&action={action_id}&model={model_name}&view_type=form&menu_id={menu_id}"
                click_lines.append(f'click {node.code} "{record_url}" "{model_name}"')
        mermaid_data = 'flowchart TD\n'
        mermaid_data += '\n'.join(node_lines) + '\n'
        mermaid_data += '\n'.join(edge_lines) + '\n'
        mermaid_data += '\n'.join(click_lines) + '\n'
        mermaid_data += '\n'.join(style_lines) + '\n'

        return mermaid_data

    @api.model
    def action_generate_diagram(self, project_id=None):
        mermaid_data = self._generate_mermaid_data(project_id)
        return mermaid_data

    def _generate_mermaid_timeline_data(self, project_id=None):
        timeline_nodes = self.search(
            [('active', '=', True), ('is_stage_node', '=', True), ('project_id', '=', project_id)])
        timeline_data = {}

        for node in timeline_nodes:
            month = node.date.strftime('%Y-%m')
            day = node.date.strftime('%Y-%m-%d')
            if month not in timeline_data:
                timeline_data[month] = {}
            if day not in timeline_data[month]:
                timeline_data[month][day] = []
            timeline_data[month][day].append(node.name)

        timeline_lines = []
        for month, days in timeline_data.items():
            timeline_lines.append(f'section {month}')
            for day, events in days.items():
                events_str = ' : '.join(events)
                timeline_lines.append(f'    {day} : {events_str}')

        mermaid_timeline_data = 'timeline\n    title Timeline\n'
        mermaid_timeline_data += '\n'.join(timeline_lines)
        return mermaid_timeline_data

    @api.model
    def action_generate_timeline(self, project_id=None):
        mermaid_timeline_data = self._generate_mermaid_timeline_data(project_id)
        return mermaid_timeline_data
