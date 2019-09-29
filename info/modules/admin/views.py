# import datetime
import time
from datetime import datetime, timedelta

from flask import render_template, request, current_app, session, g, redirect, url_for, jsonify

from info import user_login_data, constants
from info.models import User
from info.modules.admin import admin_blu
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
    print('time.localtime():', t)
    begin_mon_date_str = '%d-%02d-01' % (t.tm_year, t.tm_mon)
    print('begin_mon_date_str:', begin_mon_date_str)
    # 将字符串转成datetime对象
    begin_mon_date = datetime.strptime(begin_mon_date_str, "%Y-%m-%d")
    print('begin_mon_date:', begin_mon_date)
    try:
        mon_count = User.query.filter(User.is_admin == 0, User.create_time > begin_mon_date).count()
    except Exception as e:
        current_app.logger.error(e)

    # 日新增数
    day_count = 0
    begin_day_date = datetime.strptime(('%d-%02d-%02d' % (t.tm_year, t.tm_mon, t.tm_mday)), "%Y-%m-%d")
    print('begin_day_date:', begin_day_date)
    try:
        day_count = User.query.filter(User.is_admin == False, User.create_time > begin_day_date).count()
    except Exception as e:
        current_app.logger.error(e)

    # 拆线图数据

    active_time = []
    active_count = []

    # 取到今天的时间字符串
    today_date_str = ('%d-%02d-%02d' % (t.tm_year, t.tm_mon, t.tm_mday))
    print('today_date_str:', today_date_str)
    # 转成时间对象
    today_date = datetime.strptime(today_date_str, "%Y-%m-%d")

    for i in range(0, 31):
        # 取到某一天的0点0分
        begin_date = today_date - timedelta(days=i)
        print('begin_date%s:%s' %(str(i), begin_date))
        # 取到下一天的0点0分
        end_date = today_date - timedelta(days=(i - 1))
        print('end_date%s:%s' % (str(i), end_date))
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