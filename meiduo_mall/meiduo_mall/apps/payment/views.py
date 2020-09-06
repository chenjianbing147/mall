import os
from .models import Payment
from django.http import JsonResponse
from django.shortcuts import render
from alipay import AliPay
from django.views import View
from django.conf import settings
# Create your views here.
from orders.models import OrderInfo


class PaymentsView(View):

    def get(self, request, order_id):

        # 1. 验证Order_id
        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user=request.user,
                                          status=1)

        except Exception as e:
            return JsonResponse({"code":400,
                                 "errmsg":'order_id有误'})

        # 2. 调用Python-alipay-sdk工具类, 创建一个对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/app_private_key.pem"),
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),"keys/alipay_public_key.pem"),
            sign_type="RSA2",
            debug=settings.ALIPAY_DEBUG
        )

        # 3. 调用对象的方法 ====> 拼接好的字符串
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(order.total_amount),
            subject="美多商城%s" % order_id,
            return_url=settings.ALIPAY_RETURN_URL,
        )

        # 4. 把支付宝的网关(url) + 字符串 ====> 完整的url地址
        # 响应登录支付宝连接
        # 真实环境电脑网站支付网关：https://openapi.alipay.com/gateway.do? + order_string
        # 沙箱环境电脑网站支付网关：https://openapi.alipaydev.com/gateway.do? + order_string
        alipay_url = settings.ALIPAY_URL + "?" + order_string
        return JsonResponse({'code': 0,
                             'errmsg': 'OK',
                             'alipay_url': alipay_url})





class PaymentStatusView(View):

    def put(self, request):

        # 1.接受参数(查询字符串)
        query_dict = request.GET

        # 2.把查询字符串的dict获取到
        dict = query_dict.dict()

        # 3.从dict中剔除sign对应的部分, 获取剔除的结果signature
        signature = dict.pop('sign')

        # 4.获取python-alipy-adk工具类的对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/app_private_key.pem"),
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                "keys/alipay_public_key.pem"),
            sign_type="RSA2",
            debug=settings.ALIPAY_DEBUG
        )

        # 5.调用对象的verify(剔除后的dict, signature) =====> bool
        success = alipay.verify(dict, signature)

        # 6.根据获取的bool值,判断是否支付成功
        if not success:
            return JsonResponse({'code': 400,
                                 'errmsg': '非法请求'})

        # 7.dict ====> order_id&trade_id

        order_id = dict.get('out_trade_no')
        trade_id = dict.get('trade_no')

        # 8.把order_id&trade_id保存到payment模型类中
        Payment.objects.create(
            order_id = order_id,
            trade_id = trade_id
        )

        # 补充:更改订单的状态
        OrderInfo.objects.filter(order_id=order_id,
                                 status=OrderInfo.ORDER_STATUS_ENUM['UNPAID']).update(
                                status=OrderInfo.ORDER_STATUS_ENUM["UNCOMMENT"]
                                )

        # 9.拼接参数,返回结果
        return JsonResponse({'code': 0,
                             'errmsg': 'ok',
                             'trade_id': trade_id})