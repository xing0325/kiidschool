# 钥匙玩校 · 移动端 IA 重构 + 性能优化 (R2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把首页年龄 tab 改成真横滑 4-panel；底栏 IA 切分为 3 tab + 1 sheet trigger；首屏 MP4 与图片性能优化；弹窗加 drag-to-dismiss。

**Architecture:** 单页静态站，所有改动集中在 `index.html`（CSS、HTML、内联 JS）+ 几张图替换 + 一份汇报 HTML。方案 C：保留现有 34 张手写卡片不重写，初始化时 `cloneNode` 分发到 4 panel。MP4 通过 IntersectionObserver + 当前 panel 双重门控懒挂载 `src`。

**Tech Stack:** 纯 HTML/CSS/原生 JS。ffmpeg 用于 MP4（如需）、Python + Pillow 用于图片压缩。无构建、无测试框架——验收通过 Claude Preview 浏览器工具。

**Spec：** [docs/superpowers/specs/2026-05-18-mobile-ia-perf-redesign-design.md](../specs/2026-05-18-mobile-ia-perf-redesign-design.md)

**Branch：** `feat/2026-revision-r1`（继续推这条分支 = 上线）。每个任务一个 commit，可单独 revert。

---

## File Structure

涉及文件：

- **修改**：`index.html`（3921 行的单文件，按区段改）
- **新建**：`public/pr-report-2026-05-18-r2.html`（甲方汇报）
- **替换**：
  - `images/camps/world.jpg`（4.2 MB → 目标 ≤ 400 KB）
  - `images/playmates/linwenping.png`、`chixiao.png`、`hechao.png`、`lingr.png` → 同名 `.jpg`
  - `images/features/seven-arts.png` → `.jpg`（按需）
- **辅助脚本**（一次性，不进 git）：`.claude/optimize_static_imgs.py`

不在范围：详情页（master-detail）改造、AVIF/WebP 多源、把卡片重写为数据驱动、CDN。

---

## Task 1: 底栏改 4 tab，把「筛选」挪出底栏

**Files:**
- Modify: `index.html`（line ~2921-2937：底栏 4 个按钮；line ~315-322：tab-active 样式；以及 `toggleView` 函数 line ~3314-3317 附近）

**目的：** 把底栏第 1 项从「筛选」改为「首页」，点了切回首页瀑布流视图。「筛选」按钮挪到首页内部，本 task 不实现挪过去（Task 3 做），先把它从底栏拿下来。

- [ ] **Step 1: 改底栏 HTML（line 2921 附近）**

把 `<div class="bottom-bar">` 内 4 个按钮替换为：

```html
<div class="bottom-bar">
  <button class="bottom-bar-btn" data-view-tab="home" onclick="toggleView('home')">
    <span class="bb-icon">🏠</span><span class="bb-label">首页</span>
  </button>
  <button class="bottom-bar-btn" data-view-tab="about" onclick="toggleView('about')">
    <span class="bb-icon">🔑</span><span class="bb-label">了解我们</span>
  </button>
  <button class="bottom-bar-btn" data-view-tab="faq" onclick="toggleView('faq')">
    <span class="bb-icon">❓</span><span class="bb-label">常见问答</span>
  </button>
  <button class="bottom-bar-btn cta" onclick="goToContact()">
    <span class="bb-icon">📞</span><span class="bb-label">咨询报名</span>
  </button>
</div>
```

- [ ] **Step 2: 扩展 `toggleView` 支持 `'home'`**

找到 `toggleView` 函数（line ~3280 起），加 `'home'` 分支——切到 home 时关掉所有 sheet/view 容器（about、faq），高亮底栏首页按钮。具体在 Task 2 一起改完整，本 task 仅占位：

```js
// 临时桩，Task 2 重写
function toggleView(view) {
  // ...existing about/faq logic...
  if (view === 'home') {
    document.getElementById('about-sheet')?.classList.remove('open');
    document.getElementById('faq-sheet')?.classList.remove('open');
    document.body.style.overflow = '';
    document.querySelectorAll('.bottom-bar-btn').forEach(b => b.classList.remove('tab-active'));
    document.querySelector('.bottom-bar-btn[data-view-tab="home"]')?.classList.add('tab-active');
  }
}
```

页面初始化时调用一次 `toggleView('home')` 让首页 tab 默认高亮。

- [ ] **Step 3: preview 验证**

启动 preview，确认：
1. 底栏 4 项显示为「首页 / 了解我们 / 常见问答 / 咨询报名」。
2. 默认进入页面，「首页」icon 高亮。
3. 点「了解我们」/「常见问答」仍然能弹出（旧行为还在，下一 task 重做）。
4. 点「首页」能关掉弹出的 about/faq view，回到瀑布流。

- [ ] **Step 4: Commit**

```bash
git -c user.name=xing0325 -c user.email=xing0325@users.noreply.github.com \
  add index.html && \
git -c user.name=xing0325 -c user.email=xing0325@users.noreply.github.com \
  commit -m "refactor(nav): 底栏改 4 tab，筛选挪出底栏（第 1/N 步）"
```

---

## Task 2: about / faq 由 bottom sheet 改造为一级页面 view

**Files:**
- Modify: `index.html`（line 2980 / 3141 附近的 `about-sheet`、`faq-sheet`；line ~3314-3317 的 toggle 函数；CSS 区段）

**目的：** 让 about / faq 不再是从底部弹起的 sheet 动画，而是与瀑布流并列、整页替换显示的 view。视觉上去掉底部弹起过渡，改为 fade / 瞬切。

- [ ] **Step 1: HTML 结构调整**

外层不再用 `filter-sheet full-page-sheet`，改为：

```html
<section class="view-page" id="view-about" hidden>
  <div class="view-page-head">
    <span class="view-page-title">🔑 了解钥匙玩校</span>
  </div>
  <div class="view-page-body">
    <!-- 复用 about-sheet 内原本的内容 DOM，整段搬进来 -->
  </div>
</section>

<section class="view-page" id="view-faq" hidden>
  <div class="view-page-head">
    <span class="view-page-title">❓ 常见问答</span>
  </div>
  <div class="view-page-body">
    <!-- 复用 faq-sheet 内原本的内容 DOM -->
  </div>
</section>
```

把原 `#about-sheet`、`#faq-sheet` 的内容（去掉 sheet 的 bg、head 关闭按钮、handle）整段搬进新容器。原 sheet 元素整体删除。

