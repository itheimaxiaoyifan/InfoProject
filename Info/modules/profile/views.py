from Info import db
from Info.constants import QINIU_DOMIN_PREFIX, USER_COLLECTION_MAX_NEWS
from Info.models import News
from Info.utils.common import get_login_data
from Info.utils.response_code import RET
from . import profile_blu
from flask import render_template, g, redirect, request, jsonify, session, current_app


@profile_blu.route('/info')
@get_login_data
def info():
    user = g.user
    if not user:
        return redirect('/')
    data = {
        "user_info": user.to_dict()
    }
    return render_template('news/user.html', data=data)


@profile_blu.route('/base_info', methods=["GET", "POST"])
@get_login_data
def base_info():
    user = g.user
    if not user:
        return redirect('/')
    # 如果是GET请求
    if request.method == 'GET':
        data = {
            "user_info": user.to_dict()
        }
        return render_template('news/user_base_info.html', data=data)
    # 如果是POST请求
    param_dict = request.json
    """
    "signature": signature,
    "nick_name": nick_name,
    "gender": gender
    """
    signature = param_dict.get('signature')
    nick_name = param_dict.get('nick_name')
    gender = param_dict.get('gender')
    if not all([signature, nick_name, gender]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    if gender not in ('MAN', 'WOMAN'):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    user.signature = signature
    user.nick_name = nick_name
    user.gender = gender
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='数据库提交失败')
    session['nick_name'] = nick_name
    return jsonify(errno=RET.OK, errmsg='操作成功')


@profile_blu.route('/pic_info', methods=["POST", "GET"])
@get_login_data
def pic_info():
    user = g.user
    if not user:
        return redirect('/')
    if request.method == 'GET':
        data = {
            "user_info": user.to_dict()
        }
        return render_template('news/user_pic_info.html', data=data)

    # 1获取上传的头像的参数
    try:
        param_data = request.files.get('avatar').read()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    # 2把头像上传到七牛云
    from Info.utils.qiniu_pro import qinniu_storage
    try:
        ret_key = qinniu_storage(param_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="七牛云上传错误")
    # 3.把头像信息更新到当前用户的模型中
    user.avatar_url = ret_key
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DATAERR, errmsg="数据库上传错误")

    data = {
        "avatar_url": QINIU_DOMIN_PREFIX + ret_key
    }
    return jsonify(errno=RET.OK, errmsg="修改头像成功", data=data)


@profile_blu.route('/pass_info', methods=["POST", "GET"])
@get_login_data
def pass_info():
    user = g.user
    if not user:
        return redirect('/')
    if request.method == 'GET':
        data = {
            "user_info": user.to_dict()
        }
        return render_template('news/user_pass_info.html', data=data)
    param_dict = request.json
    old_password = param_dict.get('old_password')
    new_password = param_dict.get('new_password')
    new_password2 = param_dict.get('new_password2')
    if not all([old_password, new_password, new_password2]):
        return jsonify(errno=RET.PARAMERR, errmsg='缺少参数')
    if not user.check_passowrd(old_password):
        return jsonify(errno=RET.PWDERR, errmsg='密码错误')
    if new_password != new_password2:
        return jsonify(errno=RET.PWDERR, errmsg='两次密码不一致')
    user.password = new_password
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="数据库操作失败了")
    return jsonify(errno=RET.OK, errmsg='操作成功')


@profile_blu.route('/collect_news', methods=["GET"])
@get_login_data
def collect_news():
    user = g.user
    if not user:
        return redirect('/')
    page_now = request.args.get('P', 1)
    try:
        page_now = int(page_now)
    except Exception as e:
        current_app.logger.error(e)
        page_now = 1

    current_page_news = []
    total_pages = 1
    current_page = 1
    try:
        collection_news_mod = user.collection_news.paginate(page_now, USER_COLLECTION_MAX_NEWS, False)
        current_page_news = collection_news_mod.items
        total_pages = collection_news_mod.pages
        current_page = collection_news_mod.page
    except Exception as e:
        current_app.logger.error(e)
    current_page_news_lst = []
    for i in current_page_news:
        current_page_news_lst.append(i.to_dict())
    data = {
        "current_page_news_lst": current_page_news_lst,
        "total_pages": total_pages,
        "current_page": current_page
    }
    return render_template('news/user_collection.html', data=data)


@profile_blu.route('/news_list', methods=['GET'])
@get_login_data
def news_list():
    user = g.user
    if not user:
        return redirect('/')
    current_page = request.args.get('P')
    news_items = []
    total_pages = 1
    cur_page = 1
    try:
        news = News.query.filter(News.user_id == user.id).order_by(News.create_time.desc()).paginate(current_page, USER_COLLECTION_MAX_NEWS, False)
        news_items = news.items
        total_pages = news.pages
        cur_page = news.page
    except Exception as e:
        current_app.logger.error(e)
    news_items_lst = []
    for i in news_items:
        news_items_lst.append(i.to_review_dict())
    data = {
        "news_items_lst": news_items_lst,
        "total_pages": total_pages,
        "cur_page": cur_page
    }
    return render_template('news/user_news_list.html', data=data)
