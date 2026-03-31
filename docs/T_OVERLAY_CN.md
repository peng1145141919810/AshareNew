# T Overlay

## 定位
- `T overlay` 是长期持仓上的盘中叠加层。
- 它不是独立短线策略。
- 它不能绕过 `release / safety / OMS / V2A`。

## 当前支持的状态
- `t_disabled`
- `t_armed`
- `t_sell_leg_done_wait_buyback`
- `t_buy_leg_done_wait_sellback`
- `t_completed`
- `t_frozen`

## 当前逻辑
- 只在以下生命周期上尝试：
  - `hold`
  - `build`
  - `trim`
  - 少量 `pilot`
- 只在有老底仓代理时尝试：
  - 当前实现使用 `available_shares > 0` 作为老底仓近似判断
- 第一腿只在主执行窗口内触发：
  - 正 T：先卖腿
  - 反 T：先买腿
- 第二腿只在下午第二主窗口/收敛窗口内补完

## 风控
- `PANIC / HALT` 可直接冻结 T
- `major_event_window_flag` 可直接禁用 T
- 默认每天每票最多 `1` 轮
- 默认每票最大 T 比例 `20%`

## 当前限制
- 还没有真实 lot-age 级别的底仓追踪，所以反 T 只用 `available_shares` 代理。
- 还没有把 T 变成 OMS 下游的 per-symbol 执行接管，它当前先写 formal sidecar 和 bounded overlay recommendation。