- [ ] **Step 2: CSS 加 view-page 样式**

放到 `.bottom-bar` 样式区附近：

```css
/* view-page：一级页面容器，与主内容互斥显示 */
.view-page {
  background: #F7F5F1;
  min-height: 100vh;
  padding-bottom: 80px; /* 留底栏空间 */
}
.view-page[hidden] { display: none; }
.view-page-head {
  position: sticky; top: 0; z-index: 10;
  background: #fff;
  padding: 12px 16px;
  border-bottom: 1px solid #F0EDE8;
}
.view-page-title { font-size: 17px; font-weight: 800; color: #1A1A2E; }
.view-page-body { padding: 16px; }

/* 主页内容容器（home view）：默认显示，切到 about/faq 时隐藏 */
.home-view { }
body.view-about .home-view,
body.view-faq .home-view { display: none; }
body.view-home .view-page { display: none; }
```

并把现有的页面主内容（hero、年龄 tab、camps-list、特色、玩伴等）包裹在 `<div class="home-view">...</div>` 内。

- [ ] **Step 3: 重写 `toggleView`**

```js
function toggleView(view) {
  // view: 'home' | 'about' | 'faq'
  const valid = ['home', 'about', 'faq'];
  if (!valid.includes(view)) return;

  // body class 控制显示
  document.body.classList.remove('view-home', 'view-about', 'view-faq');
  document.body.classList.add('view-' + view);

  // hidden 属性控制 view-page
  document.getElementById('view-about').hidden = (view !== 'about');
  document.getElementById('view-faq').hidden = (view !== 'faq');

  // 底栏高亮
  document.querySelectorAll('.bottom-bar-btn').forEach(b => b.classList.remove('tab-active'));
  document.querySelector(`.bottom-bar-btn[data-view-tab="${view}"]`)?.classList.add('tab-active');

  // 切到新 view 滚回顶（跨 view scrollTop 记忆在 Task 8 加）
  window.scrollTo(0, 0);
}

// 初始化默认 home
toggleView('home');
```

- [ ] **Step 4: preview 验证**

启动 preview：
1. 默认在首页（瀑布流可见）。
2. 点「了解我们」→ 整页切换到 about 内容，底栏「了解我们」高亮，没有底部弹起动画。
3. 点「常见问答」→ 整页切换到 faq。
4. 点「首页」→ 回到瀑布流。
5. 现有 about / faq 内的内容、QR 折叠等子交互仍正常。

- [ ] **Step 5: Commit**

```bash
git -c user.name=xing0325 -c user.email=xing0325@users.noreply.github.com \
  add index.html && \
git -c user.name=xing0325 -c user.email=xing0325@users.noreply.github.com \
  commit -m "refactor(nav): 了解我们/常见问答 由 sheet 改一级页面 view"
```

---

## Task 3: 在首页顶部加「筛选」漏斗按钮

**Files:**
- Modify: `index.html`（年龄 tab 容器附近，spec §3.2 提到的顶部条）

- [ ] **Step 1: 找到年龄 tab 容器**

```bash
grep -n 'age-tabs\|age-tab\b' index.html
```

记下行号。这就是要在它**同一行右侧**插入漏斗的位置。

- [ ] **Step 2: HTML 插入漏斗按钮**

在年龄 tab 容器外层包一个 flex 容器（如果还不是）：

```html
<div class="home-top-bar">
  <div class="age-tabs"><!-- 原 4 个年龄 tab --></div>
  <button class="filter-fab" aria-label="筛选" onclick="openFilterSheet()">
    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M3 5h18M6 12h12M10 19h4"/>
    </svg>
  </button>
</div>
```

- [ ] **Step 3: CSS**

```css
.home-top-bar {
  position: sticky; top: 56px; /* 在 header 下面 */
  z-index: 90;
  background: #F7F5F1;
  display: flex; align-items: center; gap: 8px;
  padding: 8px 12px;
}
.home-top-bar .age-tabs { flex: 1; overflow-x: auto; -webkit-overflow-scrolling: touch; }
.filter-fab {
  flex: 0 0 36px; width: 36px; height: 36px;
  border-radius: 50%; border: 1px solid #E5E2DC;
  background: #fff; color: #1A1A2E;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
}
.filter-fab:active { background: #F5F3EF; }
```

- [ ] **Step 4: preview 验证**

打开首页：年龄 tab 横排在左，漏斗在右；点漏斗弹起筛选 sheet。

- [ ] **Step 5: Commit**

```bash
git -c user.name=xing0325 -c user.email=xing0325@users.noreply.github.com \
  add index.html && \
git -c user.name=xing0325 -c user.email=xing0325@users.noreply.github.com \
  commit -m "feat(home): 顶部加筛选漏斗按钮"
```

---

## Task 4: 首页加 4 panel 横滑骨架（结构 + CSS，无 JS）

**Files:**
- Modify: `index.html`（line 1679 `<div class="camps-list" id="camps-list">` 区域）

**目的：** 先把骨架立起来。把 `camps-list` 用 4-panel 横滑轨道包起来，现有 34 张卡片暂时全部留在「全部」panel 内；其它 3 个 panel 为空容器，下个 task 用 JS 填。

- [ ] **Step 1: HTML 包裹**

把 `<div class="camps-list" id="camps-list">...所有卡片...</div>` 改为：

```html
<div class="panel-swiper" id="panel-swiper">
  <div class="panel-track" id="panel-track">
    <section class="panel" data-panel="all" data-age="all">
      <div class="camps-list" id="camps-list">
        <!-- 原 34 张卡片，原样保留 -->
      </div>
    </section>
    <section class="panel" data-panel="9-12" data-age="9-12">
      <div class="camps-list" data-panel-list="9-12"></div>
    </section>
    <section class="panel" data-panel="12-16" data-age="12-16">
      <div class="camps-list" data-panel-list="12-16"></div>
    </section>
    <section class="panel" data-panel="14-18" data-age="14-18">
      <div class="camps-list" data-panel-list="14-18"></div>
    </section>
  </div>
</div>
```

- [ ] **Step 2: CSS**

```css
.panel-swiper {
  overflow: hidden;
  position: relative;
  touch-action: pan-y; /* 默认让浏览器处理垂直；水平自定义 */
}
.panel-track {
  display: flex;
  width: 400%; /* 4 panel × 100vw */
  transform: translateX(0);
  transition: transform 280ms cubic-bezier(.2,.7,.2,1);
  will-change: transform;
}
.panel-track.dragging { transition: none; }
.panel {
  flex: 0 0 25%; /* 占 track 的 1/4 == 100vw */
  min-height: 60vh;
}
/* 单 panel 内 camps-list 保持原瀑布流样式 */
```

