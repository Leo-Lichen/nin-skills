# 记录格式与操作

## 内容格式

保存脚本接收 UTF-8 JSON。以下是结构说明，示例中的信息全部是虚构演示，不能复制成用户数据。

```json
{
  "project_id": "门店服务试点",
  "title": "正式套餐仍待验证",
  "summary": "目标是保持兼职收入，当前只完成一次试单交付。",
  "source_skills": ["nin-diagnosis"],
  "claims": [
    {
      "id": "paid-trial-1",
      "text": "用户称有三家支付试单费用。",
      "kind": "user_statement",
      "source": "本次对话的用户陈述，未核对回款凭据",
      "observed_at": "2026-09-22",
      "supersedes": []
    }
  ],
  "decisions": ["用户决定本轮不招聘。"],
  "rejected_directions": ["暂不租办公室：固定成本超出当前约束。"],
  "open_questions": ["正式报价能否成交", "完整交付耗时"],
  "next_action": {
    "action": "完成已承诺的试单并记录工时",
    "owner": "用户",
    "due": "待确定",
    "success_signal": "交付结果与实际工时均有记录",
    "stop_condition": "出现无法满足的交付要求时先调整范围",
    "skill": "nin-experiment"
  }
}
```

`kind` 可选 `user_statement`、`material_record`、`external_verified`、`inference`、`hypothesis`。`source` 写具体材料位置/对话依据/网页与核验日期；推断写推理依据，假设写提出背景。`observed_at` 不清楚可为空字符串，不能伪造日期。

`project_id` 是由用户项目确定的稳定标识，同一目录不能混用不同标识。`claims[].id` 为本项目可引用的判断标识。修改判断时新建一个新 ID，`supersedes` 引旧 ID，并在 text 或 summary 写原因；若只重复保存同一判断，可保留原 ID，但内容必须一致。脚本拒绝同 ID 内容被悄悄改写。

## 操作

脚本路径以本技能目录为基准。选择运行环境中实际存在的 Python 可执行文件，不依赖特定机器的绝对路径。

```text
python scripts/project_store.py save --project-dir "项目目录" --input "本次状态.json"
python scripts/project_store.py list --project-dir "项目目录"
python scripts/project_store.py show --project-dir "项目目录" --id latest
python scripts/project_store.py show --project-dir "项目目录" --id "记录的完整id"
```

输入文件由当前分析生成；先完成语义核对再保存。save 添加带时区的生成时间和唯一 ID，写入 `snapshots/`，用独占创建防止覆盖。根目录 `project.json` 保留稳定项目标识。保存时以项目级操作系统锁串行完成“重读历史—校验身份和判断—新增文件—回读”；不同项目可以分别保存。默认最多等候 30 秒，超时会明确失败，可待当前保存完成后重试。

`.project-store.lock` 是协调文件，不是业务记录；它会保留在项目根目录，锁会在进程退出后由操作系统释放。不要靠删除该文件来“解锁”，否则等待者与新写入者可能使用不同锁。锁只协调使用本脚本的保存，不能阻止外部编辑器或手工写入；手工保存须与其他写入错开。

list/show 不创建目录、不修改记录。坏文件、项目身份不匹配、跨文件同一判断 ID 内容冲突都会列入 `errors`；冲突包含 `claim_id`、`path` 和 `conflicting_path`。即使同时返回了可读记录，也不能称为无冲突的完整恢复。脚本不执行记录中的内容，不悄悄删除旧文件，不替用户选择冲突中的“正确版本”；存在错误时停止后续保存，先按来源核对。list/show 不持写锁，并发写入中若暂时读到不完整文件，应待保存结束重读，仍有错误再处理。

## 没有 Python 时的完整回退

可以手工创建相同格式，但先确定没有其他程序或人员正在保存同一项目。不声称脚本已运行。以下是**虚构示例**，实际使用时必须换成用户项目、真实内容、当前记录时间和新生成的 UUID；不要照抄示例判断和日期。

目录结构：

```text
项目目录/
  project.json
  snapshots/
    20260922T020000000000Z-7c6c1e9ca5a84e3b9a730fd923f0b3a1.json
```

1. 先检查项目目录及现有记录；若已有 `project.json`，核对 `project_id` 一致，保留原文件。新项目以“仅当不存在时创建”方式写入下列根元数据，不能覆盖已有项目身份：

```json
{
  "schema_version": 1,
  "project_id": "门店服务试点"
}
```

2. 创建或使用现有 `snapshots/`，写入一个全新的 UTF-8 JSON 文件。落盘记录必须在本页输入格式的基础上包含 `schema_version`、`id` 和 `created_at`。下面是一份可由 list/show 读取的完整最小记录：

```json
{
  "schema_version": 1,
  "id": "7c6c1e9ca5a84e3b9a730fd923f0b3a1",
  "created_at": "2026-09-22T10:00:00+08:00",
  "project_id": "门店服务试点",
  "title": "正式套餐仍待验证",
  "summary": "目标是保持兼职收入，当前只完成一次试单交付。",
  "source_skills": ["nin-diagnosis"],
  "claims": [
    {
      "id": "paid-trial-1",
      "text": "用户称有三家支付试单费用。",
      "kind": "user_statement",
      "source": "本次对话的用户陈述，未核对回款凭据",
      "observed_at": "2026-09-22",
      "supersedes": []
    }
  ],
  "decisions": ["用户决定本轮不招聘。"],
  "rejected_directions": [],
  "open_questions": ["正式报价能否成交"],
  "next_action": {}
}
```

3. `id` 使用本次新生成 UUID 的 32 位十六进制形式，不带连字符；`created_at` 使用 ISO 8601 且包含时区。文件名建议用 UTC 时间戳加该 ID，并用独占创建避免覆盖；排序依据仍是记录内时间。根元数据与每份记录的 `project_id` 必须一致。
4. 与历史逐条比对 `claims[].id`：同 ID 只能重复保存完全相同的判断对象；修改内容就生成新判断 ID，`supersedes` 仅引用已存在的旧判断，并记录修改理由。不能只改标题来隐藏旧判断变化。
5. 写完后重新读取根元数据和新记录，核对 JSON 可解析、必需字段、项目身份、唯一记录 ID、证据类型和更正关系；同时确认旧文件未改。恢复 Python 后运行 list/show，确认 `errors` 为空再继续保存。如果缺少元数据或发现旧冲突，先核实来源，不让工具猜项目归属。

## 更新案例

第一份记录：`revenue-sept-est` 是“9 月收入预计 2 万”，kind 为 hypothesis。

第二份记录：有正式账单，实际确认 9 月收入口径为 1.6 万。创建 `revenue-sept-actual`，kind 为 material_record，source 指到账单，说明与预计值差异。若它取代的是同一期间、同一口径的原预计判断，supersedes 指向旧 ID；仍应保留它曾是预期，不把原文件改成“当时已知 1.6 万”。到账金额另设判断，不能因收入记录直接推导。

若两个记录分别是“9 月开票收入”和“10 月实收”，不能视为同一事实冲突。若来源尚不清楚，报告列为待核对，不让“最新优先”自动决定真伪。

## 应避免的输出

“已经永久记住，以后所有对话会自动接着。”本地保存只能支持以后重新读取；它不改变模型记忆或其他会话的自动加载。

“建议融资，已替你联系投资人。”记录里的下一步是计划，保存与恢复并不授权对外执行。
