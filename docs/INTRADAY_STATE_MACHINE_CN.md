# 盘中行为状态机说明

## 1. 设计目标

这套状态机的目标不是让系统“更聪明”，而是让盘中行为变得：

- 有明确阶段
- 有明确状态
- 有明确转移条件
- 有明确 sidecar 产物
- 有明确安全边界
- 有明确人工干预边界
- 可回放
- 可复盘
- 可被门户直接展示

第一版追求的是完整、有限、确定、可审计，不追求复杂的盘中预测。

## 2. 当前权责边界

盘中状态机只负责：

- 交易日阶段表达
- 单标的执行状态表达
- OMS 意图状态映射
- safety 到盘中动作带宽的映射
- 事件与 sidecar 归档

盘中状态机不负责：

- 重写 thesis
- 重写 release target
- 绕过 safety 或 OMS 真相
- 直接创造新的研究层 alpha

当前系统里的权责仍然是：

- research / V2A 负责 `source_lifecycle_state`
- release 负责目标书冻结
- safety 负责系统级许可
- OMS 负责 actual state / intent / order / fill truth
- intraday state machine 负责把这些真相收束成 formal phase / symbol state / intent state / event model

## 3. 四层状态机

### 3.1 第一层：交易日阶段状态机

正式阶段：

1. `preopen_prepare`
2. `morning_probe`
3. `morning_observe`
4. `midday_review`
5. `afternoon_adjust`
6. `close_reconcile`
7. `postclose_archive`

当前系统与 trade clock 的映射关系：

- `preopen_gate` -> `preopen_prepare`
- `simulation` / `shadow` -> `morning_probe` 或 `morning_observe`
- `midday_review` -> `midday_review`
- `afternoon_execution` / `afternoon_shadow` -> `afternoon_adjust`
- `summary` -> `postclose_archive`

这层的输出是：

- `intraday_phase_state.json`
- `intraday_control_summary.json`
- `intraday_event_log.jsonl`

### 3.2 第二层：单标的执行状态机

正式状态：

1. `watch`
2. `pilot_entry`
3. `build_entry`
4. `hold_manage`
5. `trim_watch`
6. `exit_execute`
7. `reconcile_only`
8. `freeze`

上游输入：

- `source_lifecycle_state`
- target weight / actual weight / gap
- last intent state / last order state
- phase
- safety mode
- midday decision

输出：

- `symbol_execution_state.csv`

### 3.3 第三层：Intent / Order 状态机

正式状态：

1. `planned`
2. `admitted`
3. `submitted`
4. `acknowledged`
5. `partial_fill`
6. `filled`
7. `stale_pending`
8. `replace_required`
9. `cancel_requested`
10. `cancelled`
11. `reconcile_only`
12. `aborted`

当前实现优先复用 OMS 已有产物与状态：

- `latest_open_intents.json`
- `latest_intent_continuity_report.json`
- `session_resume_audit.json`
- `cancel_replace_audit.json`
- `latest_manual_intervention_state.json`
- `desired_vs_actual_gap.csv`
- `oms_summary.json`
- ledgers: intent / order / fill

输出：

- `intent_state_daily.csv`

### 3.4 第四层：安全状态映射层

正式安全模式：

- `NORMAL`
- `CAUTION`
- `PANIC`
- `HALT`

映射规则：

- `NORMAL`：允许 `pilot_entry`、`build_entry`、`trim_watch`、`reconcile_only`
- `CAUTION`：保留 `pilot_entry`，但更偏向 `hold_manage` / `trim_watch`
- `PANIC`：默认禁止主动 build，只保留 `trim_watch` / `reconcile_only`
- `HALT`：只允许对账、收尾、保护性取消、归档

当前安全真相仍然只认：

- `system_safety_state.json`
- `incident_log.jsonl`
- trade-clock manual overrides
- OMS-local overrides

盘中状态机不能绕过这些上位规则。

## 4. 当前实现结构

模块目录：

- `hub_v6/intraday_state_machine/phase_state.py`
- `hub_v6/intraday_state_machine/symbol_state.py`
- `hub_v6/intraday_state_machine/intent_state.py`
- `hub_v6/intraday_state_machine/event_model.py`
- `hub_v6/intraday_state_machine/transition_rules.py`
- `hub_v6/intraday_state_machine/safety_mapping.py`
- `hub_v6/intraday_state_machine/artifact_writer.py`
- `hub_v6/intraday_state_machine/runtime.py`

