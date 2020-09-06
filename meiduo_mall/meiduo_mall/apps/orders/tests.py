from django.test import TestCase
import os, sys
sys.path.insert(0, '../../..')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meiduo_mall.settings.dev')

# Create your tests here.
from decimal import Decimal
import time
import base64
from django.utils import timezone
# a = base64.b64encode(('我爱你').encode())
# print(a)
# b = (base64.b64decode(a)).decode()
# print(b)


# print(time.time())
# print(timezone.localdate())
# print(timezone.localtime())
# print(timezone.localtime().strftime('%Y%m%d%H%M%S'))
# print(time.time())



# c = Decimal('2.1111111111111122222222222')
# c = str(c)
# print(type(c), c)
# d = 2.11111111111111111122222222222
# d = str(d)
# print(type(d), d)
# print(Decimal(10.00))


