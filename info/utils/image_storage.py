import logging
from qiniu import Auth, put_data

# 填写Access key 和 Secret key

access_key = 'kFaVQuiTVy3dFmddYbq5fX2F0WTgu-Fo06dWBm3B'
secret_key = 'U3f53yDfXXFWAOJMSVRCnn1IM41GMj3O32WrCxSf'

# 要上传的空间
bucket_name = 'flasknewspropic'



def storage(data):
    '''七牛云存储上传文件接口'''

    if not data:
        return None
    try:
        # 构建鉴权对象
        q = Auth(access_key, secret_key)

        # 生成上传 token，可以指定过期时间
        token = q.upload_token(bucket_name)

        # 上传文件
        ret, info = put_data(token, None, data)

    except Exception as e:
        logging.error(e)
        raise e

    if info and info.status_code != 200:
        raise Exception('上传文件到七牛失败')

    # 返回七牛中保存的图片名，这个图片名也是访问七牛获取图片的路径
    return ret["key"]


if __name__ == '__main__':
    file_name = input("输入上传的文件")
    with open(file_name, 'rb') as f:
        storage(f.read())