# -*- coding: utf-8 -*-
from openerp import models, fields, api
import time

class ContabilityIntegrationConfiguration(models.Model):
	_name='contability.integration.configuration'

	_rec_name = 'company_id'
	company_id = fields.Many2one('res.company', 'Empresa')
	journalCash_id = fields.Many2one('account.journal', 'Diario Efectivo', domain="[('type', 'in', ('bank', 'cash'))]")
	journalBank_id = fields.Many2one('account.journal', 'Diario Banco', domain="[('type', 'in', ('bank', 'cash'))]")
	journalCheck_id = fields.Many2one('account.journal', 'Diario Cheque', domain="[('type', 'in', ('bank', 'cash'))]")


class ContabilityIntegration(models.Model):
	_name='contability.integration'

	name = fields.Char()
	date = fields.Date('Fecha')
	company_id = fields.Many2one('res.company', 'Empresa')
	journalCash_id = fields.Many2one('account.journal', 'Diario Efectivo', domain="[('type', 'in', ('bank', 'cash'))]")
	journalBank_id = fields.Many2one('account.journal', 'Diario Banco', domain="[('type', 'in', ('bank', 'cash'))]")
	journalCheck_id = fields.Many2one('account.journal', 'Diario Cheque', domain="[('type', 'in', ('bank', 'cash'))]")
	state = fields.Selection([('draft', 'Borrador'), ('open', 'Abierta'), ('confirm', 'Confirmada')], default='draft', string='Status', readonly=True, track_visibility='onchange')
