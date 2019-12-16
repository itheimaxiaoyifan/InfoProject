from qiniu import Auth, put_file, etag
import qiniu.config
# 需要填写你的 Access Key 和 Secret Key
access_key = "TP7UNt345niQ037Y8-y6CMCGk1teWZFt1312C4b2"
secret_key = "XZZmq7AzlMdrLc1BqCGS5sru6_bz0btHlllulxS1"
q = Auth(access_key, secret_key)
# 要上传的空间
bucket_name = "ihome111"
# 构建鉴权对象

# 上传后保存的文件名
key = 'my-python-logo.png'
# 生成上传 Token，可以指定过期时间等
token = q.upload_token(bucket_name, key, 3600)
# 要上传文件的本地路径
localfile = r'C:\Users\Administrator\Desktop\six\1.png'
ret, info = put_file(token, key, localfile)
print(ret)
print(info)
print(ret['key'])
assert ret['key'] == key
assert ret['hash'] == etag(localfile)
