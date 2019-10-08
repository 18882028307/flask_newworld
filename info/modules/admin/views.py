# import datetime
import time
from datetime import datetime, timedelta

from flask import render_template, request, current_app, session, g, redirect, url_for, jsonify, abort

from info import user_login_data, constants, db
from info.models import User, News, Category
from info.modules.admin import admin_blu
from info.utils.image_storage import storage
from info.utils.response_code import RET



@admin_blu.route('/login', methods=['GET', 'POST'])
def admin_login():
    '''管理员登录'''
    if request.method == 'GET':
        # 获取session
        user_id = session.get('user_id', None)
        is_admin = session.get('is_admin', False)
        # 如果用户id存在，并且是管理员，那么直接跳转管理后台主页
        if user_id and is_admin:
            return redirect(url_for('admin.admin_index'))
        return render_template('admin/login.html')
    # 获取参数
    username = request.form.get('username')
    password = request.form.get('password')
    # 验证参数
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
        return render_template('admin/login.html', errmsg="密码错误")

    if not user.is_admin:
        return render_template('admin/login.html', errmsg='用户权限错误')

    session['user_id'] = user.id
    session['nick_name'] = user.nick_name
    session['mobile'] = user.mobile
    session['is_admin'] = True

    return redirect(url_for('admin.admin_index'))


@admin_blu.route('/index')
@user_login_data
def admin_index():
    '''后台页面'''
    user = g.user
    if not user:
        # return redirect('/admin/login')
        return redirect(url_for('admin.admin_login'))
    return render_template('admin/index.html', user=user.to_dict())


@admin_blu.route('/logout', methods=['POST'])
@user_login_data
def admin_logout():
    '''退出登录'''
    session.pop('user_id', None)
    session.pop('nick_name', None)
    session.pop('mobile', None)
    session.pop('is_admin', None)
    # 返回结果
    return jsonify(errno=RET.OK, errmsg="OK")


@admin_blu.route('/user_count')
def user_count():
    '''用户统计'''
    # 总人数
    total_count = 0
    try:
        total_count = User.query.filter(User.is_admin == 0).count()
    except Exception as e:
        current_app.logger.error(e)

    # 月新增数
    mon_count = 0
    t = time.localtime()

    begin_mon_date_str = '%d-%02d-01' % (t.tm_year, t.tm_mon)

    # 将字符串转成datetime对象
    begin_mon_date = datetime.strptime(begin_mon_date_str, "%Y-%m-%d")

    try:
        mon_count = User.query.filter(User.is_admin == 0, User.create_time > begin_mon_date).count()
    except Exception as e:
        current_app.logger.error(e)

    # 日新增数
    day_count = 0
    begin_day_date = datetime.strptime(('%d-%02d-%02d' % (t.tm_year, t.tm_mon, t.tm_mday)), "%Y-%m-%d")

    try:
        day_count = User.query.filter(User.is_admin == False, User.create_time > begin_day_date).count()
    except Exception as e:
        current_app.logger.error(e)

    # 拆线图数据

    active_time = []
    active_count = []

    # 取到今天的时间字符串
    today_date_str = ('%d-%02d-%02d' % (t.tm_year, t.tm_mon, t.tm_mday))

    # 转成时间对象
    today_date = datetime.strptime(today_date_str, "%Y-%m-%d")

    for i in range(0, 31):
        # 取到某一天的0点0分
        begin_date = today_date - timedelta(days=i)

        # 取到下一天的0点0分
        end_date = today_date - timedelta(days=(i - 1))

        count = User.query.filter(User.is_admin == 0, User.last_login >= begin_date,
                                  User.last_login < end_date).count()
        active_count.append(count)
        active_time.append(begin_date.strftime('%Y-%m-%d'))

    # User.query.filter(User.is_admin == False, User.last_login >= 今天0点0分, User.last_login < 今天24点).count()

    # 反转，让最近的一天显示在最后
    active_time.reverse()
    active_count.reverse()

    data = {
        "total_count": total_count,
        "mon_count": mon_count,
        "day_count": day_count,
        "active_date": active_time,
        "active_count": active_count
    }
    return render_template('admin/user_count.html', data=data)


@admin_blu.route('/user_list')
def user_list():
    '''获取用户列表'''

    # 获取参数
    p = request.args.get('p', 1)
    # 校验参数
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        p = 1

    users = []
    current_page = 1
    total_page = 1
    # 查询数据
    try:
        paginate = User.query.filter(User.is_admin == 0).order_by(User.last_login.desc()).paginate(p, constants.ADMIN_USER_PAGE_MAX_COUNT, False)
        # 获取当前页数据
        users = paginate.items
        # 获取当前页页数
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    users_list = []
    for user in users:
        users_list.append(user.to_admin_dict())
    data = {
        'total_page': total_page,
        'current_page': current_page,
        'users': users_list
    }
    return render_template('admin/user_list.html', data=data)


@admin_blu.route('/news_review')
def news_review():
    p = request.args.get('p', 1)
    keywords = request.args.get('keywords', None)

    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        p = 1

    news = []
    current_page = 1
    total_page = 1

    try:
        filters = [News.status != 0]
        # 如果右关键字
        if keywords:
            filters.append(News.title.contains(keywords))
        paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(p, constants.ADMIN_NEWS_PAGE_MAX_COUNT, False)
        news = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    news_list = []
    for new in news:
        news_list.append(new.to_review_dict())

    data = {
        'total_page': total_page,
        'current_page': current_page,
        'news_list': news_list
    }
    return render_template('admin/news_review.html', data=data)


