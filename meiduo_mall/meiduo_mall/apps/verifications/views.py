# from django.shortcuts import render
# from meiduo_mall.libs.captcha.captcha import captcha
# from django.views import View
# from django.http import HttpResponse, JsonResponse
# from django_redis import get_redis_connection
# import logging
# from celery_tasks.sms.tasks import ccp_send_sms_code
#
# from meiduo_mall.libs.yuntongxun.ccp_sms import CCP
#
# logger = logging.getLogger('django')
# import random
#
#
#
# # Create your views here.
# # from meiduo_mall.meiduo_mall.libs.captcha.captcha import captcha
#
#
# class ImageCodeView(View):
#     """返回图形验证码的类视图"""
#
#     def get(self, request, uuid):
#         # 调用工具类，captcha生成图形验证码
#         text, image = captcha.generate_captcha()
#
#         # 链接redis，获取链接对象
#         redis_conn = get_redis_connection('verify_code')
#
#         # 利用链接对象，保存数据到redis， 使用setex函数
#         redis_conn.setex('img_%s' % uuid,
#                                  300,
#                                  text)
#
#         # 返回图片
#         return HttpResponse(
#             image,
#             content_type='image/jpg',
#         )
#
#
#
# class SMSCodeView(View):
#     """短信验证码"""
#
#     def get(self, request, mobile):
#         redis_conn = get_redis_connection('verify_code')
#         flag = redis_conn.get('flag_mobile_%s' % mobile)
#         if flag:
#             return JsonResponse({
#                 "code":400,
#                 "errmsg":"请勿重复发送短信"
#             })
#
#         image_code_client = request.GET.get('image_code')
#         uuid = request.GET.get('image_code_id')
#
#         # 效验参数
#         if not all([image_code_client, uuid]):
#             return JsonResponse({
#                 "code":400,
#                 "errmsg":'少传了参数'
#             })
#
#
#         image_code_server = redis_conn.get('img_%s' % uuid)
#
#         if image_code_server is None:
#             # 图形验证码过期或者不存在
#             return JsonResponse({
#                 "code":400,
#                 "errmsg":'图形验证码失效'
#             })
#
#         # 删除图形验证码，避免恶意测试图形验证码
#         try:
#             redis_conn.delete(uuid)
#         except Exception as e:
#             logger.error(e)
#
#
#         # 对比图形验证码
#         # bytes转字符串
#         image_code_server = image_code_server.decode()
#         # 转小写之后比较
#         if image_code_client.lower() != image_code_server.lower():
#             return JsonResponse({
#                 "code":400,
#                 "msg":'验证码不正确'
#             })
#
#         # 生成短信验证码，生成6位数验证码
#         sms_code = '%06d' % random.randint(0,999999)
#         logger.info(sms_code)
#
#         # 保存短信验证码
#         pl = redis_conn.pipeline()
#
#         pl.setex(
#             'sms_%s' % mobile, 300, sms_code)
#
#         pl.setex('flag_mobile_%s' % mobile, 60, 1)
#
#         pl.execute()
#
#         # CCP().send_template_sms(mobile, [sms_code, 5], 1)
#
#         # ccp_send_sms_code.delay(mobile,sms_code)
#         return JsonResponse({
#             "code":200
#         })
#
import random

from meiduo_mall.libs.captcha.captcha import captcha
from meiduo_mall.libs.yuntongxun.ccp_sms import CCP
from django.views import View
from django_redis import get_redis_connection
from django.http import HttpResponse, JsonResponse
import logging
logger = logging.getLogger('django')
from celery_tasks.sms.tasks import ccp_send_sms_code





class ImageCodeView(View):

    def get(self, request, uuid):

        text, image = captcha.generate_captcha()

        redis_conn = get_redis_connection('verify_code')

        redis_conn.setex('img_%s' % uuid, 300, text)

        return HttpResponse(image, content_type='image/jpg')




class SMSCodeView(View):

    def get(self,request, mobile):
        redis_conn = get_redis_connection('verify_code')
        send_flag = redis_conn.get('send_flag_%s' % mobile)
        if send_flag:
            return JsonResponse({"code":400,
                                 "errmsg":"该手机号发送短信过于频繁"})

        uuid = request.GET.get('image_code_id')
        image_code_client = request.GET.get('image_code')
        image_code_server = redis_conn.get('img_%s' % uuid)
        if image_code_server is None:
            return JsonResponse({"code": 400,
                                 "errmsg": "验证码过期"})

        try:
            redis_conn.delete('img_%s' % uuid)
        except Exception as e:
            logger.error(e)

        image_code_server =image_code_server.decode()
        if image_code_client.lower() != image_code_server.lower():  # redis里面取出来的是bytes类型，要解码，因为redis是把数据存放在内存中的
            return JsonResponse({"code":400,
                                 "errmsg":"验证码有误"})


        sms_code = '%06d' % random.randint(0, 999999)
        logger.info(sms_code)
        CCP().send_template_sms(mobile, [sms_code, 5], 1) #, 这里要用异步方案celery替换
        # 注意，这里的函数调用需要加上delay
        # ccp_send_sms_code.delay(mobile,sms_code)
        # 创建Redis管道
        pl = redis_conn.pipeline()
        pl.setex('sms_%s' % mobile, 300, sms_code)
        pl.setex('send_flag_%s' % mobile, 60, 1)
        pl.execute()
        return JsonResponse({"code":0,
                             "errmsg":'ok',
                             })
