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
    Company form schemas
"""
import colander
import logging
import deform

import deform_extensions
from sqlalchemy.orm import load_only

from autonomie_base.models.base import DBSESSION
from autonomie.models.company import (
    CompanyActivity,
    Company,
)

from autonomie.models.customer import Customer

from autonomie import forms
from autonomie.forms.customer import build_customer_values
from autonomie.forms import (
    files,
    lists,
)
from autonomie.utils.image import ImageResizer

log = logging.getLogger(__name__)

HEADER_RESIZER = ImageResizer(4, 1)


@colander.deferred
def deferred_edit_adminonly_widget(node, kw):
    """
        return a deferred adminonly edit widget
    """
    request = kw['request']
    if not request.has_permission('admin_company', request.context):
        return deform_extensions.DisabledInput()
    else:
        return deform.widget.TextInputWidget()


@colander.deferred
def deferred_upload_header_widget(node, kw):
    request = kw['request']
    tmpstore = files.SessionDBFileUploadTempStore(
        request,
        filters=HEADER_RESIZER.complete
    )
    return files.CustomFileUploadWidget(tmpstore)


@colander.deferred
def deferred_default_contribution(node, kw):
    """
        Return the default contribution
    """
    request = kw['request']
    cae_contribution = request.config.get('contribution_cae')
    if cae_contribution is not None and cae_contribution.isdigit():
        return cae_contribution
    else:
        return colander.null


def remove_admin_fields(schema, kw):
    """
        Remove admin only fields from the company schema
    """
    request = kw['request']
    if not request.has_permission("admin_treasury", request.context):
        del schema['RIB']
        del schema['IBAN']
        del schema['code_compta']
        del schema['contribution']


@colander.deferred
def deferred_company_datas_select(node, kw):
    values = CompanyActivity.query('id', 'label').all()
    values.insert(0, ('', "- Sélectionner un type d'activité"))
    return deform.widget.SelectWidget(
        values=values
    )


@colander.deferred
def deferred_company_datas_validator(node, kw):
    ids = [entry[0] for entry in CompanyActivity.query('id')]
    return colander.OneOf(ids)


class CompanyActivitySchema(colander.SequenceSchema):
    id = colander.SchemaNode(
        colander.Integer(),
        title=u"un domaine",
        widget=deferred_company_datas_select,
        validator=deferred_company_datas_validator,
    )


class CompanySchema(colander.MappingSchema):
    """
        Company add/edit form schema
    """
    user_id = forms.id_node()
    name = colander.SchemaNode(
        colander.String(),
        widget=deferred_edit_adminonly_widget,
        title=u'Nom'
    )

    goal = colander.SchemaNode(
        colander.String(),
        title=u"Descriptif de l'activité")

    activities = CompanyActivitySchema(
        title=u"Domaines d'activité",
        missing=colander.drop,
    )

    email = forms.mail_node(missing=u'')

    phone = colander.SchemaNode(
            colander.String(),
            title=u'Téléphone',
            missing=u'')

    mobile = colander.SchemaNode(
            colander.String(),
            title=u'Téléphone portable',
            missing=u'')

    logo = files.ImageNode(
        title="Choisir un logo",
        missing=colander.drop,
    )
    header = files.ImageNode(
        widget=deferred_upload_header_widget,
        title=u'Entête des fichiers PDF',
        missing=colander.drop,
        description=u"Le fichier est idéalement au format 5/1 (par exemple \
1000px x 200 px)",
    )

    # Fields specific to the treasury
    code_compta = colander.SchemaNode(
            colander.String(),
            title=u"Compte analytique",
            description=u"Compte analytique utilisé dans le logiciel de \
comptabilité",
            missing="")

    contribution = colander.SchemaNode(
            colander.Integer(),
            widget=deform.widget.TextInputWidget(
                input_append="%",
                css_class="col-md-1"
                ),
            validator=colander.Range(
                min=0,
                max=100,
                min_err=u"Veuillez fournir un nombre supérieur à 0",
                max_err=u"Veuillez fournir un nombre inférieur à 100"),
            title=u"Contribution à la CAE",
            missing=colander.drop,
            description=u"Pourcentage que cette entreprise contribue à la CAE",
    )

    cgv = forms.textarea_node(
        title=u"Conditions générales complémentaires",
        richwidget=True,
        missing="",
    )

    RIB = colander.SchemaNode(
            colander.String(),
            title=u'RIB',
            missing=u'')

    IBAN = colander.SchemaNode(
            colander.String(),
            title=u'IBAN',
            missing=u'')

    come_from = forms.come_from_node()


COMPANYSCHEMA = CompanySchema(after_bind=remove_admin_fields)


# Company node related tools
def get_deferred_company_choices(widget_options):
    """
    Build a deferred for company selection widget
    """
    default_entry = widget_options.pop('default', None)

    @colander.deferred
    def deferred_company_choices(node, kw):
        """
        return a deferred company selection widget
        """
        values = DBSESSION().query(Company.id, Company.name).all()
        if default_entry is not None:
            values.insert(0, default_entry)
        return deform.widget.Select2Widget(
            values=values,
            placeholder=u"Sélectionner une entreprise",
            **widget_options
            )
    return deferred_company_choices


def company_node(**kw):
    """
    Return a schema node for company selection
    """
    widget_options = kw.pop('widget_options', {})
    return colander.SchemaNode(
        colander.Integer(),
        widget=get_deferred_company_choices(widget_options),
        **kw
    )


# Customer node related tools
@colander.deferred
def deferred_fullcustomer_list_widget(node, kw):
    values = [('', u"Tous les clients")]
    for comp in Company.query().options(load_only("id", "name")):
        customers = Customer.label_query().filter_by(company_id=comp.id)
        values.append(
            deform.widget.OptGroup(
                comp.name,
                *build_customer_values(customers, default=False)
            )
        )
    return deform.widget.Select2Widget(
        values=values,
        placeholder=u"Sélectionner un client"
    )


@colander.deferred
def deferred_customer_list_widget(node, kw):
    values = [('', u'Tous les clients'), ]
    company = kw['request'].context
    for cust in company.customers:
        values.append(
            (cust.id, u"%s (%s)" % (cust.name, cust.code))
        )
    return deform.widget.Select2Widget(
        values=values,
        placeholder=u'Sélectionner un client',
    )


@colander.deferred
def deferred_company_customer_validator(node, kw):
    """
    Ensure we don't query customers from other companies
    """
    company = kw['request'].context
    values = [customer.id for customer in company.customers]
    return colander.OneOf(values)


def customer_node(is_admin=False):
    """
    return a customer selection node

        is_admin

            is the associated view restricted to company's invoices
    """
    if is_admin:
        deferred_customer_widget = deferred_fullcustomer_list_widget
        deferred_customer_validator = None
    else:
        deferred_customer_widget = deferred_customer_list_widget
        deferred_customer_validator = deferred_company_customer_validator

    return colander.SchemaNode(
        colander.Integer(),
        name='customer_id',
        widget=deferred_customer_widget,
        validator=deferred_customer_validator,
        missing=colander.drop,
    )


def get_list_schema(company=False):
    """
    Return a schema for filtering companies list
    """
    schema = lists.BaseListsSchema().clone()
    schema.add(
        colander.SchemaNode(
            colander.Boolean(),
            name='include_inactive',
            label=u"Inclure les entreprises désactivées",
            default=False,
        )
    )
    return schema
