"""
FastAPI HTTP 服务 - GPU 加速视频渲染

同步模式：直接返回视频URL字符串
"""

import os
from pathlib import Path
from typing import List
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
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


# 自定义异常处理器：修复包含二进制数据和异常对象的验证错误
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    自定义请求验证异常处理器

    解决问题：
    1. 验证错误中包含二进制数据（如上传的文件）时，FastAPI默认的错误序列化
       会尝试将bytes解码为UTF-8，导致UnicodeDecodeError
    2. 验证错误的ctx中包含异常对象，无法被JSON序列化

    解决方案：递归清理错误信息，将所有不可序列化的对象转换为字符串
    """
    logger.info(f"🔧 自定义异常处理器被调用 - 错误数量: {len(exc.errors())}")

    def make_serializable(obj):
        """递归将对象转换为可JSON序列化的格式"""
        if isinstance(obj, bytes):
            # bytes转换为简短的十六进制预览
            preview = obj[:20].hex() if len(obj) > 20 else obj.hex()
            return f"<binary data: {preview}{'...' if len(obj) > 20 else ''}>"
        elif isinstance(obj, Exception):
            # 异常对象转换为字符串
            return f"{type(obj).__name__}: {str(obj)}"
        elif isinstance(obj, dict):
            # 递归处理字典
            return {k: make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            # 递归处理列表和元组
            return [make_serializable(item) for item in obj]
        elif isinstance(obj, (str, int, float, bool, type(None))):
            # 基本类型直接返回
            return obj
        else:
            # 其他对象转换为字符串表示
            return str(obj)

    errors = []
    for error in exc.errors():
        # 递归清理整个错误字典
        clean_error = make_serializable(error)
        errors.append(clean_error)

    return JSONResponse(
        status_code=422,
        content={"detail": errors},
    )


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
