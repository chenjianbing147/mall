#!/home/ubuntu/.virtualenvs/meiduo_mall/bin/python

import sys
sys.path.insert(0, '../../')
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meiduo_mall.settings.dev')
import django
django.setup()



from celery_tasks.html.tasks import generate_static_sku_detail_html
for i in range(1,17):
    generate_static_sku_detail_html.delay(i)