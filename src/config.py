"""
配置加载模块 - 负责加载和验证模板配置
"""

import yaml
import os
from pathlib import Path
from datetime import datetime


class TemplateConfig:
    """模板配置类"""

    def __init__(self, template_name: str):
        self.template_name = template_name
        self.config_path = Path("config.yaml")
        self.config = self._load_config(template_name)
        self.global_config = self._load_global_config()
        self._validate_config()

    def _load_config(self, template_name: str) -> dict:
        """加载 YAML 配置文件并提取指定模板配置"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"全局配置文件不存在: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            all_configs = yaml.safe_load(f)

        if "templates" not in all_configs:
            raise ValueError("配置文件格式错误：缺少 'templates' 节点")

        if template_name not in all_configs["templates"]:
            available = list(all_configs["templates"].keys())
            raise ValueError(
                f"模板 '{template_name}' 不存在\n" f"可用模板: {available}"
            )

        return all_configs["templates"][template_name]

    def _load_global_config(self) -> dict:
        """加载全局渲染参数配置"""
        with open(self.config_path, "r", encoding="utf-8") as f:
            all_configs = yaml.safe_load(f)

        # 返回全局配置，如果不存在则返回默认值
        return all_configs.get(
            "global",
            {
                "width": 1920,
                "height": 1080,
                "fps": 25,
                "image_duration": 8.0,
                "video_duration": 16.0,
                "transition_duration": 2.0,
            },
        )

    def _validate_config(self):
        """验证配置文件完整性"""
        required_keys = ["border", "bgm", "transitions", "font", "subtitle"]
        missing = [key for key in required_keys if key not in self.config]
        if missing:
            raise ValueError(f"配置文件缺少必要字段: {missing}")

        # 验证文件路径 - 支持新的 image_path/video_path 以及旧的 path
        border_config = self.config["border"]
        image_border = border_config.get("image_path") or border_config.get("path")
        if image_border and not os.path.exists(image_border):
            print(f"⚠️  警告: 图片边框文件不存在: {image_border}")

        video_border = border_config.get("video_path")
        if video_border and not os.path.exists(video_border):
            print(f"⚠️  警告: 视频边框文件不存在: {video_border}")

        bgm_path = self.config["bgm"]["path"]
        if not os.path.exists(bgm_path):
            print(f"⚠️  警告: BGM 文件不存在: {bgm_path}")

        font_path = self.config["font"]["path"]
        if not os.path.exists(font_path):
            raise FileNotFoundError(f"字体文件不存在: {font_path}")

    @staticmethod
    def list_available_templates() -> list:
        """列出所有可用模板"""
        config_path = Path("config.yaml")
        if not config_path.exists():
            return []

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                all_configs = yaml.safe_load(f)
            return list(all_configs.get("templates", {}).keys())
        except Exception:
            return []

    def get_subtitle_text(self) -> str:
        """生成字幕文本（带日期）"""
        now = datetime.now()
        template = self.config["subtitle"]["template"]
        return template.format(year=now.year, month=now.month, day=now.day)

    def __getattr__(self, name):
        """便捷访问配置项"""
        if name in self.config:
            return self.config[name]
        raise AttributeError(f"配置项 '{name}' 不存在")

    def __repr__(self):
        return f"TemplateConfig('{self.template_name}')"
