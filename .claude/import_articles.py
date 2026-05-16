# -*- coding: utf-8 -*-
"""把抓取下来的 10 篇微信文章去重 + 导入 kiidschool/articles/。
重写：用 _index.json 拿 image_urls 顺序，匹配本地 img-NN 文件，重写 HTML。"""
import hashlib, shutil, json, re
from pathlib import Path

src_root = Path(r'C:/工作资料/钥匙玩校营期文章')
dst_root = Path(r'C:/Users/david/kiidschool/articles')
shared_dir = dst_root / '_shared'

# 重建 shared
if shared_dir.exists():
    shutil.rmtree(shared_dir)
shared_dir.mkdir(parents=True, exist_ok=True)

TITLE_TO_SLUG = [
    (r'运气秘籍', 'luck-recipe'),
    (r'玩笑盲盒', 'joy-blindbox'),
    (r'重走人类', 'human-history'),
    (r'头脑特工队', 'emotion-team'),
    (r'硬核成长|命运手斧|手斧男孩', 'fate-axe'),
    (r'六艺通识', 'liuyi'),
    (r'世界重启', 'world-restart'),
    (r'AI游戏', 'ai-game'),
    (r'龙与地下城', 'dnd'),
    (r'学习方法', 'learning-method'),
]


def slug_for(title):
    for pat, slug in TITLE_TO_SLUG:
        if re.search(pat, title):
            return slug
    return 'unknown-' + hashlib.md5(title.encode()).hexdigest()[:6]


def url_variants(url):
    """生成 URL 的所有可能在 HTML 中的形式（原始 & HTML 转义）。"""
    return [url, url.replace('&', '&amp;')]


# 读 _index.json 拿每篇 image_urls
index_path = src_root / '_index.json'
articles = json.loads(index_path.read_text(encoding='utf-8'))

# 第一遍：所有图建立 hash → 共享文件名
print('=== 收集唯一图片 ===')
hash_to_shared_name = {}
for f in sorted(src_root.rglob('img-*.*')):
    if not f.is_file():
        continue
    data = f.read_bytes()
    h = hashlib.md5(data).hexdigest()
    if h not in hash_to_shared_name:
        ext = f.suffix.lower()
        if ext == '.jpeg':
            ext = '.jpg'
        name = f'{h[:16]}{ext}'
        (shared_dir / name).write_bytes(data)
        hash_to_shared_name[h] = name
print(f'  共 {len(hash_to_shared_name)} 张唯一图，存到 _shared/')

# 第二遍：处理每个 article
print('\n=== 重写 article.html ===')
manifest = []
for article in articles:
    src_folder = Path(article['_local_dir'])
    slug = slug_for(article['title'])
    html_path = src_folder / 'article.html'
    if not html_path.exists():
        print(f'  ✗ {slug}: 缺 article.html')
        continue

    html = html_path.read_text(encoding='utf-8')
    image_urls = article.get('image_urls', [])

    # 遍历 image_urls，找对应的本地 img-NN 文件，算 hash → 替换 URL
    replaced = 0
    for i, url in enumerate(image_urls, 1):
        # 找该索引对应的本地文件
        local_candidates = list(src_folder.glob(f'img-{i:02d}.*'))
        if not local_candidates:
            continue
        local = local_candidates[0]
        h = hashlib.md5(local.read_bytes()).hexdigest()
        if h not in hash_to_shared_name:
            continue
        new_src = f'../_shared/{hash_to_shared_name[h]}'
        for variant in url_variants(url):
            if variant in html:
                html = html.replace(variant, new_src)
                replaced += 1

    out_dir = dst_root / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / 'article.html').write_text(html, encoding='utf-8')

    # 检查仍有未替换的远程 URL
    remaining_remote = len(re.findall(r'src="https?://mmbiz', html))

    # 提取首图（封面）
    m_first = re.search(r'<img[^>]+src="(\.\./_shared/[^"]+)"', html)
    cover = m_first.group(1).replace('../_shared/', '_shared/') if m_first else ''

    # 提取主标题（H1 是脚本生成的"标题"，更可靠的是数据里的）
    article_title = article['title']

    manifest.append({
        'slug': slug,
        'title': article_title,
        'url': article['_url'],
        'cover': cover,
        'html_path': f'articles/{slug}/article.html',
        'img_replaced': replaced,
        'img_remote_left': remaining_remote,
    })
    print(f'  ✓ {slug}: 替换 {replaced} 处，剩 {remaining_remote} 个远程 URL')

(dst_root / 'manifest.json').write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8'
)
print(f'\n清单写入 {dst_root}/manifest.json')

total = sum(f.stat().st_size for f in dst_root.rglob('*') if f.is_file())
print(f'最终 articles/ 大小: {total/(1024*1024):.1f} MB')
