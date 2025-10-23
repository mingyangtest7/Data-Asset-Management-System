#!/usr/bin/env python
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from accounts.models import DataModel, UploadLog, LocationTag, ProjectTag

def check_database_data():
    """检查数据库中的数据"""
    print("=== 数据库数据检查 ===")
    
    # 检查数据模型
    models = DataModel.objects.all()
    print(f"数据模型总数: {models.count()}")
    
    for model in models:
        print(f"\n模型: {model.name}")
        print(f"  来源: {model.get_source_display()}")
        print(f"  等级: {model.get_model_level_display()}")
        print(f"  创建时间: {model.created_at}")
        print(f"  创建者: {model.created_by.username}")
        print(f"  媒体文件: {len(model.media_files) if model.media_files else 0} 个")
        if model.media_files:
            for media_file in model.media_files:
                print(f"    - {media_file.get('filename', 'unknown')}")
    
    # 检查上传日志
    uploads = UploadLog.objects.all()
    print(f"\n上传日志总数: {uploads.count()}")
    
    for upload in uploads:
        print(f"\n上传记录: {upload.filename}")
        print(f"  用户: {upload.user.username}")
        print(f"  文件大小: {upload.file_size} bytes")
        print(f"  上传时间: {upload.upload_time}")
        print(f"  状态: {upload.status}")
    
    # 检查标签
    location_tags = LocationTag.objects.all()
    project_tags = ProjectTag.objects.all()
    
    print(f"\n地理位置标签: {location_tags.count()}")
    for tag in location_tags:
        print(f"  - {tag.name}")
    
    print(f"\n项目归属标签: {project_tags.count()}")
    for tag in project_tags:
        print(f"  - {tag.name}")

if __name__ == "__main__":
    check_database_data()
