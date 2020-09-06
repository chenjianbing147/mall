# 定义任务
# 真实的开发环境有可能会把celery——tasks单独拿到某一个电脑上独立执行，会和美多商城项目分开，所以那时就找不到libs了

from celery_tasks.main import celery_app
from celery_tasks.yuntongxun.ccp_sms import CCP

@celery_app.task(name='cpp_send_sms_code')
def ccp_send_sms_code(mobile, sms_code):
    CCP().send_template_sms(mobile, [sms_code, 5], 1)
