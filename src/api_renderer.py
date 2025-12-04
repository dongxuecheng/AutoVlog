"""
API 专用渲染器 - 支持图片和视频混合渲染

特性：
- 图片持续 8 秒
- 每个视频持续 16 秒
- 图片使用独立边框
- 视频使用统一边框
"""

import numpy as np
import moderngl
from pathlib import Path
from PIL import Image

from src.config import TemplateConfig
from src.renderers import BorderRenderer, SubtitleRenderer
from src.shaders import (
    create_transition_shader,
    create_overlay_shader,
    load_transitions,
)
from src.video import VideoReader, create_encoder, merge_audio


class ApiVlogRenderer:
    """API 专用 Vlog 渲染器"""

    def __init__(
        self,
        template_name: str,
        image_path: str,
        video_paths: list,
        output_file: str = None,
    ):
        self.config = TemplateConfig(template_name)
        self.image_path = image_path
        self.video_paths = video_paths
        self.output_file = output_file or f"output_api_{template_name}.mp4"
        self.temp_file = f"temp_api_{template_name}_silent.mp4"

        # 从配置文件加载渲染参数
        self.WIDTH = self.config.global_config["width"]
        self.HEIGHT = self.config.global_config["height"]
        self.FPS = self.config.global_config["fps"]
        self.IMAGE_DURATION = self.config.global_config["image_duration"]
        self.VIDEO_DURATION = self.config.global_config["video_duration"]
        self.TRANSITION_DURATION = self.config.global_config["transition_duration"]

        # 计算帧数
        self.FRAME_SIZE = self.WIDTH * self.HEIGHT * 3
        self.IMAGE_FRAMES = int(self.IMAGE_DURATION * self.FPS)
        self.VIDEO_FRAMES = int(self.VIDEO_DURATION * self.FPS)
        self.TRANS_FRAMES = int(self.TRANSITION_DURATION * self.FPS)
        self.SOLO_FRAMES = self.VIDEO_FRAMES - self.TRANS_FRAMES

        print(f"🎬 API渲染 - 模板: {self.config.name}")
        print(f"   图片: {image_path}")
        print(f"   视频数量: {len(video_paths)}")

    def setup_gpu(self):
        """初始化 GPU 上下文和纹理"""
        print("🚀 初始化 GPU 环境...")
        self.ctx = moderngl.create_context(standalone=True, backend="egl")
        self.tex0 = self.ctx.texture((self.WIDTH, self.HEIGHT), 3)
        self.tex1 = self.ctx.texture((self.WIDTH, self.HEIGHT), 3)
        self.fbo = self.ctx.simple_framebuffer((self.WIDTH, self.HEIGHT), components=3)
        self.fbo.use()
        self.fbo.clear(0.0, 0.0, 0.0, 1.0)

    def setup_overlays(self):
        """初始化边框渲染系统（图片和视频使用不同边框）"""
        print("📝 初始化叠加层...")

        # 图片边框（使用模板配置的图片边框）
        image_border_path = self.config.border.get(
            "image_path"
        ) or self.config.border.get("path")
        self.image_border_renderer = BorderRenderer(
            image_border_path, self.WIDTH, self.HEIGHT
        )
        self.image_border_tex = self.ctx.texture((self.WIDTH, self.HEIGHT), 4)
        self.image_border_tex.write(self.image_border_renderer.get_texture_data())

        # 视频边框（使用模板配置的视频边框，如果不存在则回退到图片边框）
        video_border_path = self.config.border.get("video_path")
        if not video_border_path or not Path(video_border_path).exists():
            print(f"   ⚠️  video_path 未配置或文件不存在，使用图片边框")
            video_border_path = image_border_path

        self.video_border_renderer = BorderRenderer(
            video_border_path, self.WIDTH, self.HEIGHT
        )
        self.video_border_tex = self.ctx.texture((self.WIDTH, self.HEIGHT), 4)
        self.video_border_tex.write(self.video_border_renderer.get_texture_data())

        # 边框 FBO 和 Shader
        self.border_fbo = self.ctx.simple_framebuffer(
            (self.WIDTH, self.HEIGHT), components=3
        )
        self.border_prog = create_overlay_shader(self.ctx, "border")
        self.border_vao = self._create_vao(self.border_prog)
        self.border_prog["video_tex"].value = 0
        self.border_prog["overlay_tex"].value = 1

        # 临时纹理
        self.temp_tex = self.ctx.texture((self.WIDTH, self.HEIGHT), 3)

        # 字幕系统初始化
        self.subtitle_renderer = SubtitleRenderer(
            self.config.font["path"], self.config.font["size"], self.WIDTH, self.HEIGHT
        )
        self.subtitle_tex = self.ctx.texture((self.WIDTH, self.HEIGHT), 4)  # RGBA纹理
        self.subtitle_fbo = self.ctx.simple_framebuffer(
            (self.WIDTH, self.HEIGHT), components=3
        )
        self.subtitle_prog = create_overlay_shader(self.ctx, "subtitle")
        self.subtitle_vao = self._create_vao(self.subtitle_prog)
        self.subtitle_prog["video_tex"].value = 0
        self.subtitle_prog["overlay_tex"].value = 1

        # 用于存储边框后的临时帧
        self.border_temp_tex = self.ctx.texture((self.WIDTH, self.HEIGHT), 3)

    def _create_vao(self, program):
        """创建顶点数组对象（全屏四边形）"""
        vertices = np.array(
            [
                -1,
                -1,
                0,
                0,
                1,
                -1,
                1,
                0,
                -1,
                1,
                0,
                1,
                -1,
                1,
                0,
                1,
                1,
                -1,
                1,
                0,
                1,
                1,
                1,
                1,
            ],
            dtype="f4",
        )
        vbo = self.ctx.buffer(vertices)
        return self.ctx.vertex_array(program, [(vbo, "2f 2f", "in_vert", "in_text")])

    def render_frame_with_border(self, use_image_border=False, subtitle_text=None):
        """
        渲染一帧并叠加边框和字幕

        Args:
            use_image_border: True=使用图片边框，False=使用视频边框
            subtitle_text: 字幕文本，None表示不显示字幕
        """
        # 选择边框纹理
        border_tex = (
            self.image_border_tex if use_image_border else self.video_border_tex
        )

        # 步骤1: 边框叠加
        self.temp_tex.write(self.fbo.read(components=3))
        self.border_fbo.use()
        self.temp_tex.use(0)
        border_tex.use(1)
        self.border_vao.render()

        # 步骤2: 字幕叠加（如果有字幕）
        if subtitle_text:
            # 渲染字幕文字到纹理
            subtitle_data = self.subtitle_renderer.render_text(
                subtitle_text,
                color=tuple(self.config.font["color"]),
                outline_color=tuple(self.config.font["outline_color"]),
                outline_width=self.config.font["outline_width"],
            )
            self.subtitle_tex.write(subtitle_data)

            # 将边框结果叠加字幕
            self.border_temp_tex.write(self.border_fbo.read(components=3))
            self.subtitle_fbo.use()
            self.border_temp_tex.use(0)
            self.subtitle_tex.use(1)
            self.subtitle_vao.render()

            final_frame = self.subtitle_fbo.read(components=3)
        else:
            final_frame = self.border_fbo.read(components=3)

        # 恢复主 FBO 状态
        self.fbo.use()
        self.tex0.use(0)
        self.tex1.use(1)

        return final_frame

    def render(self):
        """主渲染循环"""
        self.setup_gpu()
        self.setup_overlays()

        # 加载转场效果
        transitions = load_transitions(self.config.transitions)

        # 创建编码器
        encoder = create_encoder(self.WIDTH, self.HEIGHT, self.FPS, self.temp_file)
        print("📂 开始渲染...")

        # 初始化着色器
        prog = create_transition_shader(self.ctx, transitions[0]["source"])
        vao = self._create_vao(prog)
        self.tex0.use(0)
        self.tex1.use(1)
        prog["tex0"].value = 0
        prog["tex1"].value = 1
        if "ratio" in prog:
            prog["ratio"].value = self.WIDTH / self.HEIGHT

        total_frames = 0

        # ========== 第一部分：渲染图片 (8秒，使用图片边框 + 字幕) ==========
        print(f"   🖼️  图片: {self.IMAGE_FRAMES} 帧 ({self.IMAGE_DURATION}秒)")

        # 使用BorderRenderer将图片复合到边框上
        position_config = self.config.config.get("image_position", {})
        composited_img_data = self.image_border_renderer.composite_image_on_border(
            self.image_path, position_config
        )
        print(
            f"   ✓ 图片已复合到边框 (位置: x={position_config.get('x')}, y={position_config.get('y')}, "
            f"区域: {position_config.get('width')}x{position_config.get('height')})"
        )

        # 生成字幕文本
        from datetime import datetime

        now = datetime.now()
        subtitle_template = self.config.subtitle.get("template", "")
        full_subtitle_text = subtitle_template.format(
            year=now.year, month=now.month, day=now.day
        )
        typewriter_speed = self.config.subtitle.get("typewriter_speed", 3)
        subtitle_duration = self.config.subtitle.get("duration", 6.0)
        subtitle_frames = int(subtitle_duration * self.FPS)

        print(f"   📝 字幕: {full_subtitle_text}")

        # 渲染图片帧（图片已经包含边框，只需添加字幕）
        for frame_idx in range(self.IMAGE_FRAMES):
            # 直接将复合后的图片写入纹理
            self.tex0.write(composited_img_data)

            # 计算字幕文本（打字机效果）
            subtitle_text = None
            if frame_idx < subtitle_frames:
                chars_to_show = (frame_idx // typewriter_speed) + 1
                subtitle_text = full_subtitle_text[:chars_to_show]

            # 只需叠加字幕（不再需要边框）
            if subtitle_text:
                # 渲染字幕到纹理
                subtitle_data = self.subtitle_renderer.render_text(
                    subtitle_text,
                    color=tuple(self.config.font["color"]),
                    outline_color=tuple(self.config.font["outline_color"]),
                    outline_width=self.config.font["outline_width"],
                )
                self.subtitle_tex.write(subtitle_data)

                # 叠加字幕
                self.temp_tex.write(composited_img_data)
                self.subtitle_fbo.use()
                self.temp_tex.use(0)
                self.subtitle_tex.use(1)
                self.subtitle_vao.render()
                final_frame = self.subtitle_fbo.read(components=3)

                # 恢复主FBO
                self.fbo.use()
            else:
                final_frame = composited_img_data

            encoder.stdin.write(final_frame)
            total_frames += 1

        # ========== 第二部分：图片到视频的转场 ==========
        print(f"   ✨ 转场: 图片→视频1", flush=True)

        # 加载第一个视频用于转场
        first_video_path = self.video_paths[0]
        first_vid = VideoReader(
            first_video_path,
            self.WIDTH,
            self.HEIGHT,
            self.FPS,
            self.FRAME_SIZE,
            self.VIDEO_DURATION,
        )

        # 选择转场效果
        transition = transitions[0]
        print(f"      使用转场: {transition['name']}", flush=True)

        # 创建转场着色器
        prog = create_transition_shader(self.ctx, transition["source"])
        vao = self._create_vao(prog)
        self.tex0.use(0)
        self.tex1.use(1)
        prog["tex0"].value = 0
        prog["tex1"].value = 1
        if "ratio" in prog:
            prog["ratio"].value = self.WIDTH / self.HEIGHT

        # 渲染转场帧
        for j in range(self.TRANS_FRAMES):
            # tex0: 图片（复合后的），tex1: 第一个视频的帧
            self.tex0.write(composited_img_data)
            self.tex1.write(first_vid.read_frame())
            prog["progress"].value = (j + 1) / self.TRANS_FRAMES

            self.fbo.use()
            self.tex0.use(0)
            self.tex1.use(1)
            vao.render()

            # 转场帧使用视频边框
            final_frame = self.render_frame_with_border(use_image_border=False)
            encoder.stdin.write(final_frame)
            total_frames += 1

        # ========== 第三部分：渲染视频序列 (每个16秒，使用视频边框) ==========
        current_vid = first_vid  # 使用已经加载的第一个视频

        for i, video_path in enumerate(self.video_paths):
            is_last = i == len(self.video_paths) - 1

            # 处理当前视频的加载
            if i == 0:
                # 第一个视频已经在转场时加载，已读取TRANS_FRAMES帧
                frames_to_play = (
                    self.SOLO_FRAMES
                    if not is_last
                    else (self.VIDEO_FRAMES - self.TRANS_FRAMES)
                )
            else:
                # 加载后续视频
                trim_duration = (
                    self.VIDEO_DURATION
                    if not is_last
                    else ((self.TRANS_FRAMES + self.VIDEO_FRAMES) / self.FPS + 1.0)
                )
                current_vid = VideoReader(
                    video_path,
                    self.WIDTH,
                    self.HEIGHT,
                    self.FPS,
                    self.FRAME_SIZE,
                    trim_duration,
                )
                frames_to_play = self.SOLO_FRAMES if not is_last else self.VIDEO_FRAMES

            print(f"   📹 视频 {i+1}/{len(self.video_paths)}: {frames_to_play} 帧")

            # 主体播放
            for frame_idx in range(frames_to_play):
                # 渲染视频帧
                self.tex0.write(current_vid.read_frame())
                prog["progress"].value = 0.0
                self.fbo.use()
                vao.render()

                # 叠加视频边框
                final_frame = self.render_frame_with_border(use_image_border=False)
                encoder.stdin.write(final_frame)
                total_frames += 1

            # 视频间转场
            if not is_last:
                # 加载下一个视频
                next_video_path = self.video_paths[i + 1]
                is_next_last = (i + 1) == len(self.video_paths) - 1
                trim_duration = (
                    self.VIDEO_DURATION
                    if not is_next_last
                    else ((self.TRANS_FRAMES + self.VIDEO_FRAMES) / self.FPS + 1.0)
                )

                next_vid = VideoReader(
                    next_video_path,
                    self.WIDTH,
                    self.HEIGHT,
                    self.FPS,
                    self.FRAME_SIZE,
                    trim_duration,
                )

                # 转场效果（图片→视频1用了transitions[0]，视频1→视频2用transitions[1]，依此类推）
                transition = transitions[(i + 1) % len(transitions)]
                print(f"   ✨ 转场 {i+1}→{i+2}: {transition['name']}")

                # 切换着色器
                prog = create_transition_shader(self.ctx, transition["source"])
                vao = self._create_vao(prog)
                self.tex0.use(0)
                self.tex1.use(1)
                prog["tex0"].value = 0
                prog["tex1"].value = 1
                if "ratio" in prog:
                    prog["ratio"].value = self.WIDTH / self.HEIGHT

                # 渲染转场帧
                for j in range(self.TRANS_FRAMES):
                    self.tex0.write(current_vid.read_frame())
                    self.tex1.write(next_vid.read_frame())
                    prog["progress"].value = (j + 1) / self.TRANS_FRAMES

                    self.fbo.use()
                    self.tex0.use(0)
                    self.tex1.use(1)
                    vao.render()

                    # 转场帧使用视频边框
                    final_frame = self.render_frame_with_border(use_image_border=False)
                    encoder.stdin.write(final_frame)
                    total_frames += 1

                current_vid.close()
                current_vid = next_vid
            else:
                # 最后一个视频，关闭
                current_vid.close()

        encoder.stdin.close()
        encoder.wait()

        print(f"📊 总帧数: {total_frames} ({total_frames/self.FPS:.1f}秒)")

        # 合并音频
        merge_audio(self.temp_file, self.config.bgm["path"], self.output_file)
        print(f"✅ 完成: {self.output_file}")
