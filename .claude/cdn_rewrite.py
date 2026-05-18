"""把 HTML 里所有静态资源路径改成 jsDelivr CDN URL。

用法：
    python .claude/cdn_rewrite.py <commit-hash>

会改：
- index.html
    src="images/...", data-src="images/..."
    src="articles/_shared/...", data-src="articles/_shared/..."
    （仅 <img> <video> 的 src/data-src；不动 CSS 里的 url(...)，因为站里几乎没有用）
- articles/*/article.html
    src="../_shared/...", data-src="../_shared/..."

CDN base: https://cdn.jsdelivr.net/gh/xing0325/kiidschool@<hash>/
"""
import re
import sys
from pathlib import Path

if len(sys.argv) < 2:
    print('usage: python .claude/cdn_rewrite.py <commit-hash>')
    sys.exit(1)

HASH = sys.argv[1]
REPO = 'xing0325/kiidschool'
CDN_BASE = f'https://cdn.jsdelivr.net/gh/{REPO}@{HASH}/'

ROOT = Path(__file__).resolve().parent.parent

def rewrite_index():
    p = ROOT / 'index.html'
    src = p.read_text(encoding='utf-8')
    n_total = 0

    # (src|data-src)="(images|articles/_shared)/..."
    def sub(m):
        attr, prefix, path = m.group(1), m.group(2), m.group(3)
        # 跳过已经是 CDN 的 / 已经是绝对 URL 的
        if path.startswith('http') or 'cdn.jsdelivr.net' in m.group(0):
            return m.group(0)
        return f'{attr}="{CDN_BASE}{prefix}/{path}"'

    pattern = re.compile(r'(src|data-src)="(images|articles/_shared)/([^"]+)"')
    src, n = pattern.subn(sub, src)
    n_total += n

    p.write_text(src, encoding='utf-8', newline='')
    print(f'index.html: rewrote {n_total}')

def rewrite_articles():
    files = list((ROOT / 'articles').glob('*/article.html'))
    total = 0
    for f in files:
        src = f.read_text(encoding='utf-8')
        # 替换 (src|data-src)="../_shared/..."
        def sub(m):
            attr, path = m.group(1), m.group(2)
            return f'{attr}="{CDN_BASE}articles/_shared/{path}"'
        pattern = re.compile(r'(src|data-src)="\.\./_shared/([^"]+)"')
        src, n = pattern.subn(sub, src)
        f.write_text(src, encoding='utf-8', newline='')
        total += n
        print(f'  {f.relative_to(ROOT)}: rewrote {n}')
    print(f'articles total: {total}')

if __name__ == '__main__':
    rewrite_index()
    rewrite_articles()
    print(f'\nCDN base: {CDN_BASE}')
