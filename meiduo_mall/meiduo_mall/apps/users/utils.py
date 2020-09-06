from .models import User
from django.contrib.auth.backends import ModelBackend
import re

def get_user_by_account(account):
    """判断account是否是是手机号，返回user对象"""
    try:
        if re.match('^1[3-9]\d{9}$', account):
            user = User.objects.get(mobile=account)

        else:
            user = User.objects.get(username=account)

    except Exception as e:
        user = None

    return user




class UsernameMobileAuthBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):

        user = get_user_by_account(username)

        if user and user.check_password(password):
            return user









