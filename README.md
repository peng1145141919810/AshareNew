# Ashare Quant Research System

当前 `F:\quant_data\AshareC#` 是给 Rider / C# 迁移准备的代码工作区副本，不是已经切换完成的 live 运行根。
当前 live Python 系统仍以原始 `F:\quant_data\Ashare` 为主。
当前仓库已经带有一份本地 `data/` 镜像和自动化产物镜像，但仍不是完全独立副本，因为它还依赖本机私有 `hub_v6/local_settings.py`，且 Gmtrade 仍使用老库下的 `gmtrade39` 环境。

当前 GitHub 仓库只承载可运行代码和治理文档，不包含大体量训练表、运行产物、密钥、本机配置。

## 当前工作区镜像入口

- 正式操作入口: `launch_canonical.py`
- 被包装的业务根入口: `main_research_runner.py`
- 默认模式: `integrated_supervisor`
- 默认 profile: `quick_test`
- 精准撮合建议工作流:
  - `research_only` -> 发布 `portfolio release`
  - `trade_clock_service.py` -> 常驻读时间并触发 `execution_only`

不要把旧文档里提到的历史入口当成现行真相。当前工作区法统以 `CODEX_DEV_LOG.md` 为准。
如果你问的是当前 live 生产链，请先确认是不是仍在指原始 `F:\quant_data\Ashare`。

## 仓库里有什么

- 当前 live runtime 代码
- V6 + 内嵌 V5.1 研究链
- 执行桥接代码
- 治理层文件:
  - `PROJECT_LAW.md`
  - `SYSTEM_MANIFEST.yaml`
  - `RUN_PROFILES.yaml`
  - `CHANGELOG_CANONICAL.md`
  - `CODEX_DEV_LOG.md`

## 仓库里没有什么

- 训练表文件
- 运行输出
- API token
- 本机 `local_settings.py`

这些内容需要按实际环境单独补齐。
当前默认现实情况是: `AshareC#` 已有本地 `data/` 镜像，但训练表、桥接运行环境和私有本机配置仍可能依赖 `F:\quant_data\Ashare`。

## 协作者最小上手步骤

1. 克隆仓库。
2. 准备两套 Python 环境:
   - 研究主环境
   - `gmtrade39` 专用环境
3. 从 `quant_research_hub_v6_repacked_clean/quant_research_hub_v6_repacked_clean/hub_v6/local_settings.example.py` 复制出本机 `local_settings.py`。
4. 在 `local_settings.py` 里至少填写:
   - `PYTHON_EXECUTABLE`
   - `GMTRADE_PYTHON_EXECUTABLE`
   - `TUSHARE_TOKEN`
   - 需要时再填 OpenAI / DeepSeek 等密钥
5. 当前若只是做 Rider / C# 迁移分析，可把原始 `F:\quant_data\Ashare` 视为只读外部依赖。
6. 若要让 `AshareC#` 独立运行，再补齐本机 `local_settings.py`、训练表和相关运行依赖。
7. 先跑轻量预检:

```powershell
python launch_canonical.py --preflight-only --profile quick_test --mode integrated_supervisor
```

8. 预检通过后，再跑正式入口:

```powershell
python launch_canonical.py --profile quick_test
```

更完整的当前混合架构使用方式见：

- `SYSTEM_DAILY_USAGE_GUIDE_CN.txt`

## 精准撮合分层

- 研究层:
  - `python launch_canonical.py --profile quick_test --mode research_only`
- 发布层:
  - `python launch_canonical.py --profile quick_test --mode release_only`
- 执行层:
  - `python launch_canonical.py --profile quick_test --mode execution_only --gate-only`
- 执行账户模式切换:
  - 模拟调试: `python launch_canonical.py --profile quick_test --mode execution_only --gate-only --execution-mode simulation`
  - 精准撮合巡检: `python launch_canonical.py --profile quick_test --mode execution_only --gate-only --execution-mode precision --precision-trade off`
  - 精准撮合允许交易: `python launch_canonical.py --profile quick_test --mode execution_only --execution-mode precision --precision-trade on`
- 时钟服务:
  - `python trade_clock_service.py --profile quick_test --once`
  - 开机自启动安装脚本: `scripts/install_trade_clock_autostart.ps1`
  - 当前默认建议: `precision + trade off`

## 运行和排查

- 运行总状态:
  - `data/event_lake_v6/research/supervisor/supervisor_state.json`
- 正式包装层追溯:
  - `outputs/canonical_runs/<run_id>/run_manifest.json`
- 正式输出法统:
  - `outputs/canonical_runs` 是 formal trace root
  - 其余 `outputs/` 默认不视为正式法统输出

## 给协作者的注意事项

- 本仓库已经把历史根目录 `quant_research_hub_v5*` 退役，现行 V5.1 在内嵌目录里。
- `.githooks/` 和 `scripts/` 里有一部分是维护者本地运维脚本，不是运行主链必需项。
- 不要把 `quick_test` 当成秒级 smoke test，它仍然会走真实集成链路。
- `csharp_runtime_skeleton` 当前是治理 / 编排骨架，不是正式运行时替代品。
