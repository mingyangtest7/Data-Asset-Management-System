from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.conf import settings
import json
import os
from datetime import datetime, timedelta

from .models import User, PermissionGroup, UserPermission, LocationTag, ProjectTag, DataModel, UploadLog, DownloadLog


def check_permission(user, permission_name):
    """检查用户是否有特定权限"""
    try:
        user_permission = UserPermission.objects.get(user=user)
        permission_group = user_permission.permission_group
        
        if permission_name == 'dashboard':
            return permission_group.can_view_dashboard
        elif permission_name == 'my_data':
            return permission_group.can_view_my_data
        elif permission_name == 'data_management':
            return permission_group.can_view_data_management
        elif permission_name == 'system_settings':
            return permission_group.can_view_system_settings
    except UserPermission.DoesNotExist:
        return False
    return False


def login_view(request):
    """登录页面视图"""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if not username or not password:
            messages.error(request, '请输入用户名和密码')
            return render(request, 'login.html')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'欢迎回来，{user.username}！')
            return redirect('accounts:dashboard')
        else:
            messages.error(request, '用户名或密码错误')
    
    return render(request, 'login.html')


@login_required
def main_view(request):
    """主页面视图（重定向到仪表盘）"""
    return redirect('accounts:dashboard')


@login_required
def dashboard_view(request):
    """仪表盘视图"""
    if not check_permission(request.user, 'dashboard'):
        messages.error(request, '您没有访问数据统计的权限')
        return redirect('accounts:login')
    
    # 获取当前用户的统计数据
    user_total_uploads = UploadLog.objects.filter(user=request.user, status='success').count()
    user_total_downloads = DownloadLog.objects.filter(user=request.user, status='success').count()
    
    # 获取最近7天的用户数据
    seven_days_ago = timezone.now() - timedelta(days=7)
    user_recent_uploads = UploadLog.objects.filter(
        user=request.user,
        upload_time__gte=seven_days_ago, 
        status='success'
    ).count()
    user_recent_downloads = DownloadLog.objects.filter(
        user=request.user,
        download_time__gte=seven_days_ago, 
        status='success'
    ).count()
    
    # 获取当前用户的上传记录（用于本月数据展示）
    user_uploads = UploadLog.objects.filter(user=request.user, status='success').order_by('-upload_time')[:5]
    
    # 获取当前用户的下载记录（用于本月数据展示）
    user_downloads = DownloadLog.objects.filter(user=request.user, status='success').order_by('-download_time')[:5]
    
    # 获取最近30天的数据用于折线图
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    # 生成最近30天的日期列表
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
            user=request.user,
            upload_time__gte=day_start,
            upload_time__lt=day_end,
            status='success'
        ).count()
        
        download_count = DownloadLog.objects.filter(
            user=request.user,
            download_time__gte=day_start,
            download_time__lt=day_end,
            status='success'
        ).count()
        
        upload_counts.append(upload_count)
        download_counts.append(download_count)
    
    context = {
        'user': request.user,
        'total_uploads': user_total_uploads,
        'total_downloads': user_total_downloads,
        'recent_uploads': user_recent_uploads,
        'recent_downloads': user_recent_downloads,
        'user_uploads': user_uploads,
        'user_downloads': user_downloads,
        'chart_data': json.dumps({
            'dates': dates,
            'upload_counts': upload_counts,
            'download_counts': download_counts,
        })
    }
    return render(request, 'dashboard.html', context)


@login_required
def my_data_view(request):
    """我的数据视图"""
    if not check_permission(request.user, 'my_data'):
        messages.error(request, '您没有访问我的数据的权限')
        return redirect('accounts:login')
    
    # 获取用户的上传记录（UploadLog）
    user_uploads = UploadLog.objects.filter(user=request.user).order_by('-upload_time')
    
    # 获取用户的下载记录（DownloadLog）
    user_downloads = DownloadLog.objects.filter(user=request.user).order_by('-download_time')
    
    # 上传记录分页
    upload_paginator = Paginator(user_uploads, 10)
    upload_page_number = request.GET.get('upload_page', 1)
    upload_page_obj = upload_paginator.get_page(upload_page_number)
    
    # 下载记录分页
    download_paginator = Paginator(user_downloads, 10)
    download_page_number = request.GET.get('download_page', 1)
    download_page_obj = download_paginator.get_page(download_page_number)
    
    context = {
        'user': request.user,
        'user_uploads': upload_page_obj,
        'user_downloads': download_page_obj,
        'total_uploads': user_uploads.count(),
        'total_downloads': user_downloads.count(),
    }
    return render(request, 'my_data.html', context)


