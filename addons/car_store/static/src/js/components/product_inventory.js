/** @odoo-module **/

import { Component, xml, useState, onWillStart } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";

export class ProductInventory extends Component {

    // Define the component's structure
static template = xml/*xml*/`
        <div class="o_owl_inventory mt-4">
            <t t-if="state.isLoading">
                <div class="alert alert-info text-center">Loading products...</div>
            </t>
            <t t-elif="state.error">
                <div class="alert alert-danger">Error: <t t-esc="state.error"/></div>
            </t>
            
            <t t-else="">
                <div class="row">
                    <t t-foreach="state.cars" t-as="car" t-key="car['id']">
                        <div class="col-lg-4 col-md-6 mb-4">
                            <div class="card h-100 shadow-sm">
                                <img 
                                    t-attf-src="/web/image?model=product.template&amp;id={{car['id']}}&amp;field=image_256"
                                    class="card-img-top img-fluid" 
                                    t-att-alt="car.name"
                                />
                                <div class="card-body">
                                    <h5 class="card-title text-primary" t-esc="car['name']"/>
                                    <p class="card-text text-success lead">
                                        Price: <span t-esc="this.formatPrice(car['list_price'], '$')"/>
                                    </p>
                                    <div class="text-muted small">
                                        <t t-esc="car.description_sale or 'No description provided.'"/>
                                    </div>
                                    <button class="btn btn-outline-primary btn-sm mt-3" t-on-click="() => this.addToCart(car['id'])">
                                        Add to Cart
                                    </button>
                                </div>
                            </div>
                        </div>
                    </t>
                </div>
            </t>
        </div>
    `;
    // State initialization (no more interface needed)
    setup() {
        this.state = useState({
            cars: [],
            isLoading: true,
            error: null,
        });
        onWillStart(this.fetchProducts);
    }

    async fetchProducts() {
        try {
            this.state.isLoading = true;
            // The JSON RPC call remains the same
            const data = await rpc("/api/products");
            console.log(data)
            this.state.cars = data;
        } catch (e) {
            console.error("Failed to load products:", e);
            this.state.error = "Could not load product data.";
        } finally {
            this.state.isLoading = false;
        }
    }

    formatPrice(price, currencySymbol) {
        return `${currencySymbol} ${price.toFixed(2)}`;
    }

    addToCart(productId) {
        console.log(`Product ID ${productId} added to cart!`);
    }
}