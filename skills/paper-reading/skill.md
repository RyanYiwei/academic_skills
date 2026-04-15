---
name: paper-analysis-robotics
description: "机器人学与控制领域论文深度分析工具，专注于 learning-based control。每当用户上传论文 PDF 并要求"分析"、"深度解读"、"帮我看看这篇论文讲了什么"、"详细分析一下"时触发。也包括用户说"解读这篇论文"、"这篇论文的方法是什么"、"帮我理解这篇论文"等场景。"
---

# Paper Analysis — 机器人与控制领域论文深度分析

> **工具适配说明**：本 Skill 中"读取文件"操作在不同环境下使用不同工具：
> - **Claude Desktop**：使用 `view` 工具
> - **Claude Code**：使用 `Read` 工具
>
> 本 Skill 专为 **Robotics & System Control / Learning-based Control** 方向定制，分析框架会自动适配该领域的核心问题与惯用术语。

---

## 第一步：前置检查

检查用户是否提供了论文内容：

- ✅ 上传了 PDF / 粘贴了文本 / 提供了摘要 → 继续
- ❌ 未提供 → 回复："请上传论文 PDF 或粘贴论文内容，我来帮你深度分析。"

在开始前，先在内部判断论文属于以下哪个子类型（不向用户展示，但后续分析要贴合该类型的核心关切）：

| 类型 | 判断依据 |
|------|----------|
| **RL-based control** | 用 reward 驱动 policy 学习，on/off-policy 算法 |
| **Imitation Learning / BC** | 从 demo 学习，behavior cloning、IRL、GAIL 等 |
| **Model-based / MBRL** | 显式建立系统 dynamics model，用于规划或辅助 RL |
| **Sim-to-Real** | 核心贡献在于缩小 sim-real gap，domain randomization、adaptation |
| **Foundation / Generalist Policy** | 大规模数据预训练，zero/few-shot 泛化，如 RT-X、π₀ |
| **Safe / Constrained Control** | 显式约束满足，safety filter、CBF、Lyapunov 相关 |
| **System ID / Adaptive Control** | 在线或离线识别系统参数，自适应律设计 |
| **Hardware / System Paper** | 主要贡献是平台设计、驱动器、传感器集成 |

---

## 第二步：理解论文

使用 `Read` 工具读取 `${CLAUDE_SKILL_DIR}/shared/paper_core.md`，按照其中定义的提取框架，在内部构建 `PAPER_CORE`。

这一步**静默完成，不向用户展示提取过程**。

**字段缺失处理**：缺失字段填 `null`，在报告中遇到 `null` 字段时注明"论文未涉及"，不捏造内容。

---

## 第三步：生成深度分析报告

基于 `PAPER_CORE` 输出完整分析报告。风格：专业严谨，面向同方向的工科研究生。全程中文，专业术语保留英文原文。

严格按照以下 7 个部分输出，不得省略。

---

### 0. 摘要翻译

将论文摘要原文翻译为中文，保持学术语言风格，不做删减。

---

### 1. 问题定义与动机

**a) 要解决的控制问题**
明确说明：
- 控制任务是什么（locomotion / manipulation / navigation / 其他）？
- 系统的 observation space 和 action space 是什么？
- 对系统动力学有什么假设（已知 / 部分已知 / 完全未知）？

**b) 现有方法的痛点**
现有方法（传统控制 or 已有学习方法）在这个问题上卡在哪里？要具体，不泛泛而谈。
例如：MPC 需要精确模型、纯 BC 存在 distribution shift、RL 样本效率低等。

**c) 核心假设与 insight**
作者的核心 insight 是什么？用 2-3 句话概括本文认为"为什么这样做能解决上述痛点"。

---

### 2. 方法设计

> ⚠️ 核心部分，必须细致——用户可能不会再读原文。

**a) 整体 Pipeline**
输入 → 每个处理步骤（含技术细节）→ 输出。每步说明：做了什么、为什么这样设计。

**b) Policy / Controller 结构**
- 网络结构是什么（MLP / CNN / Transformer / diffusion / 其他）？
- 输入特征如何处理（proprioception、视觉特征提取方式等）？
- 输出是什么（直接 action / residual / 参数化轨迹 / 其他）？
- 如果有层级结构（high-level planner + low-level controller），分别说明。

