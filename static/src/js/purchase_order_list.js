/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { kanbanView } from "@web/views/kanban/kanban_view";
import { ListController } from "@web/views/list/list_controller";
import { KanbanController } from "@web/views/kanban/kanban_controller";

export class PurchaseOrderListController extends ListController {
    setup() {
        super.setup();
    }
};

PurchaseOrderListController.components = {
    ...ListController.components,
};

export const PurchaseOrderListView = {
    ...listView,
    Controller: PurchaseOrderListController,
};

export class PurchaseOrderKanbanController extends KanbanController {
    setup() {
        super.setup();
    }
};

PurchaseOrderKanbanController.components = {
    ...KanbanController.components,
};

export const PurchaseOrderKanbanView = {
    ...kanbanView,
    Controller: PurchaseOrderKanbanController,
};

registry.category("views").add("purchase_order_search_list", PurchaseOrderListView);
registry.category("views").add("purchase_order_search_kanban", PurchaseOrderKanbanView);
