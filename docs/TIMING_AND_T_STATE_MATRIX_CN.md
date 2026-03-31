# Timing / T 状态矩阵

## Timing State

| 状态 | 含义 |
| --- | --- |
| `timing_frozen` | 当前被 safety / 消息 veto / 流动性 / OMS 脏状态冻结 |
| `reconcile_only` | 只允许对账、撤改单、收尾 |
| `observe` | 当前窗口不适合动作，仅观察 |
| `buy_watch` | 买窗已开，但分数还不够 |
| `buy_ready` | 可买 |
| `sell_watch` | 卖窗已开，但分数还不够 |
| `sell_ready` | 可卖 |
| `dual_ready` | 买卖两边都可动作，通常用于复杂盘中调节 |

## T Overlay State

| 状态 | 含义 |
| --- | --- |
| `t_disabled` | 当前不做 T |
| `t_armed` | 当前可做 T，但还没触发第一腿 |
| `t_sell_leg_done_wait_buyback` | 正 T 第一腿已完成，等待下午买回 |
| `t_buy_leg_done_wait_sellback` | 反 T 第一腿已完成，等待下午卖回 |
| `t_completed` | 当日 T 已完成 |
| `t_frozen` | 当日 T 被 safety / close reconcile / 重大事件冻结 |

## 对应网页
- `https://peng1145141919810.xyz/intraday-state.html`

## 对应探针
- `scripts/probe_execution_timing_layer.py`
- `scripts/probe_t_overlay.py`
