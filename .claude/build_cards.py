# -*- coding: utf-8 -*-
"""为现有 13 卡加状态标记 + 移除冗余 + 插入 13 张新卡（4 有详情 + 9 毛坯房）。"""
import re, json
from pathlib import Path

HTML = Path(r'C:/Users/david/kiidschool/index.html')
MANIFEST = Path(r'C:/Users/david/kiidschool/articles/manifest.json')
s = HTML.read_text(encoding='utf-8')

manifest = {a['slug']: a for a in json.loads(MANIFEST.read_text(encoding='utf-8'))}

# ============ Step 1: 在每张已有卡片的 .card-poster 内插入 status 标记 ============
def inject_status_to_card(s, data_dates, status_class, status_char):
    """找该 data-dates 的卡片，在其 .card-poster 内追加 status 标记。"""
    # 找到 <div class="camp-card ... data-dates="X" ...> 后的下一个 .card-poster
    pat = re.compile(
        r'(<div class="camp-card[^"]*"[^>]*data-dates="' + re.escape(data_dates) + r'"[^>]*>\s*<div class="card-main">\s*<div class="card-poster"[^>]*>)',
        re.DOTALL
    )
    status_tag = f'<span class="card-status {status_class}">{status_char}</span>'
    new_s, n = pat.subn(lambda m: m.group(1) + '\n        ' + status_tag, s, count=1)
    if n == 0:
        print(f'  ✗ 找不到 data-dates="{data_dates}" 的卡片')
        return s
    # 同时把 data-status 加到 camp-card 标签上
    new_s = re.sub(
        r'(<div class="camp-card[^"]*")(?=[^>]*data-dates="' + re.escape(data_dates) + r'")',
        r'\1 data-status="' + ('done' if status_class == 'done' else 'todo') + '"',
        new_s, count=1
    )
    return new_s


# 6 张 done 卡（有 data-slug）
DONE_DATES = ['7.4-7.10,7.11-7.17',                                  # liuyi
              '7.4-7.10,7.11-7.17,7.18-7.24,7.25-7.31',              # emotion-team
              '7.11-7.17',                                            # world-restart
              '7.23-7.25',                                            # learning-method
              '7.25-7.31',                                            # ai-game
              '8.1-8.7']                                              # dnd
# 7 张 todo 卡
TODO_DATES = ['7.18-7.24',                                            # 勇敢者游戏
              '7.4-7.10',                                             # 少年大富翁
              '8.8-8.17',                                             # 学院制 9-12
              '7.4-7.13',                                             # 招牌学院制 6.0
              '8.8-8.14',                                             # 名侦探
              '7.14-7.23',                                            # 职业探索 3.0
              ]
# 注意：data-dates="7.25-7.31,8.1-8.7" 是泛 招牌通识 12-16，要删除
TO_REMOVE_DATES = ['7.25-7.31,8.1-8.7']

for d in DONE_DATES:
    s = inject_status_to_card(s, d, 'done', '✓')
for d in TODO_DATES:
    s = inject_status_to_card(s, d, 'todo', '✗')

# ============ Step 2: 移除冗余「招牌通识营 12-16」卡片 ============
# 找到 <!-- 招牌通识营 12-16 --> 后面的整张卡（直到 </div> 关闭 .camp-card）
remove_pat = re.compile(
    r'\s*<!-- 招牌通识营 12-16 -->\s*<div class="camp-card"[^>]*data-dates="7\.25-7\.31,8\.1-8\.7"[^>]*>.*?\n  </div>\n',
    re.DOTALL
)
s, n_removed = remove_pat.subn('\n', s, count=1)
print(f'移除冗余卡片：{n_removed} 张')


