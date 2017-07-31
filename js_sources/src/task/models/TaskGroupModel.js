/*
 * File Name : TaskGroupModel.js
 *
 * Copyright (C) 2017 Gaston TJEBBES g.t@majerti.fr
 * Company : Majerti ( http://www.majerti.fr )
 *
 * This software is distributed under GPLV3
 * License: http://www.gnu.org/licenses/gpl-3.0.txt
 *
 */
import _ from 'underscore';
import Bb from 'backbone';
import TaskLineCollection from './TaskLineCollection.js';


const TaskGroupModel = Bb.Model.extend({
    props: [
        'id',
        'order',
        'title',
        'description',
        'lines',
        'task_id',
    ],
    constructor: function() {
        arguments[0] = _.pick(arguments[0], this.props);
        Bb.Model.apply(this, arguments);
    },
    initialize: function(){
        this.populate();
        this.on('change:id', this.populate.bind(this));
    },
    populate: function(){
        if (this.get('id')){
            this.lines = new TaskLineCollection(this.get('lines'));
            this.lines.url = this.url() + '/task_lines';
        }
    },
    loadProductGroup: function(sale_product_group_datas){
        this.set('title', sale_product_group_datas.title);
        this.set('description', sale_product_group_datas.description);
    },
    ht: function(){
        return this.lines.ht();
    },
    tvaParts: function(){
        return this.lines.tvaParts();
    },
    ttc: function(){
        return this.lines.ttc();
    }
});
export default TaskGroupModel;