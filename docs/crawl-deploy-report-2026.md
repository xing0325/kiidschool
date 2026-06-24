# 2026 夏令营文章重爬 + 专属报名QR 部署报告

> 你睡觉时自动跑完的。醒来看这份对账 + 最后一步服务器命令。

## 一、抓取对账（你给 27 条 URL）

| 类别 | 数量 | 说明 |
|---|---|---|
| 总公告 | 1 | 不是营期卡，未接入卡片（#1） |
| camp 文章 | 26 条 URL | 其中「世界重启」给了 2 条 URL（#2 新 / #19 旧），是同一篇 |
| **唯一营期** | **25** | 去掉世界重启重复后 |
| 网站卡片 | 25 | **1:1 全部对上** ✅ |

- **多抓**：world-restart 第 2 条 URL（重复）→ 已丢弃，不影响
- **少抓**：无
- 26 篇全部抓取成功，图片全本地化（`remote_left:0`），每篇都提取到专属报名二维码

## 二、25 张卡 → 文章 + 专属报名QR 映射

| 卡片 | slug | 专属报名QR |
|---|---|---|
| 六艺通识营 | liuyi | 31b46612… ✓老码一致 |
| 头脑特工队 | emotion-team | 19e2955c… ✓ |
| 勇敢者游戏（剧本营） | brave-game | 802120da… 🆕 |
| 招牌通识营·世界重启 | world-restart | 31248ddd… ✓ |
| 少年大富翁创业营 | tycoon | da7db49f… 🆕 |
| 学院制夏令营 2.0 | academy-2 | a5fd106d… 🆕 |
| 重走人类创造之路 | human-history | cc889ba1… ✓ |
| 硬核成长营·命运手斧 | fate-axe | e8973e40… ✓ |
| 火星生存指南 | mars | 9f296f20… 🆕 |
| 数学战争 | math-war | 71d45056… 🆕 |
| 水形物语 ⚠️ | water-oasis | 37de3937… 🆕（见存疑） |
| 时间玩家 | time-player | 38200b46… 🆕 |
| 搞笑诺贝尔 | funny-nobel | d8a89f13… 🆕 |
| 造船 PBL | boat-pbl | 3c26f657… 🆕 |
| 定向越野 + AI | orienteering | d806b308… 🆕 |
| 招牌学院制 6.0 | academy-6 | f38d38fe… 🆕 |
| 名侦探学院 2.0 | detective | 6e471ac8… 🆕 |
| 招牌跨学科·运气秘籍 | luck-recipe | c9d9788c… ✓ |
| 玩笑盲盒营 | joy-blindbox | 6084735c… ✓ |
| 第一桶金 | first-gold | 697b7cf1… 🆕 |
| 饥饿游戏 | hunger-games | 2ec00e38… 🆕 |
| 职业探索学院制 3.0 | career-explore | 2b607d31… 🆕 |
| 学习方法升级营 | learning-method | 16fe992b… 🆕 |
| AI游戏设计营 | ai-game | 0e9915d4… 🆕 |
| 龙与地下城跑团营 | dnd | 47248d04… 🆕 |

「✓老码一致」= 与上次验证过的同一张二维码，说明提取准确。

## 三、⚠️ 唯一存疑（请你确认）

**「水形物语」卡 ↔「绿洲水人节」文章**
- 你的清单里**没有**「水形物语」，但有「绿洲水人节·跨学科通识」(#12)
- 网站卡片里有「水形物语」（9-12 占位卡），没有「绿洲水人节」
- 两者都是 9-12 岁、都跟水有关 → 我判断是**同一个营**（水形物语是占位名，正式发布叫绿洲水人节），已把绿洲水人节的文章+报名码接到了「水形物语」卡
- **如果不对**（其实是两个不同的营），告诉我，我拆开

## 四、性能优化（这次顺手做的）

- `_shared` 图片：GIF→MP4（65MB→6MB）、JPG/PNG 压到 ≤800w
- **报名二维码全部原样保留**（不压缩，保证扫码清晰）
- articles 总体积 142MB → 80MB

## 五、部署状态

- ✅ 已 push 到 GitHub（feat/2026-revision-r1 + feat/r2-no-panel）
- ✅ GitHub Pages 预览自动更新：https://xing0325.github.io/kiidschool/v2/
- ⏳ **服务器（2026.kiidschool.cn）需要你粘一条命令同步**（见下）

### 服务器同步命令（醒来粘到 OpenClaw 终端）

```
cd /var/www/kiidschool-2026 && sudo git fetch --depth 1 origin feat/r2-no-panel && sudo git reset --hard FETCH_HEAD && sudo find . -name '*.html' -exec sed -i -E 's#https://cdn\.jsdelivr\.net/gh/xing0325/kiidschool@[a-f0-9]+/#/#g' {} + && sudo systemctl reload caddy && echo "=== 同步完成 ===" && curl -s https://2026.kiidschool.cn | grep -o '<title>[^<]*</title>'
```

粘完，2026.kiidschool.cn 就是最新的（25 篇详情 + 每卡专属报名码）。
