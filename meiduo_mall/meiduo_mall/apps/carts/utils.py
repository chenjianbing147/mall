import base64, pickle
from django_redis import get_redis_connection

def merge_cart_cookie_to_redis(request, response):
    """
    登录后合并cookie购物车数据到redis
    :param request: 本次请求对象
    :param uer: 本次响应对象
    :param response: 登录用户信息
    :return: response
    """

    cookie_cart = request.COOKIES.get('carts')

    if not cookie_cart:
        return response

    cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))

    new_dict = {}
    new_add = []
    new_remove = []

    for sku_id, item in cart_dict.items():
        new_dict[sku_id] = item['count']
        if item['selected']:
            new_add.append(sku_id)
        else:
            new_remove.append(sku_id)

    # 将new_cart_dict写入Redis数据库

    redis_conn = get_redis_connection('carts')
    pl = redis_conn.pipeline()
    pl.hmset('carts_%s' % request.user.id, new_dict)
    if new_add:
        pl.sadd('selected_%s' % request.user.id, *new_add)
    if new_remove:
        pl.srem('selected_%s' % request.user.id, *new_remove)
    pl.execute()


    request.delete_cookie('carts')
    return response


