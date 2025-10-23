from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, Http404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import View
import os
import hashlib
import mimetypes
from .models import Video, Category, VideoComment, VideoFavorite
from permissions.decorators import permission_required, security_level_required
from audit.models import OperationLog
import json
import logging

logger = logging.getLogger('videos')


@login_required
def dashboard(request):
    """仪表盘视图"""
    try:
        user_profile = request.user.userprofile
        max_level = user_profile.max_security_level
    except AttributeError:
        max_level = 1
    
    # 获取用户可访问的视频
    videos = Video.objects.filter(
        is_active=True,
        security_level__lte=max_level
    )
    
    # 统计数据
    total_videos = videos.count()
    total_size = videos.aggregate(total=Sum('file_size'))['total'] or 0
    total_downloads = videos.aggregate(total=Sum('download_count'))['total'] or 0
    total_views = videos.aggregate(total=Sum('view_count'))['total'] or 0
    
    # 按分类统计
    category_stats = videos.values('category__name').annotate(
        count=Count('id'),
        total_size=Sum('file_size')
    ).order_by('-count')
    
    # 按安全级别统计
    security_stats = videos.values('security_level').annotate(
        count=Count('id')
    ).order_by('security_level')
    
    # 按文件类型统计
    type_stats = videos.values('file_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # 最近的视频
    recent_videos = videos.order_by('-uploaded_at')[:10]
    
    # 热门视频
    popular_videos = videos.order_by('-download_count')[:10]
    
    context = {
        'total_videos': total_videos,
        'total_size': round(total_size / (1024 * 1024 * 1024), 2),  # GB
        'total_downloads': total_downloads,
        'total_views': total_views,
        'category_stats': category_stats,
        'security_stats': security_stats,
        'type_stats': type_stats,
        'recent_videos': recent_videos,
        'popular_videos': popular_videos,
        'security_levels': settings.SECURITY_LEVELS,
    }
    
    return render(request, 'videos/dashboard.html', context)


@login_required
@permission_required('video:view')
def video_list(request):
    """视频列表"""
    try:
        user_profile = request.user.userprofile
        max_level = user_profile.max_security_level
    except AttributeError:
        max_level = 1
    
    videos = Video.objects.filter(
        is_active=True,
        security_level__lte=max_level
    ).select_related('category', 'uploader').order_by('-uploaded_at')
    
    # 搜索功能
    search = request.GET.get('search', '')
    if search:
        videos = videos.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(tags__icontains=search)
        )
    
    # 筛选功能
    category_id = request.GET.get('category')
    if category_id:
        videos = videos.filter(category_id=category_id)
    
    security_level = request.GET.get('security_level')
    if security_level:
        videos = videos.filter(security_level=int(security_level))
    
    file_type = request.GET.get('file_type')
    if file_type:
        videos = videos.filter(file_type=file_type)
    
    # 排序
    sort_by = request.GET.get('sort', '-uploaded_at')
    if sort_by in ['title', '-title', 'uploaded_at', '-uploaded_at', 'download_count', '-download_count', 'view_count', '-view_count']:
        videos = videos.order_by(sort_by)
    
    # 分页
    paginator = Paginator(videos, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 获取筛选选项
    categories = Category.objects.filter(is_active=True)
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'search': search,
        'category_id': category_id,
        'security_level': security_level,
        'file_type': file_type,
        'sort_by': sort_by,
        'security_levels': settings.SECURITY_LEVELS,
        'file_types': Video.FILE_TYPE_CHOICES,
    }
    
    return render(request, 'videos/video_list.html', context)


@login_required
@permission_required('video:view')
def video_detail(request, video_id):
    """视频详情"""
    video = get_object_or_404(Video, id=video_id, is_active=True)
    
    # 检查权限
    if not video.can_user_access(request.user):
        messages.error(request, '您没有权限访问此视频')
        return redirect('videos:video_list')
    
    # 增加观看次数
    video.increment_view_count()
    
    # 记录观看日志
    OperationLog.objects.create(
        user=request.user,
        operation_type='view',
        result='success',
        content_object=video,
        description=f'观看视频: {video.title}',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT'),
        security_level=video.security_level
    )
    
    # 获取评论
    comments = video.comments.filter(is_active=True).order_by('-created_at')
    
    # 检查是否已收藏
    is_favorited = False
    try:
        VideoFavorite.objects.get(video=video, user=request.user)
        is_favorited = True
    except VideoFavorite.DoesNotExist:
        pass
    
    context = {
        'video': video,
        'comments': comments,
        'is_favorited': is_favorited,
    }
    
    return render(request, 'videos/video_detail.html', context)


