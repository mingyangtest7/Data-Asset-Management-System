from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import datetime


class User(AbstractUser):
    """扩展用户模型"""
    display_name = models.CharField(max_length=100, default='', blank=True, verbose_name="显示名称")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    created_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="创建人")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="创建时间")
    
    class Meta:
        verbose_name = "用户"
        verbose_name_plural = "用户"


class PermissionGroup(models.Model):
    """权限组模型"""
    name = models.CharField(max_length=100, unique=True, verbose_name="权限名称")
    description = models.TextField(blank=True, verbose_name="权限描述")
    
    # 模块权限
    can_view_dashboard = models.BooleanField(default=False, verbose_name="数据统计")
    can_view_my_data = models.BooleanField(default=False, verbose_name="我的数据")
    can_view_data_management = models.BooleanField(default=False, verbose_name="数据管理")
    can_view_system_settings = models.BooleanField(default=False, verbose_name="系统设置")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    class Meta:
        verbose_name = "权限组"
        verbose_name_plural = "权限组"
    
    def __str__(self):
        return self.name


class UserPermission(models.Model):
    """用户权限关联"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    permission_group = models.ForeignKey(PermissionGroup, on_delete=models.CASCADE, verbose_name="权限组")
    
    class Meta:
        verbose_name = "用户权限"
        verbose_name_plural = "用户权限"
        unique_together = ['user', 'permission_group']


class LocationTag(models.Model):
    """地理位置标签"""
    name = models.CharField(max_length=100, unique=True, verbose_name="地理位置名称")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    class Meta:
        verbose_name = "地理位置标签"
        verbose_name_plural = "地理位置标签"
    
    def __str__(self):
        return self.name


class ProjectTag(models.Model):
    """项目归属标签"""
    name = models.CharField(max_length=200, unique=True, verbose_name="项目归属名称")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    class Meta:
        verbose_name = "项目归属标签"
        verbose_name_plural = "项目归属标签"
    
    def __str__(self):
        return self.name


class DataModel(models.Model):
    """数据模型"""
    SOURCE_CHOICES = [
        ('internal', '内部'),
        ('external', '外部'),
    ]
    
    INFRINGEMENT_CHOICES = [
        ('no', '不侵权'),
        ('yes', '侵权'),
    ]
    
    LEVEL_CHOICES = [
        ('confidential', '保密'),
        ('important', '重要'),
        ('normal', '普通'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="模型名称")
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, verbose_name="来源")
    project_tag = models.ForeignKey(ProjectTag, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="项目归属")
    location_tag = models.ForeignKey(LocationTag, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="地理位置")
    infringement_risk = models.CharField(max_length=20, choices=INFRINGEMENT_CHOICES, verbose_name="侵权风险")
    model_level = models.CharField(max_length=20, choices=LEVEL_CHOICES, verbose_name="模型等级")
    description = models.TextField(blank=True, verbose_name="简介或建议")
    
    # 文件信息
    model_file = models.FileField(upload_to='models/', null=True, blank=True, verbose_name="模型文件")
    media_files = models.JSONField(default=list, blank=True, verbose_name="媒体文件")
    
    # 元数据
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="创建人")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        verbose_name = "数据模型"
        verbose_name_plural = "数据模型"
    
    def __str__(self):
        return self.name


class UploadLog(models.Model):
    """上传日志"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    filename = models.CharField(max_length=255, verbose_name="文件名")
    file_size = models.BigIntegerField(verbose_name="文件大小")
    upload_time = models.DateTimeField(auto_now_add=True, verbose_name="上传时间")
    status = models.CharField(max_length=20, default='success', verbose_name="状态")
    source_model = models.ForeignKey(DataModel, on_delete=models.CASCADE, null=True, blank=True, verbose_name="来源模型")
    
    class Meta:
        verbose_name = "上传日志"
        verbose_name_plural = "上传日志"


class DownloadLog(models.Model):
    """下载日志"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    filename = models.CharField(max_length=255, verbose_name="文件名")
    file_size = models.BigIntegerField(verbose_name="文件大小")
    download_time = models.DateTimeField(auto_now_add=True, verbose_name="下载时间")
    source_model = models.ForeignKey(DataModel, on_delete=models.CASCADE, null=True, blank=True, verbose_name="来源模型")
    download_source = models.CharField(max_length=50, default='data_management', verbose_name="下载来源")
    status = models.CharField(max_length=20, default='success', verbose_name="状态")
    
    class Meta:
        verbose_name = "下载日志"
        verbose_name_plural = "下载日志"