from celery import  Celery


import os
if not os.getenv('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'meiduo_mall.settings.dev'


celery_app = Celery('meiduo')  #  这里‘meiduo’可以使用别的字符串替换

# 把config添加到刚刚创建的对象中
celery_app.config_from_object('celery_tasks.config')

# 自动捕获目标地址下的任务，目标地址就是我们创建的文件夹sms，这个名字可以随便，tasks文件的名字规定死的
celery_app.autodiscover_tasks(['celery_tasks.sms', 'celery_tasks.email', 'celery_tasks.html'])


