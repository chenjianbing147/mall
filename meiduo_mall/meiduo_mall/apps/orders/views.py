from decimal import Decimal
import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection
from .models import OrderGoods, OrderInfo
from goods.models import SKU
from meiduo_mall.utils.Views import LoginRequiredMixin
from users.models import Address
from django.utils import timezone
from django.db import transaction



class OrderSettlementView(LoginRequiredMixin,View):

    def get(self, request):

        # 1.  从mysql中Addresss 中获取该用户没有删除的地址
        try:
            addresses = Address.objects.filter(user=request.user, is_deleted=False)
        except Exception as e:
            return JsonResponse({"code":400,
                                 'errmsg':'数据库出错'})

        address_list = []

        # 2. 遍历addresses所有的地址
        for address in addresses:
            address_list.append({
                'id': address.id,
                'province': address.province.name,
                'city': address.city.name,
                'district': address.district.name,
                'place': address.place,
                'receiver': address.receiver,
                'mobile': address.mobile
            })
        # 3. 连接redis
        redis_conn = get_redis_connection('carts')

        # 4. 从hash中获取count
        item_dict = redis_conn.hgetall('carts_%s' % request.user.id)

        # 5. 从set中获取sku_id
        selected_item = redis_conn.smembers('selected_%s' % request.user.id )
        dict = {}

        # 6. 整理成{sku_id:count}
        for sku_id in selected_item:
            dict[int(sku_id)] = int(item_dict[sku_id])

        # 7. 把sku_id变成sku
        try:
            skus = SKU.objects.filter(id__in=dict.keys())
        except Exception as e:
            return JsonResponse({"code":400,
                                 'errmsg':'数据库出错'})

        # 8. 获取所有的商品
            # 查询商品信息
        sku_list = []
        for sku in skus:
            sku_list.append({
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image_url,
                'count': dict[sku.id],
                'price': sku.price
            })
        # 9.定义一个运费的变量
        yunfei = Decimal('10.00')
        # 10. 整理数据
        dict = {
            'addresses':address_list,
            'freight':yunfei,
            'skus':sku_list

        }
        # 11. 返回
        return JsonResponse({"code":0,
                             "context":dict})


class OrderCommitView(View):
    """订单提交"""

    def post(self, request):
        """保存订单信息和订单商品信息"""
        # 获取当前保存订单时需要的信息
        json_dict = json.loads(request.body)
        address_id = json_dict.get('address_id')
        pay_method = json_dict.get('pay_method')

        # 校验参数
        if not all([address_id, pay_method]):
            return JsonResponse({'code':400,
                                       'errmsg': '缺少必传参数'})
            # 判断address_id是否合法
        try:
            address = Address.objects.get(id=address_id)
        except Exception as e:
            return JsonResponse({'code':400,
                                       'errmsg': '参数address_id有误'})
         # 判断pay_method是否合法
        if pay_method not in [OrderInfo.PAY_METHODS_ENUM['CASH'],
                              OrderInfo.PAY_METHODS_ENUM['ALIPAY']]:
            return JsonResponse({'code':400,
                            'errmsg': '参数pay_method有误'})

        # 获取登录用户
        user = request.user
        # 生成订单编号：年月日时分秒+用户编号
        order_id = timezone.localtime().strftime('%Y%m%d%H%M%S') + ('%09d' % user.id)


        # 显式的开启一个事务
        with transaction.atomic():
            # 创建事务保存点
            save_id = transaction.savepoint()

            # 保存订单基本信息 OrderInfo（一）
            order = OrderInfo.objects.create(
                order_id=order_id,
                user=user,
                address=address,
                total_count=0,
                total_amount=Decimal('0'),
                freight=Decimal('10.00'),
                pay_method=pay_method,
                status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'] if pay_method == OrderInfo.PAY_METHODS_ENUM['ALIPAY'] else
                OrderInfo.ORDER_STATUS_ENUM['UNSEND']
            )

            # 从redis读取购物车中被勾选的商品信息
            redis_conn = get_redis_connection('carts')
            redis_cart = redis_conn.hgetall('carts_%s' % user.id)
            selected = redis_conn.smembers('selected_%s' % user.id)
            carts = {}
            for sku_id in selected:
                carts[int(sku_id)] = int(redis_cart[sku_id])
            sku_ids = carts.keys()

            # 遍历购物车中被勾选的商品信息
            for sku_id in sku_ids:
                # 增加的代码: 增加一个死循环
                while True:
                    # 查询SKU信息
                    sku = SKU.objects.get(id=sku_id)

                    # 增加的代码: 读取原始库存
                    origin_stock = sku.stock
                    origin_sales = sku.sales

                    # 判断SKU库存
                    sku_count = carts[sku.id]
                    if sku_count > sku.stock:
                        # 事务回滚
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse({
                                'code': 400,
                                'errmsg': '库存不足'
                        })


                    # SKU减少库存，增加销量
                    # sku.stock -= sku_count
                    # sku.sales += sku_count
                    # sku.save()

                    # 增加的代码: 乐观锁更新库存和销量
                    # 计算差值
                    new_stock = origin_stock - sku_count
                    new_sales = origin_sales + sku_count
                    result = SKU.objects.filter(
                                    id=sku_id,
                                    stock=origin_stock
                    ).update(stock=new_stock, sales=new_sales)
                    # 如果下单失败，但是库存足够时，
                    # 继续下单，直到下单成功或者库存不足为止
                    if result == 0:
                        continue

                    # 修改SPU销量
                    sku.goods.sales += sku_count
                    sku.goods.save()

                    # 保存订单商品信息 OrderGoods（多）
                    OrderGoods.objects.create(
                        order=order,
                        sku=sku,
                        count=sku_count,
                        price=sku.price,
                    )

                    # 保存商品订单中总价和总数量
                    order.total_count += sku_count
                    order.total_amount += (sku_count * sku.price)

                    # 增加的代码:
                    # 下单成功或者失败就跳出循环
                    break

            # 添加邮费和保存订单信息
            order.total_amount += order.freight
            order.save()
            # 清除保存点
            transaction.savepoint_commit(save_id)

        # 清除购物车中已结算的商品
        pl = redis_conn.pipeline()
        pl.hdel('carts_%s' % user.id, *selected)
        pl.srem('selected_%s' % user.id, *selected)
        pl.execute()

        # 响应提交订单结果
        return JsonResponse({'code': 0,
                             'errmsg': '下单成功',
                             'order_id': order.order_id
                           })

