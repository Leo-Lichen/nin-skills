# Ninther Skills

**从创业想法到可验证的生意，把诊断、商业计划与行动连起来。**

简体中文 · [English](README.en.md) · [新手入门](docs/getting-started.md) · [方法来源](docs/methodology.md) · [验证记录](docs/validation.md) · [许可](LICENSE)

Ninther Skills 是一套面向创业与经营任务的 AI Agent 技能，简称 **Nin-skills** 或 **nin**。基于韩树杰《创业地图：商业计划书与创业行动指南》，将项目诊断、市场与产品、成本现金、商业计划、现实验证和项目记录组织成 **18 项技能**。

当前版本：**v1.0.2**。不知道选哪一项时，从 `$nin` 开始，把你已有的事实和想解决的问题交给它。

## 适合怎样的业务

本地服务、课程与咨询、自由职业、小团队产品、企业服务，以及正在验证中的创业想法，都可以从当前问题切入。你可以只想稳定经营，也可以准备合作或融资；分析会围绕你选择的目标展开。

技能运行在支持本地 Skills 的 Agent 中。它提供判断、稿件、测算和行动设计；客户是否购买、交付是否有效，需要真实结果回到分析里。

## 从这些问题开始

| 经营场景 | 可以交付什么 |
| --- | --- |
| 朋友都说需要陪伴服务，我准备花钱开发小程序 | 项目体检、最关键的证据缺口、一轮可执行的人工服务验证 |
| 企业试用排班工具说很好，却一直不采购，我该加功能吗 | 使用者与决策者的需求区分、替代方案比较、采购障碍与下一步核对 |
| 服务还没有付费客户，后天要给潜在合伙人看BP | 可修改的商业计划书正文，明确事实、假设、产能与收入情景 |
| 课程卖出去了，广告、退款和自己的工时一算，究竟赚多少 | 同口径的收入成本表、单位经济测算与现金条件判断 |
| 我想向门店合作方讲90秒，争取客户触达渠道 | 可直接试讲的口播、时间预算、三至五个关键追问与答法 |
| 三个月收支相抵，但开支在月初、客户在月底付款 | 按付款节点排列的现金表、最早缺口、金额与可落实的调整方案 |

这些是任务场景示例，不是对经营结果的保证。资料不全时，先完成有依据的部分，并把未知项留出来。

## 快速开始

安装后，在 **Codex 对话框**中输入，而不是在终端输入：

```text
$nin 我做本地宠物照看，已经有12名付费客户，客户都来自熟人介绍。
我每月最多投入40小时。下一步想尝试门店转介绍，请帮我判断先验证什么。
```

在支持斜杠命令的宿主中，可使用 `/nin`。技能加载后，也可以用自然语言说“用 Nin 帮我分析”“请用 nin”或“用 Nin-skills 看一下这个项目”。不同宿主的选择与加载方式可能不同，详见[入门指引](docs/getting-started.md)。

已经知道需要什么，可以直接点名专项：

```text
$nin-bp 用现有资料写一份给合伙人看的商业计划书，未知数据标明，不虚构成果。
$nin-model 帮我拆清这批订单的收入、退款、交付成本和我自己的工时。
$nin-project 把这次结论和待验证项保存到我指定的项目目录，保留证据来源。
```

## 下载与安装

### 第一次使用 GitHub：下载 ZIP