- [ ] **Step 3: preview 验证**

打开首页：
1. 「全部」panel 内瀑布流照常显示。
2. 另外 3 个 panel 是空白容器（DOM 在但内容空）。
3. 页面整体没有横向滚动条溢出。

可临时把 `<body>` 加 `style="background: #ccc"`，然后给 `.panel:not([data-panel="all"]) { background: #ddf; }` 用 devtools 改 `translateX(-100%)` 等验证各 panel 真的拼好了——验证完去掉调试样式。

- [ ] **Step 4: Commit**

```bash
git -c user.name=xing0325 -c user.email=xing0325@users.noreply.github.com \
  add index.html && \
git -c user.name=xing0325 -c user.email=xing0325@users.noreply.github.com \
  commit -m "feat(home): 加 4 panel 横滑骨架（空架子）"
```

---

## Task 5: JS 把 34 张卡片克隆到对应年龄 panel

**Files:**
- Modify: `index.html`（在 `<script>` 区，靠近现有卡片相关 JS 处）

- [ ] **Step 1: 写分发函数**

在 `<script>` 区加：

```js
// === Task 5: 卡片分发到 4 panel ===
function distributeCardsToPanels() {
  const allList = document.getElementById('camps-list');
  if (!allList) return;
  const cards = Array.from(allList.querySelectorAll('.camp-card'));

  const targets = {
    '9-12':  document.querySelector('[data-panel-list="9-12"]'),
    '12-16': document.querySelector('[data-panel-list="12-16"]'),
    '14-18': document.querySelector('[data-panel-list="14-18"]'),
  };

  cards.forEach(card => {
    const min = parseInt(card.dataset.ageMin || '0', 10);
    const max = parseInt(card.dataset.ageMax || '0', 10);
    Object.entries(targets).forEach(([key, list]) => {
      if (!list) return;
      const [k1, k2] = key.split('-').map(Number);
      // 区间重叠判定
      if (max >= k1 && min <= k2) {
        const clone = card.cloneNode(true);
        clone.dataset.cloned = '1';
        clone.dataset.panelKey = key;
        // 给原卡也打上标记，便于 openDetail 区分
        if (!card.dataset.panelKey) card.dataset.panelKey = 'all';
        list.appendChild(clone);
      }
    });
  });
}

// 页面加载后立刻执行（在视频懒挂载和 IO 初始化之前）
document.addEventListener('DOMContentLoaded', distributeCardsToPanels);
```

- [ ] **Step 2: preview 验证**

打开首页 → 打开 devtools console，执行：

```js
['all','9-12','12-16','14-18'].forEach(p => {
  const list = p === 'all'
    ? document.getElementById('camps-list')
    : document.querySelector(`[data-panel-list="${p}"]`);
  console.log(p, list.querySelectorAll('.camp-card').length);
});
```

预期：`all 34`，其它 3 个 panel 是各年龄段子集（≈10/8/5 张，具体看现有 `data-age-min/max`）。

视觉上：在 devtools 把 `.panel-track` 的 `translateX` 改为 `-100%` 等，能看到各 panel 内有对应卡片。

- [ ] **Step 3: Commit**

```bash
git -c user.name=xing0325 -c user.email=xing0325@users.noreply.github.com \
  add index.html && \
git -c user.name=xing0325 -c user.email=xing0325@users.noreply.github.com \
  commit -m "feat(home): JS 把卡片克隆分发到 4 panel"
```

---

## Task 6: 横滑手势 + 年龄 tab 双向绑定

**Files:**
- Modify: `index.html`（script 区）

- [ ] **Step 1: 写状态 + 切 panel 函数**

```js
// === Task 6: panel swiper ===
const PANEL_KEYS = ['all', '9-12', '12-16', '14-18'];
let _panelIndex = 0;
const _panelScroll = [0, 0, 0, 0]; // 各 panel 记忆 window.scrollY

function setPanel(idx, opts = {}) {
  if (idx < 0 || idx >= PANEL_KEYS.length) return;
  // 保存当前 scroll
  _panelScroll[_panelIndex] = window.scrollY;

  _panelIndex = idx;
  const track = document.getElementById('panel-track');
  if (!track) return;
  track.style.transform = `translateX(-${idx * 25}%)`;

  // 年龄 tab 高亮
  document.querySelectorAll('.age-tabs [data-age]').forEach(el => {
    el.classList.toggle('active', el.dataset.age === PANEL_KEYS[idx]);
  });

  // 恢复 scroll（下一帧，给 transform 时间）
  requestAnimationFrame(() => window.scrollTo(0, _panelScroll[idx] || 0));

  // 通知 video IO 重新评估（Task 9 钩子）
  window.dispatchEvent(new CustomEvent('panelchange', { detail: { idx, key: PANEL_KEYS[idx] } }));
}

// 年龄 tab 点击
document.querySelectorAll('.age-tabs [data-age]').forEach(el => {
  el.addEventListener('click', () => {
    const i = PANEL_KEYS.indexOf(el.dataset.age);
    if (i >= 0) setPanel(i);
  });
});
```

- [ ] **Step 2: 写触摸手势**

