"""压缩详情页素材 articles/_shared。
- JPG: resize 到 ≤800w，re-encode q=72，progressive
- PNG: 有 alpha 就保留 PNG resize + optimize；无 alpha 转 JPG 同名 .png 文件（避免改 article 引用）
       （文件字节是 JPEG 但保留 .png 扩展名，浏览器会按内容嗅探正确解码）
- MP4: ffmpeg -crf 28 -vf scale=-2:480 -preset slow
"""
from PIL import Image
from pathlib import Path
import subprocess, sys, io, time

ROOT = Path(__file__).resolve().parent.parent
SHARED = ROOT / 'articles' / '_shared'
MAX_W = 800
JPG_Q = 72

def is_opaque(img):
    if img.mode != 'RGBA': return True
    alpha = img.split()[3]
    # alpha 全 255 视为不透明
    extrema = alpha.getextrema()
    return extrema[0] == 255 and extrema[1] == 255

def reencode_jpg(path):
    before = path.stat().st_size
    im = Image.open(path)
    im = im.convert('RGB')
    if im.width > MAX_W:
        im = im.resize((MAX_W, int(im.height * MAX_W / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, 'JPEG', quality=JPG_Q, optimize=True, progressive=True)
    new = buf.getvalue()
    if len(new) < before:
        path.write_bytes(new)
        return before, len(new), 'jpg'
    return before, before, 'jpg-skip'

def reencode_png(path):
    before = path.stat().st_size
    im = Image.open(path)
    if im.mode in ('LA', 'P'):
        im = im.convert('RGBA')
    if is_opaque(im):
        im2 = im.convert('RGB')
        if im2.width > MAX_W:
            im2 = im2.resize((MAX_W, int(im2.height * MAX_W / im2.width)), Image.LANCZOS)
        buf = io.BytesIO()
        im2.save(buf, 'JPEG', quality=JPG_Q, optimize=True, progressive=True)
        new = buf.getvalue()
        if len(new) < before:
            path.write_bytes(new)
            return before, len(new), 'png->jpg(.png)'
        return before, before, 'png-keep'
    else:
        # 有 alpha，保留 PNG，仅 resize
        if im.width > MAX_W:
            im = im.resize((MAX_W, int(im.height * MAX_W / im.width)), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, 'PNG', optimize=True)
        new = buf.getvalue()
        if len(new) < before:
            path.write_bytes(new)
            return before, len(new), 'png-resize'
        return before, before, 'png-skip'

def reencode_mp4(path):
    before = path.stat().st_size
    tmp = path.with_suffix('.tmp.mp4')
    cmd = ['ffmpeg', '-y', '-i', str(path),
           '-vf', 'scale=-2:480',
           '-c:v', 'libx264', '-crf', '28', '-preset', 'slow',
           '-an',  # 营期动图都是静音
           '-movflags', '+faststart',
           '-loglevel', 'error',
           str(tmp)]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        return before, before, 'mp4-fail: ' + r.stderr.decode('utf-8', errors='ignore')[:80]
    new_size = tmp.stat().st_size
    if new_size < before:
        path.unlink()
        tmp.rename(path)
        return before, new_size, 'mp4'
    tmp.unlink()
    return before, before, 'mp4-skip'

total_before = total_after = 0
counts = {}
t0 = time.time()
for f in sorted(SHARED.iterdir()):
    ext = f.suffix.lower()
    if ext == '.jpg':    b, a, tag = reencode_jpg(f)
    elif ext == '.png':  b, a, tag = reencode_png(f)
    elif ext == '.mp4':  b, a, tag = reencode_mp4(f)
    else: continue
    total_before += b; total_after += a
    counts[tag] = counts.get(tag, 0) + 1
    if b > 50*1024 or tag.startswith('mp4'):
        print(f'  {tag:18s}  {b/1024:7.0f} KB -> {a/1024:7.0f} KB  ({100*a/b:5.1f}%)  {f.name}')

print()
print(f'tags: {counts}')
print(f'total: {total_before/1024/1024:.2f} MB -> {total_after/1024/1024:.2f} MB  ({100*total_after/total_before:.1f}%)')
print(f'elapsed: {time.time()-t0:.1f}s')
