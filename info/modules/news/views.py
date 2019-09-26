from flask import render_template, g, abort, current_app, request, jsonify

from info import constants, db
from info.models import News
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

    data = {
        'user': user.to_dict() if user else None,
        'news': news,
        'news_dict_li': click_news_list,
        'is_collection': is_collection
    }
    return render_template('news/detail.html', data=data)


@news_blu.route('/news_collect', methods=['POST'])
@user_login_data
def news_collect():
    '''新闻收藏'''
    user = g.user
    # 获取参数
    news_id = request.json.get('news_id')
    action = request.json.get('action')
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
        return jsonify(errno=RET.NODATA, errmsg='无数据')

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