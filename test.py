#!/usr/bin/env python3
"""
简单测试脚本 - 调用视频渲染API
"""
import requests

API_URL = "http://localhost:8001/api/render"

# 渲染请求
data = {
    "template": "classic",
    "image_path": "/app/examples/cover.jpg",
    "video_paths": ["/app/examples/v1.mp4", "/app/examples/v2.mp4"],
}

print("🎬 发送渲染请求...")
print(f"   模板: {data['template']}")
print(f"   图片: {data['image_path']}")
print(f"   视频: {len(data['video_paths'])} 个")
print()

response = requests.post(API_URL, json=data)

if response.status_code == 200:
    video_url = response.text  # 直接返回URL字符串
    print("✅ 渲染成功！")
    print(f"   视频地址: {video_url}")
else:
    print(f"❌ 渲染失败: {response.status_code}")
    print(f"   错误: {response.text}")
