from django.conf import settings
from django.core.paginator import Paginator, EmptyPage
from django.views import View
from goods.models import SKU, GoodsCategory
from django.http import JsonResponse

from .utils import get_breadcrumb
import logging
logger = logging.getLogger('django')

class ListView(View):

    def get(self, request, category_id):
        page = request.GET.get('page')
        page_size = request.GET.get('page_size')
        ordering = request.GET.get('ordering')

        if not all([page, page_size, ordering]):
            return JsonResponse({"code":400})

        # 判断category_id是否正确
        try:
            category = GoodsCategory.objects.get(id=category_id)

        except Exception as e:
            pass

        breadcrumb = get_breadcrumb(category)

        try:
            skus = SKU.objects.filter(category_id=category_id, is_launched=True).order_by(ordering)

        except Exception as e:
            pass

        paginator = Paginator(skus, page_size)

        try:
            page_skus = paginator.page(page)

        except EmptyPage:
            pass

        total_page = paginator.num_pages




        list = [{"id":page_sku.id,
                     "default_image_url":page_sku.default_image_url,
                     "name":page_sku.name,
                     "price":page_sku.price} for page_sku in page_skus]

        return JsonResponse({"code":0,
                             "msg":"ok",
                             "count":total_page,
                             "breadcrumb":breadcrumb,
                             "list":list})




class HotGoodsView(View):

    def get(self, request, category_id):

        try:
            category = GoodsCategory.objects.get(id=category_id)

        except Exception as e:
            logger.error(e)


        skus = SKU.objects.filter(category_id=category_id, is_launched=True).order_by('-sales')[0:2]

        hot_skus = []

        try:
            for sku in skus:
                hot_skus.append({"id":sku.id,
                                 "default_image_url":sku.default_image_url,
                                 "name":sku.name,
                                 "price":sku.price})
        except Exception as e:
            pass

        return JsonResponse({"code":0,
                             "msg":"ok",
                             "hot_skus":hot_skus})



from haystack.views import SearchView

class MySearchView(SearchView):

    def create_response(self):

        page = self.request.GET.get('page')

        context = self.get_context()

        data_list = []

        for sku in context['page'].object_list:
            data_list.append({
                'id': sku.object.id,
                'name': sku.object.name,
                'price': sku.object.price,
                'default_image_url': sku.object.default_image_url,
                'searchkey': context.get('query'),
                'page_size': context['page'].paginator.per_page,
                'count': context['page'].paginator.count
            })

        return JsonResponse(data_list, safe=False)