```js
// 横滑识别
(function attachSwipe() {
  const swiper = document.getElementById('panel-swiper');
  const track = document.getElementById('panel-track');
  if (!swiper || !track) return;

  let startX = 0, startY = 0, startT = 0;
  let dx = 0, dy = 0;
  let locked = null; // 'h' | 'v' | null
  let dragging = false;

  swiper.addEventListener('touchstart', (e) => {
    if (document.body.classList.contains('detail-open')) return;
    if (!document.body.classList.contains('view-home')) return;
    const t = e.touches[0];
    startX = t.clientX; startY = t.clientY; startT = Date.now();
    dx = dy = 0; locked = null; dragging = true;
    track.classList.add('dragging');
  }, { passive: true });

  swiper.addEventListener('touchmove', (e) => {
    if (!dragging) return;
    const t = e.touches[0];
    dx = t.clientX - startX;
    dy = t.clientY - startY;
    if (!locked) {
      if (Math.abs(dx) > 10 || Math.abs(dy) > 10) {
        locked = Math.abs(dx) > Math.abs(dy) ? 'h' : 'v';
      }
    }
    if (locked === 'h') {
      e.preventDefault();
      const w = swiper.clientWidth;
      // 边界拖拽阻尼
      let pct = -(_panelIndex * 25) + (dx / w) * 25;
      if (_panelIndex === 0 && dx > 0) pct = -(_panelIndex * 25) + (dx / w) * 10;
      if (_panelIndex === PANEL_KEYS.length - 1 && dx < 0) pct = -(_panelIndex * 25) + (dx / w) * 10;
      track.style.transform = `translateX(${pct}%)`;
    }
  }, { passive: false });

  swiper.addEventListener('touchend', () => {
    if (!dragging) return;
    dragging = false;
    track.classList.remove('dragging');
    if (locked !== 'h') {
      // 还原
      track.style.transform = `translateX(-${_panelIndex * 25}%)`;
      return;
    }
    const w = swiper.clientWidth;
    const dt = Math.max(1, Date.now() - startT);
    const vx = dx / dt; // px/ms
    const threshold = w * 0.30;
    let next = _panelIndex;
    if (dx < -threshold || vx < -0.5) next = Math.min(_panelIndex + 1, PANEL_KEYS.length - 1);
    else if (dx > threshold || vx > 0.5) next = Math.max(_panelIndex - 1, 0);
    setPanel(next);
  });
})();
```

- [ ] **Step 3: 默认进入「全部」panel 时高亮第一个 tab**

```js
// 初始化（放在所有 DOMContentLoaded 之后）
document.addEventListener('DOMContentLoaded', () => {
  setPanel(0);
});
```

- [ ] **Step 4: preview 验证（preview_start + preview_eval 模拟 touch）**

桌面浏览器：手势用不上，但可以测点击。点 4 个年龄 tab，看：
1. `.panel-track` 的 `transform` 切到对应 `-0% / -25% / -50% / -75%`。
2. 当前 tab 高亮。
3. 切回时滚动位置记忆有效。

手机/dev tools mobile 模拟：
1. 在「全部」panel 上手指水平左滑 ≥ 30% 宽度，松手切到「9-12」。
2. 顶部 tab 跟着高亮。
3. 垂直滚动不受影响（手势锁向后水平不再竞争）。

- [ ] **Step 5: Commit**

```bash
git -c user.name=xing0325 -c user.email=xing0325@users.noreply.github.com \
  add index.html && \
git -c user.name=xing0325 -c user.email=xing0325@users.noreply.github.com \
  commit -m "feat(home): 横滑手势 + 年龄 tab 双向绑定"
```

---

## Task 7: openDetail 兼容克隆卡片（同 slug 多卡）

**Files:**
- Modify: `index.html`（line ~3584 起 `openDetail` 函数；line ~3911 委托点击处）

**问题：** 现 openDetail 用 `card.parentNode` 记 origin。克隆后同 slug 的卡片在 4 个 panel 里都可能被点。回退时只能放回点击的那一个。

- [ ] **Step 1: 点击委托加 panel scope 限制**

找到 line ~3911 `document.addEventListener('click', e => {` 那段，确认点击源 card 是当前 panel 内的——其它 panel 的卡片不可见也基本点不到，但加保护：

```js
document.addEventListener('click', e => {
  if (document.body.classList.contains('detail-open')) return;
  if (e.target.closest('button, a, input, video, .card-qr-panel, .card-detail-panel')) return;
  const card = e.target.closest('.camp-card');
  if (!card) return;
  // 必须是当前 panel 里的卡片（被克隆的卡片可见性也归各自 panel 控制）
  const panel = card.closest('.panel');
  if (panel && panel.dataset.panel !== PANEL_KEYS[_panelIndex]) return;
  openDetail(card);
});
```

- [ ] **Step 2: openDetail 不变**

`openDetail` 已经记录 `_detailOriginCard = card; _detailOriginParent = card.parentNode;` —— 拿到的是被点击的那张克隆卡，回退时就放回它原来的 parent（也就是那个 panel 的 camps-list）。这部分逻辑天然正确，无需改动。

- [ ] **Step 3: preview 验证**

1. 在「全部」panel 点 luck-recipe 卡 → 进详情 → 关闭 → 返回「全部」原位置。
2. 切到「12-16」panel 点同一个 luck-recipe（克隆） → 进详情 → 关闭 → 返回「12-16」原位置。
3. 二者互不影响。

- [ ] **Step 4: Commit**

```bash
git -c user.name=xing0325 -c user.email=xing0325@users.noreply.github.com \
  add index.html && \
git -c user.name=xing0325 -c user.email=xing0325@users.noreply.github.com \
  commit -m "fix(detail): 点击委托加 panel scope，避免点中非当前 panel 的克隆卡"
```

---

## Task 8: 一级页面 scrollTop 记忆（首页/about/faq）

**Files:**
- Modify: `index.html`（toggleView 内）

- [ ] **Step 1: 加跨 view 滚动记忆**

```js
const _viewScroll = { home: 0, about: 0, faq: 0 };
let _currentView = 'home';

function toggleView(view) {
  const valid = ['home', 'about', 'faq'];
  if (!valid.includes(view)) return;

  // 保存当前 view 的 scroll
  _viewScroll[_currentView] = window.scrollY;
  _currentView = view;

  document.body.classList.remove('view-home', 'view-about', 'view-faq');
  document.body.classList.add('view-' + view);
  document.getElementById('view-about').hidden = (view !== 'about');
  document.getElementById('view-faq').hidden = (view !== 'faq');

  document.querySelectorAll('.bottom-bar-btn').forEach(b => b.classList.remove('tab-active'));
  document.querySelector(`.bottom-bar-btn[data-view-tab="${view}"]`)?.classList.add('tab-active');

  requestAnimationFrame(() => window.scrollTo(0, _viewScroll[view] || 0));
}
```

注意 home view 的 scroll 复原与 panel 的 `_panelScroll` 是两层：toggleView 控制一级页面间记忆，panel 内年龄 tab 间记忆走 setPanel。home view 复原时还需要再恢复当前 panel 的 scroll；由于 setPanel 已经在 panelchange 时做了 scrollTo，但切回 home 走的是 toggleView 路径——做法：toggleView('home') 后调用 `setPanel(_panelIndex, { restoreScroll: true })`，或更简单：

```js
if (view === 'home') {
  requestAnimationFrame(() => window.scrollTo(0, _panelScroll[_panelIndex] || _viewScroll.home || 0));
}
```

