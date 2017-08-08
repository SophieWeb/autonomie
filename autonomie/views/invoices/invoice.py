# -*- coding: utf-8 -*-
# * Copyright (C) 2012-2013 Croissance Commune
# * Authors:
#       * Arezki Feth <f.a@majerti.fr>;
#       * Miotte Julien <j.m@majerti.fr>;
#       * Pettier Gabriel;
#       * TJEBBES Gaston <g.t@majerti.fr>
#
# This file is part of Autonomie : Progiciel de gestion de CAE.
#
#    Autonomie is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Autonomie is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Autonomie.  If not, see <http://www.gnu.org/licenses/>.
#

"""
    Invoice views
"""
import logging
import datetime

from pyramid.httpexceptions import HTTPFound
from colanderalchemy import SQLAlchemySchemaNode

from autonomie.models.task import (
    Invoice,
)
from autonomie_base.utils.date import format_date
from autonomie.utils.strings import format_amount

from autonomie.utils.widgets import ViewLink
from autonomie.forms.tasks.invoice import (
    get_payment_schema,
)
from autonomie.views import (
    BaseEditView,
    BaseFormView,
    submit_btn,
    cancel_btn,
)
from autonomie.views.files import FileUploadView
from autonomie.views.sage import SageSingleInvoiceExportPage

from autonomie.views.task.views import (
    TaskAddView,
    TaskEditView,
    TaskDeleteView,
    TaskHtmlView,
    TaskPdfView,
    TaskDuplicateView,
)


logger = log = logging.getLogger(__name__)


class InvoiceAddView(TaskAddView):
    """
    Invoice add view
    context is a project
    """
    title = "Nouvelle facture"
    factory = Invoice

    def _more_init_attributes(self, invoice, appstruct):
        """
        Add Invoice's specific attribute while adding this task
        """
        invoice.course = appstruct['course']
        invoice.financial_year = datetime.date.today().year
        invoice.prefix = self.request.config.get('invoiceprefix', '')
        return invoice

    def _after_flush(self, invoice):
        """
        Launch after the new invoice has been flushed
        """
        logger.debug(
            "  + Invoice successfully added : {0}".format(invoice.id)
        )


class InvoiceEditView(TaskEditView):

    def title(self):
        return u"Modification de la facture {task.name}".format(
            task=self.context
        )


class InvoiceDeleteView(TaskDeleteView):
    msg = u"La facture {context.name} a bien été supprimé."

    def pre_delete(self):
        """
        If an estimation is attached to this invoice, ensure geninv is set to
        False
        """
        if self.context.estimation is not None:
            if len(self.context.estimation.invoices) == 1:
                self.context.estimation.geninv = False
                self.request.dbsession.merge(self.context.estimation)


class InvoiceHtmlView(TaskHtmlView):
    label = u"Facture"


class InvoiceDuplicateView(TaskDuplicateView):
    label = u"la facture"


class InvoicePdfView(TaskPdfView):
    pass


def gencinv_view(context, request):
    """
    Cancelinvoice generation view
    """
    try:
        cancelinvoice = context.gen_cancelinvoice(request.user)
        request.dbsession.add(cancelinvoice)
        request.dbsession.flush()
    except:
        logger.exception(
            u"Error while generating a cancelinvoice for {0}".format(
                context.id
            )
        )
        request.session.flash(
            u"Erreur à la génération de votre avoir, "
            u"contactez votre administrateur",
            'error'
        )
        return HTTPFound(request.route_path("/invoices/{id}", id=context.id))
    return HTTPFound(
        request.route_path("/cancelinvoices/{id}", id=cancelinvoice.id)
    )


class InvoiceSetTreasuryiew(BaseEditView):
    """
    View used to set treasury related informations

    context

        An invoice

    perms

        set_treasury.invoice
    """
    factory = Invoice
    schema = SQLAlchemySchemaNode(
        Invoice,
        includes=('prefix', 'financial_year',),
        title=u"Modifier l'année fiscale de référence et le préfixe "
        u"du numéro de facture",
    )

    def before(self, form):
        BaseEditView.before(self, form)
        self.request.actionmenu.add(
            ViewLink(
                label=u"Retour à la facture",
                path="/invoices/{id}.html",
                id=self.context.id,
                _anchor="treasury",
            )
        )

    @property
    def title(self):
        return u"Facture numéro {0} en date du {1}".format(
            self.context.official_number,
            format_date(self.context.date),
        )


