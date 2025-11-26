import time
import subprocess
import numpy as np
import moderngl
import ffmpeg
import os
import sys
from pathlib import Path

# ================= 用户配置区域 =================

# 转场效果文件列表（按顺序使用，会自动循环）
TRANSITION_FILES = [
    "transitions/chromatic-rift.glsl",
    "transitions/prismatic-veils.glsl",
    "transitions/kinetic-lattice.glsl",
    # "transitions/inverted-page-curl.glsl",
    # "transitions/mosaic.glsl",
    # "transitions/perlin.glsl",
    # "transitions/stereo-viewer.glsl",
]


# 你的视频文件列表
INPUT_FILES = [f"examples/v{i}.mp4" for i in range(1, 7)]
BGM_FILE = "examples/bgm.mp3"
OUTPUT_TEMP = "temp_video_silent.mp4"
OUTPUT_FINAL = "final_vlog.mp4"

WIDTH, HEIGHT = 1920, 1080
FPS = 25
CLIP_DURATION = 8.0
TRANSITION_DURATION = 2.0

# ========================================================
FRAME_SIZE = WIDTH * HEIGHT * 3
CLIP_FRAMES = int(CLIP_DURATION * FPS)
TRANS_FRAMES = int(TRANSITION_DURATION * FPS)
SOLO_FRAMES = CLIP_FRAMES - TRANS_FRAMES


class VideoReader:
    def __init__(self, filename, is_last=False):
        self.filename = filename
        self.last_valid_frame = None
        self.eof_reached = False
        self.frames_read = 0
        self.is_last = is_last

        # 构建 FFmpeg 读取命令
        # 1. -ss 0 放在最前面，确保从文件物理头部开始寻找
        # 2. setpts=PTS-STARTPTS 强制把第一帧时间戳归零
        # 3. 最后一个视频需要：转场时被消耗的TRANS_FRAMES + 主体播放的CLIP_FRAMES + 缓冲
        if is_last:
            # 最后一个视频：转场50帧 + 主体200帧 + 缓冲 = 250+缓冲帧
            trim_duration = (TRANS_FRAMES + CLIP_FRAMES) / FPS + 1.0  # +1秒缓冲
        else:
            trim_duration = CLIP_DURATION

        self.process = (
            ffmpeg.input(filename, ss=0)
            .filter("setpts", "PTS-STARTPTS")
            .filter("scale", WIDTH, HEIGHT)
            .filter("fps", fps=FPS, round="up")
            .trim(duration=trim_duration)
            .output("pipe:", format="rawvideo", pix_fmt="rgb24")
            .run_async(pipe_stdout=True, quiet=True)
        )

        # 核心修改：移除超时逻辑，强制阻塞读取第一帧
        # 即使 FFmpeg 需要 10秒 才能吐出第一帧，这里也会死等
        # 绝不产生黑屏
        self.preload_first_frame()

    def preload_first_frame(self):
        print(f"   ⏳ 正在预读 {self.filename}...", end="", flush=True)

        # 这是一个阻塞读取，会一直等到填满 FRAME_SIZE 个字节为止
        # 除非进程崩溃(EOF)，否则不会返回空
        in_bytes = self.process.stdout.read(FRAME_SIZE)

        if len(in_bytes) == FRAME_SIZE:
            self.first_frame_buffer = in_bytes
            self.last_valid_frame = in_bytes
            print(" 就绪!")
        else:
            # 只有当文件真的是坏的/空的，才会报错
            print(" 失败! (无法读取数据)")
            self.first_frame_buffer = None
            # 这里可以抛出异常，或者用全黑兜底（但此时是因为文件真坏了）
            self.last_valid_frame = bytes([0] * FRAME_SIZE)

    def read_frame(self):
        # 优先消耗预读的那一帧
        if hasattr(self, "first_frame_buffer") and self.first_frame_buffer:
            data = self.first_frame_buffer
            self.first_frame_buffer = None
            self.frames_read += 1
            return data

        # 正常读取
        in_bytes = self.process.stdout.read(FRAME_SIZE)

        if len(in_bytes) == FRAME_SIZE:
            self.last_valid_frame = in_bytes
            self.frames_read += 1
            return in_bytes
        else:
            # 视频结束，返回最后一帧
            self.eof_reached = True
            return (
                self.last_valid_frame
                if self.last_valid_frame
                else bytes([0] * FRAME_SIZE)
            )

    def close(self):
        if self.process:
            self.process.stdout.close()
            try:
                self.process.wait(timeout=0.1)
            except:
                pass


