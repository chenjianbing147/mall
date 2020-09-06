from django.views import View
from .models import Area
from django.http import JsonResponse
from django.core.cache import cache






class ProvinceAreasView(View):

    def get(self, request):

        province_list = cache.get('province_list')

        if not province_list:
            try:
                data = Area.objects.filter(parent_id__isnull=True)
                province_list = []
                for province in data:
                    province_list.append({"id":province.id,
                                          "name":province.name})
                    cache.set('province_list', province_list, 3600)

            except Exception as e:
                return JsonResponse({"code":400,
                                     "errmsg":"服务器出错"})


        return JsonResponse({"code":0,
                             "msg":"ok",
                             "province_list":province_list})


# 妈的, 存储进去和读取出来的数据类型相同, 你存的字典, 读出来就是字典, 存的是列表, 读出来就是列表, 只有这个cache 有
# 这里存储进去和读取出来的数据类型相同，所以读取出来后可以直接使用
class SubAreasView(View):

    def get(self, request ,pk):

        sub_data = cache.get('sub_data_%s' % pk)

        if not sub_data:

            try:
                subs = Area.objects.filter(parent_id=pk)
                province = Area.objects.get(id=pk)

                sub_list = []
                for sub in subs:
                    sub_list.append({"id":sub.id,
                                     "name":sub.name})

                sub_data = {"id":pk,
                            "name":province.name,
                            "subs":sub_list}

                cache.set('sub_data_%s' % pk, sub_data, 3600)

            except Exception as e:
                return JsonResponse({'code': 400,
                                     'errmsg': '城市或区县数据错误'})


        return JsonResponse({"code":0,
                             "msg":"ok",
                             "sub_data":sub_data})


