@login_required
@permission_required('video:download')
def video_download(request, video_id):
    """视频下载"""
    video = get_object_or_404(Video, id=video_id, is_active=True)
    
    # 检查权限
    if not video.can_user_access(request.user):
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({'error': '您没有权限下载此视频'}, status=403)
        messages.error(request, '您没有权限下载此视频')
        return redirect('videos:video_list')
    
    try:
        # 增加下载次数
        video.increment_download_count()
        
        # 记录下载日志
        OperationLog.objects.create(
            user=request.user,
            operation_type='download',
            result='success',
            content_object=video,
            description=f'下载视频: {video.title}',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            security_level=video.security_level
        )
        
        # 返回文件
        file_path = video.file.path
        if not os.path.exists(file_path):
            raise Http404("文件不存在")
        
        # 设置响应头
        response = HttpResponse()
        response['Content-Type'] = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
        response['Content-Disposition'] = f'attachment; filename="{video.title}.{video.file_extension}"'
        response['Content-Length'] = video.file_size
        
        # 读取文件内容
        with open(file_path, 'rb') as f:
            response.write(f.read())
        
        return response
        
    except Exception as e:
        logger.error(f'下载视频失败: {str(e)}')
        
        # 记录失败日志
        OperationLog.objects.create(
            user=request.user,
            operation_type='download',
            result='failed',
            content_object=video,
            description=f'下载视频失败: {video.title}',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            security_level=video.security_level,
            extra_data={'error': str(e)}
        )
        
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({'error': '下载失败'}, status=500)
        messages.error(request, '下载失败')
        return redirect('videos:video_detail', video_id=video_id)


@login_required
@permission_required('video:upload')
def video_upload(request):
    """视频上传"""
    if request.method == 'POST':
        try:
            # 获取表单数据
            title = request.POST.get('title')
            description = request.POST.get('description', '')
            tags = request.POST.get('tags', '')
            category_id = request.POST.get('category')
            security_level = int(request.POST.get('security_level', 1))
            file = request.FILES.get('file')
            
            logger.info(f'开始上传文件: {file.name if file else "无文件"}, 大小: {file.size if file else 0}')
            
            if not title or not file:
                logger.error('标题或文件为空')
                messages.error(request, '标题和文件不能为空')
                return render(request, 'videos/video_upload.html')
            
            # 检查文件大小
            if file.size > settings.MAX_FILE_SIZE:
                logger.error(f'文件过大: {file.size} > {settings.MAX_FILE_SIZE}')
                messages.error(request, f'文件大小不能超过5GB，当前文件大小: {round(file.size / (1024*1024*1024), 2)}GB')
                return render(request, 'videos/video_upload.html')
            
            # 检查文件类型
            file_extension = file.name.split('.')[-1].lower()
            logger.info(f'文件扩展名: {file_extension}')
            
            if file_extension in settings.ALLOWED_VIDEO_EXTENSIONS:
                file_type = 'video'
            elif file_extension in settings.ALLOWED_IMAGE_EXTENSIONS:
                file_type = 'image'
            elif file_extension in settings.ALLOWED_MODEL_EXTENSIONS:
                file_type = 'model'
            else:
                logger.error(f'不支持的文件格式: {file_extension}')
                messages.error(request, f'不支持的文件格式: {file_extension}')
                return render(request, 'videos/video_upload.html')
            
            # 计算MD5（分块读取避免内存问题）
            file.seek(0)
            md5_hash = hashlib.md5()
            for chunk in file.chunks():
                md5_hash.update(chunk)
            md5_hash = md5_hash.hexdigest()
            file.seek(0)
            
            logger.info(f'文件MD5: {md5_hash}')
            
            # 检查是否已存在
            if Video.objects.filter(md5_hash=md5_hash).exists():
                logger.warning(f'文件已存在: {md5_hash}')
                messages.warning(request, '文件已存在，跳过上传')
                return redirect('videos:video_list')
            
            # 确保media目录存在
            media_dir = os.path.join(settings.MEDIA_ROOT, 'videos')
            os.makedirs(media_dir, exist_ok=True)
            
            # 创建视频记录
            video = Video.objects.create(
                title=title,
                description=description,
                tags=tags,
                file=file,
                file_type=file_type,
                file_size=file.size,
                file_extension=file_extension,
                md5_hash=md5_hash,
                category_id=category_id if category_id else None,
                security_level=security_level,
                uploader=request.user
            )
            
            logger.info(f'视频记录创建成功: {video.id}')
            
            # 记录上传日志
            OperationLog.objects.create(
                user=request.user,
                operation_type='upload',
                result='success',
                content_object=video,
                description=f'上传视频: {video.title}',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                security_level=video.security_level
            )
            
            messages.success(request, '视频上传成功')
            return redirect('videos:video_detail', video_id=video.id)
            
        except Exception as e:
            logger.error(f'上传视频失败: {str(e)}', exc_info=True)
            messages.error(request, f'上传失败: {str(e)}')
            return render(request, 'videos/video_upload.html')
    
    categories = Category.objects.filter(is_active=True)
    context = {
        'categories': categories,
        'security_levels': settings.SECURITY_LEVELS,
        'allowed_extensions': {
            'video': settings.ALLOWED_VIDEO_EXTENSIONS,
            'image': settings.ALLOWED_IMAGE_EXTENSIONS,
            'model': settings.ALLOWED_MODEL_EXTENSIONS,
        }
    }
    return render(request, 'videos/video_upload.html', context)


