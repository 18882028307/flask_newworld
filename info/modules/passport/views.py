from datetime import datetime
import random
import re

from werkzeug.wrappers import response

from info.libs.yuntongxun.sms import CCP
from info.models import User
from . import passport_blu
from flask import request, current_app, abort, make_response, jsonify, session
from info import redis_store, constants, db
from info.utils.response_code import RET
from info.utils.captcha.captcha import captcha


@passport_blu.route('/image_code')
def get_image_code():
    '''
    生成图片验证码
    :return:
    '''
    # 1. 获取参数 args: 取到url中 ? 后面的参数
    image_code_id = request.args.get('image_Code')
    # 2. 校验参数是否为空
    if not image_code_id:
        abort(403)

    # 3. 生成图片验证码
    name, text, image = captcha.generate_captcha()
    print('图片验证码是：{}'.format(text))
    # 4. 保存图片验证码
    try:
        redis_store.setex('ImageCode_'+image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        current_app.logger.error(e)
        abort(500)

    # 5.返回图片验证码
    response = make_response(image)
    # 设置数据类型，以便浏览器更加智能识别其是什么类型
    response.headers['Content-Type'] = 'img/jpg'
    return response


@passport_blu.route('/sms_code', methods=["POST"])
def send_sms_code():
    """
    发送短信的逻辑
    :return:
    """
    # 1.将前端参数转为字典
    data = request.json
    mobile = data.get('mobile')
    image_code = data.get('image_code')
    image_code_id = data.get('image_code_id')


    # 2. 校验参数(参数是否符合规则，判断是否有值)
    # 判断参数是否有值
    if not all([mobile, image_code, image_code_id]):
        # {"errno": "4100", "errmsg": "参数有误"}
        print('111')
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

    # 验证手机号是否正确
    # if not re.match('1[35678]\\d{9}', mobile):
    #     return jsonify(errno=RET.PARAMERR, errmsg='手机格式不正确')

    # 3. 先从redis中取出真实的验证码内容
    try:
        real_image_code = redis_store.get('ImageCode_'+image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据查询失败')
    # 如果real_image_code为空
    if not real_image_code:
        return jsonify(errno=RET.NODATA, errmsg='图片验证码已过期')

    # 4. 与用户的验证码内容进行对比，如果对比不一致，那么返回验证码输入错误
    if real_image_code.upper() != image_code.upper():
        return jsonify(errno=RET.DATAERR, errmsg='验证码输入错误')

    # 5. 如果一致，生成短信验证码的内容(随机数据)
    # 随机数字，保证数字长度为6位不够在前面补上0
    sms_code_str = "%06d" % random.randint(0, 999999)
    current_app.logger.debug('短信验证码内容是：%s'%sms_code_str)
    print("短信验证码是：{}".format(sms_code_str))
    # # 6. 使用第三方发送短信验证码
    # result = CCP().send_template_sms(mobile, [sms_code_str, constants.SMS_CODE_REDIS_EXPIRES / 5], '1')
    # if result != 0:
    #     # 代表发送失败
    #     return jsonify(errno=RET.THIRDERR, errmsg='发送短信失败')
    # 保存验证码内容到redis
    try:
        redis_store.set("SMS_" + mobile, sms_code_str, constants.SMS_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据保存失败')

    # 7. 告知发送结果
    return jsonify(errno=RET.OK, errmsg='发送成功')


@passport_blu.route('/register', methods=["POST"])
def register():
    """
    注册功能
    :return:
    """
    if request.method == "POST":
        # 1. 获取参数和判断是否有值
        data = request.json
        mobile = data.get('mobile')
        smscode = data.get('smscode')
        password = data.get('password')

        # 验证数据是否为空
        if not all([mobile, smscode, password]):
            return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

        # 验证手机号是否正确
        # if not re.match('1[35678]\\d{9}', mobile):
        #     return jsonify(errno=RET.PARAMERR, errmsg='手机号格式不正确')

        # 2. 从redis中获取指定手机号对应的短信验证码
        try:
            real_sms_code = redis_store.get('SMS_' + mobile)
        except Exception as e:
            current_app.logger.error(e)
            print('111')
            return jsonify(errno=RET.DBERR, errmsg='数据查询失败')

        if not real_sms_code:
            print('222')
            return jsonify(errno=RET.NODATA, errmsg='验证码已过期')

        # 3. 校验用户输入的验证码
        if real_sms_code != smscode:
            print('333')
            return jsonify(errno=RET.DATAERR, errmsg='验证码输入错误')


        # 4. 如果正确，初始化 user 模型，并设置数据并添加到数据库
        user = User()
        user.mobile = mobile
        # 暂时没有昵称，用手机号代替
        user.nick_name = mobile
        # 记录用户最有一次登录时间
        user.last_login = datetime.now()
        # 对密码做处理
        # 需求：在设置 password 的时候， 去对password加密， 并且将加密结果给user.password_bash 赋值
        user.password = password
        # 添加到数据库
        try:
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            # 添加日志
            current_app.logger.error(e)
            db.session.rollback()
            print('444')
            return jsonify(errno=RET.DBERR, errmsg='数据保存失败')

        # 5. 在session中保存用户登录状态
        session['user_id'] = user.id
        session['mobile'] = user.mobile
        session['nick_name'] = user.nick_name
        print(mobile)
        print(smscode)
        print(password)
        # 6. 返回注册结果
        return jsonify(errno=RET.OK, errmsg='注册成功')


@passport_blu.route('/login', methods=['POST'])
def login():
    """
    登陆功能
    :return:
    """

    # 1. 获取参数和判断是否有值
    data = request.json
    mobile = data.get('mobile')
    password = data.get('password')
    # 检验参数
    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 检验手机号是否正确
    if not re.match('1[35678]\\d{9}', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机号格式不正确")

    # 2. 从数据库查询出指定的用户
    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")
    # 判断用户是否存在
    if not user:
        return jsonify(errno=RET.NODATA, errmsg="用户不存在")

    # 3. 校验密码
    if not user.check_passowrd(password):
        return jsonify(errno=RET.PWDERR, errmsg="用户名或者密码错误")

    # 4. 保存用户登录状态
    session['user_id'] = user.id
    session['mobile'] = user.mobile
    session['nick_name'] = user.nick_name
    # 5. 登录成功返回

    # 设置当前用户最后一次登录的时间
    user.last_login = datetime.now()

    # 如果在视图函数中，对模型身上的属性有修改，那么需要commit到数据库保存
    # 但是其实可以不用自己去写 db.session.commit(),前提是对SQLAlchemy有过相关配置

    # try:
    #     db.session.commit()
    # except Exception as e:
    #     db.session.rollback()
    #     current_app.logger.error(e)

    # 5. 响应
    return jsonify(errno=RET.OK, errmsg="登录成功")
