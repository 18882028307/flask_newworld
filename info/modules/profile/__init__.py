from flask import Blueprint

# 创建蓝图
profile_blu = Blueprint('profile', __name__, url_prefix='/user')

from . import views