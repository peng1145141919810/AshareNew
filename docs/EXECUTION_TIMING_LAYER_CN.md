# 盘中 Execution Timing Layer

## 定位
- 这层只决定什么时候更适合买、什么时候更适合卖。
- 它不负责重新选股，不改 release 合同，不改 V2A 生命周期真相。
- 上游真相仍然是 `release + OMS + safety + intraday formal phase`。

## 当前输入
- 技术面主驱动：
  - `last_price_vs_prev_close`
  - `last_price_vs_open`
  - `last_price_vs_vwap`
  - `intraday_return_from_low`
  - `intraday_return_from_high`
  - `opening_gap_pct`
  - `opening_range_breakout_up/down`
  - `morning_high_fail_flag`
  - `intraday_reversal_up/down_flag`
  - `micro_trend_slope_short/medium`
  - `vwap_reclaim_flag`
  - `vwap_break_flag`
  - `intraday_amplitude_pct`
  - `distance_from_vwap_pct`
  - `distance_from_day_high_pct`
  - `distance_from_day_low_pct`
  - `relative_strength_vs_index`
  - `relative_strength_vs_industry`
  - `relative_strength_rank_intraday`
- 资金面确认：
  - `intraday_amount_ratio`
  - `intraday_volume_ratio`
  - `turnover_acceleration`
  - `amount_acceleration`
  - `price_up_amount_up_flag`
  - `price_up_amount_down_flag`
  - `price_down_amount_up_flag`
  - `relative_liquidity_vs_history`
  - `relative_amount_vs_industry`
  - `volume_confirmation_flag`
- 消息 veto：
  - `forecast/express` 公告窗口代理
  - `stk_limit` 涨跌停边缘
  - 异常波动代理
  - `is_suspended / is_st` 等基础拦截

## 时间窗口
- `open_noise_window`: `09:30-09:40`
- `morning_primary_window`: `09:40-10:30`
- `mid_morning_low_speed_window`: `10:30-11:20`
- `afternoon_primary_window`: `13:00-14:20`
- `late_afternoon_reconcile_window`: `14:20-14:50`
- `post_1450_close_only_window`: `14:50-15:00`

## 评分
- `buy_timing_score`
  - `buy_technical_component`
  - `buy_flow_confirmation_component`
  - `buy_posture_component`
  - `buy_penalty_component`
- `sell_timing_score`
  - `sell_technical_component`
  - `sell_flow_confirmation_component`
  - `sell_risk_pressure_component`
  - `sell_penalty_component`

## 产物
- `data/trade_clock/intraday_state/latest/intraday_phase_state.json`
- `data/trade_clock/intraday_state/latest/symbol_execution_state.csv`
- `data/trade_clock/intraday_state/latest/intraday_control_summary.json`

## 当前限制
- 当前本地 `daily_price_snapshot.csv` 没有稳定的分钟级 `open/high/low/vwap/volume` 全字段。
- 所以 timing 层会诚实降级：
  - `feature_quality_tier=full_intraday_snapshot`
  - `feature_quality_tier=snapshot_degraded`
  - `feature_quality_tier=no_live_snapshot`
- 当字段缺失时，不伪造分钟级真值，只做可解释降级。
- 当前 overlay 仍然是全局 plan 级，不是每个 symbol 的执行白名单直连券商。
