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
    Invoice model
"""
import datetime
import logging

from zope.interface import implementer
from beaker.cache import cache_region

from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    Boolean,
    String,
    ForeignKey,
    DateTime,
    distinct,
)
from sqlalchemy.orm import (
    relationship,
    deferred,
    backref,
)

from autonomie_base.models.types import (
    PersistentACLMixin,
)
from autonomie_base.models.base import (
    DBSESSION,
    DBBASE,
    default_table_args,
)
from autonomie import forms
from autonomie.compute import math_utils
from autonomie.compute.task import (
    TaskCompute,
    InvoiceCompute,
)
from autonomie.models.tva import (
    Product,
)
from autonomie.interfaces import (
    IMoneyTask,
    IInvoice,
)
from .task import (
    Task,
    TaskLine,
    TaskStatus,
)
from .actions import DEFAULT_ACTION_MANAGER

logger = logging.getLogger(__name__)


INVOICE_STATES = (
    ('waiting', u"En attente"),
    ('paid', u'Partiellement payée'),
    ('resulted', u'Soldée'),
)


def translate_invoices(invoicequery, from_point):
    """
    Translate invoice numbers to 'from_point'

    :param iter invoicequery: An iterable
    :param int from_point: from_point

    The first invoice will get from_point as official_number
    """
    for invoice in invoicequery:
        invoice.official_number = from_point
        from_point += 1
        DBSESSION().merge(invoice)

    return from_point


@implementer(IInvoice, IMoneyTask)
class Invoice(Task, InvoiceCompute):
    """
        Invoice Model
    """
    __tablename__ = 'invoice'
    __table_args__ = default_table_args
    __mapper_args__ = {'polymorphic_identity': 'invoice', }
    id = Column(ForeignKey('task.id'), primary_key=True)

    # Common with CancelInvoice
    financial_year = Column(
        Integer,
        info={'colanderalchemy': {'title': u"Année fiscale de référence"}},
        default=0
    )
    exported = deferred(
        Column(
            Boolean(),
            info={'colanderalchemy': {'title': u"A déjà été exportée ?"}},
            default=False
        ),
        group="edit"
    )

    # Specific to Invoice
    paid_status = Column(
        String(10),
        default='waiting',
        info={'colanderalchemy': {'title': u'Statut de la facture', }},
    )
    estimation_id = Column(ForeignKey('estimation.id'))
    estimation = relationship(
        "Estimation",
        primaryjoin="Invoice.estimation_id==Estimation.id",
        info={
            'colanderalchemy': forms.EXCLUDED,
            'export': {'exclude': True},
        },
    )

    state_manager = DEFAULT_ACTION_MANAGER['invoice']

    paid_states = ('resulted',)
    not_paid_states = ('valid', 'paid', )
    valid_states = paid_states + not_paid_states

    _number_tmpl = u"{s.company.name} {s.date:%Y-%m} F{s.company_index}"

    _name_tmpl = u"Facture {0}"

    _deposit_name_tmpl = u"Facture d'acompte {0}"

    _sold_name_tmpl = u"Facture de solde {0}"

    def _get_project_index(self, project):
        """
        Return the index of the current object in the associated project
        :param obj project: A Project instance in which we will look to get the
        current doc index
        :returns: The next number
        :rtype: int
        """
        return project.get_next_invoice_index()

    def _get_company_index(self, company):
        """
        Return the index of the current object in the associated company
        :param obj company: A Company instance in which we will look to get the
        current doc index
        :returns: The next number
        :rtype: int
        """
        return company.get_next_invoice_index()

    def set_deposit_label(self):
        self.name = self._deposit_name_tmpl.format(self.project_index)

    def set_sold_label(self):
        self.name = self._sold_name_tmpl.format(self.project_index)

    def set_project(self, project):
        self.project = project

    def gen_cancelinvoice(self, user):
        """
            Return a cancel invoice with self's informations
        """
        cancelinvoice = CancelInvoice(
            user=user,
            company=self.company,
            project=self.project,
            customer=self.customer,
            phase_id=self.phase_id,
            address=self.address,
            workplace=self.workplace,
            description=self.description,
            invoice=self,
            expenses_ht=-1 * self.expenses_ht,
            financial_year=self.financial_year,
            display_units=self.display_units,
            business_type_id=self.business_type_id,
            business_id=self.business_id,
        )

        cancelinvoice.line_groups = []
        for group in self.line_groups:
            cancelinvoice.line_groups.append(
                group.gen_cancelinvoice_group()
            )
        order = self.get_next_row_index()

        for discount in self.discounts:
            discount_line = TaskLine(
                cost=discount.amount,
                tva=discount.tva,
                quantity=1,
                description=discount.description,
                order=order,
                unity='',
            )
            discount_line.product_id = Product.first_by_tva_value(discount.tva)
            order += 1
            cancelinvoice.default_line_group.lines.append(discount_line)

        for index, payment in enumerate(self.payments):
            paid_line = TaskLine(
                cost=math_utils.reverse_tva(
                    payment.amount,
                    payment.tva.value,
                    False,
                ),
                tva=payment.tva.value,
                quantity=1,
                description=u"Paiement {0}".format(index + 1),
                order=order,
                unity='NONE',
            )
            paid_line.product_id = Product.first_by_tva_value(payment.tva.value)
            order += 1
            cancelinvoice.default_line_group.lines.append(paid_line)
        cancelinvoice.mentions = self.mentions
        cancelinvoice.payment_conditions = u"Réglé"
        return cancelinvoice

    def get_next_row_index(self):
        return len(self.default_line_group.lines) + 1

    def record_payment(self, **kw):
        """
        Record a payment for the current invoice
        """
        resulted = kw.pop('resulted', False)
        if kw['amount'] > 0:
            payment = Payment()
            for key, value in kw.iteritems():
                setattr(payment, key, value)
            logger.info(u"Amount : {0}".format(payment.amount))
            self.payments.append(payment)

        return self.check_resulted(
            force_resulted=resulted,
            user_id=kw['user_id'],
        )

    def check_resulted(self, force_resulted=False, user_id=None):
        """
        Check if the invoice is resulted or not and set the appropriate status
        """
        logger.debug(u"-> There still to pay : %s" % self.topay())
        if self.topay() <= 0 or force_resulted:
            self.paid_status = 'resulted'

        elif len(self.payments) > 0 or self.cancelinvoice_amount() > 0:
            self.paid_status = 'paid'

        else:
            self.paid_status = 'waiting'

        if user_id is not None:
            status_record = TaskStatus(
                status_code=self.paid_status,
                status_person_id=user_id,
                status_comment=''
            )
            self.statuses.append(status_record)
        return self

    def duplicate(self, user, **kw):
        """
        Duplicate the current invoice

        Mandatory args :

            user

                The user duplicating this estimation

            customer

            project
        """
        invoice = Invoice(
            user=user,
            company=self.company,
            **kw
        )

        if invoice.customer.id == self.customer_id:
            invoice.address = self.address

        invoice.workplace = self.workplace

        invoice.description = self.description

        invoice.payment_conditions = self.payment_conditions
        invoice.display_units = self.display_units
        invoice.expenses_ht = self.expenses_ht
        invoice.financial_year = datetime.date.today().year

        invoice.line_groups = []
        for group in self.line_groups:
            invoice.line_groups.append(group.duplicate())

        for line in self.discounts:
            invoice.discounts.append(line.duplicate())

        invoice.mentions = self.mentions
        return invoice

    def __repr__(self):
        return u"<Invoice id:{s.id}>".format(s=self)

    def __json__(self, request):
        datas = Task.__json__(self, request)

        datas.update(
            dict(
                financial_year=self.financial_year,
                exported=self.exported,
                estimation_id=self.estimation_id,
            )
        )
        return datas

    def is_tolate(self):
        """
            Return True if a payment is expected since more than
            45 days
        """
        res = False
        if self.paid_status in ('waiting', 'paid'):
            today = datetime.date.today()
            elapsed = today - self.date
            if elapsed > datetime.timedelta(days=45):
                res = True
            else:
                res = False
        return res


@implementer(IInvoice, IMoneyTask)
class CancelInvoice(Task, TaskCompute):
    """
        CancelInvoice model
        Could also be called negative invoice
    """
    __tablename__ = 'cancelinvoice'
    __table_args__ = default_table_args
    __mapper_args__ = {'polymorphic_identity': 'cancelinvoice'}
    id = Column(Integer, ForeignKey('task.id'), primary_key=True)
    # Common with Invoice
    financial_year = Column(
        Integer,
        info={'colanderalchemy': {'title': u"Année fiscale de référence"}},
        default=0
    )
    exported = deferred(
        Column(
            Boolean(),
            info={'colanderalchemy': {"title": "A déjà été exportée ?"}},
            default=False
        ),
        group="edit"
    )

    # Specific to CancelInvoice
    invoice_id = Column(
        Integer,
        ForeignKey('invoice.id'),
        info={
            'colanderalchemy': {
                'title': u"Identifiant de la facture associée",
            }
        },
        default=None
    )
    invoice = relationship(
        "Invoice",
        backref=backref(
            "cancelinvoices",
            info={'colanderalchemy': forms.EXCLUDED, }
        ),
        primaryjoin="CancelInvoice.invoice_id==Invoice.id",
        info={'colanderalchemy': forms.EXCLUDED, }
    )

    state_manager = DEFAULT_ACTION_MANAGER['cancelinvoice']
    valid_states = ('valid', )

    _number_tmpl = u"{s.company.name} {s.date:%Y-%m} A{s.company_index}"

    _name_tmpl = u"Avoir {0}"

    def _get_project_index(self, project):
        """
        Return the index of the current object in the associated project
        :param obj project: A Project instance in which we will look to get the
        current doc index
        :returns: The next number
        :rtype: int
        """
        return project.get_next_invoice_index()

    def _get_company_index(self, company):
        """
        Return the index of the current object in the associated company
        :param obj company: A Company instance in which we will look to get the
        current doc index
        :returns: The next number
        :rtype: int
        """
        return company.get_next_invoice_index()

    def is_tolate(self):
        """
        Return False
        """
        return False

    def __repr__(self):
        return u"<CancelInvoice id:{s.id}>".format(s=self)

    def __json__(self, request):
        datas = Task.__json__(self, request)

        datas.update(
            dict(
                invoice_id=self.invoice_id,
                financial_year=self.financial_year,
                exported=self.exported,
            )
        )
        return datas


class Payment(DBBASE, PersistentACLMixin):
    """
        Payment entry
    """
    __tablename__ = 'payment'
    __table_args__ = default_table_args
    id = Column(
        Integer,
        primary_key=True
    )
    created_at = Column(
        DateTime(),
        info={
            'colanderalchemy': {
                'exclude': True, 'title': u"Créé(e) le",
            }
        },
        default=datetime.datetime.now,
    )

    updated_at = Column(
        DateTime(),
        info={
            'colanderalchemy': {
                'exclude': True, 'title': u"Mis(e) à jour le",
            }
        },
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now
    )

    mode = Column(
        String(50),
        info={'colanderalchemy': {'title': u"Mode de paiement"}}
    )
    amount = Column(
        BigInteger(),
        info={'colanderalchemy': {"title": u"Montant"}},

    )
    bank_remittance_id = Column(
        String(255),
        info={'colanderalchemy': {'title': u"Identifiant de remise en banque"}},
    )
    date = Column(
        DateTime(),
        info={'colanderalchemy': {'title': u"Date de remise"}},
        default=datetime.datetime.now,
    )
    exported = Column(Boolean(), default=False)
    task_id = Column(
        Integer,
        ForeignKey('task.id', ondelete="cascade"),
        info={'colanderalchemy': {'title': u"Identifiant du document"}},
    )
    bank_id = Column(
        ForeignKey('bank_account.id'),
        info={'colanderalchemy': {'title': u"Compte en banque"}},
    )
    tva_id = Column(
        ForeignKey('tva.id'),
        info={'colanderalchemy': {'title': u"Tva associée à ce paiement"}},
        nullable=True
    )

    user_id = Column(
        ForeignKey('accounts.id'),
        info={'colanderalchemy': {'title': u"Utilisateur"}},
    )

    user = relationship(
        "User",
        info={'colanderalchemy': {'exclude': True}},
    )

    bank = relationship(
        "BankAccount",
        back_populates='payments',
        info={'colanderalchemy': {'exclude': True}}
    )
    tva = relationship(
        "Tva",
        info={'colanderalchemy': {'exclude': True}}
    )
    task = relationship(
        "Task",
        primaryjoin="Task.id==Payment.task_id",
    )
    # Formatting precision
    precision = 5

    # Usefull aliases
    @property
    def invoice(self):
        return self.task

    @property
    def parent(self):
        return self.task

    # Simple function
    def get_amount(self):
        return self.amount

    def __json__(self, request):
        """
        Build a Json representation of this object

        :rtype: dict
        """
        return dict(
            id=self.id,
            created_at=self.created_at,
            updated_at=self.updated_at,
            mode=self.mode,
            amount=math_utils.integer_to_amount(self.amount, 5),
            bank_remittance_id=self.bank_remittance_id,
            date=self.date,
            exporter=self.exported,
            task_id=self.task_id,
            bank_id=self.bank_id,
            tva_id=self.tva_id,
            user_id=self.user_id,
        )

    def __unicode__(self):
        return u"<Payment id:{s.id} task_id:{s.task_id} amount:{s.amount}\
 mode:{s.mode} date:{s.date}".format(s=self)


# Usefull queries
def get_invoice_years(kw):
    """
        Return a cached query for the years we have invoices configured
    """
    @cache_region("long_term", "taskyears")
    def taskyears():
        """
            return the distinct financial years available in the database
        """
        query = DBSESSION().query(distinct(Invoice.financial_year))
        query = query.order_by(Invoice.financial_year)
        years = [year[0] for year in query]
        current = datetime.date.today().year
        if current not in years:
            years.append(current)
        return years
    return taskyears()

    def __json__(self, request):
        return dict(
            id=self.id,
            created_at=self.created_at,
            updated_at=self.updated_at,
            mode=self.mode,
            amount=math_utils.integer_to_amount(self.amount),
            bank_remittance_id=self.bank_remittance_id,
            label=self.bank_remittance_id,
            date=self.date,
            exported=self.exported,
            task_id=self.task_id,
            bank_id=self.bank_id,
            bank=self.bank.label,
            tva_id=self.tva_id,
            tva=math_utils.integer_to_amount(self.tva.value, 2),
            user_id=self.user_id,
        )
