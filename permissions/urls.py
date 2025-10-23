from django.urls import path
from . import views

app_name = 'permissions'

urlpatterns = [
    # 角色管理
    path('roles/', views.role_list, name='role_list'),
    path('roles/create/', views.role_create, name='role_create'),
    path('roles/<int:role_id>/edit/', views.role_edit, name='role_edit'),
    path('roles/<int:role_id>/delete/', views.role_delete, name='role_delete'),
    
    # 用户管理
    path('users/', views.user_list, name='user_list'),
    path('users/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    
    # 个人权限
    path('my-permissions/', views.my_permissions, name='my_permissions'),
    
    # 初始化权限（仅开发环境）
    path('init-permissions/', views.init_permissions, name='init_permissions'),
]
