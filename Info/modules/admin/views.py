from Info import db
from Info.constants import ADMIN_USER_PAGE_MAX_COUNT, QINIU_DOMIN_PREFIX
from Info.models import User, News, Category
from Info.utils.qiniu_pro import qinniu_storage
from Info.utils.response_code import RET
from . import admin_blu
from flask import render_template, request, current_app, session, redirect, url_for, jsonify


@admin_blu.route('/login', methods=['GET', 'POST'])
def admin_login():
    """
    如果是get请求，直接返回登录页面
    如果是post请求：
        1.拿到参数并进行判空
        2.查询数据库看用户是否存在
        3.校验密码是否通过
        4.校验是否是管理员
        5.保存用户登录信息
        6.返回登录成功页面
    :return:
    """
    if request.method == 'GET':
        user_id = session.get('user_id', None)
        is_admin = session.get('is_admin', False)
        if user_id and is_admin:
            return redirect(url_for("admin.admin_index"))
        return render_template('admin/login.html')
    username = request.form.get('username')
    password = request.form.get('password')
    if not all([username, password]):
        return render_template('admin/login.html', errmsg='参数不足')
    try:
        user = User.query.filter(User.mobile == username).first()
    except Exception as e:
        current_app.logger.error(e)
        return render_template('admin/login.html', errmsg='数据查询失败')
    if not user:
        return render_template('admin/login.html', errmsg='用户不存在')
    if not user.check_passowrd(password):
        return render_template('admin/login.html', errmsg='账号或者密码不正确')
    if not user.is_admin:
        return render_template('admin/login.html', errmsg='无登录权限')
    session['nick_name'] = username
    session['mobile'] = user.mobile
    session['user_id'] = user.id
    session['is_admin'] = True
    return redirect(url_for('admin.admin_index'))


@admin_blu.route('/index', methods=['GET', 'POST'])
def admin_index():
    """
    直接手打/admin/index，需要进行判断是否是管理员，如果是则返回admin/index页面，如果不是则跳转到主页面
    通过钩子函数@admin_blu.before_reuqest：def check_admin实现
    :return:
    """
    return render_template('admin/index.html')


@admin_blu.route('/logout')
def logout():
    session.pop('user_id')
    session.pop('nick_name')
    session.pop('mobile')
    session.pop('is_admin')
    return redirect('/admin/login')


@admin_blu.route('/user_count')
def user_count():
    """
    :return:用户总数，用户月新增数，用户日新增数
    用户总数可以通过查询来得到
    月新增数需要通过函数来得到
    日新增数需要通过函数来得到
    """
    total_count = 0
    try:
        total_count = User.query.filter(User.is_admin == False).count()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='查询数据库失败')

    # 月新增数
    month_count = 0
    import time
    from datetime import datetime, timedelta
    t = time.localtime()
    cur_mon_str = '%d-%02d-01' % (t.tm_year, t.tm_mon)
    cur_mon = datetime.strptime(cur_mon_str, "%Y-%m-%d")
    try:
        month_count = User.query.filter(User.is_admin == False, User.create_time >= cur_mon).count()
    except Exception as e:
        current_app.logger.error(e)
    # 日新增数
    day_count = 0
    cur_day_str = '%d-%02d-%02d' % (t.tm_year, t.tm_mon, t.tm_mday)
    cur_day = datetime.strptime(cur_day_str, "%Y-%m-%d")
    try:
        month_count = User.query.filter(User.is_admin == False, User.create_time >= cur_mon).count()
    except Exception as e:
        current_app.logger.error(e)
    # 折线图
    active_time = []
    active_count = []
    for i in range(0, 31):
        startday = cur_day - timedelta(days=i)
        endday = cur_day - timedelta(days=(i - 1))
        cot = User.query.filter(User.is_admin == False, User.last_login >= startday, User.last_login < endday).count()
        active_count.append(cot)
        active_time.append(startday.strftime("%Y-%m-%d"))
    active_time.reverse()
    active_count.reverse()
    data = {
        "total_count": total_count,
        "month_count": month_count,
        "day_count": day_count,
        "active_time": active_time,
        "active_count": active_count
    }
    return render_template('admin/user_count.html', data=data)


@admin_blu.route('/user_list')
def user_list():
    p = request.args.get("p", 1)
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        p = 1
    users = []
    total_page = 1
    cur_page = 1
    try:
        paginate = User.query.filter(User.is_admin == False).order_by(User.last_login.desc()).paginate(p,
                                                                                                       ADMIN_USER_PAGE_MAX_COUNT)
        items = paginate.items
        total_page = paginate.pages
        cur_page = paginate.page
    except Exception as e:
        current_app.logger.error(e)
    user_list = []
    if items:
        for i in items:
            user_list.append(i.to_dict())
    data = {
        "user_list": user_list,
        "total_page": total_page,
        "cur_page": cur_page

    }
    return render_template('admin/user_list.html', data=data)


