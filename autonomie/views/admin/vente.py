# -*- coding: utf-8 -*-
# * Copyright (C) 2012-2016 Croissance Commune
# * Authors:
#       * TJEBBES Gaston <g.t@majerti.fr>
#       * Arezki Feth <f.a@majerti.fr>;
#       * Miotte Julien <j.m@majerti.fr>;
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
"""
Configuration générale du module vente:

    Mise en forme des PDFs
    Unité de prestation
"""
import functools
from autonomie.views.admin.tools import (
    get_model_admin_view,
    BaseConfigView,
)
from autonomie.forms.admin import (
    get_config_schema,
    tva_form_validator,
    get_sequence_model_admin,
)

from autonomie.models.task import (
    TaskMention,
    WorkUnit,
    PaymentMode,
    PaymentConditions,
)
from autonomie.models.tva import (
    Tva,
)

(
    mention_admin_class,
    mention_route,
    mention_tmpl,
) = get_model_admin_view(
    TaskMention,
    r_path="admin_vente",
)

(
    work_unit_admin_class,
    work_unit_route,
    work_unit_tmpl,
) = get_model_admin_view(
    WorkUnit,
    r_path="admin_vente",
)

(
    payment_mode_admin_class,
    payment_mode_route,
    payment_mode_tmpl,
) = get_model_admin_view(
    PaymentMode,
    r_path="admin_vente",
)

(
    payment_condition_admin_class,
    payment_condition_route,
    payment_condition_tmpl,
) = get_model_admin_view(
    PaymentConditions,
    r_path="admin_vente",
)

(
    tva_admin_class,
    tva_admin_route,
    tva_admin_tmpl,
) = get_model_admin_view(
    Tva,
    r_path="admin_vente",
)


class TaskMentionAdmin(mention_admin_class):
    pass


class WorkUnitAdmin(work_unit_admin_class):
    disable = False


class PaymentModeAdmin(payment_mode_admin_class):
    disable = False


class PaymentConditionAdmin(payment_condition_admin_class):
    pass


class AdminVenteTreasury(BaseConfigView):
    """
        Cae information configuration
    """
    redirect_path = "admin_vente"
    title = u"Configuration comptable du module ventes"
    validation_msg = u"Les informations ont bien été enregistrées"
    keys = (
        'code_journal',
        'numero_analytique',
        'compte_cg_contribution',
        'compte_rrr',
        'compte_frais_annexes',
        'compte_cg_banque',
        'compte_cg_assurance',
        'compte_cgscop',
        'compte_cg_debiteur',
        'compte_cg_organic',
        'compte_cg_debiteur_organic',
        'compte_rg_interne',
        'compte_rg_externe',
        'compte_cg_tva_rrr',
        'code_tva_rrr',
        "contribution_cae",
        "taux_assurance",
        "taux_cgscop",
        "taux_contribution_organic",
        "taux_rg_interne",
        "taux_rg_client",
        'sage_facturation_not_used',
        "sage_contribution",
        'sage_assurance',
        'sage_cgscop',
        'sage_organic',
        'sage_rginterne',
        'sage_rgclient',
    )
    schema = get_config_schema(keys)


class AdminTva(tva_admin_class):
    @property
    def schema(self):
        if self._schema is None:
            self._schema = get_sequence_model_admin(
                self.factory,
                self.title,
            )
            self._schema.title = u"Configuration des taux de TVA"
            self._schema.validator = tva_form_validator
        return self._schema

    @schema.setter
    def schema(self, value):
        self._schema = value


def admin_vente_index_view(request):
    """
    vue d'index pour la configuration du module vente
    """
    menus = []
    for label, route, title, icon in (
        (u"Retour", "admin_index", "", "fa fa-step-backward"),
        (
            u"Configuration des unités de prestation",
            "admin_vente_workunit",
            u"Les unités de prestation proposées lors de la création d'un \
devis/d'une facture", ""
        ),
        (
            u"Configuration des mentions facultatives des devis/factures",
            "admin_vente_mention",
            u"Des mentions facultatives que les entrepreneurs peuvent faire \
figurer dans leurs devis/factures", ""
        ),
        (
            u"Configuration des conditions de paiement",
            "admin_vente_payment_condition",
            u"Les conditions que les entrepreneurs peuvent sélectionner lors \
de la création d'un devis/d'une facture", ""
        ),
        (
            u"Configuration des modes de paiement",
            "admin_vente_payment_mode",
            u"Les modes de paiement que l'on peut sélectionner pour \
enregistrer le paiement d'un devis/ d'une facture", ""
        ),
        (
            u"Configuration comptable du module ventes",
            "admin_vente_treasury",
            u"Code journal, activation des modules d'export ...", ""
        ),
        (
            u"Configuration comptable des produits et TVA collectés",
            'admin_vente_tva',
            u"Taux de TVA, codes produit et codes analytiques associés",
            ""
        )
    ):
        menus.append(dict(label=label, path=route, title=title, icon=icon))
    return dict(title=u"Configuration du module Ventes", menus=menus)


def includeme(config):
    config.add_route('admin_vente', "admin/vente")
    config.add_route("admin_vente_print", "admin/vente/print")
    config.add_route("admin_vente_mention", "admin/vente/mention")
    config.add_route("admin_vente_workunit", "admin/vente/workunit")
    config.add_route("admin_vente_payment_mode", "admin/vente/payment_mode")
    config.add_route("admin_vente_treasury", "admin/vente/treasury")
    config.add_route("admin_vente_tva", "admin/vente/tva")
    config.add_route(
        "admin_vente_payment_condition",
        "admin/vente/payment_condition"
    )

    config.add_admin_view = functools.partial(
        config.add_view,
        permission='admin',
        renderer="admin/main.mako",
    )
    config.add_admin_view(
        admin_vente_index_view,
        route_name="admin_vente",
    )

    config.add_admin_view(
        TaskMentionAdmin,
        route_name="admin_vente_mention",
    )

    config.add_admin_view(
        WorkUnitAdmin,
        route_name="admin_vente_workunit",
    )

    config.add_admin_view(
        PaymentModeAdmin,
        route_name="admin_vente_payment_mode",
    )

    config.add_admin_view(
        PaymentConditionAdmin,
        route_name='admin_vente_payment_condition',
    )

    config.add_admin_view(
        AdminVenteTreasury,
        route_name='admin_vente_treasury',
    )

    config.add_admin_view(
        AdminTva,
        route_name='admin_vente_tva',
    )