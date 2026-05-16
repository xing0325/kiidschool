# -*- coding: utf-8 -*-
"""把 articles/_shared/ 里的 GIF 转 MP4、大 PNG 压成 JPG，更新所有 article.html。"""
import re, subprocess, hashlib
from pathlib import Path

shared = Path(r'C:/Users/david/kiidschool/articles/_shared')
articles_dir = Path(r'C:/Users/david/kiidschool/articles')
FFMPEG = r'C:/Users/david/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.1.1-full_build/bin/ffmpeg.exe'

# === 1. GIF → MP4 ===
print('=== Step 1: GIF -> MP4 ===')
gif_to_mp4 = {}  # old gif filename -> new mp4 filename
for gif in sorted(shared.glob('*.gif')):
    mp4 = gif.with_suffix('.mp4')
    print(f'  → {gif.name} ({gif.stat().st_size//1024} KB)...', end=' ', flush=True)
    r = subprocess.run(
        [FFMPEG, '-y', '-i', str(gif),
         '-movflags', 'faststart', '-pix_fmt', 'yuv420p',
         '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2',
         '-c:v', 'libx264', '-crf', '24', '-preset', 'fast', '-an',
         str(mp4)],
        capture_output=True
    )
    if r.returncode == 0 and mp4.exists():
        gif_to_mp4[gif.name] = mp4.name
        print(f'OK ({mp4.stat().st_size//1024} KB)')
    else:
        print(f'FAIL: {r.stderr.decode("utf-8", errors="ignore")[:200]}')

# === 2. 大 PNG -> JPG（压缩 + 限宽 1200） ===
print('\n=== Step 2: 大 PNG -> JPG ===')
from PIL import Image
png_to_jpg = {}
for png in sorted(shared.glob('*.png')):
    if png.stat().st_size < 300_000:
        continue
    try:
        img = Image.open(png)
        # 限宽
        if img.width > 1200:
            ratio = 1200 / img.width
            img = img.resize((1200, int(img.height * ratio)), Image.LANCZOS)
        # RGBA -> RGB 白底
        if img.mode in ('RGBA', 'LA', 'P'):
            bg = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            if img.mode in ('RGBA', 'LA'):
                bg.paste(img, mask=img.split()[-1])
                img = bg
            else:
                img = img.convert('RGB')
        jpg = png.with_suffix('.jpg')
        img.save(jpg, 'JPEG', quality=82, optimize=True)
        old_size = png.stat().st_size // 1024
        new_size = jpg.stat().st_size // 1024
        png_to_jpg[png.name] = jpg.name
        print(f'  ✓ {png.name} {old_size} KB → {jpg.name} {new_size} KB')
    except Exception as e:
        print(f'  ✗ {png.name}: {e}')

# === 3. 更新所有 article.html ===
print('\n=== Step 3: 更新 article.html ===')
for html_path in sorted(articles_dir.glob('*/article.html')):
    text = html_path.read_text(encoding='utf-8')
    orig = text

    # GIF -> 视频
    for old_gif, new_mp4 in gif_to_mp4.items():
        old_src = f'../_shared/{old_gif}'
        new_src = f'../_shared/{new_mp4}'
        # <img ... src="X.gif" ...> -> <video ... src="X.mp4" autoplay loop muted playsinline></video>
        pat = re.compile(
            r'<img\b([^>]*?)src="' + re.escape(old_src) + r'"([^>]*?)/?>',
            re.IGNORECASE
        )
        text = pat.sub(
            lambda m: f'<video{m.group(1)}src="{new_src}"{m.group(2)} autoplay loop muted playsinline></video>',
            text
        )

    # 大 PNG -> JPG
    for old_png, new_jpg in png_to_jpg.items():
        text = text.replace(f'../_shared/{old_png}', f'../_shared/{new_jpg}')

    # 给所有 img 加 loading="lazy"
    text = re.sub(
        r'<img(?![^>]*\bloading=)\b([^>]*)>',
        r'<img loading="lazy"\1>',
        text
    )
    # 给 video 加 preload="metadata" 避免一次性都拉
    text = re.sub(
        r'<video(?![^>]*\bpreload=)\b([^>]*)>',
        r'<video preload="metadata"\1>',
        text
    )

    if text != orig:
        html_path.write_text(text, encoding='utf-8')
        n_gif = orig.count('.gif') - text.count('.gif')
        n_png = orig.count('.png') - text.count('.png')
        print(f'  ✓ {html_path.parent.name}: GIF→MP4 ×{n_gif}, PNG→JPG ×{n_png}')

# === 4. 删除已被替代的 GIF / 大 PNG ===
print('\n=== Step 4: 删除原 GIF/PNG ===')
removed_bytes = 0
for gif_name in gif_to_mp4:
    p = shared / gif_name
    if p.exists():
        removed_bytes += p.stat().st_size
        p.unlink()
for png_name in png_to_jpg:
    p = shared / png_name
    if p.exists():
        removed_bytes += p.stat().st_size
        p.unlink()
print(f'  释放 {removed_bytes/(1024*1024):.1f} MB')

# === 总结 ===
total = sum(f.stat().st_size for f in articles_dir.rglob('*') if f.is_file())
print(f'\n最终 articles/ 大小: {total/(1024*1024):.1f} MB')
