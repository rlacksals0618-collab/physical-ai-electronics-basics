"""manim 공통 스타일 — build/theme.py 색상과 맞춘다."""
from manim import config

# 색상 (build/theme.py 와 동일한 값)
BG = "#13203B"        # 영상 배경 (짙은 남색)
NAVY = "#1B2A4A"
YELLOW = "#FFC531"    # 강조 / 에너지
BLUE = "#4C9BFF"      # 전자
WHITE = "#F4F6FB"
GRAY = "#8A97B0"
METAL = "#B9C3D6"     # 전선
RED = "#FF6B6B"

FONT = "Noto Sans KR"

config.background_color = BG
config.pixel_width = 1920
config.pixel_height = 1080
config.frame_rate = 30