@admin_blu.route('/news_review_detail', methods=['GET', 'POST'])
def news_review_detail():
    '''新闻审核'''
    if request.method == 'GET':
        news_id = request.args.get('news_id')
        if not news_id:
            return render_template('admin/news_review_detail.html', data={'errmsg': '未查询到此新闻'})
        # 通过id查询
        news = None
        try:
            news = News.query.get(news_id)
        except Exception as e:
            current_app.logger.error(e)

        if not news:
            return render_template('admin/news_review_detail.html', data={'errmsg': '未查询到此新闻'})

        data = {'news': news.to_dict()}

        return render_template('admin/news_review_detail.html', data=data)
    # 获取参数
    news_id = request.json.get('news_id')
    action = request.json.get('action')
    print(news_id)
    print(action)
    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    if action not in ('accept', 'reject'):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')


    news = None
    try:
        # 查询新闻
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)

    if not news:
        return jsonify(errno=RET.NODATA, errmsg='未查询到数据')

    # 根据不同的状态设置不同的值
    if action == 'accept':
        news.status = 0
    else:
        # 拒绝通过
        reason = request.json.get('reason')
        if not reason:
            return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
        news.reason = reason
        news.status = -1

    # 保存数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='数据保存失败')
    return jsonify(errno=RET.OK, errmsg='操作成功')


@admin_blu.route('/news_edit')
def news_edit():
    '''返回新闻列表'''

    p = request.args.get('p', 1)
    keywords = request.args.get('keywords', None)

    # 判断参数
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        p = 1

    news_list = []
    current_page = 1
    total_page = 1

    try:
        # 如果有关键词
        filter = []
        if keywords:
            filter.append(News.title.contains(keywords))
        paginate = News.query.filter(*filter) \
            .order_by(News.create_time.desc())\
            .paginate(p, constants.ADMIN_NEWS_PAGE_MAX_COUNT, False)

        new_items = paginate.items
        current_page = paginate.page
        total_page = paginate.pages

    except Exception as e:
        current_app.logger.error(e)

    for new in new_items:
        news_list.append(new.to_basic_dict())

    data = {
        'total_page': total_page,
        'current_page': current_page,
        'news_list': news_list
    }
    return render_template('admin/news_edit.html', data=data)


@admin_blu.route('/news_edit_detail', methods=['GET', 'POST'])
def news_edit_detail():
    if request.method == 'GET':
        # 获取新闻id
        news_id = request.args.get('news_id')
        print(news_id)
        if not news_id:
            abort(404)

        try:
            news_id = int(news_id)
        except Exception as e:
            current_app.logger.error(e)
            return render_template('admin/news_edit_detail.html', errmsg='参数错误')

        try:
            news = News.query.get(news_id)
        except Exception as e:
            current_app.logger.error(e)
            return render_template('admin/news_edit_detail.html', errmsg='查询数据错误')

        if not news:
            return render_template('admin/news_edit_detail.html', errmsg="未查询到数据")

        # 查询分类
        try:
            categories = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)
            return render_template('admin/news_edit_detail.html', errmsg="查询数据错误")

        category_dict_list = []
        for category in categories:
            cate_dict = category.to_dict()
            # 判断当前遍历到的分类是否是当前新闻的分类，如果是，则添加is_selected为true
            if category.id == news.category_id:
                cate_dict['is_selected'] = True
            category_dict_list.append(cate_dict)

        # 移除最新的分类
        category_dict_list.pop(0)
        data = {
            'news': news.to_dict(),
            'categories': category_dict_list
        }
        return render_template('admin/news_edit_detail.html', data=data)

    # 获取post数据
    news_id = request.form.get('news_id')
    title = request.form.get('title')
    digest = request.form.get('digest')
    content = request.form.get('content')
    index_image = request.files.get('index_image')
    category_id = request.form.get('category_id')

    # 判断数据
    if not all([news_id, title, digest, content, category_id]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 查询指定id
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据查询失败')

    if not news:
        return jsonify(errno=RET.NODATA, errmsg="未查询到新闻数据")

    if index_image:
        try:
            index_image = index_image.read()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg='参数有误')

        # 将图片上传到七牛云
        try:
            key = storage(index_image)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.THIRDERR, errmsg="上传图片错误")
        news.index_image_url = constants.QINIU_DOMIN_PREFIX + key

    # 设置相关数据
    news.title = title
    news.digest = digest
    news.content = content
    news.category_id = category_id
    return jsonify(errno=RET.OK, errmsg='ok')


@admin_blu.route('/news_type', methods=['GET', 'POST'])
def news_type():
    if request.method == 'GET':
        # 查询分类
        try:
            categories = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)
            return render_template('admin/news_type.html', errmsg="查询数据错误")

        category_dict_list = []
        for category in categories:
            cate_dict = category.to_dict()
            category_dict_list.append(cate_dict)

        # 移除最新分类
        category_dict_list.pop(0)
        data = {
            'categories': category_dict_list
        }

        return render_template('admin/news_type.html', data=data)

    cname = request.json.get('name')
    # 如果传了cid，代表是编辑
    cid = request.json.get('id')

    if not cname:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if cid:
        try:
            cid = int(cid)
            category = Category.query.get(cid)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

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
        return jsonify(errno=RET.DBERR, errmsg="保存数据失败")

    return jsonify(errno=RET.OK, errmsg='ok')