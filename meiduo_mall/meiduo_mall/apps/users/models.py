from django.db import models
from django.contrib.auth.models import AbstractUser
from meiduo_mall.utils.BaseModel import BaseModel
from itsdangerous import TimedJSONWebSignatureSerializer, BadData
from django.conf import settings

# Create your models here.

class User(AbstractUser):
    """自定义用户模型类"""

    mobile = models.CharField(max_length=11, unique=True, verbose_name='手机号')
    email_active = models.BooleanField(default=False,
                                       verbose_name='邮箱验证状态')
    default_address = models.ForeignKey('Address',
                                        related_name='users',
                                        null=True,
                                        blank=True,
                                        on_delete=models.SET_NULL,
                                        verbose_name='默认地址')


    @staticmethod
    def check_verify_email_token(token):
        """
        验证token并提取user
        :param token: 用户信息签名后的结果
        :return: user, None
        """
        obj = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, expires_in=300)

        try:
            data = obj.loads(token)

        except BadData:

            return None

        else:
            user_id = data.get('user_id')
            email = data.get('email')

        try:
            user = User.objects.get(id=user_id,email=email)
        except Exception as e:
            return None

        else:
            return user



    class Meta:
        db_table = 'tb_users'

    def __str__(self):
        return self.username




class Address(BaseModel):
    """
    用户地址
    """
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='addresses',
                             verbose_name='用户')

    province = models.ForeignKey('areas.Area',
                                 on_delete=models.PROTECT,
                                 related_name='province_addresses')
    city = models.ForeignKey('areas.Area',
                             on_delete=models.PROTECT,
                             related_name='city_address')

    district = models.ForeignKey('areas.Area',
                                on_delete=models.PROTECT,
                                related_name='district_addresses')

    title = models.CharField(max_length=20,verbose_name='地址名称')
    receiver = models.CharField(max_length=20, verbose_name='收货人')
    place = models.CharField(max_length=50, verbose_name='地址')
    mobile = models.CharField(max_length=11, verbose_name='手机')
    tel = models.CharField(max_length=20,
                           null=True,
                           blank=True,  # 该字段允许为空白
                           default='',
                           verbose_name='固定电话')

    email = models.CharField(max_length=30,
                             null=True,
                             blank=True,
                             default='',
                             verbose_name='电子邮箱')

    is_deleted = models.BooleanField(default=False, verbose_name='逻辑删除')

    class Meta:
        db_table = 'tb_address'
        ordering = ['-update_time'] # 根据更新的时间倒叙
