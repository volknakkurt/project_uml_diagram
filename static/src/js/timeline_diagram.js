/** @odoo-module **/

import { registry } from "@web/core/registry";
import { loadJS } from '@web/core/assets';
import { useService } from "@web/core/utils/hooks";
const { Component, useRef, onMounted, onWillStart } = owl;

export class TimelineDiagram extends Component {
    setup() {
        this.timelineRef = useRef('timeline-container');
        this.orm = useService("orm");
        this.actionService = useService("action")

        this.active_id = this.props.action.context.active_id

        onWillStart(async ()=>{
            await loadJS('https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js');
            mermaid.initialize({ startOnLoad: true });
        });

        onMounted(() => this.renderTimeline());
    }

    async renderTimeline() {
        const container = this.timelineRef.el;

        const project_id =this.props.action.context.active_id
        const response = await this.orm.call('project.node', 'action_generate_timeline', [project_id]);

        const mermaidTimelineData = response;

        container.innerHTML = `%%{init: { 'logLevel': 'debug', 'theme': 'neutral' } }%%\n${mermaidTimelineData}`;
        mermaid.init(undefined, container);

    }
    async changeToUmlPage() {

        await this.actionService.doAction({
            type: 'ir.actions.client',
            tag: 'owl.uml_diagram',
            context: {
            'active_id': this.props.action.context.active_id,
            }
        });
    }
}

TimelineDiagram.template = "owl.TimelineDiagram";

registry.category("actions").add("owl.timeline_diagram", TimelineDiagram);
