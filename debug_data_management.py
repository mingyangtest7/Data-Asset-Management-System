#!/usr/bin/env python
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from accounts.models import DataModel

def debug_data_management():
    """调试数据管理页面数据"""
    print("=== 数据管理页面调试 ===")
    
    models = DataModel.objects.all().order_by('-created_at')
    print(f"总模型数量: {models.count()}")
    
    for model in models:
        print(f"\n模型: {model.name}")
        print(f"ID: {model.id}")
        print(f"媒体文件: {model.media_files}")
        print(f"媒体文件类型: {type(model.media_files)}")
        
        if model.media_files:
            print(f"媒体文件数量: {len(model.media_files)}")
            for i, media_file in enumerate(model.media_files):
                print(f"  文件 {i+1}:")
                print(f"    名称: {media_file.get('name', 'N/A')}")
                print(f"    路径: {media_file.get('path', 'N/A')}")
                print(f"    大小: {media_file.get('size', 'N/A')}")
                
                # 检查文件是否存在
                import os
                full_path = os.path.join('media', media_file.get('path', ''))
                if os.path.exists(full_path):
                    print(f"    文件存在: 是")
                else:
                    print(f"    文件存在: 否")
        else:
            print("没有媒体文件")

if __name__ == "__main__":
    debug_data_management()

