from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse


def permission_required(permission_codename):
    """
    权限检查装饰器
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                if request.headers.get('Accept') == 'application/json':
                    return JsonResponse({'error': '请先登录'}, status=401)
                return redirect('accounts:login')
            
            try:
                user_profile = request.user.userprofile
                if user_profile.has_permission(permission_codename):
                    return view_func(request, *args, **kwargs)
                else:
                    if request.headers.get('Accept') == 'application/json':
                        return JsonResponse({'error': '权限不足'}, status=403)
                    messages.error(request, '您没有执行此操作的权限')
                    return redirect('videos:dashboard')
            except AttributeError:
                # 用户没有配置角色
                if request.headers.get('Accept') == 'application/json':
                    return JsonResponse({'error': '用户权限未配置'}, status=403)
                messages.error(request, '您的用户权限未配置，请联系管理员')
                return redirect('accounts:person')
        
        return wrapper
    return decorator


def security_level_required(min_level):
    """
    安全级别检查装饰器
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                if request.headers.get('Accept') == 'application/json':
                    return JsonResponse({'error': '请先登录'}, status=401)
                return redirect('accounts:login')
            
            try:
                user_profile = request.user.userprofile
                if user_profile.max_security_level >= min_level:
                    return view_func(request, *args, **kwargs)
                else:
                    if request.headers.get('Accept') == 'application/json':
                        return JsonResponse({'error': '安全级别不足'}, status=403)
                    messages.error(request, f'您需要{min_level}级或以上权限才能访问此内容')
                    return redirect('videos:dashboard')
            except AttributeError:
                if request.headers.get('Accept') == 'application/json':
                    return JsonResponse({'error': '用户权限未配置'}, status=403)
                messages.error(request, '您的用户权限未配置，请联系管理员')
                return redirect('accounts:person')
        
        return wrapper
    return decorator


def admin_required(view_func):
    """
    管理员权限装饰器
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.headers.get('Accept') == 'application/json':
                return JsonResponse({'error': '请先登录'}, status=401)
            return redirect('accounts:login')
        
        try:
            user_profile = request.user.userprofile
            if user_profile.has_permission('user:manage') or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            else:
                if request.headers.get('Accept') == 'application/json':
                    return JsonResponse({'error': '需要管理员权限'}, status=403)
                messages.error(request, '您需要管理员权限才能访问此页面')
                return redirect('videos:dashboard')
        except AttributeError:
            if request.headers.get('Accept') == 'application/json':
                return JsonResponse({'error': '用户权限未配置'}, status=403)
            messages.error(request, '您的用户权限未配置，请联系管理员')
            return redirect('accounts:person')
    
    return wrapper
