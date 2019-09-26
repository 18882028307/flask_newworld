from flask import render_template, g, request, jsonify, current_app, session, redirect

from info import db
from info.modules.profile import profile_blu
from info.utils.common import user_login_data
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
    return render_template('news/user_pic_info.html', data={"user_info": user.to_dict()})