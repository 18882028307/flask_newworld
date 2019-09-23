from . import passport_blu
from flask import request, current_app, abort, make_response
from info import redis_store, constants
from info.utils.captcha import captcha



@passport_blu.route('/passport/image_code')
def get_image_code():
    '''
    生成图片验证码
    :return:
    '''
    # 1. 获取参数
    # 2. 校验参数
    # 3. 生成图片验证码
    # 4. 保存图片验证码
    # 5.返回图片验证码
