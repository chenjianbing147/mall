# import json
# import re
#
#
#
# from django.contrib.auth import authenticate, login, logout
# from django_redis import get_redis_connection
# from django.views import View
# from django.http import JsonResponse
# from .models import User
#
# # Create your views here.
#
# class UsernameCountView(View):
#
#     def get(self, request, username):
#         try:
#             count = User.objects.filter(username=username).count()
#         except Exception as e:
#             return JsonResponse({
#                 'code':400,
#                 'errmsg':'查询数据失败'
#             })
#
#         else:
#             return JsonResponse({
#                 'code':200,
#                 'count':count
#             })
#
#
# class MobileCountView(View):
#
#     def get(self, request, mobile):
#         try:
#             count = User.objects.filter(mobile=mobile).count()
#
#         except Exception as e:
#             return JsonResponse({
#                 'code':400,
#                 'errmsg':'查询数据失败'
#             })
#
#         else:
#             return JsonResponse({
#                 'code':200,
#                 'count':count
#             })
#
#
#
# class Register(View):
#
#     def post(self, request):
#         """注册的接口"""
#
#         # 接受参数
#         content = json.loads(request.body.decode())
#         username = content.get('username')
#         password = content.get('password')
#         password2 = content.get('password2')
#         mobile = content.get('mobile')
#         sms_code_client = content.get('sms_code')
#         allow = content.get('allow')
#
#         # 效验（整体）
#         if not all([username,password,password2,mobile,allow,sms_code_client]):
#             return JsonResponse({
#                 "code":400,
#                 "errmsg":"缺少必传参数"
#             })
#
#         # username检验
#         if not re.match(r'^[a-zA-Z0-9_-]{5,20}$',username):
#             return JsonResponse({
#                 "code":400,
#                 "errmsg":"username有误"
#             })
#
#         # password检验
#         if not re.match(r'^[a-zA-Z0-9]{8,20}$',password):
#             return JsonResponse({
#                 "code": 400,
#                 "errmsg": "password有误"
#             })
#
#         # 判断两次密码是否一样
#         if password != password2:
#             return JsonResponse({
#                 "code": 400,
#                 "errmsg": "两次输入密码不一致"
#             })
#
#         # mobile检验
#         if not re.match(r'^1[3-9]\d{9}$', mobile):
#             return JsonResponse({
#                 "code":400,
#                 "errmsg":"手机号有误"
#             })
#
#         # 是否同意协议
#         if not allow:
#             return JsonResponse({
#                 "code": 400,
#                 "errmsg": "不同意协议"
#             })
#
#
#
#         # sms_code检验
#         redis_conn = get_redis_connection('verify_code')
#         sms_code_server = redis_conn.get('sms_%s' % mobile)
#
#         # 判断该值是否存在
#         if not sms_code_server:
#             return JsonResponse({
#                 "code": 400,
#                 "errmsg": "验证码过期"
#             })
#
#         if sms_code_client != sms_code_server.decode():
#             return JsonResponse({
#                 "code":400,
#                 "errmsg":"验证码错误"
#             })
#
#         try:
#             user = User.objects.create_user(username=username,
#                                             password=password,
#                                             mobile=mobile)
#
#         except Exception as e:
#             return JsonResponse({
#                 "code": 400,
#                 "errmsg": "保存到数据库出错"
#             })
#         # login里面的这个user是一个对象，不是django基础的key：value，淦
#         login(request, user)
#         response = JsonResponse({
#             "code":0,
#         })
#
#         response.set_cookie('username',user.username,max_age=3600*24*14)
#
#         return response
#
#
#
#
#
# class LoginView(View):
#     """实现登录接口"""
#     def post(self, request):
#         content = json.loads(request.body.decode())
#         username = content.get('username')
#         password = content.get('password')
#         remebered = content.get('remebered')
#
#         if not all([username, password]):
#             return JsonResponse({
#                 "code":400,
#                 "errmsg":"缺少必选参数"
#             })
#
#         user = authenticate(username=username,
#                             password=password)
#
#         if user is None:
#             return JsonResponse({
#                 "code": 400,
#                 "errmsg": "用户名或密码错误"
#             })
#
#         login(request, user)
#         if remebered != True:
#             request.session.set_expiry(0)
#
#         else:
#             request.session.set_expiry(None)
#
#         response = JsonResponse({
#             "code":0,
#         })
#
#         response.set_cookie('username', user.username, max_age=3600*24*14)
#
#         return response
#
#
#
# class LogoutView(View):
#     """定义退出登录的接口"""
#
#     def delete(self, request):
#         logout(request)
#
#         response = JsonResponse({
#             "code":0,
#         })
#
#         response.delete_cookie('username')
#
#         return response

