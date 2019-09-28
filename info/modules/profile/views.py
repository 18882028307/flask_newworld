from flask import render_template, g, request, jsonify, current_app, session, redirect, abort

from info import db, constants
from info.models import Category, News, User
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
    '''上传头像'''
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

    return jsonify(errno=RET.OK, errmsg='OK', data={'avatar_url': constants.QINIU_DOMIN_PREFIX + url})


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
        current_page = paginate.page
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
        'current_page': current_page,
        'collections': collection_dict_li
    }
    return render_template('news/user_collection.html', data=data)


@profile_blu.route('/news_release', methods=['GET', 'POST'])
@user_login_data
def news_release():
    # GET请求
    if request.method == 'GET':
        # 1. 获取新闻分类数据
        categories = []
        try:
            # 获取所有的分类数据
            categories = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)
        # 2. 移除最新分类
        # 定义列表保存分类数据
        categories_dicts = []

        for category in categories:
            # 获取字典
            cate_dict = category.to_dict()
            # 拼接内容
            categories_dicts.append(cate_dict)
        categories_dicts.pop(0)
        # 返回数据
        return render_template('news/user_news_release.html', data={'categories': categories_dicts})

    # 1. 获取要提交的数据
    title = request.form.get('title')
    source = '个人发布'
    digest = request.form.get('digest')
    content = request.form.get('content')
    index_image = request.files.get("index_image")
    category_id = request.form.get("category_id")

    print(title)
    print(source)
    print(digest)
    print(content)
    print(index_image)
    print(category_id)
    # 校验参数
    if not all([title, source, digest, content, index_image, category_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

    # 3.取到图片，将图片上传到七牛云
    try:
        index_image_data = index_image.read()
        # 上传到七牛云
        key = storage(index_image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

    # 保存数据
    news = News()
    news.title = title
    news.digest = digest
    news.source = source
    news.content = content
    news.index_image_url = constants.QINIU_DOMIN_PREFIX + key
    news.category_id = category_id
    news.user_id = g.user.id
    # 新闻状态,将新闻设置为1代表待审核状态
    news.status = 1

    # 手动设置新闻状态,在返回前commit提交
    try:
        db.session.add(news)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存数据失败")
    # 返回
    return jsonify(errno=RET.OK, errmsg='发布成功，等待审核')


@profile_blu.route('/news_list')
@user_login_data
def user_news_list():
    '''用户发布的新闻列表'''
    # 获取参数
    p = request.args.get('p')
    # 判断参数
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        p = 1
    # 获取当前用户
    user = g.user
    news_list = []  # 用户发布新闻列表
    current_page = 1    # 当前页数
    total_page = 1  # 总页数

    try:
        # 进行分页数据查询
        # paginate（page, per_page, error_out, max_per_page）
        paginate = user.news_list.order_by(News.create_time.desc()).paginate(p, constants.USER_COLLECTION_MAX_NEWS, False)
        # paginate = News.query.filter(News.user_id == user.id).paginate(p, constants.USER_COLLECTION_MAX_NEWS, False)

        # 获取当前页数据
        news_list = paginate.items
        # 获取当前页
        current_page = paginate.page
        # 获取总页数
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    news_dict_li = []
    for news_item in news_list:
        news_dict_li.append(news_item)

    data = {
        'news_list': news_dict_li,
        'total_page': total_page,
        'current_page': current_page
    }

    # 返回数据
    return render_template('news/user_news_list.html', data=data)


@profile_blu.route('/user_follow')
@user_login_data
def user_follow():
    # 获取页数
    p = request.args.get('p', 1)
    # 判断参数
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        p = 1

    # 获取当前用户
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="未登录")

    # 分页
    pagedatas = []
    current_page = 1
    total_page = 1
    try:
        paginate = user.followed.paginate(p, constants.USER_FOLLOWED_MAX_COUNT, False)
        # 当前页数据
        pagedatas = paginate.items
        # 当前页数
        current_page = paginate.page
        # 总页数
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    print(pagedatas)
    user_list = []
    for page in pagedatas:
        user_list.append(page.to_dict())
    data = {
        'users': user_list,
        'total_page': total_page,
        'current_page': current_page
    }
    return render_template('news/user_follow.html', data=data)

@profile_blu.route('/other_info')
@user_login_data
def other_info():
    """查看其他用户信息"""
    # 获取当前用户
    user = g.user
    # 获取其他用户id
    other_user_id = request.args.get('id')
    if not other_user_id:
        abort(404)
    # 查询用户模型
    other = None
    try:
        other = User.query.get(other_user_id)
    except Exception as e:
        current_app.logger.error(e)
    if not other:
        abort(404)
    # 判断当前用户是否关注过该用户
    is_followed = False

    if user:
        if other.followers.filter(User.id == user.id).count() > 0:
            is_followed = True
    try:
        user = user.to_dict()
    except Exception as e:
        current_app.logger.error(e)
        user = None

    data = {
        'user': user,
        'other_info': other.to_dict(),
        'is_followed': is_followed
    }

    return render_template('news/other1.html', data=data)


@profile_blu.route('/other_news_list')
def other_news_list():
    # 获取页数
    p = request.args.get('p', 1)
    user_id = request.args.get('user_id')

    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    if not all([p, user_id]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 查询对应id的用户
    user = None
    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")

    if not user:
        return jsonify(errno=RET.NODATA, errmsg="用户不存在")

    # 分页
    current_page = 1
    total_page = 1
    try:
        paginate = News.query.filter(News.user_id == user_id, News.status == 0).paginate(p, constants.OTHER_NEWS_PAGE_MAX_COUNT, False)
        # 当前页数据
        items = paginate.items
        # 当前页页数
        current_page = paginate.page
        # 总页数
        total_page = paginate.pages

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")

    news_dict_li = []
    for news_item in items:
        news_dict_li.append(news_item.to_review_dict())

    for i in news_dict_li:
        print(i['status'])
    data = {
        'news_list': news_dict_li,
        'total_page': total_page,
        'current_page': current_page
    }
    return jsonify(errno=RET.OK, errmsg='OK', data=data)