@login_required
@permission_required('video:edit')
def video_edit(request, video_id):
    """编辑视频"""
    video = get_object_or_404(Video, id=video_id, is_active=True)
    
    # 检查权限（只有上传者或管理员可以编辑）
    if video.uploader != request.user and not request.user.userprofile.has_permission('video:manage'):
        messages.error(request, '您没有权限编辑此视频')
        return redirect('videos:video_list')
    
    if request.method == 'POST':
        video.title = request.POST.get('title')
        video.description = request.POST.get('description', '')
        video.tags = request.POST.get('tags', '')
        video.category_id = request.POST.get('category') or None
        video.security_level = int(request.POST.get('security_level', 1))
        video.save()
        
        # 记录编辑日志
        OperationLog.objects.create(
            user=request.user,
            operation_type='edit',
            result='success',
            content_object=video,
            description=f'编辑视频: {video.title}',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            security_level=video.security_level
        )
        
        messages.success(request, '视频信息更新成功')
        return redirect('videos:video_detail', video_id=video.id)
    
    categories = Category.objects.filter(is_active=True)
    context = {
        'video': video,
        'categories': categories,
        'security_levels': settings.SECURITY_LEVELS,
    }
    return render(request, 'videos/video_edit.html', context)


@login_required
@permission_required('video:delete')
def video_delete(request, video_id):
    """删除视频"""
    video = get_object_or_404(Video, id=video_id, is_active=True)
    
    # 检查权限（只有上传者或管理员可以删除）
    if video.uploader != request.user and not request.user.userprofile.has_permission('video:manage'):
        messages.error(request, '您没有权限删除此视频')
        return redirect('videos:video_list')
    
    if request.method == 'POST':
        try:
            # 记录删除日志
            OperationLog.objects.create(
                user=request.user,
                operation_type='delete',
                result='success',
                content_object=video,
                description=f'删除视频: {video.title}',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                security_level=video.security_level
            )
            
            # 删除文件
            if video.file and os.path.exists(video.file.path):
                os.remove(video.file.path)
            if video.thumbnail and os.path.exists(video.thumbnail.path):
                os.remove(video.thumbnail.path)
            
            video.delete()
            messages.success(request, '视频删除成功')
            return redirect('videos:video_list')
            
        except Exception as e:
            logger.error(f'删除视频失败: {str(e)}')
            messages.error(request, f'删除失败: {str(e)}')
    
    context = {'video': video}
    return render(request, 'videos/video_delete.html', context)


@login_required
def toggle_favorite(request, video_id):
    """切换收藏状态"""
    video = get_object_or_404(Video, id=video_id, is_active=True)
    
    if not video.can_user_access(request.user):
        return JsonResponse({'error': '您没有权限访问此视频'}, status=403)
    
    try:
        favorite = VideoFavorite.objects.get(video=video, user=request.user)
        favorite.delete()
        is_favorited = False
    except VideoFavorite.DoesNotExist:
        VideoFavorite.objects.create(video=video, user=request.user)
        is_favorited = True
    
    return JsonResponse({
        'is_favorited': is_favorited,
        'message': '已收藏' if is_favorited else '已取消收藏'
    })


@login_required
def add_comment(request, video_id):
    """添加评论"""
    video = get_object_or_404(Video, id=video_id, is_active=True)
    
    if not video.can_user_access(request.user):
        return JsonResponse({'error': '您没有权限访问此视频'}, status=403)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            VideoComment.objects.create(
                video=video,
                user=request.user,
                content=content
            )
            return JsonResponse({'message': '评论添加成功'})
    
    return JsonResponse({'error': '评论内容不能为空'}, status=400)