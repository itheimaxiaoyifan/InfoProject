from Info import Redis_store
from Info.constants import HOME_PAGE_MAX_NEWS
from Info.models import User, News, Category
from Info.modules.index import index_blu
from flask import render_template, current_app, session, request, jsonify

from Info.utils.response_code import RET


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

    # 查询首页导航部分并进行展示
    try:
        news_category = Category.query.all()
    except Exception as e:
        current_app.logger.error(e)
    # 返回所有的数据
    data = {
        "user_info": user.to_dict() if user else None,
        "news_obj": news_obj,
        "news_category": news_category
    }
    return render_template('news/index.html', data=data)


@index_blu.route('/favicon.ico')
def get_favicon():
    # return current_app.send_static_file('news/favicon.ico')
    return current_app.send_static_file("news/favicon.ico")


@index_blu.route('/news_list')
def news_list():
    param_dict = request.args
    page = param_dict.get('page', 1)
    cid = param_dict.get('cid', 1)
    per_page = param_dict.get('per_page', HOME_PAGE_MAX_NEWS)
    try:
        page = int(page)
        cid = int(cid)
        per_page = int(per_page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='参数错误')

    filters = [News.status == 0]
    if cid != 1:
        filters.append(News.category_id == cid)
    try:
        NewsPaginationObj = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page, per_page,
                                                                                                   False)
        items = NewsPaginationObj.items  # 查询到的第page页的数据(其实是python的模型对象列表)
        total_page = NewsPaginationObj.pages
        current_page = NewsPaginationObj.page
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询失败")
    # 返回数据之前需要把每一个模型对象转换成字典格式，因为js不认识python的模型对象
    news_dict = []
    for i in items:
        news_dict.append(i.to_basic_dict())
    return jsonify(errno=RET.OK, errmsg='OK', newsList=news_dict, totalPage=total_page, currentPage=current_page)
