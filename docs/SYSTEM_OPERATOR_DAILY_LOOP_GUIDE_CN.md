# 系统日常操作指南

## 1. 先说结论

你现在这套系统的“每天循环”已经可以拆成一条明确的闭环：

1. 低成本数据刷新
2. 研究
3. release 冻结
4. preopen gate
5. 上午执行
6. 午间复核
7. 下午调整
8. summary 打包
9. 审计 HTML/JSON 生成
10. 网站自动发布
11. intraday state sidecar 归档

真正的调度器仍然是：

- `trade_clock_service.py`

正式入口仍然是：

- `launch_canonical.py`

## 2. 当前系统架构

### 2.1 核心分层

- 数据层
  - `affordable_data_v1.sqlite3`
  - `trade_release_v1`
  - `live_execution_bridge/oms_v1`
  - `trade_clock`
- 研究层
  - `industry_router`
  - `market_state`
  - `three_strategy_kernel`
  - `context_pack`
  - `research_brief`
- 组合层
  - `portfolio_recommendation`
  - `portfolio_release`
- 执行层
  - `execution_manager`
  - `OMS`
  - `gmtrade bridge`
- 调度层
  - `clock_supervisor`
  - `trade_clock_service.py`
- 审计与门户层
  - `strategy_audit`
  - `build_audit_site_index.py`
  - `publish_audit_report_to_site.ps1`
  - 站点 `peng1145141919810.xyz`
- 盘中状态机层
  - `hub_v6/intraday_state_machine/*`

### 2.2 关键原则

- 不默认跑 full integrated pipeline。
- 正式日常循环优先让 trade clock 跑。
- OMS 是 actual truth owner。
- safety 是上位 kill-switch。
- intraday state machine 先看作 formalized sidecar/control layer，不是独立交易引擎。

## 3. 关键入口

### 3.1 Python

- 正式入口
  - `F:\quant_data\AshareC#\launch_canonical.py`
- 业务根
  - `F:\quant_data\AshareC#\main_research_runner.py`
- 调度服务
  - `F:\quant_data\AshareC#\trade_clock_service.py`

### 3.2 PowerShell

- 启动调度
  - `F:\quant_data\AshareC#\scripts\start_trade_clock.ps1`
- 停止调度
  - `F:\quant_data\AshareC#\scripts\stop_trade_clock.ps1`
- 查看调度状态
  - `F:\quant_data\AshareC#\scripts\show_trade_clock_status.ps1`
- 手工发布网站
  - `F:\quant_data\AshareC#\scripts\publish_audit_report_to_site.ps1`

### 3.3 网站

- 首页
  - `https://peng1145141919810.xyz/`
- 系统状态
  - `https://peng1145141919810.xyz/system-status.html`
- 策略状态
  - `https://peng1145141919810.xyz/strategy-status.html`
- 交易观察
  - `https://peng1145141919810.xyz/trade-monitor.html`
- 盘中状态机
  - `https://peng1145141919810.xyz/intraday-state.html`
- 审计中心
  - `https://peng1145141919810.xyz/audit-center.html`

## 4. 关键产物

### 4.1 trade clock

- `data\trade_clock\clock_state.json`
- `data\trade_clock\phase_state\YYYYMMDD.json`
- `data\trade_clock\system_safety_state.json`
- `data\trade_clock\incident_log.jsonl`

### 4.2 release / OMS

- `data\trade_release_v1\latest_release.json`
- `data\trade_release_v1\releases\<release_id>\release_manifest.json`
- `data\live_execution_bridge\oms_v1\snapshots\latest_actual_portfolio_state.json`
- `data\live_execution_bridge\oms_v1\snapshots\desired_vs_actual_gap.csv`
- `data\live_execution_bridge\oms_v1\snapshots\oms_summary.json`
- `data\live_execution_bridge\oms_v1\ledgers\intent_ledger_latest.csv`
- `data\live_execution_bridge\oms_v1\ledgers\order_ledger_latest.csv`
- `data\live_execution_bridge\oms_v1\ledgers\fill_ledger_latest.csv`

### 4.3 intraday state machine

- `data\trade_clock\intraday_state\latest\intraday_phase_state.json`
- `data\trade_clock\intraday_state\latest\symbol_execution_state.csv`
- `data\trade_clock\intraday_state\latest\intent_state_daily.csv`
- `data\trade_clock\intraday_state\latest\intraday_event_log.jsonl`
- `data\trade_clock\intraday_state\latest\intraday_control_summary.json`

### 4.4 summary / audit / publish

