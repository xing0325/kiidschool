# -*- coding: utf-8 -*-
"""从 _warmwork 导入文章到仓库 articles/<slug>/，并提取每营专属报名QR。
- 图片按 md5 去重进 articles/_shared/
- _warmwork/<dir>/article.html 里的 img-NN.ext 改写为 ../_shared/<hash>.<ext>
- 提取「扫码报名」之后第一张图作为该营专属报名QR
- 输出 .claude/tmp/import_report.json 供后续接卡片
- 更新 manifest.json（additive upsert）
用法: PYTHONUTF8=1 py -3.12 .claude/import_warm.py
"""
import hashlib, json, re, sys
from pathlib import Path

ROOT = Path(r'C:/Users/david/kiidschool')
WORK = ROOT / '.claude' / '_warmwork'
ARTS = ROOT / 'articles'
SHARED = ARTS / '_shared'
SHARED.mkdir(parents=True, exist_ok=True)

# 标题关键词 → slug（具体的放前面，通用的放后面）
TITLE_TO_SLUG = [
    (r'学院制.*6\.0|学院制夏令营\s*6', 'academy-6'),
    (r'学院制.*2\.0|学院制夏令营\s*2', 'academy-2'),
    (r'职业探索', 'career-explore'),
    (r'运气秘籍', 'luck-recipe'),
    (r'玩笑盲盒', 'joy-blindbox'),
    (r'重走人类|人类创造', 'human-history'),
    (r'头脑特工队', 'emotion-team'),
    (r'命运手斧|硬核成长|手斧', 'fate-axe'),
    (r'六艺', 'liuyi'),
    (r'世界重启|万物复苏', 'world-restart'),
    (r'AI\s*游戏|游戏设计', 'ai-game'),
    (r'龙与地下城', 'dnd'),
    (r'学习方法', 'learning-method'),
    (r'定向越野', 'orienteering'),
    (r'数学战争', 'math-war'),
    (r'造船|硬核创造', 'boat-pbl'),
    (r'侦探', 'detective'),
    (r'勇敢者游戏|剧本营|赫拉克勒斯', 'brave-game'),
    (r'大富翁', 'tycoon'),
    (r'搞笑诺贝尔', 'funny-nobel'),
    (r'绿洲水人节|水人节|水形物语', 'water-oasis'),
    (r'饥饿游戏', 'hunger-games'),
    (r'第一桶金|财富通识', 'first-gold'),
    (r'火星生存', 'mars'),
    (r'时间玩家', 'time-player'),
]

def slug_for(title):
    for pat, slug in TITLE_TO_SLUG:
        if re.search(pat, title or ''):
            return slug
    return 'camp-' + hashlib.md5((title or '').encode()).hexdigest()[:6]

def main():
    idx = json.loads((WORK / '_index.json').read_text(encoding='utf-8'))
    # 第一遍：所有 img 去重进 _shared
    hash_to_name = {}
    def dedupe(f: Path):
        data = f.read_bytes()
        h = hashlib.md5(data).hexdigest()
        if h not in hash_to_name:
            ext = f.suffix.lower().lstrip('.')
            if ext == 'jpeg': ext = 'jpg'
            name = f'{h[:16]}.{ext}'
            (SHARED / name).write_bytes(data)
            hash_to_name[h] = name
        return hash_to_name[h]

    report = []
    seen_slugs = {}
    for art in idx:
        title = art.get('title', '')
        folder = Path(art['_local_dir'])
        slug = slug_for(title)
        # 处理重复 slug（如 世界重启 两条）：第二条加后缀，报告里标注
        dup = slug in seen_slugs
        eff_slug = slug if not dup else f'{slug}-alt'
        seen_slugs[slug] = seen_slugs.get(slug, 0) + 1

        html_path = folder / 'article.html'
        if not html_path.exists():
            report.append({'slug': eff_slug, 'title': title, 'url': art.get('_url',''),
                           'error': 'no article.html'})
            continue
        html = html_path.read_text(encoding='utf-8')
        image_urls = art.get('image_urls', [])

        # img-NN.ext → ../_shared/<hash>.<ext>
        local_to_shared = {}  # img-NN.ext -> hash 名
        replaced = 0
        for i in range(1, len(image_urls) + 1):
            cands = list(folder.glob(f'img-{i:02d}.*'))
            if not cands:
                continue
            shared = dedupe(cands[0])
            localname = cands[0].name  # e.g. img-01.png
            new = f'../_shared/{shared}'
            if localname in html:
                html = html.replace(localname, new)
                replaced += 1
            local_to_shared[localname] = shared

        # 提取报名QR：找「扫码报名 / 报名」关键字之后第一张 ../_shared/ 图
        qr = None
        mkw = re.search(r'扫码报名|报名二维码|本营报名|1[、.\s．]*扫码|长按.*报名|【扫码】', html)
        if mkw:
            mimg = re.search(r'\.\./_shared/([^\s"\'\)]+)', html[mkw.end():])
            if mimg:
                qr = mimg.group(1)
        # 兜底：取倒数第 2~4 张图里第一张（公众号 QR 常在结尾附近）——仅当没找到
        out = ARTS / eff_slug
        out.mkdir(parents=True, exist_ok=True)
        (out / 'article.html').write_text(html, encoding='utf-8')

        remote_left = len(re.findall(r'src="https?://mmbiz', html))
        report.append({
            'slug': eff_slug, 'base_slug': slug, 'dup': dup, 'title': title,
            'url': art.get('_url',''), 'n_images': len(image_urls),
            'img_replaced': replaced, 'remote_left': remote_left,
            'qr_shared': qr, 'html_path': f'articles/{eff_slug}/article.html',
        })
        print(f'  {eff_slug:16s} imgs={len(image_urls):3d} repl={replaced:3d} '
              f'remoteLeft={remote_left} QR={qr or "!!未找到"}  {title[:30]}')

    (ROOT / '.claude' / 'tmp' / 'import_report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

    # 更新 manifest（upsert by slug）
    man_path = ARTS / 'manifest.json'
    man = {}
    if man_path.exists():
        try:
            for it in json.loads(man_path.read_text(encoding='utf-8')):
                man[it['slug']] = it
        except Exception:
            pass
    for r in report:
        if r.get('error'):
            continue
        man[r['slug']] = {
            'slug': r['slug'], 'title': r['title'], 'url': r['url'],
            'html_path': r['html_path'], 'qr_shared': r.get('qr_shared'),
            'img_replaced': r['img_replaced'], 'img_remote_left': r['remote_left'],
        }
    man_path.write_text(json.dumps(list(man.values()), ensure_ascii=False, indent=2), encoding='utf-8')

    total = sum(f.stat().st_size for f in ARTS.rglob('*') if f.is_file())
    print(f'\n_shared 去重后 {len(hash_to_name)} 张唯一图；articles/ 共 {total/1024/1024:.1f} MB')
    print(f'报告: .claude/tmp/import_report.json （{len(report)} 篇）')

if __name__ == '__main__':
    main()
