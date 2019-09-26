from flask import render_template, g, abort, current_app, request, jsonify

from info import constants, db
from info.models import News, Comment
from info.modules.news import news_blu
from info.utils.common import user_login_data
from info.utils.response_code import RET


@news_blu.route('/<int:news_id>')
@user_login_data
def news_detail(news_id):
    '''新闻详情'''
    print(news_id)
    # 查询新闻数据
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        abort(404)
    # 校验报404错误
    if not news:
        abort(404)

    # 获取点击排行数据
    news_list = None
    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)
    click_news_list = []
    for click_news in news_list:
        click_news_list.append(click_news.to_basic_dict())

    # 进入详情页后要更新新闻的点击次数
    news.clicks += 1
    # 返回数据
    user = g.user
    # 设置默认未收藏新闻
    is_collection = False
    if user:
        if news in user.collection_news:
            is_collection = True
    # 获取当前新闻最新的评论，按时间排序
    comments = []
    try:
        comments  = Comment.query.filter(Comment.news_id == news_id).order_by(Comment.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库查询错误')
    comment_list = []
    for item in comments:
        comment_dict = item.to_dict()
        comment_list.append(comment_dict)


    data = {
        'user': user.to_dict() if user else None,
        'news': news,
        'news_dict_li': click_news_list,
        'is_collection': is_collection,
        'comments': comment_list
    }
    return render_template('news/detail.html', data=data)


@news_blu.route('/news_collect', methods=['POST'])
@user_login_data
def news_collect():
    '''新闻收藏'''
    user = g.user
    # 获取参数
    news_id = request.json.get('news_id', None)
    action = request.json.get('action', None)
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')
    # 判断参数
    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # action在不在指定的两个值：'collect', 'cancel_collect'内
    if action not in ['collect', 'cancel_collect']:
        return jsonify(errno=RET.DATAERR, errmsg='数据错误')

    # 查询新闻,并判断新闻是否存在
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库查询错误')

    if not news:
        return jsonify(errno=RET.NODATA, errmsg='该新闻不存在')

    # 收藏/取消收藏
    if action == "cancel_collect":
        # 取消收藏
        user.collection_news.remove(news)
    else:
        user.collection_news.append(news)

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存失败")
    # 返回
    return jsonify(errno=RET.OK, errmsg="操作成功")


@news_blu.route('/news_comment', methods=['POST'])
@user_login_data
def add_news_comment():
    """添加评论"""

    # 用户是否登陆
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')

    # 获取参数
    news_id = request.json.get('news_id')
    comment_str = request.json.get('comment')
    parent_id = request.json.get("parent_id")

    # 判断参数是否正确
    if not all([news_id, comment_str]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 查询新闻是否存在并校验
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库查询错误')
    if not news:
        return jsonify(errno=RET.NODATA, errmsg='该新闻不存在')

    # 初始化评论模型，保存数据
    comment = Comment()
    comment.user_id = user.id
    comment.news_id = news_id
    comment.content = comment_str
    if parent_id:
        comment.parent_id = parent_id
    # 配置文件设置了自动提交,自动提交要在return返回结果以后才执行commit命令,如果有回复
    # 评论,先拿到回复评论id,在手动commit,否则无法获取回复评论内容
    try:
        db.session.add(comment)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存评论数据失败")
    # 返回响应
    return jsonify(errno=RET.OK, errmsg='评论成功', data=comment.to_dict())


@news_blu.route('/comment_like', methods=['POST'])
@user_login_data
def comment_like():
    """
        评论点赞
        :return:
        """
    # 用户是否登陆
    # 取到请求参数
    # 判断参数
    # 获取到要被点赞的评论模型
    # action的状态,如果点赞,则查询后将用户id和评论id添加到数据库
            # 点赞评论
            # 更新点赞次数

        # 取消点赞评论,查询数据库,如果以点在,则删除点赞信息

            # 更新点赞次数

    # 返回结果

