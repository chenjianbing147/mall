from itsdangerous import TimedJSONWebSignatureSerializer, BadData
from django.conf import settings

def generate_access_token(openid):

    dict = {
        'openid':openid
    }
    obj = TimedJSONWebSignatureSerializer(settings.SECRET_KEY ,600)

    token_bytes = obj.dumps(dict)
    token_str = token_bytes.decode()

    return token_str


def check_access_token(access_token):
    obj = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, 600)

    # 因为这里前端有可能穿的参数是错误，为了防止出现bug，我们要用try
    try:
        data = obj.loads(access_token)

    except BadData:
        return None

    else:
        return data.get('openid')



