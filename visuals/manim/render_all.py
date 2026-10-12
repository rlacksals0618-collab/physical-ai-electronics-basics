"""scenes/*.py 를 렌더해 out/{ID}.mp4 와 out/{ID}_poster.png(마지막 프레임)를 만든다.

사용: python visuals/manim/render_all.py [ID ...]   (ID 생략 시 전체)
규칙: scenes/{ID}.py 안에 Scene 클래스 1개.
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

import av

HERE = Path(__file__).resolve().parent
SCENES, OUT, MEDIA = HERE / "scenes", HERE / "out", HERE / "_media"


def scene_class(path):
    m = re.search(r"^class (\w+)\((?:\w+)?Scene\)", path.read_text(encoding="utf-8"), re.M)
    if not m:
        raise SystemExit(f"{path.name}: Scene 클래스를 찾지 못함")
    return m.group(1)


def save_poster(mp4, png):
    with av.open(str(mp4)) as c:
        last = None
        for frame in c.decode(video=0):
            last = frame
        last.to_image().save(png)


def render(scene_id):
    src = SCENES / f"{scene_id}.py"
    cls = scene_class(src)
    subprocess.run([sys.executable, "-m", "manim", "render", str(src), cls, "-q", "h", "--fps", "30",
                    "--media_dir", str(MEDIA), "--disable_caching", "--progress_bar", "none"], check=True)
    mp4 = MEDIA / "videos" / scene_id / "1080p30" / f"{cls}.mp4"
    OUT.mkdir(exist_ok=True)
    shutil.copy(mp4, OUT / f"{scene_id}.mp4")
    save_poster(mp4, OUT / f"{scene_id}_poster.png")
    print(f"✓ {scene_id}")


if __name__ == "__main__":
    ids = sys.argv[1:] or sorted(p.stem for p in SCENES.glob("p*.py"))
    for i in ids:
        render(i)
