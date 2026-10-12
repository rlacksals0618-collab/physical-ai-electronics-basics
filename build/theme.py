"""덱 공통 디자인 상수 — visuals/manim/style.py 색상과 맞춘다."""
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

SLIDE_W, SLIDE_H = Inches(13.333), Inches(7.5)
MARGIN = Inches(0.6)

BG = RGBColor(0x13, 0x20, 0x3B)       # 배경 (manim BG와 동일)
CARD = RGBColor(0x1C, 0x2C, 0x4D)     # 카드/패널
WHITE = RGBColor(0xF4, 0xF6, 0xFB)
MUTED = RGBColor(0xA9, 0xB4, 0xCB)
YELLOW = RGBColor(0xFF, 0xC5, 0x31)   # 강조
BLUE = RGBColor(0x4C, 0x9B, 0xFF)     # 전자

FONT = "맑은 고딕"

TITLE_SIZE = Pt(34)
BODY_SIZE = Pt(20)
CAPTION_SIZE = Pt(22)
RED = RGBColor(0xFF, 0x6B, 0x6B)      # 경고
