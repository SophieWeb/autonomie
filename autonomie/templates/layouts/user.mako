<%doc>
    * Copyright (C) 2012-2016 Croissance Commune
 * Authors:
       * Arezki Feth <f.a@majerti.fr>;
       * Miotte Julien <j.m@majerti.fr>;
       * TJEBBES Gaston <g.t@majerti.fr>
 This file is part of Autonomie : Progiciel de gestion de CAE.
    Autonomie is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    Autonomie is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with Autonomie.  If not, see <http://www.gnu.org/licenses/>.
</%doc>
<%inherit file="/layouts/default.mako" />
<%namespace file="/base/utils.mako" import="format_mail" />
<%block name="headtitle">
</%block>
<%block name='content'>
<div class='panel panel-default page-block'>
    <div class='panel-heading'>
        <div class='row'>
            <div class='col-md-3 col-xs-12 bordered'>
                <div class='row'>
                    <div class='col-md-3 text-center'>
                        <i class='fa fa-user fa-4x'></i>
                    </div>
                    <div class='col-md-9'>
                        <div>
                            % if layout.current_user_object.civilite:
                                ${api.format_civilite(layout.current_user_object.civilite)}&nbsp;
                            % endif
                            ${api.format_account(layout.current_user_object)}
                        </div>
                        <div><small class="text-primary">${format_mail(layout.current_user_object.email)}</small></div>
                        <div style="margin:.5em 0;">
                            % if layout.current_user_object.userdatas and layout.current_user_object.userdatas.situation_situation:
                                <small><strong>${layout.current_user_object.userdatas.situation_situation.label}</strong></small>
                            % endif
                            % if layout.current_user_object.userdatas and layout.current_user_object.userdatas.situation_societariat_entrance:
                                <span class="label label-success">Sociétaire</span>
                            % endif
                            % if request.has_permission("edit.user", layout.current_user_object):
                            <a
                                class='btn btn-default btn-small pull-right'
                                href="${request.route_path('/users/{id}/edit', id=layout.current_user_object.id)}"
                                >
                                <i class='fa fa-pencil'></i>
                            </a>
                            % endif
                        </div>
                    </div>
                </div>
            </div>
            <div class='col-md-9 hidden-xs'>
            <%block name='usertitle'>
            % if title is not UNDEFINED and title is not None:
            <h3>${title}</h3>
            % endif
            </%block>
            </div>
        </div>
    </div>
    <div class='panel-body'>
        <div class='row'>
            <div class='col-md-3'>
            <%block name='rightblock'>
                ${request.layout_manager.render_panel('sidebar', layout.usermenu)}
            </%block>
            </div>
            <div class='col-md-9'>
            <%block name='mainblock'>
                Main
            </%block>
            </div>
        </div>
    </div>
</div>
</%block>