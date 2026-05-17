# -*- coding: utf-8 -*-
"""把"钥匙玩校特色 / 玩伴 / about-strip"搬到"了解我们"抽屉，
把"常见 QA"搬到"常见问答"抽屉。"""
import re
from pathlib import Path

HTML = Path(r'C:/Users/david/kiidschool/index.html')
s = HTML.read_text(encoding='utf-8')


def cut(text, start_marker, end_marker):
    """剪下 text 中从 start_marker 开始到下一个空行+end_marker 之前的段（含 start_marker，不含 end_marker）。"""
    i = text.find(start_marker)
    if i < 0:
        raise ValueError(f'未找到 start_marker: {start_marker[:40]}')
    j = text.find(end_marker, i + len(start_marker))
    if j < 0:
        raise ValueError(f'未找到 end_marker: {end_marker[:40]}')
    cut_text = text[i:j].rstrip() + '\n'
    return text[:i].rstrip() + '\n\n' + text[j:], cut_text


# 1. 剪出 4 块（顺序很重要：先剪 QA，再剪 about-strip，因为 QA 需要 ABOUT 标记作为结束）
s, feature = cut(s, '<!-- 钥匙玩校特色 -->', '<!-- 钥匙玩校玩伴 -->')
s, playmates = cut(s, '<!-- 钥匙玩校玩伴 -->', '<!-- 常见QA -->')
s, qa = cut(s, '<!-- 常见QA -->', '<!-- ABOUT -->')
s, about_strip = cut(s, '<!-- ABOUT -->', '<!-- FOOTER CTA -->')

# 3. 找 filter-sheet 后插入两个新 sheet
new_sheets = f'''
<!-- 关于我们 抽屉 -->
<div class="filter-sheet" id="about-sheet">
  <div class="filter-sheet-bg" onclick="closeAboutSheet()"></div>
  <div class="filter-sheet-content">
    <div class="filter-sheet-handle"></div>
    <div class="filter-sheet-head">
      <span class="filter-sheet-title">🔑 了解钥匙玩校</span>
      <button class="filter-sheet-clear" onclick="closeAboutSheet()">关闭</button>
    </div>

{feature.strip()}

{playmates.strip()}

{about_strip.strip()}
  </div>
</div>

<!-- 常见问答 抽屉 -->
<div class="filter-sheet" id="faq-sheet">
  <div class="filter-sheet-bg" onclick="closeFaqSheet()"></div>
  <div class="filter-sheet-content">
    <div class="filter-sheet-handle"></div>
    <div class="filter-sheet-head">
      <span class="filter-sheet-title">❓ 常见问答</span>
      <button class="filter-sheet-clear" onclick="closeFaqSheet()">关闭</button>
    </div>

{qa.strip()}

    <div style="margin-top: 20px; padding: 16px; background: linear-gradient(135deg, #FFF8F2, #FFE8D8); border-radius: 12px; text-align: center;">
      <div style="font-size: 28px; margin-bottom: 6px;">🤖</div>
      <div style="font-size: 13px; font-weight: 800; color: #1A1A2E;">AI 智能助手</div>
      <div style="font-size: 11.5px; color: #888; margin-top: 4px;">即将开放，对话式回答家长所有疑问</div>
    </div>
  </div>
</div>
'''

# 插在 </filter-sheet> 后（找最后一个 filter-sheet 的关闭）
filter_sheet_close_pat = re.compile(r'(<div class="filter-sheet" id="filter-sheet">.*?</div>\n</div>)', re.DOTALL)
m = filter_sheet_close_pat.search(s)
if not m:
    raise ValueError('找不到 filter-sheet 闭合点')
insert_pos = m.end()
s = s[:insert_pos] + '\n' + new_sheets.strip() + '\n' + s[insert_pos:]

HTML.write_text(s, encoding='utf-8')
print('✓ 完成迁移')
print(f'  钥匙玩校特色: {len(feature)} 字符')
print(f'  钥匙玩校玩伴: {len(playmates)} 字符')
print(f'  about-strip: {len(about_strip)} 字符')
print(f'  常见QA: {len(qa)} 字符')
