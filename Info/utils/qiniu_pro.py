from qiniu import Auth, put_file, etag
import qiniu.config

# 需要填写你的 Access Key 和 Secret Key
access_key = "TP7UNt345niQ037Y8-y6CMCGk1teWZFt1312C4b2"
secret_key = "XZZmq7AzlMdrLc1BqCGS5sru6_bz0btHlllulxS1"


def qinniu_storage(img_data):
    # 构建鉴权对象
    q = Auth(access_key, secret_key)
    # 要上传的空间
    bucket_name = "ihome111"
    # 生成上传 Token，可以指定过期时间等
    token = q.upload_token(bucket_name)
    # 要上传文件的本地路径
    ret, info = qiniu.put_data(token, None, img_data)
    # print("ret['key']", ret['key'])
    return ret['key']


if __name__ == '__main__':
    with open(r'C:\Users\Administrator\Desktop\six\1.png', 'rb') as f:
        img_data = f.read()
    qinniu_storage(img_data)
