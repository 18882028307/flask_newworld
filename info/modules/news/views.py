from flask import render_template, g, abort, current_app

from info import constants
from info.models import News
from info.modules.news import news_blu
from info.utils.common import user_login_data


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
    data = {
        'user': user.to_dict() if user else None,
        'news': news,
        'news_dict_li': click_news_list
    }
    return render_template('news/detail.html', data=data)