# ============ Step 3: 生成新卡片 HTML ============
def make_card(name, age_min, age_max, themes, dates, location, price, theme_tag_colors,
              slug=None, status='blank', poster_img=None, gradient=None, icon='🏕', age_label=None,
              duration='7天', meta_pills=None, featured=False):
    """生成一张 camp-card HTML。"""
    age_label = age_label or f'{age_min}-{age_max}岁'
    classes = ['camp-card']
    if featured:
        classes.append('featured')

    # 推荐排序（暂不放推荐组）
    extra_attrs = ''
    if slug:
        extra_attrs += f' data-slug="{slug}"'
    extra_attrs += f' data-status="{status}"'

    status_html = ''
    if status == 'done':
        status_html = '<span class="card-status done">✓</span>'
    elif status == 'todo':
        status_html = '<span class="card-status todo">✗</span>'
    elif status == 'blank':
        status_html = '<span class="card-status blank">毛坯</span>'

    # 海报
    if poster_img:
        poster_html = (
            f'<div class="card-poster" style="background:linear-gradient(150deg,{gradient or "#888,#666"});">\n'
            f'        {status_html}\n'
            f'        <img class="poster-img" src="{poster_img}" onerror="this.style.display=\'none\'" alt="">\n'
            f'        <div class="card-age-badge">{age_label}</div>\n'
            f'        <div class="card-duration">{duration}</div>\n'
            f'      </div>'
        )
    else:
        poster_html = (
            f'<div class="card-poster" style="background:linear-gradient(150deg,{gradient or "#FF9F43,#FECA57"});">\n'
            f'        {status_html}\n'
            f'        <div class="card-icon">{icon}</div>\n'
            f'        <div class="card-age-badge">{age_label}</div>\n'
            f'        <div class="card-duration">{duration}</div>\n'
            f'      </div>'
        )

    # 主题 tag chips
    tag_html = ''
    if themes:
        chips = []
        for t in themes:
            bg, fg = theme_tag_colors.get(t, ('#F7F5F1', '#888'))
            chips.append(f'<span class="card-tag" style="background:{bg};color:{fg};">{t}</span>')
        tag_html = '<div class="card-tags">\n          ' + '\n          '.join(chips) + '\n        </div>'

    # 价格
    price_html = (
        f'<div class="card-price-row">\n'
        f'          <span class="card-price">{price}</span><span class="card-price-unit">元</span>\n'
        f'          <span class="card-price-hint">起 · 3人团购 / 老营员 / 荣誉营员另有优惠</span>\n'
        f'        </div>'
    )

    # 日期 + 多日期格式化
    if isinstance(dates, list):
        date_str = ' &nbsp;|&nbsp; '.join(dates)
    else:
        date_str = dates

    pill_html = ''
    if meta_pills:
        chips = []
        for p in meta_pills:
            chips.append(f'<span class="card-meta-pill">{p}</span>')
        pill_html = '<div class="card-meta-row">\n          ' + '\n          '.join(chips) + '\n        </div>'

    age_group = f'{age_min}-{age_max}'
    return f'''  <!-- {name} -->
  <div class="{' '.join(classes)}"{extra_attrs} data-age-min="{age_min}" data-age-max="{age_max}" data-themes="{','.join(themes) if themes else ''}" data-dates="{','.join(dates) if isinstance(dates,list) else dates}" data-group="{age_group}">
    <div class="card-main">
      {poster_html}
      <div class="card-body">
        <div class="card-name">{name}</div>
        <div class="card-subtitle"></div>
        <div class="card-dates-wrap">
          <div class="card-date-row">📅 {date_str}</div>
        </div>
        <div class="card-location">📍 成都·{location}</div>
        {pill_html}
        {tag_html}
        {price_html}
      </div>
    </div>
  </div>
'''


THEME_COLORS = {
    '通识': ('#FFF3E0', '#E65100'),
    '学院制': ('#EDE7F6', '#4527A0'),
    '职业探索': ('#E8F5E9', '#1B5E20'),
    '创造': ('#FFFDE7', '#F57F17'),
    '财商': ('#FFF8E1', '#FF8F00'),
    '思辨': ('#E8EAF6', '#283593'),
    '心理': ('#FCE4EC', '#880E4F'),
    '户外': ('#E0F7FA', '#006064'),
}


# === 4 张新文章卡（带 ✓ done） ===
new_cards_with_articles = [
    make_card(
        name='招牌跨学科 · 运气秘籍',
        age_min=12, age_max=16, themes=['通识', '财商'],
        dates=['7.25-7.31'], location='标榜', price=6580,
        theme_tag_colors=THEME_COLORS,
        slug='luck-recipe', status='done',
        poster_img='articles/' + manifest['luck-recipe']['cover'],
        gradient='#FF9F43,#FECA57',
        meta_pills=['🏠 住宿必须', '👥 30人'],
        duration='7天',
    ),
    make_card(
        name='玩笑盲盒营 · 玩耍抗抑',
        age_min=12, age_max=16, themes=['通识', '心理'],
        dates=['8.1-8.7'], location='标榜', price=6580,
        theme_tag_colors=THEME_COLORS,
        slug='joy-blindbox', status='done',
        poster_img='articles/' + manifest['joy-blindbox']['cover'],
        gradient='#FF6B9D,#FFA8A8',
        meta_pills=['🏠 住宿必须', '👥 30人'],
        duration='7天',
    ),
    make_card(
        name='招牌通识 · 重走人类创造之路',
        age_min=9, age_max=12, themes=['通识', '创造'],
        dates=['7.4-7.10', '7.18-7.24'], location='麓客岛', price=6580,
        theme_tag_colors=THEME_COLORS,
        slug='human-history', status='done',
        poster_img='articles/' + manifest['human-history']['cover'],
        gradient='#A8E6CF,#7FCDCD',
        meta_pills=['🏠 住宿必须', '👥 25人'],
        duration='7天',
    ),
    make_card(
        name='硬核成长营 · 命运手斧',
        age_min=9, age_max=12, themes=['户外', '心理'],
        dates=['7.11-7.17'], location='麓客岛', price=6580,
        theme_tag_colors=THEME_COLORS,
        slug='fate-axe', status='done',
        poster_img='articles/' + manifest['fate-axe']['cover'],
        gradient='#F77F3C,#FFB347',
        meta_pills=['🏠 住宿必须', '👥 25人'],
        duration='7天',
    ),
]

