from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from accounts.models import PermissionGroup

User = get_user_model()

def test_url_routing():
    """测试URL路由是否正确"""
    print("测试URL路由...")
    
    # 测试API端点
    api_urls = [
        '/accounts/api/data-models/',
        '/accounts/api/permission-groups/',
        '/accounts/api/location-tags/',
        '/accounts/api/project-tags/',
    ]
    
    client = Client()
    
    for url in api_urls:
        try:
            response = client.get(url)
            print(f"URL: {url} - 状态码: {response.status_code}")
        except Exception as e:
            print(f"URL: {url} - 错误: {e}")
    
    print("URL路由测试完成")

if __name__ == "__main__":
    test_url_routing()

