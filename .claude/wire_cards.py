# -*- coding: utf-8 -*-
"""给 25 张卡接上 data-slug + data-payment-qr + data-payment-label。
按 card-name 精确匹配。处理 v2/index.html（之后再同步到根 index.html）。
用法: PYTHONUTF8=1 py -3.12 .claude/wire_cards.py <目标html>
"""
import re, sys
from pathlib import Path

# card-name → (slug, qr文件, 报名label名)
MAP = {
    '六艺通识营': ('liuyi','31b46612fbbe2a38.png','六艺通识营'),
    '头脑特工队': ('emotion-team','19e2955ca60dc88f.png','头脑特工队'),
    '勇敢者游戏': ('brave-game','802120daa6c9be6a.png','剧本营·勇敢者游戏'),
    '招牌通识营 · 世界重启': ('world-restart','31248ddd474fc507.png','世界重启'),
    '少年大富翁创业营': ('tycoon','da7db49f33f6a6c4.png','少年大富翁创业营'),
    '学院制夏令营 2.0': ('academy-2','a5fd106ddc55d96c.png','学院制夏令营2.0'),
    '招牌通识 · 重走人类创造之路': ('human-history','cc889ba154b49c26.png','重走人类创造之路'),
    '硬核成长营 · 命运手斧': ('fate-axe','e8973e403d2519fa.png','硬核成长营·命运手斧'),
    '火星生存指南': ('mars','9f296f20b4682b4a.png','火星生存指南'),
    '数学战争': ('math-war','71d4505670cd1ecd.png','数学战争'),
    '水形物语': ('water-oasis','37de393764959f0b.png','绿洲水人节'),
    '时间玩家': ('time-player','38200b46c148d9db.png','时间玩家'),
    '搞笑诺贝尔': ('funny-nobel','d8a89f1347954a77.jpg','搞笑诺贝尔'),
    '造船 PBL': ('boat-pbl','3c26f657f2423fa4.jpg','硬核创造·造船'),
    '定向越野 + AI 工具': ('orienteering','d806b30897566f6c.png','定向越野营'),
    '招牌学院制 6.0': ('academy-6','f38d38feb5f022f9.png','学院制夏令营6.0'),
    '名侦探学院 2.0': ('detective','6e471ac8d4cfa52c.png','少年侦探学院'),
    '招牌跨学科 · 运气秘籍': ('luck-recipe','c9d9788cdf06e286.png','运气秘籍'),
    '玩笑盲盒营 · 玩耍抗抑': ('joy-blindbox','6084735cbeb0cf49.png','玩笑盲盒营'),
    '第一桶金': ('first-gold','697b7cf18158adf4.png','财富通识·第一桶金'),
    '饥饿游戏': ('hunger-games','2ec00e381838b5d5.png','饥饿游戏挑战营'),
    '职业探索学院制 3.0': ('career-explore','2b607d3110020d05.png','职业探索学院制3.0'),
    '学习方法升级营': ('learning-method','16fe992bfa23b8f4.png','学习方法升级营'),
    'AI游戏设计营': ('ai-game','0e9915d4d66e44aa.jpg','AI游戏设计营'),
    '龙与地下城跑团营': ('dnd','47248d048c561c61.png','龙与地下城跑团营'),
}

def upsert_attr(tag, name, val):
    """在 <div ...> 开标签里 upsert 一个属性。"""
    if re.search(rf'\s{name}="[^"]*"', tag):
        return re.sub(rf'\s{name}="[^"]*"', f' {name}="{val}"', tag, count=1)
    # 插在 class="camp-card..." 之后
    return re.sub(r'(class="camp-card[^"]*")', rf'\1 {name}="{val}"', tag, count=1)

def main(target):
    p = Path(target)
    src = p.read_text(encoding='utf-8')
    # 切出每张卡块：开标签 + body（到下一个 camp-card 或 camps-list 结束）
    matched = set()
    out = []
    pos = 0
    pat = re.compile(r'<div class="camp-card[^"]*"[^>]*>')
    starts = [m.start() for m in pat.finditer(src)]
    starts.append(src.find('</div><!-- /camps-list'))
    new_src = src
    # 逐卡处理（从后往前，避免偏移）
    cards = []
    for i in range(len(starts)-1):
        st = starts[i]; en = starts[i+1]
        block = src[st:en]
        nm = re.search(r'<div class="card-name">([^<]+)</div>', block)
        if not nm: continue
        name = nm.group(1).strip()
        cards.append((st, en, name))
    for st, en, name in reversed(cards):
        if name not in MAP:
            print(f'  ?? 未在MAP: {name}')
            continue
        slug, qr, label = MAP[name]
        block = new_src[st:en]
        # 开标签
        tagm = re.match(r'<div class="camp-card[^"]*"[^>]*>', block)
        tag = tagm.group(0)
        ntag = tag
        ntag = upsert_attr(ntag, 'data-slug', slug)
        ntag = upsert_attr(ntag, 'data-payment-qr', f'../articles/_shared/{qr}')
        ntag = upsert_attr(ntag, 'data-payment-label', f'扫码报名 · {label}')
        new_block = ntag + block[len(tag):]
        new_src = new_src[:st] + new_block + new_src[en:]
        matched.add(name)
    p.write_text(new_src, encoding='utf-8', newline='')
    print(f'接好 {len(matched)}/25 张卡 → {target}')
    miss = set(MAP) - matched
    if miss: print('  !! 没匹配到:', miss)

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv)>1 else 'v2/index.html')