**c) 训练方式**
- RL：reward 函数设计（各项 reward term 的物理意义）、算法选择（PPO / SAC / TD3…）、curriculum 策略
- IL：demonstration 来源、loss 设计、如何处理 distribution shift
- Model-based：dynamics model 的形式与训练方式、如何用于规划/辅助 RL
- 混合方法：各模块如何协同训练

**d) 关键公式解释**（如有）
通俗解释每个关键公式或 loss term 的含义，说明其在控制/学习目标中的作用。

**e) Sim-to-Real 策略**（如适用）
- 使用了哪些 domain randomization（动力学参数、外观、延迟等）？
- 有没有 adaptation 模块（如 RMA 的 estimator、online system ID）？
- 部署时 policy 是否需要修改？

---

### 3. 与其他方法对比

**a) 本质区别**
与该领域主流方法（传统控制 / 已有学习方法）最根本的不同在哪里？

**b) 核心贡献**（编号列出）

**c) 适用场景与局限**
- 什么任务/环境下这个方法更有优势？
- 明确不适用的场景（例如：需要精确力控的任务 / 高速动态系统 / 数据稀缺场景）？

**d) 对比表格**

| 方法 | 类型 | 核心思路 | 是否需要模型 | 数据来源 | 优点 | 缺点 |
|------|------|----------|-------------|---------|------|------|
| 本文方法 | | | | | | |
| Baseline 1 | | | | | | |
| Baseline 2 | | | | | | |

---

### 4. 实验分析

**a) 实验设置**
- 仿真平台（MuJoCo / Isaac Gym / PyBullet / 其他）？
- 真实硬件平台（机器人型号、自由度、传感器）？
- 任务设置与难度梯度（是否有 curriculum）？
- 评估指标（success rate / tracking error / energy / 其他）及其物理含义？

**b) 关键结果**
最具代表性的实验数据和结论，数字要具体。
- 与 baseline 对比的核心提升点
- 真实机器人实验结果（如有），与仿真结果是否一致？

**c) 消融实验**
作者去掉哪些模块后性能下降最显著？这说明哪个设计是最关键的贡献？

**d) 局限性与潜在失效场景**
- 泛化能力如何（不同地形 / 物体 / 扰动）？
- 计算开销：训练时间、推理频率能否满足实时控制？
- 对 sim-to-real gap 的敏感性（哪些参数变化会导致 policy 失效）？

---

### 5. 实际部署考量

**a) 开源情况**
代码 / 模型 / 数据集是否开源？链接？

**b) 复现关键细节**
- 重要超参数（网络大小、学习率、reward 权重、rollout 长度等）
- 训练数据量级（环境步数 / demonstration 数量）
- 容易被忽略的训练技巧（observation normalization、action clipping、reward shaping 细节等）

**c) 迁移潜力**
- 能否迁移到其他机器人平台或任务类型？需要改动哪些部分？
- 这篇论文的哪个模块/思路可以作为其他工作的组件复用？

---

### 6. 总结与个人思考

**a) 一句话核心思想**（≤ 20 字）

**b) 速记版 Pipeline**（3-5 步，不用论文术语，直白具体）

示例格式：
1. 在仿真中随机化动力学参数，训练 RL policy
2. 用 privileged information 训练 teacher policy，再蒸馏给 student
3. Student policy 只用 proprioception，部署到真实机器人

**c) 值得关注的开放问题**
这篇论文没有解决、但读完后你觉得值得继续研究的问题（1-3 条）。

---

## 输出规范

- 若论文未涉及某子项，注明"论文未涉及"而非跳过
- 重点在 **方法设计** 和 **实验分析**，引言与结论不过度展开
- 控制领域专有名词保留英文（如 PPO、CBF、domain randomization、end-effector 等），必要时附简短解释
- 完成后询问："还需要做其他的吗？我可以进一步：生成这篇论文的方法思维导图、与某篇具体论文做对比分析、帮你整理 related work 脉络、或者起草 paper note。"
