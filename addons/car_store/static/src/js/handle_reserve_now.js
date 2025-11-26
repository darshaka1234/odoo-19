/** @odoo-module **/

// We use the Bootstrap 5 Modal API, which is guaranteed to be available in Odoo's frontend assets.

const CART_BUTTON_SELECTOR = '.js_add_to_cart_btn';
const MODAL_ID = 'cartModal';
const MODAL_NAME_ELEMENT_ID = 'modal-product-name';
const MODAL_ID_ELEMENT_ID = 'modal-product-id';
/**
 * Handles the click event on the Add to Cart button to show a confirmation modal.
 * This simulates the cart addition process on the client side for visual feedback.
 * @param {Event} event - The click event object.
 */
function handleAddToCartClick(event) {
    const button = event.currentTarget;
    const productId = button.dataset.productId;
    const productName = button.dataset.productName;

    // 1. (Simulated) Backend Call: In a real scenario, you'd make an RPC/AJAX call here
    console.log(`[SSR Handler] Simulating RPC call to add Product ID ${productId} to cart...`);

    // 2. Prepare the Modal Content
    const modalNameEl = document.getElementById(MODAL_NAME_ELEMENT_ID);
    const modalIdEl = document.getElementById(MODAL_ID_ELEMENT_ID);

    if (modalNameEl) {
        modalNameEl.textContent = productName || 'The item';
    }
    if (modalIdEl) {
        modalIdEl.textContent = `Product ID: ${productId}`;
    }

    // 3. Show the Modal using Bootstrap's native Modal API
    const cartModalElement = document.getElementById(MODAL_ID);
    if (cartModalElement && window.bootstrap && window.bootstrap.Modal) {
        const cartModal = new window.bootstrap.Modal(cartModalElement);
        cartModal.show();
    } else if (cartModalElement) {
        // Fallback or warning if Bootstrap JS is not loaded
        console.warn("Bootstrap Modal JS not found. Cannot show modal.");
    }
}

/**
 * Initializes event listeners after the DOM is fully loaded.
 */
(function () {
    const cartButtons = document.querySelectorAll(CART_BUTTON_SELECTOR);
    console.log('listening...')
    console.log(cartButtons);

    if (cartButtons.length > 0) {
        cartButtons.forEach(button => {
            button.addEventListener('click', handleAddToCartClick);
        });
        console.log(`[SSR Handler] Added click listener to ${cartButtons.length} 'Add to Cart' button(s).`);
    } else {
        console.log("[SSR Handler] No 'Add to Cart' buttons found.");
    }
})()
