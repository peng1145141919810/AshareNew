# T 审计层

当前 `T` 不是独立 alpha。

它是盘中执行增强层，核心问题是：

- 哪些窗口尝试了 T
- 哪些窗口真正触发并成交
- 哪些样本被正确阻断
- 哪些样本可能阻断过严
- T 是否改善了目标仓位与实际仓位之间的执行缺口

当前正式产物：

- `data\audit_v1\latest\latest_t_audit.json`
- `data\audit_v1\latest\t_overlay_window_daily.csv`
- `data\audit_v1\latest\t_overlay_reject_reasons.csv`
- `data\audit_v1\latest\t_overlay_mechanism_summary.csv`
- `data\audit_v1\latest\t_overlay_event_summary.csv`
- `data\audit_v1\latest\t_overlay_quality_summary.csv`

当前评估口径：

- 不把 T 伪装成日内收益账本
- 以 `desired_vs_actual_gap` 的改善作为执行质量代理
- 结合 `fill_ratio`、`timing_state`、`t_overlay_state`、`freeze_reason`
- 输出窗口、机制、事件、质量层面的阻断与执行统计

当前主入口：

- `hub_v6\t_audit.py`
- `hub_v6\strategy_audit.py`
- `scripts\probe_t_audit.py`

