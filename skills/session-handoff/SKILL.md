---
name: session-handoff
description: Use this skill for long-running "vibe coding" projects in Claude Code when the conversation context is getting long and it's time to start a fresh session without losing project state. Triggers include the user saying things like "context太长了", "开个新session", "帮我写个交接文档", "总结一下现在做到哪了", "compact之前先存一下状态", or any request to hand off, summarize, checkpoint, or persist the current state of a coding session before continuing elsewhere. Also use this skill proactively near the start of a session when the user references "上次做到哪了" or asks Claude to resume a project that has a project-docs folder — read the handoff docs first instead of re-scanning the whole codebase. Maintains a persistent project-docs folder (README.md, ARCHITECTURE.md, AGENT_HANDOFF.md, TODO.md, DECISIONS.md) so each new session only needs to read a short handoff note instead of the entire history.
---

# Session Handoff

一个用于解决 **vibe coding context 过长** 问题的 skill。核心思路：不要试图把整个对话历史塞进新 session，而是维护一个**长期项目文档文件夹**，每次开新 session 前，只需要生成/更新一份**轻量交接文档**，新 session 读取这个文件夹就能快速接上工作，而不用重新理解整个项目。

## 核心概念：稳定文档 vs 临时交接文档

项目文档文件夹里有两类文件，更新策略完全不同：

**稳定文档**（缓慢变化，跨越很多个 session，应该被"更新"而不是重写）
- `README.md` — 项目是什么、怎么跑起来、目录结构、长期使用说明
- `ARCHITECTURE.md` — 稳定的架构决策：技术栈、模块划分、数据流、关键设计模式
- `TODO.md` — 跨 session 的任务列表（不是本次 session 的任务，是项目整体待办）
- `DECISIONS.md` — 重要决策日志（类似 ADR），只增不减，记录"为什么这么做"而不是"现在状态如何"

**临时交接文档**（每次 session 结束都是全新的一份，不修改旧的）
- `AGENT_HANDOFF.md` — 只描述"相对于上面 4 份稳定文档，最近这个 session 发生了什么、现在卡在哪、下一步该干什么"。旧版本不修改，而是被归档，然后写一份全新的。

这样设计的原因：`AGENT_HANDOFF.md` 不需要重复解释整个项目背景（那是 README/ARCHITECTURE 的职责），只需要写"增量"，所以可以做得很短，新 session 读起来快。

## 目录结构

默认位置：项目根目录下的 `agent-docs/`；如果项目根目录已经有 `.claude/` 目录，则用 `.claude/agent-docs/`。

这个规则是**确定性的**，不需要询问用户、也不需要跨 session"记住"这个选择——因为新 session 本来就没有对话记忆，任何只存在于对话里的选择到了下一个 session 都会失效。做法是：每次都按固定顺序检查这两个候选路径，谁存在就用谁；如果两个都不存在，才走场景 A 的初始化流程（初始化到哪个路径同样按上面的规则确定，不用问）。

```
agent-docs/
├── README.md
├── ARCHITECTURE.md
├── AGENT_HANDOFF.md          # 当前 session 的交接文档（永远只有一份"当前"）
├── TODO.md
├── DECISIONS.md
└── handoff_archive/          # 归档的历史 AGENT_HANDOFF.md
    ├── AGENT_HANDOFF_2026-07-15_1830.md
    └── AGENT_HANDOFF_2026-07-16_0930.md
```

## 工作流程

### 场景 A：项目第一次使用这个 skill（文件夹不存在）

1. 按上面的确定性规则检查两个候选路径（`agent-docs/` 优先，其次 `.claude/agent-docs/`），确认确实都不存在。
2. 用 `assets/` 下的模板初始化 5 个文件，内容根据当前对话里对项目的了解填写（不要留占位符空着不填，尽量把已知信息填进去；确实不知道的字段写「待补充」）。
3. `DECISIONS.md` 和 `TODO.md` 从当前 session 里能提取出的信息开始建立。
4. 告知用户文件夹已创建，并简要说明以后怎么用（下次直接说"帮我写交接文档"或"context快满了"）。

