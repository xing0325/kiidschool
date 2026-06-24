# -*- coding: utf-8 -*-
"""把 articles/_shared 里的动图 GIF 转 MP4（体积小 10 倍），
并改写所有 article.html 里 <img ... src="../_shared/X.gif" ...> → <video ... src="../_shared/X.mp4">。
QR 是静态图，不涉及。
用法: PYTHONUTF8=1 py -3.12 .claude/gif2mp4.py
"""
import re, subprocess
from pathlib import Path

ROOT = Path(r'C:/Users/david/kiidschool')
SHARED = ROOT / 'articles' / '_shared'

gifs = sorted(SHARED.glob('*.gif'))
print(f'GIF 数: {len(gifs)}')
converted = {}  # X.gif -> X.mp4
b_total=a_total=0
for g in gifs:
    mp4 = g.with_suffix('.mp4')
    b = g.stat().st_size; b_total += b
    # libx264 需要偶数宽高；yuv420p 兼容性最好
    r = subprocess.run(['ffmpeg','-y','-i',str(g),
        '-movflags','+faststart','-pix_fmt','yuv420p',
        '-vf','scale=trunc(iw/2)*2:trunc(ih/2)*2',
        '-c:v','libx264','-crf','30','-preset','fast','-an',
        '-loglevel','error',str(mp4)],capture_output=True)
    if r.returncode==0 and mp4.exists() and mp4.stat().st_size>0:
        converted[g.name] = mp4.name
        a_total += mp4.stat().st_size
        g.unlink()
    else:
        if mp4.exists(): mp4.unlink()
        a_total += b
        print(f'  ! 转换失败保留gif: {g.name} {r.stderr.decode("utf-8","ignore")[:80]}')

print(f'转换 {len(converted)} 个；GIF {b_total/1024/1024:.0f}MB -> MP4 {a_total/1024/1024:.0f}MB')

# 改写 article.html：img(含X.gif) → video
VIDEO_ATTRS = 'autoplay loop muted playsinline webkit-playsinline x5-video-player-type="h5-page" x5-video-player-fullscreen="false"'
n_html=0; n_repl=0
for f in (ROOT/'articles').glob('*/article.html'):
    html = f.read_text(encoding='utf-8')
    orig = html
    for gif_name, mp4_name in converted.items():
        base = gif_name[:-4]  # 去 .gif
        # 匹配引用该 gif 的整个 <img ...> 标签
        pat = re.compile(r'<img\b[^>]*?\.\./_shared/'+re.escape(base)+r'\.gif[^>]*?>', re.IGNORECASE)
        def to_video(m):
            return f'<video src="../_shared/{mp4_name}" {VIDEO_ATTRS}></video>'
        html, c = pat.subn(to_video, html)
        n_repl += c
    if html != orig:
        f.write_text(html, encoding='utf-8', newline='')
        n_html += 1
print(f'改写 {n_html} 篇 article.html，共替换 {n_repl} 处 img.gif→video.mp4')

# 检查残留 .gif 引用
leftover = 0
for f in (ROOT/'articles').glob('*/article.html'):
    leftover += len(re.findall(r'\.\./_shared/[0-9a-f]+\.gif', f.read_text(encoding='utf-8')))
print(f'残留 .gif 引用: {leftover}（应为0）')
print(f'articles/ 现大小见下')
