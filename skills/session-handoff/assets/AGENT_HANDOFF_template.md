# Agent Handoff

> 写给下一个 session 的交接文档。假设读者完全没有本次对话的记忆，只读过 README.md 和 ARCHITECTURE.md。目标：让它在几分钟内接手继续干活，而不是重新探索整个项目。
> 这份文档每次都是全新写的，不修改上一份（上一份已被归档到 handoff_archive/）。

**生成时间**：<YYYY-MM-DD HH:MM>
**上一份交接文档**：`handoff_archive/AGENT_HANDOFF_<上次时间戳>.md`（如果是第一次，写"无"）

## 本次 session 做了什么

<简短的变更摘要，说"改了什么"而不是"聊了什么"。例如：
- 实现了用户登录的 JWT 校验逻辑（`src/auth/jwt.py`）
- 修复了 `/api/users` 分页参数的 off-by-one bug
- 给 `OrderService` 加了单元测试，覆盖率从 40% 到 65%>

## 当前状态

<能跑起来吗？测试过了吗？现在具体卡在哪一步？例如：
- 代码能跑，`pytest` 全绿
- 手动测试过登录流程，正常
- 卡住的地方：token 刷新逻辑还没写，现在过期后只能重新登录>

## 下一步该做什么

<给新 session 的具体、可执行的指令，越具体越好，最好带验收标准。例如：
1. 实现 `src/auth/refresh.py` 里的 token 刷新逻辑，参考 `ARCHITECTURE.md` 里 JWT 那一节的设计
2. 跑 `pytest tests/test_auth.py::test_refresh` 应该会失败，通过之后再检查 `test_refresh_expired`
3. 之后需要把这部分同步更新到 ARCHITECTURE.md 的"认证流程"章节>

## 本次做的临时决定（待同步进 DECISIONS.md）

<如果本 session 中做了一些值得记录的技术决策，但还没来得及正式写进 DECISIONS.md，先在这里列出来，下次更新时补进去。如果本次交接已经同步完，写"已同步，见 DECISIONS.md"。>

## 已知的坑 / 踩过的雷

<试过但没用的方案、遇到的坑，避免下一个 session 重复踩。例如：
- 试过用 `bcrypt` 直接同步调用，会阻塞事件循环，后来换成异步版本
- <坑2>>
