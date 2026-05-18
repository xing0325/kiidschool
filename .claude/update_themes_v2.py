"""按用户红字标注重构 19 标签体系。"""
import re
from pathlib import Path

# 红字标注：每张卡的新 themes
MAPPING = {
    'slug:liuyi':           '跨学科通识',
    'slug:emotion-team':    '情绪',
    'slug:world-restart':   '动手创造',
    'slug:human-history':   '动手创造',
    'slug:fate-axe':        '跨学科通识',
    'slug:luck-recipe':     '跨学科通识',
    'slug:joy-blindbox':    '跨学科通识',
    'slug:learning-method': '学习方法',
    'slug:ai-game':         'AI,创造',
    'slug:dnd':             '跑团',
    'name:勇敢者游戏':         '剧本营,冒险',
    'name:少年大富翁创业营':   '财商,PBL',
    'name:学院制夏令营 2.0':   '经典招牌',
    'name:火星生存指南':       '跨学科通识',
    'name:数学战争':           '跨学科通识,逻辑',
    'name:水形物语':           '跨学科通识',
    'name:时间玩家':           '跨学科通识,时间管理',
    'name:搞笑诺贝尔':         '跨学科通识,科学素养',
    'name:造船 PBL':           '硬核创造,PBL',
    'name:定向越野 + AI 工具': '逻辑,AI',
    'name:招牌学院制 6.0':     '学院制',
    'name:名侦探学院 2.0':     '学院制,侦探推理',
    'name:第一桶金':           '跨学科通识,财商',
    'name:饥饿游戏':           '跨学科通识',
    'name:职业探索学院制 3.0': '学院制,职业探索',
}

for target_file in ['index.html', 'v2/index.html']:
    p = Path(target_file)
    if not p.exists(): continue
    src = p.read_text(encoding='utf-8')

    pattern = re.compile(r'(<div class="camp-card[^"]*"\s+)([^>]*?)(>)(.*?)(?=<div class="camp-card|</div><!-- /camps-list)', re.DOTALL)
    cnt = 0
    def replace_card(m):
        global cnt
        head, attrs, gt, body = m.group(1), m.group(2), m.group(3), m.group(4)
        slug_m = re.search(r'data-slug="([^"]+)"', attrs)
        name_m = re.search(r'<div class="card-name">([^<]+)</div>', body)
        key = f'slug:{slug_m.group(1)}' if slug_m else (f'name:{name_m.group(1).strip()}' if name_m else None)
        if key in MAPPING:
            new = MAPPING[key]
            attrs2, n = re.subn(r'data-themes="[^"]*"', f'data-themes="{new}"', attrs, count=1)
            if n == 0:
                attrs2 = attrs + f' data-themes="{new}"'
            cnt += 1
            return head + attrs2 + gt + body
        return m.group(0)

    new_src = pattern.sub(replace_card, src)
    p.write_text(new_src, encoding='utf-8', newline='')
    print(f'{target_file}: rewrote {cnt} cards')
