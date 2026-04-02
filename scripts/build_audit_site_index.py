# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import csv
import html
import json
import math
from pathlib import Path
from typing import Any

try:
    from operator_intent import build_runtime_context as build_operator_runtime_context
except Exception:
    build_operator_runtime_context = None

STATUS_TEXT = {
    'ok': '正常', 'success': '成功', 'published': '已发布', 'normal': '正常', 'active': '活跃',
    'warning': '预警', 'warn': '预警', 'neutral': '中性', 'panic': '恐慌', 'halt': '停机',
    'failed': '失败', 'error': '错误', 'blocked': '阻断', 'balanced': '均衡', 'shadow': '影子模式',
    'bounded_takeover': '受控接管', 'simulation': '模拟', 'pre_open': '开盘前', 'morning_session': '上午盘',
    'midday_break': '午间', 'afternoon_session': '下午盘', 'post_close': '收盘后', 'entry': '建仓',
    'hold': '持有', 'trim': '减仓', 'exit': '退出', 'freeze': '冻结', 'reconcile_only': '仅对账',
    'pending': '待处理', 'applied': '已执行', 'cancelled': '已取消', 'visible': '显示中',
    'hidden': '已隐藏', 'unknown': '未知', 'true': '是', 'false': '否'
}
ACTION_TEXT = {
    'reduce': '人工减仓', 'exit': '清仓退出', 'freeze_buy': '冻结买入',
    'unfreeze_buy': '解除冻结', 'set_target_weight': '指定目标权重', 'note_only': '仅登记备注'
}


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return {}


