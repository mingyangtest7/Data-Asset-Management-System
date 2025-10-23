# 三维数据资产管理系统

## 🎯 系统概述

这是一个基于Django的三维数据资产管理系统，提供完整的用户管理、权限控制、数据上传、标签管理等功能。

## ✨ 主要功能

### 🔐 用户认证系统
- 用户注册/登录
- 密码验证
- 会话管理
- 用户状态管理

### 👥 权限管理系统
- 基于角色的权限控制
- 四个模块权限：数据统计、我的数据、数据管理、系统设置
- 权限组的新增、修改、删除
- 用户权限分配

### 📊 数据统计模块
- 总上传/下载数据统计
- 最近7天数据趋势
- 最新数据模型展示
- 图表可视化

### 📁 我的数据模块
- 个人上传记录
- 个人下载记录
- 数据分页显示
- 数据搜索功能

### 🗂️ 数据管理模块
- 数据模型网格展示
- 文件上传（支持多种格式）
- 标签管理（地理位置、项目归属）
- 数据搜索和筛选
- 数据删除功能

### ⚙️ 系统设置模块
- 账号管理（启用/禁用、编辑、删除）
- 权限管理（创建、修改、删除权限组）
- 用户权限分配
- 分页显示

## 🛠️ 技术栈

- **后端**: Django 5.2.4
- **数据库**: MySQL
- **前端**: HTML5, CSS3, JavaScript (ES6+)
- **UI框架**: Bootstrap 5.1.3
- **图标**: Font Awesome 6.0.0
- **文件上传**: Django FileField + AJAX

## 📋 系统要求

- Python 3.8+
- Django 5.2.4
- MySQL 5.7+
- 现代浏览器（Chrome, Firefox, Safari, Edge）

## 🚀 快速开始

### 1. 环境准备
```bash
# 克隆项目
git clone <repository-url>
cd mysite

# 安装依赖
pip install django pymysql pillow
```

### 2. 数据库配置
```bash
# 创建MySQL数据库
mysql -u root -p
CREATE DATABASE video_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. 数据库迁移
```bash
# 创建迁移文件
python manage.py makemigrations accounts

# 应用迁移
python manage.py migrate
```

### 4. 创建超级用户
```bash
python manage.py createsuperuser
```

### 5. 初始化数据
```bash
python init_data.py
```

### 6. 启动服务器
```bash
python manage.py runserver
```

### 7. 访问系统
- 登录页面: http://127.0.0.1:8000/accounts/login/
- 注册页面: http://127.0.0.1:8000/accounts/register/
- 仪表盘: http://127.0.0.1:8000/accounts/dashboard/

## 📁 项目结构

```
mysite/
├── accounts/                 # 用户账户应用
│   ├── models.py            # 数据模型
│   ├── views.py             # 视图函数
│   ├── urls.py              # URL路由
│   └── admin.py             # 管理后台
├── templates/               # 模板文件
│   ├── login.html           # 登录页面
│   ├── dashboard.html       # 仪表盘
│   ├── my_data.html         # 我的数据
│   ├── data_management.html # 数据管理
│   └── system_settings.html # 系统设置
├── static/                  # 静态文件
│   ├── css/                 # 样式文件
│   ├── js/                  # JavaScript文件
│   └── images/              # 图片文件
├── media/                   # 媒体文件
│   └── models/              # 上传的模型文件
├── mysite/                  # 项目配置
│   ├── settings.py          # 设置文件
│   ├── urls.py              # 主URL配置
│   └── wsgi.py              # WSGI配置
├── init_data.py             # 数据初始化脚本
└── manage.py                # Django管理脚本
```

## 🔧 配置说明

### 数据库配置 (settings.py)
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'video_management',
        'USER': 'root',
        'PASSWORD': '123456',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

### 文件上传配置
- 最大文件大小: 5GB
- 支持格式:
  - 模型文件: .fbx, .zip, .rar, .7z, .obj, .gltf, .glb
  - 媒体文件: .png, .jpg, .jpeg, .bmp, .tga, .mp4, .webm

## 🎨 界面特色

- **深色主题**: 现代化的深色界面设计
- **响应式布局**: 适配各种屏幕尺寸
- **动画效果**: 流畅的过渡动画
- **毛玻璃效果**: 现代化的视觉体验
- **图标支持**: Font Awesome图标库

## 🔒 安全特性

- CSRF保护
- 用户认证
- 权限验证
- 文件类型验证
- 文件大小限制
- SQL注入防护

## 📊 API接口

### 权限管理API
- `POST /accounts/api/permission-groups/` - 创建权限组
- `POST /accounts/api/permission-groups/{id}/` - 更新权限组
- `POST /accounts/api/permission-groups/{id}/delete/` - 删除权限组

### 标签管理API
- `POST /accounts/api/location-tags/` - 创建地理位置标签
- `POST /accounts/api/project-tags/` - 创建项目归属标签
- `POST /accounts/api/location-tags/{id}/delete/` - 删除地理位置标签
- `POST /accounts/api/project-tags/{id}/delete/` - 删除项目归属标签

### 数据管理API
- `POST /accounts/api/data-models/` - 上传数据模型
- `POST /accounts/api/data-models/{id}/delete/` - 删除数据模型

### 用户管理API
- `POST /accounts/api/users/{id}/toggle-status/` - 切换用户状态
- `POST /accounts/api/users/{id}/assign-permission/` - 分配用户权限

## 🐛 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查MySQL服务是否启动
   - 验证数据库配置信息
   - 确认数据库用户权限

2. **文件上传失败**
   - 检查media目录权限
   - 验证文件大小限制
   - 确认文件格式支持

3. **权限验证失败**
   - 检查用户是否已分配权限组
   - 验证权限组配置
   - 确认用户状态是否启用

4. **静态文件加载失败**
   - 运行 `python manage.py collectstatic`
   - 检查STATIC_URL配置
   - 验证静态文件路径

## 📝 更新日志

### v1.0.0 (2025-01-15)
- 初始版本发布
- 完整的用户认证系统
- 权限管理系统
- 数据管理功能
- 标签管理功能
- 文件上传功能

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系方式

如有问题或建议，请联系开发团队。

---

**注意**: 这是一个演示项目，生产环境使用前请进行充分的安全测试和性能优化。