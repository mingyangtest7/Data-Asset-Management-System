#!/usr/bin/env python
import os
import sys
import django
import json

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from accounts.models import DataModel

def check_media_files():
    """检查媒体文件结构"""
    print("=== 媒体文件结构检查 ===")
    
    models = DataModel.objects.all()
    for model in models:
        print(f"\n模型: {model.name}")
        print(f"媒体文件原始数据: {model.media_files}")
        print(f"媒体文件类型: {type(model.media_files)}")
        
        if model.media_files:
            for i, media_file in enumerate(model.media_files):
                print(f"  文件 {i+1}:")
                print(f"    类型: {type(media_file)}")
                print(f"    内容: {media_file}")
                if isinstance(media_file, dict):
                    for key, value in media_file.items():
                        print(f"    {key}: {value}")

if __name__ == "__main__":
    check_media_files()

