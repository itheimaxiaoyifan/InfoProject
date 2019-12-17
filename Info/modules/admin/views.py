from Info.models import User
from . import admin_blu
from flask import render_template, request, current_app, session, redirect, url_for


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
    session['user_id'] = user.id
    session['password'] = password
    session['is_admin'] = True
    return redirect(url_for('admin.admin_index'))


@admin_blu.route('/index', methods=['GET', 'POST'])
def admin_index():
    return render_template('admin/index.html')
