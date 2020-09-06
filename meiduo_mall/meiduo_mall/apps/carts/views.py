import json
from django.http import JsonResponse
from django.views import View
from django_redis import get_redis_connection
import pickle, base64

from goods.models import SKU


class CartsView(View):

    def post(self, request):
        content = json.loads(request.body)
        sku_id = content.get('sku_id')
        count = content.get('count')
        selected = content.get('selected', True)

        if not all([sku_id, count]):
            return JsonResponse({"code": 400,
                                 "errmsg": "缺少参数"})

        try:
            SKU.objects.get(id=sku_id)
        except Exception as e:
            return JsonResponse({"code": 400,
                                 })

        try:
            count = int(count)
            if count <= 0:
                return JsonResponse({"code": 400,
                                     })

        except Exception as e:
            return JsonResponse({"code": 400,
                                 })

        user = request.user
        if user.is_authenticated:
            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipeline()
            pl.hincrby('carts_%s' % user.id, sku_id, count)
            pl.sadd('selected_%s' % user.id, sku_id)

            pl.execute()
            return JsonResponse({"code": 0})

        else:
            cookie_cart = request.COOKIES.get('carts')
            if cookie_cart:
                cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))

            else:
                cart_dict = {}

            if sku_id in cart_dict:
                count += cart_dict[sku_id]['count']

            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }

            cart_data = base64.b64encode(pickle.dumps(cart_dict)).decode()
            response = JsonResponse({"code": 0})
            response.set_cookie('carts', cart_data, max_age=3600 * 24 * 14)
            return response

    def get(self, request):
        user = request.user

        if user.is_authenticated:
            redis_conn = get_redis_connection('carts')
            item_dict = redis_conn.hgetall('carts_%s' % user.id)
            selected = redis_conn.smembers('selected_%s' % user.id)
            cart_dict = {}
            for sku_id, count in item_dict.items():
                cart_dict[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in selected
                }

        else:
            cookie_cart = request.COOKIES.get('carts')
            if cookie_cart:
                cart_dict = pickle.loads(base64.b64decode(cookie_cart))
            else:
                cart_dict = {}

        sku_ids = cart_dict.keys()
        try:
            skus = SKU.objects.filter(id__in=sku_ids)
        except Exception as e:
            return JsonResponse({"code": 400})
        cart_skus = []
        for sku in skus:
            cart_skus.append({
                'id': sku.id,
                'name': sku.name,
                'count': cart_dict.get(sku.id).get('count'),
                'selected': cart_dict[sku.id]['selected'],
                'default_image_url': sku.default_image_url,
                'price': sku.price,
                'amount': sku.price * cart_dict.get(sku.id).get('count')

            })

        return JsonResponse({"code": 0,
                             "cart_skus": cart_skus})

    def put(self, request):
        content = json.loads(request.body)
        sku_id = content.get('sku_id')
        count = content.get('count')
        selected = content.get('selected', True)

        if not all([sku_id, count]):
            return JsonResponse({"code": 400,
                                 "errmsg": "缺少参数"})

        try:
            SKU.objects.get(id=sku_id)
        except Exception as e:
            return JsonResponse({"code": 400,
                                 })

        try:
            count = int(count)
            if count <= 0:
                return JsonResponse({"code": 400,
                                     })

        except Exception as e:
            return JsonResponse({"code": 400,
                                 })
        if selected:
            if not isinstance(selected, bool):
                return JsonResponse({"code": 400,
                                     })
        user = request.user
        if user.is_authenticated:
            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipeline()
            pl.hset('carts_%s' % user.id, sku_id, count)
            if selected:
                pl.sadd('selected_%s' % user.id, sku_id)
            else:
                pl.srem('selected_%s' % user.id, sku_id)

            pl.execute()
            return JsonResponse({"code": 0,
                                 'cart_sku': {
                                     'id': sku_id,
                                     'count': count,
                                     'selected': selected
                                 }})

        else:
            cookie_cart = request.COOKIES.get('carts')
            if cookie_cart:
                cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))

            else:
                cart_dict = {}

            # 幂等性, 直接覆盖
            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }

            cart_data = base64.b64encode(pickle.dumps(cart_dict)).decode()
            response = JsonResponse({"code": 0,
                                     'cart_sku': {
                                         'id': sku_id,
                                         'count': count,
                                         'selected': selected
                                     }})
            response.set_cookie('carts', cart_data, max_age=3600 * 24 * 14)
            return response

    def delete(self, request):
        json_dict = json.loads(request.body)
        sku_id = json_dict.get('sku_id')

        try:
            SKU.objects.get(id=sku_id)
        except Exception as e:
            return JsonResponse({"code": 400,
                                 "errmsg": 该商品不存在})

        user = request.user

        if user.is_authenticated:
            redis_conn = get_redis_connection('carts')

            pl = redis_conn.pipeline()

            pl.hdel('carts_%s' % user.id, sku_id)
            pl.srem('selected_%s' % user.id, sku_id)
            pl.execute()

            return JsonResponse({"code": 0,
                                 "msg": '删除购物车成功'})

        else:
            cookie_cart = request.COOKIES.get('carts')
            if cookie_cart:
                cart_dict = pickle.loads(base64.b64decode(cookie_cart))
            else:
                cart_dict = {}

            response = JsonResponse({"code": 0,
                                     "msg": "删除购物车成功"})
            if sku_id in cart_dict:
                del cart_dict[sku_id]

                cart_data = base64.b64encode(pickle.dumps(cart_dict)).decode()

                response.set_cookie('carts', cart_dict)
            return response