@admin_blu.route('/news_review')
def news_review():
    """
    参数：当前页面p，通过get请求获取
    :return: id	标题	发布时间	状态	管理操作
    """
    p = request.args.get("p", 1)
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        p = 1
    news = []
    total_page = 1
    cur_page = 1
    try:
        paginate = News.query.filter(News.status == 1).order_by(News.create_time.desc()).paginate(p,
                                                                                                  ADMIN_USER_PAGE_MAX_COUNT)
        items = paginate.items
        total_page = paginate.pages
        cur_page = paginate.page
    except Exception as e:
        current_app.logger.error(e)
    newslist = []
    for i in items:
        newslist.append(i.to_review_dict())
    data = {
        "newslist": newslist,
        "total_page": total_page,
        "cur_page": cur_page
    }
    return render_template('admin/news_review.html', data=data)


@admin_blu.route('/news_review_detail/<int:news_id>')
def news_review_detail(news_id):
    """
    参数：需要审核的新闻的id
    :return:
    """
    if request.method == 'GET':
        news = None
        try:
            news = News.query.get(news_id)
        except Exception as e:
            current_app.logger.error(e)
        if not news:
            return jsonify(errno=RET.NODATA, errmsg='新闻不存在')
    data = {
        "news": news.to_dict()
    }
    return render_template('admin/news_review_detail.html', data=data)


@admin_blu.route('/news_review_action', methods=['POST'])
def news_review_action():
    """
    :param  "action": action,
            "news_id": news_id,
            "reason": reason
    :return:
    """
    param_dict = request.json
    news_id = param_dict.get('news_id')
    action = param_dict.get('action')
    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')

    if action not in ('accept', 'reject'):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不正确')

    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='数据库查询失败')
    if not news:
        return jsonify(errno=RET.NODATA, errmsg="未查询到数据")
    if action == 'accept':
        news.status = 0
    else:
        reason = param_dict.get('reason')
        if not reason:
            return jsonify(errno=RET.PARAMERR, errmsg="请输入拒绝原因")
        news.status = -1
        news.reason = reason
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="数据库操作失败")
    return jsonify(errno=RET.OK, errmsg='操作成功')


@admin_blu.route('/news_edit')
def news_edit():
    """
    :param
    :return:
    """
    p = request.args.get("p", 1)
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        p = 1
    news = []
    total_page = 1
    cur_page = 1
    try:
        paginate = News.query.filter(News.status == 0).order_by(News.create_time.desc()).paginate(p,
                                                                                                  ADMIN_USER_PAGE_MAX_COUNT)
        items = paginate.items
        total_page = paginate.pages
        cur_page = paginate.page
    except Exception as e:
        current_app.logger.error(e)
    newslist = []
    for i in items:
        newslist.append(i.to_review_dict())
    data = {
        "newslist": newslist,
        "total_page": total_page,
        "cur_page": cur_page
    }
    return render_template("admin/news_edit.html", data=data)


@admin_blu.route('/news_edit_detail/<int:news_id>')
def news_edit_detail(news_id):
    news = None
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
    if not news:
        return jsonify(errno=RET.DBERR, errmsg="新闻不存在")
    try:
        categories = Category.query.all()
    except Exception as e:
        current_app.logger.error(e)
    category_lst = []
    for i in categories:
        category_lst.append(i.to_dict())
    data = {
        "news": news.to_dict(),
        "category_lst": category_lst
    }
    return render_template("admin/news_edit_detail.html", data=data)


@admin_blu.route('/news_edit_action', methods=['POST'])
def news_edit_action():
    """
    param news_id
    :return:
    """
    news_id = request.form.get('news_id')
    title = request.form.get('title')
    digest = request.form.get('digest')
    content = request.form.get('content')
    index_image = request.form.get('index_image')
    category_id = request.form.get('category_id')
    if not all([title, digest, content, category_id]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
    if not news:
        return jsonify(errno=RET.NODATA, errmsg='新闻查询不到')
    if index_image:
        try:
            index_image = index_image.read()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

        try:
            key = qinniu_storage(index_image)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.THIRDERR, errmsg="七牛云上传错误")
        news.index_image_url = QINIU_DOMIN_PREFIX + key
    news.title = title
    news.digest = digest
    news.content = content
    news.category_id = category_id
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="数据库操作失败")
    return jsonify(errno=RET.OK, errmsg="操作成功")


@admin_blu.route('/news_type', methods=["GET", "POST"])
def news_type():
    """
    判断请求方式如果为GET，则展示页面信息.页面信息有id name
    如果是Post请求，先取得参数cname 和 分类ID cid，如果cname不存在直接报错，如果cid存在，则category.name = cname
    如果cid 不存在，则新增一条category信息，category.name = cname
    :return:
    """
    if request.method == 'GET':
        try:
            categories = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)
            return render_template('admin/news_type.html', errmsg="查询数据错误")
        categories_lst = []
        for i in categories:
            categories_lst.append(i.to_dict())
        categories_lst.pop(0)
        data = {
            "categories_lst": categories_lst
        }
        return render_template('admin/news_type.html', data=data)
    #　post请求的情况
    cname = request.json.get('name')
    cid = request.json.get("id")
    if not cname:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    if cid:
        try:
            cid = int(cid)
            category = Category.query.get(cid)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
        if not category:
            return jsonify(errno=RET.NODATA, errmsg="未查询到分类数据")
        category.name = cname
    else:
        category = Category()
        category.name = cname
        db.session.add(category)
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="数据库操作失败")

    return jsonify(errno=RET.OK, errmsg="操作成功")