- `outputs\automation_runs\<trade_date>\strategy_audit.json`
- `outputs\automation_runs\<trade_date>\strategy_audit.html`
- `outputs\automation_runs\<trade_date>\run_manifest.json`
- `outputs\automation_runs\<trade_date>\intraday_phase_state.json`
- `outputs\automation_runs\<trade_date>\intraday_control_summary.json`

## 5. 每天的标准循环

## 5.1 开盘前

检查这些：

1. `trade_clock_service.py` 是否在跑
2. `clock_state.json` 是否持续更新
3. `system_safety_state.json` 是否不是无意义 stale
4. `latest_release.json` 是否存在且 trade date 正确
5. OMS 快照是否存在
6. 网站是否还能打开

最小检查命令：

```powershell
powershell -ExecutionPolicy Bypass -File F:\quant_data\AshareC#\scripts\show_trade_clock_status.ps1
```

## 5.2 调度自动相位

当前自动主链通常是：

1. `research`
2. `release`
3. `research_refresh`
4. `release_refresh`
5. `preopen_gate`
6. `simulation`
7. `midday_review`
8. `afternoon_execution`
9. `summary`

### 当前默认日程

1. `15:05` 跑次日 `research`
2. `15:10` 跑次日 `release`
3. `08:35` 跑当日 `research_refresh`
4. `08:55` 跑当日 `release_refresh`
5. `09:20` 跑 `preopen_gate`
6. `09:30:35` 跑 `simulation`
7. `11:35` 跑 `midday_review`
8. `13:05` 跑 `afternoon_execution`
9. `15:20` 跑 `summary`

### 这条链里现在已经自动做的额外动作

- `research` 前：
  - affordable data bundle 先刷新
- `preopen_gate` / `simulation` / `midday_review` / `afternoon_execution` / `summary` 前：
  - `daily_price_snapshot.csv` 尝试用 `Tushare realtime_quote` 刷新
  - 快照会诚实写入 `snapshot_source` 和 `snapshot_quality`
- 每个关键 phase 完成后：
  - intraday state machine 刷新 latest sidecar
- `summary` 内：
  - strategy audit pack 生成
  - intraday artifacts 复制进 daily pack
  - 审计站点自动发布到服务器

## 5.3 盘中怎么盯

你平时真正盯的不是一堆代码，而是这些产物：

### 系统级

- `clock_state.json`
- `system_safety_state.json`
- `incident_log.jsonl`

### 执行级

- `oms_summary.json`
- `desired_vs_actual_gap.csv`
- `latest_actual_portfolio_state.json`

### 状态机级

- `intraday_phase_state.json`
- `intraday_control_summary.json`
- `symbol_execution_state.csv`
- `intent_state_daily.csv`

### 门户级

- `system-status.html`
- `trade-monitor.html`
- `intraday-state.html`
- `audit-center.html`

## 6. shadow mode 与 bounded takeover

### 6.1 推荐默认值

日常默认建议：

- `ENABLE_INTRADAY_STATE_MACHINE = True`
- `INTRADAY_STATE_MACHINE_SHADOW_MODE = True`
- `INTRADAY_STATE_MACHINE_ENABLE_AFTERNOON_OVERLAY = True`

但注意：

- 当 `shadow_mode = True` 时，下午 overlay 不会接管 afternoon plan
- 当 `shadow_mode = False` 时，状态机会对下午腿做有限动作约束

### 6.2 什么时候切到 bounded takeover

满足这些再考虑：

1. 连续多个交易日 sidecar 表达合理
2. 午间决议和实际 intuition 基本一致
3. `freeze` / `reconcile_only` 没有明显误伤
4. stale / replace / cancel 映射不离谱

## 7. 日常启动、停止、恢复

### 7.1 启动

```powershell
powershell -ExecutionPolicy Bypass -File F:\quant_data\AshareC#\scripts\start_trade_clock.ps1 -Profile daily_production
```

### 7.2 停止

```powershell
powershell -ExecutionPolicy Bypass -File F:\quant_data\AshareC#\scripts\stop_trade_clock.ps1
```

### 7.3 查看状态

```powershell
powershell -ExecutionPolicy Bypass -File F:\quant_data\AshareC#\scripts\show_trade_clock_status.ps1
```

## 8. 轻量验证命令

### 8.1 语法编译

```powershell
python -m py_compile `
  F:\quant_data\AshareC#\scripts\probe_intraday_state_machine.py `
  F:\quant_data\AshareC#\scripts\build_audit_site_index.py `
  F:\quant_data\AshareC#\quant_research_hub_v6_repacked_clean\quant_research_hub_v6_repacked_clean\hub_v6\intraday_state_machine\runtime.py `
  F:\quant_data\AshareC#\quant_research_hub_v6_repacked_clean\quant_research_hub_v6_repacked_clean\hub_v6\clock_supervisor.py `
  F:\quant_data\AshareC#\quant_research_hub_v6_repacked_clean\quant_research_hub_v6_repacked_clean\hub_v6\config_builder.py
