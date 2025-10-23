#!/usr/bin/env python
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from accounts.models import UploadLog, DownloadLog, User
from django.utils import timezone
from datetime import timedelta
import json

# 获取第一个用户
user = User.objects.first()
if user:
    print(f"用户: {user.username}")
    
    # 获取统计数据
    user_total_uploads = UploadLog.objects.filter(user=user, status='success').count()
    user_total_downloads = DownloadLog.objects.filter(user=user, status='success').count()
    
    print(f"总上传数: {user_total_uploads}")
    print(f"总下载数: {user_total_downloads}")
    
    # 生成最近30天的数据
    dates = []
    upload_counts = []
    download_counts = []
    
    for i in range(30):
        date = timezone.now() - timedelta(days=29-i)
        dates.append(date.strftime('%m-%d'))
        
        # 统计当天的上传数量
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        upload_count = UploadLog.objects.filter(
            user=user,
            upload_time__gte=day_start,
            upload_time__lt=day_end,
            status='success'
        ).count()
        
        download_count = DownloadLog.objects.filter(
            user=user,
            download_time__gte=day_start,
            download_time__lt=day_end,
            status='success'
        ).count()
        
        upload_counts.append(upload_count)
        download_counts.append(download_count)
    
    chart_data = {
        'dates': dates,
        'upload_counts': upload_counts,
        'download_counts': download_counts,
    }
    
    print("图表数据:")
    print(json.dumps(chart_data, indent=2, ensure_ascii=False))
    
    # 检查是否有任何数据
    print(f"\n最近30天上传数据: {sum(upload_counts)}")
    print(f"最近30天下载数据: {sum(download_counts)}")
    
else:
    print("没有找到用户")

