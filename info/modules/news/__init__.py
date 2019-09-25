from flask import Blueprint


# 创建蓝图
news_blu = Blueprint('news', __name__, url_prefix='/news')
from . import views


