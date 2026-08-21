---
name: build-audit-loop
description: "面向普通软件开发（网站、App、CLI、后端服务等非学术代码）的'写代码 → 交给 Codex 系统性审查 → 按反馈修改'闭环工具。Claude 先按用户想法实现或修改代码，再调用 Codex（mcp__codex__codex）对实际代码做功能完整性、轻量化、内存与并发安全、网络安全、隐私数据泄漏、数据可靠性等方面的审查，循环打分-修复，直到加权总分 ≥9 且没有未解决的 Critical 问题，或达到最大轮数。当用户说'帮我写一个xxx然后用codex审查一下'、'写完让codex看看'、'code review with codex'、'打磨这段代码到能上线'等时触发。"
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, mcp__codex__codex, mcp__codex__codex-reply
---

# Build & Audit Loop

写真实代码（不是论文/研究产出）时用的闭环工具：Claude 实现 → Codex 用一份通用的系统性审查框架挑毛病 → Claude 按严重程度修复 → Codex 复审，如此循环，直到审查通过或轮数耗尽。和仓库里其他偏学术的 skill（note-taking / paper-reading / session-handoff）相互独立，不共享输出目录。

## 适用前提

- 需要 Claude Code 环境，且已配置好 Codex MCP（`mcp__codex__codex` / `mcp__codex__codex-reply` 能正常调用）。
- Claude Desktop 不支持（没有 Bash、没有 Codex MCP），不要在 Desktop 场景触发这个 skill。

## 核心循环

```
用户想法 / 已有代码
  -> 第一步：锁定项目基线（Project Anchor）
  -> 第二步：Claude 实现/修改代码，实际跑一遍
  -> 第三步：Codex 系统性审查（读 shared/audit_rubric.md 生成完整 prompt）
  -> 第四步：按 Critical > High > Medium 顺序修复，可对不合理建议 pushback
  -> 第五步：Codex 用同一个 thread 复审
  -> 重复第三~五步，直到 加权总分 ≥ 9 且没有未解决的 Critical，或达到 MAX_ROUNDS（默认 5）
  -> 第六步：输出最终审查报告
```

## 参数

- `MAX_ROUNDS`：默认 5。
- `SCORE_THRESHOLD`：默认 9（满分 10 的加权总分）。
- 六个审查维度默认权重：功能完整性 15%、轻量化设计 15%、内存与并发安全 20%、网络与服务端安全 20%、隐私与数据泄漏风险 20%、数据可靠性 10%。某个维度确实不适用（比如纯前端静态站点没有"数据可靠性"这一说）时按比例分给其余维度，并在发给 Codex 的 bundle 里写清楚原因。
- 用户可以在触发时用类似 `-- max rounds: 3, threshold: 8.5` 的方式覆盖默认值。

## 第一步：锁定项目基线

在 `audit/PROJECT_ANCHOR.md` 里写清楚（这是后面 Codex 判断"必须修"还是"过度工程化"的唯一依据，务必具体）：

- 一句话目标：用户到底想做什么。
- 起点：全新项目，还是在已有代码库（给出路径）上改/修。
- 技术栈：语言、框架、有没有客户端/服务端拆分。
- 部署场景：个人自用自建、内部工具、面向公众的服务、还是原型/一次性脚本——这个字段直接决定后面安全审查的松紧尺度。
- 是否涉及敏感数据，涉及哪种（凭据、健康数据、财务数据、个人隐私信息……），没有的话明确写"无"，不要留空。
- 非目标：明确不打算做的事（比如"不做多租户鉴权""不为超大规模优化"）。
- 约束：时间、允许/禁止使用的依赖、目标设备、离线要求、必须对接的现有基础设施。
- 成功标准：达到什么程度用户会觉得"这个可以真的拿去用/上线了"。

## 第二步：实现或修改代码

- 如果已有代码，先读懂现状——架构、入口、数据流、哪些已经实现哪些是占位——再动手，不要不分青红皂白重写整个项目。
- 优先用满足基线目标所需的最小依赖、最简架构。第三步的审查会对不必要的复杂度和资源占用扣分，跟功能缺失一样重，不要为"未来可能需要"预先堆功能。
- 实际跑一遍：编译/构建、跑 lint 和已有测试、启动服务或 app 走一遍主路径，命中真实的接口。这一步做不到的地方（比如没有 iOS 模拟器/真机）要在记录里明说没测过，不能假装测过了。
- 把这一轮做了什么、怎么跑/测的、还没做完的部分写进 `audit/round-0-build-notes.md`。

## 第三步：Codex 系统性审查