class CartSelectAllView(View):

    def put(self, request):
        json_dict = json.loads(request.body)
        selected = json_dict.get('selected')

        if not isinstance(selected, bool):
            return JsonResponse({"code": 0, })

        user = request.user

        if user.is_authenticated:
            redis_conn = get_redis_connection('carts')
            sku_ids = redis_conn.hkeys('carts_%s' % user.id)

            if selected:
                redis_conn.sadd('selected_%s' % user.id, *sku_ids)
            else:
                redis_conn.srem('selected_%s' % user.id, *sku_ids)

            return JsonResponse({"code": 0})
        else:
            cookie_cart = request.COOKIES.get('carts')
            response = JsonResponse({"code": 0,
                                     "msg": "全选成功"})

            if cookie_cart:
                cart_dict = pickle.loads(base64.b64decode(cookie_cart))
                for key in cart_dict.keys():
                    cart_dict[key]['selected'] = selected
                cart_data = base64.b64encode(pickle.dumps(cart_dict)).decode()
            response.set_cookie('carts', cart_data)
            return response


class CartsSimpleView(View):

    def get(self, request):
        user = request.user
        if user.is_authenticated:
            redis_conn = get_redis_connection('carts')
            item_dict = redis_conn.hgetall('carts_%s' % user.id)
            cart_dict = {}
            for sku_id,count in item_dict.items():
                cart_dict[int(sku_id)] = {
                    'count':int(count)
                }


        else:
            cookie_cart = request.COOKIES.get('carts')
            if cookie_cart:
                cart_dict = pickle.loads(base64.b64decode(cookie_cart))
            else:
                cart_dict = {}
        cart_skus = []
        sku_ids = cart_dict.keys()
        skus = SKU.objects.filter(id__in=sku_ids)

        try:
            for sku in skus:
                cart_skus.append({
                    'id': sku.id,
                    'name': sku.name,
                    'count': cart_dict.get(sku.id).get('count'),
                    'default_image_url': sku.default_image_url
                })
        except Exception as e:
            return JsonResponse({'code':400})

        return JsonResponse({'code': 0,
                             'errmsg': 'OK',
                             'cart_skus': cart_skus})




# class CartsSimpleView(View):
#
#     def get(self, request):
#
#         user = request.user
#
#         if user.is_authenticated:
#             redis_conn = get_redis_connection('carts')
#             item_dict = redis_conn.hgetall('carts_%s' % user.id)
#
#             selected_item = redis_conn.smemebers('selected_%s' % user.id)
#             cart_dict
#             for sku_id, count in item_dict.items():
#                 cart_dict[int(sku_id)] = {
#                     'count':int(count),
#                     'selected':sku_id in selected_item
#
#
#                 }
#         else:
#
#             cookie_cart = request.COOKIES.get('carts')
#
#             if cookie_cart:
#                 cart_dict = pickle.loads(base64.b64decode(cookie_cart))
#
#             else:
#                 pass
#
#             sku_ids = cart_dict.keys()
#             try:
#                 skus = SKU.objects.filter(id__in=sku_ids)
#                 for sku in skus:
#                     {
#                         'id':sku.id,
#                         'name':sku.name,
#                         'count':cart_dict[sku.id]['count'],
#                         'default_image_url':sku.default_image_url
#                     }
#             except Exception as e:
#                 return JsonResponse({"code":0})
