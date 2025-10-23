from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from .models import OperationLog, SystemLog, AccessLog
from permissions.decorators import permission_required
import json


@login_required
@permission_required('log:view')
def operation_logs(request):
    """操作日志列表"""
    logs = OperationLog.objects.select_related('user', 'content_type').order_by('-operation_time')
    
    # 搜索功能
    search = request.GET.get('search', '')
    if search:
        logs = logs.filter(
            Q(user__username__icontains=search) |
            Q(description__icontains=search) |
            Q(operation_type__icontains=search)
        )
    
    # 筛选功能
    operation_type = request.GET.get('operation_type')
    if operation_type:
        logs = logs.filter(operation_type=operation_type)
    
    result = request.GET.get('result')
    if result:
        logs = logs.filter(result=result)
    
    security_level = request.GET.get('security_level')
    if security_level:
        logs = logs.filter(security_level=int(security_level))
    
    # 时间范围筛选
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        logs = logs.filter(operation_time__date__gte=start_date)
    if end_date:
        logs = logs.filter(operation_time__date__lte=end_date)
    
    # 分页
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'operation_type': operation_type,
        'result': result,
        'security_level': security_level,
        'start_date': start_date,
        'end_date': end_date,
        'operation_types': OperationLog.OPERATION_TYPE_CHOICES,
        'results': OperationLog.RESULT_CHOICES,
        'security_levels': range(1, 5),
    }
    
    return render(request, 'audit/operation_logs.html', context)


@login_required
@permission_required('log:view')
def system_logs(request):
    """系统日志列表"""
    logs = SystemLog.objects.all().order_by('-created_at')
    
    # 搜索功能
    search = request.GET.get('search', '')
    if search:
        logs = logs.filter(
            Q(module__icontains=search) |
            Q(message__icontains=search)
        )
    
    # 筛选功能
    level = request.GET.get('level')
    if level:
        logs = logs.filter(level=level)
    
    module = request.GET.get('module')
    if module:
        logs = logs.filter(module=module)
    
    # 时间范围筛选
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        logs = logs.filter(created_at__date__gte=start_date)
    if end_date:
        logs = logs.filter(created_at__date__lte=end_date)
    
    # 分页
    paginator = Paginator(logs, 100)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 获取所有模块
    modules = SystemLog.objects.values_list('module', flat=True).distinct()
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'level': level,
        'module': module,
        'start_date': start_date,
        'end_date': end_date,
        'levels': SystemLog.LOG_LEVEL_CHOICES,
        'modules': modules,
    }
    
    return render(request, 'audit/system_logs.html', context)


@login_required
@permission_required('log:view')
def access_logs(request):
    """访问日志列表"""
    logs = AccessLog.objects.select_related('user').order_by('-accessed_at')
    
    # 搜索功能
    search = request.GET.get('search', '')
    if search:
        logs = logs.filter(
            Q(user__username__icontains=search) |
            Q(path__icontains=search) |
            Q(ip_address__icontains=search)
        )
    
    # 筛选功能
    method = request.GET.get('method')
    if method:
        logs = logs.filter(method=method)
    
    status_code = request.GET.get('status_code')
    if status_code:
        logs = logs.filter(status_code=status_code)
    
    # 时间范围筛选
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        logs = logs.filter(accessed_at__date__gte=start_date)
    if end_date:
        logs = logs.filter(accessed_at__date__lte=end_date)
    
    # 分页
    paginator = Paginator(logs, 100)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'method': method,
        'status_code': status_code,
        'start_date': start_date,
        'end_date': end_date,
        'methods': ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
        'status_codes': [200, 301, 302, 400, 401, 403, 404, 500],
    }
    
    return render(request, 'audit/access_logs.html', context)


@login_required
@permission_required('log:export')
def export_logs(request):
    """导出日志"""
    log_type = request.GET.get('type', 'operation')
    format_type = request.GET.get('format', 'json')
    
    if log_type == 'operation':
        logs = OperationLog.objects.all().order_by('-operation_time')
    elif log_type == 'system':
        logs = SystemLog.objects.all().order_by('-created_at')
    elif log_type == 'access':
        logs = AccessLog.objects.all().order_by('-accessed_at')
    else:
        return JsonResponse({'error': '无效的日志类型'}, status=400)
    
    # 时间范围限制
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        if log_type == 'operation':
            logs = logs.filter(operation_time__date__gte=start_date)
        elif log_type == 'system':
            logs = logs.filter(created_at__date__gte=start_date)
        else:
            logs = logs.filter(accessed_at__date__gte=start_date)
    
    if end_date:
        if log_type == 'operation':
            logs = logs.filter(operation_time__date__lte=end_date)
        elif log_type == 'system':
            logs = logs.filter(created_at__date__lte=end_date)
        else:
            logs = logs.filter(accessed_at__date__lte=end_date)
    
    # 限制导出数量
    logs = logs[:10000]
    
    if format_type == 'json':
        data = []
        for log in logs:
            if log_type == 'operation':
                data.append({
                    'operation_time': log.operation_time.isoformat(),
                    'user': log.user.username if log.user else '匿名',
                    'operation_type': log.operation_type,
                    'result': log.result,
                    'description': log.description,
                    'ip_address': log.ip_address,
                    'security_level': log.security_level,
                })
            elif log_type == 'system':
                data.append({
                    'created_at': log.created_at.isoformat(),
                    'level': log.level,
                    'module': log.module,
                    'message': log.message,
                })
            else:  # access
                data.append({
                    'accessed_at': log.accessed_at.isoformat(),
                    'user': log.user.username if log.user else '匿名',
                    'path': log.path,
                    'method': log.method,
                    'status_code': log.status_code,
                    'response_time': log.response_time,
                    'ip_address': log.ip_address,
                })
        
        return JsonResponse(data, safe=False)
    
    return JsonResponse({'error': '不支持的导出格式'}, status=400)


@login_required
@permission_required('log:view')
def log_statistics(request):
    """日志统计"""
    # 操作日志统计
    operation_stats = OperationLog.objects.extra(
        select={'date': 'DATE(operation_time)'}
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')[:30]
    
    # 按操作类型统计
    operation_type_stats = OperationLog.objects.values('operation_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # 按结果统计
    result_stats = OperationLog.objects.values('result').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # 按用户统计
    user_stats = OperationLog.objects.filter(
        user__isnull=False
    ).values('user__username').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # 系统日志统计
    system_level_stats = SystemLog.objects.values('level').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'operation_stats': operation_stats,
        'operation_type_stats': operation_type_stats,
        'result_stats': result_stats,
        'user_stats': user_stats,
        'system_level_stats': system_level_stats,
    }
    
    return render(request, 'audit/log_statistics.html', context)