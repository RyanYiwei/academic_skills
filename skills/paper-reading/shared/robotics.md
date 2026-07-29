# 报告框架 — Robotics & Learning-based Control

本文件供 `skill.md` 在判定论文属于机器人/控制领域后读取，定义完整的分析报告框架。

---

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

输出完整分析报告。风格：专业严谨，面向同方向的工科研究生。全程中文，专业术语保留英文原文。

严格按照以下 8 个部分输出，不得省略。

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

### 2. 方法精读

> ⚠️ 直接对照论文原文的 Methods 部分，保留论文自身的章节结构。逐节展开，不做合并压缩。

按照论文 Methods 的原始小标题逐节分析，每节格式如下：

---

**`§X.X 原始节标题（英文）`**

**这一节在做什么**：1-2 句话说清楚本节的核心目标。

**技术细节**（按实际涉及的维度展开，没有的维度跳过）：

- **数学公式**
  - 写出本节所有关键公式（使用 LaTeX 或清晰的文字表达）
  - 逐项解释每个符号：物理含义是什么、取值范围、单位
  - 说明公式的输入从哪里来、输出去哪里用

- **网络结构**
  - 整体架构类型：MLP / CNN / Transformer / RNN / Diffusion / 混合
  - 各子网络的输入维度、隐层维度、输出维度
  - 编码器设计：如何处理图像（CNN kernel/stride）、proprioception（MLP 层数）、点云（PointNet/3D conv）
  - 是否使用注意力机制：self-attention / cross-attention / 位置编码方式
  - 时序建模：是否有 LSTM / GRU / causal Transformer / history window
  - 归一化方式：BatchNorm / LayerNorm / 无
  - 激活函数选择及原因（ELU / ReLU / Tanh 等）
  - 多模块间权重是否共享

- **训练方式**
  - **RL 类**：算法选择（PPO / SAC / TD3 / …）及原因；reward 函数各项 term、权重系数、物理意义；rollout 长度与 update 频率；是否用 curriculum（难度如何递增）；value function 结构
  - **IL 类**：demonstration 来源（人工 / MPC / 其他 policy）；loss 函数（MSE / NLL / GAIL…）；如何缓解 distribution shift（DAgger / data augmentation / …）；训练数据量
  - **Model-based 类**：dynamics model 的形式（神经网络 / 解析模型 / 混合）；如何训练；如何用于规划（shooting / CEM / …）或辅助 RL
  - **通用**：优化器与学习率调度；batch size；训练总步数/轮数；多阶段训练（如 pre-train → fine-tune）；正则化手段（dropout / weight decay / gradient clipping）

- **改进策略**
  - 相比直接套用 baseline，作者做了哪些针对性修改？
  - 每个改动是为了解决什么具体问题（过拟合 / 训练不稳定 / sim-to-real gap / 计算效率等）

**解决了什么问题**：这个设计对应 Introduction 里提出的哪个具体痛点？

**在整体框架中的作用**：这一节的输出如何流入下一个模块？去掉这一节整个系统会在哪里断掉？

---

> 如果某节内容极少（如纯 notation 定义），可附在上一节末尾，注明"§X.X 符号定义"。

---

### 3. 方法总结（基于精读提炼）

**a) 整体 Pipeline（速览）**
用 4-6 步概括整个方法的数据流：输入 → 各处理步骤 → 输出。比方法精读更精简，侧重模块间的逻辑关系。

**b) 核心设计决策**
从方法精读中提炼出 2-4 个最关键的设计选择，说明"为什么这样选而不是用更简单的方案"。

**c) Sim-to-Real 策略**（如适用）
- 使用了哪些 domain randomization（动力学参数、外观、延迟等）？
- 有没有 adaptation 模块（如 RMA 的 estimator、online system ID）？
- 部署时 policy 是否需要修改？

---

### 4. 与现有方法对比

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

### 5. 实验分析

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

### 6. 实际部署考量

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

### 7. 总结与个人思考

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
- 重点在**方法精读**和**实验分析**，引言与结论不过度展开
- 控制领域专有名词保留英文（如 PPO、CBF、domain randomization、end-effector 等），必要时附简短解释
- 完成后询问："还需要做其他的吗？我可以进一步：生成这篇论文的方法思维导图、与某篇具体论文做对比分析、帮你整理 related work 脉络、或者起草 paper note。"
