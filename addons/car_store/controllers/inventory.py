from odoo import http
from odoo.http import request

class Inventory(http.Controller):
    @http.route('/inventory-cars', type='http', auth='public', website=True)
    def render_inventory_cars(self, **kw):
        cars = request.env['product.template'].sudo().search_read(
            [],
            ['name', 'list_price', 'categ_id', 'description_sale', 'website_ribbon_id'],
            order='name asc'
        )
        print(cars)
        values = {
            'cars': cars,
            'page_title': "Car Inventory",
        }

        return request.render('car_store.inventory', values)