- [ ] **Step 2: preview 验证**

1. 首页瀑布流滑到中部 → 切到「了解我们」滑到底部 → 切回首页 → 仍在瀑布流原位置。
2. 切「常见问答」滑到中部 → 切「了解我们」 → 切回「常见问答」→ 在原位置。

- [ ] **Step 3: Commit**

```bash
git -c user.name=xing0325 -c user.email=xing0325@users.noreply.github.com \
  add index.html && \
git -c user.name=xing0325 -c user.email=xing0325@users.noreply.github.com \
  commit -m "feat(nav): 一级页面 view 之间记忆 scrollTop"
```

---

## Task 9: MP4 懒挂载 src + IntersectionObserver 视口控制

**Files:**
- Modify: `index.html`（所有 `<video class="poster-img" ...>` 标签 + script 区）

- [ ] **Step 1: 把所有 video 的 `src` 改为 `data-src`、`preload="none"`、移除 autoplay**

搜索：

```bash
grep -n 'class="poster-img"' index.html | head -20
```

针对所有 `<video class="poster-img" ...>`，把：

```html
<video class="poster-img" src="images/camps/X.mp4" autoplay loop muted playsinline ... preload="auto" ...>
```

改为（注意保留 `loop muted playsinline`，删 `autoplay`，加 `data-src`、`preload="none"`，保留原有 `onerror`）：

```html
<video class="poster-img" data-src="images/camps/X.mp4" loop muted playsinline webkit-playsinline x5-video-player-type="h5-page" x5-video-player-fullscreen="false" preload="none" ...>
```

> 如果 video 数量多（≈9 个），可以用 Edit 的 `replace_all=true` 一次性把 `autoplay loop muted` 替换成 `loop muted`，再分别用 Edit 把每个 `src="images/camps/...mp4"` 改为 `data-src=`。或者写个一次性 Python 脚本搞定，但要小心非首屏 hero 视频也别误伤——首屏 hero 处理见 Step 3。

- [ ] **Step 2: 加 IO 控制器**

```js
// === Task 9: video lazy mount + IO ===
const _videoIO = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    const v = entry.target;
    if (!entry.isIntersecting) {
      v.pause(); // 不卸 src，避免 iOS 重挂黑屏
      return;
    }
    // 仅当所在 panel 是当前 panel 才挂 src + 播
    const panel = v.closest('.panel');
    if (panel && panel.dataset.panel !== PANEL_KEYS[_panelIndex]) return;
    if (!v.src && v.dataset.src) {
      v.src = v.dataset.src;
    }
    v.play().catch(() => { /* 微信内核可能拒绝，忽略 */ });
  });
}, { rootMargin: '100px 0px', threshold: 0.1 });

function rebindVideoIO() {
  document.querySelectorAll('video.poster-img[data-src]').forEach(v => _videoIO.observe(v));
}

// 切 panel 时把非当前 panel 的 video 都暂停
window.addEventListener('panelchange', (e) => {
  document.querySelectorAll('video.poster-img').forEach(v => {
    const panel = v.closest('.panel');
    if (!panel || panel.dataset.panel !== e.detail.key) {
      v.pause();
    } else {
      // 当前 panel：让 IO 决定具体哪些 play
    }
  });
});

document.addEventListener('DOMContentLoaded', () => {
  rebindVideoIO();
});
```

- [ ] **Step 3: 首屏 hero 视频特殊处理（如有）**

确认 hero 区是否含 `<video>`：

```bash
grep -nE 'class="hero|hero-' index.html | head -10
grep -n '<video' index.html | head -5
```

若 hero 视频不在 `.panel-swiper` 内（属于 home view 的 hero 部分，不分 panel），让它保留 autoplay：写一个 `data-no-iolazy` 标记，让 IO 跳过：

```js
// rebindVideoIO 内
document.querySelectorAll('video.poster-img[data-src]:not([data-no-iolazy])').forEach(v => _videoIO.observe(v));
```

并给 hero 的 video 加 `data-no-iolazy` + 保留 `autoplay src=...`。

- [ ] **Step 4: preview + DevTools 验证**

1. 打开首页，DevTools → Performance/Network。
2. 首屏可见区只有 1-3 个 video 在 playing 状态（看 Network 是否有对应 mp4 请求）。
3. 滑到瀑布流下方 → 之前的 video 进入「不可见」就暂停（DevTools 元素面板看 `currentTime` 不变）；下方进入视口的开始播。
4. 切到「9-12」panel，「全部」panel 里的 video 全部 pause。
5. 切回「全部」，原来在视口的恢复 play。

- [ ] **Step 5: Commit**

```bash
git -c user.name=xing0325 -c user.email=xing0325@users.noreply.github.com \
  add index.html && \
git -c user.name=xing0325 -c user.email=xing0325@users.noreply.github.com \
  commit -m "perf(video): MP4 懒挂载 src + IO 视口 + panel 双重门控"
```

---

## Task 10: 静态图压缩（world.jpg / playmate PNG → JPG）

**Files:**
- Create: `.claude/optimize_static_imgs.py`（一次性脚本）
- Replace: `images/camps/world.jpg`、`images/playmates/*.png` → `.jpg`
- Modify: `index.html`（更新 PNG → JPG 的引用路径）

- [ ] **Step 1: 写一次性 Python 脚本**

`.claude/optimize_static_imgs.py`：

```python
"""一次性压缩首屏大图。运行：python .claude/optimize_static_imgs.py"""
from PIL import Image
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (输入路径, 输出路径, 最大宽, JPG quality)
JOBS = [
    ("images/camps/world.jpg",            "images/camps/world.jpg",            1080, 80),
    ("images/playmates/linwenping.png",   "images/playmates/linwenping.jpg",   800,  82),
    ("images/playmates/chixiao.png",      "images/playmates/chixiao.jpg",      800,  82),
    ("images/playmates/hechao.png",       "images/playmates/hechao.jpg",       800,  82),
    ("images/playmates/lingr.png",        "images/playmates/lingr.jpg",        800,  82),
    ("images/features/seven-arts.png",    "images/features/seven-arts.jpg",    1000, 82),
]

for inp, outp, max_w, q in JOBS:
    src = ROOT / inp
    dst = ROOT / outp
    if not src.exists():
        print(f"SKIP (missing): {inp}")
        continue
    before = src.stat().st_size
    im = Image.open(src).convert("RGB")
    if im.width > max_w:
        ratio = max_w / im.width
        im = im.resize((max_w, int(im.height * ratio)), Image.LANCZOS)
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, "JPEG", quality=q, optimize=True, progressive=True)
    after = dst.stat().st_size
    print(f"OK  {inp} -> {outp}  {before/1024:.0f}KB -> {after/1024:.0f}KB  ({100*after/before:.0f}%)")
```

