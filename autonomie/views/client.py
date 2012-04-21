# -*- coding: utf-8 -*-
# * File Name : customer.py
#
# * Copyright (C) 2010 Gaston TJEBBES <g.t@majerti.fr>
# * Company : Majerti ( http://www.majerti.fr )
#
#   This software is distributed under GPLV3
#   License: http://www.gnu.org/licenses/gpl-3.0.txt
#
# * Creation Date : 28-03-2012
# * Last Modified :
#
# * Project : Autonomie
#
"""
    Client views
"""
import logging
from functools import partial

from deform import ValidationFailure
from deform import Form
from deform import Button

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPForbidden
from pyramid.url import route_path
from pyramid.url import current_route_url

from autonomie.models import DBSESSION
from autonomie.models.model import Client
from autonomie.utils.forms import merge_session_with_post
from autonomie.views.forms import ClientSchema

from webhelpers import paginate

log = logging.getLogger(__name__)
def get_client_form(edit=False, path=""):
    """
        Returns the client add/edit form
    """
    schema = ClientSchema().bind(edit=edit)
    form = Form(schema, actions=path, buttons=(Button(name='submit',
                                        title=u'Validez',
                                        type='submit'),))
    return form

def get_page_url(request, page):
    """
        Return a url generator for pagination
    """
    args = request.GET
    args['page'] = str(page)
    return current_route_url(request, page=page, _query=args)

@view_config(route_name='company_clients', renderer='company_clients.mako',
                                                request_method='GET')
def company_clients(request):
    """
        Return the list of all the clients
        Expects a url attribute cid
        Accepts direction, sort, search as GET
    """
    search = request.params.get("search", "")
    sort = request.params.get('sort', 'name')

    direction = request.params.get("direction", 'asc')
    if direction not in ['asc', 'desc']:
        direction = 'asc'

    cid = request.matchdict.get('cid')
    dbsession = DBSESSION()

    avatar = request.session['user']
    try:
        company = avatar.get_company(cid)
    except KeyError:
        raise HTTPForbidden()
    toquery = (Client.id, Client.contactLastName, Client.contactFirstName,
                        Client.name)
    if cid != -1:
        clients = dbsession.query(*toquery).filter(
                Client.name.like(search+"%"),
                Client.id_company == cid).order_by(sort + " " + direction)
    else:
        clients = dbsession.query(*toquery).filter(
            Client.name.like(search+"%")).order_by(sort + " " + direction)
    form = get_client_form(path=route_path('company_clients', request,
                                            cid=cid))

    page_url = partial(get_page_url, request=request)
    current_page = int(request.params.get("page", 1))
    records = paginate.Page(clients,
                    current_page,
                    url=page_url,
                    items_per_page=10,)
    return dict(title=u"Clients",
                clients=records,
                company=company,
                html_form=form.render())

@view_config(route_name='company_clients', renderer='company_client.mako', request_method='POST')
@view_config(route_name='company_client', renderer='company_client.mako', request_param='edit')
def company_client(request):
    """
        Return the client editform
    """
    cid = request.matchdict.get('cid')
    client_id = request.matchdict.get('id')
    avatar = request.session['user']
    company = avatar.get_company(cid)
    if client_id: #edition
        client = company.get_client(client_id)
        edit = True
    else: #new entry
        client = Client()
        client.id_company = cid
        edit = False
    form = get_client_form(edit=edit)
    dbsession = DBSESSION()
    if 'submit' in request.params:
        # form POSTed
        datas = request.params.items()
        try:
            app_datas = form.validate(datas)
        except ValidationFailure, errform:
            html_form = errform.render()
        else:
            client = merge_session_with_post(client, app_datas)
            dbsession.merge(client)
            if edit:
                message = u"Le client <b>%s</b> a été édité avec succès" % (
                                                                client.name,)
            else:
                message = u"Le client <b>%s</b> a été ajouté avec succès" % (
                                                                client.name,)
            request.session.flash(message, queue='main')
            return HTTPFound(route_path('company_clients', request, cid=cid))
    else:
        html_form = form.render(client.appstruct())
    return dict(title=client.name,
                client=client,
                html_form=html_form,
                company=company)

@view_config(route_name='company_client', renderer='client_view.mako', request_method='GET')
def company_client_view(request):
    """
        Return the view of a client
    """
    cid = request.matchdict.get('cid')
    client_id = request.matchdict.get('id')
    avatar = request.session['user']
    company = avatar.get_company(cid)
    client = company.get_client(client_id)
    return dict(title=client.name,
                client=client,
                company=company)
