# -*- coding: utf-8 -*-
# * File Name : test_estimation.py
#
# * Copyright (C) 2010 Gaston TJEBBES <g.t@majerti.fr>
# * Company : Majerti ( http://www.majerti.fr )
#
#   This software is distributed under GPLV3
#   License: http://www.gnu.org/licenses/gpl-3.0.txt
#
# * Creation Date : 10-04-2012
# * Last Modified :
#
# * Project :
#
from copy import deepcopy
from mock import MagicMock
from .base import BaseTestCase
DBDATAS = dict(estimation=dict(course="0",
                                displayedUnits="1",
                                discountHT=2000,
                                tva=1960,
                                expenses=1500,
                                deposit=20,
                                exclusions="Ne sera pas fait selon la règle",
                                paymentDisplay="ALL",
                                paymentConditions="Payer à l'heure",
                                IDPhase=485,
                                taskDate="10-12-2012",
                                description="Devis pour le client test",
                                manualDeliverables=1),
                estimation_lines=[
                     {'description':'text1',
                     'cost':1000,
                     'unity':'days',
                     'quantity':12,
                     'rowIndex':1},
                     {'description':'text2',
                     'cost':20000,
                     'unity':'month',
                     'quantity':12,
                     'rowIndex':2},
                     ],
                payment_lines=[
                    {'description':"Début", "paymentDate":"12-12-2012",
                                            "amount":15000, "rowIndex":1},
                    {'description':"Milieu", "paymentDate":"13-12-2012",
                                           "amount":15000, "rowIndex":2},
                    {'description':"Fin", "paymentDate":"14-12-2012",
                                            "amount":150, "rowIndex":3},
                    ]
                )
DBDATAS2 = dict(estimation=dict(course="0",
                                displayedUnits="1",
                                discountHT=0,
                                tva=0,
                                expenses=0,
                                deposit=0,
                                exclusions="Ne sera pas fait selon la règle",
                                paymentDisplay="ALL",
                                paymentConditions="Payer à l'heure",
                                IDPhase=485,
                                taskDate="10-12-2012",
                                description="Devis pour le client test",
                                manualDeliverables=0),
                estimation_lines=[
                     {'description':'text1',
                     'cost':1000,
                     'unity':'days',
                     'quantity':1,
                     'rowIndex':1},
                     ],
                payment_lines=[
                    {'description':"Début", "paymentDate":"12-12-2012",
                                            "amount":15, "rowIndex":1},
                    {'description':"Milieu", "paymentDate":"13-12-2012",
                                           "amount":15, "rowIndex":2},
                    {'description':"Fin", "paymentDate":"14-12-2012",
                                            "amount":1, "rowIndex":3},
                    ]
                )
DATAS = {'common': dict(IDPhase=485,
                        taskDate="10-12-2012",
                        description="Devis pour le client test",
                        course="0",
                        displayedUnits="1",),
        'lines':dict(discountHT=2000,
                     tva=1960,
                     expenses=1500,
                     lines=[
       {'description':'text1', 'cost':1000, 'unity':'days', 'quantity':12,},
       {'description':'text2', 'cost':20000, 'unity':'month', 'quantity':12},
                            ]
                     ),
        'notes':dict(exclusions="Ne sera pas fait selon la règle"),
        'payments':dict(paymentDisplay='ALL',
                        deposit=20,
                        payment_times=-1,
                        payment_lines=[
        {'description':"Début", "paymentDate":"12-12-2012", "amount":15000},
        {'description':"Milieu", "paymentDate":"13-12-2012","amount":15000},
        {'description':"Fin", "paymentDate":"14-12-2012","amount":150},
        ]
        ),
        'comments':dict(paymentConditions="Payer à l'heure"),
                        }

def get_full_estimation_model(datas):
    """
        Returns a simulated database model
    """
    est = MagicMock(**datas['estimation'])
    estlines = [MagicMock(**line)for line in datas['estimation_lines']]
    estpayments = [MagicMock(**line)for line in datas['payment_lines']]
    est.lines = estlines
    est.payment_lines = estpayments
    return est

