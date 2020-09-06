import json
import re

from django.http import JsonResponse
from QQLoginTool.QQtool import OAuthQQ
from django.conf import settings  # settings是django项目正在使用的配置文件，现在指的是dev.py
from django.views import View
from django_redis import get_redis_connection

from carts.utils import merge_cart_cookie_to_redis
from oauth.models import QAuthQQuser
import logging

from oauth.utils import generate_access_token, check_access_token
from meiduo_mall.libs.captcha.captcha import captcha
from users.models import User

logger = logging.getLogger('django')
from django.contrib.auth import login





# oauth开放授权
# auth自生的
# contrib普通发布版



class QQFirstView(View):
    """提供QQ登录页面网址"""

    def get(self, request):
        # next表示从哪个页面进入到的登录页面
        # 将来登录成功后，就自动回到那个页面
        next = request.GET.get('next')

        # 获取QQ登录页面网址
        # 创建OAuthQQ类的对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI,
                        state=next)

        # 调用 对象获取qq地址 的方法
        login_url = oauth.get_qq_url()

        # 返回登录地址
        return JsonResponse({
            "code":0,
            "login_url":login_url
        })

        # 上面的代码中, 需要用到一些变量.
        #
        # 这些变量, 我们添加到
        # dev.py
        # 中, 因为这样方便以后修改.
        #
        # 如果我们想修改这些变量的话, 我们可以直接找到
        # dev.py
        #
        # 而不用找对应的接口, 这样更节省性能.但是, 如果你想直接把参数
        #
        # 写到上面的接口中也是可行的.不推荐.





# 这里是 QQ 登录的第二次请求接口:
#
# 提示：
#
# 用户在 QQ 登录成功后，QQ 会将用户重定向到我们配置的回调网址.
#
# 在 QQ 重定向到回调网址时，会传给我们一个 Authorization Code 的参数.
#
# 我们需要拿到 Authorization Code 并完成 OAuth2.0 认证获取 openid
#
# 在本项目中，我们申请 QQ 登录开发资质时配置的回调网址为：
#
# http://www.meiduo.site:8000/oauth_callback
#
# QQ 互联重定向的完整网址为：
#
# http://www.meiduo.site:8000/oauth_callback/?code=AE263F12675FA79185B54870D79730A7&state=%2F





# class QQUserView(View):
#     """用户扫码的回调处理"""
#
#     def get(self, request):
#         """Oauth2.0认证"""
#         # 获取前段发送过过来的code参数
#         code = request.GET.get('code')
#
#         if not code:
#             # 判断code参数是否存在
#             return JsonResponse({
#                 "code":400,
#                 "errmsg":"缺少code参数"
#             })
#
#             # 调用我们安装的QQLoginTool工具类
#             # 创建工具对象
#         oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
#                         client_secret=settings.QQ_CLIENT_SECRET,
#                         redirect_uri=settings.QQ_REDIRECT_URI)
#
#         try:
#             # 携带code向QQ服务器请求access_token
#             access_token = oauth.get_access_token(code)
#
#             openid = oauth.get_open_id(access_token)
#
#         except Exception as e:
#             # 如果上面获取 openid 出错，则验证失败
#             logger.error()
#             return JsonResponse({'code': 400,
#                                  'errmsg': 'oauth2.0认证失败, 即获取qq信息失败'})
#             pass





class QQSecondView(View):

    def get(self, request):
        # 1. 接受code参数
        code = request.GET.get('code')
        # 2. 检验参数
        if not code:
            return JsonResponse({
                "code": 400,
                "errmsg": "缺少code参数"
            })
        # 3.创建QQLoginTool对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI)


        try:
            access_token = oauth.get_access_token(code)

            openid = oauth.get_open_id(access_token)

        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400,
                                 'errmsg': 'oauth2.0认证失败'})

        try:
            oauth_qq = QAuthQQuser.objects.get(openid=openid)

        except Exception as e:
            # 自定义一个函数，把openid加密为access_token
            access_token = generate_access_token(openid)

            return JsonResponse({"code":200,
                                 "access_token":access_token})

        else:
            user = oauth_qq.user

            login(request, user)

            response = JsonResponse({
                "code":"0"
            })

            response.set_cookie('username', user.username, max_age=3600*24*14)
            response = merge_cart_cookie_to_redis(request, response)

            return response


    def post(self, request):
        # 1.接受参数json
        content = json.loads(request.body.decode())
        mobile = content.get('mobile')
        password = content.get('password')
        sms_code_client = content.get('sms_code')
        access_token = content.get('access_token')

        if not all([mobile,password,sms_code_client,access_token]):
            return JsonResponse({"code":400,
                                 "errmsg":"缺少必传参数"})


        if not re.match(r'1[1-9]\d{9}$', mobile):
            return JsonResponse({'code': 400,
                                 'errmsg': '请输入正确的手机号码'})

        if not re.match(r'^[0-9a-zA-Z_-]{8,20}$', password):
            return JsonResponse({'code': 400,
                                 'errmsg': '请输入8-20位的密码'})

        redis_conn = get_redis_connection('verify_code')

        sms_code_server = redis_conn.get('sms_%s' % mobile).decode()

        if sms_code_client != sms_code_server:
            return JsonResponse({'code': 400,
                                 'errmsg': '手机验证码失败'})

        # 自己写一个解密函数
        openid = check_access_token(access_token)
        if not openid:
            return JsonResponse({
                "code":400,
                "errmsg":"access_token不正确，或者失效"
            })

        # 当增加时要先验证数据库是否存在

        qs = User.objects.filter(mobile=mobile)
        try:
            if not qs:
                user = User.objects.create_user(username=mobile,
                                                password=password,
                                                mobile=mobile)

            else:
                for user in qs:
                    user = user

        except Exception as e:
            return JsonResponse({
                "code": 400,
                "errmsg": "数据库出现错误"
            })

        else:
            if not user.check_password(password):
                return JsonResponse({
                    "code": 400,
                    "errmsg": "密码不正确"
                })

        try:
            user = User.objects.get(mobile=mobile)
            QAuthQQuser.objects.create(openid=openid,
                                       user=user)

        except Exception as e:
            return JsonResponse({
                "code": 400,
                "errmsg": "往数据库添加数据出错"
            })

        # 实现状态保持
        login(request, user)

        response = JsonResponse({'code':0,
                                 'msg':'ok'})

        response = merge_cart_cookie_to_redis(request, response)

        # 登录时用户名
        response.set_cookie('username', user.username, max_age=3600*24*14)

        return response
