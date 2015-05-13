# -*-coding:utf-8-*-
"""
Main classes for statistics handling
Maybe it will be merged with the models further on


1- On récupère la feuille de stats depuis la base
2- On récupère le dictionnaire d'inspection pour le modèle cible
3- Pour chaque critère, on va peupler le critère avec des les données renvoyées
par l'inspection


On doit pouvoir générer des query :
    1-
    db().query(
        distinct(models.user.UserDatas.id)
    ).filter(
        models.user.UserDatas.coordonnees_lastname.startswith('tje')
    ).count()

    2- Des relations M2o
    Les objets remotes existent déjà, c'est forcément par l'id qu'on match

    db().query(
        distinct(models.user.UserDatas.id)
    ).filter(
        models.user.UserDatas.parcours_status_id.in_((1,2,3))
    ).count()

    3- Des relations o2M
    On doit passer par les attributs des objets remotes pour filtrer
    filtre sur un attribut cible :

    db().query(
        distinct(models.user.UserDatas.id)
    ).outerjoin(
        models.user.UserDatas.parcours_date_diagnostic
    ).filter(
        models.user.DateDiagnosticDatas.date<datetime.datetime.now()
    ).count()


    filtre sur deux attributs cibles :

    db().query(
        distinct(models.user.UserDatas.id), models.user.UserDatas
        ).outerjoin(
        models.user.UserDatas.statut_external_activity
        ).filter(
        models.user.ExternalActivityDatas.brut_salary>100
        ).filter(models.user.ExternalActivityDatas.hours<8).count()
"""
from sqlalchemy import (
    not_,
    distinct,
    and_,
    or_
)

from autonomie.models.base import DBSESSION


class SheetQueryFactory(object):
    """
    Statistics sheet

    Compound of :
        a list of entries

    Rendering:

            A sheet should be rendered as a csv file, the headers :
                ('label', 'count')
            each row matches an entry

    :param obj model: The model we're building stats on (UserDatas)
    :param obj sheet: The StatSheet instance we're mapping
    :param obj inspector: The model's sqlalchemy inspector used to retrieve
    database related informations
    """
    entries = []

    def __init__(self, model, sheet, inspector):
        self.model = model
        self.sheet = sheet
        self.inspector = inspector

        self.entries = []
        for entry in self.sheet.entries:
            self.entries.append(
                EntryQueryFactory(
                    self.model,
                    entry,
                    self.inspector,
                )
            )

    @property
    def headers(self):
        return (
            {'name': u'label', 'label': u"Libellé"},
            {'name': u'description', 'label': u'Description'},
            {'name': u'count', 'label': u"Nombre"},
        )

    @property
    def rows(self):
        """
        Return the rows of our sheet output
        """
        result = []
        for entry in self.entries:
            result.append(entry.render_row())

        return result


class EntryQueryFactory(object):
    """
    Statistic entry

    Compound of :
        a label
        a description
        a list of criteria

    :param obj model: The Statentry model instance
    :param obj entry_model: The model on which to generate statistics
    :param obj inspector: The model inspector
    """
    model = None
    related_joins = None
    criteria = []

    def __init__(self, model, entry_model, inspector):
        self.model = model
        self.entry = entry_model
        self.stat_model = inspector

        self.criteria = []
        for criterion in self.entry.criteria:
            self.criteria.append(
                get_stat_criterion(self.model, criterion, inspector)
            )

    def query(self):
        """
        Returns the main query used to find objects

        E.G:

            query = DBSESSION().query(distinct(UserDatas.id), UserDatas)
            query = query.filter(UserDatas.name.startswith('test'))
            query = query.outerjoin(UserDatas.conseiller)
            query = query.filter(User.lastname=='A manager')
        """
        query = DBSESSION().query(distinct(self.model.id), self.model)

        # Pour chaque critère sur lesquels on va ajouter des filtres, on a
        # besoin d'être sûr que la classe concernée est bien requêtée, il faut
        # donc ajouter des outerjoins pour chaque classe liée.

        # NOTE: on ne gère pas les alias (les joins sur deux tables identiques
        # pour deux relations différentes)
        already_added = []
        for criterion in self.criteria:
            # On génère le filtre
            filter_ = criterion.gen_filter()

            # si il n'y a pas de filtres ...
            if filter_ is not None:
                # On récupère l'objet lié
                join_class = criterion.get_join_class()
                # Si il y a un outerjoin à faire (le critère se fait sur un
                # attribut de l'objet lié)
                if join_class is not None:
                    # on ne va pas outerjoiné deux fois la classe pour le même
                    # critère
                    if criterion.key not in already_added:
                        query = query.outerjoin(join_class)
                        already_added.append(criterion.key)

                query = query.filter(filter_)
        return query

    def render_row(self):
        """
        Returns the datas expected for statistics rendering
        """
        return {
            "label": self.entry.title,
            "count": self.query().count(),
            "description": self.entry.description,
        }