自动进程接线：

- `hub_v6/clock_supervisor.py`

探针脚本：

- `scripts/probe_intraday_state_machine.py`

门户展示：

- `scripts/build_audit_site_index.py`
- 站点页面 `intraday-state.html`

## 5. 当前 sidecar 产物

根目录：

- `F:\quant_data\AshareC#\data\trade_clock\intraday_state\latest`

当前正式产物：

- `intraday_phase_state.json`
- `symbol_execution_state.csv`
- `intent_state_daily.csv`
- `intraday_event_log.jsonl`
- `intraday_control_summary.json`
- `intraday_state_manifest.json`

归档目录：

- `F:\quant_data\AshareC#\data\trade_clock\intraday_state\<YYYYMMDD>\...`

## 6. 与现有模块的集成

### 6.1 与 trade clock 的关系

trade clock 仍然是唯一调度器。

状态机不再开第二套调度器，而是：

- 由 trade clock phase 驱动刷新
- 在 `summary` 前后写入 intraday sidecar
- 在 `afternoon_execution` / `afternoon_shadow` 读取 control summary 做有限 overlay

### 6.2 与 midday review 的关系

`midday_review` 的 formal 输出仍然是 midday plan artifact。

状态机当前做两件事：

- 读取 midday plan
- 把它收束为有限决议：
  - `carry_and_reconcile`
  - `continue_build`
  - `risk_reduce`
  - `abort_new_entries`

### 6.3 与 execution 的关系

第一版没有让状态机完全接管 execution branch。

当前只做有限接管：

- 在 `shadow_mode = True` 时：
  - 只写 sidecar
  - 不改 afternoon execution plan
- 在 `shadow_mode = False` 时：
  - 允许 `clock_supervisor` 读取 `intraday_control_summary.json`
  - 对下午腿做有限 overlay：
    - `allow_unfinished_orders_reconcile`
    - `block_new_entries`
    - `force_reconcile_only`
    - `abort_new_entries` 时可直接不跑新开仓腿

### 6.4 与 OMS 的关系

状态机不创造第二套订单真相。

OMS 仍然是：

- actual state truth owner
- intent / order / fill truth owner
- continuity / cancel-replace truth owner

状态机只是把这些 truth 映射成：

- formal intent state
- formal symbol state
- event model

## 7. 当前 integration mode

当前存在两种 integration mode：

- `shadow`
- `bounded_takeover`

它们由配置项控制：

- `ENABLE_INTRADAY_STATE_MACHINE`
- `INTRADAY_STATE_MACHINE_SHADOW_MODE`
- `INTRADAY_STATE_MACHINE_ENABLE_AFTERNOON_OVERLAY`

含义：

- `shadow`：
  - 只写 sidecar
  - 不影响下午执行计划
- `bounded_takeover`：
  - sidecar 继续写
  - 允许 afternoon overlay 改 afternoon execution 的动作带宽

## 8. 当前已实现范围

已完成：

- 四层状态机骨架
- phase / symbol / intent / event / safety mapping
- shadow probe
- trade clock 自动刷新
- summary pack 纳入 intraday sidecar
- 门户 `intraday-state.html` 展示
- C# 包装路径暴露

已有限接管：

- `afternoon_execution`
- `afternoon_shadow`

当前未完全接管：

- standalone `execution_only` 入口
- standalone `midday_review_only` 入口的动作约束
- 更细的 replace/cancel 策略执行细节
- 回放型多日状态机浏览

## 9. 当前局限

- 第一版重点是状态表达与可审计，不是盘中 alpha。
- `shadow_mode` 默认应保持 `True`，只有在你明确接受有限接管时才切到 `False`。
- 状态机依赖已有 release / OMS / safety / trade_clock 产物；这些上游本身如果不新鲜，状态机会准确地“反映旧真相”，但不会自己补真相。
- 门户页面当前展示的是 latest sidecar，不是完整交互式回放器。

## 10. 日常建议

- 平时先跑 `shadow`，观察 3 到 5 个交易日。
- 确认午间决议、symbol state 分布、intent state 映射没有明显反直觉后，再考虑把 `shadow_mode` 切到 `False`。
- 如果系统处于 `HALT` / `PANIC`，先看 `intraday_control_summary.json` 和 `system_safety_state.json`，不要先怀疑状态机本身。
