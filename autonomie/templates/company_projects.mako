<%inherit file="base.mako"></%inherit>
<%namespace file="/base/pager.html" import="pager"/>
<%block name='actionmenu'>
<ul class='nav nav-pills'>
    <li>
    <a class='btn-primary' title='Créer un nouveau projet' href='#new' onclick="$('#addform').dialog('open');">
        Ajouter un Projet
    </a>
    </li>
    <li>
    <form class='navbar-form pull-right form-search' id='search_form' method='GET'>
        <input type='text' name='search' class='input-medium search-query' value="${request.params.get('search', '')}">
        <button type="submit" class="btn">Rechercher</button>
    </form>
    </li>
</ul>
</%block>
<%block name='content'>
<table class="table table-striped table-condensed">
    <thead>
        <tr>
            <th>Code</th>
            <th>Nom du projet</th>
            <th>Client</th>
            <th>Actions</th>
        </tr>
    </thead>
    <tbody>
        % if projects:
            % for project in projects:
                <tr class='tableelement' id="${project.id}">
                    <td>${project.code}</td>
                    <td>${project.name}</td>
                    <td>${project.client.name}</td>
                    <td>
                        <div class='btn-group'>
                            <a class='btn' href='${request.route_path("company_project", cid=company.id, id=project.id)}'>
                                <span class='ui-icon ui-icon-pencil'></span>
                                Éditer
                            </a>
                            <a class='btn' href='${request.route_path("estimation", cid=company.id, id=project.id)}'>
                                <span class='ui-icon ui-icon-plusthick'></span>
                                Devis
                            </a>
                            <a class='btn' href='${request.route_path("company_project", cid=company.id, id=project.id)}'>
                                <span class='ui-icon ui-icon-plusthick'></span>
                                Facture
                            </a>
                            <a class='btn' href='${request.route_path("company_project", cid=company.id, id=project.id)}'>
                                <span class='ui-icon ui-icon-folder-collapsed'></span>
                                Archiver
                            </a>
                        </div>
                    </td>
                </tr>
            % endfor
        % else:
            <tr>
                <td colspan='6'>
                    Aucun projet n'a été créé pour l'instant
                </td>
            </tr>
        % endif
    </tbody>
</table>
${pager(projects)}
% if html_form is not UNDEFINED:
    <div id='addform' style="overflow:hidden;">
        ${html_form|n}
    </div>
% endif
</%block>
<%block name='footerjs'>
% if html_form is not UNDEFINED:
    $( function() {
    $("#addform").dialog({ autoOpen: false,
    modal:true,
    width:"auto",
    height:"auto",
    autoResize:true,
    title:"Ajouter un Projet"
    })
    });
% endif
</%block>

