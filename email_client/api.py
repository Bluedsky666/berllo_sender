import requests
import hashlib
import json
import base64
from urllib.parse import urlencode

class ApiClient:
    """
    用于与邮件发送服务器API进行交互的客户端。
    """
    def __init__(self, host="127.0.0.1", port=8060, key="", use_ssl=False):
        """
        初始化ApiClient。
        :param host: 服务器主机地址
        :param port: 服务器端口
        :param key: 用于签名的API密钥
        :param use_ssl: 是否使用HTTPS
        """
        protocol = "https://" if use_ssl else "http://"
        self.base_url = f"{protocol}{host}:{port}"
        self.key = key

    def _calculate_signature(self, query_string="", post_data=""):
        """
        计算API请求签名。
        签名算法为: md5(QueryString + key + PostData + key)
        :param query_string: URL中的查询字符串
        :param post_data: POST请求体
        :return: 包含签名的请求头字典
        """
        if not self.key:
            return {}

        # API文档规定使用GBK编码。所有参与签名的组件都必须在哈希前进行GBK编码。
        query_bytes = str(query_string).encode('gbk')
        key_bytes = str(self.key).encode('gbk')
        post_data_bytes = str(post_data).encode('gbk')

        # 签名原文: QueryString + key + PostData + key
        signature_str = query_bytes + key_bytes + post_data_bytes + key_bytes

        signature = hashlib.md5(signature_str).hexdigest()

        # API兼容 berllosoft-auth 和 qiangsoft-auth 两种请求头
        return {
            "berllosoft-auth": signature,
            "qiangsoft-auth": signature
        }

    def _make_request(self, method, endpoint, params=None, data=None):
        """
        发送HTTP请求到API服务器。
        :param method: 请求方法 (GET, POST)
        :param endpoint: API端点 (例如 /test)
        :param params: URL查询参数
        :param data: POST请求的数据 (通常是字典或列表)
        :return: 服务器响应的JSON数据
        """
        url = self.base_url + endpoint
        query_string = urlencode(params, encoding='gbk') if params else ""

        full_url = f"{url}?{query_string}" if query_string else url

        post_data_str = ""
        if data is not None:
            # 用于签名的POST数据是原始的JSON字符串
            post_data_str = json.dumps(data, separators=(',', ':'), ensure_ascii=False)

        headers = self._calculate_signature(query_string=query_string, post_data=post_data_str)
        headers['Content-Type'] = 'application/json'

        try:
            # 文档规定请求体使用GBK编码
            encoded_data = post_data_str.encode('gbk') if post_data_str else None

            response = requests.request(
                method,
                full_url,
                headers=headers,
                data=encoded_data,
                timeout=30 # 30秒超时
            )
            response.raise_for_status()

            # API响应也使用GBK编码，因此需要正确解码
            response.encoding = 'gbk'
            return response.json()

        except requests.exceptions.RequestException as e:
            return {"ret": 500, "msg": f"请求失败: {e}"}
        except json.JSONDecodeError:
            return {"ret": 500, "msg": "无法解码服务器返回的JSON响应。"}

    def test_connection(self):
        """接口1：测试API连通性。"""
        return self._make_request("GET", "/test")

    def send_bulk_emails(self, emails: list, template_id: int = None):
        """接口2：使用模板批量发送邮件。"""
        params = {}
        if template_id:
            params['tid'] = template_id

        return self._make_request("POST", "/send", params=params, data=emails)

    def push_single_email(self, email: str, subject: str, content: str, **kwargs):
        """接口3：推送单封通知邮件。"""
        # 标题和内容必须是Base64编码
        encoded_subject = base64.b64encode(subject.encode('gbk')).decode('ascii')
        encoded_content = base64.b64encode(content.encode('gbk')).decode('ascii')

        data = {
            "email": email,
            "subject": encoded_subject,
            "content": encoded_content,
        }
        # 添加可选的宏定义
        for i in range(1, 6):
            if f"def{i}" in kwargs:
                data[f"def{i}"] = kwargs[f"def{i}"]

        return self._make_request("POST", "/push", data=data)

    def query_send_results(self, guids: list):
        """接口4：查询邮件发送结果。"""
        return self._make_request("POST", "/query", data=guids)
