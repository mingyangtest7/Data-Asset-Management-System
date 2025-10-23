# 创建测试文件
import os

# 创建测试目录
test_dir = "test_files"
os.makedirs(test_dir, exist_ok=True)

# 创建测试模型文件
with open(os.path.join(test_dir, "test_model.fbx"), "w") as f:
    f.write("This is a test FBX model file")

# 创建测试图片文件
with open(os.path.join(test_dir, "test_image.png"), "w") as f:
    f.write("This is a test PNG image file")

# 创建测试视频文件
with open(os.path.join(test_dir, "test_video.mp4"), "w") as f:
    f.write("This is a test MP4 video file")

print("测试文件已创建:")
print("- test_model.fbx")
print("- test_image.png") 
print("- test_video.mp4")
print(f"文件位置: {os.path.abspath(test_dir)}")

