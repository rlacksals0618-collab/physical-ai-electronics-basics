"""p01_electron_flow — 스위치를 닫기 전엔 전자가 제자리에서 꿈틀, 닫으면 한 방향으로 흐른다."""
import sys
from pathlib import Path

import numpy as np
from manim import *

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from style import BG, BLUE, FONT, GRAY, METAL, WHITE, YELLOW  # noqa: E402

# 회로(둥근 사각형 고리) 치수
W, H, R = 10.0, 4.6, 0.8
CENTER = np.array([0.0, -0.55, 0.0])
LV, LH, ARC = H - 2 * R, W - 2 * R, PI * R / 2
PERIM = 2 * LV + 2 * LH + 4 * ARC
SWITCH_GAP = 0.65  # 스위치 구간(윗변 중앙) 반폭


def loop_point(s):
    """왼쪽 변 중앙에서 출발해 반시계 방향(전지 − → 회로 → 전지 +)으로 s만큼 간 지점."""
    s %= PERIM
    hw, hh = W / 2, H / 2
    segs = [
        ("line", (-hw, 0), (-hw, -hh + R), LV / 2),
        ("arc", (-hw + R, -hh + R), (PI, 1.5 * PI), ARC),
        ("line", (-hw + R, -hh), (hw - R, -hh), LH),
        ("arc", (hw - R, -hh + R), (1.5 * PI, 2 * PI), ARC),
        ("line", (hw, -hh + R), (hw, hh - R), LV),
        ("arc", (hw - R, hh - R), (0, 0.5 * PI), ARC),
        ("line", (hw - R, hh), (-hw + R, hh), LH),
        ("arc", (-hw + R, hh - R), (0.5 * PI, PI), ARC),
        ("line", (-hw, hh - R), (-hw, 0), LV / 2),
    ]
    for kind, a, b, length in segs:
        if s <= length:
            t = s / length
            if kind == "line":
                p = np.array(a) + t * (np.array(b) - np.array(a))
            else:
                ang = b[0] + t * (b[1] - b[0])
                p = np.array(a) + R * np.array([np.cos(ang), np.sin(ang)])
            return CENTER + np.array([p[0], p[1], 0.0])
        s -= length
    return CENTER + np.array([-hw, 0, 0])


def in_switch_gap(s):
    p = loop_point(s) - CENTER
    return abs(p[1] - H / 2) < 1e-6 and abs(p[0]) < SWITCH_GAP


