/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { formatFloat, formatFloatTime } from "@web/views/fields/formatters";
import { ProjectRightSidePanel } from '@project/components/project_right_side_panel/project_right_side_panel';

patch(ProjectRightSidePanel.prototype, {

    async onPhaseItemActionClick(_id) {
        return this.actionService.doAction({
                type: "ir.actions.act_window",
                res_model: 'project.phase',
                res_id: _id,
                views: [[false, "form"]],
                target: "current"
        });
    },

    async onPhaseItemActionListClick(_ids) {
        return this.actionService.doAction({
                type: "ir.actions.act_window",
                res_model: 'project.phase',
                views: [[false, "list"]],
                target: "current",
                domain: [["id", "in", _ids]]
        });
    },

    async onBudgetItemActionClick(_id) {
        return this.actionService.doAction({
                type: "ir.actions.act_window",
                res_model: 'project.budget',
                res_id: _id,
                views: [[false, "form"]],
                target: "current"
        });
    },

    async onBudgetItemActionListClick(_ids) {
        return this.actionService.doAction({
                type: "ir.actions.act_window",
                res_model: 'project.budget',
                views: [[false, "list"]],
                target: "current",
                domain: [["id", "in", _ids]]
        });
    },



});
