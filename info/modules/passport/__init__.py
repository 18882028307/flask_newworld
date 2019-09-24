from flask import Blueprint

# 创建蓝图
passport_blu = Blueprint('passport', __name__, url_prefix='/passport')
from . import views