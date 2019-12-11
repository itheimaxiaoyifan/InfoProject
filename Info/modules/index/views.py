from Info import Redis_store
from Info.modules.index import index_blu
from flask import render_template, current_app


@index_blu.route('/')
def index():
    # session['a1'] = 'python'
    # Redis_store.set('a1', 'xiaoyifan')
    return render_template('news/index.html')


@index_blu.route('/favicon.ico')
def get_favicon():
    # return current_app.send_static_file('news/favicon.ico')
    return current_app.send_static_file("news/favicon.ico")
