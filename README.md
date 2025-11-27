# GPU 视频渲染 API

基于 ModernGL + NVENC 的 GPU 加速视频渲染服务。

## 功能特性

- 🎨 支持多种模板风格（classic/modern/elegant）
- 🖼️ 图片 + 视频混合渲染
- 📝 自动字幕生成（打字机效果）
- 🎬 GPU 加速转场效果
- ⚡ NVENC 硬件编码

## 快速开始

### 1. 启动服务

```bash
docker compose up -d
```

服务将在 `http://localhost:8001` 启动。

### 2. 调用接口

**接口地址**: `POST http://localhost:8001/api/render`

**请求参数**:
```json
{
  "template": "classic",
  "image_path": "/app/examples/cover.jpg",
  "video_paths": [
    "/app/examples/v1.mp4",
    "/app/examples/v2.mp4"
  ]
}
```

**响应示例** (纯文本URL):
```
http://localhost:8001/videos/202511271430.mp4
```

视频文件按 `年月日时分.mp4` 格式命名（如：202511271430.mp4）。

### 3. 使用测试脚本

```bash
python3 test.py
```

## 视频规格

- **图片段**: 8秒，带字幕（打字机效果）
- **视频段**: 每个16秒
- **分辨率**: 1920x1080
- **帧率**: 25 FPS
- **编码**: H.264 (NVENC)
- **音频**: AAC 44.1kHz

## 配置管理

所有配置统一在 `config.yaml` 文件中管理：

### 全局渲染参数
```yaml
global:
  width: 1920              # 视频分辨率-宽度
  height: 1080             # 视频分辨率-高度
  fps: 25                  # 帧率
  image_duration: 8.0      # 图片持续时间（秒）
  video_duration: 16.0     # 每个视频持续时间（秒）
  transition_duration: 2.0 # 转场持续时间（秒）
```

### 可用模板

- `classic` - 经典风格，适合正式场合
- `modern` - 现代风格，适合年轻化场景
- `elegant` - 优雅风格，适合艺术展示

修改全局参数、模板配置或添加新模板，只需编辑根目录的 `config.yaml` 文件。

## 服务管理

```bash
# 启动
docker compose up -d

# 查看日志
docker compose logs -f

# 停止
docker compose stop

# 重启
docker compose restart

# 删除
docker compose down
```

## 注意事项

- 路径必须是**容器内路径**（如 `/app/examples/xxx.mp4`）
- 图片格式支持：jpg, jpeg, png, bmp
- 视频格式支持：mp4, avi, mov, mkv
- 视频数量：1-5个
- 渲染时间：约10-60秒（取决于视频数量）

## 环境要求

- Docker + Docker Compose
- NVIDIA GPU + 驱动
- nvidia-docker2
