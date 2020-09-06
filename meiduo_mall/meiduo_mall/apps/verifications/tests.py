from unittest.mock import patch

from django.test import TestCase, Client
import uuid
from django_redis import get_redis_connection

class SMSCode(TestCase):

    def setUp(self) -> None:
        self.image_code_id = str(uuid.uuid4())
        path = f'/image_codes/{self.image_code_id}/'
        self.client = Client()
        resp = self.client.get(path)
        if resp.status_code != 200:
            print('获取短信验证码失败')
        self.redis_conn = get_redis_connection('verify_code')
        res = self.redis_conn.get(f'img_{self.image_code_id}')

        if res:
            self.image_code = res.decode()
        else:
            print('没有获取到redis的数据')

        self.mobile = '13712345678'

        def tearDown(self) -> None:
            # 清理器掉 redis 中写入的数据
            self.redis_conn.delete(f'sms_{self.mobile}', f'send_flag_{self.mobile}', f'img_{self.image_code_id}')

    @patch('meiduo_mall.libs.yuntongxun.ccp_sms.CCP.send_template_sms')
    def test_sms_code(self, mock_send_sms):
        # 修改mock_send_sms.return.value
        # 构建请求路径
        mock_send_sms.return_value = 1
        path = f'/sms_codes/{self.mobile}/'
        data = {
            "image_code": self.image_code,
            "image_code_id": self.image_code_id
        }
        # 发送请求, 这里的data作为查询字符串发送
        resp = self.client.get(path, data=data)


        result = resp.json()
        if result['code'] != 0:
            print('手机验证码发送失败')
        else:
            print('手机验证码发送成功')

        # 验证手机验证码是否存在
        res = self.redis_conn.get(f'sms_{self.mobile}')
        self.assertIsNotNone(res, "redis 中没有数据")

        # 验证手机flag是否存在
        res = self.redis_conn.get(f'send_flag_{self.mobile}')
        self.assertIsNotNone(res, "redis没有flag")
        # 检查发送短信接口是否调用过
        print(mock_send_sms.called)

