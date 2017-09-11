# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
import time
import openpyxl
from tempfile import TemporaryFile

class ContabilityIntegrationConfiguration(models.Model):
	_name='contability.integration.configuration'

	_rec_name = 'company_id'
	company_id = fields.Many2one('res.company', 'Empresa')
	journalCash_id = fields.Many2one('account.journal', 'Diario Efectivo', domain="[('type', 'in', ('bank', 'cash'))]")
	journalBank_id = fields.Many2one('account.journal', 'Diario Banco', domain="[('type', 'in', ('bank', 'cash'))]")
	journalCheck_id = fields.Many2one('account.journal', 'Diario Cheque', domain="[('type', 'in', ('bank', 'cash'))]")

class ContabilityIntegration(models.TransientModel):
	_name='contability.integration'

	name = fields.Char()
	date = fields.Date('Fecha', default=lambda *a: time.strftime('%Y-%m-%d'))
	company_id = fields.Many2one('res.company', 'Empresa')
	journalCash_id = fields.Many2one('account.journal', 'Diario Efectivo', domain="[('type', 'in', ('bank', 'cash'))]")
	journalBank_id = fields.Many2one('account.journal', 'Diario Banco', domain="[('type', 'in', ('bank', 'cash'))]")
	journalCheck_id = fields.Many2one('account.journal', 'Diario Cheque', domain="[('type', 'in', ('bank', 'cash'))]")
	account_id = fields.Many2one('account.account', 'Cuenta de ingreso')
	state = fields.Selection([('draft', 'Borrador'), ('open', 'Abierta'), ('confirm', 'Confirmada')], default='draft', string='Status', readonly=True, track_visibility='onchange')
	file = fields.Binary('Archivo')
	
	sum_cash = fields.Float('Total efectivo', default=0.00)
	count_cash = fields.Integer('Movimientos en efectivo', default=0)
	sum_bank = fields.Float('Total banco', default=0.00)
	count_bank = fields.Integer('Transferencias de banco', default=0)
	sum_check = fields.Float('Total cheques', default=0.00)
	count_check = fields.Integer('Cantidad de cheques', default=0)
	sum_total = fields.Float('Total')

	bank_moves = []
	cash_moves = []
	check_moves = []

	def create_move(self, fecha, recibo, familia, importe, tipo):
		print "---- create_move -----"
		print familia
		print fecha
		partner_pool = self.env['res.partner']
		partner_id = partner_pool.search([('name', '=', familia)])
		print "partner_id"
		print partner_id
		partner_id = partner_id[0]
		print "partner_id"
		print partner_id

		if partner_id == None:
			partner_obj = self.env['res.partner']
			partner_id = partner_obj.sudo(self.env.uid).create(dict(name=familia,))
		
		if tipo == 1:
			journal_move_id = self.journalCash_id
		elif tipo == 2:
			journal_move_id = self.journalBank_id
		elif tipo == 3:
			journal_move_id = self.journalCheck_id
		
		# Registramos la deuda de la familia
		aml = {
		    'date': fecha,
		    'account_id': partner_id.property_account_receivable_id.id,
		    'name':  recibo,
		    'partner_id': partner_id.id,
		    'debit': importe,
		}
		# Registramos el ingreso
		aml2 = {
		    'date': fecha,
		    'account_id': self.account_id.id,
		    'name':  recibo,
		    'partner_id': partner_id.id,
		    'credit': importe,
		}
		# Registramos incremento en caja/banco/cartera de cheques
		aml3 = {
		    'date': fecha,
		    'account_id': journal_move_id.default_debit_account_id.id,
		    'name':  recibo,
		    'partner_id': familia,
		    'debit': importe,
		}
		# Registramos el pago a la familia
		aml4 = {
		    'date': fecha,
		    'account_id': partner_id.property_account_receivable_id.id,
		    'name':  recibo,
		    'partner_id': partner_id.id,
		    'credit': importe,
		}
		line_ids = [(0, 0, aml), (0,0, aml2), (0,0, aml3), (0,0, aml4)]
		# create move
		move_name = "ingresos/" + partner_id.name
		company_id = self.env['res.users'].browse(self.env.uid).company_id.id

		move = self.env['account.move'].create({
		'name': move_name,
		'date': fecha,
		'journal_id': journal_move_id.id,
		'state':'draft',
		'company_id': company_id,
		'partner_id': partner_id.id,
		'line_ids': line_ids,
		})
		#move.state = 'posted'



	def import_excel(self):
		file = self.file.decode('base64')
		excel_fileobj = TemporaryFile('wb+')
		excel_fileobj.write(file)
		excel_fileobj.seek(0)
		# Create workbook
		workbook = openpyxl.load_workbook(excel_fileobj, data_only=True)
		# Get the first sheet of excel file
		sheet = workbook[workbook.get_sheet_names()[0]]
		#print sheet.get_highest_row()
		#last_selection = 'J' + str(sheet.get_highest_row())
		#selection = sheet['A5': last_selection]

		for row in sheet.rows:
			if row[0] != None and row[0] != 'Fecha':
				fecha = row[0].value
				recibo = row[1].value
				familia = row[2].value
				cod_cuenta = row[3].value
				tipo_cuenta = row[4].value
				importe = row[5].value
				emision = row[6].value
				acreditacion = row[7].value
				banco = row[8].value
				nro_cheque = row[9].value
				if row[3].value == 1:
					# Cash move
					self.cash_moves.append([fecha, recibo, familia, importe])
					self.sum_cash += importe
					self.count_cash += 1
				if row[3].value == 2:
					# Bank move
					self.bank_moves.append([fecha, recibo, familia, importe])
					self.sum_bank += importe
					self.count_bank += 1
				if row[3].value == 3:
					# Check move
					self.check_moves.append([fecha, recibo, familia, importe, emision,acreditacion, banco, nro_cheque])
					self.sum_check += importe
					self.count_check += 1

				self.sum_total = self.sum_cash + self.sum_bank + self.sum_check

	@api.one
	def validate(self):
		self.import_excel()
		self.state = 'open'
		return True
	
	@api.one
	def confirm(self):
		print "Confirm ***********************************"
		print self.cash_moves[0]
		self.create_move(self.cash_moves[0][0], self.cash_moves[0][1], self.cash_moves[0][2], self.cash_moves[0][3], 1)
		#self.state = 'draft'
		return True
