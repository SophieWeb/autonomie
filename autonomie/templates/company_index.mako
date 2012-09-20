<%doc>
    Company index page shows last activities and elapsed invoices
</%doc>
<%namespace file="/base/utils.mako" import="format_text" />
<%namespace file="/base/utils.mako" import="format_client" />
<%namespace file="/base/utils.mako" import="format_project" />
<%namespace file="/base/utils.mako" import="table_btn"/>
<%inherit file="base.mako"></%inherit>
<%block name='content'>
<div class='row'>
    <div class='span4'>
        %if elapsed_invoices:
            <div class='well' style="margin-top:10px">
                <div class='section-header'>
                    Vos impayés de + de 45 jours
                </div>
                <table class='table table-stripped'>
                    <thead>
                        <th>Numéro</th>
                        <th>Client</th>
                        <th>Total</th>
                        <th></th>
                    </thead>
                    <tbody>
                        % for invoice in elapsed_invoices[:5]:
                            <tr>
                                <td>
                                    ${invoice.officialNumber}
                                </td>
                                <td>
                                    ${format_client(invoice.project.client)}
                                </td>
                                <td>
                                    ${api.format_amount(invoice.total())|n}&nbsp;€
                                </td>
                                <td>
                                    ${table_btn(request.route_path("invoice", id=invoice.id), u"Voir", u"Voir ce document", icon=u"icon-search")}
                                </td>
                            </tr>
                        % endfor
                    </tbody>
                </table>
                % if len(elapsed_invoices) > 5:
                    <b>...</b>
                    <a class='btn btn-primary'
                        href="${request.route_path('company_invoices', id=company.id, _query=dict(paid="notpaid"))}">
                        Voir plus
                    </a>
                % else:
                    <a class='btn btn-primary'
                        href="${request.route_path('company_invoices', id=company.id, _query=dict(paid="notpaid"))}">
                        Voir
                    </a>
                % endif
            </div>
        %endif
    </div>
    <div class='span6 offset1'>
        % if request.config.has_key('welcome'):
            <p>
                ${format_text(request.config['welcome'])}
            </p>
        % endif
    </div>
</div>

<div class='row'>
    <div class='span12'>
        <div class='well' style="margin-top:10px">
            <div class='section-header'>Dernières activités</div>
            <table class='table table-stripped'>
                <thead>
                    <th>
                        Projet
                    </th>
                    <th>
                        Client
                    </th>
                    <th>
                        Nom du document
                    </th>
                    <th>
                        Dernière modification
                    </th>
                </thead>
                <tbody>
                    % for task in tasks:
                        <tr>
                            <td>
                                ${format_project(task.project)}
                            </td>
                            <td>
                                ${format_client(task.project.client)}
                            </td>
                            <td>${task.name}</td>
                            <td>${api.format_status(task)}</td>
                            <td>
                                ${table_btn(request.route_path(task.type_, id=task.id), u"Voir", u"Voir ce document", icon=u"icon-search")}
                            </td>
                        </tr>
                    % endfor
                </tbody>
            </table>
        </div>
    </div>
</div>
</%block>
