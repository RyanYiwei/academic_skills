---
name: paper-reading
description: "论文深度分析工具，覆盖机器人学/控制领域及通用学术论文。每当用户上传论文 PDF 并要求'分析'、'深度解读'、'帮我看看这篇论文讲了什么'、'详细分析一下'时触发。也包括用户说'解读这篇论文'、'这篇论文的方法是什么'、'帮我理解这篇论文'等场景。"
---

# Paper Analysis

> **工具适配说明**：
> - **Claude Desktop**：使用 `view` 工具
> - **Claude Code**：使用 `Read` 工具，路径前缀为 `${CLAUDE_SKILL_DIR}/`

---

## 第一步：前置检查

检查用户是否提供了论文内容：

- ✅ 上传了 PDF / 粘贴了文本 / 提供了摘要 → 继续
- ❌ 未提供 → 回复："请上传论文 PDF 或粘贴论文内容，我来帮你深度分析。"

---

## 第二步：理解论文

使用 `Read` 工具读取 `${CLAUDE_SKILL_DIR}/shared/paper_core.md`，按照其中定义的提取框架，在内部构建 `PAPER_CORE`。

这一步**静默完成，不向用户展示提取过程**。

**字段缺失处理**：缺失字段填 `null`，报告中遇到 `null` 时注明"论文未涉及"，不捏造内容。

---

## 第三步：判断论文领域并路由

根据 `PAPER_CORE` 的内容，判断这篇论文是否属于 **Robotics / Control / Learning-based Control** 领域。

**判断依据**（满足其中一条即视为机器人/控制类）：
- 论文研究对象是物理系统的控制（locomotion、manipulation、navigation、飞行、自动驾驶等）
- 核心方法涉及强化学习用于控制、imitation learning、model predictive control、adaptive control
- 实验平台是机器人硬件或物理仿真环境（MuJoCo、Isaac Gym、Gazebo 等）
- 关键词包含：policy learning、sim-to-real、dynamics model、reward function、robot、actuator、trajectory tracking 等

**路由规则**：

- ✅ **属于机器人/控制领域** → 使用 `Read` 工具读取 `${CLAUDE_SKILL_DIR}/shared/robotics.md`，严格按照其中的报告框架生成分析
- ✅ **不属于，是通用学术论文** → 使用 `Read` 工具读取 `${CLAUDE_SKILL_DIR}/shared/general.md`，严格按照其中的报告框架生成分析

读取对应文件后，直接进入报告生成，**不向用户展示路由过程**。