@login_required
def data_management_view(request):
    """数据管理视图"""
    if not check_permission(request.user, 'data_management'):
        messages.error(request, '您没有访问数据管理的权限')
        return redirect('accounts:login')
    
    # 获取所有数据模型
    models = DataModel.objects.all().order_by('-created_at')
    
    # 获取查询参数
    source = request.GET.get('source', '')
    project_tag = request.GET.get('project_tag', '')
    model_name = request.GET.get('model_name', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    # 应用筛选条件
    if source:
        models = models.filter(source=source)
    
    if project_tag:
        models = models.filter(project_tag_id=project_tag)
    
    if model_name:
        models = models.filter(name__icontains=model_name)
    
    if start_date:
        try:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            models = models.filter(created_at__gte=start_datetime)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
            # 添加一天的时间以包含结束日期的整天
            end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
            models = models.filter(created_at__lte=end_datetime)
        except ValueError:
            pass
    
    # 分页
    paginator = Paginator(models, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 获取标签数据
    location_tags = LocationTag.objects.all()
    project_tags = ProjectTag.objects.all()
    
    context = {
        'user': request.user,
        'models': page_obj,
        'location_tags': location_tags,
        'project_tags': project_tags,
        'current_source': source,
        'current_project_tag': project_tag,
        'current_model_name': model_name,
        'current_start_date': start_date,
        'current_end_date': end_date,
    }
    return render(request, 'data_management.html', context)


@login_required
def system_settings_view(request):
    """系统设置视图"""
    if not check_permission(request.user, 'system_settings'):
        messages.error(request, '您没有访问系统设置的权限')
        return redirect('accounts:login')
    
    # 获取用户列表
    users = User.objects.all().order_by('-created_at')
    
    # 获取权限组列表
    permission_groups = PermissionGroup.objects.all().order_by('-created_at')
    
    # 分页
    user_paginator = Paginator(users, 10)
    user_page_number = request.GET.get('user_page')
    user_page_obj = user_paginator.get_page(user_page_number)
    
    context = {
        'user': request.user,
        'users': user_page_obj,
        'permission_groups': permission_groups,
    }
    return render(request, 'system_settings.html', context)


@login_required
def logout_view(request):
    """退出登录视图"""
    logout(request)
    messages.info(request, '您已成功退出登录')
    return redirect('accounts:login')


def test_data_management_view(request):
    """测试数据管理功能"""
    return render(request, 'test_data_management.html')


def register_view(request):
    """注册页面视图"""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        email = request.POST.get('email', '')
        display_name = request.POST.get('display_name', username)

        if not username or not password:
            messages.error(request, '请输入用户名和密码')
            return render(request, 'register.html')

        if password != confirm_password:
            messages.error(request, '两次输入的密码不一致')
            return render(request, 'register.html')

        # 检查用户名是否已存在
        if User.objects.filter(username=username).exists():
            messages.error(request, '用户名已存在')
            return render(request, 'register.html')

        try:
            # 创建新用户
            new_user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                display_name=display_name
            )
            
            # 默认分配普通用户权限
            try:
                default_permission = PermissionGroup.objects.get(name='普通用户')
                UserPermission.objects.create(user=new_user, permission_group=default_permission)
            except PermissionGroup.DoesNotExist:
                pass
            
            messages.success(request, '注册成功，请登录')
            return redirect('accounts:login')
        except Exception as e:
            messages.error(request, f'注册失败：{str(e)}')

    return render(request, 'register.html')


@login_required
def person_view(request):
    """个人中心视图"""
    context = {
        'user': request.user,
    }
    return render(request, 'person.html', context)


# API 视图 - 权限管理
@login_required
@require_http_methods(["POST"])
def create_permission_group(request):
    """创建权限组"""
    if not check_permission(request.user, 'system_settings'):
        return JsonResponse({'success': False, 'message': '权限不足'})
    
    try:
        data = json.loads(request.body)
        name = data.get('name')
        description = data.get('description', '')
        
        if not name:
            return JsonResponse({'success': False, 'message': '权限名称不能为空'})
        
        if PermissionGroup.objects.filter(name=name).exists():
            return JsonResponse({'success': False, 'message': '权限名称已存在'})
        
        permission_group = PermissionGroup.objects.create(
            name=name,
            description=description,
            can_view_dashboard=data.get('can_view_dashboard', False),
            can_view_my_data=data.get('can_view_my_data', False),
            can_view_data_management=data.get('can_view_data_management', False),
            can_view_system_settings=data.get('can_view_system_settings', False),
        )
        
        return JsonResponse({
            'success': True, 
            'message': '权限组创建成功',
            'data': {
                'id': permission_group.id,
                'name': permission_group.name,
                'description': permission_group.description,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'创建失败：{str(e)}'})


@login_required
@require_http_methods(["POST"])
def update_permission_group(request, group_id):
    """更新权限组"""
    if not check_permission(request.user, 'system_settings'):
        return JsonResponse({'success': False, 'message': '权限不足'})
    
    try:
        permission_group = get_object_or_404(PermissionGroup, id=group_id)
        data = json.loads(request.body)
        
        permission_group.name = data.get('name', permission_group.name)
        permission_group.description = data.get('description', permission_group.description)
        permission_group.can_view_dashboard = data.get('can_view_dashboard', permission_group.can_view_dashboard)
        permission_group.can_view_my_data = data.get('can_view_my_data', permission_group.can_view_my_data)
        permission_group.can_view_data_management = data.get('can_view_data_management', permission_group.can_view_data_management)
        permission_group.can_view_system_settings = data.get('can_view_system_settings', permission_group.can_view_system_settings)
        
        permission_group.save()
        
        return JsonResponse({
            'success': True, 
            'message': '权限组更新成功',
            'data': {
                'id': permission_group.id,
                'name': permission_group.name,
                'description': permission_group.description,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'更新失败：{str(e)}'})


@login_required
@require_http_methods(["POST"])
def delete_permission_group(request, group_id):
    """删除权限组"""
    if not check_permission(request.user, 'system_settings'):
        return JsonResponse({'success': False, 'message': '权限不足'})
    
    try:
        permission_group = get_object_or_404(PermissionGroup, id=group_id)
        permission_group.delete()
        
        return JsonResponse({'success': True, 'message': '权限组删除成功'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'删除失败：{str(e)}'})


# API 视图 - 标签管理
@login_required
@require_http_methods(["POST"])
def create_location_tag(request):
    """创建地理位置标签"""
    if not check_permission(request.user, 'data_management'):
        return JsonResponse({'success': False, 'message': '权限不足'})
    
    try:
        data = json.loads(request.body)
        name = data.get('name')
        
        if not name:
            return JsonResponse({'success': False, 'message': '标签名称不能为空'})
        
        if LocationTag.objects.filter(name=name).exists():
            return JsonResponse({'success': False, 'message': '标签名称已存在'})
        
        location_tag = LocationTag.objects.create(name=name)
        
        return JsonResponse({
            'success': True, 
            'message': '地理位置标签创建成功',
            'data': {'id': location_tag.id, 'name': location_tag.name}
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'创建失败：{str(e)}'})


@login_required
@require_http_methods(["POST"])
def create_project_tag(request):
    """创建项目归属标签"""
    if not check_permission(request.user, 'data_management'):
        return JsonResponse({'success': False, 'message': '权限不足'})
    
    try:
        data = json.loads(request.body)
        name = data.get('name')
        
        if not name:
            return JsonResponse({'success': False, 'message': '标签名称不能为空'})
        
        if ProjectTag.objects.filter(name=name).exists():
            return JsonResponse({'success': False, 'message': '标签名称已存在'})
        
        project_tag = ProjectTag.objects.create(name=name)
        
        return JsonResponse({
            'success': True, 
            'message': '项目归属标签创建成功',
            'data': {'id': project_tag.id, 'name': project_tag.name}
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'创建失败：{str(e)}'})


@login_required
@require_http_methods(["POST"])
def delete_location_tag(request, tag_id):
    """删除地理位置标签"""
    if not check_permission(request.user, 'data_management'):
        return JsonResponse({'success': False, 'message': '权限不足'})
    
    try:
        location_tag = get_object_or_404(LocationTag, id=tag_id)
        location_tag.delete()
        
        return JsonResponse({'success': True, 'message': '地理位置标签删除成功'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'删除失败：{str(e)}'})


@login_required
@require_http_methods(["POST"])
def delete_project_tag(request, tag_id):
    """删除项目归属标签"""
    if not check_permission(request.user, 'data_management'):
        return JsonResponse({'success': False, 'message': '权限不足'})
    
    try:
        project_tag = get_object_or_404(ProjectTag, id=tag_id)
        project_tag.delete()
        
        return JsonResponse({'success': True, 'message': '项目归属标签删除成功'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'删除失败：{str(e)}'})


# API 视图 - 数据模型管理
@login_required
@require_http_methods(["POST"])
def upload_data_model(request):
    """上传数据模型"""
    if not check_permission(request.user, 'data_management'):
        return JsonResponse({'success': False, 'message': '权限不足'})
    
    try:
        name = request.POST.get('name')
        source = request.POST.get('source')
        project_tag_id = request.POST.get('project_tag')
        location_tag_id = request.POST.get('location_tag')
        infringement_risk = request.POST.get('infringement_risk')
        model_level = request.POST.get('model_level')
        description = request.POST.get('description', '')
        
        if not name:
            return JsonResponse({'success': False, 'message': '模型名称不能为空'})
        
        # 获取标签
        project_tag = None
        location_tag = None
        
        if project_tag_id:
            project_tag = get_object_or_404(ProjectTag, id=project_tag_id)
        if location_tag_id:
            location_tag = get_object_or_404(LocationTag, id=location_tag_id)
        
        # 处理文件上传
        media_files = request.FILES.getlist('media_files')
        
        if not media_files:
            return JsonResponse({'success': False, 'message': '请上传图片或视频文件'})
        
        # 创建数据模型
        data_model = DataModel.objects.create(
            name=name,
            source=source,
            project_tag=project_tag,
            location_tag=location_tag,
            infringement_risk=infringement_risk,
            model_level=model_level,
            description=description,
            created_by=request.user
        )
        
        # 保存媒体文件信息
        media_file_info = []
        for media_file in media_files:
            # 保存媒体文件到media目录
            import os
            from django.conf import settings
            
            media_dir = os.path.join(settings.MEDIA_ROOT, 'media_files')
            os.makedirs(media_dir, exist_ok=True)
            
            file_path = os.path.join(media_dir, media_file.name)
            with open(file_path, 'wb') as f:
                for chunk in media_file.chunks():
                    f.write(chunk)
            
            media_file_info.append({
                'name': media_file.name,
                'size': media_file.size,
                'path': f'media_files/{media_file.name}'
            })
        
        data_model.media_files = media_file_info
        data_model.save()
        
        # 记录上传日志
        UploadLog.objects.create(
            user=request.user,
            filename=name,
            file_size=sum(file.size for file in media_files),
            status='success',
            source_model=data_model
        )
        
        return JsonResponse({
            'success': True, 
            'message': '图片/视频上传成功',
            'data': {'id': data_model.id, 'name': data_model.name}
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'上传失败：{str(e)}'})


@login_required
@require_http_methods(["POST"])
def update_data_model(request, model_id):
    """更新数据模型"""
    if not check_permission(request.user, 'data_management'):
        return JsonResponse({'success': False, 'message': '权限不足'})
    
    try:
        data_model = get_object_or_404(DataModel, id=model_id)
        
        # 检查权限：只有创建者或管理员可以更新
        if data_model.created_by != request.user and not request.user.is_superuser:
            return JsonResponse({'success': False, 'message': '权限不足'})
        
        # 更新基本信息
        if 'name' in request.POST:
            data_model.name = request.POST['name']
        if 'source' in request.POST:
            data_model.source = request.POST['source']
        if 'infringement_risk' in request.POST:
            data_model.infringement_risk = request.POST['infringement_risk']
        if 'model_level' in request.POST:
            data_model.model_level = request.POST['model_level']
        if 'description' in request.POST:
            data_model.description = request.POST['description']
        
        # 更新关联标签
        if 'project_tag' in request.POST and request.POST['project_tag']:
            try:
                project_tag = ProjectTag.objects.get(id=request.POST['project_tag'])
                data_model.project_tag = project_tag
            except ProjectTag.DoesNotExist:
                pass
        
        if 'location_tag' in request.POST and request.POST['location_tag']:
            try:
                location_tag = LocationTag.objects.get(id=request.POST['location_tag'])
                data_model.location_tag = location_tag
            except LocationTag.DoesNotExist:
                pass
        
        # 处理文件上传
        print(f"DEBUG: Files in request: {list(request.FILES.keys())}")
        
        if 'model_file' in request.FILES:
            data_model.model_file = request.FILES['model_file']
            print(f"DEBUG: Model file uploaded: {request.FILES['model_file'].name}")
        
        if 'media_file' in request.FILES:
            print(f"DEBUG: Media file uploaded: {request.FILES['media_file'].name}")
            # 处理媒体文件上传
            media_file = request.FILES['media_file']
            media_info = {
                'name': media_file.name,
                'size': media_file.size,
                'path': f'media_files/{media_file.name}',
                'upload_time': timezone.now().isoformat()
            }
            
            # 保存文件
            import os
            from django.core.files.storage import default_storage
            
            file_path = default_storage.save(f'media_files/{media_file.name}', media_file)
            media_info['path'] = file_path
            
            # 替换媒体文件列表（而不是追加）
            data_model.media_files = [media_info]
        
        data_model.save()
        
        return JsonResponse({
            'success': True,
            'message': '数据模型更新成功'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'更新失败：{str(e)}'})


@login_required
@require_http_methods(["POST"])
def delete_data_model(request, model_id):
    """删除数据模型"""
    if not check_permission(request.user, 'data_management'):
        return JsonResponse({'success': False, 'message': '权限不足'})
    
    try:
        data_model = get_object_or_404(DataModel, id=model_id)
        
        # 检查权限：只有创建者或管理员可以删除
        if data_model.created_by != request.user and not request.user.is_superuser:
            return JsonResponse({'success': False, 'message': '权限不足'})
        
        data_model.delete()
        
        return JsonResponse({'success': True, 'message': '数据模型删除成功'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'删除失败：{str(e)}'})


# API 视图 - 用户管理
@login_required
@require_http_methods(["POST"])
def toggle_user_status(request, user_id):
    """切换用户状态"""
    if not check_permission(request.user, 'system_settings'):
        return JsonResponse({'success': False, 'message': '权限不足'})
    
    try:
        user = get_object_or_404(User, id=user_id)
        user.is_active = not user.is_active
        user.save()
        
        status = '启用' if user.is_active else '禁用'
        return JsonResponse({
            'success': True, 
            'message': f'用户{status}成功',
            'data': {'is_active': user.is_active}
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'操作失败：{str(e)}'})


@login_required
@require_http_methods(["POST"])
def assign_user_permission(request, user_id):
    """分配用户权限"""
    if not check_permission(request.user, 'system_settings'):
        return JsonResponse({'success': False, 'message': '权限不足'})
    
    try:
        user = get_object_or_404(User, id=user_id)
        data = json.loads(request.body)
        permission_group_id = data.get('permission_group_id')
        
        if not permission_group_id:
            return JsonResponse({'success': False, 'message': '请选择权限组'})
        
        permission_group = get_object_or_404(PermissionGroup, id=permission_group_id)
        
        # 更新或创建用户权限
        user_permission, created = UserPermission.objects.get_or_create(
            user=user,
            defaults={'permission_group': permission_group}
        )
        
        if not created:
            user_permission.permission_group = permission_group
            user_permission.save()
        
        return JsonResponse({
            'success': True, 
            'message': '用户权限分配成功',
            'data': {'permission_group': permission_group.name}
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'分配失败：{str(e)}'})


# 个人设置中心视图
@login_required
def person_view(request):
    """个人设置中心"""
    user = request.user

    if request.method == 'POST':
        # 处理表单数据
        new_username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        display_name = request.POST.get('display_name')

        # 更新用户信息
        if new_username:
            user.username = new_username
        if email:
            user.email = email
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        if display_name:
            user.display_name = display_name

        try:
            user.save()
            messages.success(request, '个人信息更新成功！')
        except Exception as e:
            messages.error(request, f'更新失败：{str(e)}')

    return render(request, 'person.html', {
        'user': user,
    })


@login_required
@require_http_methods(["GET"])
def get_data_model(request, model_id):
    """获取单个数据模型详情"""
    if not check_permission(request.user, 'data_management'):
        return JsonResponse({'success': False, 'message': '权限不足'})
    
    try:
        model = get_object_or_404(DataModel, id=model_id)
        
        # 构建模型数据
        model_data = {
            'id': model.id,
            'name': model.name,
            'source': model.source,
            'infringement_risk': model.infringement_risk,
            'model_level': model.model_level,
            'description': model.description,
            'media_files': model.media_files,
            'created_at': model.created_at.isoformat(),
            'created_by': {
                'username': model.created_by.username,
                'display_name': getattr(model.created_by, 'display_name', model.created_by.username)
            },
            'project_tag': {
                'id': model.project_tag.id,
                'name': model.project_tag.name
            } if model.project_tag else None,
            'location_tag': {
                'id': model.location_tag.id,
                'name': model.location_tag.name
            } if model.location_tag else None,
        }
        
        return JsonResponse({
            'success': True,
            'model': model_data
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'获取失败：{str(e)}'})


def test_images_view(request):
    """测试图片显示"""
    models = DataModel.objects.all()
    return render(request, 'test_images.html', {'models': models})


@require_http_methods(["POST"])
def delete_upload_log(request, log_id):
    """删除上传记录（只删除记录，不删除数据）"""
    try:
        upload_log = get_object_or_404(UploadLog, id=log_id, user=request.user)
        upload_log.delete()
        
        return JsonResponse({
            'success': True,
            'message': '上传记录删除成功'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'删除失败：{str(e)}'})


@require_http_methods(["GET"])
def get_upload_log_detail(request, log_id):
    """获取上传记录详情"""
    try:
        upload_log = get_object_or_404(UploadLog, id=log_id, user=request.user)
        
        log_data = {
            'id': upload_log.id,
            'filename': upload_log.filename,
            'file_size': upload_log.file_size,
            'upload_time': upload_log.upload_time.isoformat(),
            'status': upload_log.status,
            'related_model': None
        }
        
        # 如果有关联的模型，添加模型信息
        if upload_log.source_model:
            model = upload_log.source_model
            model_data = {
                'id': model.id,
                'name': model.name,
                'source': model.source,
                'infringement_risk': model.infringement_risk,
                'model_level': model.model_level,
                'description': model.description,
                'created_at': model.created_at.isoformat(),
                'media_files': model.media_files,
                'project_tag': {
                    'id': model.project_tag.id,
                    'name': model.project_tag.name
                } if model.project_tag else None,
                'location_tag': {
                    'id': model.location_tag.id,
                    'name': model.location_tag.name
                } if model.location_tag else None,
                'created_by': {
                    'username': model.created_by.username,
                    'display_name': model.created_by.display_name
                } if model.created_by else None,
            }
            log_data['related_model'] = model_data
        
        return JsonResponse({
            'success': True,
            'data': log_data
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'获取失败：{str(e)}'})


@require_http_methods(["POST"])
def download_data_model(request, model_id):
    """下载数据模型并记录下载日志"""
    try:
        model = get_object_or_404(DataModel, id=model_id)
        
        # 创建下载记录
        if model.media_files:
            for media_file in model.media_files:
                DownloadLog.objects.create(
                    user=request.user,
                    filename=media_file['name'],
                    file_size=media_file['size'],
                    source_model=model,
                    download_source='data_management',
                    status='success'
                )
        
        # 返回文件下载信息
        download_info = []
        if model.media_files:
            for media_file in model.media_files:
                download_info.append({
                    'filename': media_file['name'],
                    'url': f'/media/{media_file["path"]}',
                    'size': media_file['size']
                })
        
        return JsonResponse({
            'success': True,
            'message': '下载记录已创建',
            'downloads': download_info
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'下载失败：{str(e)}'})


@require_http_methods(["GET"])
def get_download_log_detail(request, log_id):
    """获取下载记录详情"""
    try:
        download_log = get_object_or_404(DownloadLog, id=log_id, user=request.user)
        
        log_data = {
            'id': download_log.id,
            'filename': download_log.filename,
            'file_size': download_log.file_size,
            'download_time': download_log.download_time.isoformat(),
            'download_source': download_log.download_source,
            'status': download_log.status,
            'source_model': None
        }
        
        # 如果有关联的模型，添加模型信息
        if download_log.source_model:
            model = download_log.source_model
            model_data = {
                'id': model.id,
                'name': model.name,
                'source': model.source,
                'infringement_risk': model.infringement_risk,
                'model_level': model.model_level,
                'description': model.description,
                'created_at': model.created_at.isoformat(),
                'media_files': model.media_files,
                'project_tag': {
                    'id': model.project_tag.id,
                    'name': model.project_tag.name
                } if model.project_tag else None,
                'location_tag': {
                    'id': model.location_tag.id,
                    'name': model.location_tag.name
                } if model.location_tag else None,
                'created_by': {
                    'username': model.created_by.username,
                    'display_name': model.created_by.display_name
                } if model.created_by else None,
            }
            log_data['source_model'] = model_data
        
        return JsonResponse({
            'success': True,
            'data': log_data
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'获取失败：{str(e)}'})


@require_http_methods(["POST"])
def update_data_model(request, model_id):
    """更新数据模型"""
    try:
        model = get_object_or_404(DataModel, id=model_id)
        
        # 更新模型信息
        model.name = request.POST.get('name', model.name)
        model.description = request.POST.get('description', model.description)
        model.source = request.POST.get('source', model.source)
        model.infringement_risk = request.POST.get('infringement_risk', model.infringement_risk)
        model.model_level = request.POST.get('model_level', model.model_level)
        
        # 更新项目归属
        project_tag_id = request.POST.get('project_tag')
        if project_tag_id:
            try:
                model.project_tag = ProjectTag.objects.get(id=project_tag_id)
            except ProjectTag.DoesNotExist:
                model.project_tag = None
        else:
            model.project_tag = None
        
        # 更新地理位置
        location_tag_id = request.POST.get('location_tag')
        if location_tag_id:
            try:
                model.location_tag = LocationTag.objects.get(id=location_tag_id)
            except LocationTag.DoesNotExist:
                model.location_tag = None
        else:
            model.location_tag = None
        
        model.save()
        
        return JsonResponse({
            'success': True,
            'message': '更新成功'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'更新失败：{str(e)}'})


@login_required
@require_http_methods(["GET"])
def get_model_detail(request, model_id):
    """获取模型详情用于预览弹窗"""
    if not check_permission(request.user, 'data_management'):
        return JsonResponse({'success': False, 'message': '您没有访问数据管理的权限'})
    
    try:
        model = get_object_or_404(DataModel, id=model_id)
        
        model_data = {
            'id': model.id,
            'name': model.name,
            'source': model.source,
            'infringement_risk': model.infringement_risk,
            'model_level': model.model_level,
            'description': model.description,
            'created_at': model.created_at.isoformat(),
            'updated_at': model.updated_at.isoformat(),
            'media_files': model.media_files,
            'model_file': model.model_file.url if model.model_file else None,
            'project_tag': {
                'id': model.project_tag.id,
                'name': model.project_tag.name
            } if model.project_tag else None,
            'location_tag': {
                'id': model.location_tag.id,
                'name': model.location_tag.name
            } if model.location_tag else None,
            'created_by': {
                'id': model.created_by.id,
                'username': model.created_by.username,
                'display_name': model.created_by.display_name
            } if model.created_by else None,
        }
        
        return JsonResponse({
            'success': True,
            'model': model_data
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'获取模型详情失败：{str(e)}'})


@login_required
@require_http_methods(["POST"])
def update_model(request, model_id):
    """更新模型信息"""
    if not check_permission(request.user, 'data_management'):
        return JsonResponse({'success': False, 'message': '您没有访问数据管理的权限'})
    
    try:
        model = get_object_or_404(DataModel, id=model_id)
        
        # 更新基本信息
        if 'name' in request.POST:
            model.name = request.POST['name']
        if 'source' in request.POST:
            model.source = request.POST['source']
        if 'infringement_risk' in request.POST:
            model.infringement_risk = request.POST['infringement_risk']
        if 'model_level' in request.POST:
            model.model_level = request.POST['model_level']
        if 'description' in request.POST:
            model.description = request.POST['description']
        
        # 更新关联标签
        if 'project_tag' in request.POST and request.POST['project_tag']:
            try:
                project_tag = ProjectTag.objects.get(id=request.POST['project_tag'])
                model.project_tag = project_tag
            except ProjectTag.DoesNotExist:
                pass
        
        if 'location_tag' in request.POST and request.POST['location_tag']:
            try:
                location_tag = LocationTag.objects.get(id=request.POST['location_tag'])
                model.location_tag = location_tag
            except LocationTag.DoesNotExist:
                pass
        
        # 处理文件上传
        print(f"DEBUG: Files in request: {list(request.FILES.keys())}")
        
        if 'model_file' in request.FILES:
            model.model_file = request.FILES['model_file']
            print(f"DEBUG: Model file uploaded: {request.FILES['model_file'].name}")
        
        if 'media_file' in request.FILES:
            print(f"DEBUG: Media file uploaded: {request.FILES['media_file'].name}")
            # 处理媒体文件上传
            media_file = request.FILES['media_file']
            media_info = {
                'name': media_file.name,
                'size': media_file.size,
                'path': f'media_files/{media_file.name}',
                'upload_time': timezone.now().isoformat()
            }
            
            # 保存文件
            import os
            from django.core.files.storage import default_storage
            
            file_path = default_storage.save(f'media_files/{media_file.name}', media_file)
            media_info['path'] = file_path
            
            # 替换媒体文件列表（而不是追加）
            model.media_files = [media_info]
        
        model.save()
        
        return JsonResponse({
            'success': True,
            'message': '模型更新成功'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'更新模型失败：{str(e)}'})


@login_required
@require_http_methods(["POST"])
def delete_model(request, model_id):
    """删除模型"""
    if not check_permission(request.user, 'data_management'):
        return JsonResponse({'success': False, 'message': '您没有访问数据管理的权限'})
    
    try:
        model = get_object_or_404(DataModel, id=model_id)
        
        # 删除关联的文件
        if model.model_file:
            model.model_file.delete()
        
        if model.media_files:
            for media_file in model.media_files:
                try:
                    file_path = media_file.get('path')
                    if file_path and os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    print(f"删除文件失败: {e}")
        
        model.delete()
        
        return JsonResponse({
            'success': True,
            'message': '模型删除成功'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'删除模型失败：{str(e)}'})