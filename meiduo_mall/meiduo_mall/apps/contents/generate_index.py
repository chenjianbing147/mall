from collections import OrderedDict
from django.conf import settings
from django.template import loader
import os
import time
from goods.models import GoodsChannel, GoodsCategory
from contents.models import ContentCategory, Content

# 添加生成 html 文件的函数:
from goods.utils import get_categories


def generate_static_index_html():
    categories = get_categories()

    # =====================生成首页广告部分数据=======================
    # 我们定义一个字典, 里面将要存储广告内容部分:
    contents = {}
    # 从 ContentCategory 模型类中获取所有数据, 存放到 content_categories 中:
    content_categories = ContentCategory.objects.all()
    # 遍历刚刚获取的所有数据: 拿到每一个广告分类 cat:
    for cat in content_categories:
        # 根据广告分类的 外键反向
        # 获取广告内容中状态为 True 并且按 sequence 排序的部分,
        # 赋值给上面定义的字典, 快捷键(cat.key) 作为 key, 排序的部分作为value
        contents[cat.key] = Content.objects.filter(category=cat,
                                                   status=True).order_by('sequence')


    # 第二部分: 模板渲染部分:
    # 把上面两部分获取的有序字典和字典作为变量,拼接新的字典 context
    context = {
        'categories': categories,
        'contents': contents
    }

    # =====================获取模板,把数据添加进去生成页面====================
    # 根据导入的 loader 获取 'index.html' 模板
    template = loader.get_template('index.html')

    # 拿到模板, 然后将 context 渲染到模板中, 生成渲染过的模板
    html_text = template.render(context)

    # 我们拼接新的 index.html 模板将要生成的所在地地址:
    file_path = os.path.join(settings.GENERATED_STATIC_HTML_FILES_DIR, 'index.html')
    print(time.time())

    # 以写的权限,将渲染过的模板重新生成, 写入到文件中.
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_text)







