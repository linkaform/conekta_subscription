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
        # print 'eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeentra aquiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii'
        self.payment_model = self.env['account.payment']
        res = {}
        res['domain'] = {'cards_conekta':[("partner_id", "=", self.partner_id.id)]}
        # print 'reeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeees',res
        # return res




class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def action_invoice_open(self):
        # print 'eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeentra', dir(self.invoice_line_ids.subscription_id)
        subscription = self.invoice_line_ids.subscription_id.id
        auto_pay = self.invoice_line_ids.subscription_id.auto_pay

        # print 'suuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuubscription',subscription
        # print 'auuuuuuuuuuuuuuuuuuuuuuuuuuuuuutopaaaaaaaaaaaaaaaaaaaaaaaaay',auto_pay

        if subscription != False and auto_pay != False:
            # print 'eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeentra AAaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaqui'
            values = super(AccountInvoice, self).action_invoice_open()
            if self.number :
                res = self.conekta_payment_validate()
                print 'eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeentra AAaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaqui',  res
                if res == True:
                    pay = AccountPaymentConekta()
                    print 'aaaaaaaaaaaaaaaaaaaaaaaacoooooooooooooooouuuuunt', pay
                    payment = pay.action_validate_invoice_payment()
                    trans = self._create_payment_transaction()
                    # pay.payment_transaction_id = trans.id
                    # trans.state = 'done'
                else:
                    message = 'Message form your friends at Contekta \n'+self.error
                    raise ValidationError(message)
        else:
           res = super(AccountInvoice, self).action_invoice_open()
        #    print 'eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeentra'
        return False


    def _set_conketa_key(self):
        self.acquirer = self.env['payment.acquirer']

        environment = self.acquirer.search([('name','ilike','Conekta')])
        # print 'ennnnnnnnnnnnnnnnnnnviroooooooooonment', environment.environment

        if environment.environment == 'prod':
             CONEKTA_KEY = environment.conekta_secret_key
             CONEKTA_PUBLIC_KEY = environment.conekta_publishable_key
        else:
             CONEKTA_KEY = environment.conekta_secret_key_test
             CONEKTA_PUBLIC_KEY = environment.conekta_publishable_key_test

        conekta.api_key = CONEKTA_KEY
        conekta.api_version = CONEKTA_API_VERSION

        return True

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

    # def _create_payment(self):
    #     self.payment_env = self.env['account.payment']
    #     # payment_model = {
    #     #         'payment_type': 'inbound',
    #     #         'partner_type': 'customer',
    #     #         'partner_id': self.partner_id.id,
    #     #         'amount': self.amount_total,
    #     #         'currency_id': self.currency_id.id,
    #     #         'l10n_mx_edi_payment_method_id': self.l10n_mx_edi_payment_method_id.id,
    #     #         'communication': self.number
    #     #     }
    #     # print 'paaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaymeeeeeeeeeeeeeeeeeeeeeeeeeeent', payment_model
    #     print '****************************************DIR*******************************', dir(self.payment_env)

    #     res = self.payment_env.action_validate_invoice_payment()
    #     print 'paaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaymeeeeeeeeeeeeeeeeeeeeeeeeeeent', res
    #     return res

    @api.multi
    def conekta_payment_validate(self):
        card_token = self.invoice_line_ids.subscription_id.cards_conekta.conekta_card_id
        amount = self.amount_total
        currency = self.currency_id.name
        partner_id = self.partner_id
        invoice = self.number
        #print 'noooooooooooooooooooooooombre', invoice

        description="Linkaform Factura %s"%invoice

        conekta_object = {
                "currency":currency,
                "amount":amount * 100,
                "description":description,
                "reference_id": str(invoice) + ' ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
                "card":card_token,
                "pay_method": {'object': 'card_payment'}
        }
        # print 'sssssssssssssssssssssssssssssssellllllllllllllllllllllllllllllffffffffffffffffff', dir(self)
        print 'ooooooooooooooooooooooooooooooooooooooooooooooobjeeeeeeeeeeeto\n', conekta_object

        self._set_conketa_key()
        try:
          charge  = conekta.Charge.create(conekta_object)
          print 'chaaaaaaaaaaaaaaaaaaaaaargeeeeeeeeeeeeeeeeeeee',charge
        except conekta.ConektaError as e:
            # self.error = e.error_json['message_to_purchaser']
            self.communication ='Not Charge'
        else:
            return True

class AccountPaymentConekta(models.Model):
    _inherit = 'account.payment'

    def action_validate_invoice_payment(self):
        res = super(AccountPaymentConekta, self).action_validate_invoice_payment()
        print 'oooooooooooooooooooootra clllllllllllllase', res

        return False