import json
import re

from django.http import JsonResponse
from django.views import View

from carts.utils import merge_cart_cookie_to_redis
from meiduo_mall.utils.Views import LoginRequiredMixin
from users.models import User, Address
from django_redis import get_redis_connection
import logging
logger = logging.getLogger('django')
from django.contrib.auth import login, authenticate, logout
from celery_tasks.email.tasks import send_verify_email
from itsdangerous import TimedJSONWebSignatureSerializer
from django.conf import settings
from goods.models import SKU



class UsernameCountView(View):

    def get(self, request, username):
        try:
            count = User.objects.filter(username=username).count()
        except Exception as e:
            return JsonResponse({
                "code": 400,
                "errmsg": "数据库出错"
            })

        else:
            return JsonResponse({
                "code": 0,
                "errmsg": "ok",
                "count": count
            })



class MobileCountView(View):

    def get(self, request, mobile):
        try:
            count = User.objects.filter(mobile=mobile).count()
        except Exception as e:
            return JsonResponse({
                "code": 400,
                "errmsg": "数据库出错"
            })

        else:
            return JsonResponse({
                "code": 0,
                "errmsg": "ok",
                "count": count
            })



class RegisterView(View):

    def post(self, request):
        content = json.loads(request.body.decode())
        username = content.get('username')
        password = content.get('password')
        password2 = content.get('password2')
        mobile = content.get('mobile')
        sms_code_client = content.get('sms_code')
        allow = content.get('allow')

        if not all([username,password,password2,mobile,sms_code_client,allow]):
            return JsonResponse({"code":400,
                                 "errmsg":"缺少必传参数"})

        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$',username):
            return JsonResponse({"code": 0,
                                 "errmsg": "用户名不符合规范"})

        if not re.match(r'^[a-zA-Z0-9]{8,20}$', password):
            return JsonResponse({"code": 400,
                                 "errmsg": "密码不符合规范"})

        if password != password2:
            return JsonResponse({"code": 400,
                                 "errmsg": "两次密码不相等"})

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({"code": 400,
                                  "errmsg": "手机号不符合规范"})

        # 这段代码挺多余的
        if allow != True:
            return JsonResponse({"code": 400,
                                 "errmsg": "没有同意用户协议"})


        redis_conn = get_redis_connection('verify_code')
        sms_code_server = redis_conn.get('sms_%s' % mobile)
        if not sms_code_server:
            return JsonResponse({'code': 400,
                                      'errmsg': '短信验证码过期'})
            # 11.把redis中取得值和前端发的值对比
        if sms_code_client != sms_code_server.decode():
            return JsonResponse({'code': 400,
                                      'errmsg': '验证码有误'})

        try:
            user = User.objects.create_user(username=username,
                                     password=password,
                                     mobile=mobile)


        except Exception as e:
            return JsonResponse({"code":400,
                                 "errmsg":"保存到数据库出错误"})

        else:
            login(request, user)
            response = JsonResponse({"code": 0,
                                     "msg": "注册成功", })
            response = merge_cart_cookie_to_redis(request, response)
            response.set_cookie('username', user.username, max_age=3600 * 24 * 14)

            return response