def csv_rows(path: Path, limit: int = 20) -> list[dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open('r', encoding='utf-8-sig', newline='') as handle:
            rows = []
            for idx, row in enumerate(csv.DictReader(handle)):
                rows.append({str(k): str(v or '') for k, v in row.items()})
                if idx + 1 >= limit:
                    break
            return rows
    except Exception:
        return []


def jsonl_tail(path: Path, limit: int = 10) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    for line in path.read_text(encoding='utf-8', errors='ignore').splitlines()[-limit:]:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            out.append({'raw': line})
    return out


def raw_text(value: Any, default: str = '-') -> str:
    return str(value or '').strip() or default


def text(value: Any, default: str = '-') -> str:
    raw = raw_text(value, default)
    return STATUS_TEXT.get(raw.lower(), ACTION_TEXT.get(raw.lower(), raw))


def fmt_num(value: Any, digits: int = 2, default: str = '-') -> str:
    try:
        return f"{float(value):,.{digits}f}"
    except Exception:
        return default


def fmt_int(value: Any, default: str = '-') -> str:
    try:
        return f"{int(float(value)):,}"
    except Exception:
        return default


def fmt_pct(value: Any, digits: int = 1, default: str = '-') -> str:
    try:
        return f"{float(value) * 100:.{digits}f}%"
    except Exception:
        return default


def esc(value: Any) -> str:
    return html.escape(raw_text(value))


def tone(value: Any) -> str:
    lowered = str(value or '').strip().lower()
    if lowered in {'ok', 'success', 'published', 'normal', 'active', 'balanced', 'visible', 'applied'}:
        return 'good'
    if lowered in {'warning', 'warn', 'neutral', 'pending', 'shadow', 'simulation'}:
        return 'warn'
    if lowered in {'panic', 'halt', 'failed', 'error', 'blocked', 'hidden', 'cancelled'}:
        return 'bad'
    return 'neutral'


def badge(value: Any) -> str:
    return f"<span class='badge badge-{tone(value)}'>{html.escape(text(value))}</span>"


def card(body: str, cls: str = 'card') -> str:
    return f"<article class='{cls}'>{body}</article>"


def section(title: str, sub: str) -> str:
    return f"<div class='section-title'><h2>{html.escape(title)}</h2><div class='sub'>{html.escape(sub)}</div></div>"


def info_list(items: list[str]) -> str:
    rows = [item for item in items if str(item).strip()]
    if not rows:
        return "<div class='empty'>当前没有补充说明。</div>"
    return "<ul class='list'>" + ''.join(f"<li>{html.escape(item)}</li>" for item in rows) + "</ul>"


def table(headers: list[str], rows: list[list[str]]) -> str:
    head = ''.join(f"<th>{html.escape(h)}</th>" for h in headers)
    body = ''.join("<tr>" + ''.join(f"<td>{c}</td>" for c in row) + "</tr>" for row in rows)
    if not body:
        body = f"<tr><td colspan='{len(headers)}' class='empty'>当前没有可展示的数据。</td></tr>"
    return f"<div class='table-wrap'><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>"


def timeline(items: list[tuple[str, str, str]]) -> str:
    if not items:
        return "<div class='empty'>当前没有时间线事件。</div>"
    body = []
    for a, b, c in items:
        body.append("<div class='timeline-item'>" f"<div class='timeline-time'>{html.escape(a)}</div>" "<div class='timeline-dot'></div>" f"<div class='timeline-body'><strong>{html.escape(b)}</strong><div class='muted'>{html.escape(c)}</div></div></div>")
    return "<div class='timeline'>" + ''.join(body) + "</div>"

def bar_chart(items: list[tuple[str, float, str]]) -> str:
    if not items:
        return "<div class='empty'>当前没有图表数据。</div>"
    body = []
    for label, ratio, shown in items:
        width = max(0.0, min(100.0, ratio * 100.0))
        body.append("<div class='bar-row'>" f"<div class='bar-label'>{html.escape(label)}</div>" f"<div class='bar-track'><div class='bar-fill' style='width:{width:.1f}%'></div></div>" f"<div class='bar-value'>{html.escape(shown)}</div></div>")
    return "<div class='bar-chart'>" + ''.join(body) + "</div>"


def donut_chart(items: list[tuple[str, float, str]]) -> str:
    values = [(label, max(0.0, value), shown) for label, value, shown in items]
    total = sum(v for _, v, _ in values)
    if total <= 0:
        return "<div class='empty'>当前没有环形图数据。</div>"
    colors = ['#0f5cc0', '#c66a2b', '#2d7c63', '#7b405f', '#c49424']
    radius = 58
    circumference = 2 * math.pi * radius
    offset = 0.0
    circles = []
    legends = []
    for idx, (label, value, shown) in enumerate(values):
        pct = value / total if total else 0.0
        length = circumference * pct
        color = colors[idx % len(colors)]
        circles.append(f"<circle cx='84' cy='84' r='{radius}' fill='none' stroke='{color}' stroke-width='18' stroke-dasharray='{length:.2f} {circumference:.2f}' stroke-dashoffset='{-offset:.2f}' stroke-linecap='round'></circle>")
        legends.append(f"<div class='legend-item'><span class='legend-dot' style='background:{color}'></span><span>{html.escape(label)} · {html.escape(shown)}</span></div>")
        offset += length
    svg = "<svg class='donut' viewBox='0 0 168 168'>" + f"<circle cx='84' cy='84' r='{radius}' fill='none' stroke='rgba(23,36,43,.08)' stroke-width='18'></circle>" + ''.join(circles) + "<text x='84' y='80' text-anchor='middle' class='donut-text'>资产</text><text x='84' y='101' text-anchor='middle' class='donut-sub'>结构</text></svg>"
    return f"<div class='donut-wrap'>{svg}<div class='legend'>{''.join(legends)}</div></div>"


def line_chart(points: list[tuple[str, float]], title: str) -> str:
    if len(points) < 2:
        return "<div class='empty'>当前没有足够的折线图数据。</div>"
    values = [v for _, v in points]
    min_v = min(values)
    max_v = max(values)
    spread = max(max_v - min_v, 1e-9)
    width, height, left, top = 540, 240, 22, 16
    inner_w, inner_h = width - left * 2, height - 52
    coords = []
    for idx, (_, value) in enumerate(points):
        x = left + inner_w * idx / max(1, len(points) - 1)
        y = top + inner_h * (1 - ((value - min_v) / spread))
        coords.append((x, y))
    polyline = ' '.join(f"{x:.1f},{y:.1f}" for x, y in coords)
    area = ' '.join([f"{coords[0][0]:.1f},{top + inner_h:.1f}", polyline, f"{coords[-1][0]:.1f},{top + inner_h:.1f}"])
    point_marks = ''.join(f"<circle cx='{x:.1f}' cy='{y:.1f}' r='4' class='chart-point'></circle>" for x, y in coords)
    return (
        "<div class='line-chart'>"
        f"<div class='chart-title'>{html.escape(title)}</div>"
        f"<svg viewBox='0 0 {width} {height}'><path d='M {area} Z' class='chart-area'></path><polyline points='{polyline}' class='chart-line'></polyline>{point_marks}<text x='{left}' y='{height - 10}' class='chart-label'>{html.escape(fmt_num(min_v, 3))}</text><text x='{width - left}' y='24' class='chart-label' text-anchor='end'>{html.escape(fmt_num(max_v, 3))}</text><text x='{coords[0][0]:.1f}' y='{height - 10}' class='chart-label' text-anchor='middle'>{html.escape(points[0][0])}</text><text x='{coords[-1][0]:.1f}' y='{height - 10}' class='chart-label' text-anchor='middle'>{html.escape(points[-1][0])}</text></svg></div>"
    )


def shell(title: str, body: str, active: str) -> str:
    navs = [('总览', 'index.html', 'index'), ('系统状态', 'system-status.html', 'system'), ('策略状态', 'strategy-status.html', 'strategy'), ('交易监控', 'trade-monitor.html', 'trade'), ('盘中状态机', 'intraday-state.html', 'intraday'), ('审计中心', 'audit-center.html', 'audit'), ('评论区', 'comments.html', 'comments'), ('管理后台', 'admin.html', 'admin'), ('对话驾驶舱', 'operator-console.html', 'operator'), ('登录', 'login.html', 'login'), ('注册', 'register.html', 'register'), ('关于', 'about.html', 'about')]
    nav = ''.join(f"<a class='nav-link {'active' if key == active else ''}' href='./{href}'>{label}</a>" for label, href, key in navs)
    return f"""<!doctype html>
<html lang='zh-CN'>
<head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>{html.escape(title)} | 量化系统门户</title>
<style>
:root{{--paper:#efe2cb;--paper2:#d7c5ac;--ink:#17242b;--muted:#5b6872;--line:rgba(23,36,43,.12);--panel:rgba(255,249,241,.92);--navy:#143f67;--clay:#c0662d;--leaf:#2d7c63;--wine:#7b405f;--shadow:0 24px 70px rgba(24,34,41,.10);}}
*{{box-sizing:border-box}}body{{margin:0;font-family:"Microsoft YaHei","PingFang SC","Noto Serif SC",serif;color:var(--ink);background:radial-gradient(circle at top left,rgba(255,255,255,.55),transparent 22%),linear-gradient(145deg,var(--paper),var(--paper2));}}a{{color:var(--navy);text-decoration:none}}code{{font-family:Consolas,monospace;background:rgba(19,63,103,.07);padding:1px 5px;border-radius:6px}}.wrap{{max-width:1380px;margin:0 auto;padding:28px 18px 64px}}
.hero{{padding:30px 28px 26px;border-radius:34px;background:linear-gradient(135deg,rgba(255,251,245,.98),rgba(222,239,235,.88));border:1px solid rgba(23,36,43,.1);box-shadow:var(--shadow)}}.eyebrow{{font-size:13px;letter-spacing:.08em;color:var(--muted);text-transform:uppercase}}h1{{margin:10px 0 12px;font-size:42px;line-height:1.08}}.hero p{{margin:0;max-width:860px;color:var(--muted);line-height:1.75;font-size:15px}}
.nav{{display:flex;flex-wrap:wrap;gap:10px;margin-top:20px}}.nav-link{{padding:10px 16px;border-radius:999px;background:rgba(255,255,255,.72);border:1px solid rgba(23,36,43,.08);color:var(--ink);font-size:14px}}.nav-link.active{{background:var(--ink);border-color:var(--ink);color:#fff}}
.badge{{display:inline-flex;align-items:center;padding:5px 10px;border-radius:999px;font-size:12px;font-weight:700;margin:0 8px 8px 0}}.badge-good{{background:rgba(47,119,94,.12);color:var(--leaf)}}.badge-warn{{background:rgba(196,148,36,.14);color:#8f6509}}.badge-bad{{background:rgba(123,64,95,.12);color:var(--wine)}}.badge-neutral{{background:rgba(19,63,103,.08);color:var(--navy)}}
.section-title{{display:flex;justify-content:space-between;align-items:end;gap:16px;flex-wrap:wrap;margin:30px 2px 14px}}.section-title h2{{margin:0;font-size:26px}}.sub,.muted,.empty,.footer{{color:var(--muted);font-size:13px;line-height:1.7}}.grid{{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:18px}}.card{{grid-column:span 4;background:var(--panel);border:1px solid var(--line);border-radius:26px;padding:20px;box-shadow:var(--shadow)}}.wide{{grid-column:span 8}}.full{{grid-column:1/-1}}.label{{font-size:12px;color:var(--muted);letter-spacing:.06em;text-transform:uppercase}}.metric{{font-size:30px;font-weight:700;margin:10px 0 8px;line-height:1.12}}
.table-wrap{{overflow:auto;margin-top:10px}}table{{width:100%;border-collapse:collapse;font-size:14px}}th,td{{padding:10px 8px;border-bottom:1px solid rgba(23,36,43,.08);text-align:left;vertical-align:top}}th{{color:var(--muted);font-weight:700;white-space:nowrap}}.list{{margin:12px 0 0;padding-left:18px;line-height:1.8}}.callout{{margin-top:14px;padding:14px 16px;border-radius:18px;background:rgba(19,63,103,.07);border:1px solid rgba(19,63,103,.12);line-height:1.8;color:#18456d}}.button-row,.toolbar{{display:flex;gap:10px;flex-wrap:wrap;margin-top:12px}}.btn{{display:inline-flex;align-items:center;justify-content:center;padding:11px 18px;border:none;border-radius:999px;background:var(--ink);color:#fff;font:inherit;font-weight:700;cursor:pointer}}.btn.alt{{background:rgba(255,255,255,.75);color:var(--ink);border:1px solid rgba(23,36,43,.1)}}.btn.warn{{background:var(--clay)}}
.form-grid{{display:grid;gap:12px;margin-top:12px}}.form-grid.two{{grid-template-columns:repeat(2,minmax(0,1fr))}}.form-grid label{{display:grid;gap:6px;font-size:14px;color:var(--muted)}}.form-grid input,.form-grid textarea,.form-grid select{{width:100%;padding:12px 14px;border-radius:16px;border:1px solid rgba(23,36,43,.12);background:rgba(255,255,255,.9);color:var(--ink);font:inherit}}.form-grid textarea{{min-height:120px;resize:vertical}}.toast{{display:none;margin-top:12px;padding:12px 14px;border-radius:16px;background:rgba(47,119,94,.12);color:#245f4c}}.comment-card{{border:1px solid rgba(23,36,43,.08);background:rgba(255,255,255,.62);border-radius:18px;padding:14px;margin-top:12px}}
.bar-chart{{display:grid;gap:10px;margin-top:10px}}.bar-row{{display:grid;grid-template-columns:150px 1fr 86px;gap:10px;align-items:center}}.bar-label,.bar-value{{font-size:13px;color:var(--muted)}}.bar-track{{height:10px;border-radius:999px;background:rgba(23,36,43,.08);overflow:hidden}}.bar-fill{{height:100%;background:linear-gradient(90deg,var(--navy),var(--clay))}}.donut-wrap{{display:grid;grid-template-columns:190px 1fr;gap:16px;align-items:center}}.donut{{width:180px;height:180px}}.donut-text{{font-size:26px;fill:var(--ink);font-weight:700}}.donut-sub{{font-size:12px;fill:var(--muted)}}.legend{{display:grid;gap:8px}}.legend-item{{display:flex;align-items:center;gap:10px;font-size:14px}}.legend-dot{{width:12px;height:12px;border-radius:999px;display:inline-block}}.line-chart{{margin-top:10px}}.chart-title{{font-size:13px;color:var(--muted);margin-bottom:8px}}.chart-area{{fill:rgba(19,63,103,.09)}}.chart-line{{fill:none;stroke:var(--navy);stroke-width:3;stroke-linecap:round;stroke-linejoin:round}}.chart-point{{fill:var(--clay)}}.chart-label{{font-size:11px;fill:var(--muted)}}.timeline{{display:grid;gap:12px;margin-top:12px}}.timeline-item{{display:grid;grid-template-columns:130px 18px 1fr;gap:12px;align-items:start}}.timeline-time{{font-size:12px;color:var(--muted)}}.timeline-dot{{width:12px;height:12px;border-radius:50%;margin-top:4px;background:var(--clay);box-shadow:0 0 0 4px rgba(192,102,45,.12)}}
@media (max-width:1080px){{.card,.wide,.full{{grid-column:1/-1}}.form-grid.two{{grid-template-columns:1fr}}.donut-wrap{{grid-template-columns:1fr}}.bar-row{{grid-template-columns:120px 1fr 72px}}h1{{font-size:34px}}}}
</style>
</head>
<body><div class='wrap'><section class='hero'><div class='eyebrow'>量化系统门户 · 静态发布 + 轻量后台</div><h1>{html.escape(title)}</h1><p>当前门户从本地运行产物中生成状态页面，同时通过轻量后台提供登录、评论、管理员审核与人工持仓干预工单。网页端不直接绕过安全层下单，但管理员可以登记并追踪对当前持仓的人工干预指令。</p><div>{badge('published')}{badge('active')}{badge('balanced')}{badge('shadow')}</div><nav class='nav'>{nav}</nav></section>{body}<div class='footer' style='margin-top:34px'>当前页面由门户静态生成器构建；登录、评论、管理员后台和对话接口由本地轻量后台提供。</div></div></body></html>"""


def load_state(repo_root: Path, reports_root: Path) -> dict[str, Any]:
    latest_release = read_json(repo_root / 'data' / 'trade_release_v1' / 'latest_release.json')
    manifest_path = Path(str(latest_release.get('manifest_path', '') or '').strip())
    manifest = read_json(manifest_path) if str(manifest_path).strip() else {}
    intraday_root = repo_root / 'data' / 'trade_clock' / 'intraday_state' / 'latest'
    reports = []
    if reports_root.exists():
        for folder in sorted(reports_root.iterdir(), key=lambda item: item.name, reverse=True):
            if folder.is_dir() and (folder / 'strategy_audit.html').exists():
                payload = read_json(folder / 'strategy_audit.json')
                pnl_source = dict(payload.get('pnl_source_analysis') or {})
                t_overlay = dict(payload.get('t_overlay_analysis') or {})
                mechanism_rollup = list(pnl_source.get('mechanism_rollup') or [])
                t_window_rows = list(t_overlay.get('window_daily') or [])
                reports.append({
                    'trade_date': raw_text(payload.get('trade_date'), folder.name),
                    'generated_at': raw_text(payload.get('generated_at')),
                    'primary_strategy': raw_text((payload.get('strategy_exposure') or {}).get('primary_strategy_key')),
                    'overfit_risk': raw_text((payload.get('overfit_risk') or {}).get('risk_level')),
                    'latest_nav': payload.get('equity_curve_analysis', {}).get('latest_nav'),
                    'excess_20d': payload.get('benchmark_comparison', {}).get('excess_20d'),
                    'money_source_mode': raw_text(pnl_source.get('mode')),
                    'top_money_source_mechanism': raw_text((mechanism_rollup[0] or {}).get('bucket') if mechanism_rollup else ''),
                    'money_source_summary': raw_text((list(pnl_source.get('summary_lines') or []) or [''])[0]),
                    't_top_reject_reason': raw_text(t_overlay.get('top_reject_reason')),
                    't_top_mechanism': raw_text(t_overlay.get('top_suited_mechanism')),
                    't_window_summary': raw_text((t_window_rows[0] or {}).get('timing_window') if t_window_rows else ''),
                    'html_href': f"./reports/{folder.name}/strategy_audit.html"
                })
    return {
        'latest_release': latest_release, 'manifest': manifest,
        'market': read_json(repo_root / 'data' / 'market_state_v6' / 'latest_market_state.json'),
        'strategy': read_json(repo_root / 'data' / 'event_lake_v6' / 'research' / 'integrated_thesis' / 'integrated_thesis_state.json'),
        'oms': read_json(repo_root / 'data' / 'live_execution_bridge' / 'oms_v1' / 'snapshots' / 'latest_actual_portfolio_state.json'),
        'clock': read_json(repo_root / 'data' / 'trade_clock' / 'clock_state.json'),
        'safety': read_json(repo_root / 'data' / 'trade_clock' / 'system_safety_state.json'),
        'health': read_json(repo_root / 'data' / 'trade_clock' / 'latest_account_health.json'),
        'reports': reports,
        'targets': csv_rows(Path(str((manifest.get('artifacts') or {}).get('target_positions_path', '') or '')), 24),
        'gaps': csv_rows(repo_root / 'data' / 'live_execution_bridge' / 'oms_v1' / 'snapshots' / 'desired_vs_actual_gap.csv', 24),
        'live_snapshot': csv_rows(repo_root / 'data' / 'live_execution_bridge' / 'daily_price_snapshot.csv', 10),
        'intraday_phase': read_json(intraday_root / 'intraday_phase_state.json'),
        'intraday_control': read_json(intraday_root / 'intraday_control_summary.json'),
        'intraday_symbols': csv_rows(intraday_root / 'symbol_execution_state.csv', 18),
        'intraday_intents': csv_rows(intraday_root / 'intent_state_daily.csv', 18),
        'intraday_events': jsonl_tail(intraday_root / 'intraday_event_log.jsonl', 12),
        'incidents': jsonl_tail(repo_root / 'data' / 'trade_clock' / 'incident_log.jsonl', 10),
    }

def build_pages(state: dict[str, Any]) -> dict[str, str]:
    latest_release, manifest = state['latest_release'], state['manifest']
    market, strategy, oms = state['market'], state['strategy'], state['oms']
    clock, safety, health = state['clock'], state['safety'], state['health']
    reports, targets, gaps, live_snapshot = state['reports'], state['targets'], state['gaps'], state['live_snapshot']
    intraday_phase, intraday_control = state['intraday_phase'], state['intraday_control']
    intraday_symbols, intraday_intents = state['intraday_symbols'], state['intraday_intents']
    intraday_events, incidents = state['intraday_events'], state['incidents']
    account = oms.get('account') or {}
    positions = list(oms.get('positions') or [])
    allocations = {
        '主线事件产业盈利 Alpha': 1.0 if strategy else 0.0,
        '市场风险预算参考': float((strategy.get('portfolio_construction') or {}).get('risk_budget_reference') or 0.0)
    }
    allocation_chart = bar_chart([(raw_text(k), float(v or 0), fmt_pct(v, 1)) for k, v in allocations.items()])
    account_chart = donut_chart([('可用现金', float(account.get('available_cash') or 0), fmt_num(account.get('available_cash'), 2)), ('现金', float(account.get('cash') or 0), fmt_num(account.get('cash'), 2)), ('总资产', float(account.get('total_asset') or 0), fmt_num(account.get('total_asset'), 2))])
    nav_points = [(raw_text(item.get('trade_date')), float(item.get('latest_nav') or 0)) for item in reversed(reports[:8]) if item.get('latest_nav') is not None]
    audit_chart = line_chart(nav_points, '最近审计净值') if nav_points else "<div class='empty'>当前没有审计净值曲线。</div>"
    target_chart = bar_chart([(raw_text(r.get('symbol') or r.get('ts_code')), float(r.get('final_target_weight_v2a') or r.get('portfolio_weight') or r.get('target_weight') or 0), fmt_pct(r.get('final_target_weight_v2a') or r.get('portfolio_weight') or r.get('target_weight'), 1)) for r in targets[:8]])
    actual_chart = bar_chart([(raw_text(r.get('symbol')), float(r.get('actual_weight') or 0), fmt_pct(r.get('actual_weight'), 1)) for r in positions[:8]])
    incidents_timeline = timeline([(raw_text(i.get('timestamp') or i.get('time') or i.get('at')), text(i.get('level') or i.get('status') or 'unknown'), raw_text(i.get('event') or i.get('kind') or i.get('message') or i.get('raw'))) for i in reversed(incidents[:6])])
    audit_timeline = timeline([(raw_text(i.get('trade_date')), text(i.get('primary_strategy')), f"过拟合风险：{text(i.get('overfit_risk'))}，净值：{fmt_num(i.get('latest_nav'), 3)}，赚钱主线：{raw_text(i.get('top_money_source_mechanism'))}，T 适配：{raw_text(i.get('t_top_mechanism'))}") for i in reports[:6]])
    intraday_timeline = timeline([(raw_text(i.get('timestamp') or i.get('generated_at') or i.get('updated_at')), text(i.get('event_type') or i.get('event') or 'unknown'), raw_text(i.get('stock_code') or i.get('intent_state') or i.get('payload') or i.get('raw'))) for i in intraday_events])
    target_rows = [[esc(r.get('symbol') or r.get('ts_code')), esc(r.get('industry')), esc(fmt_pct(r.get('final_target_weight_v2a') or r.get('portfolio_weight') or r.get('target_weight'), 1)), esc(text(r.get('desired_state') or r.get('current_state') or 'unknown')), esc(text(r.get('recommended_action') or r.get('desired_action') or 'unknown'))] for r in targets]
    actual_rows = [[esc(r.get('symbol')), esc(fmt_int(r.get('actual_shares'))), esc(fmt_pct(r.get('actual_weight'), 1)), esc(text(r.get('actual_state') or 'unknown')), esc(r.get('state_gap_reason'))] for r in positions[:24]]
    gap_rows = [[esc(r.get('symbol') or r.get('ts_code')), esc(fmt_pct(r.get('target_weight') or r.get('desired_weight'), 1)), esc(fmt_pct(r.get('actual_weight'), 1)), esc(fmt_pct(r.get('gap_weight') or r.get('weight_gap'), 1)), esc(r.get('state_gap_reason') or r.get('gap_reason'))] for r in gaps]
    live_rows = [[esc(r.get('ts_code') or r.get('symbol')), esc(fmt_num(r.get('price'), 2)), esc(fmt_num(r.get('open'), 2)), esc(fmt_num(r.get('high'), 2)), esc(fmt_num(r.get('low'), 2)), esc(fmt_num(r.get('volume'), 0)), esc(fmt_num(r.get('amount'), 0))] for r in live_snapshot]
    system_rows = [[esc(i.get('timestamp') or i.get('time') or i.get('at')), esc(text(i.get('level') or i.get('status') or 'unknown')), esc(i.get('event') or i.get('kind') or i.get('message') or i.get('raw'))] for i in reversed(incidents)]
    intraday_symbol_rows = [[esc(r.get('stock_code')), esc(text(r.get('symbol_state') or 'unknown')), esc(text(r.get('timing_state') or 'unknown')), esc(text(r.get('source_lifecycle_state') or 'unknown')), esc(fmt_pct(r.get('target_weight'), 1)), esc(fmt_pct(r.get('actual_weight'), 1)), esc(fmt_num(r.get('buy_timing_score'), 3)), esc(fmt_num(r.get('sell_timing_score'), 3)), esc(text(r.get('t_overlay_state') or 'unknown')), esc(r.get('freeze_reason') or r.get('timing_freeze_reason'))] for r in intraday_symbols]
    intraday_intent_rows = [[esc(r.get('stock_code')), esc(r.get('intent_id')), esc(text(r.get('intent_state') or 'unknown')), esc(text(r.get('oms_status') or 'unknown')), esc(text(r.get('order_status') or 'unknown')), esc(fmt_num(r.get('fill_ratio'), 3)), esc(r.get('stale_reason'))] for r in intraday_intents]
    report_rows = [[esc(r.get('trade_date')), esc(text(r.get('primary_strategy'))), esc(raw_text(r.get('top_money_source_mechanism'))), esc(raw_text(r.get('t_top_mechanism'))), esc(raw_text(r.get('t_top_reject_reason'))), esc(text(r.get('overfit_risk'))), esc(fmt_num(r.get('latest_nav'), 3)), esc(fmt_pct(r.get('excess_20d'), 2)), esc(raw_text(r.get('money_source_mode'))), f"<a href='{esc(r.get('html_href'))}'>打开报告</a>"] for r in reports[:20]]
    intraday_symbol_table = table(['\u6807\u7684', '\u6807\u7684\u72b6\u6001', '\u65f6\u70b9\u72b6\u6001', '\u751f\u547d\u5468\u671f', '\u76ee\u6807\u6743\u91cd', '\u5b9e\u9645\u6743\u91cd', '\u4e70\u5165\u8bc4\u5206', '\u5356\u51fa\u8bc4\u5206', 'T\u5c42\u72b6\u6001', '\u51bb\u7ed3\u539f\u56e0'], intraday_symbol_rows)
    intraday_intent_table = table(['\u6807\u7684', '\u610f\u56fe\u7f16\u53f7', '\u610f\u56fe\u72b6\u6001', '\u59d4\u6258\u7cfb\u7edf\u72b6\u6001', '\u8ba2\u5355\u72b6\u6001', '\u6210\u4ea4\u6bd4\u4f8b', '\u6ede\u540e\u539f\u56e0'], intraday_intent_rows)
    audit_info = info_list(["\u53d1\u5e03\u7f16\u53f7\uff1a" + raw_text(latest_release.get("release_id")), "\u8fd0\u884c\u7f16\u53f7\uff1a" + raw_text(manifest.get("run_id")), "\u6700\u8fd1\u62a5\u544a\u6570\uff1a" + str(len(reports))])
    audit_report_table = table(['\u4ea4\u6613\u65e5', '\u4e3b\u5bfc\u7b56\u7565', '\u4e3b\u8981\u8d5a\u94b1\u673a\u5236', 'T\u9002\u914d\u673a\u5236', 'T\u4e3b\u963b\u65ad', '\u8fc7\u62df\u5408\u98ce\u9669', '\u6700\u65b0\u51c0\u503c', '20\u65e5\u8d85\u989d', '\u5f52\u56e0\u6a21\u5f0f', '\u94fe\u63a5'], report_rows)
    strategy_cards = ''.join(card(f"<div class='label'>{esc(p.get('strategy_key') or key)}</div><div class='metric'>{esc(p.get('strategy_name') or key)}</div>{badge(p.get('state') or 'unknown')}<p class='muted'>准备度 {fmt_num(p.get('readiness_score'), 3)}，证据强度 {fmt_num(p.get('evidence_strength'), 3)}</p>{info_list(list(p.get('data_limitations') or [])[:4])}") for key, p in (strategy.get('strategies') or {}).items()) or card("<div class='empty'>当前没有策略条目。</div>", 'card full')
    seed = ''.join(f"<tr><td>{html.escape(raw_text(r.get('symbol')))}</td><td>{html.escape(fmt_int(r.get('actual_shares')))}</td><td>{html.escape(fmt_pct(r.get('actual_weight'), 1))}</td><td>{html.escape(text(r.get('actual_state') or 'unknown'))}</td><td><button class='btn alt' type='button' onclick=\"prefillIntervention('{html.escape(raw_text(r.get('symbol')))}')\">填入干预表单</button></td></tr>" for r in positions[:16])
    seed_table = "<div class='table-wrap'><table><thead><tr><th>标的</th><th>股数</th><th>权重</th><th>状态</th><th>快捷操作</th></tr></thead><tbody>" + (seed or "<tr><td colspan='5' class='empty'>当前没有持仓快照。</td></tr>") + "</tbody></table></div>"
    login_script = "<script>async function portalLogin(){const identity=document.getElementById('login-identity').value.trim();const password=document.getElementById('login-password').value;const toast=document.getElementById('login-toast');try{const res=await fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({identity,password})});const data=await res.json();toast.style.display='block';toast.textContent=data.message||data.error||'登录完成';if(data.ok){setTimeout(()=>location.href='./admin.html',400);}}catch(e){toast.style.display='block';toast.textContent='登录请求失败，请检查门户后台是否运行。';}}</script>"
    register_script = "<script>async function portalRegister(){const username=document.getElementById('register-username').value.trim();const email=document.getElementById('register-email').value.trim();const password=document.getElementById('register-password').value;const confirm=document.getElementById('register-confirm').value;const toast=document.getElementById('register-toast');if(password!==confirm){toast.style.display='block';toast.textContent='两次输入的密码不一致。';return;}try{const res=await fetch('/api/auth/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username,email,password})});const data=await res.json();toast.style.display='block';toast.textContent=data.message||data.error||'注册完成';if(data.ok){setTimeout(()=>location.href='./admin.html',400);}}catch(e){toast.style.display='block';toast.textContent='注册请求失败，请检查门户后台是否运行。';}}</script>"
    comments_script = "<script>function commentCard(c){return `<div class=\"comment-card\"><div><strong>${c.author_name}</strong> · <span class=\"muted\">${new Date(c.created_at*1000).toLocaleString('zh-CN')}</span> · <span class=\"muted\">${c.page_key}</span> · <span class=\"muted\">${c.status}</span></div><div style=\"margin-top:8px;line-height:1.8\">${c.body}</div></div>`;}async function loadComments(){const pageKey=document.getElementById('comment-page-key').value.trim()||'\u5ba1\u8ba1\u4e2d\u5fc3';const list=document.getElementById('comment-list');const toast=document.getElementById('comment-toast');try{const res=await fetch(`/api/comments?page_key=${encodeURIComponent(pageKey)}`);const data=await res.json();list.innerHTML=(data.comments||[]).map(commentCard).join('')||'当前没有评论。';toast.style.display='block';toast.textContent='评论已刷新。';}catch(e){list.textContent='评论加载失败。';toast.style.display='block';toast.textContent='评论加载失败，请检查门户后台。';}}async function postComment(){const pageKey=document.getElementById('comment-page-key').value.trim()||'\u5ba1\u8ba1\u4e2d\u5fc3';const body=document.getElementById('comment-body').value.trim();const toast=document.getElementById('comment-toast');try{const res=await fetch('/api/comments',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({page_key:pageKey,thread_key:pageKey,body})});const data=await res.json();toast.style.display='block';toast.textContent=data.message||data.error||'评论提交完成';if(data.ok){document.getElementById('comment-body').value='';loadComments();}}catch(e){toast.style.display='block';toast.textContent='评论提交失败，请检查门户后台。';}}loadComments();</script>"
    admin_script = "<script>function prefillIntervention(symbol){document.getElementById('iv-symbol').value=symbol;document.getElementById('iv-reason').focus();window.scrollTo({top:0,behavior:'smooth'});}function interventionCard(item){const controls=item.status==='pending'?`<div class=\"toolbar\"><button class=\"btn alt\" onclick=\"updateInterventionStatus(${item.id},'applied')\">标记已执行</button><button class=\"btn alt\" onclick=\"updateInterventionStatus(${item.id},'cancelled')\">取消工单</button></div>`:'';return `<div class=\"comment-card\"><div><strong>${item.symbol}</strong> · <span class=\"muted\">${item.action_label||item.action_type}</span> · <span class=\"muted\">${item.status_label||item.status}</span> · <span class=\"muted\">${new Date(item.created_at*1000).toLocaleString('zh-CN')}</span></div><div style=\"margin-top:8px;line-height:1.8\"><div>理由：${item.reason||'-'}</div><div>说明：${item.note||'-'}</div><div>目标权重：${item.target_weight_display||'-'} · 股数变化：${item.share_delta_display||'-'}</div></div>${controls}</div>`;}function adminCommentCard(c){const nextAction=c.status==='hidden'?'show':'hide';const nextLabel=c.status==='hidden'?'恢复显示':'隐藏评论';return `<div class=\"comment-card\"><div><strong>${c.author_name}</strong> · <span class=\"muted\">${new Date(c.created_at*1000).toLocaleString('zh-CN')}</span> · <span class=\"muted\">${c.page_key}</span> · <span class=\"muted\">${c.status}</span></div><div style=\"margin-top:8px;line-height:1.8\">${c.body}</div><div class=\"toolbar\"><button class=\"btn alt\" onclick=\"moderateComment(${c.id},'${nextAction}')\">${nextLabel}</button></div></div>`;}async function loadAdminSummary(){const toast=document.getElementById('admin-toast');try{const res=await fetch('/api/admin/summary');const data=await res.json();toast.style.display='block';toast.textContent=data.ok?'后台数据已刷新。':(data.error||'加载失败');if(!data.ok){return;}const s=data.summary;document.getElementById('admin-summary').innerHTML=`<div class=\"bar-chart\"><div class=\"bar-row\"><div class=\"bar-label\">用户数</div><div class=\"bar-track\"><div class=\"bar-fill\" style=\"width:${Math.min(100,(s.total_users||0)*12)}%\"></div></div><div class=\"bar-value\">${s.total_users||0}</div></div><div class=\"bar-row\"><div class=\"bar-label\">评论总数</div><div class=\"bar-track\"><div class=\"bar-fill\" style=\"width:${Math.min(100,(s.total_comments||0)*5)}%\"></div></div><div class=\"bar-value\">${s.total_comments||0}</div></div><div class=\"bar-row\"><div class=\"bar-label\">待处理干预</div><div class=\"bar-track\"><div class=\"bar-fill\" style=\"width:${Math.min(100,(s.pending_interventions||0)*14)}%\"></div></div><div class=\"bar-value\">${s.pending_interventions||0}</div></div></div>`;document.getElementById('admin-comments').innerHTML=(s.recent_comments||[]).map(adminCommentCard).join('')||'当前没有评论。';}catch(e){toast.style.display='block';toast.textContent='后台请求失败，请确认你已登录管理员账号且门户后台在线。';}}async function moderateComment(id,action){const toast=document.getElementById('admin-toast');try{const res=await fetch(`/api/admin/comments/${id}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action})});const data=await res.json();toast.style.display='block';toast.textContent=data.message||data.error||'操作完成';if(data.ok){loadAdminSummary();}}catch(e){toast.style.display='block';toast.textContent='评论审核操作失败。';}}async function loadInterventions(){const toast=document.getElementById('admin-toast');try{const res=await fetch('/api/admin/interventions');const data=await res.json();if(!data.ok){toast.style.display='block';toast.textContent=data.error||'干预记录加载失败';return;}document.getElementById('intervention-list').innerHTML=(data.interventions||[]).map(interventionCard).join('')||'当前没有人工干预记录。';}catch(e){toast.style.display='block';toast.textContent='干预记录加载失败，请检查门户后台。';}}async function submitIntervention(){const toast=document.getElementById('admin-toast');const payload={symbol:document.getElementById('iv-symbol').value.trim(),action_type:document.getElementById('iv-action').value,target_weight:document.getElementById('iv-target-weight').value,share_delta:document.getElementById('iv-share-delta').value,reason:document.getElementById('iv-reason').value.trim(),note:document.getElementById('iv-note').value.trim(),page_context:'admin.html'};try{const res=await fetch('/api/admin/interventions',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const data=await res.json();toast.style.display='block';toast.textContent=data.message||data.error||'工单已提交';if(data.ok){document.getElementById('iv-target-weight').value='';document.getElementById('iv-share-delta').value='';document.getElementById('iv-reason').value='';document.getElementById('iv-note').value='';loadInterventions();loadAdminSummary();}}catch(e){toast.style.display='block';toast.textContent='人工干预提交失败。';}}async function updateInterventionStatus(id,status){const toast=document.getElementById('admin-toast');try{const res=await fetch(`/api/admin/interventions/${id}/status`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({status})});const data=await res.json();toast.style.display='block';toast.textContent=data.message||data.error||'状态已更新';if(data.ok){loadInterventions();loadAdminSummary();}}catch(e){toast.style.display='block';toast.textContent='工单状态更新失败。';}}loadAdminSummary();loadInterventions();</script>"
    operator_script = """
<script>
const OPERATOR_CHAT_API_BASE = window.OPERATOR_CHAT_API_BASE || '/api';
let operatorRequestInFlight = false;

function operatorRoleLabel(role){
  return role === 'assistant' ? '系统' : '你';
}

function setOperatorSendBusy(isBusy){
  operatorRequestInFlight = !!isBusy;
  const sendButton = document.getElementById('operator-send-btn');
  const input = document.getElementById('operator-input');
  if(sendButton){
    sendButton.disabled = !!isBusy;
    sendButton.textContent = isBusy ? '发送中...' : '发送给系统';
  }
  if(input){
    input.dataset.busy = isBusy ? '1' : '0';
  }
}

function setOperatorToast(message){
  const toast = document.getElementById('operator-toast');
  if(!toast){return;}
  toast.style.display = 'block';
  toast.textContent = message || '';
}

function operatorConversationStatus(item){
  const flags = [];
  if(item && Number(item.is_pinned || 0)){
    flags.push('已置顶');
  }
  if(item && Number(item.is_archived || 0)){
    flags.push('已归档');
  }
  return flags.join(' · ');
}

function renderOperatorProviderSummary(config){
  const box = document.getElementById('operator-provider-summary');
  if(!box){return;}
  const provider = (config && config.provider) || 'openai';
  const openaiModel = (config && config.openai_model) || '-';
  const ollamaModel = (config && config.ollama_model) || '-';
  const ollamaReachable = !!(((config || {}).available_providers || []).find(item => item.key === 'ollama') || {}).reachable;
  box.innerHTML = `<div>当前通道：${provider === 'ollama' ? '本地 Ollama' : '云端 API'}</div><div>云端模型：${openaiModel}</div><div>本地模型：${ollamaModel}</div><div>本地通道：${ollamaReachable ? '已连通' : '未连通'}</div>`;
}

function syncProviderSelectors(config){
  document.getElementById('operator-provider').value = (config && config.provider) || 'openai';
  document.getElementById('operator-openai-model').value = (config && config.openai_model) || 'deepseek-chat';
  const ollamaSelect = document.getElementById('operator-ollama-model');
  const models = (((config || {}).available_models || {}).ollama || []).slice();
  if(!models.length && config && config.ollama_model){
    models.push(config.ollama_model);
  }
  ollamaSelect.innerHTML = models.map(name => `<option value="${name}">${name}</option>`).join('') || '<option value="qwen2.5:7b">qwen2.5:7b</option>';
  ollamaSelect.value = (config && config.ollama_model) || 'qwen2.5:7b';
  renderOperatorProviderSummary(config || {});
}

async function loadProviderConfig(){
  try{
    const res = await fetch(`${OPERATOR_CHAT_API_BASE}/chat/provider`, {credentials:'include'});
    const data = await res.json();
    if(!data.ok){
      setOperatorToast(data.error || '无法读取模型通道配置。');
      return;
    }
    syncProviderSelectors(data.provider_config || {});
  }catch(e){
    setOperatorToast('无法读取模型通道配置。');
  }
}

async function saveProviderConfig(){
  const provider = document.getElementById('operator-provider').value || 'openai';
  const payload = {
    provider,
    openai_model: document.getElementById('operator-openai-model').value.trim() || 'deepseek-chat',
    ollama_model: document.getElementById('operator-ollama-model').value.trim() || 'qwen2.5:7b',
  };
  try{
    const res = await fetch(`${OPERATOR_CHAT_API_BASE}/chat/provider`, {
      method:'POST',
      credentials:'include',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify(payload)
    });
    const data = await res.json();
    if(!data.ok){
      setOperatorToast(data.error || '模型通道保存失败。');
      return;
    }
    syncProviderSelectors(data.provider_config || payload);
    setOperatorToast('模型通道已更新。云端和本地继续共用同一套会话与计划。');
  }catch(e){
    setOperatorToast('模型通道保存失败。');
  }
}

async function loadOperatorPlans(){
  const box = document.getElementById('operator-plans');
  if(!box){return;}
  try{
    const res = await fetch(`${OPERATOR_CHAT_API_BASE}/chat/plans`, {credentials:'include'});
    const data = await res.json();
    if(!data.ok){
      box.textContent = data.error || '无法读取待确认计划。';
      return;
    }
    box.innerHTML = (data.plans || []).map(item => `<div class="comment-card"><div><strong>${item.title}</strong><span class="muted"> · ${item.status||'-'} · ${new Date(item.updated_at*1000).toLocaleString('zh-CN')}</span></div><pre class="muted" style="white-space:pre-wrap;margin-top:8px">${JSON.stringify(item.plan||{},null,2)}</pre></div>`).join('') || '当前没有待确认计划。';
  }catch(e){
    box.textContent = '无法读取待确认计划。';
  }
}

async function operatorSend(){
  if(operatorRequestInFlight){
    return;
  }
  const message = document.getElementById('operator-input').value.trim();
  if(!message){return;}
  const conversationId = document.getElementById('operator-conversation-id').value || null;
  setOperatorSendBusy(true);
  try{
    const res = await fetch(`${OPERATOR_CHAT_API_BASE}/chat/send`, {
      method:'POST',
      credentials:'include',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({message, conversation_id:conversationId})
    });
    const data = await res.json();
    setOperatorToast(data.ok ? '系统回复已更新。' : (data.error || '请求失败。'));
    if(!data.ok){return;}
    document.getElementById('operator-conversation-id').value = data.conversation_id || '';
    document.getElementById('operator-reply').textContent = data.reply || '-';
    document.getElementById('operator-intent').textContent = JSON.stringify(data.intent || {}, null, 2);
    document.getElementById('operator-decision').textContent = JSON.stringify(data.decision || {}, null, 2);
    document.getElementById('operator-plan').textContent = JSON.stringify(data.pending_plan || ((data.decision || {}).pending_execution_plan) || {}, null, 2);
    document.getElementById('operator-context').textContent = JSON.stringify(data.runtime_context || {}, null, 2);
    document.getElementById('operator-model').textContent = JSON.stringify({
      active_provider: data.provider_config || {},
      intent_model: data.model_result || {},
      reply_model: data.reply_model_result || {}
    }, null, 2);
    document.getElementById('operator-docs').textContent = (data.docs_used || []).join('\\n') || '-';
    document.getElementById('operator-input').value = '';
    await loadOperatorConversations();
    await loadOperatorPlans();
  }catch(e){
    setOperatorToast('对话服务暂时不可用，请检查公网后台或本地 Ollama 隧道。');
  }finally{
    setOperatorSendBusy(false);
  }
}

async function loadOperatorConversations(){
  const list = document.getElementById('operator-conversations');
  try{
    const res = await fetch(`${OPERATOR_CHAT_API_BASE}/chat/conversations`, {credentials:'include'});
    const data = await res.json();
    if(!data.ok){
      list.textContent = data.error || '无法读取历史会话。';
      return;
    }
    list.innerHTML = (data.conversations || []).map(item => {
      const safeTitle = String(item.title || '').replace(/'/g, "\\'");
      const pinLabel = Number(item.is_pinned || 0) ? '取消置顶' : '置顶';
      const archiveLabel = Number(item.is_archived || 0) ? '取消归档' : '归档';
      const status = operatorConversationStatus(item);
      return `<div class="comment-card"><div><strong>${item.title}</strong><span class="muted"> · ${new Date(item.updated_at*1000).toLocaleString('zh-CN')}</span>${status?`<span class="muted"> · ${status}</span>`:''}</div><div class="muted" style="margin-top:8px">${item.summary_text || '当前还没有历史摘要。'}</div><div class="toolbar"><button class="btn alt" onclick="loadOperatorConversation(${item.id})">打开会话</button><button class="btn alt" onclick="renameOperatorConversation(${item.id}, '${safeTitle}')">重命名</button><button class="btn alt" onclick="updateOperatorConversation(${item.id}, 'toggle_pin')">${pinLabel}</button><button class="btn alt" onclick="updateOperatorConversation(${item.id}, 'toggle_archive')">${archiveLabel}</button><button class="btn alt" onclick="deleteOperatorConversation(${item.id})">删除会话</button></div></div>`;
    }).join('') || '当前还没有历史会话。';
  }catch(e){
    list.textContent = '无法读取历史会话。';
  }
}

function resetOperatorConversationView(){
  document.getElementById('operator-conversation-id').value = '';
  document.getElementById('operator-reply').textContent = '等待你的问题...';
  document.getElementById('operator-intent').textContent = '{}';
  document.getElementById('operator-decision').textContent = '{}';
  document.getElementById('operator-plan').textContent = '{}';
  document.getElementById('operator-context').textContent = '{}';
  document.getElementById('operator-model').textContent = '{}';
}

async function deleteOperatorConversation(id){
  if(!window.confirm('确认删除这条历史会话吗？对应消息和待确认计划会一并删除。')){
    return;
  }
  try{
    const res = await fetch(`${OPERATOR_CHAT_API_BASE}/chat/conversations/${id}`, {
      method:'POST',
      credentials:'include',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({action:'delete'})
    });
    const data = await res.json();
    if(!data.ok){
      setOperatorToast(data.error || '删除历史会话失败。');
      return;
    }
    if(String(document.getElementById('operator-conversation-id').value || '') === String(id)){
      resetOperatorConversationView();
    }
    setOperatorToast('历史会话已删除。');
    await loadOperatorConversations();
    await loadOperatorPlans();
  }catch(e){
    setOperatorToast('删除历史会话失败。');
  }
}

async function updateOperatorConversation(id, action, extra){
  try{
    const res = await fetch(`${OPERATOR_CHAT_API_BASE}/chat/conversations/${id}`, {
      method:'POST',
      credentials:'include',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify(Object.assign({action}, extra || {}))
    });
    const data = await res.json();
    if(!data.ok){
      setOperatorToast(data.error || '会话更新失败。');
      return;
    }
    setOperatorToast('会话设置已更新。');
    await loadOperatorConversations();
  }catch(e){
    setOperatorToast('会话更新失败。');
  }
}

async function renameOperatorConversation(id, currentTitle){
  const title = window.prompt('请输入新的会话名称：', currentTitle || '');
  if(title === null){
    return;
  }
  const trimmed = title.trim();
  if(!trimmed){
    setOperatorToast('会话名称不能为空。');
    return;
  }
  await updateOperatorConversation(id, 'rename', {title: trimmed});
}

async function loadOperatorConversation(id){
  try{
    const res = await fetch(`${OPERATOR_CHAT_API_BASE}/chat/conversations/${id}`, {credentials:'include'});
    const data = await res.json();
    if(!data.ok){
      setOperatorToast(data.error || '读取会话失败。');
      return;
    }
    document.getElementById('operator-conversation-id').value = id;
    const messages = (data.messages || []).map(item => `${operatorRoleLabel(item.role)}: ${item.content}`).join('\\n\\n');
    document.getElementById('operator-reply').textContent = messages || '-';
    const lastAssistant = [...(data.messages || [])].reverse().find(item => item.role === 'assistant') || {};
    document.getElementById('operator-intent').textContent = JSON.stringify(lastAssistant.intent || {}, null, 2);
    document.getElementById('operator-decision').textContent = JSON.stringify(lastAssistant.decision || {}, null, 2);
    document.getElementById('operator-plan').textContent = JSON.stringify((lastAssistant.decision || {}).pending_execution_plan || {}, null, 2);
    document.getElementById('operator-context').textContent = JSON.stringify(lastAssistant.context || {}, null, 2);
  }catch(e){
    setOperatorToast('读取会话失败。');
  }
}

loadProviderConfig();
loadOperatorConversations();
loadOperatorPlans();
document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('operator-input');
  if(!input){
    return;
  }
  input.addEventListener('keydown', (event) => {
    if(event.key === 'Enter' && !event.shiftKey){
      event.preventDefault();
      if(!operatorRequestInFlight){
        operatorSend();
      }
    }
  });
});
</script>
"""
    pages = {}
    pages['index.html'] = shell('量化系统总览', section('总览面板', '先看系统、策略、交易和盘中控制的整体状态') + "<section class='grid'>" + card(f"<div class='label'>当前市场状态</div><div class='metric'>{esc(text(market.get('market_regime') or 'unknown'))}</div>{badge(market.get('style_bias') or 'unknown')}{badge(market.get('mechanism_bias') or 'unknown')}<p class='muted'>风险预算倍数 {fmt_num(market.get('risk_budget_multiplier'), 2)}，时钟模式 {text(clock.get('mode') or 'unknown')}</p>") + card(f"<div class='label'>最新发布</div><div class='metric'>{esc(latest_release.get('release_id') or '暂无发布')}</div><p class='muted'>交易日 {esc(latest_release.get('trade_date'))}，生成时间 {esc(latest_release.get('generated_at'))}</p>{badge(latest_release.get('release_status') or 'published')}") + card(f"<div class='label'>风控与账户</div><div class='metric'>{esc(fmt_num(account.get('total_asset'), 2))}</div><p class='muted'>安全状态 {text(safety.get('status') or 'unknown')}，账户健康 {text(health.get('status') or 'unknown')}</p>") + card(f"<div class='label'>策略分配</div>{allocation_chart}", 'card wide') + card(f"<div class='label'>账户结构</div>{account_chart}", 'card wide') + card(f"<div class='label'>审计时间线</div>{audit_timeline}", 'card full') + card(f"<div class='label'>最新事件</div>{incidents_timeline}", 'card full') + '</section>', 'index')
    pages['system-status.html'] = shell('系统状态', section('系统运行情况', '交易时钟、风控状态和运行事件') + "<section class='grid'>" + card(f"<div class='label'>时钟阶段</div><div class='metric'>{esc(text(clock.get('current_phase') or clock.get('phase') or 'unknown'))}</div><p class='muted'>最近心跳 {esc(clock.get('last_heartbeat_at'))}</p>{badge(clock.get('mode') or 'unknown')}") + card(f"<div class='label'>系统安全</div><div class='metric'>{esc(text(safety.get('status') or 'unknown'))}</div><p class='muted'>{esc(safety.get('summary') or safety.get('message'))}</p>") + card(f"<div class='label'>账户健康</div><div class='metric'>{esc(text(health.get('status') or 'unknown'))}</div><p class='muted'>{esc(health.get('summary') or health.get('message'))}</p>") + card(f"<div class='label'>运行事件</div>{table(['时间', '级别', '事件'], system_rows)}", 'card full') + '</section>', 'system')
    pages['strategy-status.html'] = shell('策略状态', section('主线策略看板', '查看主线策略准备度、数据约束和目标分配') + "<section class='grid'>" + strategy_cards + card(f"<div class='label'>策略权重图</div>{allocation_chart}", 'card wide') + card(f"<div class='label'>目标持仓权重图</div>{target_chart}", 'card wide') + card(f"<div class='label'>目标持仓表</div>{table(['标的', '行业', '目标权重', '状态', '建议动作'], target_rows)}", 'card full') + '</section>', 'strategy')
    pages['trade-monitor.html'] = shell('交易监控', section('持仓与偏离', '对比目标持仓、实际持仓和偏离明细') + "<section class='grid'>" + card(f"<div class='label'>实际持仓权重图</div>{actual_chart}", 'card wide') + card(f"<div class='label'>最新价格快照</div>{table(['标的', '现价', '开盘', '最高', '最低', '成交量', '成交额'], live_rows)}", 'card wide') + card(f"<div class='label'>实际持仓</div>{table(['标的', '股数', '权重', '状态', '偏离原因'], actual_rows)}", 'card full') + card(f"<div class='label'>目标与实际偏离</div>{table(['标的', '目标权重', '实际权重', '偏离', '说明'], gap_rows)}", 'card full') + '</section>', 'trade')
    pages['intraday-state.html'] = shell('\u76d8\u4e2d\u72b6\u6001\u673a', section('\u76d8\u4e2d\u9636\u6bb5\u4e0e\u6267\u884c\u610f\u56fe', '\u67e5\u770b\u76d8\u4e2d\u9636\u6bb5\u3001\u6807\u7684\u72b6\u6001\u548c\u6267\u884c\u610f\u56fe') + "<section class='grid'>" + card(f"<div class='label'>\u5f53\u524d\u76d8\u4e2d\u9636\u6bb5</div><div class='metric'>{esc(text(intraday_phase.get('current_phase') or intraday_phase.get('phase') or 'unknown'))}</div><p class='muted'>\u63a7\u5236\u6a21\u5f0f {esc(text(intraday_control.get('control_mode') or 'unknown'))}\uff0c\u66f4\u65b0\u65f6\u95f4 {esc(intraday_phase.get('updated_at') or intraday_control.get('updated_at'))}</p>") + card(f"<div class='label'>\u63a7\u5236\u7ed3\u8bba</div><div class='metric'>{esc(text(intraday_control.get('decision') or intraday_control.get('status') or 'unknown'))}</div><p class='muted'>{esc(intraday_control.get('summary') or intraday_control.get('message'))}</p>") + card(f"<div class='label'>\u76d8\u4e2d\u4e8b\u4ef6\u65f6\u95f4\u7ebf</div>{intraday_timeline}", 'card full') + card(f"<div class='label'>\u6807\u7684\u6267\u884c\u72b6\u6001</div>{intraday_symbol_table}", 'card full') + card(f"<div class='label'>\u6267\u884c\u610f\u56fe\u72b6\u6001</div>{intraday_intent_table}", 'card full') + '</section>', 'intraday')
    audit_info = info_list(["\u53d1\u5e03\u7f16\u53f7\uff1a" + raw_text(latest_release.get("release_id")), "\u8fd0\u884c\u7f16\u53f7\uff1a" + raw_text(manifest.get("run_id")), "\u6700\u8fd1\u62a5\u544a\u6570\uff1a" + str(len(reports))])
    pages['audit-center.html'] = shell('\u5ba1\u8ba1\u4e2d\u5fc3', section('\u5ba1\u8ba1\u62a5\u544a\u3001\u51c0\u503c\u4e0e\u6536\u76ca\u5f52\u56e0', '\u67e5\u770b\u6700\u65b0\u5ba1\u8ba1\u62a5\u544a\u3001\u51c0\u503c\u3001\u8d85\u989d\u8868\u73b0\u4ee5\u53ca\u201c\u94b1\u662f\u600e\u4e48\u8d5a\u6765\u7684\u201d') + "<section class='grid'>" + card(f"<div class='label'>\u51c0\u503c\u66f2\u7ebf</div>{audit_chart}", 'card wide') + card(f"<div class='label'>\u6700\u65b0\u53d1\u5e03\u6458\u8981</div>{audit_info}", 'card wide') + card(f"<div class='label'>\u62a5\u544a\u5217\u8868</div>{audit_report_table}", 'card full') + '</section>', 'audit')
    pages['login.html'] = shell('登录', section('账户登录', '登录后可发表评论，管理员可进入后台') + "<section class='grid'>" + card("<div class='label'>登录门户</div><div class='metric'>系统门户登录</div><div class='form-grid'><label>用户名或邮箱<input id='login-identity' type='text' placeholder='请输入用户名或邮箱'></label><label>密码<input id='login-password' type='password' placeholder='请输入密码'></label></div><div class='button-row'><button class='btn' type='button' onclick='portalLogin()'>立即登录</button><a class='btn alt' href='./register.html'>前往注册</a></div><div id='login-toast' class='toast'></div><div class='callout'>登录成功后会根据账号角色切换评论和管理能力。</div>", 'card wide') + card(f"<div class='label'>权限边界</div>{info_list(['普通用户可浏览页面并发表评论。', '管理员可查看后台摘要、管理评论并提交持仓干预工单。', '网页端不直接绕过安全层或券商风控。'])}") + '</section>' + login_script, 'login')
    pages['register.html'] = shell('注册', section('创建账户', '第一位注册用户自动成为管理员') + "<section class='grid'>" + card("<div class='label'>创建门户账户</div><div class='metric'>系统门户注册</div><div class='form-grid two'><label>用户名<input id='register-username' type='text' placeholder='建议使用清晰的操作员名称'></label><label>邮箱<input id='register-email' type='email' placeholder='请输入常用邮箱'></label><label>密码<input id='register-password' type='password' placeholder='请输入密码'></label><label>确认密码<input id='register-confirm' type='password' placeholder='请再次输入密码'></label></div><div class='button-row'><button class='btn' type='button' onclick='portalRegister()'>立即注册</button><a class='btn alt' href='./login.html'>已有账号，去登录</a></div><div id='register-toast' class='toast'></div>", 'card wide') + card("<div class='label'>当前实现</div><div class='callout'>账户系统当前使用 SQLite，足够支撑登录、评论和管理员工单，复杂度保持可控。</div>") + '</section>' + register_script, 'register')
    pages['comments.html'] = shell('评论区', section('页面评论区', '围绕门户页面和报告的轻量讨论区') + "<section class='grid'>" + card("<div class='label'>发表评论</div><div class='form-grid'><label>页面键<input id='comment-page-key' type='text' value='\u5ba1\u8ba1\u4e2d\u5fc3'></label><label>评论内容<textarea id='comment-body' placeholder='请输入你对页面、报告或策略的看法'></textarea></label></div><div class='toolbar'><button class='btn' type='button' onclick='postComment()'>发布评论</button><button class='btn alt' type='button' onclick='loadComments()'>刷新评论</button><a class='btn alt' href='./login.html'>去登录</a></div><div id='comment-toast' class='toast'></div>", 'card wide') + card(f"<div class='label'>说明</div>{info_list(['未登录时不能发表评论。', '管理员可在后台隐藏或恢复评论。', '当前按页面键分流，后续可以细化为线程结构。'])}") + card("<div class='label'>最新评论</div><div id='comment-list' class='muted'>正在加载评论...</div>", 'card full') + '</section>' + comments_script, 'comments')
    pages['admin.html'] = shell('管理后台', section('管理员后台', '管理员可直接登记对当前持仓的人工干预工单') + "<section class='grid'>" + card("<div class='label'>后台摘要</div><div class='toolbar'><button class='btn' type='button' onclick='loadAdminSummary()'>刷新后台数据</button><button class='btn alt' type='button' onclick='loadInterventions()'>刷新干预记录</button></div><div id='admin-toast' class='toast'></div><div id='admin-summary' class='muted' style='margin-top:12px'>正在加载后台摘要...</div>", 'card wide') + card(f"<div class='label'>干预边界</div>{info_list(['管理员可以登记人工干预工单，直接面向当前持仓。', '工单会写入后台数据库和审计日志，便于人工执行与追踪。', '网页端仍不直接绕过系统安全层和券商风控。'])}") + card(f"<div class='label'>人工干预当前持仓</div><div class='form-grid two'><label>标的代码<input id='iv-symbol' type='text' placeholder='例如 600519'></label><label>干预动作<select id='iv-action'><option value='reduce'>人工减仓</option><option value='exit'>清仓退出</option><option value='freeze_buy'>冻结买入</option><option value='unfreeze_buy'>解除冻结</option><option value='set_target_weight'>指定目标权重</option><option value='note_only'>仅登记备注</option></select></label><label>目标权重（可选）<input id='iv-target-weight' type='number' min='0' max='1' step='0.01' placeholder='0.10 表示 10%'></label><label>股数变化（可选）<input id='iv-share-delta' type='number' step='1' placeholder='负数表示减仓'></label></div><div class='form-grid'><label>干预理由<input id='iv-reason' type='text' placeholder='例如 风险事件、临时停牌、人工校正'></label><label>补充说明<textarea id='iv-note' placeholder='填写管理员判断、上下文与执行备注'></textarea></label></div><div class='button-row'><button class='btn warn' type='button' onclick='submitIntervention()'>提交人工干预工单</button><a class='btn alt' href='./trade-monitor.html'>查看交易监控</a></div><div class='callout'>建议先从下方当前持仓中点击“填入干预表单”，再补充理由。</div>", 'card wide') + card(f"<div class='label'>当前持仓快捷填入</div>{seed_table}", 'card full') + card("<div class='label'>人工干预记录</div><div id='intervention-list' class='muted'>正在加载干预记录...</div>", 'card full') + card("<div class='label'>最新评论审核</div><div id='admin-comments' class='muted'>正在加载评论...</div>", 'card full') + '</section>' + admin_script, 'admin')
    pages['operator-console.html'] = shell('对话驾驶舱', section('系统对话驾驶舱', '在同一套记忆上下文里切换云端 API 和本地 Ollama') + "<section class='grid'>" + card("<div class='label'>操作对话</div><div class='form-grid'><label>向系统发消息<textarea id='operator-input' placeholder='例如：今天如果市场继续走弱，帮我分析是否需要降低高波动持仓。'></textarea></label><input id='operator-conversation-id' type='hidden'></div><div class='button-row'><button id='operator-send-btn' class='btn' type='button' onclick='operatorSend()'>发送给系统</button><button class='btn alt' type='button' onclick='loadOperatorConversations()'>刷新历史会话</button></div><div id='operator-toast' class='toast'></div><div class='callout'>这里的云端与本地模型共用同一套会话、上下文快照和待确认执行计划。切换模型不会丢失记忆。</div>", 'card wide') + card("<div class='label'>模型通道切换</div><div class='form-grid two'><label>当前通道<select id='operator-provider'><option value='openai'>云端 API</option><option value='ollama'>本地 Ollama</option></select></label><label>云端模型<input id='operator-openai-model' type='text' value='deepseek-chat' placeholder='例如 deepseek-chat'></label></div><div class='form-grid'><label>本地模型<select id='operator-ollama-model'><option value='qwen2.5:7b'>qwen2.5:7b</option><option value='deepseek-r1:14b'>deepseek-r1:14b</option></select></label></div><div class='button-row'><button class='btn warn' type='button' onclick='saveProviderConfig()'>保存模型通道</button><button class='btn alt' type='button' onclick='loadProviderConfig()'>刷新通道状态</button></div><div id='operator-provider-summary' class='callout'>正在读取模型通道...</div>", 'card wide') + card("<div class='label'>系统回复</div><pre id='operator-reply' class='muted' style='white-space:pre-wrap'>等待你的问题...</pre>", 'card wide') + card("<div class='label'>解析后的意图 JSON</div><pre id='operator-intent' class='muted' style='white-space:pre-wrap'>{}</pre>", 'card full') + card("<div class='label'>决策审查结果</div><pre id='operator-decision' class='muted' style='white-space:pre-wrap'>{}</pre>", 'card full') + card("<div class='label'>待确认执行计划</div><pre id='operator-plan' class='muted' style='white-space:pre-wrap'>{}</pre>", 'card full') + card("<div class='label'>运行时上下文</div><pre id='operator-context' class='muted' style='white-space:pre-wrap'>{}</pre>", 'card full') + card("<div class='label'>模型侧结果</div><pre id='operator-model' class='muted' style='white-space:pre-wrap'>{}</pre>", 'card full') + card("<div class='label'>知识上下文</div><pre id='operator-docs' class='muted' style='white-space:pre-wrap'>等待装载...</pre>", 'card full') + card("<div class='label'>待确认计划列表</div><div id='operator-plans' class='muted'>正在加载待确认计划...</div>", 'card full') + card("<div class='label'>历史会话</div><div id='operator-conversations' class='muted'>正在加载历史会话...</div>", 'card full') + '</section>' + operator_script, 'operator')
    pages['about.html'] = shell('关于系统', section('关于这个网站', '说明门户定位、权限边界和下一阶段工作') + "<section class='grid'>" + card("<div class='label'>门户定位</div><div class='metric'>量化系统门户</div><p class='muted'>它不是单纯的展示页，而是面向真实运行系统的观察、发布和轻量运维界面。当前版本优先保证可观察、可审计、可解释，再逐步补充更多受控交互。</p><div class='callout'>管理员现在已经可以通过网站登记对当前持仓的人工干预工单，但这仍然不会绕过本地安全层和交易风控。</div>", 'card wide') + card(f"<div class='label'>当前已接入</div>{info_list(['系统状态：交易时钟、市场状态和最新发布。', '策略状态：主线策略的状态、分配与数据限制。', '交易监控：目标持仓、实际持仓和偏离明细。', '盘中状态机：盘中阶段、标的执行状态、执行意图状态与事件时间线。', '审计中心：净值曲线、超额表现、赚钱来源与报告列表。', '管理后台：登录、评论、管理员人工干预工单。'])}") + card(f"<div class='label'>下一阶段</div>{info_list(['把管理员工单接入更正式的执行前人工确认链。', '补充盘中状态机的跨日对比与阶段回放。', '继续把审计页从代理归因推进到成交级收益归因。'])}") + '</section>', 'about')
    return pages


def build_site(reports_root: Path, output_dir: Path, repo_root: Path) -> None:
    state = load_state(repo_root, reports_root)
    pages = build_pages(state)
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, content in pages.items():
        (output_dir / name).write_text(content, encoding='utf-8')
    site_state = {'generated_at': raw_text(state['latest_release'].get('generated_at') or state['clock'].get('last_heartbeat_at')), 'latest_release_id': raw_text(state['latest_release'].get('release_id')), 'report_count': len(state['reports']), 'target_count': len(state['targets']), 'position_count': len((state['oms'].get('positions') or []))}
    (output_dir / 'site_state.json').write_text(json.dumps(site_state, ensure_ascii=False, indent=2), encoding='utf-8')
    if build_operator_runtime_context is not None:
        try:
            runtime_context = build_operator_runtime_context(repo_root)
            (output_dir / 'operator_runtime_context.json').write_text(json.dumps(runtime_context, ensure_ascii=False, indent=2), encoding='utf-8')
        except Exception:
            pass


def main() -> None:
    ap = argparse.ArgumentParser(description='Build the static portal site for audit and live state browsing.')
    ap.add_argument('--reports-root', type=Path, default=Path('F:/quant_data/AshareC#/outputs/site_publish_stage/reports'))
    ap.add_argument('--output-dir', type=Path, default=Path('F:/quant_data/AshareC#/outputs/site_publish_stage'))
    ap.add_argument('--repo-root', type=Path, default=Path('F:/quant_data/AshareC#'))
    args = ap.parse_args()
    build_site(args.reports_root, args.output_dir, args.repo_root)
    print(f"site built at {args.output_dir}")


if __name__ == '__main__':
    main()
