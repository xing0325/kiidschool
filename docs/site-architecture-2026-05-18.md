# 钥匙玩校 2026 夏令营官网 · 架构与交互简报

**目的**：给一位网页设计/前端专家做评估优化用。

**线上**：https://xing0325.github.io/kiidschool/
**源码**：https://github.com/xing0325/kiidschool/tree/feat/2026-revision-r1
**日期**：2026-05-18 · commit `6876c9c`
**主受众**：国内 4G/5G 移动端浏览（90%+ 微信内置浏览器），辅以桌面查看。
**业务目标**：让家长（35-50 岁）在 5 分钟内挑出适合自家孩子的夏令营，扫码加客服。

---

## 1 · 技术栈

| 层 | 选型 | 备注 |
|---|---|---|
| 构建 | 无构建 | 纯手写 HTML/CSS/原生 JS，单文件 `index.html` (≈4200 行) |
| 部署 | GitHub Pages | 直接服务 `feat/2026-revision-r1` 分支根目录，push = 上线 |
| 静态资源 CDN | jsDelivr (`cdn.jsdelivr.net/gh/...@<hash>`) | 用 commit hash 钉版本；HTML 走 GitHub Pages，图片/视频走 CDN |
| 域名 | 在迁移中 | 拟将 kiidschool.cn 指向 GitHub Pages，长期计划搬到阿里云/腾讯云 + ICP 备案 |
| 文章数据 | 静态 HTML | `articles/<slug>/article.html` 共 11 篇，来自微信公众号爬取后清洗 |
| 图片 | JPG q72 ≤800w / PNG（含 alpha）/ MP4 480p crf28 | 详情页素材在 `articles/_shared/` |

---

## 2 · 信息架构 (IA)

底栏 4 项：**首页 / 了解我们 / 常见问答 / 咨询报名**
- 前 3 个是一级页面 tab（整页替换，类小红书）
- 「咨询报名」是 bottom-sheet 触发（弹两张客服二维码），不切 tab

```
首页 (默认)
├─ Header (sticky)
├─ Hero（标题 + 品牌四行 + 「20+主题、9-18岁、7月4日-8月17日」）
├─ 顶部条 (sticky)
│   ├─ 年龄 Tabs：全部 | 9-12 | 12-16 | 14-18
│   └─ 筛选漏斗按钮 (右)
├─ 周次档期 chips
├─ 结果条「共 N 个营期」
├─ Panel Swiper (横滑 4 panel)
│   ├─ panel[all]    — 25 张原始卡片
│   ├─ panel[9-12]   — 15 张 (克隆)
│   ├─ panel[12-16]  — 6 张  (克隆)
│   └─ panel[14-18]  — 4 张  (克隆)
├─ 营地实景照片横滑相册 + 灯箱
├─ Footer CTA (报名 + 关注公众号)
└─ → 详情页 (master-detail，body class .detail-open)

了解我们 (一级页面)
└─ 钥匙玩校特色 (7艺/PBL/玩伴等)

常见问答 (一级页面)
└─ 5 条 QA：接送 / 手机管理 / 洗衣 / 住宿 / 报到时间

弹层 (Sheets / Modals)
├─ 筛选 sheet     (从底部弹起，drag-to-dismiss)
└─ 咨询报名 sheet (两张二维码，drag-to-dismiss)
```

---

## 3 · 核心数据模型

每张营期卡片 (`.camp-card`) 的属性：

```
data-age-min     int   起始年龄
data-age-max     int   终止年龄
data-group       enum  '9-12' | '12-16' | '14-18' | 'recommend'
data-themes      csv   见下方 10 标签
data-dates       csv   '7.4-7.10,7.11-7.17,...' (一卡 N 期)
data-status      enum  'done' | 'todo' | 'blank'  (✓ / ✗ / ?)
data-slug        str?  对应 articles/<slug>/article.html
data-rank        int?  recommend 卡排序
data-cloned      bool  分发后的克隆卡标识
data-panel-key   enum  指明所在 panel
```

**10 个主题标签**（多标签，OR 命中）：
🎓 招牌学院 · 🧠 学习力 · 🌍 跨学科 · 💪 心理抗挫 · 🏕️ 户外冒险 · 🔍 思辨解谜 · 🤖 AI科创 · 🎭 艺术叙事 · 💰 财商 · 🚀 职业探索

**总量**：25 张产品卡 / 31 个营期次数（按 `data-dates` 累加）/ 10 篇详情文章已接入

---

## 4 · 关键交互

### 4.1 首页年龄段横滑切换
- 4 个 panel 横排，CSS `transform: translateX()` 平移
- 手势：手指水平位移 > 30% 宽度 或 速度 > 0.5 px/ms 触发切换；首 10px 内判定方向锁
- 各 panel 独立记忆 `scrollTop`（小红书同款体验）
- panel 内容由 JS 在 DOMContentLoaded 后用 `cloneNode` 从「全部」panel 分发
- panel 高度跟随当前内容（`panel-track.style.height = currentPanel.scrollHeight`），避免短 panel 下方留白
- 视频播放双重门控：仅当 panel = active **且** 元素 in viewport 才挂 `src` + `play()`

