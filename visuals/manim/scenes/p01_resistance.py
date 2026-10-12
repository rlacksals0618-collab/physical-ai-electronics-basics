"""p01_resistance — 같은 전지·같은 전구에서, 저항이 있는 길은 전자가 느리게 흘러 전구가 어둡다."""
import sys
from pathlib import Path

import numpy as np
from manim import *

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from parts import bulb, electron, set_electron_opacity  # noqa: E402
from style import BG, BLUE, FONT, GRAY, METAL, WHITE, YELLOW  # noqa: E402

XA, XB = -5.9, 4.85          # 전선 시작(전지) ~ 끝(전구 왼쪽)
BULB_X, BULB_R = 5.4, 0.55
RES_HALF = 1.3               # 저항 반폭
LANES = [  # (y, 제목, 결과 문구, 전자 속도, 전구 밝기, 저항 여부)
    (1.05, "① 저항이 작을 때", "전류 많이 → 전구 밝음", 2.2, 1.0, False),
    (-1.95, "② 저항이 클 때", "전류 적게 → 전구 어두움", 0.55, 0.25, True),
]
N = 34


def small_battery(x, y):
    low = RoundedRectangle(width=0.55, height=0.62, corner_radius=0.08, stroke_width=0,
                           fill_color="#2E3F66", fill_opacity=1).move_to([x, y - 0.2, 0])
    top = RoundedRectangle(width=0.55, height=0.42, corner_radius=0.08, stroke_width=0,
                           fill_color=YELLOW, fill_opacity=1).move_to([x, y + 0.31, 0])
    tip = RoundedRectangle(width=0.22, height=0.1, corner_radius=0.03, stroke_width=0,
                           fill_color="#D9DEE8", fill_opacity=1).next_to(top, UP, buff=0)
    plus = Text("+", font=FONT, font_size=26, color=BG, weight=BOLD).move_to(top)
    return VGroup(low, top, tip, plus)


def resistor(y):
    body = RoundedRectangle(width=2 * RES_HALF, height=0.82, corner_radius=0.3, stroke_width=0,
                            fill_color="#D8B583", fill_opacity=1).move_to([0, y, 0])
    bands = VGroup(*[
        Rectangle(width=0.16, height=0.82, stroke_width=0, fill_color=c, fill_opacity=1).move_to([bx, y, 0])
        for bx, c in [(-0.75, "#E0464E"), (-0.4, "#E0464E"), (-0.05, "#7A4A2A"), (0.75, "#D4AF37")]
    ])  # 빨강·빨강·갈색·금 = 220Ω (LED 실습에서 쓰는 저항)
    channel = Rectangle(width=2 * RES_HALF + 0.02, height=0.2, stroke_width=0,
                        fill_color=BG, fill_opacity=0.9).move_to([0, y, 0])
    return VGroup(body, bands, channel)


class P01Resistance(Scene):
    def construct(self):
        rng = np.random.default_rng(3)

        def caption(text, t2c=None, size=40):
            return Text(text, font=FONT, font_size=size, color=WHITE, t2c=t2c or {}).move_to(UP * 3.25)

        cap = caption("같은 전지, 같은 전구 — 지나가는 길만 다르다")

        clock = ValueTracker(0)
        clock.add_updater(lambda m, dt: m.increment_value(dt))
        ramp = ValueTracker(0)   # 0→1 : 흐름 시작
        alpha = ValueTracker(0)  # 전자 불투명도
        self.add(clock)

        statics, glows_all, bodies, electrons_all, results, res_mob = [], [], [], [], [], None
        for y, title, result, speed, bright, has_res in LANES:
            tube = Line([XA, y, 0], [XB, y, 0], stroke_width=34, color=METAL, stroke_opacity=0.22)
            core = Line([XA, y, 0], [XB, y, 0], stroke_width=3, color=METAL, stroke_opacity=0.55)
            label = Text(title, font=FONT, font_size=30, color=WHITE).move_to([XA, y + 0.85, 0], aligned_edge=LEFT)
            group = VGroup(tube, core, label)
            if has_res:
                res_mob = resistor(y)
                group.add(res_mob)
            batt = small_battery(XA - 0.45, y)
            group.add(batt)
            statics.append(group)

            b = ValueTracker(0)
            glows, body = bulb([BULB_X, y, 0], b, radius=BULB_R)
            glows_all.append(glows)
            bodies.append(body)

            drift = ValueTracker(0)
            drift.add_updater(lambda m, dt, s=speed: m.increment_value(s * ramp.get_value() * dt))
            self.add(drift)
            length = XB - XA
            bases = np.linspace(0, length, N, endpoint=False) + rng.uniform(-0.05, 0.05, N)
            freqs, phases = rng.uniform(2, 4.5, (N, 2)), rng.uniform(0, TAU, (N, 2))
            es = VGroup(*[electron() for _ in range(N)])

            def update(group, y=y, drift=drift, bases=bases, freqs=freqs, phases=phases, has_res=has_res, L=length):
                t, d = clock.get_value(), drift.get_value()
                for i, e in enumerate(group):
                    x = XA + (bases[i] + d) % L
                    squeeze = 0.25 if (has_res and abs(x) < RES_HALF) else 1.0
                    jx = 0.1 * np.sin(freqs[i, 0] * t + phases[i, 0])
                    jy = 0.12 * squeeze * np.sin(freqs[i, 1] * t + phases[i, 1])
                    e.move_to([x + jx, y + jy, 0])
                    edge = min(1, max(0, (x - XA) / 0.4)) * min(1, max(0, (XB - x) / 0.4))
                    set_electron_opacity(e, alpha.get_value() * edge)

            es.add_updater(update)
            electrons_all.append(es)
            results.append((b, bright, Text(result, font=FONT, font_size=28,
                                            color=YELLOW if bright > 0.5 else GRAY).move_to([2.0, y + 0.85, 0])))

        # ── 타임라인 ──
        self.add(*glows_all)
        self.play(FadeIn(cap, shift=DOWN * 0.2), *[FadeIn(g) for g in statics], *[FadeIn(b) for b in bodies],
                  run_time=1.2)
        self.add(*electrons_all)
        self.add_foreground_mobjects(*bodies)
        self.play(alpha.animate.set_value(1), run_time=0.8)
        self.play(ramp.animate.set_value(1), *[b.animate.set_value(v) for b, v, _ in results],
                  run_time=2.0, rate_func=smooth)
        self.wait(2.0)

        res_label = Text("저항", font=FONT, font_size=28, color=YELLOW).next_to(res_mob, DOWN, buff=0.25)
        self.play(Transform(cap, caption("저항이 크면 → 전자가 지나가기 힘들다 → 전류가 줄어든다",
                                         {"저항이 크면": YELLOW, "전류가 줄어든다": YELLOW}, size=36)),
                  Circumscribe(res_mob, color=YELLOW, buff=0.12), FadeIn(res_label), run_time=1.4)
        self.play(*[FadeIn(t, shift=UP * 0.15) for _, _, t in results], run_time=0.8)
        self.wait(5)
