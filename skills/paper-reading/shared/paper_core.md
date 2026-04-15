# Paper Core — 论文理解共享层

所有子模块都依赖这里提取的内容。入口 `skill.md` 读取论文后，填充以下结构，后续模块直接复用，**不重复读论文**。

---

## 提取框架

读取论文后，在内部构建以下「论文核心卡片」（不直接展示给用户，作为所有后续模块的原材料）：

```
PAPER_CORE = {

  # ── 基本信息 ──────────────────────────────────────────
  title:        论文标题（英文原文）
  year:         发表年份
  venue:        发表期刊/会议（如 NeurIPS 2024、Nature、CoRL 2023）
  authors:      作者列表（简写，如 "Zhang et al." 或列出前三位）
  paper_type:   论文类型（方法论文 / 分析论文 / 综述 / 应用论文 / 数据集论文）
  open_source:  代码/数据是否开源？（是/否/部分），附链接（如有）
  arxiv:        arXiv 链接或 DOI（如有）

  # ── 核心内容 ──────────────────────────────────────────
  one_liner:    一句话核心思想，≤20字，不用术语
                例："让机器人在仿真中练习，迁移到真实世界后依然好用"

  problem:      这篇论文要解决什么问题？（2-3句，口语化，说清楚为什么这个问题难）
  prior_work:   现有主流方法是什么？它们的核心局限在哪里？（2-4句，具体方法名）
  hypothesis:   本文的核心假设是什么？（1-2句，即"我们认为…所以…"）
  insight:      核心洞察/创新点（2-4条，每条一句，具体而非泛泛）
  contributions:论文明确声称的贡献列表（直接来自原文 Introduction，逐条列出）

  # ── 方法 ──────────────────────────────────────────────
  method:       方法流程概述（4-6步，每步一句，含关键技术细节）
  key_modules:  核心模块/组件列表，每个模块一句话说明其作用
                例：["Privileged Teacher：使用仿真特权信息训练教师策略",
                     "Student Distillation：学生只用本体感知蒸馏教师"]
  datasets:     使用的数据集/环境列表（名称 + 规模 + 用途，如训练/验证/测试）
  metrics:      评估指标列表（名称 + 含义）
                例："Success Rate：任务完成率；Tracking Error (m)：末端轨迹误差"

  # ── 实验结果 ──────────────────────────────────────────
  result:       最重要的实验结论（3-5条，每条含具体数字 + 对比基线）
                例："在 ANYmal 上四足步态成功率达 91%，比 PPO baseline 高 23%"
  ablation:     消融实验的关键发现（哪个模块/设计最关键？去掉后掉了多少？）
  failure_case: 方法在哪些情况下表现不好？（如有 failure analysis）

  # ── 评估与展望 ────────────────────────────────────────
  significance: 为什么重要？对哪个领域/人群有用？可能带来什么影响？
  limitation:   主要局限性（包括作者自己承认的和读者能看出的）
  future_work:  作者提出的未来研究方向（来自原文 Conclusion/Future Work）
  prerequisites:读懂这篇论文需要哪些前置知识？（列出2-4个关键概念）

  # ── 创意模块专用 ──────────────────────────────────────
  fun_fact:     反直觉的发现、意外失败、有趣的消融结果（可留空）
  key_concepts: [术语1, 术语2, ...]  # 论文中的关键技术词汇，附简短中文解释
  analogy:      一个生活化类比，帮助非专业人士理解核心方法
                例："就像先在游戏里练习开车，再去真实道路上考驾照"

  # ── Robotics & Learning-based Control 专用 ────────────
  # 以下字段仅当论文涉及机器人学习控制时填写，否则填 null

  robot_task:       控制任务类型
                    （locomotion / manipulation / navigation / whole-body / aerial / 其他）
  obs_space:        observation 构成
                    例："proprio (joint pos/vel/IMU) + depth image 64×64"
  action_space:     action 形式
                    例："关节力矩 12-dim，控制频率 50Hz"
  policy_type:      policy/controller 形式
                    （MLP / CNN / Transformer / Diffusion Policy / MPC / 其他）
  training_paradigm:学习范式
                    （RL-on-policy / RL-off-policy / BC / DAgger / IRL / MBRL / hybrid）
  reward_terms:     RL reward 各项 term 及其物理意义（如有）
                    例：["tracking_reward：鼓励跟踪指令速度",
                         "energy_penalty：惩罚关节力矩过大",
                         "survival_bonus：每步存活奖励"]
  sim_platform:     仿真平台（MuJoCo / Isaac Gym / Gazebo / 自研 / 无）
  real_platform:    真实硬件平台（机器人型号、自由度）
                    例："ANYmal-C，18-DoF 四足机器人"
  sim_to_real:      sim-to-real 策略概述
                    例："动力学随机化（质量±30%、摩擦系数±50%）+ 延迟随机化"
  control_freq:     控制频率（Hz），推理是否满足实时要求
  paper_subtype:    论文子类型（从下列选一个）：
                    RL-based / Imitation Learning / Model-based / Sim-to-Real /
                    Foundation Policy / Safe Control / System ID / Hardware / 其他
}
```

---

## 提取原则

- `one_liner` 和 `analogy` 是后续所有创意模块的基础，必须认真写，不能敷衍
- 所有数字必须来自论文原文，不能估算或捏造
- `contributions` 直接从原文 Introduction 里找，不要自己总结替换
- `fun_fact` 优先找：反直觉结果、意外失败、有趣的消融实验、作者自己也觉得 surprising 的发现
- `ablation` 是理解方法设计动机的关键，尽量填写
- Robotics 专用字段仅在相关论文中填写；纯理论/算法论文这些字段填 `null` 即可
- 如果是**综述类论文**：`method` 改为"覆盖的主要研究方向"，`key_modules` 改为"主要子领域"
- 如果是**数据集论文**：重点填写 `datasets` 和 `metrics`，`method` 描述数据收集/标注流程
- 字段找不到时填 `null`，不要捏造内容
