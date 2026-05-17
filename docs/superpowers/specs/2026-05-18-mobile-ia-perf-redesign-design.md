# 钥匙玩校 · 移动端 IA 重构 + 性能优化 设计文档

- 日期：2026-05-18
- 分支：feat/2026-revision-r1（GitHub Pages 直接服务该分支根目录，推送 = 上线）
- 相关 Issue：#1「2026夏令营网站改版 R1（同事反馈）」
- 上一轮 PR/汇报：无（此前 32 个 commit 均直推线上，未走 PR）

---

## 1. 背景

R1 改版已落地（头图/筛选/特色/QA），25+ 卡片骨架在位、10 张完整、6 张待补、18 张毛坯。当前问题：

- 移动端首屏加载/动图体验慢。
- 年龄分段切换是「点击 tab + 同一份卡片过滤」，体感不像内容浏览类 App。
- 底栏 4 项（筛选/了解我们/常见问答/咨询报名）混杂两种交互（弹窗 vs 页面），层级语义不清。
- 弹窗只支持点击空白处关闭，不支持手势下滑。

## 2. 目标

1. 把首页年龄 tab 切换从「点击 + 过滤」升级为「真横滑 panel」（类小红书发现/关注/同城）。
2. 重新切分底栏 IA：把「了解我们」「常见问答」从底部弹起改为与首页瀑布流并列的一级页面；筛选按钮挪出底栏，咨询报名保持 bottom sheet。
3. 弹窗支持下滑收起（drag-to-dismiss），不影响点空白处关闭。
4. 显著降低首屏图片/动图加载与解码压力，**不破坏现有视觉**。

## 3. 信息架构

### 3.1 底栏（4 项，行为分两类）

| 位置 | 名称 | 行为 | 类型 |
|---|---|---|---|
| 1 | 首页 | 切到首页（瀑布流 + 顶部年龄横滑 + 顶部右侧筛选按钮） | tab |
| 2 | 了解我们 | 切到「了解我们」一级页面 | tab |
| 3 | 常见问答 | 切到「常见问答」一级页面 | tab |
| 4 | 咨询报名 | 弹起 bottom sheet（两个客服二维码），不切 tab | sheet trigger |

- 切 tab 时整页替换；当前 tab 在底栏图标上高亮。
- 「筛选」从底栏移除，挪到**首页页面顶部右侧**（与年龄横滑同一区域，作为漏斗 icon）。

### 3.2 首页内部（横滑 4 panel）

```
[顶部条：logo · 「筛选」漏斗]
[年龄横滑 tab：全部 | 9-12 | 12-16 | 14-18 ]
[ panel 横向滑轨：
   ┌─────────┬─────────┬─────────┬─────────┐
   │ 全部    │ 9-12    │ 12-16   │ 14-18   │
   │ (34张)  │ (子集)  │ (子集)  │ (子集)  │
   └─────────┴─────────┴─────────┴─────────┘
]
[ 底栏：首页 | 了解我们 | 常见问答 | 咨询报名 ]
```

- 4 panel 横向排列，translateX 切换。
- 每个 panel 是独立 scroll 容器，**各自记忆 scrollTop**（小红书同款）。
- 顶部年龄 tab 与 panel 双向绑定：点 tab → 滑到对应 panel；横滑结束 → 高亮对应 tab。
- 横滑过程中（手指未松开），tab 高亮**不**跟随手指做百分比插值，仅在释放/结束后切到目标 tab。简化交互、避免抖动。
- 横滑临界：手指水平位移 > 30% panel 宽度，或释放时水平速度 > 阈值（0.5 px/ms），则切换；否则回弹。

### 3.3 一级页面间的状态

- 首页、了解我们、常见问答 三个一级页面均**各自记忆 scrollTop**；切 tab 不重置滚动位置。
- 详情页（master-detail 那套）属于首页的子页面，打开方式不变，返回时回到首页瀑布流。

## 4. 实现路线（方案 C：克隆现有卡片到各 panel）

### 4.1 卡片分发

- 现有 34 张卡片 markup 保留**不动**（包括价格、状态标记、slug、`data-*` 属性）。
- 在 DOMContentLoaded 后用 JS 完成一次性「分发」：
  1. 创建 4 个 panel 容器：`#panel-all`、`#panel-9-12`、`#panel-12-16`、`#panel-14-18`。
  2. 遍历 34 张卡片：每张依据 `data-age-min`/`data-age-max` 决定要进哪几个 panel。
  3. 用 `cloneNode(true)` 克隆到各目标 panel；「全部」panel 直接接管原节点（不克隆，省一份）。
- DOM 体积估算：34 + ≈45（年龄段克隆）= ~79 个卡片节点。每卡很轻（一图 + 几行文字 + 小按钮），可接受。

### 4.2 卡片内动图（MP4）按视口 + 按 panel 双重门控

- 所有卡片内 `<video>` 初始化时**移除 `src` 属性、设 `preload="none"`**，加 `data-src="..."`。
- 建一个 IntersectionObserver：
  - 当 video 进入视口 **且** 所在 panel 是「当前 panel」→ 设 `src=data-src`，`play()`。
  - 当 video 离开视口 **或** 所在 panel 不是当前 panel → `pause()`，可选 `removeAttribute('src'); load()` 释放解码资源（首版先只 pause，省释放成本）。
