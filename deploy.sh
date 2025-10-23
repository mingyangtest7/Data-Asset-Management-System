#!/bin/bash
# Django项目部署脚本

echo "开始部署Django项目..."

# 更新系统包
sudo apt update && sudo apt upgrade -y

# 安装必要的软件包
sudo apt install -y python3 python3-pip python3-venv nginx mysql-server git

# 安装Python依赖
pip3 install --upgrade pip
pip3 install django mysqlclient gunicorn supervisor

# 创建项目目录
sudo mkdir -p /var/www/mysite
sudo chown $USER:$USER /var/www/mysite

# 进入项目目录
cd /var/www/mysite

# 克隆项目（如果使用Git）
# git clone your-repository-url .

# 或者直接上传项目文件

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装项目依赖
pip install -r requirements.txt

# 配置MySQL数据库
sudo mysql_secure_installation

# 创建数据库
sudo mysql -u root -p << EOF
CREATE DATABASE video_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'django_user'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON video_management.* TO 'django_user'@'localhost';
FLUSH PRIVILEGES;
EOF

# 运行Django迁移
python manage.py makemigrations
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 收集静态文件
python manage.py collectstatic --noinput

# 设置文件权限
sudo chown -R www-data:www-data /var/www/mysite
sudo chmod -R 755 /var/www/mysite

echo "部署完成！"