class P01ElectronFlow(Scene):
    def construct(self):
        rng = np.random.default_rng(7)

        # ── 자막 ──
        def caption(text, t2c=None):
            return Text(text, font=FONT, font_size=40, color=WHITE, t2c=t2c or {}).move_to(UP * 3.25)

        cap = caption("전선 속에는 '전자'가 가득 들어 있어요", {"'전자'": BLUE})

        # ── 전선 ──
        wire_outer = RoundedRectangle(width=W, height=H, corner_radius=R).move_to(CENTER)
        wire_outer.set_stroke(METAL, width=34, opacity=0.22)
        wire_inner = wire_outer.copy().set_stroke(METAL, width=3, opacity=0.55)
        wire = VGroup(wire_outer, wire_inner)

        # ── 스위치 (윗변 중앙) ──
        top_y = CENTER[1] + H / 2
        gap_cover = Rectangle(width=2 * SWITCH_GAP, height=0.6, stroke_width=0, fill_color=BG, fill_opacity=1)
        gap_cover.move_to([0, top_y, 0])
        pin_l = Dot([-SWITCH_GAP, top_y, 0], radius=0.11, color=WHITE)
        pin_r = Dot([SWITCH_GAP, top_y, 0], radius=0.11, color=WHITE)
        lever = Line([-SWITCH_GAP, top_y, 0], [SWITCH_GAP, top_y, 0], stroke_width=9, color=WHITE)
        lever.rotate(35 * DEGREES, about_point=pin_l.get_center())
        switch_label = Text("스위치", font=FONT, font_size=26, color=GRAY).next_to(pin_r, UR, buff=0.25)
        switch = VGroup(gap_cover, lever, pin_l, pin_r)

        # ── 전지 (왼쪽 변) ──
        bx, by = CENTER[0] - W / 2, CENTER[1]
        body_low = RoundedRectangle(width=0.95, height=1.1, corner_radius=0.12, stroke_width=0,
                                    fill_color="#2E3F66", fill_opacity=1).move_to([bx, by - 0.35, 0])
        body_top = RoundedRectangle(width=0.95, height=0.75, corner_radius=0.12, stroke_width=0,
                                    fill_color=YELLOW, fill_opacity=1).move_to([bx, by + 0.55, 0])
        cap_tip = RoundedRectangle(width=0.38, height=0.18, corner_radius=0.05, stroke_width=0,
                                   fill_color="#D9DEE8", fill_opacity=1).next_to(body_top, UP, buff=0)
        plus = Text("+", font=FONT, font_size=40, color="#13203B", weight=BOLD).move_to(body_top)
        minus = Text("−", font=FONT, font_size=40, color=WHITE, weight=BOLD).move_to(body_low)
        battery = VGroup(body_low, body_top, cap_tip, plus, minus)
        battery_label = Text("전지", font=FONT, font_size=26, color=GRAY).next_to(battery, LEFT, buff=0.3)

        # ── 전구 (오른쪽 변) ──
        lx, ly = CENTER[0] + W / 2, CENTER[1]
        brightness = ValueTracker(0)
        glass = Circle(radius=0.62, stroke_color=WHITE, stroke_width=4).move_to([lx, ly, 0])
        glass.set_fill("#2A3550", opacity=1)
        filament = VMobject(stroke_color=GRAY, stroke_width=5).set_points_as_corners(
            [[lx - 0.3, ly - 0.15, 0], [lx - 0.15, ly + 0.15, 0], [lx, ly - 0.15, 0],
             [lx + 0.15, ly + 0.15, 0], [lx + 0.3, ly - 0.15, 0]])
        glows = VGroup(*[Circle(radius=0.62 + 0.28 * k, stroke_width=0).move_to([lx, ly, 0]) for k in range(1, 7)])

        def update_bulb(m):
            b = brightness.get_value()
            glass.set_fill(interpolate_color(ManimColor("#2A3550"), ManimColor(YELLOW), b), opacity=1)
            filament.set_stroke(interpolate_color(ManimColor(GRAY), ManimColor(WHITE), b))
            for k, g in enumerate(glows, start=1):
                g.set_fill(YELLOW, opacity=0.16 * b * (1 - k / 7))

        bulb = VGroup(glass, filament)  # glows는 전자 뒤에 깔리도록 따로 추가
        bulb.add_updater(update_bulb)
        bulb_label = Text("전구", font=FONT, font_size=26, color=GRAY).next_to(glass, RIGHT, buff=0.35)

        # ── 전자 ──
        n = 78
        bases = np.linspace(0, PERIM, n, endpoint=False) + rng.uniform(-0.08, 0.08, n)
        freqs = rng.uniform(2.0, 4.5, (n, 2))
        phases = rng.uniform(0, TAU, (n, 2))
        clock, drift, speed, jiggle = ValueTracker(0), ValueTracker(0), ValueTracker(0), ValueTracker(1)
        alpha, gap_alpha = ValueTracker(0), ValueTracker(0)  # 전체 / 스위치 구간 전자 불투명도
        clock.add_updater(lambda m, dt: m.increment_value(dt))
        drift.add_updater(lambda m, dt: m.increment_value(speed.get_value() * dt))

        electrons = VGroup(*[
            VGroup(Dot(radius=0.2, color=BLUE, fill_opacity=0.18), Dot(radius=0.095, color=BLUE))
            for _ in range(n)
        ])
        hidden = [i for i in range(n) if in_switch_gap(bases[i])]  # 스위치가 열린 동안 가려둘 전자

        hidden_set = set(hidden)

        def update_electrons(group):
            t, d, a = clock.get_value(), drift.get_value(), 0.13 * jiggle.get_value()
            for i, e in enumerate(group):
                op = alpha.get_value() * (gap_alpha.get_value() if i in hidden_set else 1)
                e[0].set_fill(opacity=0.18 * op)
                e[1].set_fill(opacity=op)
                jig = a * np.array([np.sin(freqs[i, 0] * t + phases[i, 0]),
                                    np.sin(freqs[i, 1] * t + phases[i, 1]), 0])
                e.move_to(loop_point(bases[i] + d) + jig)

        electrons.add_updater(update_electrons)

        # 범례
        legend = VGroup(
            VGroup(Dot(radius=0.2, color=BLUE, fill_opacity=0.18), Dot(radius=0.095, color=BLUE)),
            Text("= 전자 (아주 작은 알갱이)", font=FONT, font_size=28, color=WHITE),
        ).arrange(RIGHT, buff=0.25).move_to(CENTER + UP * 0.5)

        # 흐름 방향 표시
        flow_arrow = Arrow(LEFT * 2.2, RIGHT * 2.2, color=YELLOW, stroke_width=8,
                           max_tip_length_to_length_ratio=0.12).move_to(CENTER + DOWN * 1.35)
        flow_text = Text("전자가 이동하는 방향", font=FONT, font_size=28, color=YELLOW).next_to(flow_arrow, UP, buff=0.15)

        # ── 타임라인 ──
        self.add(clock, drift, glows)
        self.play(FadeIn(cap, shift=DOWN * 0.2), Create(wire), run_time=1.4)
        self.play(FadeIn(battery), FadeIn(battery_label), FadeIn(bulb), FadeIn(bulb_label),
                  FadeIn(switch), FadeIn(switch_label), run_time=1.0)
        self.add_foreground_mobjects(battery, bulb, switch)
        self.add(electrons)
        self.play(alpha.animate.set_value(1), FadeIn(legend), run_time=1.0)
        self.wait(1.5)

        self.play(Transform(cap, caption("스위치가 열려 있으면 → 제자리에서 꿈틀꿈틀", {"꿈틀꿈틀": BLUE})), run_time=0.8)
        self.wait(2.5)

        self.play(Transform(cap, caption("스위치를 닫으면…?")), run_time=0.6)
        self.play(Rotate(lever, -35 * DEGREES, about_point=pin_l.get_center()), run_time=0.6)
        self.remove_foreground_mobjects(switch)
        self.remove(gap_cover)
        self.play(gap_alpha.animate.set_value(1), FadeOut(legend), run_time=0.4)

        self.play(speed.animate.set_value(1.6), jiggle.animate.set_value(0.35),
                  brightness.animate.set_value(1), run_time=2.0, rate_func=smooth)
        self.play(Transform(cap, caption("전자가 한 방향으로 흘러요  =  전기(전류)!", {"전기(전류)!": YELLOW})),
                  GrowArrow(flow_arrow), FadeIn(flow_text), run_time=1.0)
        self.wait(5)
