# 测试上传功能脚本
import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from accounts.models import DataModel, UploadLog, User, LocationTag, ProjectTag

def test_upload_functionality():
    """测试上传功能"""
    
    print("=== 测试上传功能 ===")
    
    # 1. 检查数据模型
    total_models = DataModel.objects.count()
    print(f"当前数据模型总数: {total_models}")
    
    # 2. 检查上传日志
    total_uploads = UploadLog.objects.count()
    print(f"当前上传日志总数: {total_uploads}")
    
    # 3. 检查标签
    location_tags = LocationTag.objects.count()
    project_tags = ProjectTag.objects.count()
    print(f"地理位置标签数量: {location_tags}")
    print(f"项目归属标签数量: {project_tags}")
    
    # 4. 检查用户
    users = User.objects.count()
    print(f"用户总数: {users}")
    
    # 5. 显示最新的数据模型
    latest_models = DataModel.objects.order_by('-created_at')[:3]
    print("\n最新的数据模型:")
    for model in latest_models:
        print(f"- {model.name} (创建时间: {model.created_at})")
    
    # 6. 显示最新的上传日志
    latest_uploads = UploadLog.objects.order_by('-upload_time')[:3]
    print("\n最新的上传日志:")
    for upload in latest_uploads:
        print(f"- {upload.filename} (上传时间: {upload.upload_time})")
    
    print("\n=== 测试完成 ===")

if __name__ == '__main__':
    test_upload_functionality()