- [ ] **Step 2: 跑脚本**

```bash
python .claude/optimize_static_imgs.py
```

预期输出：每行打印 KB 对比。`world.jpg` 应从 ~4200 KB 降到 < 500 KB；玩伴 PNG 各 2-3 MB 降到 < 250 KB。

- [ ] **Step 3: 删除被替换的 PNG**

```bash
git rm images/playmates/linwenping.png \
       images/playmates/chixiao.png \
       images/playmates/hechao.png \
       images/playmates/lingr.png \
       images/features/seven-arts.png
```

`world.jpg` 是原地覆盖，不用 rm。

- [ ] **Step 4: 更新 index.html 引用**

```bash
grep -nE 'playmates/(linwenping|chixiao|hechao|lingr)\.png|features/seven-arts\.png' index.html
```

把每处 `.png` 路径改成 `.jpg`。用 Edit `replace_all=true`，逐文件名：

```
images/playmates/linwenping.png → images/playmates/linwenping.jpg
images/playmates/chixiao.png    → images/playmates/chixiao.jpg
images/playmates/hechao.png     → images/playmates/hechao.jpg
images/playmates/lingr.png      → images/playmates/lingr.jpg
images/features/seven-arts.png  → images/features/seven-arts.jpg
```

- [ ] **Step 5: preview 验证**

打开首页：
1. hero 后面的 world.jpg 仍显示，肉眼几乎看不出质量损失。
2. 玩伴头像照常显示。
3. 七艺图标照常显示。
4. DevTools Network → Img 列：world.jpg 体积 < 500 KB，玩伴 jpg 各 < 250 KB。

- [ ] **Step 6: Commit**

```bash
git -c user.name=xing0325 -c user.email=xing0325@users.noreply.github.com \
  add -u && \
git -c user.name=xing0325 -c user.email=xing0325@users.noreply.github.com \
  add images/playmates/*.jpg images/features/*.jpg .claude/optimize_static_imgs.py && \
git -c user.name=xing0325 -c user.email=xing0325@users.noreply.github.com \
  commit -m "perf(img): world.jpg 4.2MB→<500KB；玩伴/七艺 PNG→JPG"
```

---

## Task 11: 静态图全面补 `loading="lazy"` / `decoding="async"` / `width|height`

**Files:**
- Modify: `index.html`

**目的：** 让首屏 viewport 之外的所有 `<img>` 都不阻塞首屏。

- [ ] **Step 1: 列出未带 lazy 的 img**

```bash
grep -nE '<img(?![^>]*loading="lazy")[^>]*>' index.html | head -30
```

逐一判断是否首屏可见（hero 内的 logo 等保留 eager），其余加 `loading="lazy" decoding="async"`。

- [ ] **Step 2: 加 width/height 防抖动（按经验设值）**

对卡片封面图（统一 16:9 比例）以及其它已知比例图，加 `width` 和 `height` 属性（仅 CSS aspect-ratio 也行）。如果在 CSS 里已经用 `.poster-img { aspect-ratio: 16/9; }` 控制，则不必每张加。检查：

```bash
grep -nE '\.poster-img\s*\{' index.html | head -5
```

如果未设，在 `.poster-img` 样式里加：

```css
.poster-img { aspect-ratio: 16 / 9; width: 100%; height: auto; }
```

- [ ] **Step 3: preview 验证**

DevTools Performance：滚到首屏正下方时不再出现明显的 layout shift；Network → Img 首屏请求数下降。

- [ ] **Step 4: Commit**

```bash
git -c user.name=xing0325 -c user.email=xing0325@users.noreply.github.com \
  add index.html && \
git -c user.name=xing0325 -c user.email=xing0325@users.noreply.github.com \
  commit -m "perf(img): 全面 lazy + decoding=async + aspect-ratio 防抖动"
```

---

## Task 12: Bottom sheet 加 drag-to-dismiss

**Files:**
- Modify: `index.html`（filter-sheet 是唯一保留的 sheet，咨询报名也是 sheet——找它的容器）

- [ ] **Step 1: 列出现存所有 sheet**

```bash
grep -n 'class="filter-sheet\|class="qr-sheet\|class="contact-sheet' index.html
```

应剩下：`#filter-sheet`（筛选）以及咨询报名相关的 sheet（goToContact 弹起的）。一旦 about/faq 已在 Task 2 改成 view-page，此处只剩这两个 sheet。

- [ ] **Step 2: 通用 drag-to-dismiss 函数**

```js
// === Task 12: drag-to-dismiss ===
function attachDragDismiss(sheetEl, closeFn) {
  const content = sheetEl.querySelector('.filter-sheet-content, .sheet-content');
  if (!content) return;
  let startY = 0, startT = 0, dy = 0, dragging = false;

  function onStart(e) {
    // 只有在 sheet 内部 scroll 到顶时才识别下滑
    if (content.scrollTop > 0) return;
    const t = (e.touches ? e.touches[0] : e);
    startY = t.clientY; startT = Date.now(); dy = 0; dragging = true;
    content.style.transition = 'none';
  }
  function onMove(e) {
    if (!dragging) return;
    const t = (e.touches ? e.touches[0] : e);
    dy = t.clientY - startY;
    if (dy < 0) dy = 0; // 只允许下滑
    content.style.transform = `translateY(${dy}px)`;
  }
  function onEnd() {
    if (!dragging) return;
    dragging = false;
    content.style.transition = '';
    const dt = Math.max(1, Date.now() - startT);
    const vy = dy / dt;
    if (dy > 100 || vy > 0.5) {
      // 关
      content.style.transform = '';
      closeFn();
    } else {
      content.style.transform = '';
    }
  }

  content.addEventListener('touchstart', onStart, { passive: true });
  content.addEventListener('touchmove',  onMove,  { passive: true });
  content.addEventListener('touchend',   onEnd);
}

document.addEventListener('DOMContentLoaded', () => {
  const filter = document.getElementById('filter-sheet');
  if (filter) attachDragDismiss(filter, () => closeFilterSheet());
  // 同样为咨询报名的 sheet 挂上（id 看实际命名）
  const contact = document.getElementById('contact-sheet');
  if (contact) attachDragDismiss(contact, () => closeContactSheet?.());
});
```