def get_stat_criterion(model, criterion_model, inspector):
    """
    Return the appropriate criterion class
    """
    if criterion_model.type == 'string':
        factory = StrCriterionQueryFactory
    elif criterion_model.type == 'number':
        factory = NumericCriterionQueryFactory
    elif criterion_model.type == 'optrel':
        factory = OptRelCriterionQueryFactory
    elif criterion_model.type == 'date':
        factory = DateCriterionQueryFactory
    return factory(model, criterion_model, inspector)


class CriterionQueryFactory(object):
    """
    Statistic criterion

    Compound of :
        a model we query on
        a field name
        a condition key
        conditions values
        a type
    """
    model = None
    key = None
    search1 = None
    type = 'str'

    def __init__(self, model, criterion_model, inspector):
        self.model = model
        self.criterion_model = criterion_model

        self.key = criterion_model.key
        self.method = criterion_model.method

        self.sqla_datas = inspector.get_datas(self.key)
        self.column = self.sqla_datas['column']

    def get_join_class(self):
        """
        Return a related class if this criterion used one
        """
        return self.sqla_datas.get('join_class')

    def gen_filter(self):
        result = None
        if self.key:
            filter_method = getattr(self, "filter_%s" % self.method, None)
            if filter_method is not None:
                result = filter_method(self.column)
        return result

    # FIXME : maybe one of the none values ('', 0 ...)
    def filter_nll(self, attr):
        """ null """
        return attr == None

    def filter_nnll(self, attr):
        """ not null """
        return attr != None

    def filter_eq(self, attr):
        """ equal """
        if self.search1:
            return attr == self.search1

    def filter_neq(self, attr):
        """ not equal """
        if self.search1:
            return attr != self.search1


class StrCriterionQueryFactory(CriterionQueryFactory):
    """
    Statistic criterion related to strings
    """
    def __init__(self, model, criterion_model, inspector):
        CriterionQueryFactory.__init__(self, model, criterion_model, inspector)
        self.search1 = criterion_model.search1
        self.search2 = criterion_model.search2

    def filter_has(self, attr):
        """ contains """
        if self.search1:
            like_str = u"%" + self.search1 + u"%"
            return attr.like(like_str)

    def filter_sw(self, attr):
        """ startswith """
        if self.search1:
            like_str = self.search1 + u"%"
            return attr.like(like_str)

    def filter_ew(self, attr):
        """ endswith """
        if self.search1:
            like_str = self.search1 + u"%"
            return attr.like(like_str)

    def filter_nhas(self, attr):
        """ not contains """
        f = self.filter_has(attr)
        if f is not None:
            return not_(f)


class OptRelCriterionQueryFactory(CriterionQueryFactory):
    """
    Statistic criterion related to related options
    """
    def __init__(self, model, criterion_model, inspector):
        CriterionQueryFactory.__init__(self, model, criterion_model, inspector)
        self.searches = criterion_model.searches

    def filter_ioo(self, attr):
        """ is one of """
        if self.searches:
            return attr.in_(self.searches)

    def filter_nioo(self, attr):
        """ is not one of """
        if self.searches:
            return not_(attr.in_(self.searches))


class NumericCriterionQueryFactory(CriterionQueryFactory):
    """
    Statistic criterion for filtering numeric datas
    """
    def __init__(self, model, criterion_model, inspector):
        CriterionQueryFactory.__init__(self, model, criterion_model, inspector)
        self.search1 = criterion_model.search1
        self.search2 = criterion_model.search2

    def filter_lte(self, attr):
        if self.search1:
            return attr <= self.search1
        return

    def filter_gte(self, attr):
        if self.search1:
            return attr >= self.search1
        return

    def filter_lt(self, attr):
        if self.search1:
            return attr < self.search1
        return

    def filter_gt(self, attr):
        if self.search1:
            return attr > self.search1
        return

    def bw(self, attr):
        if self.search1 and self.search2:
            return and_(attr > self.search1, attr < self.search2)

    def nbw(self, attr):
        if self.search1 and self.search2:
            return or_(attr <= self.search1, attr >= self.search2)


class DateCriterionQueryFactory(CriterionQueryFactory):
    """
    Statistic criterion related to Dates
    """
    def __init__(self, model, criterion_model, inspector):
        CriterionQueryFactory.__init__(self, model, criterion_model, inspector)
        self.search1 = criterion_model.search1
        self.search2 = criterion_model.search2

    def filter_dr(self, attr):
        # TODO
        pass

#   80 DATE_OPTIONS = (
#   81     ('', '- Tous -', ),
#   82     ('dr', u"Dans l'intervalle", ),
#   83     ('this_year', u"Depuis le début de l'année", ),
#   84     ('this_month', u"Ce mois-ci", ),
#   85     ("previous_year", u"L'année dernière", ),
#   86     ("previous_month", u"Le mois dernier", ),
#   87     ("nll", u"N'est pas renseigné(e)", ),
#   88     ("nnll", u"Est renseigné(e)", ),
#   89 )
