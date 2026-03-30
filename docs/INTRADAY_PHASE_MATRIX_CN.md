# 盘中阶段矩阵

## 1. 正式阶段

| Formal Phase | 上游 source phase | 主要输入 | 允许动作 | 禁止动作 | 主要输出 |
| --- | --- | --- | --- | --- | --- |
| `preopen_prepare` | `preopen_gate` | latest release, OMS actual state, safety truth, account health, market state | 生成当日日内执行计划、初始化 symbol state、判定今日是 build day 还是 reconcile day | 重写 thesis、重写 release target | phase state, action bands |
| `morning_probe` | `simulation` / `shadow` 早段 | release, OMS gap, lifecycle, safety | 小额试探建仓、优先级减仓、受控 risk reduction | 一开盘 aggressive build-all、多轮 replace 风暴 | symbol state first pass |
| `morning_observe` | `simulation` / `shadow` 后段 | order/fill truth, gap shrink, market drift | 观察 ack / partial / stale，准备午间复核摘要 | 用盘中噪音重写研究层判断 | midday review input pack |
| `midday_review` | `midday_review` | 上午真实执行 namespace、OMS continuity、unfinished orders、market/safety truth | 输出有限决议、确定下午是真 build、risk reduce 还是 reconcile-only | 只给自由文本建议、不形成有限决议 | midday decision, midday plan |
| `afternoon_adjust` | `afternoon_execution` / `afternoon_shadow` | midday decision, latest OMS truth, safety | reconcile、第二腿 build、trim、cancel/replace、freeze 部分标的 | 凭空新建大量 thesis 交易、绕开上午真相 | updated symbol/intent states |
| `close_reconcile` | `summary` 之前收尾 | open intents, stale orders, cancel/replace lineage | 收尾、清理 stale、必要取消、对账 | 新开仓、脱离 release 目标做扩张 | close reconcile summary |
| `postclose_archive` | `summary` | 所有当日 sidecar 和控制摘要 | 归档、写 latest sidecar、供次日消费 | 任何主动交易扩张 | archive + latest sidecar |

## 2. 阶段进入与退出

### `preopen_prepare`

- 进入条件：
  - 交易日开始
  - 当日 release 可解析
- 退出条件：
  - 已生成 phase artifact
  - 已形成初始 allowed action bands

### `morning_probe`

- 进入条件：
  - 交易窗口开启
  - safety 未 `HALT`
- 退出条件：
  - 初始建仓/减仓腿完成
  - 已有第一轮 OMS 真相

### `morning_observe`

- 进入条件：
  - 上午第一轮动作已落入 OMS
- 退出条件：
  - 已形成午间摘要
  - 可以给 `midday_review` 提供有限输入

### `midday_review`

- 进入条件：
  - 上午 phase 结束
  - OMS continuity / pending truth 可读
- 退出条件：
  - 午间决议必须落在枚举中：
    - `carry_and_reconcile`
    - `continue_build`
    - `risk_reduce`
    - `abort_new_entries`

### `afternoon_adjust`

- 进入条件：
  - midday plan 已发布
  - 真实 execution namespace 可识别
- 退出条件：
  - 下午腿执行或被正式跳过
  - 已形成新的 control summary

### `close_reconcile`

- 进入条件：
  - 接近收盘或 summary 即将执行
- 退出条件：
  - lingering intents 已进入稳定 terminal / reconcile-only 表达

### `postclose_archive`

- 进入条件：
  - 当日执行结束
- 退出条件：
  - latest sidecar 写完
  - archive 路径写完

## 3. phase × action permission

| Formal Phase | build | pilot | trim | exit | reconcile | cancel/replace | freeze |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `preopen_prepare` | 否 | 否 | 否 | 否 | 否 | 否 | 仅规则判定 |
| `morning_probe` | 受限 | 允许 | 允许 | 允许 | 受限 | 受限 | 允许 |
| `morning_observe` | 一般不新增 | 一般不新增 | 允许 | 允许 | 允许 | 受限 | 允许 |
| `midday_review` | 不直接下单 | 不直接下单 | 不直接下单 | 不直接下单 | 只做决策 | 不直接执行 | 允许决策推进 |
| `afternoon_adjust` | 受决议和 safety 约束 | 一般不新增 | 允许 | 允许 | 允许 | 允许 | 允许 |
| `close_reconcile` | 禁止 | 禁止 | 仅保护性 | 仅保护性 | 允许 | 允许 | 允许 |
| `postclose_archive` | 禁止 | 禁止 | 禁止 | 禁止 | 禁止 | 禁止 | 只保留归档表达 |

## 4. safety 对 phase 的覆盖

| Safety | build/pilot | trim/exit | reconcile | archive |
| --- | --- | --- | --- | --- |
| `NORMAL` | 允许 | 允许 | 允许 | 允许 |
| `CAUTION` | 更严格 | 允许 | 允许 | 允许 |
| `PANIC` | 默认禁止 | 允许 | 允许 | 允许 |
| `HALT` | 禁止 | 仅保护性 | 允许 | 允许 |

## 5. 当前实现注意点

- `trade_clock` 仍然是唯一调度器，phase 不由状态机自行推进。
- `shadow_mode = True` 时，状态机只表达这些阶段和权限，不改 afternoon plan。
- `shadow_mode = False` 时，`afternoon_execution` / `afternoon_shadow` 会读取 overlay recommendation 做有限接管。
