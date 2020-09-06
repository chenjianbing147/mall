from django.db import models
from meiduo_mall.utils.BaseModel import BaseModel

# Create your models here.

class QAuthQQuser(BaseModel):

    user = models.ForeignKey('users.User',
                             on_delete=models.CASCADE,)

    openid = models.CharField(max_length=64,
                              verbose_name='openid',
                              db_index=True)

    class Meta:
        db_table = 'tb_oauth_qq'



# 外检关联别的子应用只需要在前面加上子应用的名称，