def load_transition(filepath):
    """加载转场效果GLSL文件"""
    with open(filepath, "r") as f:
        return f.read()


def create_shader_program(ctx, transition_source):
    """创建shader程序"""
    import re

    # 检查转场源码中是否已经**定义**了这些函数（不是仅仅使用）
    # 匹配函数定义模式: vec4 getFromColor(...) 或 float rand(...)
    has_getFromColor_def = bool(
        re.search(r"\bvec4\s+getFromColor\s*\(", transition_source)
    )
    has_getToColor_def = bool(re.search(r"\bvec4\s+getToColor\s*\(", transition_source))
    has_rand_def = bool(
        re.search(r"\bfloat\s+rand\s*\(", transition_source, re.IGNORECASE)
    )

    # 只在转场源码中没有定义时才添加这些函数
    helper_functions = ""
    if not has_getFromColor_def:
        helper_functions += (
            "vec4 getFromColor(vec2 uv) { return texture(tex0, uv); }\n        "
        )
    if not has_getToColor_def:
        helper_functions += (
            "vec4 getToColor(vec2 uv) { return texture(tex1, uv); }\n        "
        )
    if not has_rand_def:
        helper_functions += "float rand(vec2 co) { return fract(sin(dot(co.xy ,vec2(12.9898,78.233))) * 43758.5453); }\n        "

    full_fragment_shader = f"""
        #version 330
        uniform sampler2D tex0;
        uniform sampler2D tex1;
        uniform float progress;
        uniform float ratio;
        in vec2 v_text;
        out vec4 f_color;

        {helper_functions}
        {transition_source}

        void main() {{
            if (progress <= 0.0) {{ f_color = texture(tex0, v_text); }} 
            else if (progress >= 1.0) {{ f_color = texture(tex1, v_text); }} 
            else {{ f_color = transition(v_text); }}
        }}
    """

    prog = ctx.program(
        vertex_shader="""#version 330
        in vec2 in_vert; in vec2 in_text; out vec2 v_text;
        void main() { gl_Position = vec4(in_vert, 0.0, 1.0); v_text = in_text; }""",
        fragment_shader=full_fragment_shader,
    )
    return prog


