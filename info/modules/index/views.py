from . import index_blu


# 测试

@index_blu.route('/')
def index():
    return '<h1>index-text</h1>'