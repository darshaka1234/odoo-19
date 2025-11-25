from odoo import http
from odoo.http import request
import json

class ClientSideInventory(http.Controller):
    @http.route('/inventory-cars-2', type='http', auth='public', website=True)
    def render_owl_inventory_page(self, **kw):
        return request.render('car_store.main', {})

    @http.route('/api/products', type='json', auth='public')
    def get_products_data(self, **kw):
        cars = request.env['product.template'].sudo().search_read(
            [],
            ['name', 'list_price', 'categ_id', 'description_sale', 'website_ribbon_id'],
            order='name asc'
        )
        return cars