- 顶部「hero」区的 video 单独处理：首屏必播，但只播一个（其它 hero video 推迟到滑到视野再播）。

### 4.3 静态图压缩与轻量化

| 资源 | 当前 | 目标 |
|---|---|---|
| `images/camps/world.jpg` | 4.2 MB | 重新编码 ≤ 400 KB（保持 1080w，q=80） |
| `images/playmates/*.png`（2-3 MB 多张） | PNG | 转 JPG q=82，目标每张 ≤ 250 KB |
| `images/features/seven-arts.png` 等 | 600+ KB PNG | 转 JPG 或 WebP |
| 首屏以下 `<img>` | 已有 41 个 `loading="lazy"` | 检查首屏以下 `<img>` 全部带 lazy + `decoding="async"` |
| 卡片 `<img>` | 未声明 `width/height` | 加 `width/height` 或 `aspect-ratio` 防抖动 |

> 不在本次：HEIC/AVIF 多源；CDN；图床改造。

### 4.4 底栏一级页面

- 「了解我们」「常见问答」当前是底部弹起的全屏视图；改造为：
  - 与首页同级的 `<section>`，默认 `display:none`，切到时显示。
  - 点底栏 tab → 切显示，并 push 一条 history state（手机物理返回键可回首页）。
  - 内容素材直接复用现有的全屏视图 DOM；只把"如何打开"从 sheet 改成 tab 切换。

### 4.5 Bottom Sheet（筛选 + 咨询报名）

- 共用一个底部弹窗组件（已有筛选 sheet 可改造）。
- **drag-to-dismiss**：
  - sheet 顶部加一条 handle（视觉提示可下滑）。
  - 监听 sheet 容器的 `touchstart/touchmove/touchend`。
  - 仅当 sheet 内部 `scrollTop === 0` 时，下滑手势才被识别为"关 sheet"（否则交给内部滚动）。
  - 阈值：下滑位移 > 100 px 或下滑速度 > 0.5 px/ms → 关。否则回弹。
- 保留点空白处关闭 + 点关闭按钮关闭。

## 5. 不在本次范围（YAGNI）

- 把 34 张卡片重构为 JS 数据驱动（方案 B 的内容，本次不做）。
- AVIF/WebP 多源 picture。
- 改 GitHub Pages 部署方式 / 切换到走 PR 合并流。
- 详情页（master-detail）的进一步改造。
- 6 张 todo / 18 张 blank 卡片的内容补全（属于 Issue #1 余项，单独迭代）。

## 6. 验收标准

1. **横滑**：手指在首页 panel 区水平横滑 ≥ 30% 宽度，松手后切到下一年龄段；顶部 tab 同步高亮。
2. **滚动记忆**：在「全部」滑到中部，切到「9-12」再切回「全部」，仍在原位置。
3. **底栏 IA**：点底栏「了解我们」整页切换到该 tab（不是 sheet）；点「咨询报名」弹起 sheet。
4. **筛选位置**：底栏没有「筛选」；首页顶部右侧有漏斗图标，点了弹筛选 sheet。
5. **Drag-to-dismiss**：任一 sheet 在内部 scrollTop=0 时，按住下滑 ≥ 100 px 关闭。
6. **MP4 节流**：用 Chrome DevTools Performance 抓首屏，同屏只有"可见且当前 panel"的 video 处于 playing 状态，其它 paused 且未占用 GPU 解码。
7. **图片体积**：`images/camps/world.jpg` 与 玩伴头像 PNG 全部压缩；首屏总传输字节相较优化前下降 ≥ 50%（用 DevTools Network 对比）。
8. **甲方汇报 HTML**：完工后生成一份 `public/pr-report.html`（或同级路径）的 HTML 汇报页，列出本轮做了什么、改了哪些文件、可点的对比截图。

## 7. 风险与回滚

- **克隆 DOM 与现有详情打开逻辑冲突**：详情打开是基于卡片点击 + 状态保存 origin parent。克隆后会出现"同 slug 多卡片"，需在 openDetail 内基于 panel 锁定唯一卡片。回滚策略：保留方案 A 的过渡作为 fallback flag。
- **MP4 卸 src 后重新挂回首帧黑屏**：iOS Safari 已知问题。缓解：保留 `poster` 属性（从 MP4 抽首帧生成的 jpg）。
- **横滑与垂直滚动手势冲突**：必须在 `touchstart` 起测主方向（首 10 px 内判定），一旦判为垂直就完全放弃水平识别。
- **History/back 兼容微信内嵌**：微信内置 X5 内核对 history API 有特殊处理。需要在真机验证。
- **回滚**：所有改动集中在 index.html + 新增 css/js 块；如有问题，`git revert` 单 commit 即可回退到当前 097bb2d。

## 8. 交付物

- 修改后的 `index.html`。
- 一份甲方汇报 HTML：`public/pr-report-2026-05-18-r2.html`（模仿 PR #83 的 `public/pr-report.html` 模板：左侧导航 + 右侧分块陈述「做了什么 / 对比截图 / 文件改动 / 验收清单」）。
- 本设计文档（已提交 git）。
- 实施计划文档（由 superpowers:writing-plans 下一步产出）。
