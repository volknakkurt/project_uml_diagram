/** @odoo-module **/

import { registry } from "@web/core/registry";
import { loadJS } from '@web/core/assets';
import { useService } from "@web/core/utils/hooks";
const { Component, useRef, onMounted, onWillStart } = owl;

export class UmlDiagram extends Component {
    setup() {
        this.mermaidRef = useRef('uml-container');
        this.orm = useService("orm");
        this.actionService = useService("action")

        this.active_id = this.props.action.context.active_id

        onWillStart(async ()=>{
            await loadJS('https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js');
            mermaid.initialize({ startOnLoad: true });
        });

        onMounted(()=> this.renderDiagram());

    }

    async renderDiagram() {
        const project_id =this.props.action.context.active_id
        const mermaidData = await this.orm.call('project.node', 'action_generate_diagram', [project_id]);

        const container = this.mermaidRef.el;
        container.innerHTML = `%%{
              init: {
                'theme': 'base',
                'themeVariables': {
                  'primaryColor': '#B7DAE4',
                  'primaryTextColor': '#545342',
                  'primaryBorderColor': '#e8e8e8',
                  'lineColor': '#333333',
                  'secondaryColor': '#006100',
                  'tertiaryColor': '#cfcfcf'
                }
              }
            }%%\n${mermaidData}`;

        mermaid.init(undefined, container);
    }

    async changeToTimelinePage() {
        await this.actionService.doAction({
            type: 'ir.actions.client',
            tag: 'owl.timeline_diagram',
            context: {
            'active_id': this.props.action.context.active_id,
            }
        });
    }

}
UmlDiagram.template = "owl.UmlDiagram"

registry.category("actions").add("owl.uml_diagram", UmlDiagram);
