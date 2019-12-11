import random
from re import match

from Info import Redis_store
from Info.constants import SMS_CODE_REDIS_EXPIRES
from Info.models import User
from Info.modules.passport import passport_blu
from flask import request, render_template, jsonify, current_app, make_response
from Info.utils.captcha.captcha import captcha
from Info.utils.response_code import RET
from Info.utils.yuntongxun.sms import CCP


@passport_blu.route('/image_code')
def get_img_code():
    # 1验证参数
    imageCodeId = request.args.get('image_code_id')  # 获取uuid（唯一标识用户浏览器）
    if not imageCodeId:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    # 2生成验证码
    name, test, content = captcha.generate_captcha()
    # 3保存验证码
    try:
        Redis_store.set('uuid_' + imageCodeId, test, SMS_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='数据错误')
    # 4返回验证码
    response = make_response(content)
    response.headers['Content-Type'] = 'image/jpg'
    return response


@passport_blu.route('/sms_code', methods=['POST'])
def get_sms_code():
    # 1.获取参数并进行校验 手机号码，验证码，imageCodeId
    param_dict = request.json
    mobile = param_dict.get('mobile')  # 用户输入的手机号
    image_code = param_dict.get('image_code')  # 用户输入的验证码
    image_code_id = param_dict.get('image_code_id')  # 用户的uuid（通过前端传的）
    if not all([mobile, image_code, image_code_id]):
        return jsonify(errno=RET.DATAERR, eemsg='缺少参数')
    if not match(r"^1[3578]\d{9}$", mobile):
        return jsonify(errno=RET.DATAERR, errmsg="手机格式不正确")
    # 2.对比图片验证码
    # 2.1 通过uuid获取redis里面的uuid_imageCodeId
    try:
        real_image_code = Redis_store.get('uuid_' + image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据查询错误')
    if not real_image_code:
        return jsonify(errno=RET.NODATA, errmsg='验证码已经过期')
    # 2.2 将1的验证码和2.1拿到的uuid_imageCodeId文本进行对比
    if image_code.lower() != real_image_code.decode().lower():
        return jsonify(errno=RET.DATAERR, errmsg='输入验证码错误')
    # 3.发送短信验证码
    # 3.1验证手机号是否已经被注册
    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据查询错误')
    if user:
        return jsonify(errno=RET.DATAEXIST, errmsg='数据已经存在')
    # 3.2代码生产发送的短信的内容并发送短信
    result = random.randint(0, 999999)
    sms_code = '%6d' % result
    ccp = CCP()
    result = ccp.send_template_sms(mobile, [sms_code, 5], 1)  # 5是代表5分钟有效,1是代表按照模板1进行发送
    if result == -1:
        return jsonify(errno=RET.DATAERR, errmsg='发送短信失败')
    # 3.3保存用户发送的短信内容
    try:
        Redis_store.set('sms_code_' + mobile, sms_code, SMS_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='数据保存失败')
    # 3.4返回发送成功的响应
    return jsonify(errno=RET.OK, errmsg='发送短信成功')
