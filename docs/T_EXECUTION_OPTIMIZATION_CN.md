# 盘中 T 执行优化

这轮优化做了两件事：

1. 盘中 timing / T overlay 不再只依赖全局阈值
2. T 审计进入正式审计包和网站报告

当前执行优化点：

- `timing_rules.py`
  - 引入基于机制 / 事件 / 生命周期 / 时间窗口 / 快照质量的 T policy
  - 将 policy 阻断原因写回 `timing_freeze_reason`

- `t_overlay.py`
  - 每个标的按 policy 解析 `max_t_ratio`
  - 是否允许 second leg 不再只看全局开关

- `midday_review.py`
  - 会带上最新 T 审计摘要
  - 午间计划可以直接看到最常见阻断和最适配机制

- `strategy_audit.py`
  - 审计包内新增 `t_overlay_analysis`

当前目标不是把盘中执行做成复杂自治系统，而是：

- 明确 T 的适用边界
- 减少错误触发
- 保留审计解释链

