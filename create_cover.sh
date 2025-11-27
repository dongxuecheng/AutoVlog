#!/bin/bash
# 创建测试用的封面图片

echo "创建测试封面图片..."

# 检查 ImageMagick 是否安装
if ! command -v convert &> /dev/null; then
    echo "❌ ImageMagick 未安装"
    echo "   Ubuntu: sudo apt install imagemagick"
    exit 1
fi

# 创建示例封面图片
convert -size 1920x1080 \
    xc:'#1a1a2e' \
    -gravity center \
    -pointsize 120 \
    -fill white \
    -annotate +0-200 '安全体验馆' \
    -pointsize 60 \
    -fill '#16c79a' \
    -annotate +0-50 'SAFETY TRAINING CENTER' \
    -pointsize 40 \
    -fill white \
    -annotate +0+100 '长沙卷烟厂' \
    examples/cover.jpg

if [ -f examples/cover.jpg ]; then
    echo "✅ 封面图片已创建: examples/cover.jpg"
    ls -lh examples/cover.jpg
else
    echo "❌ 创建失败"
    exit 1
fi
