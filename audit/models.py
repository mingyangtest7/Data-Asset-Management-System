from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class OperationLog(models.Model):
    """操作日志模型"""
    OPERATION_TYPE_CHOICES = [
        ('upload', '上传'),
        ('download', '下载'),
        ('view', '观看'),
        ('edit', '编辑'),
        ('delete', '删除'),
        ('create', '创建'),
        ('update', '更新'),
        ('login', '登录'),
        ('logout', '退出'),
        ('permission_change', '权限变更'),
    ]

    RESULT_CHOICES = [
        ('success', '成功'),
        ('failed', '失败'),
        ('denied', '拒绝'),
    ]

    # 基本信息
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="操作用户")
    operation_type = models.CharField(max_length=20, choices=OPERATION_TYPE_CHOICES, verbose_name="操作类型")
    operation_time = models.DateTimeField(auto_now_add=True, verbose_name="操作时间")
    result = models.CharField(max_length=10, choices=RESULT_CHOICES, verbose_name="操作结果")
    
    # 操作对象（通用外键）
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # 详细信息
    description = models.TextField(verbose_name="操作描述")
    ip_address = models.GenericIPAddressField(verbose_name="IP地址")
    user_agent = models.TextField(blank=True, null=True, verbose_name="用户代理")
    
    # 额外信息
    extra_data = models.JSONField(default=dict, blank=True, verbose_name="额外数据")
    
    # 安全相关
    security_level = models.IntegerField(default=1, verbose_name="涉及安全级别")

    class Meta:
        verbose_name = "操作日志"
        verbose_name_plural = "操作日志"
        ordering = ['-operation_time']

    def __str__(self):
        return f"{self.get_operation_type_display()} - {self.user.username if self.user else '匿名'} - {self.operation_time}"

    @property
    def operation_type_display(self):
        return dict(self.OPERATION_TYPE_CHOICES).get(self.operation_type, '未知')

    @property
    def result_display(self):
        return dict(self.RESULT_CHOICES).get(self.result, '未知')


class SystemLog(models.Model):
    """系统日志模型"""
    LOG_LEVEL_CHOICES = [
        ('DEBUG', '调试'),
        ('INFO', '信息'),
        ('WARNING', '警告'),
        ('ERROR', '错误'),
        ('CRITICAL', '严重'),
    ]

    level = models.CharField(max_length=10, choices=LOG_LEVEL_CHOICES, verbose_name="日志级别")
    module = models.CharField(max_length=50, verbose_name="模块")
    message = models.TextField(verbose_name="日志消息")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    extra_data = models.JSONField(default=dict, blank=True, verbose_name="额外数据")

    class Meta:
        verbose_name = "系统日志"
        verbose_name_plural = "系统日志"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.level} - {self.module} - {self.created_at}"


class AccessLog(models.Model):
    """访问日志模型"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="用户")
    path = models.CharField(max_length=500, verbose_name="访问路径")
    method = models.CharField(max_length=10, verbose_name="HTTP方法")
    status_code = models.IntegerField(verbose_name="状态码")
    response_time = models.FloatField(verbose_name="响应时间(ms)")
    ip_address = models.GenericIPAddressField(verbose_name="IP地址")
    user_agent = models.TextField(blank=True, null=True, verbose_name="用户代理")
    accessed_at = models.DateTimeField(auto_now_add=True, verbose_name="访问时间")

    class Meta:
        verbose_name = "访问日志"
        verbose_name_plural = "访问日志"
        ordering = ['-accessed_at']

    def __str__(self):
        return f"{self.method} {self.path} - {self.status_code} - {self.accessed_at}"