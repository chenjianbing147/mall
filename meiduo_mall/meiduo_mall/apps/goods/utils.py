import sys
sys.path.insert(0, '../../../')
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meiduo_mall.settings.dev')
import django
django.setup()


from django.http import JsonResponse
from collections import OrderedDict
from goods.models import GoodsCategory
from goods.models import GoodsChannel, SKU
from goods.models import SKUImage, SKUSpecification
from goods.models import GoodsSpecification, SpecificationOption


def get_breadcrumb(cateory):

    dict = {
        'cat1':'',
        'cat2':'',
        'cat3':'',
    }

    if cateory.parent is None:
        dict['cat1'] = cateory.name

    elif cateory.parent.parent is None:
        dict['cat2'] = cateory.name
        dict['cat1'] = cateory.parent.name

    else:
        dict['cat3'] = cateory.name
        dict['cat2'] = cateory.parent.name
        dict['cat1'] = cateory.parent.parent.name

    return dict


def get_goods_and_spec(sku_id):

    # ======== 获取该商品和该商品对应的规格选项id ========
    # 根据 sku_id 获取该商品(sku)
    sku = SKU.objects.get(id=sku_id)
    # 获取该商品的图片
    sku.images = SKUImage.objects.filter(sku=sku)

    # ======== 获取类别下所有商品对应的规格选项id ========
    # 根据sku对象,获取对应的类别
    goods = sku.goods

    # 获取该类别下面的所有商品
    skus = SKU.objects.filter(goods=goods)

    dict = {}
    for temp_sku in skus:
        # 获取每一个商品(temp_sku)的规格参数
        sku_zuhe = SKUSpecification.objects.filter(sku=temp_sku).order_by('spec_id')

        temp_list = []
        for zuhe in sku_zuhe:
            # 规格 ---> 规格选项 ---> 规格选项id ----> 保存到[]
            temp_list.append(zuhe.option.id)

        # 把 list 转为 () 拼接成 k : v 保存到dict中:
        dict[tuple(temp_list)] = temp_sku.id

    # ======== 在每个选项上绑定对应的sku_id值 ========
    guige_list = GoodsSpecification.objects.filter(goods=goods).order_by('id')

    for index, guige in enumerate(guige_list):
        # 该规格的选项
        guige_xuanxiang = SpecificationOption.objects.filter(spec=guige)
        for xuanxiang in guige_xuanxiang:
            # 在规格参数sku字典中查找符合当前规格的sku
            temp_list[index] = xuanxiang.id
            xuanxiang.sku_id = dict.get(tuple(temp_list))

        guige.spec_options = guige_xuanxiang

    return goods, guige_list, sku




def get_categories():

    # ======== 生成上面字典格式数据 ========
    # 第一部分: 从数据库中取数据:
    # 定义一个有序字典对象
    dict = OrderedDict()

    # 对 GoodsChannel 进行 group_id 和 sequence 排序, 获取排序后的结果:
    channels = GoodsChannel.objects.order_by('group_id', 'sequence')

    # 遍历排序后的结果: 得到所有的一级菜单( 即,频道 )
    for channel in channels:
        # 从频道中得到当前的 组id
        group_id = channel.group_id

        # 判断: 如果当前 组id 不在我们的有序字典中:
        if group_id not in dict:
            # 我们就把 组id 添加到 有序字典中
            # 并且作为 key值, value值是
            # {'channels': [], 'sub_cats': []}
            dict[group_id] =  {
                                 'channels': [],
                                 'sub_cats': []
                               }

        # 获取当前频道的分类名称
        cat1 = channel.category

        # 给刚刚创建的字典中, 追加具体信息:
        # 即, 给'channels' 后面的 [] 里面添加如下的信息:
        dict[group_id]['channels'].append({
            'id':   cat1.id,
            'name': cat1.name,
            'url':  channel.url
        })
        cat2s = GoodsCategory.objects.filter(parent=cat1)
        # 根据 cat1 的外键反向, 获取下一级(二级菜单)的所有分类数据, 并遍历:
        for cat2 in cat2s:
            # 创建一个新的列表:
            cat2.sub_cats = []
            # 获取所有的三级菜单
            cat3s = GoodsCategory.objects.filter(parent=cat2)
            # 遍历
            for cat3 in cat3s:
                # 把三级菜单保存到cat2对象的属性中.
                cat2.sub_cats.append(cat3)
            # 把cat2对象保存到对应的列表中
            dict[group_id]['sub_cats'].append(cat2)

    return dict




if __name__ == '__main__':
    get_goods_and_spec(10)
