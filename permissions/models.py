from django.db import models
from django.conf import settings


class Role(models.Model):
    """角色模型"""
    name = models.CharField(max_length=50, unique=True, verbose_name="角色名称")
    description = models.TextField(blank=True, null=True, verbose_name="角色描述")
    max_security_level = models.IntegerField(default=1, verbose_name="最高可访问级别")
    is_active = models.BooleanField(default=True, verbose_name="是否激活")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "角色"
        verbose_name_plural = "角色"

    def __str__(self):
        return self.name


class Permission(models.Model):
    """权限模型"""
    name = models.CharField(max_length=50, unique=True, verbose_name="权限名称")
    codename = models.CharField(max_length=100, unique=True, verbose_name="权限代码")
    description = models.TextField(blank=True, null=True, verbose_name="权限描述")
    module = models.CharField(max_length=50, verbose_name="所属模块")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "权限"
        verbose_name_plural = "权限"

    def __str__(self):
        return f"{self.name} ({self.codename})"


class RolePermission(models.Model):
    """角色权限关联模型"""
    role = models.ForeignKey(Role, on_delete=models.CASCADE, verbose_name="角色")
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, verbose_name="权限")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "角色权限"
        verbose_name_plural = "角色权限"
        unique_together = ('role', 'permission')

    def __str__(self):
        return f"{self.role.name} - {self.permission.name}"


class UserProfile(models.Model):
    """用户扩展信息模型"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="用户")
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="角色")
    department = models.CharField(max_length=100, blank=True, null=True, verbose_name="部门")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="电话")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="头像")
    is_active = models.BooleanField(default=True, verbose_name="是否激活")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "用户信息"
        verbose_name_plural = "用户信息"

    def __str__(self):
        return f"{self.user.username} - {self.role.name if self.role else '无角色'}"

    @property
    def max_security_level(self):
        """获取用户最高可访问的安全级别"""
        if self.role:
            return self.role.max_security_level
        return 1  # 默认公开级别

    def has_permission(self, codename):
        """检查用户是否有指定权限"""
        if not self.role:
            return False
        return self.role.rolepermission_set.filter(
            permission__codename=codename
        ).exists()