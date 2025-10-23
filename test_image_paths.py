#!/usr/bin/env python
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from accounts.models import DataModel

def test_image_paths():
    """测试图片路径"""
    print("=== 图片路径测试 ===")
    
    models = DataModel.objects.all()
    for model in models:
        print(f"\n模型: {model.name}")
        print(f"媒体文件: {model.media_files}")
        
        if model.media_files:
            for media_file in model.media_files:
                print(f"  文件名: {media_file['name']}")
                print(f"  路径: {media_file['path']}")
                
                # 检查文件是否存在
                full_path = os.path.join('media', media_file['path'])
                if os.path.exists(full_path):
                    print(f"  文件存在: {full_path}")
                    print(f"  文件大小: {os.path.getsize(full_path)} bytes")
                else:
                    print(f"  文件不存在: {full_path}")
                
                # 检查URL路径
                url_path = f"/{media_file['path']}"
                print(f"  URL路径: {url_path}")
                
                # 检查是否为图片文件
                name_lower = media_file['name'].lower()
                is_image = any(ext in name_lower for ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tga'])
                print(f"  是否为图片: {is_image}")

if __name__ == "__main__":
    test_image_paths()
