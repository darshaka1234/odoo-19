from odoo import http
from odoo.http import request

class HelloWorldPage(http.Controller):
    @http.route('/hello', type='http', auth='public', website=True)
    def render_hello_world(self, **kw):
        values = {
            'message': "Hello World!",
            'page_title': "My First Coded Page",
        }

        return request.render('car_store.hello_world_template', values)