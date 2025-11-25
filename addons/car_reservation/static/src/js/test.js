/** @odoo-module */

import publicWidget from "@web/legacy/js/public/public_widget";

export const ReserveButton = publicWidget.Widget.extend({
    // Selector for your new button within the product page
    selector: '#product_details',

    // Events mapping: {event_name selector: handler_method}
    events: {
        'click #reserve_now_btn': '_onClickReserveNow',
    },

    /**
     * Click handler for the 'Reserve Now' button.
     * @param {Event} ev
     */
    _onClickReserveNow: function (ev) {
        // Prevent default navigation if 'href="#"' is used
        ev.preventDefault();

// --- 1. Identify the Main Form ---
        // The product details are contained within the main product form
        const $productForm = this.$el.find('form.js_product_details');
        console.log($productForm);

        if (!$productForm.length) {
            console.error("Product form not found.");
            return;
        }

        // --- 2. Extract Key Product Information ---

        // A. Product ID (The actual variant ID currently selected)
        const productID = $productForm.find('input[name="product_id"]').val();

        // B. Product Template ID (The base product ID)
        // This is often needed for server-side logic
        const productTemplateID = $productForm.find('input[name="product_template_id"]').val();

        // C. Quantity
        const quantity = $productForm.find('input[name="add_qty"]').val();

        // D. Attributes (Selections like size, color, etc.)
        // Odoo uses hidden input fields or selectors for attributes.
        // We can serialize the form to easily grab all these inputs.
        // The form includes the product_id, product_template_id, and add_qty by default.
        const formData = $productForm.serializeArray();

        // --- 3. Log and Prepare Payload ---
        console.log("--- Product Data Extracted ---");
        console.log(`Product Template ID: ${productTemplateID}`);
        console.log(`Variant ID (product_id): ${productID}`);
        console.log(`Quantity: ${quantity}`);
        console.log("All Form Data:", formData);


        // --- 4. Perform Custom Reservation Logic (RPC Call Example) ---

        // Convert array data to a simple object for the RPC payload
        const payload = {};
        formData.forEach(item => {
            payload[item.name] = item.value;
        });

        // --- Your Custom Logic Goes Here ---
        // 1. Get Product ID/Quantity: You'll typically need to traverse the DOM
        //    to find the necessary product information like:
        //    const $form = this.$el.find('#product_details form.js_product_details');
        //    const productID = $form.find('input[name="product_id"]').val();

        // 2. Perform an action (e.g., an RPC call to a custom controller):
        //    this._rpc({
        //        route: '/shop/reserve',
        //        params: {
        //            product_id: productID,
        //            // ... other data (e.g., variant attributes)
        //        },
        //    }).then(function (result) {
        //        // Handle the server response (e.g., show a modal, redirect)
        //        console.log("Reservation successful:", result);
        //    });
        // ------------------------------------

        // Optional: Add a visual effect while processing
        // this.$('#reserve_now_btn').addClass('disabled');
    },
});

// Register the widget in the public widgets registry
publicWidget.registry.ReserveButton = ReserveButton;

// Optional: If you want to replace/extend the existing `website_sale` widget,
// you would import it and then extend it, but for a new button, a new widget is cleaner.