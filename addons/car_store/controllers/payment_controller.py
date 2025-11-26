from odoo import http
from odoo.http import request

class PaymentController(http.Controller):

    @http.route('/reserve/car', type='http', auth='public', website=True, methods=['POST'])
    def reserve_and_checkout(self, product_id, add_qty=1, **post):
        """
        Adds the specified car to the existing cart (without clearing it) and
        redirects the user directly to the checkout/payment page.
        """
        try:
            if request.env.user._is_public():
                # Optional: Handle public users if necessary
                pass

                # 2. Get the current Sale Order (cart) for the user
            order = request.website.sale_get_order(force_create=True)

            # 3. Add the new product to the cart (keeping any existing items)
            order._cart_update(
                product_id=int(product_id),
                add_qty=int(add_qty),
            )

            # 4. Redirect to the final payment/checkout step
            return request.redirect("/shop/checkout")

        except Exception as e:
            # Log the error for debugging
            request.env.cr.rollback()  # Ensure transaction is clean
            print(f"Error during car reservation: {e}")

            # Redirect back to the product page with an error message
            return request.redirect(f"/inventory-cars/{product_id}?reservation_error=true")