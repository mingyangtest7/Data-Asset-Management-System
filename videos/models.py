from django.db import models
from django.conf import settings
import os


class Category(models.Model):
    """视频分类模型"""
    name = models.CharField(max_length=50, unique=True, verbose_name="分类名称")
    description = models.TextField(blank=True, null=True, verbose_name="分类描述")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, verbose_name="父分类")
    is_active = models.BooleanField(default=True, verbose_name="是否激活")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "视频分类"
        verbose_name_plural = "视频分类"

    def __str__(self):
        return self.name


class Video(models.Model):
    """视频模型"""
    SECURITY_LEVEL_CHOICES = [
        (1, '公开'),
        (2, '内部'),
        (3, '秘密'),
        (4, '绝密'),
    ]

    FILE_TYPE_CHOICES = [
        ('video', '视频'),
        ('image', '图片'),
        ('model', '模型'),
    ]

    # 基本信息
    title = models.CharField(max_length=200, verbose_name="标题")
    description = models.TextField(blank=True, null=True, verbose_name="描述")
    tags = models.CharField(max_length=500, blank=True, null=True, verbose_name="标签")
    
    # 文件信息
    file = models.FileField(upload_to='videos/', verbose_name="文件")
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES, verbose_name="文件类型")
    file_size = models.BigIntegerField(verbose_name="文件大小(字节)")
    file_extension = models.CharField(max_length=10, verbose_name="文件扩展名")
    md5_hash = models.CharField(max_length=32, unique=True, verbose_name="MD5哈希值")
    
    # 视频特有信息
    duration = models.DurationField(blank=True, null=True, verbose_name="时长")
    resolution = models.CharField(max_length=20, blank=True, null=True, verbose_name="分辨率")
    codec = models.CharField(max_length=50, blank=True, null=True, verbose_name="编码格式")
    bitrate = models.IntegerField(blank=True, null=True, verbose_name="比特率")
    frame_rate = models.FloatField(blank=True, null=True, verbose_name="帧率")
    
    # 分类和权限
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="分类")
    security_level = models.IntegerField(choices=SECURITY_LEVEL_CHOICES, default=1, verbose_name="重要级别")
    
    # 上传信息
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="上传者")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="上传时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    # 状态信息
    is_active = models.BooleanField(default=True, verbose_name="是否激活")
    download_count = models.IntegerField(default=0, verbose_name="下载次数")
    view_count = models.IntegerField(default=0, verbose_name="观看次数")
    
    # 缩略图
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True, null=True, verbose_name="缩略图")

    class Meta:
        verbose_name = "视频"
        verbose_name_plural = "视频"
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.title

    @property
    def file_size_mb(self):
        """返回文件大小的MB表示"""
        return round(self.file_size / (1024 * 1024), 2)

    @property
    def security_level_display(self):
        """返回安全级别的显示名称"""
        return dict(self.SECURITY_LEVEL_CHOICES).get(self.security_level, '未知')

    def get_file_url(self):
        """获取文件访问URL"""
        if self.file:
            return self.file.url
        return None

    def get_thumbnail_url(self):
        """获取缩略图URL"""
        if self.thumbnail:
            return self.thumbnail.url
        return None

    def can_user_access(self, user):
        """检查用户是否有权限访问此视频"""
        try:
            user_profile = user.userprofile
            return user_profile.max_security_level >= self.security_level
        except UserProfile.DoesNotExist:
            return self.security_level == 1  # 默认只能访问公开级别

    def increment_view_count(self):
        """增加观看次数"""
        self.view_count += 1
        self.save(update_fields=['view_count'])

    def increment_download_count(self):
        """增加下载次数"""
        self.download_count += 1
        self.save(update_fields=['download_count'])


class VideoVersion(models.Model):
    """视频版本模型（用于存储不同码率的版本）"""
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='versions', verbose_name="原视频")
    resolution = models.CharField(max_length=20, verbose_name="分辨率")
    bitrate = models.IntegerField(verbose_name="比特率")
    file = models.FileField(upload_to='videos/versions/', verbose_name="版本文件")
    file_size = models.BigIntegerField(verbose_name="文件大小(字节)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "视频版本"
        verbose_name_plural = "视频版本"
        unique_together = ('video', 'resolution', 'bitrate')

    def __str__(self):
        return f"{self.video.title} - {self.resolution}"


class VideoComment(models.Model):
    """视频评论模型"""
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='comments', verbose_name="视频")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="评论者")
    content = models.TextField(verbose_name="评论内容")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="评论时间")
    is_active = models.BooleanField(default=True, verbose_name="是否显示")

    class Meta:
        verbose_name = "视频评论"
        verbose_name_plural = "视频评论"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.video.title}"


class VideoFavorite(models.Model):
    """视频收藏模型"""
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='favorites', verbose_name="视频")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="收藏者")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="收藏时间")

    class Meta:
        verbose_name = "视频收藏"
        verbose_name_plural = "视频收藏"
        unique_together = ('video', 'user')

    def __str__(self):
        return f"{self.user.username} 收藏了 {self.video.title}"