def main():
    print("🚀 初始化 GPU 环境 (EGL)...")
    try:
        ctx = moderngl.create_context(standalone=True, backend="egl")
    except:
        ctx = moderngl.create_context(standalone=True)

    tex0 = ctx.texture((WIDTH, HEIGHT), 3)
    tex1 = ctx.texture((WIDTH, HEIGHT), 3)
    fbo = ctx.simple_framebuffer((WIDTH, HEIGHT), components=3)
    fbo.use()

    # --- 加载所有转场效果 ---
    print(f"📦 加载转场效果...")
    transitions = []
    for trans_file in TRANSITION_FILES:
        if os.path.exists(trans_file):
            trans_source = load_transition(trans_file)
            transitions.append({"name": Path(trans_file).stem, "source": trans_source})
            print(f"   ✓ {Path(trans_file).name}")
        else:
            print(f"   ✗ 找不到文件: {trans_file}")

    if not transitions:
        print("❌ 错误: 没有加载到任何转场效果！")
        return

    print(f"   共加载 {len(transitions)} 个转场效果")
    # --- 准备顶点数据 ---
    vertices = np.array(
        [-1, -1, 0, 0, 1, -1, 1, 0, -1, 1, 0, 1, -1, 1, 0, 1, 1, -1, 1, 0, 1, 1, 1, 1],
        dtype="f4",
    )
    vertex_buffer = ctx.buffer(vertices)

    # --- 编码器 (NVENC) ---
    print("🎥 启动 FFmpeg 编码器...")
    encoder = (
        ffmpeg.input(
            "pipe:", format="rawvideo", pix_fmt="rgb24", s=f"{WIDTH}x{HEIGHT}", r=FPS
        )
        .output(
            OUTPUT_TEMP,
            vcodec="h264_nvenc",
            pix_fmt="yuv420p",
            bitrate="15M",
            preset="p4",  # 最快编码速度
            rc="cbr",  # 恒定码率模式
            **{
                "rc-lookahead": "32",
                "spatial-aq": "1",
                "temporal-aq": "1",
            },  # 启用空间和时间自适应量化
        )
        .overwrite_output()
        .run_async(pipe_stdin=True, quiet=True)
    )

    print(f"📂 开始渲染处理...")

    # 关键修复：在开始渲染前清除framebuffer，避免黑屏
    fbo.clear(0.0, 0.0, 0.0, 1.0)

    # 创建shader程序并设置静态uniform
    current_transition_idx = 0
    prog = create_shader_program(ctx, transitions[0]["source"])
    vao = ctx.vertex_array(prog, [(vertex_buffer, "2f 2f", "in_vert", "in_text")])

    # 一次性设置静态uniform
    tex0.use(0)
    prog["tex0"].value = 0
    tex1.use(1)
    prog["tex1"].value = 1
    if "ratio" in prog:
        prog["ratio"].value = WIDTH / HEIGHT

    total_encoded_frames = 0  # 统计写入编码器的帧数
    current_vid = None

    for i in range(len(INPUT_FILES)):
        is_last_clip = i == len(INPUT_FILES) - 1

        # 加载当前视频（如果还没加载）
        if current_vid is None:
            current_vid = VideoReader(INPUT_FILES[i], is_last=is_last_clip)

        next_vid = None
        if not is_last_clip:
            # 预加载下一个视频
            next_vid = VideoReader(
                INPUT_FILES[i + 1], is_last=(i + 1 == len(INPUT_FILES) - 1)
            )

        # A. 主体播放
        frames_to_play = CLIP_FRAMES if is_last_clip else SOLO_FRAMES

        print(f"   📹 渲染视频 {i+1}/{len(INPUT_FILES)}: {frames_to_play} 帧")

        for frame_idx in range(frames_to_play):
            raw = current_vid.read_frame()

            # 检测是否已EOF，给出警告
            if current_vid.eof_reached and frame_idx < frames_to_play - 1:
                print(
                    f"   ⚠️  警告: 视频 {i+1} 在第 {frame_idx}/{frames_to_play} 帧处EOF，剩余帧使用最后一帧"
                )

            tex0.write(raw)
            prog["progress"].value = 0.0
            vao.render()
            encoder.stdin.write(fbo.read(components=3))
            total_encoded_frames += 1
        # B. 转场播放
        if not is_last_clip and next_vid:
            # 选择转场效果（循环使用）
            transition = transitions[i % len(transitions)]
            print(f"   ✨ 转场: {i+1} -> {i+2} (使用: {transition['name']})")

            # 如果转场效果改变，重新创建shader程序
            if i % len(transitions) != current_transition_idx:
                current_transition_idx = i % len(transitions)
                prog = create_shader_program(ctx, transition["source"])
                vao = ctx.vertex_array(
                    prog, [(vertex_buffer, "2f 2f", "in_vert", "in_text")]
                )
                # 设置静态uniform
                tex0.use(0)
                prog["tex0"].value = 0
                tex1.use(1)
                prog["tex1"].value = 1
                if "ratio" in prog:
                    prog["ratio"].value = WIDTH / HEIGHT

            for j in range(TRANS_FRAMES):
                raw_c = current_vid.read_frame()
                raw_n = next_vid.read_frame()

                tex0.write(raw_c)
                tex1.write(raw_n)

                # 只更新变化的uniform
                prog["progress"].value = (j + 1) / TRANS_FRAMES
                vao.render()
                encoder.stdin.write(fbo.read(components=3))
                total_encoded_frames += 1

            current_vid.close()
            current_vid = next_vid
        else:
            current_vid.close()

    encoder.stdin.close()
    encoder.wait()

    print(
        f"📊 总共写入编码器: {total_encoded_frames} 帧 ({total_encoded_frames/FPS:.2f}秒)"
    )

    # --- BGM 合成优化 ---
    if os.path.exists(BGM_FILE):
        print("🎵 合成 BGM...")
        # 增加 -ss 0 到音频流，防止音频有封面图导致的偏移
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                OUTPUT_TEMP,
                "-ss",
                "0",
                "-stream_loop",
                "-1",
                "-i",
                BGM_FILE,
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",  # 明确指定流映射
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-shortest",
                "-fflags",
                "+genpts",
                OUTPUT_FINAL,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        os.remove(OUTPUT_TEMP)
        print(f"✅ 完成: {OUTPUT_FINAL}")
    else:
        os.rename(OUTPUT_TEMP, OUTPUT_FINAL)


if __name__ == "__main__":
    main()
