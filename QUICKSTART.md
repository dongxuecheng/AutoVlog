# 🎬 API 服务 - 快速测试指南

## 准备工作

### 1. 检查资源文件

```bash
# 视频文件（已存在）
ls examples/v*.mp4

# 封面图片（已创建）
ls examples/cover.jpg

# 边框文件
ls templates/*/border*.png
```

### 2. 创建视频边框（可选）

如果只有 `border.png`，可以复制一份作为 `border_video.png`：

```bash
# 为每个模板创建视频边框
cp templates/classic/border.png templates/classic/border_video.png
cp templates/modern/border.png templates/modern/border_video.png
cp templates/elegant/border.png templates/elegant/border_video.png
```

**提示**: 后续可以使用图像编辑工具编辑 `border_video.png` 使其与图片边框有所区别。

## 启动服务

### 方式一：使用启动脚本（推荐）

```bash
./start_api.sh
```

### 方式二：使用 Docker Compose

```bash
docker-compose up --build
```

### 方式三：直接运行

```bash
# 重建镜像
docker build -t video-renderer-api .

# 启动服务
docker run --rm -it \
  --gpus all \
  --device /dev/dri:/dev/dri \
  -e NVIDIA_DRIVER_CAPABILITIES=all \
  -e NVIDIA_VISIBLE_DEVICES=all \
  -v $(pwd):/app \
  -p 8000:8000 \
  video-renderer-api
```

## 测试 API

### 1. 访问 API 文档

浏览器打开：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 2. 使用测试脚本

```bash
python3 test_api.py
```

### 3. 手动测试

#### 健康检查
```bash
curl http://localhost:8000/health
```

#### 列出模板
```bash
curl http://localhost:8000/api/templates
```

#### 创建渲染任务
```bash
curl -X POST http://localhost:8000/api/render \
  -H "Content-Type: application/json" \
  -d '{
    "template": "classic",
    "image_path": "/app/examples/cover.jpg",
    "video_paths": [
      "/app/examples/v1.mp4",
      "/app/examples/v2.mp4"
    ]
  }'
```

**响应示例：**
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "pending",
  "video_url": null,
  "message": "任务已创建，正在队列中等待处理",
  "created_at": "2025-11-27T10:30:00"
}
```

#### 查询任务状态
```bash
# 替换为实际的 task_id
curl http://localhost:8000/api/status/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

#### 查看视频
```bash
# 在浏览器中打开
http://localhost:8000/videos/a1b2c3d4-e5f6-7890-abcd-ef1234567890.mp4
```

## Python 客户端示例

```python
import requests
import time

# 创建任务
response = requests.post('http://localhost:8000/api/render', json={
    "template": "classic",
    "image_path": "/app/examples/cover.jpg",
    "video_paths": [
        "/app/examples/v1.mp4",
        "/app/examples/v2.mp4"
    ]
})

task = response.json()
task_id = task['task_id']
print(f"任务ID: {task_id}")

# 轮询状态
while True:
    response = requests.get(f'http://localhost:8000/api/status/{task_id}')
    status = response.json()
    
    print(f"状态: {status['status']} - 进度: {status['progress']*100:.1f}%")
    
    if status['status'] == 'completed':
        print(f"✅ 视频地址: {status['video_url']}")
        break
    elif status['status'] == 'failed':
        print(f"❌ 失败: {status['error']}")
        break
    
    time.sleep(3)
```

## 预期输出

### 渲染时长
- 1 图片 (8秒) + 2 视频 (16秒×2) + 1 转场 (2秒) = **42秒**

### 控制台日志
```
🎬 API渲染 - 模板: Classic
   图片: /app/examples/cover.jpg
   视频数量: 2
🚀 初始化 GPU 环境...
📝 初始化叠加层...
   ✓ 边框加载: templates/classic/border.png
   ✓ 边框加载: templates/classic/border_video.png
📦 加载转场效果...
   ✓ ai5.glsl
   ✓ ai3.glsl
   ✓ ai2.glsl
   共 3 个转场
🎥 启动编码器...
📂 开始渲染...
   🖼️  图片: 200 帧 (8.0秒)
   ⏳ 预读 /app/examples/v1.mp4... 就绪!
   ⏳ 预读 /app/examples/v2.mp4... 就绪!
   📹 视频 1/2: 350 帧
   ✨ 转场 1→2: ai5
   📹 视频 2/2: 400 帧
📊 总帧数: 1050 (42.0秒)
🎵 合成 BGM...
✅ 完成: outputs/a1b2c3d4-e5f6-7890-abcd-ef1234567890.mp4
```

## 验证结果

### 检查输出文件
```bash
ls -lh outputs/*.mp4
```

### 播放视频
```bash
# 使用 ffplay
ffplay outputs/xxx.mp4

# 或使用系统播放器
xdg-open outputs/xxx.mp4
```

### 验证时长
```bash
ffprobe -v error -show_entries format=duration \
  -of default=noprint_wrappers=1:nokey=1 \
  outputs/xxx.mp4
```

## 常见问题

### 1. 服务无法启动
```bash
# 检查端口占用
lsof -i:8000

# 检查 GPU
nvidia-smi

# 检查 Docker
docker ps
```

### 2. 渲染失败
- 检查文件路径是否正确（必须是容器内路径 `/app/...`）
- 检查边框文件是否存在
- 查看详细错误日志

### 3. 视频边框未生效
```bash
# 检查是否存在 border_video.png
ls templates/classic/border_video.png

# 如果不存在，将使用 border.png
```

## 下一步

1. ✅ 测试基本渲染功能
2. ✅ 验证图片和视频使用不同边框
3. 📝 根据需求自定义边框图片
4. 🎨 调整模板配置（字体、颜色等）
5. 🚀 部署到生产环境

## 相关文档

- [API_GUIDE.md](./API_GUIDE.md) - 完整 API 文档
- [README.md](./README.md) - 项目说明

---

**快速测试命令：**
```bash
# 1. 创建边框（如果需要）
cp templates/classic/border.png templates/classic/border_video.png

# 2. 启动服务
./start_api.sh

# 3. 新终端运行测试
python3 test_api.py
```