- [ ] **Step 3: preview 验证（DevTools Mobile）**

1. 点漏斗 → 筛选 sheet 弹起。手指按住 sheet 顶部 handle 处或上半部，往下拖 > 100 px → sheet 关闭。
2. 拖 < 100 px 松手 → sheet 回弹。
3. 如果 sheet 内部有滚动条且 scrollTop > 0，下滑应被内部滚动接管，不触发关 sheet。
4. 咨询报名 sheet 同上。

- [ ] **Step 4: Commit**

```bash
git -c user.name=xing0325 -c user.email=xing0325@users.noreply.github.com \
  add index.html && \
git -c user.name=xing0325 -c user.email=xing0325@users.noreply.github.com \
  commit -m "feat(sheet): bottom sheet 加 drag-to-dismiss"
```

---

## Task 13: 写甲方汇报 HTML

**Files:**
- Create: `public/pr-report-2026-05-18-r2.html`

**目的：** 给甲方看的本轮更新汇报。模仿 PR #83 的 `public/pr-report.html` 模板结构：左侧导航 + 右侧分块陈述。

- [ ] **Step 1: 找老模板参考（如有）**

```bash
git log --all --oneline --diff-filter=A -- 'public/pr-report*.html' | head -5
git show <旧commit>:public/pr-report.html | head -50
```

如果旧模板不在当前分支但在历史里，可以 `git show <hash>:path` 取出来作为骨架。否则按下面骨架直接写。

- [ ] **Step 2: 写报告骨架**