# === 9 张毛坯卡片（仅标题/价格/日期，data-status="blank"） ===
blank_cards = [
    # 12-16 缺 2
    make_card(name='第一桶金', age_min=12, age_max=16, themes=['财商'], dates=['7.25-7.31'],
              location='标榜', price=6580, theme_tag_colors=THEME_COLORS,
              status='blank', meta_pills=['🏠 住宿必须', '👥 30人']),
    make_card(name='饥饿游戏', age_min=12, age_max=16, themes=['户外'], dates=['8.1-8.7'],
              location='标榜', price=6580, theme_tag_colors=THEME_COLORS,
              status='blank', meta_pills=['🏠 住宿必须', '👥 30人']),
    # 9-12 缺 7
    make_card(name='火星生存指南', age_min=9, age_max=12, themes=['创造', '思辨'], dates=['7.18-7.24'],
              location='标榜', price=6580, theme_tag_colors=THEME_COLORS,
              status='blank', meta_pills=['🏠 住宿必须', '👥 25人']),
    make_card(name='数学战争', age_min=9, age_max=12, themes=['思辨'], dates=['7.25-7.31'],
              location='标榜', price=6580, theme_tag_colors=THEME_COLORS,
              status='blank', meta_pills=['🏠 住宿必须', '👥 25人']),
    make_card(name='水形物语', age_min=9, age_max=12, themes=['创造'], dates=['7.25-7.31'],
              location='麓客岛', price=6580, theme_tag_colors=THEME_COLORS,
              status='blank', meta_pills=['🏠 住宿必须', '👥 25人']),
    make_card(name='时间玩家', age_min=9, age_max=12, themes=['思辨'], dates=['8.1-8.7'],
              location='标榜', price=6580, theme_tag_colors=THEME_COLORS,
              status='blank', meta_pills=['🏠 住宿必须', '👥 25人']),
    make_card(name='搞笑诺贝尔', age_min=9, age_max=12, themes=['创造', '思辨'], dates=['8.1-8.7'],
              location='标榜', price=6580, theme_tag_colors=THEME_COLORS,
              status='blank', meta_pills=['🏠 住宿必须', '👥 25人']),
    make_card(name='造船 PBL', age_min=9, age_max=12, themes=['创造'], dates=['8.1-8.7'],
              location='麓客岛', price=6580, theme_tag_colors=THEME_COLORS,
              status='blank', meta_pills=['🏠 住宿必须', '👥 25人']),
    make_card(name='定向越野 + AI 工具', age_min=9, age_max=12, themes=['户外', '创造'], dates=['8.1-8.7'],
              location='麓客岛', price=6580, theme_tag_colors=THEME_COLORS,
              status='blank', meta_pills=['🏠 住宿必须', '👥 25人']),
]


# === 插入新卡：12-16 新卡放在 12-16 divider 之后，9-12 新卡放在 9-12 区末尾（12-16 divider 之前） ===
# 新 9-12 卡 = 2 个 article 卡 (human-history, fate-axe) + 7 个 blank 卡
new_9_12 = [new_cards_with_articles[2], new_cards_with_articles[3]] + blank_cards[2:]
new_12_16 = [new_cards_with_articles[0], new_cards_with_articles[1]] + blank_cards[0:2]

# 找 12-16 divider 位置插入 9-12 新卡（在它之前）
divider_12_16 = re.search(r'(\s*<!-- ── 12-16岁 ── -->\s*<div class="age-group-divider" data-group="12-16">.*?</div>\s*</div>)', s, re.DOTALL)
if divider_12_16:
    insert_pos = divider_12_16.start()
    insert_text = '\n' + '\n'.join(new_9_12)
    s = s[:insert_pos] + insert_text + s[insert_pos:]
    print(f'9-12 新卡：插入 {len(new_9_12)} 张')

# 找 14-18 divider 位置插入 12-16 新卡（在它之前）
divider_14_18 = re.search(r'(\s*<!-- ── 14-18岁 ── -->\s*<div class="age-group-divider" data-group="14-18">.*?</div>\s*</div>)', s, re.DOTALL)
if divider_14_18:
    insert_pos = divider_14_18.start()
    insert_text = '\n' + '\n'.join(new_12_16)
    s = s[:insert_pos] + insert_text + s[insert_pos:]
    print(f'12-16 新卡：插入 {len(new_12_16)} 张')


HTML.write_text(s, encoding='utf-8')
print(f'\n✓ index.html 已更新 ({len(s)} 字符)')