### 场景 B：文件夹已存在，用户要求"生成交接文档 / 开新 session"

这是最常见的触发场景，按以下顺序执行：

1. **归档前，先读一遍旧的 `AGENT_HANDOFF.md`（如果存在），把里面还没"过期"的关键信息提炼出来**，重点看它的"下一步该做什么"和"已知的坑"两节——这些往往是上一个 session 交给这个 session、但这个 session 还没处理完的事项。**这一步是强制的，不能跳过**：`AGENT_HANDOFF.md` 每次都会被归档，如果不先提炼就直接归档，那些还有效的信息就等于从"当前可见范围"里消失了，下一个新 session 更不会主动去翻档案，等于永久丢失。提炼出来的信息分两类去向：
   - 已经确定、稳定下来的 → 直接更新进 `ARCHITECTURE.md` / `DECISIONS.md` / `TODO.md`
   - 还没解决、这个 session 也没处理完的 → 原样带进新写的 `AGENT_HANDOFF.md`（不要因为"写了新的就该是全新内容"而漏掉还悬而未决的事）
2. **归档旧的 AGENT_HANDOFF.md**：运行 `scripts/archive_handoff.sh <项目agent-docs路径>`，它会把当前的 `AGENT_HANDOFF.md` 移动到 `handoff_archive/AGENT_HANDOFF_<时间戳>.md`，不做任何修改。**旧文件的内容不允许被改写**，只是搬家。
3. **写一份全新的 `AGENT_HANDOFF.md`**，参照 `assets/AGENT_HANDOFF_template.md` 的结构。这份文档要让一个完全没看过本次对话、也没读过旧 handoff 归档的新 session，读完就能立刻继续干活（也就是说它必须自包含第 1 步提炼出的、仍然有效的信息，不能假设读者会去翻档案）。必须包含：
   - **本次 session 做了什么**：简短的变更摘要（改了哪些文件/功能，不是聊天记录流水账）
   - **当前状态**：能跑吗？测试过了吗？现在卡在哪一步？
   - **下一步该做什么**：给新 session 的具体、可执行的下一步指令，越具体越好（比如"运行 `pytest tests/test_auth.py` 应该会失败在 xxx，需要修 yyy"而不是"继续完善认证功能"）。如果上一份 handoff 里有没做完的下一步，要延续下来，不能丢
   - **本次 session 中做的、但还没写进 DECISIONS.md 的临时决定**（如果有，稍后要同步进 DECISIONS.md）
   - **已知的坑/注意事项**：踩过的坑、试过但没用的方案，避免新 session 重复踩坑（包含从旧 handoff 里延续下来的、依然有效的坑）
4. **按需更新其他 4 份稳定文档**（不是重写，是增量编辑）：
   - `README.md`：只有长期使用方式变了才改（比如新增了启动命令、环境变量）
   - `ARCHITECTURE.md`：只有架构/设计发生了稳定的、持久性的变化才改。本次 session 里的临时性探索不要写进这里，等确定下来再写
   - `TODO.md`：勾掉本 session 完成的任务，加入新发现的任务，不要整个重写，保留任务历史的勾选痕迹
   - `DECISIONS.md`：如果本 session 做了值得记录的架构/技术决策，以追加的形式加一条新记录（格式见模板），不要删除或修改已有条目
5. 告诉用户已经完成，交接文档在哪，新 session 应该怎么读（见下方"新 session 如何接手"）。如果用户马上要开新对话，可以直接把 `AGENT_HANDOFF.md` 的内容简要念给用户看一眼确认没问题。

### 场景 C：新 session 开始，用户说"继续之前的项目 / 上次做到哪了"

不要重新扫描整个代码库来猜项目状态。先按"目录结构"一节的确定性规则找到 `agent-docs/` 实际所在路径（`agent-docs/` 或 `.claude/agent-docs/`），再按顺序读取：

