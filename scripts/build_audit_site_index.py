# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import csv
import html
import json
from pathlib import Path
from typing import Any


def j(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def csv_rows(path: Path, limit: int = 20) -> list[dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            rows = []
            for i, row in enumerate(csv.DictReader(f)):
                rows.append({str(k): str(v or "") for k, v in row.items()})
                if i + 1 >= limit:
                    break
            return rows
    except Exception:
        return []


def jsonl_tail(path: Path, limit: int = 8) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines()[-limit:]:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            out.append({"raw": line})
    return out


def t(v: Any, d: str = "-") -> str:
    s = str(v or "").strip()
    return s or d


def n(v: Any, d: int = 3) -> str:
    try:
        return f"{float(v):,.{d}f}"
    except Exception:
        return "-"


def p(v: Any, d: int = 2) -> str:
    try:
        return f"{float(v):.{d}%}"
    except Exception:
        return "-"


def tone(v: Any) -> str:
    s = str(v or "").lower()
    if s in {"ok", "success", "published", "normal", "active", "allow", "balanced"}:
        return "good"
    if s in {"warning", "warn", "warming_up", "thin", "neutral", "selective"}:
        return "warn"
    if s in {"panic", "halt", "failed", "error", "risk_off", "blocked"}:
        return "bad"
    return "neutral"


def badge(text: str) -> str:
    return f"<span class='badge badge-{tone(text)}'>{html.escape(text)}</span>"


def table(headers: list[str], rows: list[list[str]]) -> str:
    th = "".join(f"<th>{html.escape(x)}</th>" for x in headers)
    if not rows:
        body = f"<tr><td colspan='{len(headers)}' class='empty'>当前没有可展示的数据。</td></tr>"
    else:
        body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<div class='table-wrap'><table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>"


def kv(rows: list[tuple[str, Any]]) -> str:
    return "<div class='kv'>" + "".join(
        f"<div class='k'>{html.escape(k)}</div><div class='v'>{html.escape(t(v))}</div>" for k, v in rows
    ) + "</div>"


def bars(items: list[tuple[str, Any]]) -> str:
    rows = []
    for label, value in items:
        try:
            width = max(0.0, min(100.0, float(value) * 100.0))
        except Exception:
            width = 0.0
        rows.append(
            f"<div class='bar-row'><div class='bar-label'>{html.escape(str(label))}</div>"
            f"<div class='bar-track'><div class='bar-fill' style='width:{width:.1f}%'></div></div>"
            f"<div class='bar-value'>{p(value)}</div></div>"
        )
    return "<div class='bar-chart'>" + "".join(rows) + "</div>"


def timeline(items: list[tuple[str, str, str]]) -> str:
    if not items:
        return "<div class='empty'>当前没有可展示的时间轴事件。</div>"
    return "<div class='timeline'>" + "".join(
        f"<div class='timeline-item'><div class='timeline-time'>{html.escape(a)}</div>"
        f"<div class='timeline-dot'></div><div class='timeline-body'><strong>{html.escape(b)}</strong><div class='muted'>{html.escape(c)}</div></div></div>"
        for a, b, c in items
    ) + "</div>"


def shell(title: str, domain: str, active: str, body: str) -> str:
    navs = [
        ("首页", "index.html", "index"),
        ("系统状态", "system-status.html", "system"),
        ("策略状态", "strategy-status.html", "strategy"),
        ("交易观察", "trade-monitor.html", "trade"),
        ("盘中状态机", "intraday-state.html", "intraday"),
        ("审计中心", "audit-center.html", "audit"),
        ("评论区", "comments.html", "comments"),
        ("管理后台", "admin.html", "admin"),
        ("登录", "login.html", "login"),
        ("注册", "register.html", "register"),
        ("关于系统", "about.html", "about"),
    ]
    nav = "".join(
        f"<a class='nav-link {'active' if k == active else ''}' href='./{h}'>{l}</a>" for l, h, k in navs
    )
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(title)} | 量化系统门户</title><style>
    :root{{--bg:#efe7db;--bg2:#e5dac8;--panel:rgba(255,250,242,.93);--text:#1c272d;--muted:#5f6b72;--border:rgba(82,67,45,.14);--shadow:0 18px 48px rgba(34,40,45,.08);--good:#2d7c63;--warn:#9d6d10;--bad:#a73d36;--neutral:#55636c;}}
    *{{box-sizing:border-box}}body{{margin:0;font-family:"Segoe UI","Microsoft YaHei",sans-serif;color:var(--text);background:radial-gradient(circle at 10% 10%,rgba(255,255,255,.55),transparent 22%),linear-gradient(180deg,var(--bg),var(--bg2));}}a{{color:#0f5cc0;text-decoration:none}}.wrap{{max-width:1280px;margin:0 auto;padding:24px 18px 56px}}
    .hero{{padding:28px;border-radius:32px;background:linear-gradient(135deg,rgba(255,250,242,.98),rgba(225,239,231,.9));border:1px solid rgba(84,95,74,.18);box-shadow:var(--shadow)}}.eyebrow{{color:var(--muted);font-size:13px}}h1{{margin:10px 0;font-size:40px}}.hero p{{margin:0;max-width:860px;color:var(--muted);line-height:1.7}}
    .nav{{display:flex;flex-wrap:wrap;gap:10px;margin-top:22px}}.nav-link{{padding:10px 16px;border-radius:999px;background:rgba(255,255,255,.72);color:var(--text);border:1px solid rgba(28,39,45,.1);font-size:14px}}.nav-link.active{{background:#1d2b31;color:#fff;border-color:transparent}}
    .section-title{{display:flex;justify-content:space-between;align-items:baseline;gap:16px;margin:28px 4px 14px;flex-wrap:wrap}}.section-title h2{{margin:0;font-size:24px}}.section-title .sub,.muted,.footer,.empty{{color:var(--muted);font-size:13px;line-height:1.7}}
    .grid{{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:18px}}.card{{grid-column:span 4;border-radius:24px;background:var(--panel);border:1px solid var(--border);box-shadow:var(--shadow);padding:20px}}.wide{{grid-column:span 8}}.full{{grid-column:1/-1}}.label{{color:var(--muted);font-size:13px}}.metric{{font-size:30px;font-weight:700;margin:10px 0 8px}}
    .badge{{display:inline-block;margin:0 8px 8px 0;padding:4px 10px;border-radius:999px;font-size:12px;font-weight:700}}.badge-good{{background:rgba(45,124,99,.12);color:var(--good)}}.badge-warn{{background:rgba(157,109,16,.12);color:var(--warn)}}.badge-bad{{background:rgba(167,61,54,.12);color:var(--bad)}}.badge-neutral{{background:rgba(85,99,108,.1);color:var(--neutral)}}
    .kv{{display:grid;grid-template-columns:140px 1fr;gap:8px 12px;margin-top:10px;font-size:14px}}.k{{color:var(--muted)}}.table-wrap{{overflow-x:auto;margin-top:10px}}table{{width:100%;border-collapse:collapse;font-size:14px}}th,td{{text-align:left;padding:10px 8px;border-bottom:1px solid rgba(28,39,45,.08);vertical-align:top}}th{{color:var(--muted);font-weight:700;white-space:nowrap}}
    .list{{margin:12px 0 0;padding-left:18px;line-height:1.7}}.form-grid{{display:grid;gap:12px;margin-top:12px}}.form-grid label{{display:grid;gap:6px;font-size:14px;color:var(--muted)}}.form-grid input,.form-grid textarea{{padding:12px 14px;border-radius:14px;border:1px solid rgba(28,39,45,.12);background:rgba(255,255,255,.9);font:inherit;color:var(--text)}}.form-grid textarea{{min-height:120px;resize:vertical}}.button-row{{display:flex;gap:12px;flex-wrap:wrap;margin-top:12px}}.btn{{display:inline-flex;align-items:center;justify-content:center;padding:11px 18px;border-radius:999px;background:#1d2b31;color:#fff;font-weight:700;cursor:pointer}}.btn.alt{{background:rgba(255,255,255,.65);color:var(--text);border:1px solid rgba(28,39,45,.1)}}.callout{{margin-top:14px;padding:14px 16px;border-radius:18px;background:rgba(189,100,38,.08);border:1px solid rgba(189,100,38,.14);color:#6e461e;line-height:1.7}}.bar-chart{{display:grid;gap:10px;margin-top:12px}}.bar-row{{display:grid;grid-template-columns:160px 1fr 72px;gap:10px;align-items:center}}.bar-label,.bar-value{{font-size:13px;color:var(--muted)}}.bar-track{{height:10px;background:rgba(28,39,45,.08);border-radius:999px;overflow:hidden}}.bar-fill{{height:100%;background:linear-gradient(90deg,#0f5cc0,#bd6426)}}.timeline{{display:grid;gap:12px;margin-top:12px}}.timeline-item{{display:grid;grid-template-columns:130px 18px 1fr;gap:12px;align-items:start}}.timeline-time{{font-size:12px;color:var(--muted)}}.timeline-dot{{width:12px;height:12px;border-radius:999px;background:#0f5cc0;box-shadow:0 0 0 4px rgba(15,92,192,.12);margin-top:4px}}.comment-card{{border:1px solid rgba(28,39,45,.08);border-radius:18px;padding:14px;background:rgba(255,255,255,.55);margin-top:12px}}.toolbar{{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}}.toast{{margin-top:12px;padding:12px 14px;border-radius:14px;background:rgba(15,92,192,.08);color:#18406f;display:none}}
    @media (max-width:980px){{.card,.wide{{grid-column:1/-1}}h1{{font-size:34px}}.kv{{grid-template-columns:1fr}}}}
    </style></head><body><div class='wrap'><section class='hero'><div class='eyebrow'>量化系统门户 · {html.escape(domain)}</div><h1>{html.escape(title)}</h1><p>当前门户从已有运行产物中读取系统状态、策略状态、交易观察和审计报告，先把可观察和可解释做扎实，再逐步补充交互层和账号层。</p><div style='margin-top:16px'>{badge("中文门户")}{badge("静态发布")}{badge("真实产物驱动")}{badge("高风险交易默认关闭")}</div><nav class='nav'>{nav}</nav></section>{body}<div class='footer' style='margin-top:30px'>页面由 <code>scripts/build_audit_site_index.py</code> 自动生成并通过 SSH 发布到云端。</div></div></body></html>"""


def report_rows(reports_root: Path) -> list[dict[str, Any]]:
    out = []
    if not reports_root.exists():
        return out
    for d in sorted(reports_root.iterdir(), key=lambda p: p.name, reverse=True):
        if not d.is_dir() or not (d / "strategy_audit.html").exists():
            continue
        payload = j(d / "strategy_audit.json")
        out.append({
            "slug": d.name,
            "trade_date": t(payload.get("trade_date"), d.name),
            "generated_at": t(payload.get("generated_at")),
            "primary_strategy": t((payload.get("strategy_exposure") or {}).get("primary_strategy_key")),
            "overfit_risk": t((payload.get("overfit_risk") or {}).get("risk_level")),
            "latest_nav": (payload.get("equity_curve_analysis") or {}).get("latest_nav"),
            "excess_20d": (payload.get("benchmark_comparison") or {}).get("excess_20d"),
            "html_href": f"./reports/{d.name}/strategy_audit.html",
            "json_href": f"./reports/{d.name}/strategy_audit.json",
        })
    return out


def build_site(reports_root: Path, output_dir: Path, domain: str, repo_root: Path) -> None:
    latest_release = j(repo_root / "data" / "trade_release_v1" / "latest_release.json")
    manifest = j(Path(t(latest_release.get("manifest_path"), "")))
    market = j(repo_root / "data" / "market_state_v6" / "latest_market_state.json")
    strategy = j(repo_root / "data" / "event_lake_v6" / "research" / "three_strategy_kernel" / "three_strategy_state.json")
    oms = j(repo_root / "data" / "live_execution_bridge" / "oms_v1" / "snapshots" / "latest_actual_portfolio_state.json")
    clock = j(repo_root / "data" / "trade_clock" / "clock_state.json")
    safety = j(repo_root / "data" / "trade_clock" / "system_safety_state.json")
    health = j(repo_root / "data" / "trade_clock" / "latest_account_health.json")
    intraday_root = repo_root / "data" / "trade_clock" / "intraday_state" / "latest"
    intraday_phase = j(intraday_root / "intraday_phase_state.json")
    intraday_control = j(intraday_root / "intraday_control_summary.json")
    intraday_symbols = csv_rows(intraday_root / "symbol_execution_state.csv", 16)
    intraday_intents = csv_rows(intraday_root / "intent_state_daily.csv", 16)
    intraday_events = jsonl_tail(intraday_root / "intraday_event_log.jsonl", 12)
    incidents = jsonl_tail(repo_root / "data" / "trade_clock" / "incident_log.jsonl")
    gaps = csv_rows(repo_root / "data" / "live_execution_bridge" / "oms_v1" / "snapshots" / "desired_vs_actual_gap.csv", 12)
    targets = csv_rows(Path(t((manifest.get("artifacts") or {}).get("target_positions_path"), "")), 12)
    reports = report_rows(reports_root)
    account = oms.get("account") or {}
    allocation_bars = bars(list((strategy.get("strategy_allocations") or {}).items()))
    account_bars = bars([
        ("可用现金", (account.get("available_cash") or 0) / (account.get("total_asset") or 1)),
        ("现金占比", (account.get("cash") or 0) / (account.get("total_asset") or 1)),
        ("总仓位上限", (manifest.get("constraints") or {}).get("total_exposure_cap") or 0),
    ])
    report_timeline = timeline([
        (t(row.get("trade_date")), t(row.get("primary_strategy"), "-"), f"过拟合风险 {t(row.get('overfit_risk'), '-')}")
        for row in reports[:6]
    ])
    incident_timeline = timeline([
        (t(x.get("timestamp") or x.get("time") or x.get("at")), t(x.get("level"), "-"), t(x.get("event") or x.get("kind") or x.get("message"), t(x.get("raw"))))
        for x in reversed(incidents[:6])
    ])

    home = shell("量化系统门户", domain, "index", f"""
    <div class='section-title'><h2>首页总览</h2><div class='sub'>先看系统姿态、策略主导权和最新发布</div></div>
    <section class='grid'>
      <article class='card'><div class='label'>当前市场状态</div><div class='metric'>{html.escape(t(market.get("market_regime"), "未知"))}</div>{badge(t(market.get("style_bias"), "balanced"))}{badge(t(market.get("mechanism_bias"), "balanced"))}<p class='muted'>风险预算倍数 {n(market.get("risk_budget_multiplier"))}，换手倍数 {n(market.get("turnover_multiplier"))}。</p></article>
      <article class='card'><div class='label'>主导策略</div><div class='metric'>{html.escape(t(strategy.get("primary_strategy_key"), "未知"))}</div>{badge(t(strategy.get("status"), "unknown"))}<p class='muted'>生成时间 {html.escape(t(strategy.get("generated_at")))}</p></article>
      <article class='card'><div class='label'>交易时钟</div><div class='metric'>{html.escape(t(clock.get("market_stage"), "未知"))}</div>{badge(t((clock.get("gate") or {}).get("reason"), "未提供"))}<p class='muted'>服务状态 {html.escape(t((clock.get("runtime") or {}).get("service_status"), "未知"))}</p></article>
      <article class='card wide'><div class='label'>最新发布</div><div class='metric'>{html.escape(t(latest_release.get("release_id"), "暂无发布"))}</div>{kv([("交易日", latest_release.get("trade_date")), ("发布状态", latest_release.get("status")), ("生成时间", latest_release.get("generated_at")), ("运行模式", latest_release.get("source_mode")), ("候选数量", manifest.get("target_count")), ("策略名", manifest.get("strategy_name"))])}</article>
      <article class='card'><div class='label'>账户状态</div><div class='metric'>{n(account.get("total_asset"), 2)}</div>{badge(t(account.get("snapshot_health"), "unknown"))}<p class='muted'>可用现金 {n(account.get("available_cash"), 2)}，模式 {html.escape(t(account.get("account_mode")))}</p></article>
      <article class='card'><div class='label'>盘中状态机</div><div class='metric'>{html.escape(t(intraday_phase.get("current_phase"), "未生成"))}</div>{badge(t(intraday_phase.get("integration_mode"), "shadow"))}{badge(t(intraday_phase.get("safety_mode"), "unknown"))}<p class='muted'>午间决议 {html.escape(t(intraday_phase.get("midday_decision"), "-"))}，命名空间 {html.escape(t(intraday_phase.get("namespace"), "-"))}</p></article>
      <article class='card'><div class='label'>最新审计</div><div class='metric'>{html.escape(t(reports[0]["trade_date"] if reports else "暂无"))}</div><p class='muted'>主策略 {html.escape(t(reports[0]["primary_strategy"] if reports else "-"))}</p><p><a href='{html.escape(t(reports[0]["html_href"] if reports else "./audit-center.html"))}'>打开最新审计报告</a></p></article>
    </section>
    <div class='section-title'><h2>快速入口</h2><div class='sub'>减少来回切页</div></div>
    <section class='grid'>
      <article class='card'><div class='label'>系统状态页</div><div class='metric'>运行与安全</div><p class='muted'>看交易时钟、市场状态、安全状态和最近事件。</p><div class='button-row'><a class='btn' href='./system-status.html'>进入系统状态</a></div></article>
      <article class='card'><div class='label'>策略状态页</div><div class='metric'>三策略框架</div><p class='muted'>看三条长期策略的准备度和局限。</p><div class='button-row'><a class='btn' href='./strategy-status.html'>进入策略状态</a></div></article>
      <article class='card'><div class='label'>交易观察页</div><div class='metric'>仓位与执行</div><p class='muted'>看目标仓位、实际仓位、账户状态和执行差异。</p><div class='button-row'><a class='btn' href='./trade-monitor.html'>进入交易观察</a></div></article>
      <article class='card'><div class='label'>盘中状态机页</div><div class='metric'>阶段、标的、意图</div><p class='muted'>看 formal phase、symbol state、intent state 和事件时间轴。</p><div class='button-row'><a class='btn' href='./intraday-state.html'>进入盘中状态机</a></div></article>
    </section>""")

    incident_table = [[html.escape(t(x.get("timestamp") or x.get("time") or x.get("at"))), html.escape(t(x.get("level"))), html.escape(t(x.get("event") or x.get("kind") or x.get("message"), t(x.get("raw"))))] for x in reversed(incidents)]
    system = shell("系统状态", domain, "system", f"""
    <div class='section-title'><h2>系统状态</h2><div class='sub'>运行、调度、安全和账户健康集中展示</div></div>
    <section class='grid'>
      <article class='card'><div class='label'>交易时钟阶段</div><div class='metric'>{html.escape(t(clock.get("market_stage"), "未知"))}</div>{badge(t((clock.get("gate") or {}).get("reason"), "未提供"))}</article>
      <article class='card'><div class='label'>系统模式</div><div class='metric'>{html.escape(t(clock.get("system_mode"), "未知"))}</div>{badge(t(clock.get("market_safety_regime"), "unknown"))}</article>
      <article class='card'><div class='label'>安全状态</div><div class='metric'>{html.escape(t(safety.get("system_state") or safety.get("safety_state"), "未生成"))}</div>{badge(t(safety.get("system_state") or safety.get("safety_state"), "未生成"))}</article>
      <article class='card'><div class='label'>盘中 formal phase</div><div class='metric'>{html.escape(t(intraday_phase.get("current_phase"), "未生成"))}</div>{badge(t(intraday_phase.get("integration_mode"), "shadow"))}<p class='muted'>上一个阶段 {html.escape(t(intraday_phase.get("previous_phase"), "-"))}</p></article>
      <article class='card wide'><div class='label'>运行细节</div>{kv([("最近心跳", clock.get("last_heartbeat_at")), ("服务状态", (clock.get("runtime") or {}).get("service_status")), ("最后阶段", (clock.get("runtime") or {}).get("last_phase")), ("最后阶段状态", (clock.get("runtime") or {}).get("last_phase_status")), ("下一阶段", clock.get("next_due_phase")), ("下一时间", clock.get("next_due_at")), ("当前发布", latest_release.get("release_id")), ("发布交易日", latest_release.get("trade_date"))])}</article>
      <article class='card wide'><div class='label'>市场状态快照</div>{kv([("市场 regime", market.get("market_regime")), ("风格偏向", market.get("style_bias")), ("机制偏向", market.get("mechanism_bias")), ("风险预算倍数", n(market.get("risk_budget_multiplier"))), ("换手倍数", n(market.get("turnover_multiplier"))), ("建仓策略", market.get("new_position_policy")), ("去风险提示", market.get("de_risk_hint")), ("生成时间", market.get("generated_at"))])}</article>
      <article class='card'><div class='label'>账户健康</div><div class='metric'>{html.escape(t(health.get("status"), "未生成"))}</div><p class='muted'>如果这里长期为空，说明账户健康快照尚未接入当前副本。</p></article>
      <article class='card'><div class='label'>发布约束</div><div class='metric'>{p((manifest.get("constraints") or {}).get("total_exposure_cap"), 1)}</div><p class='muted'>单票上限 {p((manifest.get("constraints") or {}).get("single_name_cap"), 1)}，最大目标数 {html.escape(t(manifest.get("target_count")))}。</p></article>
      <article class='card'><div class='label'>账户结构图</div>{account_bars}</article>
      <article class='card wide'><div class='label'>盘中控制摘要</div>{kv([("integration_mode", intraday_control.get("integration_mode")), ("midday_action", intraday_control.get("midday_action")), ("timing_window", intraday_control.get("timing_window")), ("buy_ready_count", intraday_control.get("buy_ready_count")), ("sell_ready_count", intraday_control.get("sell_ready_count")), ("t_eligible_symbols", intraday_control.get("t_eligible_symbols")), ("t_triggered_symbols", intraday_control.get("t_triggered_symbols")), ("详情页", "./intraday-state.html")])}</article>
      <article class='card full'><div class='label'>最近异常与事件</div>{table(["时间", "级别", "事件"], incident_table)}</article>
      <article class='card full'><div class='label'>系统时间轴</div>{incident_timeline}</article>
    </section>""")

    strat_cards = []
    for key, payload in (strategy.get("strategies") or {}).items():
        payload = payload or {}
        limits = "".join(f"<li>{html.escape(str(x))}</li>" for x in list(payload.get("data_limitations", []) or [])[:4]) or "<li>当前没有额外的数据局限说明。</li>"
        strat_cards.append(f"<article class='card'><div class='label'>{html.escape(t(payload.get('strategy_key'), key))}</div><div class='metric'>{html.escape(t(payload.get('strategy_name'), key))}</div>{badge(t(payload.get('state'), 'unknown'))}<p class='muted'>readiness {n(payload.get('readiness_score'))}，evidence {n(payload.get('evidence_strength'))}</p><ul class='list'>{limits}</ul></article>")
    alloc = [[html.escape(k), p(v), html.escape(t(((strategy.get("strategies") or {}).get(k) or {}).get("state"), "-"))] for k, v in (strategy.get("strategy_allocations") or {}).items()]
    allowed = "".join(f"<li>{html.escape(str(x))}</li>" for x in list((strategy.get("llm_operating_model") or {}).get("allowed_roles", []) or [])) or "<li>暂无允许项说明。</li>"
    forbidden = "".join(f"<li>{html.escape(str(x))}</li>" for x in list((strategy.get("llm_operating_model") or {}).get("forbidden_roles", []) or [])) or "<li>暂无禁止项说明。</li>"
    strategy_page = shell("策略状态", domain, "strategy", f"""
    <div class='section-title'><h2>策略状态</h2><div class='sub'>三条长期策略已接入系统，但数据完备度并不一致</div></div>
    <section class='grid'>
      <article class='card full'>{kv([("策略框架", strategy.get("formal_strategy_framework")), ("主导策略", strategy.get("primary_strategy_key")), ("状态", strategy.get("status")), ("生成时间", strategy.get("generated_at")), ("股票 alpha 预算", n((strategy.get("portfolio_construction") or {}).get("alpha_budget_multiplier"))), ("目标现金缓冲", n((strategy.get("portfolio_construction") or {}).get("target_cash_buffer")))])}</article>
      {''.join(strat_cards) or "<article class='card full'><div class='empty'>当前没有策略状态可展示。</div></article>"}
      <article class='card wide'><div class='label'>策略配比</div>{table(["策略键", "当前配比", "状态"], alloc)}</article>
      <article class='card'><div class='label'>配比图</div>{allocation_bars}</article>
      <article class='card'><div class='label'>LLM 使用边界</div><div class='grid' style='grid-template-columns:1fr;gap:14px'><div><strong>允许</strong><ul class='list'>{allowed}</ul></div><div><strong>禁止</strong><ul class='list'>{forbidden}</ul></div></div><div class='callout'>LLM 现在是解释器和抽取器，不是数据真源，更不是直接拍板的交易员。</div></article>
    </section>""")

    target_rows = [[html.escape(t(r.get("symbol") or r.get("ts_code"))), html.escape(t(r.get("industry"))), p(r.get("final_target_weight_v2a") or r.get("portfolio_weight") or r.get("target_weight")), html.escape(t(r.get("desired_state") or r.get("current_state"))), html.escape(t(r.get("recommended_action") or r.get("desired_action")))] for r in targets]
    actual_rows = [[html.escape(t(r.get("symbol"))), n(r.get("actual_shares"), 0), p(r.get("actual_weight")), html.escape(t(r.get("actual_state"))), html.escape(t(r.get("state_gap_reason")))] for r in list(oms.get("positions") or [])[:12]]
    gap_rows = [[html.escape(t(r.get("symbol") or r.get("ts_code"))), p(r.get("target_weight") or r.get("desired_weight")), p(r.get("actual_weight")), p(r.get("gap_weight") or r.get("weight_gap")), html.escape(t(r.get("state_gap_reason") or r.get("gap_reason")))] for r in gaps]
    trade = shell("交易观察", domain, "trade", f"""
    <div class='section-title'><h2>交易观察</h2><div class='sub'>目标仓位、实际仓位和执行约束放在同一页看</div></div>
    <section class='grid'>
      <article class='card'><div class='label'>账户总资产</div><div class='metric'>{n(account.get("total_asset"), 2)}</div>{badge(t(account.get("snapshot_health"), "unknown"))}<p class='muted'>可用现金 {n(account.get("available_cash"), 2)}</p></article>
      <article class='card'><div class='label'>执行模式</div><div class='metric'>{html.escape(t(account.get("account_mode"), "未知"))}</div>{badge(t((manifest.get("execution_policy") or {}).get("precision_trade_enabled"), "false"))}<p class='muted'>默认高风险网页交易仍然关闭。</p></article>
      <article class='card'><div class='label'>最新发布交易日</div><div class='metric'>{html.escape(t(latest_release.get("trade_date"), "未知"))}</div><p class='muted'>目标持仓数 {html.escape(t(manifest.get("target_count")))}</p></article>
      <article class='card wide'><div class='label'>执行约束</div>{kv([("总仓位上限", p((manifest.get("constraints") or {}).get("total_exposure_cap"), 1)), ("单票上限", p((manifest.get("constraints") or {}).get("single_name_cap"), 1)), ("最大名称数", (manifest.get("constraints") or {}).get("max_names")), ("最大日换手", p((manifest.get("constraints") or {}).get("max_daily_turnover_ratio"), 1)), ("漂移阈值", n((manifest.get("constraints") or {}).get("drift_threshold"))), ("现金保留", p((manifest.get("constraints") or {}).get("cash_reserve_ratio"), 1))])}</article>
      <article class='card full'><div class='label'>目标仓位</div>{table(["标的", "行业", "目标权重", "目标状态", "建议动作"], target_rows)}</article>
      <article class='card full'><div class='label'>实际仓位</div>{table(["标的", "实际股数", "实际权重", "实际状态", "差异原因"], actual_rows)}</article>
      <article class='card full'><div class='label'>目标与实际差异</div>{table(["标的", "目标权重", "实际权重", "权重差", "说明"], gap_rows)}</article>
    </section>""")

    intraday_symbol_rows = [[
        html.escape(t(r.get("stock_code"))),
        html.escape(t(r.get("symbol_state"))),
        html.escape(t(r.get("timing_state"))),
        html.escape(t(r.get("source_lifecycle_state"))),
        p(r.get("target_weight")),
        p(r.get("actual_weight")),
        n(r.get("buy_timing_score")),
        n(r.get("sell_timing_score")),
        html.escape(t(r.get("t_overlay_state"))),
        html.escape(t(r.get("t_direction"))),
        p(r.get("t_allowed_ratio")),
        html.escape(t(r.get("last_intent_state"))),
        html.escape(t(r.get("action_band"))),
        html.escape(t(r.get("freeze_reason") or r.get("timing_freeze_reason"))),
        html.escape(t(r.get("feature_quality_tier"))),
    ] for r in intraday_symbols]
    intraday_intent_rows = [[
        html.escape(t(r.get("stock_code"))),
        html.escape(t(r.get("intent_id"))),
        html.escape(t(r.get("intent_state"))),
        html.escape(t(r.get("oms_status"))),
        html.escape(t(r.get("order_status"))),
        n(r.get("fill_ratio")),
        html.escape(t(r.get("stale_reason"))),
        html.escape(t(r.get("continuation_status"))),
    ] for r in intraday_intents]
    intraday_event_timeline = timeline([
        (
            t(x.get("timestamp") or x.get("generated_at") or x.get("updated_at")),
            t(x.get("event_type") or x.get("event")),
            t(x.get("stock_code") or x.get("symbol_state") or x.get("intent_state") or x.get("payload")),
        )
        for x in intraday_events
    ])
    intraday_phase_rows = [
        [html.escape(str(k)), html.escape(t(v))]
        for k, v in (intraday_phase.get("phase_status_overview") or {}).items()
    ]
    intraday_count_bars = bars(
        [(k, v / max(1, sum((intraday_control.get("symbol_state_counts") or {}).values()))) for k, v in (intraday_control.get("symbol_state_counts") or {}).items()]
        or [("no_symbol_state", 0.0)]
    )
    intraday_timing_state_bars = bars(
        [(k, v / max(1, sum((intraday_control.get("timing_state_counts") or {}).values()))) for k, v in (intraday_control.get("timing_state_counts") or {}).items()]
        or [("no_timing_state", 0.0)]
    )
    intraday_t_overlay_bars = bars(
        [(k, v / max(1, sum((intraday_control.get("t_overlay_state_counts") or {}).values()))) for k, v in (intraday_control.get("t_overlay_state_counts") or {}).items()]
        or [("no_t_overlay_state", 0.0)]
    )
    intraday_timing_bars = bars(
        [(k, v / max(1, sum((intraday_control.get("timing_feature_quality") or {}).values()))) for k, v in (intraday_control.get("timing_feature_quality") or {}).items()]
        or [("no_timing_quality", 0.0)]
    )
    intraday = shell("盘中状态机", domain, "intraday", f"""
    <div class='section-title'><h2>盘中状态机</h2><div class='sub'>把交易日阶段、单标的执行状态、OMS 意图状态和事件时间轴放到一套正式 sidecar 上</div></div>
    <section class='grid'>
      <article class='card'><div class='label'>当前 formal phase</div><div class='metric'>{html.escape(t(intraday_phase.get("current_phase"), "未生成"))}</div>{badge(t(intraday_phase.get("integration_mode"), "shadow"))}{badge(t(intraday_phase.get("safety_mode"), "unknown"))}</article>
      <article class='card'><div class='label'>午间决议</div><div class='metric'>{html.escape(t(intraday_phase.get("midday_decision"), "未生成"))}</div><p class='muted'>命名空间 {html.escape(t(intraday_phase.get("namespace"), "-"))}，上阶段 {html.escape(t(intraday_phase.get("previous_phase"), "-"))}</p></article>
      <article class='card'><div class='label'>风险压缩</div><div class='metric'>{html.escape(t((intraday_control.get("risk_summary") or {}).get("safety_mode"), "未生成"))}</div>{badge(t((intraday_control.get("risk_summary") or {}).get("market_safety_regime"), "unknown"))}<p class='muted'>halt_reason {html.escape(t((intraday_control.get("risk_summary") or {}).get("halt_reason"), "-"))}</p></article>
      <article class='card wide'><div class='label'>phase 约束</div>{kv([("integration_mode", intraday_phase.get("integration_mode")), ("timing_window", intraday_control.get("timing_window")), ("projected_afternoon_window", intraday_control.get("projected_afternoon_window")), ("allowed_action_bands", ", ".join(list(intraday_phase.get("allowed_action_bands", []) or [])) or "-"), ("manual_halt", intraday_phase.get("manual_halt")), ("manual_reduce_only", intraday_phase.get("manual_reduce_only")), ("overlay.block_new_entries", (intraday_control.get("overlay_recommendation") or {}).get("block_new_entries")), ("overlay.block_new_t", (intraday_control.get("overlay_recommendation") or {}).get("block_new_t")), ("event_count", intraday_control.get("event_count"))])}</article>
      <article class='card wide'><div class='label'>状态分布</div>{intraday_count_bars}</article>
      <article class='card'><div class='label'>控制计数</div>{kv([("freeze_count", intraday_control.get("freeze_count")), ("reconcile_only_count", intraday_control.get("reconcile_only_count")), ("buy_ready_count", intraday_control.get("buy_ready_count")), ("sell_ready_count", intraday_control.get("sell_ready_count")), ("t_eligible_symbols", intraday_control.get("t_eligible_symbols")), ("t_triggered_symbols", intraday_control.get("t_triggered_symbols")), ("open_intents_after", (intraday_control.get("risk_summary") or {}).get("open_intents_after")), ("gap_symbols", (intraday_control.get("risk_summary") or {}).get("n_gap_symbols"))])}</article>
      <article class='card'><div class='label'>Timing / T 摘要</div>{kv([("timing_layer_active", (intraday_control.get("overlay_recommendation") or {}).get("timing_layer_active")), ("buy_window_open_count", intraday_control.get("buy_window_open_count")), ("sell_window_open_count", intraday_control.get("sell_window_open_count")), ("afternoon_second_leg_candidates", intraday_control.get("afternoon_second_leg_candidates")), ("t_completed_count", intraday_control.get("t_completed_count")), ("feature_quality_keys", ", ".join(list((intraday_control.get("timing_feature_quality") or {}).keys())) or "-")])}</article>
      <article class='card wide'><div class='label'>Timing state 分布</div>{intraday_timing_state_bars}</article>
      <article class='card wide'><div class='label'>T overlay 分布</div>{intraday_t_overlay_bars}</article>
      <article class='card wide'><div class='label'>Timing 特征质量</div>{intraday_timing_bars}</article>
      <article class='card'><div class='label'>trade_clock phase 状态</div>{table(["phase", "status"], intraday_phase_rows)}</article>
      <article class='card full'><div class='label'>symbol execution state</div>{table(["标的", "symbol_state", "timing_state", "source_lifecycle", "target_weight", "actual_weight", "buy_score", "sell_score", "t_overlay_state", "t_direction", "t_allowed_ratio", "last_intent_state", "action_band", "freeze_reason", "feature_quality"], intraday_symbol_rows)}</article>
      <article class='card full'><div class='label'>intent state</div>{table(["标的", "intent_id", "intent_state", "oms_status", "order_status", "fill_ratio", "stale_reason", "continuation"], intraday_intent_rows)}</article>
      <article class='card full'><div class='label'>事件时间轴</div>{intraday_event_timeline}</article>
      <article class='card full'><div class='label'>当前 sidecar 名称</div>{kv([("phase_state", "intraday_phase_state.json"), ("control_summary", "intraday_control_summary.json"), ("symbol_execution_state", "symbol_execution_state.csv"), ("intent_state_daily", "intent_state_daily.csv"), ("event_log", "intraday_event_log.jsonl")])}</article>
    </section>""")

    audit_rows = [[html.escape(t(r["trade_date"])), html.escape(t(r["primary_strategy"])), html.escape(t(r["overfit_risk"])), n(r["latest_nav"]), p(r["excess_20d"]), f"<a href='{html.escape(t(r['html_href']))}'>查看 HTML</a>"] for r in reports[:20]]
    audit = shell("审计中心", domain, "audit", f"""
    <div class='section-title'><h2>审计中心</h2><div class='sub'>围绕系统盈亏、超额和过拟合风险做日常复盘</div></div>
    <section class='grid'>
      <article class='card wide'><div class='label'>最新审计摘要</div><div class='metric'>{html.escape(t(reports[0]["trade_date"] if reports else "暂无审计"))}</div>{kv([("主导策略", reports[0]["primary_strategy"] if reports else "-"), ("过拟合风险", reports[0]["overfit_risk"] if reports else "-"), ("最新净值", n(reports[0]["latest_nav"] if reports else None)), ("20日超额", p(reports[0]["excess_20d"] if reports else None)), ("链接", reports[0]["html_href"] if reports else "./index.html")])}</article>
      <article class='card'><div class='label'>当前用途</div><ul class='list'><li>看系统自己赚了什么，亏了什么。</li><li>看相对 HS300 是否有超额。</li><li>看执行损耗、仓位填充和策略主导权。</li><li>看是否出现纸面漂亮、实盘落不下去的过拟合迹象。</li></ul></article>
      <article class='card'><div class='label'>报告时间轴</div>{report_timeline}</article>
      <article class='card full'><div class='label'>报告列表</div>{table(["交易日", "主策略", "过拟合风险", "最新净值", "20日超额", "链接"], audit_rows)}</article>
    </section>""")

    login = shell("登录", domain, "login", """
    <div class='section-title'><h2>登录</h2><div class='sub'>这里已经接上轻量门户后端，可直接登录获取会话。</div></div>
    <section class='grid'><article class='card wide'><div class='label'>账户登录</div><div class='metric'>系统门户登录</div><div class='form-grid'><label>用户名或邮箱<input id='login-identity' type='text' placeholder='请输入用户名或邮箱'></label><label>密码<input id='login-password' type='password' placeholder='请输入密码'></label></div><div class='button-row'><button class='btn' onclick='portalLogin()'>立即登录</button><a class='btn alt' href='./register.html'>前往注册页</a></div><div id='login-toast' class='toast'></div><div class='callout'>登录成功后，评论区与管理后台会根据当前账号角色显示不同能力。</div></article><article class='card'><div class='label'>权限说明</div><ul class='list'><li>普通用户：浏览公开页面、提交评论、查看公开审计。</li><li>管理员：查看管理后台、隐藏或恢复评论。</li><li>高风险交易接口：默认关闭，仅预留入口，不直接开放。</li></ul></article></section><script>
    async function portalLogin(){const identity=document.getElementById('login-identity').value.trim();const password=document.getElementById('login-password').value;const toast=document.getElementById('login-toast');try{const res=await fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({identity,password})});const data=await res.json();toast.style.display='block';toast.textContent=data.message||data.error||'登录完成';if(data.ok){setTimeout(()=>location.href='./comments.html',500);}}catch(e){toast.style.display='block';toast.textContent='登录请求失败，请检查门户后端是否运行。';}}</script>""")

    register = shell("注册", domain, "register", """
    <div class='section-title'><h2>注册</h2><div class='sub'>第一位注册用户会自动成为管理员，适合当前单操作者场景。</div></div>
    <section class='grid'><article class='card wide'><div class='label'>创建账户</div><div class='metric'>量化系统门户注册</div><div class='form-grid'><label>用户名<input id='register-username' type='text' placeholder='建议使用容易识别的名称'></label><label>邮箱<input id='register-email' type='email' placeholder='请输入常用邮箱'></label><label>密码<input id='register-password' type='password' placeholder='请输入密码'></label><label>确认密码<input id='register-confirm' type='password' placeholder='请再次输入密码'></label></div><div class='button-row'><button class='btn' onclick='portalRegister()'>立即注册</button><a class='btn alt' href='./login.html'>已有账号，去登录</a></div><div id='register-toast' class='toast'></div></article><article class='card'><div class='label'>阶段说明</div><div class='callout'>这版先用 SQLite 做小型账号层，足够支撑门户登录、评论和管理员审核，不把复杂度拉得过高。</div></article></section><script>
    async function portalRegister(){const username=document.getElementById('register-username').value.trim();const email=document.getElementById('register-email').value.trim();const password=document.getElementById('register-password').value;const confirm=document.getElementById('register-confirm').value;const toast=document.getElementById('register-toast');if(password!==confirm){toast.style.display='block';toast.textContent='两次输入的密码不一致。';return;}try{const res=await fetch('/api/auth/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username,email,password})});const data=await res.json();toast.style.display='block';toast.textContent=data.message||data.error||'注册完成';if(data.ok){setTimeout(()=>location.href='./comments.html',500);}}catch(e){toast.style.display='block';toast.textContent='注册请求失败，请检查门户后端是否运行。';}}</script>""")

    comments = shell("评论区", domain, "comments", """
    <div class='section-title'><h2>评论区</h2><div class='sub'>面向门户页面和日报的轻量讨论区，默认按页面分流。</div></div>
    <section class='grid'><article class='card wide'><div class='label'>发表评论</div><div class='form-grid'><label>页面键<input id='comment-page-key' type='text' value='audit-center'></label><label>评论内容<textarea id='comment-body' placeholder='请输入你对当前页面、报告或策略的看法'></textarea></label></div><div class='toolbar'><button class='btn' onclick='postComment()'>发布评论</button><button class='btn alt' onclick='loadComments()'>刷新评论</button><a class='btn alt' href='./login.html'>去登录</a></div><div id='comment-toast' class='toast'></div></article><article class='card'><div class='label'>说明</div><ul class='list'><li>未登录时不能发表评论。</li><li>管理员可在后台隐藏或恢复评论。</li><li>当前以页面键分流，后面再补更细的线程结构。</li></ul></article><article class='card full'><div class='label'>最新评论</div><div id='comment-list' class='muted'>正在加载评论...</div></article></section><script>
    function commentCard(c, admin){const btn=admin?`<div class="toolbar"><button class="btn alt" onclick="moderateComment(${c.id}, '${c.status==='hidden'?'show':'hide'}')">${c.status==='hidden'?'恢复显示':'隐藏评论'}</button></div>`:'';return `<div class="comment-card"><div><strong>${c.author_name}</strong> · <span class="muted">${new Date(c.created_at*1000).toLocaleString('zh-CN')}</span> · <span class="muted">${c.page_key}</span> · <span class="muted">${c.status}</span></div><div style="margin-top:8px;line-height:1.8">${c.body}</div>${btn}</div>`;}
    async function loadComments(){const pageKey=document.getElementById('comment-page-key').value.trim()||'audit-center';const toast=document.getElementById('comment-toast');const list=document.getElementById('comment-list');try{const res=await fetch(`/api/comments?page_key=${encodeURIComponent(pageKey)}`);const data=await res.json();list.innerHTML=(data.comments||[]).map(c=>commentCard(c,false)).join('')||'当前没有评论。';toast.style.display='block';toast.textContent='评论已刷新。';}catch(e){list.textContent='评论加载失败。';toast.style.display='block';toast.textContent='评论加载失败，请检查门户后端。';}}
    async function postComment(){const pageKey=document.getElementById('comment-page-key').value.trim()||'audit-center';const body=document.getElementById('comment-body').value.trim();const toast=document.getElementById('comment-toast');try{const res=await fetch('/api/comments',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({page_key:pageKey,thread_key:pageKey,body})});const data=await res.json();toast.style.display='block';toast.textContent=data.message||data.error||'评论提交完成';if(data.ok){document.getElementById('comment-body').value='';loadComments();}}catch(e){toast.style.display='block';toast.textContent='评论提交失败，请检查门户后端。';}}
    loadComments();</script>""")

    admin = shell("管理后台", domain, "admin", """
    <div class='section-title'><h2>管理后台</h2><div class='sub'>当前先提供评论审核和后台概览，不直接开放危险交易按钮。</div></div>
    <section class='grid'><article class='card wide'><div class='label'>后台概览</div><div class='toolbar'><button class='btn' onclick='loadAdminSummary()'>刷新后台数据</button><a class='btn alt' href='./comments.html'>去评论区</a></div><div id='admin-toast' class='toast'></div><div id='admin-summary' class='muted' style='margin-top:12px'>正在加载后台摘要...</div></article><article class='card'><div class='label'>受控边界</div><ul class='list'><li>这里只做低风险后台操作。</li><li>不开放网页直接实盘下单。</li><li>不绕过安全层覆盖风险预算。</li></ul></article><article class='card full'><div class='label'>最新评论审核</div><div id='admin-comments' class='muted'>正在加载评论...</div></article></section><script>
    function adminCommentCard(c){return `<div class="comment-card"><div><strong>${c.author_name}</strong> · <span class="muted">${new Date(c.created_at*1000).toLocaleString('zh-CN')}</span> · <span class="muted">${c.page_key}</span> · <span class="muted">${c.status}</span></div><div style="margin-top:8px;line-height:1.8">${c.body}</div><div class="toolbar"><button class="btn alt" onclick="moderateComment(${c.id}, '${c.status==='hidden'?'show':'hide'}')">${c.status==='hidden'?'恢复显示':'隐藏评论'}</button></div></div>`;}
    async function loadAdminSummary(){const toast=document.getElementById('admin-toast');try{const res=await fetch('/api/admin/summary');const data=await res.json();toast.style.display='block';toast.textContent=data.ok?'后台数据已刷新。':(data.error||'加载失败');if(!data.ok){return;}const s=data.summary;document.getElementById('admin-summary').innerHTML=`<div class="bar-chart"><div class="bar-row"><div class="bar-label">用户数</div><div class="bar-track"><div class="bar-fill" style="width:${Math.min(100,s.total_users*10)}%"></div></div><div class="bar-value">${s.total_users}</div></div><div class="bar-row"><div class="bar-label">评论总数</div><div class="bar-track"><div class="bar-fill" style="width:${Math.min(100,s.total_comments*5)}%"></div></div><div class="bar-value">${s.total_comments}</div></div><div class="bar-row"><div class="bar-label">隐藏评论</div><div class="bar-track"><div class="bar-fill" style="width:${Math.min(100,s.hidden_comments*10)}%"></div></div><div class="bar-value">${s.hidden_comments}</div></div></div>`;document.getElementById('admin-comments').innerHTML=(s.recent_comments||[]).map(adminCommentCard).join('')||'当前没有评论。';}catch(e){toast.style.display='block';toast.textContent='后台请求失败，请确认你已登录管理员账号且门户后端在线。';}}
    async function moderateComment(id, action){const toast=document.getElementById('admin-toast');try{const res=await fetch(`/api/admin/comments/${id}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action})});const data=await res.json();toast.style.display='block';toast.textContent=data.message||data.error||'操作完成';if(data.ok){loadAdminSummary();}}catch(e){toast.style.display='block';toast.textContent='审核操作失败。';}}
    loadAdminSummary();</script>""")

    about = shell("关于系统", domain, "about", """
    <div class='section-title'><h2>关于系统</h2><div class='sub'>解释门户、核心策略框架和受控交易边界。</div></div>
    <section class='grid'><article class='card wide'><div class='label'>这个网站是什么</div><div class='metric'>量化系统门户</div><p class='muted'>它不是单纯演示页，而是面向真实运行系统的观察和发布界面。这里会逐步接入账号体系、评论区、管理员工具和受控接口，但所有高风险动作都要走清晰权限边界。</p><div class='callout'>实时交易相关接口目前仍然是预留和受控状态。第一版重点是可观察、可审计、可解释，不是网页上一键实盘下单。</div></article><article class='card'><div class='label'>当前已接入</div><ul class='list'><li>系统状态：交易时钟、市场状态、最新发布。</li><li>策略状态：三条长期策略状态与局限。</li><li>交易观察：目标仓位、实际仓位、执行约束。</li><li>盘中状态机：formal phase、symbol state、intent state、事件时间轴。</li><li>审计中心：系统净值、基准对比、过拟合风险。</li></ul></article><article class='card'><div class='label'>下一阶段</div><ul class='list'><li>管理员页接更多低风险运维动作。</li><li>盘中状态机页面加入跨日回放和 phase 对比。</li><li>更丰富的图表、时间轴和归因分析。</li><li>严格收益归因账本和策略级 NAV。</li></ul></article></section>""")

    output_dir.mkdir(parents=True, exist_ok=True)
    for name, content in {
        "index.html": home,
        "system-status.html": system,
        "strategy-status.html": strategy_page,
        "trade-monitor.html": trade,
        "intraday-state.html": intraday,
        "audit-center.html": audit,
        "comments.html": comments,
        "admin.html": admin,
        "login.html": login,
        "register.html": register,
        "about.html": about,
    }.items():
        (output_dir / name).write_text(content, encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="Build the Chinese static portal pages.")
    ap.add_argument("--reports-root", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--domain", type=str, default="peng1145141919810.xyz")
    args = ap.parse_args()
    build_site(args.reports_root.resolve(), args.output_dir.resolve(), args.domain, Path(__file__).resolve().parents[1])


if __name__ == "__main__":
    main()
