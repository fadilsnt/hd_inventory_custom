/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PurchaseDashBoard } from "@purchase/views/purchase_dashboard";
import { DateSearch } from "./purchase_date_search";

// pastikan components ada
PurchaseDashBoard.components ??= {};

patch(PurchaseDashBoard.components, {
    DateSearch,
});

patch(PurchaseDashBoard.prototype, {
    setup() {
        super.setup?.();
        this.purchase_order_search = true;
    },
});
