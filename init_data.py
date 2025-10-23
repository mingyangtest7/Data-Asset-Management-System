import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from accounts.models import User, PermissionGroup, UserPermission, LocationTag, ProjectTag

def init_data():
    """初始化系统数据"""
    
    # 1. 创建默认权限组
    permission_groups = [
        {
            'name': '超级管理员',
            'description': '拥有所有权限的超级管理员',
            'can_view_dashboard': True,
            'can_view_my_data': True,
            'can_view_data_management': True,
            'can_view_system_settings': True,
        },
        {
            'name': '普通用户',
            'description': '只能查看数据统计和我的数据',
            'can_view_dashboard': True,
            'can_view_my_data': True,
            'can_view_data_management': False,
            'can_view_system_settings': False,
        },
        {
            'name': '数据管理员',
            'description': '可以管理数据但不能访问系统设置',
            'can_view_dashboard': True,
            'can_view_my_data': True,
            'can_view_data_management': True,
            'can_view_system_settings': False,
        },
        {
            'name': '只读用户',
            'description': '只能查看数据统计',
            'can_view_dashboard': True,
            'can_view_my_data': False,
            'can_view_data_management': False,
            'can_view_system_settings': False,
        }
    ]
    
    for group_data in permission_groups:
        permission_group, created = PermissionGroup.objects.get_or_create(
            name=group_data['name'],
            defaults=group_data
        )
        if created:
            print(f"创建权限组: {permission_group.name}")
    
    # 2. 创建默认地理位置标签
    location_tags = [
        '北京', '上海', '广州', '深圳', '杭州', '南京', '武汉', '成都', '西安', '重庆'
    ]
    
    for tag_name in location_tags:
        location_tag, created = LocationTag.objects.get_or_create(name=tag_name)
        if created:
            print(f"创建地理位置标签: {location_tag.name}")
    
    # 3. 创建默认项目归属标签
    project_tags = [
        '具身智能项目', 'VR/AR项目', '游戏开发项目', '建筑设计项目', 
        '影视制作项目', '教育培训项目', '医疗健康项目', '工业设计项目'
    ]
    
    for tag_name in project_tags:
        project_tag, created = ProjectTag.objects.get_or_create(name=tag_name)
        if created:
            print(f"创建项目归属标签: {project_tag.name}")
    
    # 4. 为超级用户分配权限
    try:
        superuser = User.objects.filter(is_superuser=True).first()
        if superuser:
            super_admin_permission = PermissionGroup.objects.get(name='超级管理员')
            UserPermission.objects.get_or_create(
                user=superuser,
                defaults={'permission_group': super_admin_permission}
            )
            print(f"为超级用户 {superuser.username} 分配超级管理员权限")
    except Exception as e:
        print(f"分配权限时出错: {e}")
    
    print("数据初始化完成！")

if __name__ == '__main__':
    init_data()