from django.urls import path
from . import views

app_name = 'videos'

urlpatterns = [
    # 仪表盘
    path('', views.dashboard, name='dashboard'),
    
    # 视频列表和详情
    path('list/', views.video_list, name='video_list'),
    path('<int:video_id>/', views.video_detail, name='video_detail'),
    path('<int:video_id>/download/', views.video_download, name='video_download'),
    
    # 视频上传和编辑
    path('upload/', views.video_upload, name='video_upload'),
    path('<int:video_id>/edit/', views.video_edit, name='video_edit'),
    path('<int:video_id>/delete/', views.video_delete, name='video_delete'),
    
    # 交互功能
    path('<int:video_id>/toggle-favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('<int:video_id>/add-comment/', views.add_comment, name='add_comment'),
]
