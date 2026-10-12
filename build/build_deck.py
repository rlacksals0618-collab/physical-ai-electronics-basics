"""content/*.yaml + visuals/ → output/*.pptx

사용: python build/build_deck.py [출력파일명]
"""
import sys
from pathlib import Path

import av
import yaml
from pptx import Presentation

sys.path.insert(0, str(Path(__file__).resolve().parent))
from layouts import LAYOUTS  # noqa: E402
from theme import SLIDE_H, SLIDE_W  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
VIS = ROOT / "visuals"


def resolve(visual):
    """'flow/p01_atom' 또는 'manim/p01_electron_flow' → 파일 경로들."""
    kind, vid = visual.split("/", 1)
    if kind == "flow":
        return {"image": find_image(VIS / "flow" / "images", vid)}
    if kind == "manim":
        video = need(VIS / "manim" / "out" / f"{vid}.mp4")
        with av.open(str(video)) as c:
            duration_ms = int(c.duration / 1000)  # av.time_base = 1e6
        return {"image": need(VIS / "manim" / "out" / f"{vid}_poster.png"), "video": video, "duration_ms": duration_ms}
    if kind == "chart":
        return {"image": need(VIS / "charts" / "out" / f"{vid}.png")}
    raise SystemExit(f"알 수 없는 시각자료 종류: {visual}")


def find_image(folder, vid):
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        if (folder / f"{vid}{ext}").exists():
            return folder / f"{vid}{ext}"
    raise SystemExit(f"시각자료 없음: {(folder / vid).relative_to(ROOT)}.(png|jpg)")


def need(path):
    if not path.exists():
        raise SystemExit(f"시각자료 없음: {path.relative_to(ROOT)}")
    return path


def main(out_name="전자기초이론_1장_맛보기.pptx"):
    prs = Presentation()
    prs.slide_width, prs.slide_height = SLIDE_W, SLIDE_H
    slides = []
    for f in sorted((ROOT / "content").glob("*.yaml")):
        slides += yaml.safe_load(f.read_text(encoding="utf-8"))
    for s in slides:
        LAYOUTS[s["layout"]](prs, s, resolve)
    out = ROOT / "output" / out_name
    out.parent.mkdir(exist_ok=True)
    prs.save(out)
    print(f"✓ {len(slides)}장 → {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main(*sys.argv[1:])
