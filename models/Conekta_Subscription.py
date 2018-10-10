# -*- coding: utf-8 -*-


import logging, datetime

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


try:
    import conekta
except ImportError as err:
    print 'No se pudo installar el modulo, favor de instalar api de conekta ver README'
    _logger.debug(err)

CONEKTA_API_VERSION = "0.3.0"

class ConektaSubscriptions(models.Model):
    _inherit = 'sale.subscription'

    acquirer = fields.Many2one(comodel_name='payment.acquirer', string='Aquirer')
    cards_conekta = fields.Many2one(comodel_name='conekta.credit.card', domain= lambda self:self._get_domain(),string="Conekta Credit Card")
    auto_pay = fields.Boolean(string="Pagar automaticamente")

    @api.multi
    @api.onchange('partner_id')
    def _get_domain(self):
        self.payment_model = self.env['account.payment']
        res = {}
        res['domain'] = {'cards_conekta':[("partner_id", "=", self.partner_id.id)]}
        # return res




class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    error = fields.Char()

    @api.multi
    def action_invoice_paid(self):
        res = super(AccountInvoice, self).action_invoice_paid()
        return res


    def action_invoice_open(self):
        subscription = self.invoice_line_ids.subscription_id.id
        auto_pay = self.invoice_line_ids.subscription_id.auto_pay
        card = self.invoice_line_ids.subscription_id.cards_conekta

        if subscription != False and auto_pay != False:
            values = super(AccountInvoice, self).action_invoice_open()
            if self.number :
                res = self.conekta_payment_validate()
                if res == True:
                    pay = self._create_payment()
                    invoice = self.search_factura(self.id)
                    reconcile = self.reconcile_invoice_with_payment(invoice,pay.id)
                    trans = self._create_payment_transaction()

                else:
                    message = 'Message form your friends at Contekta \n'+self.error
                    raise ValidationError(message)
        else:
           res = super(AccountInvoice, self).action_invoice_open()
        return False

    @api.model
    def search_factura(self,invoice_id):
        invoice_brw = self.env['account.invoice'].browse(invoice_id)
        return invoice_brw



    def _set_conketa_key(self):
        self.acquirer = self.env['payment.acquirer']

        environment = self.acquirer.search([('name','ilike','Conekta')])

        if environment.environment == 'prod':
             CONEKTA_KEY = environment.conekta_secret_key
             CONEKTA_PUBLIC_KEY = environment.conekta_publishable_key
        else:
             CONEKTA_KEY = environment.conekta_secret_key_test
             CONEKTA_PUBLIC_KEY = environment.conekta_publishable_key_test

        conekta.api_key = CONEKTA_KEY
        conekta.api_version = CONEKTA_API_VERSION

        return True

    @api.model
    def _create_payment_transaction(self):
        self.payment_model = self.env['payment.transaction']
        transaction_model = {
                'reference': self.number,
                'invoice_id': self.id,
                'amount': self.amount_total,
                'currency_id': self.currency_id.id,
                'partner_id': self.partner_id.id,
                'acquirer_id': self.invoice_line_ids.subscription_id.acquirer.id,
                'fees': (self.amount_total * 2.9)/100
            }
        # print 'transaction', transaction_model

        transaction = self.payment_model.create(transaction_model)
        # print 'transaction', transaction
        return transaction

    @api.model
    def reconcile_invoice_with_payment(self, invoice_brw, payment_id):
        payment_credit_id = 0
        payment_brw = self.env["account.payment"].browse(payment_id)
        print ' \n \n reconcileeeeeeeeeeeeeeeeeeeeeeeeee \n \n', payment_brw
        for line in payment_brw.move_line_ids:
            if line.credit > 0.00:
                payment_credit_id = line.id
        invoice_brw.assign_outstanding_credit(payment_credit_id)
        invoice_brw.action_invoice_paid()
        return True

    @api.model
    def _create_payment(self):
        payment_env = self.env['account.payment']
        if self.currency_id.name == 'USD':
            journal = 13
        else:
            journal = 11
        payment_model = {
                'payment_method_id': 1,
                'payment_type': 'inbound',
                'journal_id': journal,
                'partner_type': 'customer',
                'partner_id': self.partner_id.id,
                'amount': self.amount_total,
                'currency_id': self.currency_id.id,
                'l10n_mx_edi_payment_method_id': self.l10n_mx_edi_payment_method_id.id,
                'communication': self.number
            }

        res = payment_env.create(payment_model)
        return res

    @api.multi
    def conekta_payment_validate(self):
        card_token = self.invoice_line_ids.subscription_id.cards_conekta.conekta_card_id
        amount = self.amount_total
        currency = self.currency_id.name
        partner_id = self.partner_id
        invoice = self.number

        description="Linkaform Factura %s"%invoice

        conekta_object = {
                "currency":currency,
                "amount":amount * 100,
                "description":description,
                "reference_id": str(invoice) + ' ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
                "card":card_token,
                "pay_method": {'object': 'card_payment'}
        }

        self._set_conketa_key()
        try:
          charge  = conekta.Charge.create(conekta_object)
        except conekta.ConektaError as e:
            self.error = e.error_json['message_to_purchaser']
            self.communication ='Not Charge'
        else:
            return True