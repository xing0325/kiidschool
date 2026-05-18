"""一次性压缩首屏大图。运行：python .claude/optimize_static_imgs.py"""
from PIL import Image
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (输入, 输出, 最大宽, JPG quality)
JOBS = [
    ("images/camps/world.jpg",          "images/camps/world.jpg",          1080, 80),
    ("images/playmates/linwenping.png", "images/playmates/linwenping.jpg", 800, 82),
    ("images/playmates/chixiao.png",    "images/playmates/chixiao.jpg",    800, 82),
    ("images/playmates/hechao.png",     "images/playmates/hechao.jpg",     800, 82),
    ("images/playmates/lingr.png",      "images/playmates/lingr.jpg",      800, 82),
    ("images/features/seven-arts.png",  "images/features/seven-arts.jpg",  1000, 82),
]

for inp, outp, max_w, q in JOBS:
    src = ROOT / inp
    dst = ROOT / outp
    if not src.exists():
        print(f"SKIP (missing): {inp}")
        continue
    before = src.stat().st_size
    im = Image.open(src).convert("RGB")
    if im.width > max_w:
        ratio = max_w / im.width
        im = im.resize((max_w, int(im.height * ratio)), Image.LANCZOS)
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, "JPEG", quality=q, optimize=True, progressive=True)
    after = dst.stat().st_size
    print(f"OK  {inp:42s} -> {outp:42s}  {before/1024:>7.0f} KB -> {after/1024:>5.0f} KB  ({100*after/before:.0f}%)")
