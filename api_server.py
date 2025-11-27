"""
FastAPI HTTP 服务 - GPU 加速视频渲染

同步模式：直接返回视频URL字符串
"""

import os
from pathlib import Path
from typing import List
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, validator
import logging

from src.api_renderer import ApiVlogRenderer

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(title="GPU Video Renderer API", version="1.0.0")

# 输出目录配置
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

# 挂载静态文件服务
app.mount("/videos", StaticFiles(directory=str(OUTPUT_DIR)), name="videos")


class RenderRequest(BaseModel):
    """渲染请求模型"""

    template: str = Field(..., description="模板名称 (classic/modern/elegant)")
    image_path: str = Field(..., description="图片路径（本机目录路径）")
    video_paths: List[str] = Field(
        ..., min_items=1, max_items=5, description="视频路径列表（1-5个）"
    )

    @validator("image_path")
    def validate_image_path(cls, v):
        if not os.path.exists(v):
            raise ValueError(f"图片文件不存在: {v}")
        if not v.lower().endswith((".jpg", ".jpeg", ".png", ".bmp")):
            raise ValueError(f"不支持的图片格式: {v}")
        return v

    @validator("video_paths")
    def validate_video_paths(cls, v):
        for path in v:
            if not os.path.exists(path):
                raise ValueError(f"视频文件不存在: {path}")
            if not path.lower().endswith((".mp4", ".avi", ".mov", ".mkv")):
                raise ValueError(f"不支持的视频格式: {path}")
        return v


@app.post("/api/render", response_class=PlainTextResponse)
def render_video(request: RenderRequest):
    """
    渲染视频接口

    - **template**: 模板名称 (classic/modern/elegant)
    - **image_path**: 图片路径（容器内绝对路径，如 /app/examples/cover.jpg）
    - **video_paths**: 视频路径列表（1-5个容器内绝对路径）

    返回视频URL字符串（同步阻塞，需等待10-60秒）
    """
    # 按时间命名文件：年月日时分.mp4
    now = datetime.now()
    output_filename = (
        f"{now.year}{now.month:02d}{now.day:02d}{now.hour:02d}{now.minute:02d}.mp4"
    )
    output_path = OUTPUT_DIR / output_filename

    # 获取基础URL
    base_url = os.getenv("API_BASE_URL", "http://localhost:8001")

    try:
        logger.info(f"开始渲染: {output_filename} | 模板: {request.template}")

        # 同步渲染
        renderer = ApiVlogRenderer(
            template_name=request.template,
            image_path=request.image_path,
            video_paths=request.video_paths,
            output_file=str(output_path),
        )
        renderer.render()

        video_url = f"{base_url}/videos/{output_filename}"
        logger.info(f"渲染完成: {output_filename}")

        # 直接返回URL字符串
        return video_url

    except Exception as e:
        logger.error(f"渲染失败 {output_filename}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"渲染失败: {str(e)}")
