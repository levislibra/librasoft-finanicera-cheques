# -*- coding: utf-8 -*-

from openerp import models, fields, api
import time

class firmante(models.Model):
	_name = 'firmante'
	_description = 'Firmante del cheque'
	name = fields.Char("Nombre", size=30, required=True)
	cuit = fields.Char("Cuit", size=20, required=True)

class AccountCheck(models.Model):
    # This OpenERP object inherits from cheques.de.terceros
    # to add a new float field
    _inherit = 'account.check'
    _name = 'account.check'
    _description = 'Opciones extras de cheques para calculo del descuento'

    liquidacion_id = fields.Many2one('liquidacion', 'Liquidacion id')
    firmante_id = fields.Many2one('firmante', 'Firmante')

    fecha_acreditacion = fields.Date('Acreditacion')
    dias = fields.Integer(string='Dias')
    tasa_fija = fields.Float('% Fija')
    monto_fijo = fields.Float(string='Gasto', compute='_monto_fijo')
    tasa_mensual = fields.Float('% Mensual')
    monto_mensual = fields.Float(string='Interes', compute='_monto_mensual')
    vat_tax_id = fields.Many2one('account.tax', '% IVA')
    monto_iva = fields.Integer('IVA', compute='_monto_iva')
    monto_neto = fields.Float(string='Neto', compute='_monto_neto')

    @api.one
    @api.depends('monto_mensual', 'vat_tax_id')
    def _monto_iva(self):
        if self.vat_tax_id != None:
    	   self.monto_iva = self.monto_mensual * (self.vat_tax_id.amount / 100)

    @api.one
    @api.depends('amount', 'tasa_fija')
    def _monto_fijo(self):
    	self.monto_fijo = self.amount * (self.tasa_fija / 100)

    @api.one
    @api.depends('amount', 'tasa_mensual', 'dias')
    def _monto_mensual(self):
    	self.monto_mensual = self.dias * ((self.tasa_mensual / 30) / 100) * self.amount

    @api.one
    @api.depends('monto_fijo', 'monto_mensual', 'monto_iva')
    def _monto_neto(self):
    	self.monto_neto = self.amount - self.monto_fijo - self.monto_mensual - self.monto_iva

    @api.onchange('firmante_id')
    def _set_name_cuit(self):
    	print('names')
    	self.owner_name = self.firmante_id.name
    	self.owner_vat = self.firmante_id.cuit
    	if (self.owner_vat != False and self.owner_name != False):
    		self.name = self.owner_name + " " + self.owner_vat
    	print self.liquidacion_id
        if (self.liquidacion_id.journal_id != False):
        	self.journal_id = self.liquidacion_id.journal_id

    @api.onchange('payment_date')
    def _fecha_acreditacion(self):
        print("payment_date change")
        self.fecha_acreditacion = self.payment_date

class Liquidacion(models.Model):
	_name = 'liquidacion'

	id = fields.Integer('Nro Liquidacion')
	fecha_liquidacion = fields.Date('Fecha', required=True, default=lambda *a: time.strftime('%Y-%m-%d'))
	active = fields.Boolean('Activa', default=True)
	partner_id = fields.Many2one('res.partner', 'Cliente', required=True)
	journal_id = fields.Many2one('account.journal', 'Diario', required=True)
	analytic_id = fields.Many2one('account.analytic.account', 'Cuenta analítica')
	move_id = fields.Many2one('account.move', 'Asiento', readonly=True)
	invoice_id = fields.Many2one('account.invoice', 'Factura', readonly=True)
	cheques_ids = fields.One2many('account.check', 'liquidacion_id', 'Cheques', ondelete='cascade')
	state = fields.Selection([('cotizacion', 'Cotizacion'), ('confirmada', 'Confirmada'), ('pagado', 'Pagado'), ('cancelada', 'Cancelada')], default='cotizacion', string='Status', readonly=True, track_visibility='onchange')

	@api.onchange('journal_id')
	def _set_journal_id(self):
		for cheque in self.cheques_ids:
			cheque.journal_id = self.journal_id
			print("cheque Nro %r", cheque.number)
			print("set journal")

	def confirmar(self, cr, uid, ids, context=None):
		self.write(cr, uid, ids, {'state':'confirmada'}, context=None)
		return True

	def editar(self, cr, uid, ids, context=None):
		self.write(cr, uid, ids, {'state':'cotizacion'}, context=None)
		return True

#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100