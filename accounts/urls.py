from django.urls import path
from django.shortcuts import redirect
from . import views

def redirect_to_login(request):
    return redirect('accounts:login')

app_name = 'accounts'

urlpatterns = [
    # 页面路由
    path('', redirect_to_login, name='home'),
    path('login/', views.login_view, name='login'),
    path('main/', views.main_view, name='main'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('my-data/', views.my_data_view, name='my_data'),
    path('data-management/', views.data_management_view, name='data_management'),
    path('system-settings/', views.system_settings_view, name='system_settings'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('person/', views.person_view, name='person'),
    path('test-data-management/', views.test_data_management_view, name='test_data_management'),
    
    # API 路由 - 权限管理
    path('api/permission-groups/', views.create_permission_group, name='create_permission_group'),
    path('api/permission-groups/<int:group_id>/', views.update_permission_group, name='update_permission_group'),
    path('api/permission-groups/<int:group_id>/delete/', views.delete_permission_group, name='delete_permission_group'),
    
    # API 路由 - 标签管理
    path('api/location-tags/', views.create_location_tag, name='create_location_tag'),
    path('api/project-tags/', views.create_project_tag, name='create_project_tag'),
    path('api/location-tags/<int:tag_id>/delete/', views.delete_location_tag, name='delete_location_tag'),
    path('api/project-tags/<int:tag_id>/delete/', views.delete_project_tag, name='delete_project_tag'),
    
    # API 路由 - 数据模型管理
    path('api/data-models/', views.upload_data_model, name='upload_data_model'),
    path('api/data-models/<int:model_id>/', views.get_data_model, name='get_data_model'),
    path('api/data-models/<int:model_id>/update/', views.update_data_model, name='update_data_model'),
    path('api/data-models/<int:model_id>/delete/', views.delete_data_model, name='delete_data_model'),
    
    # API 路由 - 模型详情和编辑
    path('api/models/<int:model_id>/', views.get_model_detail, name='get_model_detail'),
    path('api/models/<int:model_id>/update/', views.update_model, name='update_model'),
    path('api/models/<int:model_id>/delete/', views.delete_model, name='delete_model'),
    
    # API 路由 - 用户管理
    path('api/users/<int:user_id>/toggle-status/', views.toggle_user_status, name='toggle_user_status'),
    path('api/users/<int:user_id>/assign-permission/', views.assign_user_permission, name='assign_user_permission'),
    
    # API 路由 - 上传记录管理
    path('api/upload-logs/<int:log_id>/delete/', views.delete_upload_log, name='delete_upload_log'),
    path('api/upload-logs/<int:log_id>/', views.get_upload_log_detail, name='get_upload_log_detail'),
    
    # API 路由 - 下载记录管理
    path('api/data-models/<int:model_id>/download/', views.download_data_model, name='download_data_model'),
    path('api/download-logs/<int:log_id>/', views.get_download_log_detail, name='get_download_log_detail'),
    
    # 测试路由
    path('test-images/', views.test_images_view, name='test_images'),
]