class LoginView(View):

    def post(self, request):
        content = json.loads(request.body.decode())
        username =content.get('username')
        password =content.get('password')
        remembered =content.get('remembered')

        if not all([username, password]):
            return JsonResponse({"code": 400,
                                 "errmsg": "缺少必选参数"})

        user = authenticate(username=username,
                            password=password)

        if user is None:
            return JsonResponse({"code":400,
                                 "errmsg":'用户名或者密码错误'})

        login(request, user)

        if remembered != True:
            request.session.set_expiry(0)
            response = JsonResponse({"code":0})
            response.set_cookie('username', user.username)
            return response
        else:
            request.session.set_expiry(None)
            response = JsonResponse({"code": 0})
            response.set_cookie('username', user.username, max_age=3600*24*14)
            return response



class LogoutView(View):

    def delete(self, request):

        logout(request)

        response = JsonResponse({"code":0,
                                 "errmsg":"ok"})

        response.delete_cookie('username')

        return response






class UserCenter(LoginRequiredMixin,View):

    def get(self, request):

        info_data = {"username":request.user.username,
                     "mobile": request.user.mobile,
                     "email":request.user.email,
                     "email_active":request.user.email_active}

        return JsonResponse({"code":0,
                             "msg":'ok',
                             "info_data":info_data})



class AddEmail(LoginRequiredMixin, View):

    def put(self, request):

        content = json.loads(request.body.decode())
        email = content.get('email')

        if email is None:
            return JsonResponse({"code":400,
                                 "errmsg":"缺少必传参数"})

        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return JsonResponse({'code': 400,
                                 'errmsg': '参数email有误'})

        try:
            request.user.email = email
            request.user.save()

        except Exception as e:
            return JsonResponse({"code":400,
                                 "errmsg":"数据库出错"})

        else:
            dict = {"user_id":request.user.id,
                     "email": request.user.email}
            obj = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, 60*60*24)
            token = obj.dumps(dict).decode()
            print(settings.EMAIL_VERIFY_URL)
            verify_url = settings.EMAIL_VERIFY_URL + token
            send_verify_email.delay(email, verify_url)

            return JsonResponse({"code":0})



class VerifyEmail(View):

    def put(self,request):

        token = request.GET.get('token')

        if not token:
            return JsonResponse({'code': 400,
                                 'errmsg': '缺少token'})

        user = User.check_verify_email_token(token)
        if not user:
            return JsonResponse({'code': 400,
                                 'errmsg': '无效的token'})

        try:
            user.email_active =True
            user.save()

        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400,
                                 'errmsg': '激活邮件失败'})

        return JsonResponse({'code': 0,
                             'errmsg': 'ok'})



















class CreateAddressView(View):

    def post(self,request):
        try:
            count = Address.objects.filter(user=request.user, is_deleted=False).count()
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'errmsg': '获取地址数据出错'})
        if count == 20:
            return JsonResponse({"code":400,
                                 "errmsg":"超过地址数量上限"})

        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        if not all([receiver, province_id, city_id,district_id,place,mobile]):
            return JsonResponse({"code":400,
                                 "errmsg":"缺少必传参数"})

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400,
                                 'errmsg': '参数mobile有误'})

        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return JsonResponse({'code': 400,
                                     'errmsg': '参数tel有误'})
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return JsonResponse({'code': 400,
                                     'errmsg': '参数email有误'})

        try:
            address = Address.objects.create(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )

            if not request.user.default_address:
                request.user.default_address=address
                request.user.save()

        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400,
                                 'errmsg': '新增地址失败'})

        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        # 响应保存结果
        return JsonResponse({'code': 0,
                             'errmsg': '新增地址成功',
                             'address': address_dict})



class AddressView(LoginRequiredMixin,View):

    def get(self, request):
       addresses = Address.objects.filter(user=request.user, is_deleted=False)

       # 创建空的列表
       address_dict_list = []
       # 遍历
       for address in addresses:
           address_dict = {
               "id": address.id,
               "title": address.title,
               "receiver": address.receiver,
               "province": address.province.name,
               "city": address.city.name,
               "district": address.district.name,
               "place": address.place,
               "mobile": address.mobile,
               "tel": address.tel,
               "email": address.email
           }

           # 将默认地址移动到最前面
           default_address = request.user.default_address
           if default_address.id == address.id:
               # 查询集 addresses 没有 insert 方法
               address_dict_list.insert(0, address_dict)
           else:
               address_dict_list.append(address_dict)

       default_id = request.user.default_address_id

       return JsonResponse({'code': 0,
                            'errmsg': 'ok',
                            'addresses': address_dict_list,
                            'default_address_id': default_id})


