/** @odoo-module **/

import { whenReady } from "@odoo/owl";
import { mountComponent } from "@web/env";
import { ProductInventory } from "./components/product_inventory";

function start() {
    const target = document.getElementById("owl_inventory_root");
    whenReady(() => mountComponent(ProductInventory, target));
}

start();