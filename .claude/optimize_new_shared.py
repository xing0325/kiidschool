# -*- coding: utf-8 -*-
"""压缩 articles/_shared（原地、不改名 → 零 HTML 改动）。
- 报名QR(import_report 里的 qr_shared)与小文件跳过
- JPG: ≤800w, q72, progressive
- PNG: 有alpha→优化; 无alpha→若>120KB 降到≤800w 再优化(仍存png)
- GIF: ffmpeg scale=560 + fps 12 + palette（仍存gif）
- MP4: ffmpeg crf28 scale=-2:480
用法: PYTHONUTF8=1 py -3.12 .claude/optimize_new_shared.py
"""
import json, subprocess, io
from pathlib import Path
from PIL import Image

ROOT = Path(r'C:/Users/david/kiidschool')
SHARED = ROOT / 'articles' / '_shared'
report = json.loads((ROOT / '.claude/tmp/import_report.json').read_text(encoding='utf-8'))
QR_KEEP = {r['qr_shared'] for r in report if r.get('qr_shared')}
print(f'保留(不压) QR {len(QR_KEEP)} 张')

MAXW = 800
def is_opaque(im):
    if im.mode in ('RGBA','LA','P'):
        im2 = im.convert('RGBA'); a=im2.split()[3].getextrema(); return a[0]==255
    return True

before_total=after_total=0
n_jpg=n_png=n_gif=n_mp4=n_skip=0
for f in sorted(SHARED.iterdir()):
    if not f.is_file(): continue
    if f.name in QR_KEEP:
        n_skip+=1; continue
    b=f.stat().st_size; before_total+=b
    ext=f.suffix.lower()
    try:
        if ext in ('.jpg','.jpeg'):
            im=Image.open(f).convert('RGB')
            if im.width>MAXW: im=im.resize((MAXW,int(im.height*MAXW/im.width)),Image.LANCZOS)
            buf=io.BytesIO(); im.save(buf,'JPEG',quality=72,optimize=True,progressive=True)
            if buf.tell()<b: f.write_bytes(buf.getvalue()); n_jpg+=1
        elif ext=='.png':
            im=Image.open(f)
            if b>120*1024 and is_opaque(im):
                im=im.convert('RGB')
                if im.width>MAXW: im=im.resize((MAXW,int(im.height*MAXW/im.width)),Image.LANCZOS)
                buf=io.BytesIO(); im.save(buf,'PNG',optimize=True)
                # 无alpha大图：png优化有限，但保持png名；若能省就存
                if buf.tell()<b: f.write_bytes(buf.getvalue()); n_png+=1
            elif b>120*1024:
                im=im.convert('RGBA')
                if im.width>MAXW: im=im.resize((MAXW,int(im.height*MAXW/im.width)),Image.LANCZOS)
                buf=io.BytesIO(); im.save(buf,'PNG',optimize=True)
                if buf.tell()<b: f.write_bytes(buf.getvalue()); n_png+=1
        elif ext=='.gif':
            tmp=f.with_suffix('.tmp.gif')
            r=subprocess.run(['ffmpeg','-y','-i',str(f),
                '-vf','fps=12,scale=560:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse',
                '-loglevel','error',str(tmp)],capture_output=True)
            if r.returncode==0 and tmp.exists() and tmp.stat().st_size<b:
                f.unlink(); tmp.rename(f); n_gif+=1
            elif tmp.exists(): tmp.unlink()
        elif ext=='.mp4':
            tmp=f.with_suffix('.tmp.mp4')
            r=subprocess.run(['ffmpeg','-y','-i',str(f),'-vf','scale=-2:480',
                '-c:v','libx264','-crf','28','-preset','fast','-an','-movflags','+faststart',
                '-loglevel','error',str(tmp)],capture_output=True)
            if r.returncode==0 and tmp.exists() and tmp.stat().st_size<b:
                f.unlink(); tmp.rename(f); n_mp4+=1
            elif tmp.exists(): tmp.unlink()
    except Exception as e:
        print(f'  ! {f.name}: {type(e).__name__} {str(e)[:50]}')
    after_total+=f.stat().st_size

print(f'jpg压{n_jpg} png压{n_png} gif压{n_gif} mp4压{n_mp4} 跳过QR{n_skip}')
print(f'_shared: {before_total/1024/1024:.0f}MB -> {after_total/1024/1024:.0f}MB')