# def get_paid_form(request, counter=None):
#     """
#         Return a payment form
#     """
#     valid_btn = Button(
#         name='submit',
#         value="paid",
#         type='submit',
#         title=u"Valider",
#     )
#     schema = get_payment_schema(request).bind(request=request)
#     action = request.route_path(
#         "/invoices/{id}/addpayment",
#         id=request.context.id,
#         _query=dict(action='payment')
#     )
#     form = Form(
#         schema=schema,
#         buttons=(valid_btn,),
#         action=action,
#         counter=counter,
#     )
#     return form
#
#
# def get_set_products_form(request, counter=None):
#     """
#         Return a form used to set products reference to :
#             * invoice lines
#             * cancelinvoice lines
#     """
#     schema = SetProductsSchema().bind(request=request)
#     action = request.route_path(
#         "/%ss/{id}/set_products" % request.context.type_,
#         id=request.context.id,
#     )
#     valid_btn = Button(
#         name='submit',
#         value="set_products",
#         type='submit',
#         title=u"Valider"
#     )
#     form = Form(schema=schema, buttons=(valid_btn,), action=action,
#                 counter=counter)
#     return form
#
#
# def add_lines_to_invoice(task, appstruct):
#     """
#         Add the lines to the current invoice
#     """
#     # Needed for edition only
#     task.default_line_group.lines = []
#     task.line_groups = [task.default_line_group]
#     task.discounts = []
#
#     for group in appstruct['groups']:
#         lines = group.pop('lines', [])
#         group = TaskLineGroup(**group)
#         for line in lines:
#             group.lines.append(TaskLine(**line))
#         task.line_groups.append(group)
#     for line in appstruct['lines']:
#         task.default_line_group.lines.append(TaskLine(**line))
#
#     for line in appstruct.get('discounts', []):
#         task.discounts.append(DiscountLine(**line))
#
#     return task
#
#
# class InvoiceFormActions(TaskFormActions):
#     """
#     The form actions class specific to invoices
#     """
#
#     def _set_financial_year_form(self):
#         """
#             Return the form for setting the financial year of a document
#         """
#         form = get_set_financial_year_form(self.request, self.formcounter)
#         form.set_appstruct(
#             {
#                 'financial_year': self.context.financial_year,
#                 'prefix': self.context.prefix,
#             }
#         )
#         self.formcounter = form.counter
#         return form
#
#     def _set_financial_year_btn(self):
#         """
#             Return the button for the popup with the financial year set form
#             of the current document
#         """
#         if context_is_task(self.context):
#             title = u"Année comptable de référence"
#             form = self._set_financial_year_form()
#             popup = PopUp(
#                 "set_financial_year_form_container",
#                 title,
#                 form.render(),
#             )
#             self.request.popups[popup.name] = popup
#             yield popup.open_btn(css='btn btn-primary')
#
#     def _set_products_form(self):
#         """
#             Return the form for configuring the products for each lines
#         """
#         form = get_set_products_form(self.request, self.formcounter)
#         form.set_appstruct(
#             {
#                 'lines': [
#                     line.appstruct() for line in self.context.all_lines
#                 ]
#             }
#         )
#         self.formcounter = form.counter
#         return form
#
#     def _set_products_btn(self):
#         """
#             Popup fire button
#         """
#         title = u"Configuration des produits"
#         form = self._set_products_form()
#         popup = PopUp("set_products_form", title, form.render())
#         self.request.popups[popup.name] = popup
#         yield popup.open_btn(css='btn btn-primary')
#
#     def _paid_form(self):
#         """
#             return the form for payment registration
#         """
#         form = get_paid_form(self.request, self.formcounter)
#         appstruct = []
#         for tva_value, value in self.context.topay_by_tvas().items():
#             tva = Tva.by_value(tva_value)
#             appstruct.append({'tva_id': tva.id, 'amount': value})
#             form.set_appstruct({'tvas': appstruct})
#
#         self.formcounter = form.counter
#         return form
#
#     def _paid_btn(self):
#         """
#             Return a button to set a paid btn and a select to choose
#             the payment mode
#         """
#
#         if self.request.has_permission("add_payment.invoice"):
#             form = self._paid_form()
#             title = u"Notifier un paiement"
#             popup = PopUp("paidform", title, form.render())
#             self.request.popups[popup.name] = popup
#             yield popup.open_btn(css='btn btn-primary')
#
#     def _aboinv_btn(self):
#         """
#             Return a button to abort an invoice
#         """
#         yield Submit(
#             u"Annuler cette facture",
#             value="aboinv",
#             request=self.request,
#             confirm=u"Êtes-vous sûr de vouloir annuler cette facture ?"
#         )
#
#     def _gencinv_btn(self):
#         """
#             Return a button for generating a cancelinvoice
#         """
#         if self.request.context.topay() != 0:
#             yield Submit(
#                 u"Générer un avoir",
#                 value="gencinv",
#                 request=self.request,
#             )
#
#
# class CommonInvoiceStatusView(TaskStatusView):
#     """
#         Handle the invoice status processing
#         Is called when the status btn from the html view or
#         the edit view are pressed
#
#         context is an invoice
#     """
#
#     def redirect(self):
#         project_id = self.request.context.project.id
#         return HTTPFound(self.request.route_path('project', id=project_id))
#
#     def pre_set_products_process(self, task, status, params):
#         """
#             Pre processed method for product configuration
#         """
#         log.debug(u"+ Setting products for an invoice (pre-step)")
#         form = get_set_products_form(self.request)
#         appstruct = form.validate(params.items())
#         log.debug(appstruct)
#         return appstruct
#
#     def post_set_products_process(self, task, status, invoice):
#         log.debug(u"+ Setting products for an invoice (post-step)")
#         invoice = self.request.dbsession.merge(invoice)
#         log.debug(
#             u"Configuring products for {context.__name__} :{context.id}".
#             format(context=invoice)
#         )
#         msg = u"Les codes produits ont bien été configurés"
#         self.request.session.flash(msg)
#
#     def pre_gencinv_process(self, task, status, params):
#         params = dict(params.items())
#         params['user'] = self.request.user
#         return params
#
#     def pre_set_financial_year_process(self, task, status, params):
#         """
#             Handle form validation before setting the financial year of
#             the current task
#         """
#         form = get_set_financial_year_form(self.request)
#         # if an error is raised here, it will be cached a level higher
#         appstruct = form.validate(params.items())
#         log.debug(u" * Form has been validated")
#         return appstruct
#
#     def post_set_financial_year_process(self, task, status, params):
#         invoice = params
#         invoice = self.request.dbsession.merge(invoice)
#         log.debug(u"Set financial year and prefix of the invoice :{0}".format(
#             invoice.id))
#         msg = u"Le document a bien été modifié"
#         msg = msg.format(self.request.route_path(
#             "/invoices/{id}.html", id=invoice.id
#         ))
#         self.request.session.flash(msg)
#
#
# class InvoiceStatusView(CommonInvoiceStatusView):
#     def pre_paid_process(self, task, status, params):
#         """
#             Validate a payment form's data
#         """
#         form = get_paid_form(self.request)
#         # We don't try except on the data validation, since this is done in the
#         # original wrapping call (see taskaction set_status)
#         appstruct = form.validate(params.items())
#
#         if 'amount' in appstruct:
#             # Les lignes de facture ne conservent pas le lien avec les objets
#             # Tva, ici on en a une seule, on récupère l'objet et on le set sur
#             # le amount
#             appstruct['tva_id'] = Tva.by_value(
#                 self.context.get_tvas().keys()[0]
#             ).id
#
#         elif 'tvas' in appstruct:
#             # Ce champ ne servait que pour tester las somme des valeurs saisies
#             appstruct.pop('payment_amount')
#             # si on a plusieurs tva :
#             for tva_payment in appstruct['tvas']:
#                 remittance_amount = appstruct['remittance_amount']
#                 tva_payment['remittance_amount'] = remittance_amount
#                 tva_payment['date'] = appstruct['date']
#                 tva_payment['mode'] = appstruct['mode']
#                 tva_payment['bank_id'] = appstruct.get('bank_id')
#                 tva_payment['resulted'] = appstruct.get('resulted', False)
#         else:
#             raise Exception(u"On a rien à faire ici")
#
#         logger.debug(u"In pre paid process")
#         logger.debug(u"Returning : {0}".format(appstruct))
#         return appstruct
#
#     def post_valid_process(self, task, status, params):
#         msg = u"La facture porte le numéro <b>{0}</b>"
#         self.session.flash(msg.format(task.official_number))
#
#     def post_gencinv_process(self, task, status, params):
#         cancelinvoice = params
#         cancelinvoice = self.request.dbsession.merge(cancelinvoice)
#         self.request.dbsession.flush()
#         id_ = cancelinvoice.id
#         log.debug(u"Generated cancelinvoice {0}".format(id_))
#         msg = u"Un avoir a été généré, vous pouvez le modifier \
# <a href='{0}'>Ici</a>."
#         msg = msg.format(
#             self.request.route_path(
#                 "/cancelinvoices/{id}.html", id=id_
#             )
#         )
#         self.session.flash(msg)
#
#     def post_duplicate_process(self, task, status, params):
#         invoice = params
#         invoice = self.request.dbsession.merge(invoice)
#         self.request.dbsession.flush()
#         id_ = invoice.id
#         log.debug(u"Duplicated invoice : {0}".format(id_))
#         msg = u"La facture a bien été dupliquée, vous pouvez le modifier \
# <a href='{0}'>Ici</a>."
#         msg = msg.format(
#             self.request.route_path(
#                 "/invoices/{id}.html", id=id_
#             )
#         )
#         self.request.session.flash(msg)
#
#

