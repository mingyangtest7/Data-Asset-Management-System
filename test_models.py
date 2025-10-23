#!/usr/bin/env python
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from accounts.models import DataModel

def test_models():
    """测试模型数据"""
    print("=== 模型数据测试 ===")
    
    models = DataModel.objects.all()
    print(f"总模型数量: {models.count()}")
    
    for model in models:
        print(f"\n模型ID: {model.id}")
        print(f"模型名称: {model.name}")
        print(f"媒体文件: {model.media_files}")
        print(f"创建时间: {model.created_at}")
        print(f"创建人: {model.created_by.username}")

if __name__ == "__main__":
    test_models()