读取 `shared/audit_rubric.md` 里的完整审查框架，把第一步基线里的信息（目标 / 技术栈 / 部署场景 / 敏感数据 / 非目标）填进框架里的占位符，连同项目根目录、`PROJECT_ANCHOR.md`、`round-0-build-notes.md` 的绝对路径一起写进 `audit/codex_round_1_bundle.md`（避免把整份 rubric 直接塞进 MCP prompt，那会很长），再用一句简短的 prompt 让 Codex 去读这个文件：

```
mcp__codex__codex:
  model: gpt-5.6-sol
  config: {"model_reasoning_effort": "xhigh"}
  prompt: |
    请阅读 <audit/codex_round_1_bundle.md 的绝对路径> 并严格按照其中的说明执行审查。
```

**保存这次调用返回的 `threadId`**——后续所有轮次的复审都要用 `mcp__codex__codex-reply` 复用同一个 thread，这样 Codex 才能记得之前审过什么。**完整保存 Codex 的原始回复**（不要摘要、不要改写），存进 `audit/round-1-review.md`。

## 第四步：按优先级修复

1. 从 `round-N-review.md` 里提取六个维度的打分、加权总分、verdict，以及所有 Critical / High / Medium / Low 问题（每条应包含文件、函数、触发条件、后果、修复建议）。更新 `audit/SCORE_HISTORY.md` 的打分表。
2. **停止条件**：加权总分 ≥ `SCORE_THRESHOLD`，verdict = READY，且没有未解决的 Critical → 跳到第六步。三个条件必须同时满足——总分很高但还挂着一个 Critical（比如 token 明文写进日志）不算过关。
3. 没达标就修：先修全部 Critical，再修 High，时间精力允许再修 Medium，Minor 可以先记下来延后处理，不必每轮都清空。
4. 回看 `PROJECT_ANCHOR.md` 里的部署场景——如果 Codex 的建议明显不符合这个项目实际的威胁模型（比如给一个只有自己用的自建工具要求证书 pinning 级别的加固），可以带着理由 pushback，而不是照单全收；但理由必须写清楚、扣得住基线里的部署场景，不能只是"我觉得不需要"。
5. 改完之后按第二步的方式重新验证一遍，不要没验证就在记录里写"已修复"。
6. 把这一轮改了什么、pushback 了什么（及理由）、验证结果记进 `audit/round-N-fixes.md`。

## 第五步：复审

流程和第三步类似，但用 `mcp__codex__codex-reply`（同一个 `threadId`）。bundle 里带上这一轮实际改了哪些文件（或给一个 `git diff` 范围）和 `round-N-fixes.md` 的路径，要求 Codex 去读真实的 diff 验证，而不是只信任修复记录里的描述。要求它：

- 对每个之前的 Critical / High 问题明确给出 RESOLVED / PARTIALLY RESOLVED / STILL OPEN；
- 对每条 pushback 给出 SUSTAINED（认可理由）或 OVERRULED（风险依然真实存在）的裁决，并说明理由；
- 重新给六个维度打分和加权总分；
- 检查有没有因为这轮修改引入新的回归问题。

存进 `audit/round-N-review.md`，回到第四步，直到满足停止条件或到达 `MAX_ROUNDS`。

## 第六步：输出最终报告

写 `audit/FINAL_REPORT.md`，包含：

- 最终六维度打分与加权总分、verdict。
- 逐轮解决记录表（每轮的主要问题、做了什么、结果）。
- Pushback 记录表（Codex 说了什么、Claude 怎么回应、最终裁决）。
- 剩余未解决问题（包括被推迟的 Minor 项）。
- Codex 最后一轮给出的"最终结论"问答（详见 `shared/audit_rubric.md` 第 8 节）：是否足够轻量、能否长期跑、有没有明显内存/资源泄漏风险、有没有明显数据泄漏风险、暴露在网络上是否有明显攻击面风险、能不能拿真实数据/真实场景使用、上线前最该修的 3-5 件事。

然后给用户一段简短总结：跑了几轮、最终分数、还剩什么问题、报告文件在哪。

## 使用建议

- 调用 Codex 时始终使用 `config: {"model_reasoning_effort": "xhigh"}`。
- 不要在没实际跑/测的情况下声称验证过某个修复。
- 每一轮 Codex 的原始回复都要完整保存在对应的 `round-N-review.md` 里，不要只留摘要——摘要是给人看的，原始回复是唯一可信的记录。
- 审查发现要具体：文件、函数/类、触发条件、后果、严重程度、建议改法，Claude 和 Codex 双方都要遵守这个标准，不接受"感觉有风险"这种没有依据的判断。