class InvoicePaymentView(BaseFormView):
    buttons = (submit_btn, cancel_btn)
    add_template_vars = ('help_message',)

    @property
    def help_message(self):
        return (
            u"Enregistrer un paiement pour la facture {0} dont le montant "
            u"ttc restant à payer est de {1} €".format(
                self.context.official_number,
                format_amount(self.context.topay(), precision=5)
            )
        )

    @property
    def schema(self):
        return get_payment_schema(self.request).bind(request=self.request)

    @schema.setter
    def schema(self, value):
        """
        A setter for the schema property
        The BaseClass in pyramid_deform gets and sets the schema attribute that
        is here transformed as a property
        """
        self._schema = value

    @property
    def title(self):
        return (
            u"Enregistrer un encaissement pour la facture "
            u"{0.official_number}".format(self.context)
        )

    def before(self, form):
        BaseFormView.before(self, form)
        self.request.actionmenu.add(
            ViewLink(
                label=u"Retour à la facture",
                path="/invoices/{id}.html",
                id=self.context.id,
                _anchor="payment",
            )
        )

    def submit_success(self, appstruct):
        self.context.record_payment(user=self.request.user, **appstruct)
        self.request.dbsession.merge(self.context)
        return HTTPFound(
            self.request.route_path(
                '/invoices/{id}.html',
                id=self.context.id,
                _anchor='payment',
            )
        )

    def cancel_success(self, appstruct):
        return HTTPFound(
            self.request.route_path(
                '/invoices/{id}.html',
                id=self.context.id,
                _anchor='payment',
            )
        )
    cancel_failure = cancel_success