1. `agent-docs/README.md` — 了解项目全貌
2. `agent-docs/ARCHITECTURE.md` — 了解架构
3. `agent-docs/AGENT_HANDOFF.md` — 了解最近发生了什么、下一步做什么（这是最重要的，其余三个是背景）
4. `agent-docs/TODO.md` — 了解还有哪些待办
5. 只有在 `AGENT_HANDOFF.md` 里提到具体文件需要查看时，才去读代码库里对应的文件，不要无差别地重新读整个仓库。


## 什么时候读 handoff_archive/，什么时候不读

`handoff_archive/` 存的是历史快照，不是"给 agent 用的当前上下文"，这个区分很重要。

**默认不读，因为：**
- 这个 skill 存在的目的就是让新 session 不用读历史堆积的内容。如果每次开新 session 还要把归档也翻一遍，context 又被撑起来了，等于白做
- 理论上旧 handoff 里所有还有价值的信息，在归档前都应该已经被提炼进了当前的 `ARCHITECTURE.md` / `DECISIONS.md` / `TODO.md` / 新的 `AGENT_HANDOFF.md`（见场景 B 第 1 步）。归档文件里剩下的，理应只是过程性的流水账
- 如果发现"不读归档就没法正常接手"，说明上一次写 handoff 的时候提炼没做到位，应该去修正当前文档，而不是把读归档变成常规动作

**该读的情况（按需、有目标地读，不要无差别通读整个 archive/ 目录）：**
- **追溯某个设计/bug 的历史成因**：比如用户问"这个奇怪的写法是什么时候、为什么引入的"，而 `DECISIONS.md` 里没记录到足够细节，这时候翻对应时间段的归档文件比翻 git log 更快，因为是自然语言写的
- **怀疑提炼过程中漏掉了信息**：新 session 发现上下文有缺口，怀疑是归档时该同步的东西没同步，需要去确认
- **用户明确要求复盘/回顾项目进展**：这更像是给人看的日志需求，不是 agent 接手干活的前置步骤，可以按用户指定的时间范围去读



## AGENT_HANDOFF.md 写作原则

- **面向读者写，不是面向记录写**：假设读者是一个完全没有本次对话记忆的新 agent，它需要的是能马上行动的信息，不是聊天摘要。
- **短**：目标是让新 session 几百字以内就能进入状态，细节该放 ARCHITECTURE.md/DECISIONS.md 的就不要堆在这里。
- **具体**：下一步行动要写成可以直接执行的指令或清晰的验收标准，而不是模糊的方向。
- **诚实**：如果某个方案试了但失败了，要写清楚失败了、为什么失败，避免新 session 重复劳动。
- **自包含，不能依赖读者去翻档案**：新 `AGENT_HANDOFF.md` 写完之后，旧的那份就会被归档，新 session 默认不会去读归档（见"什么时候读 handoff_archive/"一节）。所以上一份 handoff 里任何还没解决、还有效的信息（没做完的下一步、依然存在的坑），都必须在写新版本前提炼出来并原样带入新版本，不能假设"反正历史都在归档里，需要的话自己会去翻"。这是避免关键信息随归档丢失的唯一保障。

## 归档脚本

`scripts/archive_handoff.sh` 用法：

```bash
bash scripts/archive_handoff.sh /path/to/agent-docs
```

会把 `AGENT_HANDOFF.md`（如果存在）移动为 `handoff_archive/AGENT_HANDOFF_YYYY-MM-DD_HHMM.md`，然后主目录下不再有旧的 `AGENT_HANDOFF.md`（因为马上会被新写的一份取代）。如果 `agent-docs` 目录本身不存在，脚本会报错提醒先做场景 A 的初始化。

## 模板文件

- `assets/README_template.md`
- `assets/ARCHITECTURE_template.md`
- `assets/AGENT_HANDOFF_template.md`
- `assets/TODO_template.md`
- `assets/DECISIONS_template.md`

初始化项目文档文件夹或新写 `AGENT_HANDOFF.md` 时，参照对应模板的结构填写，不要照抄模板里的示例文字。