### 4.2 一级页面切换 (底栏 tab)
- `body.view-home` / `body.view-about` / `body.view-faq` 三套互斥 CSS 类
- `display: none` 切显示，无过渡动画
- 各 view 独立记忆 `window.scrollY`，切回时恢复

### 4.3 筛选
- Bottom sheet 弹起；包含：年龄段、主题（10 chip 多选）、地点、日期区间
- chip 多选 OR 逻辑（任一命中即显示）
- 筛选后克隆卡片同步 hidden 状态
- result-count 显示「当前 panel + 当前筛选」下的营期次数（不是卡片数）

### 4.4 Drag-to-dismiss
- Sheet 内部 `scrollTop=0` 时识别下滑手势
- 阈值：位移 > 100px 或速度 > 0.5px/ms 关闭
- 兼容点击空白处关闭

### 4.5 详情页 (master-detail)
- 同 DOM 切换（不路由），点卡 → `body.detail-open` → 隐藏列表、显示详情
- 详情内容 = 微信公众号原文 + 阅读进度条 + 侧边 Dot Rail TOC + 估读时间
- 文章 HTML 通过 fetch → innerHTML 注入；图片/视频走 jsDelivr CDN
- 物理返回键关闭详情（监听 popstate）

---

## 5 · 性能策略

| 项 | 做法 |
|---|---|
| MP4 封面动图 | `src` 移到 `data-src`、`preload="none"`、移除 `autoplay`；IntersectionObserver + panel 双重门控按需挂 src |
| 图片 lazy | 全部 `<img>` 带 `loading="lazy" decoding="async"`，`.poster-img` 走 `aspect-ratio: 16/9` 防抖动 |
| 静态资源压缩 | JPG q72/≤800w，PNG 不透明者转 JPG 同 .png 文件名，MP4 480p crf28；详情页素材 28MB → 18MB (-41%) |
| CDN 加速 | 静态资源走 jsDelivr (`@<commit-hash>`) 而非 GitHub Pages 直链，国内速度 ↑ |
| HTML 大小 | `index.html` ≈ 4200 行（含全部 CSS、JS、25 张卡片 markup） |

---

## 6 · 已知薄弱点 / 想听专家意见的点

1. **单文件 4200 行**——视觉/交互/数据/JS 全在一处。可读性、协作友好度、可维护性怎么改？拆 CSS/JS 是否值得？
2. **微信 X5 内核兼容**——MP4 自动播放、滚动、`history.pushState` 都有过坑；现在的兼容代码（`webkit-playsinline` 等）够不够 robust？
3. **detail 页是 SPA-like 注入**——SEO 弃疗（GitHub Pages 不预渲染）。若要兼顾 SEO，是否值得换 Astro/Next 静态生成？
4. **横滑 panel 内的列表与垂直 body 滚动共用一根 Y 轴**——目前各 panel 独立 scrollTop 是 JS 模拟（保存/恢复），不是真正的 CSS `overflow-y: auto` 独立滚动容器。小红书是后者；我们没做是因为底栏/header sticky 实现简单。哪种更值得？
5. **底栏 4 项**：3 tab + 1 sheet 行为混杂，「咨询报名」点了不切 tab——是否破坏一致性？
6. **筛选 vs 横滑切年龄**：年龄通过 panel，主题/地点/日期通过 sheet。家长心智上能 mapping 上去吗？
7. **视觉调性**：现在是橙色品牌色 + 米色背景 + emoji，倾向「亲切活力」。要不要更升一档「专业稳重」感（同行如 Nature Bridge、世纪明德）？
8. **首屏体验**——肉眼觉得 hero 太密（标题 + 4 行品牌文 + 气泡 + 渐变背景），FCP/LCP 没测过。
9. **「全部」panel 仍带 age-group divider 分隔**，但子 panel 没有——视觉规则不一致，但去掉觉得"全部"会糊在一起。

---

## 7 · 还未做的事 (设计可指点)

- 详情页阅读体验：进度条/TOC/续读/锚点已做，**字号选择器、深色模式、长文章懒加载分段**未做
- 18 张「毛坯」卡（`data-status="blank"`）没有内文，目前点不开
- 询问/报名链路在弹窗里靠扫码加客服，没有表单或预约日历
- A/B 测试体系无
- 埋点/分析无（连最基础 PV/UV 都没接 GA / 百度统计）

---

## 8 · 评估期望

希望从这位专家拿到：
1. **导航与信息架构**的整体诊断（IA 是否符合家长心智，4 panel 横滑这套是否过度设计）
2. **视觉/品牌调性**的方向建议（保持现在 vs 升级到更专业感）
3. **交互细节**的几个红字优先级（哪几处现在最劝退）
4. **可投入产出比最高的 3 件事**（不需要 10 件，只要 3 件最值得做的）
