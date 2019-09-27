from flask import render_template, g, request, jsonify, current_app, session, redirect

from info import db, constants
from info.modules.profile import profile_blu
from info.utils.common import user_login_data
from info.utils.image_storage import storage
from info.utils.response_code import RET


@profile_blu.route('/info')
@user_login_data
def user_info():
    # 如果用户登陆则进入个人中心
    user = g.user
    # 如果没有登陆,跳转主页
    if not user:
        return redirect('/')
    # 返回用户数据
    data = {
        "user": user.to_dict(),
    }
    return render_template('news/user.html', data=data)


@profile_blu.route('/base_info', methods=['GET', 'POST'])
@user_login_data
def base_info():
    """
    用户基本信息
    1. 获取用户登录信息
    2. 获取到传入参数
    3. 更新并保存数据
    4. 返回结果
    :return:
    """
    # 获取当前用户信息
    user = g.user
    if request.method == 'GET':
        return render_template('news/user_base_info.html', data={"user_info": user.to_dict()})
    # 获取参数
    nick_name = request.json.get("nick_name")
    gender = request.json.get('gender')
    signature = request.json.get('signature')
    # 验证参数
    if not all([nick_name, gender, signature]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

    if gender not in ['MAN', 'WOMAN']:
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

    # 更新并保存
    user.nick_name = nick_name
    user.gender = gender
    user.signature = signature
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存数据失败")

    # 将session中保存的数据进行实时更新
    session['nick_name'] = nick_name

    # 返回
    return jsonify(errno=RET.OK, errmsg='更新成功')


@profile_blu.route('/pic_info', methods=['GET', 'POST'])
@user_login_data
def pic_info():
    user = g.user
    # 如果是GET请求,返回用户数据
    if request.method == 'GET':
        return render_template('news/user_pic_info.html', data={"user_info": user.to_dict()})
    # 如果是POST请求表示修改头像
    # 1. 获取到上传的图片
    try:
        avatar_file = request.files.get('avatar').read()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="读取文件出错")

    # 2. 上传头像
    # 使用自已封装的storage方法去进行图片上传
    try:
        url = storage(avatar_file)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="上传图片错误")

    # 3. 保存头像地址
    # 拼接url并返回数据
    user.avatar_url = url
    # 将数据保存到数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存用户数据错误")

    return jsonify(errno=RET.OK, errmsg='OK', data={'avatar_url':constants.QINIU_DOMIN_PREFIX + url})


@profile_blu.route('/pass_info', methods=['GET', 'POST'])
@user_login_data
def pass_info():
    # GET请求,返回
    if request.method == "GET":
        return render_template('news/user_pass_info.html')

    # 1. 获取参数
    old_password = request.json.get('old_password')
    new_password = request.json.get('new_password')
    # 2. 校验参数
    if not all([old_password, new_password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

    # 3. 判断旧密码是否正确
    user = g.user
    if not user.check_passowrd(old_password):
        return jsonify(errno=RET.PWDERR, errmsg="原密码错误")
    # 4. 设置新密码
    user.password = new_password
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存数据失败")
    # 清除session
    session.pop('user_id')
    session.pop('mobile')
    session.pop('nick_name')
    # 返回
    return jsonify(errno=RET.OK, errmsg='保存成功')


@profile_blu.route('/collection')
@user_login_data
def user_collection():
    # 1. 获取参数
    p = request.args.get('p', 1)
    # 2. 判断参数
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        p = 1
    user = g.user
    # 3. 查询用户指定页数的收藏的新闻
    collections = []
    current_page = 1
    total_page = 1
    try:
        # 进行分页数据查询
        # paginate（page, per_page, error_out, max_per_page）
        paginate = user.collection_news.paginate(p, constants.USER_COLLECTION_MAX_NEWS, False)
        # 获取分页数据
        collections = paginate.items
        # 获取当前页
        current_app = paginate.page
        # 获取总页数
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)
    # 收藏列表
    collection_dict_li = []
    for news in  collections:
        collection_dict_li.append(news.to_basic_dict())

    # 返回数据
    data = {
        'total_page': total_page,
        'current_page': current_app,
        'collections': collection_dict_li
    }
    return render_template('news/user_collection.html', data=data)