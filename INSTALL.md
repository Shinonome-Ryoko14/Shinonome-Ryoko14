# 部署与维护说明

这套文件是为 **Shinonome-Ryoko14** 的 GitHub Profile 仓库准备的。视觉主色仍是 `#3388BB`，并加入了来自新头图的樱花粉、薄荷绿和淡紫。所有图片与统计卡都在本地生成，不依赖第三方统计卡片。

## 文件结构

```text
.
├── README.md
├── INSTALL.md
├── assets/
│   ├── branding/
│   │   ├── wordmark.svg        # 顶部 Ryoko 字标（亮色，渐变光晕 + 高光扫过）
│   │   ├── wordmark-dark.svg   # 顶部 Ryoko 字标（暗色）
│   │   ├── hero-light.svg      # 亮色头图（内嵌 hero-light.jpg）
│   │   ├── hero-dark.svg       # 暗色头图（内嵌 hero-dark.jpg）
│   │   ├── section-mark.svg    # 章节标记（呼吸光条）
│   │   ├── toolchain.svg       # 15 个技术栈徽章合并面板
│   │   └── footer-wave.svg     # 页脚音波（绘制动画）
│   ├── images/
│   │   ├── hero-light.jpg      # 亮色头图源文件（1400×788）
│   │   ├── hero-dark.jpg       # 暗色头图源文件（1400×788）
│   │   ├── chibi-avatar.jpg    # 统计卡用方形头像源文件
│   │   └── chibi-sticker.svg   # About 旁圆形贴纸（内嵌 chibi-avatar.jpg）
│   ├── generated/
│   │   ├── metrics-light.svg   # 亮色动画统计卡，由 Action 自动更新
│   │   ├── metrics-dark.svg    # 暗色动画统计卡，由 Action 自动更新
│   │   └── metrics.json        # 最近一次抓取的数据，便于排查
│   └── tech/                   # 15 个技术栈徽章源文件（会被 toolchain.svg 内联）
├── scripts/
│   ├── build_profile_assets.py # 重新生成头图/字标/技术栈/贴纸/页脚 SVG
│   └── update_metrics.py       # 只用 Python 标准库，生成动画统计卡
└── .github/
    └── workflows/
        └── update-metrics.yml
```

## 部署步骤

1. 新建一个 **public** 仓库，仓库名必须与 GitHub 用户名完全一致：`Shinonome-Ryoko14`。
2. 把本目录下的 `README.md`、`INSTALL.md`、`assets/`、`scripts/`、`.github/` 全部复制到仓库根目录。
3. 提交并推送到默认分支（通常是 `main`）。
4. 打开仓库的 **Settings → Actions → General → Workflow permissions**，选择 **Read and write permissions**，保存。
5. 打开 **Actions → Refresh profile metrics → Run workflow**，手动运行一次。
6. 等待约半分钟，Action 会提交新的 `assets/generated/metrics-*.svg` 和 `metrics.json`。回到个人主页刷新即可看到最新数据。

之后 Action 每天 UTC 02:23 自动运行；你也可以随时手动触发。

## 动效是怎么实现的

- 所有动画都是 SVG 内部的纯 CSS，不需要 JavaScript，也不依赖外部脚本。
- 光晕没有使用昂贵的模糊滤镜，而是用径向渐变 + 多层半透明描边模拟，滚动时不掉帧。
- 统计卡包含数字滚动、52 周贡献热力图、连续天数环形进度、语言条展开、星光闪烁和 Q 版头像轻浮动。
- 所有关键内容的默认状态就是最终状态；即使客户端不支持 CSS 动画，也会直接显示完整数字和图形，不会出现“停在 0”或透明消失。
- 支持 `prefers-reduced-motion: reduce`，系统开启减少动效时所有动画自动关闭，直接显示静态完整画面。
- GitHub 不支持在 README 里运行 JavaScript，动画只在页面加载时播放；GitHub App 内可能只显示静态首帧，因此静态首帧也是完整画面。

## 统计卡的数据来源

- 仓库、语言、关注者：GitHub REST API。
- 贡献总数、52 周每日贡献：GitHub 公开的 contributions 页面；不需要 token 也能解析。
- Action 使用仓库自带的 `GITHUB_TOKEN`，只统计公开数据。
- 抓取失败时会保留上一次成功的卡片；语言或日历缺失时会回填 `metrics.json` 里的旧数据，避免裂图。
- 连续天数优先显示当前 streak；如果当前为 0，则显示历史最佳 streak，并改标签为 `BEST STREAK`。

## 本地预览

生成统计卡（不会覆盖仓库里的正式文件）：

```bash
python3 scripts/update_metrics.py --demo --out /tmp/ryoko-preview
```

重新生成头图、字标、技术栈面板、贴纸和页脚（会覆盖 `assets/` 下的 SVG）：

```bash
python3 scripts/build_profile_assets.py
```

两个脚本都只用 Python 标准库。直接双击 `assets/branding/hero-light.svg` 或 `assets/generated/metrics-light.svg`，用浏览器打开即可看到动画。

## 自定义

- **换头图**：用同尺寸（建议 1400×788）的 JPG 替换 `assets/images/hero-light.jpg` 和 `hero-dark.jpg`，然后运行 `python3 scripts/build_profile_assets.py`。
- **换 About 贴纸 / 统计卡头像**：替换 `assets/images/chibi-avatar.jpg`（建议正方形），再运行一次构建脚本。
- **换角色**：当前使用千早爱音风格的粉发吉他 Q 版形象。若要换成 millsage 的滨崎茉幌，需要先准备同画风的短发角色图，再按上面的方式替换。
- **换主色**：统计卡的配色在 `scripts/update_metrics.py` 的 `LIGHT` / `DARK` 字典里；头图光晕和边框颜色在 `scripts/build_profile_assets.py` 的 `build_hero()` 里。
- **去掉访客计数器**：删除 `README.md` 中 `<p align="center">` 包住 `count.getloli.com` 的那一段即可，其余内容不受影响。
- **不想显示统计卡**：删除 README 中的 “GitHub” 一节，以及 `.github/workflows/update-metrics.yml`。

## 注意事项

- `metrics-*.svg` 中的数字来自公开 API，私有仓库不会计入。
- 语言统计默认排除 fork 仓库；如果需要包含 fork，修改 `scripts/update_metrics.py` 里的 `own_repos` 过滤逻辑。
- 技术栈徽章源文件在 `assets/tech/` 下；增删技术时，同时修改 `scripts/build_profile_assets.py` 里的 `TECH_ORDER`，再重新生成 `toolchain.svg`。
- 头图和头像已经压缩到适合 README 的体积；替换时请避免直接提交 10MB 以上的原图。
- GitHub 的定时任务在仓库长期无活动时可能被暂停；重新手动运行一次即可恢复。
- 访客计数器是唯一的外部图片（`count.getloli.com`），如果服务不可用，删掉那一行即可。
