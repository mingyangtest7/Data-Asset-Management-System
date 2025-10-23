from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import JsonResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Role, Permission, RolePermission, UserProfile
from .decorators import permission_required
import json


@login_required
@permission_required('user:manage')
def role_list(request):
    """角色列表"""
    roles = Role.objects.all().order_by('-created_at')
    
    # 搜索功能
    search = request.GET.get('search', '')
    if search:
        roles = roles.filter(Q(name__icontains=search) | Q(description__icontains=search))
    
    # 分页
    paginator = Paginator(roles, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
    }
    return render(request, 'permissions/role_list.html', context)


@login_required
@permission_required('user:manage')
def role_create(request):
    """创建角色"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        max_security_level = int(request.POST.get('max_security_level', 1))
        permissions = request.POST.getlist('permissions')
        
        if not name:
            messages.error(request, '角色名称不能为空')
            return render(request, 'permissions/role_form.html')
        
        if Role.objects.filter(name=name).exists():
            messages.error(request, '角色名称已存在')
            return render(request, 'permissions/role_form.html')
        
        try:
            role = Role.objects.create(
                name=name,
                description=description,
                max_security_level=max_security_level
            )
            
            # 分配权限
            for permission_id in permissions:
                permission = get_object_or_404(Permission, id=permission_id)
                RolePermission.objects.create(role=role, permission=permission)
            
            messages.success(request, '角色创建成功')
            return redirect('permissions:role_list')
        except Exception as e:
            messages.error(request, f'创建角色失败: {str(e)}')
    
    permissions = Permission.objects.all().order_by('module', 'name')
    context = {
        'permissions': permissions,
        'security_levels': range(1, 5),
    }
    return render(request, 'permissions/role_form.html', context)


@login_required
@permission_required('user:manage')
def role_edit(request, role_id):
    """编辑角色"""
    role = get_object_or_404(Role, id=role_id)
    
    if request.method == 'POST':
        role.name = request.POST.get('name')
        role.description = request.POST.get('description', '')
        role.max_security_level = int(request.POST.get('max_security_level', 1))
        role.save()
        
        # 更新权限
        role.rolepermission_set.all().delete()
        permissions = request.POST.getlist('permissions')
        for permission_id in permissions:
            permission = get_object_or_404(Permission, id=permission_id)
            RolePermission.objects.create(role=role, permission=permission)
        
        messages.success(request, '角色更新成功')
        return redirect('permissions:role_list')
    
    permissions = Permission.objects.all().order_by('module', 'name')
    role_permissions = role.rolepermission_set.values_list('permission_id', flat=True)
    
    context = {
        'role': role,
        'permissions': permissions,
        'role_permissions': role_permissions,
        'security_levels': range(1, 5),
    }
    return render(request, 'permissions/role_form.html', context)


@login_required
@permission_required('user:manage')
def role_delete(request, role_id):
    """删除角色"""
    role = get_object_or_404(Role, id=role_id)
    
    if request.method == 'POST':
        try:
            role.delete()
            messages.success(request, '角色删除成功')
        except Exception as e:
            messages.error(request, f'删除角色失败: {str(e)}')
    
    return redirect('permissions:role_list')


@login_required
@permission_required('user:manage')
def user_list(request):
    """用户列表"""
    users = settings.AUTH_USER_MODEL.objects.select_related('userprofile__role').all().order_by('-date_joined')
    
    # 搜索功能
    search = request.GET.get('search', '')
    if search:
        users = users.filter(Q(username__icontains=search) | Q(email__icontains=search))
    
    # 分页
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
    }
    return render(request, 'permissions/user_list.html', context)


@login_required
@permission_required('user:manage')
def user_edit(request, user_id):
    """编辑用户"""
    user = get_object_or_404(settings.AUTH_USER_MODEL, id=user_id)
    user_profile, created = UserProfile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        # 更新用户基本信息
        user.username = request.POST.get('username')
        user.email = request.POST.get('email', '')
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.is_active = request.POST.get('is_active') == 'on'
        user.save()
        
        # 更新用户扩展信息
        role_id = request.POST.get('role')
        if role_id:
            role = get_object_or_404(Role, id=role_id)
            user_profile.role = role
        else:
            user_profile.role = None
        
        user_profile.department = request.POST.get('department', '')
        user_profile.phone = request.POST.get('phone', '')
        user_profile.is_active = request.POST.get('profile_is_active') == 'on'
        user_profile.save()
        
        messages.success(request, '用户信息更新成功')
        return redirect('permissions:user_list')
    
    roles = Role.objects.filter(is_active=True)
    context = {
        'user': user,
        'user_profile': user_profile,
        'roles': roles,
    }
    return render(request, 'permissions/user_form.html', context)


@login_required
def my_permissions(request):
    """查看我的权限"""
    try:
        user_profile = request.user.userprofile
        role = user_profile.role
        permissions = []
        
        if role:
            permissions = Permission.objects.filter(
                rolepermission__role=role
            ).order_by('module', 'name')
        
        context = {
            'user_profile': user_profile,
            'role': role,
            'permissions': permissions,
        }
        return render(request, 'permissions/my_permissions.html', context)
    except UserProfile.DoesNotExist:
        messages.warning(request, '您还没有配置用户信息')
        return redirect('accounts:person')


def init_permissions(request):
    """初始化权限数据（仅开发环境使用）"""
    if not request.user.is_superuser:
        return JsonResponse({'error': '权限不足'}, status=403)
    
    # 创建默认权限
    default_permissions = [
        ('video:upload', '上传视频', '视频管理'),
        ('video:view', '观看视频', '视频管理'),
        ('video:download', '下载视频', '视频管理'),
        ('video:edit', '编辑视频', '视频管理'),
        ('video:delete', '删除视频', '视频管理'),
        ('video:manage', '视频管理', '视频管理'),
        ('user:manage', '用户管理', '用户管理'),
        ('role:manage', '角色管理', '角色管理'),
        ('log:view', '查看日志', '系统管理'),
        ('log:export', '导出日志', '系统管理'),
    ]
    
    created_count = 0
    for codename, name, module in default_permissions:
        permission, created = Permission.objects.get_or_create(
            codename=codename,
            defaults={
                'name': name,
                'module': module,
                'description': f'{module}模块的{name}权限'
            }
        )
        if created:
            created_count += 1
    
    # 创建默认角色
    default_roles = [
        ('超级管理员', '系统超级管理员，拥有所有权限', 4),
        ('管理员', '系统管理员，拥有大部分权限', 3),
        ('普通用户', '普通用户，拥有基本权限', 2),
        ('访客', '访客用户，只有查看权限', 1),
    ]
    
    role_created_count = 0
    for role_name, description, max_level in default_roles:
        role, created = Role.objects.get_or_create(
            name=role_name,
            defaults={
                'description': description,
                'max_security_level': max_level
            }
        )
        if created:
            role_created_count += 1
            
            # 为角色分配权限
            if role_name == '超级管理员':
                permissions = Permission.objects.all()
            elif role_name == '管理员':
                permissions = Permission.objects.exclude(codename__in=['user:manage', 'role:manage'])
            elif role_name == '普通用户':
                permissions = Permission.objects.filter(
                    codename__in=['video:upload', 'video:view', 'video:download']
                )
            else:  # 访客
                permissions = Permission.objects.filter(codename='video:view')
            
            for permission in permissions:
                RolePermission.objects.get_or_create(role=role, permission=permission)
    
    return JsonResponse({
        'message': '权限初始化成功',
        'created_permissions': created_count,
        'created_roles': role_created_count
    })