1. 打开 [Ninther Skills 仓库](https://github.com/Leo-Lichen/nin-skills)。
2. 点击文件列表上方的 **Code**，再点击 **Download ZIP**。
3. 解压下载的文件，进入能看到 `skills`、`scripts` 和 `manifest.json` 的那一层目录。
4. 在这个目录打开终端，运行下面的安装命令。

不需要注册 GitHub 账号或学习 Git，就可以下载公开仓库的 ZIP。

### 使用 Python 安装器

需要本机可运行 **Python 3.10 或更高版本**。安装器使用 Python 标准库，无需额外安装 Python 包。

先预览安装目标，再安装到 Codex：

```bash
python scripts/install.py --target codex --dry-run
python scripts/install.py --target codex
```

也可以选择其他目标目录：

```bash
python scripts/install.py --target claude
python scripts/install.py --target agents
```

`codex`、`claude`、`agents` 分别对应 Codex、Claude Code 和通用 Agents 技能目录。可在任一命令后加 `--dry-run` 先看计划。安装器遇到同名技能目录会停止，不覆盖已有文件。安装后，重新打开或刷新宿主会话，确认技能已经加载。

### 不使用脚本：手动复制

把本仓库 `skills/` 下面的 **18 个完整技能目录**复制到对应位置，保留其中的 `SKILL.md`、`references` 和脚本等文件：

| 使用环境 | 常见用户级技能目录 |
| --- | --- |
| Codex | `~/.codex/skills/` |
| Claude Code | `~/.claude/skills/` |
| 通用 Agents | `~/.agents/skills/` |

`~` 代表你的用户主目录。Codex 设置了 `CODEX_HOME` 时，安装器使用该目录下的 `skills/`；其他自定义位置以宿主实际配置为准。不要只复制 `SKILL.md`，也不要把整个仓库多套一层当成单个技能。完整步骤见[新手入门](docs/getting-started.md)。

## 18 项技能

下表使用技能名；Codex 中可加 `$` 显式调用，支持斜杠命令的宿主可加 `/`。

| 技能 | 适用任务 | 主要交付 |
| --- | --- | --- |
| [nin](skills/nin/SKILL.md) | 不确定从哪里开始 | 根据当前任务选择专项，沿用已有资料 |
| [nin-diagnosis](skills/nin-diagnosis/SKILL.md) | 项目体检、判断卡点 | 问题、方案、团队与业务模块的证据检查 |
| [nin-positioning](skills/nin-positioning/SKILL.md) | 说不清做什么、为谁做 | 一句话定位、项目简介与价值边界 |
| [nin-market](skills/nin-market/SKILL.md) | 判断需求、客户和市场机会 | 客群、替代办法、竞争与市场口径 |
| [nin-product](skills/nin-product/SKILL.md) | 取舍功能、明确服务范围 | 需求与能力对应、交付方案和效果验证 |
| [nin-model](skills/nin-model/SKILL.md) | 定价、获客、交付与赚钱方式 | 交易结构、收入成本、单位经济和现金区分 |
| [nin-team](skills/nin-team/SKILL.md) | 合作分工、团队和资源安排 | 能力缺口、责任分工与合作待决事项 |
| [nin-progress](skills/nin-progress/SKILL.md) | 核对已有成果 | 证据表、成绩表述与下一项补证动作 |
| [nin-strategy](skills/nin-strategy/SKILL.md) | 把目标变成行动 | 里程碑、容量、预算、依赖与调整条件 |
| [nin-risk](skills/nin-risk/SKILL.md) | 判断哪些条件失效会出问题 | 失败条件、预警信号、负责人和应对方案 |
| [nin-funding](skills/nin-funding/SKILL.md) | 是否筹资、筹多少、用在哪里 | 资金需求、来源比较、用途与支持周期 |
| [nin-bp](skills/nin-bp/SKILL.md) | 写作或修改商业计划书 | 有正文的BP草稿、关键论证与待补证据 |
| [nin-pitch](skills/nin-pitch/SKILL.md) | 路演、合作介绍、模拟答辩 | 实际口播、计时预算与答辩卡 |
| [nin-investor](skills/nin-investor/SKILL.md) | 从投资人角度审视项目 | 支持与反面证据、尽调问题与准备重点 |
| [nin-experiment](skills/nin-experiment/SKILL.md) | 用小实验验证商业假设 | 对象、报价、投入上限、观察与复盘判据 |
| [nin-survival](skills/nin-survival/SKILL.md) | 现金紧张、收缩与维持经营 | 现金时间线、缺口和继续或调整条件 |
| [nin-founder](skills/nin-founder/SKILL.md) | 创业与工作、家庭等取舍 | 路线比较、个人资源边界与重新判断条件 |
| [nin-project](skills/nin-project/SKILL.md) | 保存、恢复、回填与汇总 | 可追溯的项目记录和报告 |

## 方法来源与证据原则

方法参考韩树杰《创业地图：商业计划书与创业行动指南》（2020），包括问题、方案、团队三项价值，以及商业计划书的九模块、三十六要点等框架。各技能保留对应来源说明。任务路由、证据标签、实验卡和本地记录流程是面向 Agent 使用的应用设计。

使用时遵循几个基本区分：

- 口头兴趣、意向书、押金、正常付费和完成交付分别记录。
- 用户陈述、原始材料、外部核验、推断与待验证假设不混写。
- 收入、利润、到账现金与尚需履约的责任分别计算。
- 计划受可用时间、人员、现金和已承诺交付约束。
- 新结果可以改变判断，旧结论和修改依据保留。

原书中的历史案例不能直接证明今天的市场。需要当前外部事实时，应另行核验；没有资料的数字会作为未知或明确的情景假设处理。

## 实际验证范围

本地核对覆盖18项技能的目录结构与引用。行为试跑包括7个原始场景，其中3组进行了同题对照，另有3个新场景复核，关注实际交付、数字口径、证据边界和资源约束。

这是有限的本地样本，不代表在所有模型、操作系统和软件中都完成了真实测试，也不构成对其他技能工具箱的普遍优劣结论。安装目标目录与宿主实际加载效果应分别确认；口播时长等依赖现场表现的结果，仍需要真实试讲或业务反馈。

## 项目结构与许可

```text
nin-skills/
├── skills/             # 18项技能及各自参考材料
├── scripts/            # 安装等本地工具
├── docs/               # 使用文档
├── manifest.json       # 名称、版本与技能清单
└── VERSION
```

本项目采用 **CC BY-NC 4.0**，公开发布并提供下载。在注明来源、提供许可证链接并标明修改的前提下，允许非商业使用、分享与改编；商业用途需另行获得授权。

完整条款见 [LICENSE](LICENSE)。许可咨询可通过 [GitHub 账号页面](https://github.com/Leo-Lichen)或[仓库 Issue](https://github.com/Leo-Lichen/nin-skills/issues)联系。原书及其他第三方材料的权利不因本仓库许可而改变。
