/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { ProjectRightSidePanel } from '@project/components/project_right_side_panel/project_right_side_panel';
import { useService } from "@web/core/utils/hooks";

patch(ProjectRightSidePanel.prototype, {
    setup() {
        super.setup();
        this.state.active_id = this.props.context.active_id
        this.action = useService('action');
    },

    triggerUmlDiagramAction() {

        const active_id = this.props.context.active_id

        this.action.doAction('project_update_management.action_uml_component', {
            additionalContext: {
                active_id: active_id,
            }
        });
    },

    triggerTimelineDiagramAction() {

        const active_id = this.props.context.active_id

        this.action.doAction('project_update_management.action_timeline_component', {
            additionalContext: {
                active_id: active_id,
            }
        });
    },

});
