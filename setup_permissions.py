#!/usr/bin/env python
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from accounts.models import PermissionGroup, UserPermission, User

def setup_permissions():
    """设置默认权限"""
    
    # 创建超级管理员权限组
    admin_group, created = PermissionGroup.objects.get_or_create(
        name='超级管理员',
        defaults={
            'description': '拥有所有权限的超级管理员',
            'can_view_dashboard': True,
            'can_view_my_data': True,
            'can_view_data_management': True,
            'can_view_system_settings': True,
        }
    )
    
    if created:
        print(f"创建权限组: {admin_group.name}")
    else:
        print(f"权限组已存在: {admin_group.name}")
    
    # 为所有用户分配超级管理员权限
    users = User.objects.all()
    for user in users:
        user_permission, created = UserPermission.objects.get_or_create(
            user=user,
            permission_group=admin_group
        )
        if created:
            print(f"为用户 {user.username} 分配权限组: {admin_group.name}")
        else:
            print(f"用户 {user.username} 已有权限组: {admin_group.name}")
    
    print("权限设置完成！")

if __name__ == '__main__':
    setup_permissions()

