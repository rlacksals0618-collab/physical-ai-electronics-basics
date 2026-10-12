"""여러 장면에서 같이 쓰는 부품: 전자 알갱이, 전구."""
from manim import Circle, Dot, ManimColor, VGroup, VMobject, interpolate_color

from style import BLUE, GRAY, WHITE, YELLOW

BULB_OFF = "#2A3550"


def electron():
    """빛번짐(바깥 반투명) + 알갱이. e[0]=glow, e[1]=core."""
    return VGroup(Dot(radius=0.2, color=BLUE, fill_opacity=0.18), Dot(radius=0.095, color=BLUE))


def set_electron_opacity(e, op):
    e[0].set_fill(opacity=0.18 * op)
    e[1].set_fill(opacity=op)


def bulb(center, brightness, radius=0.62):
    """(glows, body) 반환. glows 는 전자 뒤에, body 는 앞에 두면 된다.
    brightness: 0~1 ValueTracker. body 에 updater 가 붙어 있어 body 가 장면에 있어야 갱신된다."""
    x, y = center[0], center[1]
    glass = Circle(radius=radius, stroke_color=WHITE, stroke_width=4).move_to(center)
    glass.set_fill(BULB_OFF, opacity=1)
    r = radius / 0.62
    filament = VMobject(stroke_color=GRAY, stroke_width=5).set_points_as_corners(
        [[x - 0.3 * r, y - 0.15 * r, 0], [x - 0.15 * r, y + 0.15 * r, 0], [x, y - 0.15 * r, 0],
         [x + 0.15 * r, y + 0.15 * r, 0], [x + 0.3 * r, y - 0.15 * r, 0]])
    glows = VGroup(*[Circle(radius=radius + 0.28 * r * k, stroke_width=0).move_to(center) for k in range(1, 7)])

    def update(_):
        b = brightness.get_value()
        glass.set_fill(interpolate_color(ManimColor(BULB_OFF), ManimColor(YELLOW), b), opacity=1)
        filament.set_stroke(interpolate_color(ManimColor(GRAY), ManimColor(WHITE), b))
        for k, g in enumerate(glows, start=1):
            g.set_fill(YELLOW, opacity=0.16 * b * (1 - k / 7))

    body = VGroup(glass, filament)
    body.add_updater(update)
    return glows, body
