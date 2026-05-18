"""按新 10 标签体系，重写 25 张卡片的 data-themes。
匹配标识：data-slug（首选）或 card-name 文本（兜底）。
"""
import re
from pathlib import Path

# 新标签映射：{ 标识: 新 themes }
MAPPING = {
    # by slug
    'slug:liuyi':           '学习力,跨学科',
    'slug:emotion-team':    '心理抗挫',
    'slug:world-restart':   '跨学科',
    'slug:human-history':   '跨学科',
    'slug:fate-axe':        '户外冒险,心理抗挫',
    'slug:luck-recipe':     '跨学科,财商,学习力',
    'slug:joy-blindbox':    '心理抗挫',
    'slug:learning-method': '学习力',
    'slug:ai-game':         'AI科创',
    'slug:dnd':             '艺术叙事',
    # by name (无 slug 的卡)
    'name:勇敢者游戏':         '心理抗挫,户外冒险',
    'name:少年大富翁创业营':   '财商',
    'name:学院制夏令营 2.0':   '学院制',
    'name:火星生存指南':       '跨学科,户外冒险',
    'name:数学战争':           '思辨解谜',
    'name:水形物语':           '艺术叙事',
    'name:时间玩家':           '思辨解谜',
    'name:搞笑诺贝尔':         '跨学科,思辨解谜',
    'name:造船 PBL':           'AI科创,跨学科',
    'name:定向越野 + AI 工具': '户外冒险,AI科创',
    'name:招牌学院制 6.0':     '学院制',
    'name:名侦探学院 2.0':     '思辨解谜',
    'name:第一桶金':           '财商',
    'name:饥饿游戏':           '户外冒险',
    'name:职业探索学院制 3.0': '学院制,职业探索',
}

p = Path('index.html')
src = p.read_text(encoding='utf-8')

# 用正则定位每张卡片块（从 <div class="camp-card 开到下一个 camp-card 或 camps-list 结束）
pattern = re.compile(r'(<div class="camp-card[^"]*"\s+)([^>]*?)(>)(.*?)(?=<div class="camp-card|</div><!-- /camps-list)', re.DOTALL)

changes = []
def replace_card(m):
    head, attrs, gt, body = m.group(1), m.group(2), m.group(3), m.group(4)
    slug_m = re.search(r'data-slug="([^"]+)"', attrs)
    name_m = re.search(r'<div class="card-name">([^<]+)</div>', body)
    key = None
    if slug_m:
        key = f'slug:{slug_m.group(1)}'
    elif name_m:
        key = f'name:{name_m.group(1).strip()}'
    if key in MAPPING:
        new_themes = MAPPING[key]
        # 替换 data-themes="..."
        new_attrs, n = re.subn(r'data-themes="[^"]*"', f'data-themes="{new_themes}"', attrs, count=1)
        if n == 0:
            # 之前可能没 themes，插一个
            new_attrs = attrs + f' data-themes="{new_themes}"'
        changes.append((key, new_themes))
        return head + new_attrs + gt + body
    else:
        changes.append((key, '(no match — kept)'))
        return m.group(0)

new_src = pattern.sub(replace_card, src)
p.write_text(new_src, encoding='utf-8', newline='')

for k, v in changes:
    print(f'  {k:35s}  -> {v}')
print(f'\n{len(changes)} cards processed, {sum(1 for _,v in changes if v != "(no match — kept)")} updated')