#
#
# def set_financial_year(request):
#     """
#         Set the financial year of a document
#     """
#     try:
#         ret_dict = InvoiceStatusView(request)()
#     except ValidationFailure, err:
#         log.exception(u"Financial year set error")
#         log.error(err.error)
#         ret_dict = dict(
#             form=err.render(),
#             title=u"Année comptable de référence",
#         )
#     return ret_dict
#
#
# def set_products(request):
#     """
#         Set products in a document
#     """
#     try:
#         ret_dict = InvoiceStatusView(request)()
#     except ValidationFailure, err:
#         log.exception(u"Error setting products")
#         log.error(err.error)
#         ret_dict = dict(
#             form=err.render(),
#             title=u"Année comptable de référence",
#         )
#     return ret_dict


class InvoiceAdminView(BaseEditView):
    """
    Vue pour l'administration de factures /invoices/id/admin

    Vue accessible aux utilisateurs admin
    """
    factory = Invoice
    schema = SQLAlchemySchemaNode(
        Invoice,
        title=u"Formulaire d'édition forcée de devis/factures/avoirs",
        help_msg=u"Les montants sont *10^5   10 000==1€",
    )


def add_routes(config):
    """
    add module related routes
    """
    config.add_route(
        'project_invoices',
        '/projects/{id:\d+}/invoices',
        traverse='/projects/{id}'
    )

    config.add_route(
        '/invoices/{id}',
        '/invoices/{id:\d+}',
        traverse='/invoices/{id}',
    )
    for extension in ('html', 'pdf', 'txt'):
        config.add_route(
            '/invoices/{id}.%s' % extension,
            '/invoices/{id:\d+}.%s' % extension,
            traverse='/invoices/{id}'
        )
    for action in (
        'addfile',
        'delete',
        'duplicate',
        'admin',
        'set_treasury',
        'set_products',
        'addpayment',
        'gencinv',
        'metadatas',
    ):
        config.add_route(
            '/invoices/{id}/%s' % action,
            '/invoices/{id:\d+}/%s' % action,
            traverse='/invoices/{id}'
        )


