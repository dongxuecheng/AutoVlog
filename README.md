# OpenGL 视频转场渲染器

使用 ModernGL + FFmpeg + GL Transitions 创建专业视频转场效果。

## 项目结构

```
opengl-demo/
├── render.py              # 主渲染脚本
├── transitions/           # 转场效果目录
│   ├── README.md         # 转场效果说明
│   ├── fade.glsl         # 淡入淡出效果
│   └── stereo-viewer.glsl # 立体查看器效果
└── examples/             # 示例视频文件
    ├── v1.mp4 - v6.mp4   # 输入视频
    └── bgm.mp3           # 背景音乐
```

## 使用方法

### 1. 下载转场效果

访问 [GL Transitions](https://gl-transitions.com/) 浏览数百种转场效果：

1. 选择喜欢的转场效果
2. 点击 "View Source" 查看源代码
3. 复制完整的 GLSL 代码
4. 保存为 `.glsl` 文件到 `transitions/` 目录

### 2. 配置转场列表

编辑 `render.py` 中的 `TRANSITION_FILES` 列表：

```python
TRANSITION_FILES = [
    "transitions/fade.glsl",
    "transitions/wipeleft.glsl",
    "transitions/circle.glsl",
    # 添加更多转场...
]
```

**转场使用规则**：
- 转场按顺序循环使用
- 如果有5个转场，6个视频，则：转场1→淡入淡出，转场2→擦除左侧...转场5→圆形，转场6→淡入淡出（循环）
- 可以重复添加同一个转场文件来增加其使用频率

### 3. 配置视频参数

```python
# 视频文件列表
INPUT_FILES = [f"examples/v{i}.mp4" for i in range(1, 7)]

# 背景音乐
BGM_FILE = "examples/bgm.mp3"

# 输出文件
OUTPUT_FINAL = "final_vlog.mp4"

# 渲染参数
WIDTH, HEIGHT = 1920, 1080  # 分辨率
FPS = 25                     # 帧率
CLIP_DURATION = 8.0         # 每个片段时长（秒）
TRANSITION_DURATION = 2.0   # 转场时长（秒）
```

### 4. 运行渲染

```bash
docker run --rm -it \
  --gpus all \
  --device /dev/dri:/dev/dri \
  -e NVIDIA_DRIVER_CAPABILITIES=all \
  -e NVIDIA_VISIBLE_DEVICES=all \
  -v $(pwd):/app \
  my-gl-video \
  python3 render.py
```

## 转场效果推荐

### 简单过渡
- **fade** - 淡入淡出（最常用）
- **dissolve** - 溶解效果
- **crosswarp** - 交叉扭曲

### 擦除效果
- **wipeleft/wiperight/wipeup/wipedown** - 四向擦除
- **directionalwipe** - 方向擦除
- **radialwipe** - 径向擦除

### 几何效果
- **circle** - 圆形扩展
- **squares** - 方块效果
- **hexagonalize** - 六边形化

### 创意效果
- **glitch** - 故障效果
- **kaleidoscope** - 万花筒
- **mosaic** - 马赛克

### 3D效果
- **cube** - 立方体翻转
- **page-curl** - 翻页效果
- **stereo-viewer** - 立体查看器（ViewMaster）

## 输出信息

渲染过程会显示详细信息：

```
🚀 初始化 GPU 环境 (EGL)...
📦 加载转场效果...
   ✓ fade.glsl
   ✓ stereo-viewer.glsl
   共加载 2 个转场效果
🎥 启动 FFmpeg 编码器...
📂 开始渲染处理...
   📹 渲染视频 1/6: 149 帧
   ✨ 转场: 1 -> 2 (使用: fade)
   📹 渲染视频 2/6: 150 帧
   ✨ 转场: 2 -> 3 (使用: stereo-viewer)
   ...
🎵 合成 BGM...
✅ 完成: final_vlog.mp4
```

## 技术细节

### 帧数计算
- **非最后视频**: `SOLO_FRAMES = CLIP_FRAMES - TRANS_FRAMES` 
  - 例：8秒片段 - 2秒转场 = 6秒主体播放
- **最后视频**: 完整的 `CLIP_FRAMES`（无后续转场）

### 时长计算
对于6个视频：
```
视频1: 6秒
转场1: 2秒
视频2: 6秒
转场2: 2秒
...
视频6: 8秒
-------------------
总计: 约48秒
```

### GPU加速
- 使用 NVIDIA NVENC 硬件编码器
- ModernGL 在 GPU 上渲染转场效果
- 实时处理，速度快

## 故障排除

### 找不到转场文件
```
✗ 找不到文件: transitions/xxx.glsl
```
检查文件路径和文件名是否正确。

### 转场效果不显示
- 确保转场 GLSL 文件包含 `vec4 transition(vec2 uv)` 函数
- 检查是否有语法错误

### EOF警告
```
⚠️ 警告: 视频 6 在第 175/200 帧处EOF
```
视频源文件太短，代码会自动使用最后一帧填充。

## 许可证

- 项目代码: MIT
- GL Transitions: 各转场效果有各自的许可证，请查看源文件头部
