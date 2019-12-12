from Info import Redis_store
from Info.models import User, News
from Info.modules.index import index_blu
from flask import render_template, current_app, session


@index_blu.route('/')
def index():
    # 1.获取到登录信息
    user_id = session.get('user_id')
    # 2.通过id获取用户信息
    user = None
    if user_id:
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)

    try:
        news_obj = News.query.order_by(News.clicks.desc()).limit(6)
    except Exception as e:
        current_app.logger.error(e)

    # 返回所有的数据
    data = {
            "user_info": user.to_dict() if user else None,
            "news_obj": news_obj,
            }
    return render_template('news/index.html', data=data)


@index_blu.route('/favicon.ico')
def get_favicon():
    # return current_app.send_static_file('news/favicon.ico')
    return current_app.send_static_file("news/favicon.ico")
