# 📦 模板资源准备指南

## 目录结构

```
templates/
├── classic/          # 经典模板
│   ├── config.yaml   ✅ (已提交)
│   ├── .gitkeep      ✅ (已提交)
│   ├── border.png    ⚠️  (需要准备)
│   └── bgm.mp3       ⚠️  (需要准备)
├── modern/           # 现代模板
│   ├── config.yaml   ✅
│   ├── .gitkeep      ✅
│   ├── border.png    ⚠️
│   └── bgm.mp3       ⚠️
└── elegant/          # 优雅模板
    ├── config.yaml   ✅
    ├── .gitkeep      ✅
    ├── border.png    ⚠️
    └── bgm.mp3       ⚠️

fonts/
├── .gitkeep          ✅ (已提交)
├── NotoSansSC-Bold.otf      ⚠️ (需要准备)
├── NotoSansSC-Medium.otf    ⚠️
└── NotoSansSC-Light.otf     ⚠️
```

## 🎨 边框图片要求

**文件名**: `border.png`  
**尺寸**: 1920 x 1080 像素  
**格式**: PNG (支持透明通道)  
**要求**: 中间区域必须是透明的（Alpha = 0）

### 制作方法
1. 使用 Photoshop/GIMP 创建 1920x1080 画布
2. 设置背景为透明
3. 在边缘绘制装饰性边框
4. 保留中间区域透明（视频显示区）
5. 导出为 PNG 格式

### 参考尺寸
- 边框宽度: 推荐 50-100 像素
- 透明区域: 建议保留 1720x880 中心区域

## 🎵 背景音乐要求

**文件名**: `bgm.mp3`  
**格式**: MP3  
**时长**: 建议 > 60 秒（会自动循环）  
**码率**: 128-320 kbps  
**采样率**: 44.1 kHz

### 风格建议
- **Classic**: 轻音乐、钢琴曲、古典乐
- **Modern**: 电子音乐、流行轻快曲风
- **Elegant**: 爵士乐、弦乐、舒缓曲目

## 🔤 字体文件要求

**格式**: `.otf` 或 `.ttf`  
**推荐字体**: 
- Noto Sans SC (支持中文)
- 思源黑体
- 阿里巴巴普惠体

### 下载地址
- Noto Sans SC: https://fonts.google.com/noto/specimen/Noto+Sans+SC
- 思源黑体: https://github.com/adobe-fonts/source-han-sans

## 📝 快速设置步骤

### 1. 准备字体文件
```bash
cd /home/xcd/opengl-demo/fonts
# 下载并放置字体文件
wget https://github.com/notofonts/noto-cjk/releases/download/Sans2.004/06_NotoSansSC.zip
unzip 06_NotoSansSC.zip
mv OTF/*.otf ./
```

### 2. 准备模板资源
```bash
# Classic 模板
cd /home/xcd/opengl-demo/templates/classic
# 复制或创建 border.png (1920x1080)
# 复制或下载 bgm.mp3

# Modern 模板
cd /home/xcd/opengl-demo/templates/modern
# 复制或创建 border.png
# 复制或下载 bgm.mp3

# Elegant 模板
cd /home/xcd/opengl-demo/templates/elegant
# 复制或创建 border.png
# 复制或下载 bgm.mp3
```

### 3. 验证资源
```bash
cd /home/xcd/opengl-demo
python3 render_v2.py --list
# 应该显示所有三个模板无警告
```

## 🚀 快速复制（临时方案）

如果三个模板暂时使用相同资源：

```bash
cd /home/xcd/opengl-demo

# 从 border/ 复制边框（如果存在）
cp border/border.png templates/classic/
cp border/border.png templates/modern/
cp border/border.png templates/elegant/

# 从 examples/ 复制音乐（如果存在）
cp examples/bgm.mp3 templates/classic/
cp examples/bgm.mp3 templates/modern/
cp examples/bgm.mp3 templates/elegant/
```

## ⚠️ 注意事项

1. **版权问题**: 确保音乐和字体有使用权限
2. **文件大小**: 避免过大的音频文件（推荐 < 10MB）
3. **边框设计**: 避免边框过于花哨影响视频主体
4. **字体兼容**: 确保字体支持所需的中文字符

## 🔍 验证清单

- [ ] `fonts/*.otf` 文件存在且可读
- [ ] `templates/*/border.png` 尺寸正确 (1920x1080)
- [ ] `templates/*/bgm.mp3` 格式正确
- [ ] 运行 `render_v2.py --list` 无错误
- [ ] 测试渲染一个模板成功

## 📚 相关文档

- [TEMPLATE_GUIDE.md](./TEMPLATE_GUIDE.md) - 模板开发完整指南
- [README.md](./README.md) - 项目说明
- 配置文件: `templates/*/config.yaml`
