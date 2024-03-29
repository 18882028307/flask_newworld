from flask import render_template, session, current_app, g, request, jsonify

from info import constants
from info.models import User, News, Category
from info.utils.common import user_login_data
from info.utils.response_code import RET
from . import index_blu

# 测试

@index_blu.route('/')
@user_login_data
def index():
    '''
    显示首页
    1.如果用户已经登录，将当前登录用户的数据传到模板中，供模板显示
    :return:
    '''
    # # 显示用户是否登录的逻辑
    # # 获取用户id
    # user_id = session.get('user_id', None)
    # user = None
    # if user_id:
    #     # 尝试查询用户的模型
    #     try:
    #         user = User.query.get(user_id)
    #     except Exception as e:
    #         current_app.logger.error(e)


    user = g.user
    # 右侧的新闻排行的逻辑
    news_list = []
    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)

    # 定义一个空的字典列表，里面装的是字典
    news_dict_li = []
    # 遍历对象列表，将对象的字典添加到字典列表中
    for news in news_list:
        news_dict_li.append(news.to_basic_dict())

    # 查询分类数据，通过模板的形式渲染出来
    categories = Category.query.all()
    category_li = []
    for category in categories:
        category_li.append(category.to_dict())

    datas = {
        'user': user.to_dict() if user else None,
        'news_dict_li': news_dict_li,
        'category_li': category_li
    }
    return render_template('news/index.html', data=datas)


@index_blu.route('/news_list')
def news_list():
    """
    获取首页新闻数据
    :return:
    """
    # 1. 获取参数,并指定默认为最新分类,第一页,一页显示10条数据
    page = request.args.get('page', 1)  # 第几页，默认为1
    per_page = request.args.get('per_page', constants.HOME_PAGE_MAX_NEWS)  # 每页的条数，默认10
    category_id = request.args.get('cid', 1)    # 分类id，默认为1

    # 2. 校验参数
    try:
        page = int(page)
        per_page = int(per_page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    # 默认选择审核通过的数据
    filters = [News.status == 0]
    # 如果查询的不是最新数据
    if category_id != 1:
        filters.append(News.category_id == category_id)

    # 3. 查询数据
    try:
        paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page, per_page, False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据查询错误')

    items = paginate.items          # 获取当前页数据
    total_page = paginate.pages     # 总页数
    current_page = paginate.page    # 当前页数

    # 将模型对象列表转成字典列表
    news_dict_li = []
    for news in items:
        news_dict_li.append(news.to_basic_dict())

    # 返回数据
    data = {
        'total_page': total_page,
        'current_page': current_page,
        'news_dict_li': news_dict_li
    }

    return jsonify(errno=RET.OK, errmsg='OK', data=data)




# 在打开网页的时候，浏览器会默认去请求根路径+favicon.ico作网站标签的小图标
# send_static_file 是 flask 去查找指定的静态文件所调用的方法
@index_blu.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')