def includeme(config):
    add_routes(config)

    config.add_view(
        InvoiceAddView,
        route_name="project_invoices",
        renderer='base/formpage.mako',
        permission='add_invoice',
    )

    config.add_view(
        InvoiceEditView,
        route_name='/invoices/{id}',
        renderer='tasks/form.mako',
        permission='view.invoice',
        layout='opa',
    )

    config.add_view(
        InvoiceDeleteView,
        route_name='/invoices/{id}/delete',
        permission='delete.invoice',
    )

    config.add_view(
        InvoiceAdminView,
        route_name='/invoices/{id}/admin',
        renderer="base/formpage.mako",
        permission="admin",
    )

    config.add_view(
        InvoiceDuplicateView,
        route_name="/invoices/{id}/duplicate",
        permission="view.invoice",
        renderer='base/formpage.mako',
    )

    config.add_view(
        InvoiceHtmlView,
        route_name='/invoices/{id}.html',
        renderer='tasks/invoice_view_only.mako',
        permission='view.invoice',
    )

    config.add_view(
        InvoicePdfView,
        route_name='/invoices/{id}.pdf',
        permission='view.invoice',
    )

    config.add_view(
        FileUploadView,
        route_name="/invoices/{id}/addfile",
        renderer='base/formpage.mako',
        permission='add.file',
    )

    config.add_view(
        gencinv_view,
        route_name="/invoices/{id}/gencinv",
        permission="gencinv.invoice",
    )

    config.add_view(
        SageSingleInvoiceExportPage,
        route_name="/invoices/{id}.txt",
        renderer='/treasury/sage_single_export.mako',
        permission='admin_treasury'
    )
    config.add_view(
        InvoicePaymentView,
        route_name="/invoices/{id}/addpayment",
        permission="add_payment.invoice",
        renderer='base/formpage.mako',
    )
    config.add_view(
        InvoiceSetTreasuryiew,
        route_name="/invoices/{id}/set_treasury",
        permission="set_treasury.invoice",
        renderer='base/formpage.mako',
    )

#    config.add_view(
#         set_products,
#         route_name="/invoices/{id}/set_products",
#         permission="admin_treasury",
#         renderer='base/formpage.mako',
#     )
#