class UpdateDestroyAddressView(View):

    def put(self, request, address_id):
        """修改地址"""

        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return JsonResponse({'code': 400,
                                 'errmsg': '缺少必传参数'})

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400,
                                 'errmsg': '参数mobile有误'})

        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return JsonResponse({'code': 400,
                                     'errmsg': '参数tel有误'})
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return JsonResponse({'code': 400,
                                     'errmsg': '参数email有误'})

        try:
            Address.objects.filter(id=address_id).update(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400,
                                 'errmsg': '更新地址失败'})
        address = Address.objects.get(id=address_id)
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        return JsonResponse({'code': 0,
                             'errmsg': '更新地址成功',
                             'address': address_dict})


    def delete(self, request, address_id):
        try:
          address = Address.objects.get(id=address_id)
          address.is_deleted = True
          address.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({"code":400,
                                 "errmsg":"删除地址失败"})

        return JsonResponse({"code":0,
                             "msg":"删除地址成功"})



class DefalutAddressView(View):

    def put(self, request, address_id):

        try:
            address = Address.objects.get(id=address_id)

            request.user.default_address = address
            request.user.save()

        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400,
                                 'errmsg': '设置默认地址失败'})

        return JsonResponse({"code":0,
                             "msg":"设置默认地址成功"})


class UpdateTitleAddressView(View):

    def put(self, request, address_id):

        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')

        try:
            address = Address.objects.get(id=address_id)
            address.title = title
            address.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({"code":400,
                                 "errmsg":"修改失败"})

        return JsonResponse({"code":0})


class ChangePasswordView(LoginRequiredMixin, View):

    def put(self, request):
        content = json.loads(request.body.decode())
        old_password = content.get('old_password')
        new_password = content.get('new_password')
        new_password2 = content.get('new_password2')

        if not all([old_password, new_password, new_password2]):
            return JsonResponse({"code":400,
                                 "errmsg":"缺少必传参数"})

        if not re.match(r'^[0-9A-Za-z]{8,20}$', new_password):
            return JsonResponse({'code': 400,
                                 'errmsg': '密码最少8位,最长20位'})

        if new_password != new_password2:
            return JsonResponse({'code': 400,
                                 'errmsg': '两次输入密码不一致'})

        if not request.user.check_password(old_password):
            return  JsonResponse({"code":400,
                                  "errmsg":"密码不正确"})

        try:
            request.user.set_password(new_password)
            request.user.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({"code": 400,
                                 "errmsg": "修改失败"})

        logout(request)
        response = JsonResponse({"code": 0,
                             "msg": "ok"})
        response.delete_cookie('username')

        return response



class UserBrowseHistory(LoginRequiredMixin,View):

    def post(self, request):

        content = json.loads(request.body)
        sku_id = content.get('sku_id')

        try:
            SKU.objects.get(id=sku_id)
        except Exception as e:
            return JsonResponse({"code":400})
        user = request.user
        redis_conn = get_redis_connection('history')
        pl = redis_conn.pipeline()
        # 先去重
        pl.lrem('history_%s' % user.id, 0, sku_id)
        # 再存储
        pl.lpush('history_%s' % user.id, sku_id)
        # 最后截取，界面有限，只保留5个
        pl.ltrim('history_%s' % user.id, 0, 4)
        pl.execute()

        return JsonResponse({"code":0})




    def get(self, request):
        redis_conn = get_redis_connection('history')
        sku_ids = redis_conn.lrange('history_%s' % request.user.id, 0, -1)
        skus_list = []
        try:
            for sku_id in sku_ids:
                sku = SKU.objects.get(id=sku_id)
                skus_list.append({'id': sku.id,
                                  'name': sku.name,
                                  'default_image_url': sku.default_image_url,
                                  'price': sku.price
                                  })

        except Exception as e:
            return JsonResponse({"code":400})

        return JsonResponse({"code": 0,
                             "msg": "ok",
                             "skus": skus_list})






