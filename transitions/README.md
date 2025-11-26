# GL Transitions

这个目录存放从 [gl-transitions.com](https://gl-transitions.com/) 下载的转场效果文件。

## 使用方法

1. 从 https://gl-transitions.com/ 浏览并下载你喜欢的转场效果
2. 将 `.glsl` 文件放到这个目录
3. 在 `render.py` 中配置 `TRANSITION_FILES` 列表

## 已包含的转场

- `fade.glsl` - 简单的淡入淡出
- `stereo-viewer.glsl` - 立体查看器效果（ViewMaster风格）

## 注意事项

- 所有转场文件必须包含 `vec4 transition(vec2 uv)` 函数
- 转场效果会按顺序循环使用
- 如果转场数量少于视频数量，会自动循环
