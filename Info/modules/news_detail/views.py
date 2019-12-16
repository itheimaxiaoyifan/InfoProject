from Info import db
from Info.constants import CLICK_RANK_MAX_NEWS
from Info.models import User, News, Comment
from Info.utils.common import get_login_data
from Info.utils.response_code import RET
from . import news_detail_blu
import json
from flask import render_template, session, current_app, abort, g, request, jsonify


@news_detail_blu.route('/<int:news_id>')
@get_login_data
def news_detail(news_id):
    """

    :param news_id:
    :return:
    """
    # 1.获取到登录信息
    user = g.user
    try:
        news_obj = News.query.order_by(News.clicks.desc()).limit(CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)

    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        abort(404)
    if not news:
        abort(404)
    news.clicks += 1
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()

    # 展示收藏或者取消收藏按钮
    is_collected = False
    if user:
        if news in user.collection_news:
            is_collected = True

    # 展示评论信息
    try:
        comments = Comment.query.filter(Comment.news_id == news.id).order_by(Comment.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库查询错误')
    comment_lst = []
    for i in comments:
        comment_lst.append(i.to_dict())

    # 展示作者信息 通过user_id = news.user_id来找到作者
    author = news.user
    if not author:
        return jsonify(errno=RET.NODATA, errmsg='作者不存在')

    # 展示关注信息
    is_followed = False
    if user:
        if user in author.followers:
            is_followed = True

    if user:
        user_like_comments = []
        for i in user.like_comments.all():
            user_like_comments.append(i.to_dict())
    data = {
        "user_info": user.to_dict() if user else None,
        "news_obj": news_obj,
        "news": news.to_dict(),
        "is_collected": is_collected,
        "comments": comment_lst,
        "author": author.to_dict(),
        "is_followed": is_followed,
        "user_like_comments": user_like_comments if user else []
    }
    return render_template('news/detail.html', data=data)


@news_detail_blu.route('/news_collect', methods=['POST'])
@get_login_data
def news_collect():
    """
    :param "news_id": news_id
            action: collect ,cancel_collect
    """
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')
    param_dict = request.json
    news_id = param_dict.get('news_id')
    action = param_dict.get('action')
    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')
    if action not in ("collect", "cancel_collect"):
        return jsonify(errno=RET.PARAMERR, errmsg='参数有误')
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库查询错误')
    if not news:
        return jsonify(errno=RET.NODATA, errmsg='新闻不存在')
    if action == 'collect':
        # 执行收藏操作
        user.collection_news.append(news)
    else:
        # 执行取消收藏操作
        user.collection_news.remove(news)
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='数据库提交错误')
    return jsonify(errno=RET.OK, errmsg='操作成功')


@news_detail_blu.route('/news_comment', methods=['POST'])
@get_login_data
def news_comment():
    """
    news_id comment parent_id
    :return:
    """
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')
    param_dict = request.json
    news_id = param_dict.get('news_id')
    comment = param_dict.get('comment')
    parent_id = param_dict.get('parent_id')
    if not all([news_id, comment]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库查询错误')
    if not news:
        return jsonify(errno=RET.NODATA, ERRMSG='数据不存在')
    from datetime import datetime
    comment_obj = Comment()
    comment_obj.create_time = datetime.now()
    comment_obj.user_id = user.id
    comment_obj.news_id = news_id
    comment_obj.content = comment
    comment_data = comment_obj.to_dict()
    if parent_id:
        comment_obj.parent_id = parent_id
    try:
        db.session.add(comment_obj)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DATAERR, ERRMSG='保存评论失败')
    return jsonify(errno=RET.OK, errmsg='评论成功', data=comment_obj.to_dict())


@news_detail_blu.route('/comment_like', methods=['POST'])
@get_login_data
def comment_like():
    """
    :param
    comment_id : comment_id
    action: add or remove
    :return: 操作成功
    """
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')
    param_dict = request.json
    comment_id = param_dict.get('comment_id')
    action = param_dict.get('action')  # add
    if not all([action, comment_id]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不全')
    if action not in ('add', 'remove'):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    try:
        comment = Comment.query.get(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询评论失败')
    if not comment:
        return jsonify(errno=RET.NODATA, errmsg='评论不存在')
    if action == 'add':
        user.like_comments.append(comment)
        comment.like_count += 1
    else:
        user.like_comments.remove(comment)
        comment.like_count -= 1
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='提交到数据库失败')
    return jsonify(errno=RET.OK, errmsg="操作成功")


@news_detail_blu.route('/followed_user', methods=['POST'])
@get_login_data
def followed_user():
    """
    :param
    author_id: user_id
    action : follow or unfollow
    :return:
    """
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')
    param_dict = request.json
    author_id = param_dict.get('author_id')
    action = param_dict.get('action')  # follow or unfollow
    if not all([action, author_id]):
        return jsonify(errno=RET.PARAMERR, errmsg='缺少参数')
    if action not in ('follow', 'unfollow'):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    try:
        author = User.query.get(author_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='查询作者失败')
    if not author:
        return jsonify(errno=RET.NODATA, errmsg='作者不存在')
    if action == 'follow':
        # 执行关注
        author.followers.append(user)
    else:
        author.followers.remove(user)
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DATAERR, errmsg='数据库提交失败')

    return jsonify(errno=RET.OK, errmsg='OK')
