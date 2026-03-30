# Symbol / Intent 状态矩阵

## 1. Symbol execution state

### 1.1 状态定义

| Symbol State | 语义 | 允许动作 | 常见来源 |
| --- | --- | --- | --- |
| `watch` | 今日只观察，不主动建新腿 | 观察、等待 | research lifecycle=`watch`、gap 很小、或 phase 不允许 |
| `pilot_entry` | 小额第一腿试探 | 首腿建仓、轻量补单 | lifecycle=`pilot`，phase 允许，safety 允许 |
| `build_entry` | 第二腿或后续腿加到目标仓位 | add / build / replace | lifecycle=`build`，上午验证通过，gap 仍明显 |
| `hold_manage` | 已有持仓维护态 | 小修正、风险对齐 | lifecycle=`hold` |
| `trim_watch` | 减仓并继续观察 | trim / reduce | lifecycle=`trim`，或 midday 决议转为 risk reduce |
| `exit_execute` | 明确退出 | exit / protection sell | lifecycle=`exit` 或风险触发 |
| `reconcile_only` | 不再主动扩张，只做收尾和对账 | reconcile / cancel / cleanup | close phase、HALT、unfinished orders |
| `freeze` | 异常冻结 | 等待、记录、人工干预、保护性收尾 | safety panic/halt、OMS 异常、严重 stale |

### 1.2 关键转移

| From | Event / Condition | To |
| --- | --- | --- |
| `watch` | phase 允许、release 有目标、safety 正常、lifecycle=`pilot` | `pilot_entry` |
| `pilot_entry` | 首腿落地、fill 质量尚可、gap 仍存在、午间决议=`continue_build` | `build_entry` |
| `pilot_entry` | 首腿完成但不再扩张 | `hold_manage` |
| `pilot_entry` | safety 变差、OMS 异常、stale 严重 | `freeze` |
| `build_entry` | 接近目标或 build 已完成 | `hold_manage` |
| `build_entry` | 午间决议=`risk_reduce` 或 safety 下降 | `trim_watch` |
| `build_entry` | safety=`HALT` 或重大异常 | `freeze` |
| `hold_manage` | risk reduce / trim signal | `trim_watch` |
| `hold_manage` | thesis / release 已转 exit | `exit_execute` |
| `trim_watch` | 退出完成 | `exit_execute` |
| `*` | 收盘、HALT、unfinished orders 仍在 | `reconcile_only` |
| `*` | safety 急剧恶化、账户/OMS 真相异常 | `freeze` |

### 1.3 影响因子

正式影响因子：

- current phase
- safety mode
- market posture
- desired vs actual gap
- account health
- order / fill 结果
- stale / partial / replace-required
- `source_lifecycle_state`
- release target pressure
- midday decision

## 2. Intent state

### 2.1 状态定义

| Intent State | 语义 | 上游 truth 参考 |
| --- | --- | --- |
| `planned` | 已形成意图但还未进入 OMS admission | release / internal planner |
| `admitted` | 已进入 OMS 可派发集合 | intent ledger |
| `submitted` | 已发往 broker | order ledger |
| `acknowledged` | broker 已确认 | order ledger |
| `partial_fill` | 已部分成交 | fill ledger / OMS summary |
| `filled` | 已完全成交 | fill ledger |
| `stale_pending` | 长时间未推进，需要人工或 replace policy 介入 | order age / continuity |
| `replace_required` | 已判定应取消旧单并重建新意图 | cancel_replace_audit / continuity |
| `cancel_requested` | 已提交取消请求，等待 broker 回应 | cancel_replace_audit / order status |
| `cancelled` | 取消完成 | order / broker truth |
| `reconcile_only` | 当前只允许做对账和收尾 | close / HALT / unfinished orders |
| `aborted` | 本次意图正式废弃，不再继续 | override / hard failure |

### 2.2 关键转移

| From | Event / Condition | To |
| --- | --- | --- |
| `planned` | OMS 准入通过 | `admitted` |
| `admitted` | 已派发 | `submitted` |
| `submitted` | broker 确认 | `acknowledged` |
| `acknowledged` | 首笔成交出现 | `partial_fill` |
| `partial_fill` | 完全成交 | `filled` |
| `acknowledged` | 超时未推进 | `stale_pending` |
| `partial_fill` | 长时间残单 | `stale_pending` |
| `stale_pending` | replace policy 满足 | `replace_required` |
| `replace_required` | 已提交取消 | `cancel_requested` |
| `cancel_requested` | broker 确认取消 | `cancelled` |
| `cancelled` | 新 intent 已建立 | `admitted` |
| `*` | close / HALT / manual reconcile | `reconcile_only` |
| `*` | hard failure / manual abort | `aborted` |

## 3. Replace / Cancel 规则

### 3.1 Replace 触发

至少考虑：

- `order_age_minutes >= stale_order_minutes`
- gap 仍显著
- 旧 intent 不是 terminal
- safety 允许保护性操作

### 3.2 Cancel 规则

正式要求：

- `replace_required` 不能 silent replace
- 必须能看到：
  - old intent
  - cancel request
  - cancel result
  - new intent

当前依赖：

- `cancel_replace_audit.json`
- `latest_intent_continuity_report.json`
- order / fill ledgers

### 3.3 Reconcile 规则

进入 `reconcile_only` 后：

- 不再主动扩张
- 只允许：
  - lingering intent cleanup
  - protective cancel
  - continuity closeout
  - archive-facing truth收口

## 4. 当前实现语义

- `source_lifecycle_state` 保留 research/V2A 真相，不被盘中状态机反写。
- `symbol_state` 是盘中层表达，不等价于 research lifecycle。
- `intent_state` 是 OMS-facing formalized view，不替代 OMS ledger。
- `freeze` 是异常保护态，不是普通的“不交易”。
- `reconcile_only` 是收尾态，不是“今天看空”。

## 5. 当前局限

- 第一版没有接管每一条 standalone `execution_only` 分支。
- replace/cancel 已 formalized 成状态表达，但具体 broker 微观执行策略仍然主要由现有 OMS 逻辑决定。
- 当前页面和 sidecar 主要展示 latest，不是完整的跨日状态转移回放器。