class Test(BaseTestCase):
    def test_estimation_dbdatas_to_appstruct(self):
        from autonomie.views.forms.estimation import EstimationMatch
        e = EstimationMatch()
        result = e.toschema(DBDATAS, {})
        for field, group in e.matching_map:
            self.assertEqual(DBDATAS['estimation'][field], result[group][field])

    def test_estimationlines_dbdatas_to_appstruct(self):
        from autonomie.views.forms.estimation import EstimationLinesMatch
        e = EstimationLinesMatch()
        result = e.toschema(DBDATAS, {})
        from copy import deepcopy
        lines = deepcopy(DBDATAS['estimation_lines'])
        lines = sorted(lines, key=lambda row:int(row['rowIndex']))
        for line in lines:
            del(line['rowIndex'])
        for i, line in enumerate(lines):
            self.assertEqual(result['lines']['lines'][i], line)

    def test_paymentlines_dbdatas_to_appstruct(self):
        from autonomie.views.forms.estimation import PaymentLinesMatch
        p = PaymentLinesMatch()
        result = p.toschema(DBDATAS, {})
        lines = deepcopy(DBDATAS['payment_lines'])
        lines = sorted(lines, key=lambda row:int(row['rowIndex']))
        for line in lines:
            del(line['rowIndex'])
        for i,line in enumerate(lines):
            self.assertEqual(result['payments']['payment_lines'][i], line)

    def test_appstruct_to_estimationdbdatas(self):
        from autonomie.views.forms.estimation import EstimationMatch
        datas_ = deepcopy(DATAS)
        e = EstimationMatch()
        result = e.todb(datas_, {})
        dbdatas_ = deepcopy(DBDATAS)
        del(dbdatas_['estimation']['manualDeliverables'])
        self.assertEqual(result['estimation'], dbdatas_['estimation'])

    def test_appstruct_to_estimationlinesdbdatas(self):
        from autonomie.views.forms.estimation import EstimationLinesMatch
        datas_ = deepcopy(DATAS)
        e = EstimationLinesMatch()
        result = e.todb(datas_, {})
        self.assertEqual(result['estimation_lines'], DBDATAS['estimation_lines'])

    def test_appstruct_to_paymentlinesdbdatas(self):
        from autonomie.views.forms.estimation import PaymentLinesMatch
        p = PaymentLinesMatch()
        datas_ = deepcopy(DATAS)
        result = p.todb(datas_, {})
        self.assertEqual(result['payment_lines'], DBDATAS['payment_lines'])

    def test_appstruct_to_dbdatas(self):
        from autonomie.views.forms.estimation import get_dbdatas
        datas_ = deepcopy(DATAS)
        self.assertEqual(get_dbdatas(datas_), DBDATAS)

    def test_dbdatas_to_appstruct(self):
        from autonomie.views.forms.estimation import get_appstruct
        self.assertEqual(get_appstruct(DBDATAS), DATAS)

    def test_computing(self):
        from autonomie.views.forms.estimation import EstimationComputingModel
        mocked_est = get_full_estimation_model(DBDATAS)
        estimation = EstimationComputingModel(mocked_est)
        self.assertEqual(estimation.compute_line_total(mocked_est.lines[0]),
                        12000)
        self.assertEqual(estimation.compute_lines_total(), 252000)
        self.assertEqual(estimation.compute_totalht(), 250000)
        self.assertEqual(estimation.compute_ttc(), 299000)
        self.assertEqual(estimation.compute_total(), 297500)
        self.assertEqual(estimation.compute_deposit(), 59500)
        self.assertEqual(estimation.compute_sold(), 208000)

    def test_computing_strange_amounts(self):
        from autonomie.views.forms.estimation import EstimationComputingModel
        mocked_est = get_full_estimation_model(DBDATAS2)
        estimation = EstimationComputingModel(mocked_est)
        self.assertEqual(estimation.compute_line_amount(), 333)
        self.assertEqual(estimation.compute_sold(), 334)