`public/pr-report-2026-05-18-r2.html`：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>钥匙玩校 R2 更新汇报 · 2026-05-18</title>
  <style>
    body { font-family: -apple-system, "PingFang SC", sans-serif; background: #F7F5F1; color: #1A1A2E; margin: 0; }
    .layout { display: flex; max-width: 1080px; margin: 0 auto; }
    nav.toc { width: 200px; padding: 24px 16px; position: sticky; top: 0; align-self: flex-start; height: 100vh; overflow-y: auto; }
    nav.toc a { display: block; padding: 6px 8px; color: #444; text-decoration: none; border-radius: 4px; }
    nav.toc a:hover { background: #ECE9E2; color: #FF6B35; }
    main { flex: 1; padding: 24px 32px; background: #fff; }
    h1 { font-size: 28px; margin: 0 0 8px; }
    h2 { font-size: 20px; margin: 32px 0 12px; padding-bottom: 6px; border-bottom: 2px solid #FF6B35; }
    h3 { font-size: 16px; margin: 16px 0 8px; }
    .meta { color: #888; font-size: 13px; margin-bottom: 24px; }
    .badge { display: inline-block; padding: 2px 8px; background: #FF6B35; color: #fff; border-radius: 10px; font-size: 11px; margin-right: 6px; }
    ul.changes li { margin: 8px 0; }
    pre, code { background: #F0EDE8; padding: 2px 6px; border-radius: 3px; font-size: 13px; }
    pre { padding: 12px; overflow-x: auto; }
    .compare { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 12px 0; }
    .compare div { background: #FAFAFA; padding: 12px; border-radius: 6px; text-align: center; }
    .compare img { max-width: 100%; border: 1px solid #E5E2DC; border-radius: 4px; }
  </style>
</head>
<body>
  <div class="layout">
    <nav class="toc">
      <a href="#overview">概览</a>
      <a href="#ia">底栏 IA 改造</a>
      <a href="#swipe">首页年龄横滑</a>
      <a href="#perf">性能优化</a>
      <a href="#sheet">弹窗下滑收起</a>
      <a href="#files">文件改动</a>
      <a href="#verify">验收清单</a>
    </nav>
    <main>
      <h1>钥匙玩校 2026 夏令营 · R2 更新汇报</h1>
      <div class="meta">2026-05-18 · 分支 feat/2026-revision-r1 · <a href="https://xing0325.github.io/kiidschool/">线上预览</a></div>

      <h2 id="overview">概览</h2>
      <p>本轮针对同事/家长在移动端反馈的两个痛点：<b>加载慢</b> 与 <b>页面间切换不顺</b>，做了一次交互架构与性能的并行重构。改动均集中在 <code>index.html</code> 与几张大图。</p>

      <h2 id="ia">① 底栏信息架构重新切分</h2>
      <h3>变化前</h3>
      <ul class="changes">
        <li>底栏：筛选 / 了解我们 / 常见问答 / 咨询报名 —— 4 项混杂两种交互</li>
        <li>了解我们 / 常见问答 都是从底部弹起的 sheet</li>
      </ul>
      <h3>变化后</h3>
      <ul class="changes">
        <li>底栏：<b>首页 / 了解我们 / 常见问答 / 咨询报名</b> —— 前 3 真 tab 切换，后 1 弹窗</li>
        <li>「筛选」漏斗按钮挪到<b>首页顶部右侧</b></li>
        <li>了解我们 / 常见问答 成为与瀑布流并列的<b>一级页面</b>（如小红书首页/市集/消息/我的）</li>
        <li>3 个一级页面各自记忆 scrollTop</li>
      </ul>

      <h2 id="swipe">② 首页年龄段「真横滑」4 panel</h2>
      <p>原来是点击 tab + CSS 过滤；现在是<b>真 4-panel 横滑</b>，类小红书发现/关注/同城。</p>
      <ul class="changes">
        <li>4 个 panel：全部 / 9-12 / 12-16 / 14-18</li>
        <li>手指横滑 ≥ 30% 宽度即切；点击 tab 也可切</li>
        <li>每个 panel 独立记忆滚动位置</li>
        <li>实现细节：现有 34 张卡片不重写，初始化时按年龄区间克隆到对应 panel</li>
      </ul>

      <h2 id="perf">③ 移动端加载性能</h2>
      <h3>MP4 封面动图</h3>
      <ul class="changes">
        <li>原：9 个 MP4 同时 <code>preload="auto"</code> + <code>autoplay</code></li>
        <li>新：所有 MP4 <code>src</code> 改 <b>懒挂载</b>（<code>data-src</code>），<code>preload="none"</code></li>
        <li>IntersectionObserver 控制：仅<b>当前 panel + 在视口</b>的 MP4 挂 src 并播放</li>
        <li>切 panel 时旧 panel 的 MP4 全部 pause</li>
      </ul>
      <h3>静态图压缩</h3>
      <ul class="changes">
        <li><code>images/camps/world.jpg</code>：4.2 MB → &lt; 500 KB</li>
        <li>玩伴 PNG（林文平/赤霄/何潮/凌儿）→ JPG，每张 &lt; 250 KB</li>
        <li>七艺图标 PNG → JPG</li>
        <li>首屏外 <code>&lt;img&gt;</code> 全面补 <code>loading="lazy" decoding="async"</code>，加 <code>aspect-ratio</code> 防抖动</li>
      </ul>

      <h2 id="sheet">④ 底部弹窗下滑收起</h2>
      <ul class="changes">
        <li>筛选 sheet、咨询报名 sheet 均支持<b>按住下滑关闭</b></li>
        <li>阈值：位移 &gt; 100 px 或速度 &gt; 0.5 px/ms</li>
        <li>仅在 sheet 内部 <code>scrollTop=0</code> 时识别（否则交给内部滚动）</li>
        <li>原「点空白处关闭」「点关闭按钮关闭」保留</li>
      </ul>

      <h2 id="files">文件改动</h2>
      <pre>index.html                            修改（结构 + CSS + JS）
images/camps/world.jpg                替换（压缩）
images/playmates/*.jpg                新增（替代 PNG）
images/features/seven-arts.jpg        新增（替代 PNG）
.claude/optimize_static_imgs.py       新增（一次性压缩脚本）
public/pr-report-2026-05-18-r2.html   新增（本文件）</pre>

      <h2 id="verify">验收清单</h2>
      <ul class="changes">
        <li>✅ 底栏 4 项：首页 / 了解我们 / 常见问答 / 咨询报名</li>
        <li>✅ 首页顶部右侧漏斗按钮可弹起筛选</li>
        <li>✅ 4 个年龄段可手指横滑切换 + 各自记忆滚动位置</li>
        <li>✅ 一级页面切换无底部弹起动画、各自记忆滚动</li>
        <li>✅ 首屏总传输字节相较上版下降 ≥ 50%（DevTools Network）</li>
        <li>✅ 同屏仅当前 panel 内可见 MP4 处于 playing</li>
        <li>✅ Bottom sheet 按住下滑可关闭</li>
      </ul>
    </main>
  </div>
</body>
</html>
```

- [ ] **Step 3: 用 preview 验证报告本身打得开**

```js
// preview_start 后访问 /public/pr-report-2026-05-18-r2.html
```

- [ ] **Step 4: 把可点本地链接发给用户**

回复里附上 `file:///C:/Users/david/kiidschool/public/pr-report-2026-05-18-r2.html` 以及预期的 GitHub Pages 路径 `https://xing0325.github.io/kiidschool/public/pr-report-2026-05-18-r2.html`。

- [ ] **Step 5: Commit**

```bash
mkdir -p public
git -c user.name=xing0325 -c user.email=xing0325@users.noreply.github.com \
  add public/pr-report-2026-05-18-r2.html && \
git -c user.name=xing0325 -c user.email=xing0325@users.noreply.github.com \
  commit -m "docs(report): 甲方汇报 HTML · 2026-05-18 R2"
```

---

## Task 14: 端到端冒烟 + 决定是否推 origin

**Files:** 无新增

- [ ] **Step 1: preview 全流程**

启动 preview，按验收清单逐条过：

1. 默认进入首页，底栏「首页」高亮，漏斗在右上。
2. 手势横滑 4 个 panel，tab 跟随高亮；各 panel 滚动位置记忆。
3. 点底栏「了解我们」切换；再回首页仍在原位置。
4. 任一详情卡点击 → 详情打开 → 关闭 → 回到原 panel 原位置。
5. 漏斗 → 筛选 sheet；按住下滑 → 关闭。
6. 「咨询报名」→ QR sheet；按住下滑 → 关闭。
7. DevTools Network：首屏 transfer 总量比上版小 ≥ 50%；MP4 不再首屏全部并发。

- [ ] **Step 2: 跑一遍 git status / log，确认本轮 commit 都已 in**

```bash
git status
git log origin/feat/2026-revision-r1..HEAD --oneline
```

预期：本地领先 origin ≈ 12-13 个 commit。

- [ ] **Step 3: 询问用户是否推 origin（推 = 上线）**

不要自动推。问用户：「本轮 12+ 个 commit，跑预览看着 OK 吗？我推 origin 就是上线了。」

- [ ] **Step 4: 用户点头 → 推**

```bash
git -c user.name=xing0325 -c user.email=xing0325@users.noreply.github.com \
  push origin feat/2026-revision-r1
```

---

## Self-Review

### 1. Spec coverage

| Spec 节 | 任务 |
|---|---|
| §3.1 底栏 IA | Task 1, 2 |
| §3.2 首页 4 panel 横滑 | Task 4, 5, 6 |
| §3.3 一级页面状态 | Task 8 |
| §4.1 卡片分发 | Task 5 |
| §4.2 MP4 双重门控 | Task 9 |
| §4.3 静态图压缩 + lazy | Task 10, 11 |
| §4.4 底栏一级页面 | Task 2 |
| §4.5 drag-to-dismiss | Task 12 |
| §6 验收 1-7 | Task 14 端到端 |
| §6 验收 8 甲方汇报 HTML | Task 13 |
| §7 风险：克隆 vs openDetail | Task 7 |

全部覆盖。

### 2. Placeholder scan

无 TBD / 待补 / TODO 注释。每段都有完整代码示例。

### 3. Type consistency

- `PANEL_KEYS = ['all', '9-12', '12-16', '14-18']` 在 Task 6 定义，Task 9 复用——名称一致。
- `setPanel(idx)` 在 Task 6 定义并在 Task 9 触发 `panelchange` 事件——签名一致。
- `attachDragDismiss(sheetEl, closeFn)` 在 Task 12 定义，调用处传 `closeFilterSheet`、`closeContactSheet`——签名一致。
- `_viewScroll` / `_panelScroll` 是两个独立对象——分工清楚（一级页面 vs 年龄 panel）。

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-18-mobile-ia-perf-redesign-r2.md`.

Two execution options:

**1. Subagent-Driven (recommended)** — 每个 task 派一个新 subagent 干，主会话评审；改动隔离、回滚粒度好。适合这种 14 task 的大计划。

**2. Inline Execution** — 在当前会话用 executing-plans 一气呵成，分批 checkpoint。上下文紧凑、不用切换。

哪个？
