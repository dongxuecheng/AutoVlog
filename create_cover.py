#!/usr/bin/env python3
"""
创建测试封面图片
"""
from PIL import Image, ImageDraw, ImageFont

# 创建图片
width, height = 1920, 1080
img = Image.new('RGB', (width, height), color='#1a1a2e')
draw = ImageDraw.Draw(img)

# 尝试使用系统字体
try:
    font_large = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 120)
    font_medium = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 60)
    font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 40)
except:
    print("⚠️  使用默认字体")
    font_large = ImageFont.load_default()
    font_medium = ImageFont.load_default()
    font_small = ImageFont.load_default()

# 绘制文字
# 标题
title = "Safety Training Center"
bbox = draw.textbbox((0, 0), title, font=font_large)
text_width = bbox[2] - bbox[0]
x = (width - text_width) // 2
draw.text((x, 300), title, fill='white', font=font_large)

# 副标题
subtitle = "长沙卷烟厂安全体验馆"
bbox = draw.textbbox((0, 0), subtitle, font=font_medium)
text_width = bbox[2] - bbox[0]
x = (width - text_width) // 2
draw.text((x, 500), subtitle, fill='#16c79a', font=font_medium)

# 日期
date = "2025"
bbox = draw.textbbox((0, 0), date, font=font_small)
text_width = bbox[2] - bbox[0]
x = (width - text_width) // 2
draw.text((x, 700), date, fill='white', font=font_small)

# 保存
output_path = 'examples/cover.jpg'
img.save(output_path, 'JPEG', quality=95)
print(f"✅ 封面图片已创建: {output_path}")
print(f"   尺寸: {width}x{height}")
