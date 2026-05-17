# -*- coding: utf-8 -*-
"""按 2026 价格表把早鸟价 + 原价 写进 25 张卡。"""
import re
from pathlib import Path

HTML = Path(r'C:/Users/david/kiidschool/index.html')

# (营期标识 → (原价, 早鸟价)) 按价格表
# 营期标识可以是卡片的 card-name 包含的子串
PRICES = [
    # (匹配 card-name 关键字, 原价, 早鸟价)
    ('招牌学院制 6.0',         12800, 10800),
    ('职业探索学院制 3.0',     14800, 12800),
    ('学习方法升级营',         4580, 4280),
    ('AI游戏设计营',           12800, 10800),
    ('运气秘籍',               6580, 5980),
    ('玩笑盲盒',               6580, 5980),
    ('龙与地下城',             8280, 7280),
    ('名侦探学院 2.0',         8280, 7280),
    ('六艺通识营',             6580, 5980),
    ('头脑特工队',             6580, 5980),
    ('少年大富翁',             6580, 5980),
    ('重走人类创造之路',       6580, 5980),
    ('世界重启',               6580, 5980),
    ('硬核成长营',             6580, 5980),
    ('命运手斧',               6580, 5980),
    ('学院制夏令营 2.0',       12800, 10800),
    ('勇敢者游戏',             6580, 5980),
    # 毛坯卡
    ('第一桶金',               6580, 5980),
    ('饥饿游戏',               6580, 5980),
    ('火星生存指南',           6580, 5980),
    ('数学战争',               6580, 5980),
    ('水形物语',               6580, 5980),
    ('时间玩家',               6580, 5980),
    ('搞笑诺贝尔',             6580, 5980),
    ('造船 PBL',               6580, 5980),
    ('定向越野',               6580, 5980),
]

s = HTML.read_text(encoding='utf-8')

# 每张卡的 card-price-row 块
def update_card_price(s, name_keyword, full_price, early_price):
    save = full_price - early_price
    # 找包含 name_keyword 的 card-name 后第一个 card-price-row
    pat = re.compile(
        r'(<div class="card-name">[^<]*' + re.escape(name_keyword) + r'[^<]*</div>.*?)'
        r'<div class="card-price-row">.*?</div>',
        re.DOTALL
    )
    new_block = (
        '<div class="card-price-row">\n'
        '          <span class="card-price">' + str(early_price) + '</span><span class="card-price-unit">元起</span>\n'
        '          <span class="card-orig-price">¥' + str(full_price) + '</span>\n'
        '          <span class="card-save">省' + str(save) + '</span>\n'
        '          <span class="card-price-hint">早鸟价 · 3人团购 / 老营员 / 荣誉营员另有优惠</span>\n'
        '        </div>'
    )
    new_s, n = pat.subn(lambda m: m.group(1) + new_block, s, count=1)
    if n == 0:
        print(f'  ✗ 未找到卡片：{name_keyword}')
        return s
    return new_s

for kw, full, early in PRICES:
    s = update_card_price(s, kw, full, early)
    print(f'  ✓ {kw}: 原 {full} / 早鸟 {early} / 省 {full-early}')

HTML.write_text(s, encoding='utf-8')
print(f'\n✓ 已更新 {HTML}')
