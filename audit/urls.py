from django.urls import path
from . import views

app_name = 'audit'

urlpatterns = [
    # 日志查看
    path('operation-logs/', views.operation_logs, name='operation_logs'),
    path('system-logs/', views.system_logs, name='system_logs'),
    path('access-logs/', views.access_logs, name='access_logs'),
    
    # 日志导出
    path('export-logs/', views.export_logs, name='export_logs'),
    
    # 日志统计
    path('log-statistics/', views.log_statistics, name='log_statistics'),
]
