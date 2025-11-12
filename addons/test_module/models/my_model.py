from odoo import models, fields

class Student(models.Model):
    _name = 'school.student'
    _description = 'Student'

    name = fields.Char(string='Name', required=True)
    age = fields.Integer(string='Age')
    email = fields.Char(string='Email')