```

### 8.2 状态机探针

```powershell
python F:\quant_data\AshareC#\scripts\probe_intraday_state_machine.py --source-phase summary
```

### 8.3 C# 包装层编译

```powershell
dotnet build F:\quant_data\AshareC#\csharp_runtime_skeleton\Ashare.RuntimeSkeleton.sln
```

## 9. 常见故障处理

### 9.1 网站没更新

先查：

1. `summary` 是否成功
2. `audit_site_publish` 是否在 summary manifest 里成功
3. SSH 免密是否还有效
4. 服务器磁盘和 nginx 是否正常

手工重发：

```powershell
powershell -ExecutionPolicy Bypass -File F:\quant_data\AshareC#\scripts\publish_audit_report_to_site.ps1
```

### 9.2 盘中状态机没刷新

先查：

1. `ENABLE_INTRADAY_STATE_MACHINE`
2. `INTRADAY_STATE_MACHINE_REFRESH_PHASES`
3. `phase_state\YYYYMMDD.json`
4. OMS 和 safety 侧快照是否存在

手工探针：

```powershell
python F:\quant_data\AshareC#\scripts\probe_intraday_state_machine.py --source-phase midday_review
```

### 9.3 safety 进入 HALT

先看：

- `data\trade_clock\system_safety_state.json`
- `data\trade_clock\incident_log.jsonl`
- `data\trade_clock\intraday_state\latest\intraday_control_summary.json`

不要先去改状态机。先确认：

- release 是否 stale
- account/OMS truth 是否 stale
- unfinished orders 是否堆积
- 是否人为 manual halt

### 9.4 OMS 路径看起来不对

当前 C# PathRegistry 已暴露：

- `intraday_phase_state_path`
- `intraday_symbol_state_path`
- `intraday_intent_state_path`
- `intraday_event_log_path`
- `intraday_control_summary_path`

并且 OMS ledger 路径应包含：

- `...\oms_v1\ledgers\intent_ledger_latest.csv`
- `...\oms_v1\ledgers\order_ledger_latest.csv`
- `...\oms_v1\ledgers\fill_ledger_latest.csv`

## 10. 配置面

### 10.1 intraday state machine

- `ENABLE_INTRADAY_STATE_MACHINE`
- `INTRADAY_STATE_MACHINE_SHADOW_MODE`
- `INTRADAY_STATE_MACHINE_FAIL_OPEN`
- `INTRADAY_STATE_MACHINE_ENABLE_AFTERNOON_OVERLAY`
- `INTRADAY_STATE_MACHINE_STALE_ORDER_MINUTES`
- `INTRADAY_STATE_MACHINE_REFRESH_PHASES`
- `INTRADAY_STATE_MACHINE_ROOT`

### 10.2 网站发布

- `ENABLE_AUDIT_SITE_PUBLISH`
- `AUDIT_SITE_PUBLISH_RUN_AFTER_SUMMARY`
- `AUDIT_SITE_PUBLISH_FAIL_OPEN`
- `AUDIT_SITE_PUBLISH_SCRIPT_PATH`
- `AUDIT_SITE_PUBLISH_POWERSHELL`
- `AUDIT_SITE_PUBLISH_REMOTE_USER`
- `AUDIT_SITE_PUBLISH_REMOTE_HOST`
- `AUDIT_SITE_PUBLISH_REMOTE_ROOT`
- `AUDIT_SITE_PUBLISH_DOMAIN`
- `AUDIT_SITE_PUBLISH_TIMEOUT_MINUTES`

## 11. 云端与 Google Drive

### 11.1 站点服务器

- 域名
  - `peng1145141919810.xyz`
- 服务器
  - 腾讯云 Lighthouse 香港
- Web 根目录
  - `/var/www/peng1145141919810.xyz/site`

### 11.2 Google Drive

当前默认根目录：

- `H:\我的云端硬盘\AshareCSharp_backups`

常用动作：

- dev log 同步
- script snapshot
- runtime skeleton export

## 12. 最后的操作纪律

1. 不默认跑 full integrated pipeline。
2. 任何重要改动先看 `CODEX_DEV_LOG.md`。
3. 先看产物，再怀疑代码。
4. 先看 safety / OMS / release / phase truth，再讨论盘中智能。
5. 盘中状态机默认先 shadow，确认稳定后再 bounded takeover。
6. 任何行为变化必须回写开发日志稳定区。
