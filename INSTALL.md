# 部署与维护说明

这套文件用于 **Shinonome-Ryoko14** 的 GitHub Profile 仓库。视觉主色为 `#3388BB`，主页图片与图标均保存在仓库本地；语言统计由 GitHub Actions 定时生成。

## 文件结构

```text
.
├── README.md
├── INSTALL.md
├── assets/
│   ├── images/
│   │   └── hero.jpg                 # 完整主页头图
│   ├── branding/
│   │   ├── wordmark.svg             # 顶部字标
│   │   └── section-mark.svg         # 章节标题装饰
│   ├── tech/                        # 技术栈图标（每个技术一个 SVG）
│   └── generated/
│       ├── metrics-light.svg        # 自动生成：浅色统计面板
│       ├── metrics-dark.svg         # 自动生成：深色统计面板
│       └── metrics.json             # 自动生成：最近一次统计数据
├── scripts/
│   └── update_metrics.py            # GitHub API 数据抓取与 SVG 生成
└── .github/
    └── workflows/
        └── update-metrics.yml       # 定时、手动及推送触发配置
```

## 部署步骤

1. 新建一个 **Public** 仓库，仓库名必须与 GitHub 用户名完全一致：`Shinonome-Ryoko14`。
2. 将本目录下的 `README.md`、`INSTALL.md`、`assets/`、`scripts/`、`.github/` 全部复制到个人主页仓库根目录，保留目录结构。
3. 提交并推送到默认分支（推荐 `main`）。
4. 打开仓库 `Settings → Actions → General → Workflow permissions`，选择 **Read and write permissions** 并保存。
5. 打开 `Actions → Refresh profile metrics → Run workflow`，手动运行一次。
6. 等待工作流完成。成功时会把最新统计结果提交到 `assets/generated/`；刷新个人主页即可看到更新。

工作流默认每天 `02:23 UTC` 运行，也会在 `main` / `master` 分支收到普通推送时运行（统计文件自身的变更不会触发重复运行）。定时任务由 GitHub 调度，实际启动可能有延迟。

## 语言统计的口径

脚本通过 GitHub REST API 的 `GET /repos/{owner}/{repo}/languages` 获取每个仓库的语言字节数，再累加仓库结果生成总览条。

默认统计范围：

- 只统计账号名下的公开仓库；
- 排除 Fork 仓库；
- 排除个人主页仓库本身；
- 按 GitHub 对每个仓库识别出的代码字节数汇总，而不是按提交次数、文件数量或投入时间计算。

因此，某个项目新写入代码并推送后，GitHub 更新该仓库的语言识别结果，下一次工作流运行就会反映到个人主页。语言占比不会因为一次提交就立刻变化。

### 私有仓库

当前工作流使用自动生成的 `GITHUB_TOKEN`。该令牌的权限范围受运行工作流的仓库限制，不能自动读取账号下其他私有仓库。若未来需要把私有仓库纳入统计，需要另行创建具有目标仓库 Metadata 读取权限的个人访问令牌，将其保存为仓库 Secret，并在脚本中改为读取该 Secret。不要把 Token 明文写进脚本或提交到仓库。

## 手动更新与排查

- **手动更新**：`Actions → Refresh profile metrics → Run workflow`。
- **确认是否成功**：打开该次运行，检查 `Regenerate the local metrics cards` 和 `Commit changes` 两步。
- **没有自动触发**：确认工作流文件已推送到默认分支、仓库启用了 Actions，且仓库没有因长期无活动而暂停定时任务。
- **统计没有变化**：检查新代码是否已经推送到 GitHub、文件是否被 GitHub 的语言统计识别，以及仓库是否符合上面的统计范围。
- **想加入 Fork**：修改 `scripts/update_metrics.py` 中 `own_repos` 的过滤条件；默认排除 Fork 是为了避免把别人的原始代码重复计入。

## 本地预览

```bash
python3 scripts/update_metrics.py --demo
```

此命令使用脚本内的示例数据生成预览，不会抓取真实账号数据。正式数据由 GitHub Actions 获取。

## 修改资源

- 更换头图：替换 `assets/images/hero.jpg`，并保持文件名不变。
- 更换字标或章节装饰：编辑 `assets/branding/` 中对应 SVG。
- 增删技术图标：将图标放入 `assets/tech/`，并在 `README.md` 中增删对应 `<img>`。
- 修改统计卡片颜色与样式：编辑 `scripts/update_metrics.py` 中的 `LIGHT`、`DARK` 和 SVG 绘制逻辑，再手动运行工作流。
- 不要手工编辑 `assets/generated/` 中的文件；它们会在下次运行时被重新生成。
