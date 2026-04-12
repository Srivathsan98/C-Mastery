#!/usr/bin/env python3
"""
Single-page C Mastery site: Claude roadmap look, sidebar navigation,
per-module workspace with merged questions (Claude checklist + ChatGPT coding +
Perplexity concepts + ChatGPT phase notes).
"""

from __future__ import annotations

import html as html_module
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "C-Mastery-Unified-Roadmap-Tracker.html"
LS_KEY = "c_mastery_merged_q_v1"

# GitHub Issues → live checklist (works when page is served over HTTPS, e.g. GitHub Pages)
GITHUB_REPO = "Srivathsan98/C-Mastery"


def he(s: str) -> str:
    return html_module.escape(s, quote=True)


def extract_modules_object(tracker_html: str) -> str:
    marker = "const MODULES = "
    start = tracker_html.index(marker) + len(marker)
    while tracker_html[start].isspace():
        start += 1
    assert tracker_html[start] == "{"
    depth = 0
    for i in range(start, len(tracker_html)):
        c = tracker_html[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return tracker_html[start : i + 1]
    raise ValueError("MODULES object not closed")


def parse_roadmap_cards(roadmap_html: str) -> list[dict]:
    """30 cards: index, icon, title, desc, phase class."""
    pat = re.compile(
        r'<div class="card-index">(\d{2})</div>\s*'
        r'<span class="card-icon">([^<]+)</span>\s*'
        r'<div class="card-title">([^<]+)</div>\s*'
        r'<div class="card-desc">([^<]+)</div>',
        re.DOTALL,
    )
    cards = []
    for m in pat.finditer(roadmap_html):
        idx = int(m.group(1))
        phase = "beginner" if idx <= 10 else "intermediate" if idx <= 20 else "advanced"
        cards.append(
            {
                "n": idx,
                "id": f"m{m.group(1)}",
                "icon": m.group(2).strip(),
                "title": m.group(3).strip(),
                "desc": m.group(4).strip(),
                "phase": phase,
            }
        )
    if len(cards) != 30:
        raise RuntimeError(f"expected 30 roadmap cards, got {len(cards)}")
    return cards


def parse_code_questions(md: str) -> list[dict]:
    sections = re.split(r"\n(?=# )", md.strip())
    out = []
    for sec in sections:
        if not sec.strip():
            continue
        lines = sec.strip().splitlines()
        title = lines[0].lstrip("# ").strip()
        cur = {"title": title, "beginner": [], "intermediate": [], "advanced": []}
        bucket = None
        for ln in lines[1:]:
            if ln.startswith("## "):
                h = ln[3:].strip().lower()
                if "beginner" in h:
                    bucket = "beginner"
                elif "intermediate" in h:
                    bucket = "intermediate"
                elif "advanced" in h:
                    bucket = "advanced"
                else:
                    bucket = None
            elif bucket and re.match(r"^\d+\.\s", ln):
                cur[bucket].append(re.sub(r"^\d+\.\s", "", ln).strip())
        out.append(cur)
    return out


def split_phase_raw(md: str) -> list[dict]:
    parts = re.split(r"\n(?=# [^#])", md.strip())
    sections = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        lines = p.split("\n", 1)
        title = lines[0].lstrip("# ").strip()
        body = lines[1] if len(lines) > 1 else ""
        sections.append({"title": title, "body": body})
    return sections


def dedupe_indices(indices: list[int]) -> list[int]:
    seen: set[int] = set()
    out: list[int] = []
    for i in indices:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


def pq_item_kind(text: str) -> str:
    t = text.lower()
    if any(
        w in t
        for w in (
            "write ",
            "write a",
            "implement ",
            "program ",
            "show how",
            "compile ",
            "run gdb",
            "use `",
            "debug ",
        )
    ):
        return "code"
    return "theory"


def extract_phase_tier_questions(body: str) -> dict[str, list[dict[str, str]]]:
    result: dict[str, list[dict[str, str]]] = {
        "Beginner": [],
        "Intermediate": [],
        "Advanced": [],
    }
    current: str | None = None
    for raw in body.splitlines():
        line = raw.strip()
        if line.startswith("### "):
            h = line[4:].lower()
            if "beginner" in h:
                current = "Beginner"
            elif "intermediate" in h:
                current = "Intermediate"
            elif "advanced" in h:
                current = "Advanced"
            else:
                current = None
            continue
        if not current or not line or line.startswith("---") or line.startswith("#"):
            continue
        if line.startswith("*(") or line.startswith(">"):
            continue
        text = ""
        if line.startswith("- "):
            text = line[2:].strip()
        elif re.match(r"^\d+\.\s", line):
            text = re.sub(r"^\d+\.\s", "", line).strip()
        if len(text) < 4:
            continue
        result[current].append({"t": text, "k": pq_item_kind(text)})
    return result


def build_extra_questions(
    mid: str,
    mg: dict,
    cq_topics: list[dict],
    pq_topics: list[dict],
    phase_sections: list[dict],
) -> dict[str, list[dict[str, str]]]:
    out: dict[str, list[dict[str, str]]] = {
        "Beginner": [],
        "Intermediate": [],
        "Advanced": [],
    }
    seen: set[str] = set()

    def push(tier: str, item: dict[str, str]) -> None:
        k = item["t"].strip().lower()
        if k in seen:
            return
        seen.add(k)
        out[tier].append({"t": item["t"], "k": item["k"]})

    for ci in dedupe_indices(mg["cq"]):
        t = cq_topics[ci]
        for lab, key in (
            ("Beginner", "beginner"),
            ("Intermediate", "intermediate"),
            ("Advanced", "advanced"),
        ):
            for q in t.get(key) or []:
                push(lab, {"t": q, "k": "code"})

    for pi in dedupe_indices(mg["pq"]):
        t = pq_topics[pi]
        for lab, key in (
            ("Beginner", "beginner"),
            ("Intermediate", "intermediate"),
            ("Advanced", "advanced"),
        ):
            for q in t.get(key) or []:
                qq = str(q).strip()
                push(lab, {"t": qq, "k": pq_item_kind(qq)})

    for ph_i in sorted(set(mg["ph"])):
        if 0 <= ph_i < len(phase_sections):
            sub = extract_phase_tier_questions(phase_sections[ph_i]["body"])
            for lab in ("Beginner", "Intermediate", "Advanced"):
                for item in sub[lab]:
                    push(lab, item)
    return out


def parse_claude_totals(modules_obj: str) -> dict[str, int]:
    totals: dict[str, int] = {}
    for m in re.finditer(r"\bm(\d{2}):\s*\{\s*total:\s*(\d+)", modules_obj):
        totals[f"m{m.group(1)}"] = int(m.group(2))
    return totals


def layer_for_card_phase(phase: str) -> str:
    return {"beginner": "Beginner", "intermediate": "Intermediate", "advanced": "Advanced"}[phase]


def count_merged_rows(claude_n: int, layer: str, extra: dict[str, list]) -> int:
    n = 0
    for tier in ("Beginner", "Intermediate", "Advanced"):
        if tier == layer:
            n += claude_n
        n += len(extra.get(tier) or [])
    return n


# Perplexity JSON index 0..15, ChatGPT Code-Questions index 0..11, phase section indices
MERGE = {
    "m01": {"pq": [0], "cq": [0], "ph": [0]},
    "m02": {"pq": [1], "cq": [0], "ph": [0]},
    "m03": {"pq": [1], "cq": [0], "ph": [0]},
    "m04": {"pq": [2], "cq": [1], "ph": [0, 1]},
    "m05": {"pq": [2], "cq": [1], "ph": [0, 2]},
    "m06": {"pq": [3], "cq": [3], "ph": [0, 4]},
    "m07": {"pq": [3], "cq": [3], "ph": [0, 4]},
    "m08": {"pq": [3], "cq": [0], "ph": [0]},
    "m09": {"pq": [2], "cq": [0], "ph": [0]},
    "m10": {"pq": [7], "cq": [6], "ph": [0, 7]},
    "m11": {"pq": [4], "cq": [2], "ph": [0, 3]},
    "m12": {"pq": [5], "cq": [5], "ph": [0, 6]},
    "m13": {"pq": [6], "cq": [4], "ph": [0, 5]},
    "m14": {"pq": [8], "cq": [7], "ph": [0, 8]},
    "m15": {"pq": [11], "cq": [2, 3], "ph": [0, 3, 4]},
    "m16": {"pq": [11], "cq": [1, 3], "ph": [0, 1, 4]},
    "m17": {"pq": [11], "cq": [2, 3], "ph": [0, 3, 4]},
    "m18": {"pq": [5], "cq": [5], "ph": [0, 6]},
    "m19": {"pq": [10], "cq": [0], "ph": [0, 12]},
    "m20": {"pq": [12], "cq": [7], "ph": [0, 13]},
    "m21": {"pq": [15], "cq": [2, 4], "ph": [0, 13]},
    "m22": {"pq": [4, 10], "cq": [2], "ph": [0, 3]},
    "m23": {"pq": [11], "cq": [2, 3], "ph": [0, 3, 4]},
    "m24": {"pq": [7], "cq": [6], "ph": [0, 7, 9]},
    "m25": {"pq": [13], "cq": [8], "ph": [0, 10]},
    "m26": {"pq": [13], "cq": [9], "ph": [0, 11]},
    "m27": {"pq": [13], "cq": [11], "ph": [0, 10]},
    "m28": {"pq": [15], "cq": [6], "ph": [0, 13]},
    "m29": {"pq": [15], "cq": [10], "ph": [0, 12]},
    "m30": {"pq": [12], "cq": [8, 3], "ph": [0, 13]},
}


def extract_roadmap_css(roadmap_html: str) -> str:
    return roadmap_html[roadmap_html.index("<style>") + 7 : roadmap_html.index("</style>")]


def main():
    roadmap_path = ROOT / "Claude" / "c_roadmap.html"
    tracker_path = ROOT / "Claude" / "c_notion_tracker.html"
    code_path = ROOT / "ChatGPT" / "Code-Questions.md"
    json_path = ROOT / "Perplexity" / "c-roadmap-full-questions.json"
    phase_path = ROOT / "ChatGPT" / "🧱 PHASE 1: CORE FOUNDATIONS (You must b.md"

    roadmap_raw = roadmap_path.read_text(encoding="utf-8")
    tracker_raw = tracker_path.read_text(encoding="utf-8")
    cards = parse_roadmap_cards(roadmap_raw)
    modules_obj = extract_modules_object(tracker_raw)
    cq_topics = parse_code_questions(code_path.read_text(encoding="utf-8"))
    pq_topics = json.loads(json_path.read_text(encoding="utf-8"))
    phase_raw = split_phase_raw(phase_path.read_text(encoding="utf-8"))
    claude_totals = parse_claude_totals(modules_obj)
    base_css = extract_roadmap_css(roadmap_raw)

    extra_by_mid: dict[str, dict[str, list]] = {}
    merged_totals: dict[str, int] = {}
    module_layer: dict[str, str] = {}
    for c in cards:
        mid = c["id"]
        layer = layer_for_card_phase(c["phase"])
        module_layer[mid] = layer
        ex = build_extra_questions(mid, MERGE[mid], cq_topics, pq_topics, phase_raw)
        extra_by_mid[mid] = ex
        cn = claude_totals.get(mid, 0)
        merged_totals[mid] = count_merged_rows(cn, layer, ex)
    global_total = sum(merged_totals.values())
    _sep = (",", ":")
    extra_json = json.dumps(extra_by_mid, ensure_ascii=False, separators=_sep)
    layer_json = json.dumps(module_layer, ensure_ascii=False, separators=_sep)
    totals_json = json.dumps(merged_totals, ensure_ascii=False, separators=_sep)

    extra_css = """
  .app-shell { max-width: 1480px; margin: 0 auto; padding: 0 20px 64px; position: relative; z-index: 1; }
  .workspace { display: grid; grid-template-columns: minmax(220px, 280px) 1fr; gap: 0; align-items: start;
    border: 1px solid var(--border); background: var(--panel); border-radius: 0; overflow: hidden; }
  @media (max-width: 900px) {
    .workspace { grid-template-columns: 1fr; }
    .rail { position: relative !important; max-height: none !important; border-right: none !important; border-bottom: 1px solid var(--border); }
  }
  .rail {
    position: sticky; top: 0; align-self: start; max-height: 100vh; overflow-y: auto;
    background: var(--bg2); border-right: 1px solid var(--border);
    font-family: 'JetBrains Mono', monospace; font-size: 11px;
  }
  .rail-head { padding: 20px 16px; border-bottom: 1px solid var(--border); color: var(--muted); letter-spacing: 2px; text-transform: uppercase; }
  .rail-phase { padding: 10px 16px 6px; color: var(--accent3); font-size: 10px; letter-spacing: 3px; text-transform: uppercase; }
  .rail-phase.beg { color: var(--accent); }
  .rail-phase.adv { color: var(--accent2); }
  .rail a.nav-mod {
    display: flex; align-items: center; gap: 10px; padding: 10px 16px; color: var(--text); text-decoration: none;
    border-left: 3px solid transparent; transition: background .15s, border-color .15s;
  }
  .rail a.nav-mod:hover { background: rgba(0,255,157,0.06); }
  .rail a.nav-mod.active { background: rgba(0,255,157,0.1); border-left-color: var(--accent); color: #fff; }
  .rail a.nav-mod .mi { opacity: .45; width: 22px; text-align: center; }
  .rail a.nav-mod .mt { flex: 1; line-height: 1.35; }
  .stage { padding: 28px 32px 40px; min-height: 70vh; background: var(--bg); }
  .module-view { display: none; animation: fade .2s ease; }
  .module-view.active { display: block; }
  @keyframes fade { from { opacity: 0; } to { opacity: 1; } }
  .detail-panel { border: 1px solid var(--border); padding: 0; overflow: hidden; }
  .detail-panel.beginner { box-shadow: inset 3px 0 0 var(--accent); }
  .detail-panel.intermediate { box-shadow: inset 3px 0 0 var(--accent3); }
  .detail-panel.advanced { box-shadow: inset 3px 0 0 var(--accent2); }
  .detail-top { padding: 24px 28px; border-bottom: 1px solid var(--border); background: var(--panel); position: relative; }
  .detail-top .big-idx { position: absolute; top: 16px; right: 20px; font-family: 'Bebas Neue', sans-serif; font-size: 56px; color: rgba(255,255,255,0.05); line-height: 1; }
  .detail-top .ico { font-size: 28px; display: block; margin-bottom: 10px; }
  .detail-top h2 { font-family: 'JetBrains Mono', monospace; font-size: 1.15rem; color: #fff; margin-bottom: 12px; letter-spacing: .5px; }
  .detail-top .detail-desc { font-size: 12px; color: var(--muted); line-height: 1.75; max-width: 900px; }
  .question-sheet { padding: 20px 24px 28px; }
  .panel-intro { font-size: 11px; color: var(--muted); margin-bottom: 16px; line-height: 1.6; }
  tr.q-section td { background: var(--bg2); border-bottom: 1px solid var(--border) !important; padding: 12px 10px !important; }
  .q-section-label { font-family: 'JetBrains Mono', monospace; font-size: 10px; letter-spacing: 3px; text-transform: uppercase; color: var(--accent3); }
  .detail-panel.beginner .q-section-label { color: var(--accent); }
  .detail-panel.advanced .q-section-label { color: var(--accent2); }
  .q-table { width: 100%; border-collapse: collapse; font-size: 12px; }
  .q-table th { text-align: left; font-size: 10px; color: var(--muted); font-weight: 500; padding: 8px 10px; border-bottom: 1px solid var(--border); text-transform: uppercase; letter-spacing: 1px; }
  .q-table td { padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.04); vertical-align: top; }
  .q-num { font-family: 'JetBrains Mono', monospace; font-size: 10px; color: var(--muted); white-space: nowrap; }
  .q-text { color: var(--text); line-height: 1.55; }
  .q-check { width: 18px; height: 18px; border: 1px solid var(--border); border-radius: 3px; cursor: pointer; display: flex; align-items: center; justify-content: center; flex-shrink: 0; transition: .15s; }
  .q-check:hover { border-color: var(--accent); }
  .q-check.checked { background: var(--accent); border-color: var(--accent); }
  .q-check.checked::after { content: '✓'; font-size: 11px; color: #000; font-weight: 800; }
  .q-row.checked .q-text { text-decoration: line-through; color: var(--muted); opacity: .7; }
  .q-type { font-size: 10px; padding: 2px 8px; border-radius: 2px; text-transform: lowercase; }
  .type-theory { color: var(--accent); border: 1px solid rgba(0,255,157,0.25); }
  .type-code { color: var(--accent4); border: 1px solid rgba(30,144,255,0.25); }
  .prog-inline { display: flex; align-items: center; gap: 14px; margin-bottom: 16px; flex-wrap: wrap; }
  .prog-inline .bar { flex: 1; min-width: 120px; height: 4px; background: var(--border); border-radius: 2px; overflow: hidden; }
  .prog-inline .fill { height: 100%; background: var(--accent); width: 0%; transition: width .3s; }
  .top-stats { display: flex; flex-wrap: wrap; gap: 20px; align-items: center; justify-content: center; padding: 20px 0 8px; border-bottom: 1px solid var(--border); margin-bottom: 24px; }
  .top-stats .chip { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--muted); }
  .top-stats .chip strong { color: var(--accent); }
  .hdr-mini { text-align: center; padding: 32px 16px 8px; }
  .hdr-mini .subtitle { margin-bottom: 0; }
  .sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0,0,0,0); border: 0; }
  .meta-hid span { position: absolute; left: -9999px; width: 1px; height: 1px; overflow: hidden; }
  .github-panel {
    margin: 0 0 24px; padding: 20px 22px; border: 1px solid var(--border); background: var(--panel);
    font-family: 'JetBrains Mono', monospace; font-size: 11px;
  }
  .github-panel h3 { font-size: 11px; letter-spacing: 3px; text-transform: uppercase; color: var(--accent); margin: 0 0 8px; font-weight: 600; }
  .github-panel .gh-lead { color: var(--muted); line-height: 1.6; margin-bottom: 14px; font-size: 11px; }
  .github-panel .gh-stats { display: flex; flex-wrap: wrap; align-items: center; gap: 12px; margin-bottom: 14px; }
  .github-panel .gh-bar-wrap { flex: 1; min-width: 160px; height: 4px; background: var(--border); border-radius: 2px; overflow: hidden; }
  .github-panel .gh-bar-fill { height: 100%; width: 0%; background: var(--accent4); transition: width .4s; }
  .github-panel #github-status { color: var(--accent3); min-height: 1.2em; margin-bottom: 10px; }
  .github-panel #github-issues { max-height: 320px; overflow-y: auto; border: 1px solid var(--border); padding: 10px 12px; background: var(--bg); }
  .gh-group { margin-bottom: 14px; }
  .gh-group:last-child { margin-bottom: 0; }
  .gh-group-title { font-size: 10px; letter-spacing: 2px; text-transform: uppercase; color: var(--accent3); margin-bottom: 8px; padding-bottom: 4px; border-bottom: 1px solid var(--border); }
  .gh-issue-row { display: flex; align-items: flex-start; gap: 10px; padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.04); }
  .gh-issue-row:last-child { border-bottom: none; }
  .gh-issue-row input { margin-top: 3px; flex-shrink: 0; accent-color: var(--accent); }
  .gh-issue-link { color: var(--text); text-decoration: none; flex: 1; line-height: 1.45; }
  .gh-issue-link:hover { color: var(--accent); text-decoration: underline; }
  .gh-issue-meta { color: var(--muted); flex-shrink: 0; font-size: 10px; }
"""

    # Sidebar
    rail_parts = ['<div class="rail-head">Modules</div>']
    current_phase = None
    for c in cards:
        p = c["phase"]
        if p != current_phase:
            current_phase = p
            lbl = {"beginner": "Phase 01 · Beginner", "intermediate": "Phase 02 · Intermediate", "advanced": "Phase 03 · Advanced"}[p]
            cls = "rail-phase beg" if p == "beginner" else "rail-phase adv" if p == "advanced" else "rail-phase"
            rail_parts.append(f'<div class="{cls}">{he(lbl)}</div>')
        mid = c["id"]
        rail_parts.append(
            f'<a href="#{mid}" class="nav-mod" data-mid="{mid}"><span class="mi">{he(c["icon"])}</span>'
            f'<span class="mt">{c["n"]:02d} · {he(c["title"])}</span></a>'
        )
    rail_html = "\n".join(rail_parts)

    # Module views — single merged question table per module
    view_parts = []
    for c in cards:
        mid = c["id"]
        mt = merged_totals[mid]
        view_parts.append(
            f'''
<section class="module-view" id="view-{mid}" data-mid="{mid}">
  <div class="detail-panel {c["phase"]}">
    <div class="detail-top">
      <span class="big-idx">{c["n"]:02d}</span>
      <span class="ico">{he(c["icon"])}</span>
      <h2>{he(c["title"])}</h2>
      <p class="detail-desc">{he(c["desc"])}</p>
    </div>
    <div class="question-sheet">
      <p class="panel-intro">All sources merged by section (Beginner → Intermediate → Advanced). Original checklist items sit in the section that matches this module’s phase. Type is <strong>theory</strong> or <strong>code</strong> only.</p>
      <div class="prog-inline">
        <span id="{mid}-prog" class="chip">0/{mt}</span>
        <span id="{mid}-status" class="module-status status-notstarted" style="font-size:10px;color:var(--muted)">Not started</span>
        <div class="bar"><div class="fill" id="{mid}-bar"></div></div>
        <span id="{mid}-barpct" style="font-size:10px;color:var(--muted)">0%</span>
      </div>
      <table class="q-table"><thead><tr><th style="width:36px">✓</th><th style="width:52px">#</th><th>Question</th><th style="width:80px">Type</th></tr></thead>
      <tbody id="{mid}-tbody"></tbody></table>
    </div>
  </div>
</section>'''
        )

    js_modules = "const MODULES = " + modules_obj + ";"

    app_js = """
const LS_KEY = "__LS_KEY__";
const EXTRA_QUESTIONS = __EXTRA_JSON__;
const MODULE_LAYER = __LAYER_JSON__;
const MERGED_TOTALS = __TOTALS_JSON__;
const GLOBAL_TOTAL = __GLOBAL_TOTAL__;
""" + js_modules + """
const saved = JSON.parse(localStorage.getItem(LS_KEY) || '{}');
let currentMid = 'm01';
let rendered = {};

function rowKind(t) {
  return String(t || '').toLowerCase() === 'code' ? 'code' : 'theory';
}

function escapeHtml(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

function renderModule(mid) {
  const tbody = document.getElementById(mid + '-tbody');
  if (!tbody) return;
  const m = MODULES[mid];
  const layer = MODULE_LAYER[mid];
  const extra = EXTRA_QUESTIONS[mid] || { Beginner: [], Intermediate: [], Advanced: [] };
  const tiers = ['Beginner', 'Intermediate', 'Advanced'];
  tbody.innerHTML = '';
  let u = 0;
  let qnum = 0;
  tiers.forEach(tier => {
    const rows = [];
    if (tier === layer && m && m.questions) {
      m.questions.forEach(q => { rows.push({ t: q.t, k: rowKind(q.type) }); });
    }
    (extra[tier] || []).forEach(item => { rows.push({ t: item.t, k: rowKind(item.k) }); });
    if (!rows.length) return;
    const sec = document.createElement('tr');
    sec.className = 'q-section';
    sec.innerHTML = '<td colspan="4"><span class="q-section-label">' + tier + '</span></td>';
    tbody.appendChild(sec);
    rows.forEach(item => {
      const key = mid + '_u' + u;
      u++;
      qnum++;
      const isDone = saved[key] === true;
      const ty = item.k === 'code' ? 'code' : 'theory';
      const tyClass = ty === 'code' ? 'type-code' : 'type-theory';
      const tr = document.createElement('tr');
      tr.className = 'q-row' + (isDone ? ' checked' : '');
      tr.innerHTML = '<td><div class="q-check' + (isDone ? ' checked' : '') + '" onclick="toggleUnified(\\'' + key + '\\',\\'' + mid + '\\',this)"></div></td>' +
        '<td class="q-num">Q' + String(qnum).padStart(3, '0') + '</td>' +
        '<td class="q-text">' + escapeHtml(item.t) + '</td>' +
        '<td><span class="q-type ' + tyClass + '">' + ty + '</span></td>';
      tbody.appendChild(tr);
    });
  });
  updateModuleProgress(mid);
}

function toggleUnified(key, mid, el) {
  const row = el.closest('tr');
  const isDone = !el.classList.contains('checked');
  saved[key] = isDone;
  localStorage.setItem(LS_KEY, JSON.stringify(saved));
  el.classList.toggle('checked', isDone);
  row.classList.toggle('checked', isDone);
  updateModuleProgress(mid);
  updateGlobal();
}

function updateModuleProgress(mid) {
  const total = MERGED_TOTALS[mid] || 0;
  let done = 0;
  for (let i = 0; i < total; i++) if (saved[mid + '_u' + i]) done++;
  const pct = total ? Math.round(done / total * 100) : 0;
  const prog = document.getElementById(mid + '-prog');
  const bar = document.getElementById(mid + '-bar');
  const barpct = document.getElementById(mid + '-barpct');
  const status = document.getElementById(mid + '-status');
  if (prog) prog.textContent = done + '/' + total;
  if (bar) bar.style.width = pct + '%';
  if (barpct) barpct.textContent = pct + '%';
  if (status) {
    if (done === 0) { status.textContent = 'Not started'; status.className = 'module-status status-notstarted'; }
    else if (done === total && total > 0) { status.textContent = 'Complete ✓'; status.className = 'module-status status-done'; }
    else { status.textContent = 'In progress'; status.className = 'module-status status-inprogress'; }
  }
}

function updateGlobal() {
  let totalDone = 0, modulesDone = 0;
  Object.keys(MERGED_TOTALS).forEach(mid => {
    const t = MERGED_TOTALS[mid];
    let d = 0;
    for (let i = 0; i < t; i++) if (saved[mid + '_u' + i]) d++;
    totalDone += d;
    if (t > 0 && d === t) modulesDone++;
  });
  const pct = GLOBAL_TOTAL ? Math.round(totalDone / GLOBAL_TOTAL * 100) : 0;
  const td = document.getElementById('total-done');
  const pd = document.getElementById('pct-done');
  const md = document.getElementById('modules-done');
  const mb = document.getElementById('main-bar');
  const bp = document.getElementById('bar-pct');
  if (td) td.textContent = totalDone;
  if (pd) pd.textContent = pct + '%';
  if (md) md.textContent = modulesDone;
  if (mb) mb.style.width = pct + '%';
  if (bp) bp.textContent = pct + '%';
}

function selectModule(mid) {
  currentMid = mid;
  document.querySelectorAll('.module-view').forEach(v => v.classList.toggle('active', v.dataset.mid === mid));
  document.querySelectorAll('.rail a.nav-mod').forEach(a => a.classList.toggle('active', a.dataset.mid === mid));
  if (!rendered[mid]) {
    renderModule(mid);
    rendered[mid] = true;
  } else {
    updateModuleProgress(mid);
  }
}

document.querySelectorAll('.rail a.nav-mod').forEach(a => {
  a.addEventListener('click', (e) => {
    e.preventDefault();
    selectModule(a.dataset.mid);
    history.replaceState(null, '', '#' + a.dataset.mid);
  });
});

function bootFromHash() {
  const h = (location.hash || '#m01').slice(1);
  if (MODULES[h]) selectModule(h);
  else selectModule('m01');
}

window.addEventListener('hashchange', bootFromHash);
document.addEventListener('DOMContentLoaded', () => {
  Object.keys(MERGED_TOTALS).forEach(mid => updateModuleProgress(mid));
  updateGlobal();
  bootFromHash();
});
"""
    app_js = (
        app_js.replace("__LS_KEY__", LS_KEY)
        .replace("__EXTRA_JSON__", extra_json)
        .replace("__LAYER_JSON__", layer_json)
        .replace("__TOTALS_JSON__", totals_json)
        .replace("__GLOBAL_TOTAL__", str(global_total))
    )

    github_js = """
(function () {
  const GH_REPO = "__GH_REPO__";
  const ISSUES_URL = "https://api.github.com/repos/" + GH_REPO + "/issues?state=all&per_page=100";

  function parseLinkNext(linkHeader) {
    if (!linkHeader) return null;
    const parts = linkHeader.split(",");
    for (const p of parts) {
      const m = p.match(/<([^>]+)>;\\s*rel="next"/);
      if (m) return m[1].trim();
    }
    return null;
  }

  async function fetchAllIssues() {
    const all = [];
    let url = ISSUES_URL;
    for (let page = 0; page < 10 && url; page++) {
      const res = await fetch(url, { headers: { Accept: "application/vnd.github+json" } });
      if (res.status === 403) {
        const j = await res.json().catch(() => ({}));
        const msg = (j && j.message) || "rate limited";
        throw new Error("GitHub API 403: " + msg);
      }
      if (!res.ok) throw new Error("GitHub API " + res.status);
      const chunk = await res.json();
      if (!Array.isArray(chunk)) throw new Error("bad JSON");
      all.push(...chunk);
      url = parseLinkNext(res.headers.get("Link"));
    }
    return all.filter((item) => !item.pull_request);
  }

  async function loadGitHubIssues() {
    const statusEl = document.getElementById("github-status");
    const listEl = document.getElementById("github-issues");
    const barEl = document.getElementById("github-issue-bar");
    const countsEl = document.getElementById("github-issue-counts");
    if (!listEl) return;
    if (statusEl) statusEl.textContent = "Loading issues…";
    listEl.innerHTML = "";
    try {
      const data = await fetchAllIssues();
      let open = 0,
        closed = 0;
      const groups = {};
      data.forEach((issue) => {
        if (issue.state === "open") open++;
        else closed++;
        const label =
          issue.labels && issue.labels.length ? String(issue.labels[0].name) : "Uncategorized";
        if (!groups[label]) groups[label] = [];
        groups[label].push(issue);
      });
      const total = open + closed;
      const pct = total ? Math.round((100 * closed) / total) : 0;
      if (barEl) barEl.style.width = pct + "%";
      if (countsEl)
        countsEl.textContent = closed + " / " + total + " closed · " + open + " open";
      if (statusEl) statusEl.textContent = total ? "" : "No issues in this repo yet.";
      const sortedLabels = Object.keys(groups).sort((a, b) => a.localeCompare(b));
      sortedLabels.forEach((gname) => {
        const wrap = document.createElement("div");
        wrap.className = "gh-group";
        const title = document.createElement("div");
        title.className = "gh-group-title";
        title.textContent = gname;
        wrap.appendChild(title);
        groups[gname]
          .sort((a, b) => b.number - a.number)
          .forEach((issue) => {
            const row = document.createElement("div");
            row.className = "gh-issue-row";
            const cb = document.createElement("input");
            cb.type = "checkbox";
            cb.checked = issue.state === "closed";
            cb.disabled = true;
            cb.title = issue.state === "closed" ? "Closed" : "Open";
            const link = document.createElement("a");
            link.href = issue.html_url;
            link.target = "_blank";
            link.rel = "noopener noreferrer";
            link.className = "gh-issue-link";
            link.textContent = issue.title;
            const meta = document.createElement("span");
            meta.className = "gh-issue-meta";
            meta.textContent = "#" + issue.number;
            row.appendChild(cb);
            row.appendChild(link);
            row.appendChild(meta);
            wrap.appendChild(row);
          });
        listEl.appendChild(wrap);
      });
    } catch (e) {
      if (statusEl)
        statusEl.textContent =
          "Could not load issues. Use HTTPS (GitHub Pages) or check rate limits / network. " +
          String(e.message || e);
      console.error(e);
    }
  }

  document.addEventListener("DOMContentLoaded", loadGitHubIssues);
})();
""".replace(
        "__GH_REPO__", GITHUB_REPO.replace("\\", "\\\\").replace('"', '\\"')
    )

    html_out = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>C Mastery — Roadmap &amp; merged question bank</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700;800&family=Bebas+Neue&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
{base_css}
{extra_css}
  .status-notstarted {{ color: var(--muted) !important; }}
  .status-inprogress {{ color: var(--accent3) !important; }}
  .status-done {{ color: var(--accent) !important; }}
</style>
</head>
<body>
<div class="container app-shell">
  <div class="header hdr-mini">
    <div class="header-badge">// complete mastery path</div>
    <h1>C ROADMAP</h1>
    <div class="subtitle">FROM ZERO TO SYSTEMS PROGRAMMER · EVERY CONCEPT · MERGED BANK</div>
    <div class="stats-row" style="margin-top:28px">
      <div class="stat"><div class="stat-num">30</div><div class="stat-label">Modules</div></div>
      <div class="stat"><div class="stat-num">{global_total}</div><div class="stat-label">Questions</div></div>
      <div class="stat"><div class="stat-num">3</div><div class="stat-label">Phases</div></div>
      <div class="stat"><div class="stat-num">∞</div><div class="stat-label">Extra drills</div></div>
    </div>
  </div>
  <div class="legend">
    <div class="legend-item"><div class="legend-dot" style="background:var(--accent)"></div>Beginner — 15 Qs / module</div>
    <div class="legend-item"><div class="legend-dot" style="background:var(--accent3)"></div>Intermediate — 20 Qs</div>
    <div class="legend-item"><div class="legend-dot" style="background:var(--accent2)"></div>Advanced — 30 Qs</div>
  </div>
  <div class="total-bar">
    <span class="bar-label">CHECKLIST + CODING + CONCEPTS (PER MODULE)</span>
    <div class="bar-track">
      <div class="bar-seg" style="left:0; width:29%; background:var(--accent); opacity:0.8"></div>
      <div class="bar-seg" style="left:29%; width:35%; background:var(--accent3); opacity:0.8"></div>
      <div class="bar-seg" style="left:64%; width:36%; background:var(--accent2); opacity:0.8"></div>
    </div>
    <span class="bar-total">ONE WORKSPACE</span>
  </div>
  <div class="top-stats">
    <span class="chip"><strong id="total-done">0</strong> / {global_total} questions done</span>
    <span class="chip"><strong id="pct-done">0%</strong> overall</span>
    <span class="chip"><strong id="modules-done">0</strong> / 30 modules complete</span>
    <span class="chip" style="flex:1;min-width:200px;max-width:420px;display:flex;align-items:center;gap:10px">
      <span style="flex:1;height:4px;background:var(--border);border-radius:2px;overflow:hidden">
        <span id="main-bar" style="display:block;height:100%;width:0%;background:var(--accent);transition:width .3s"></span>
      </span>
      <span id="bar-pct" style="min-width:36px">0%</span>
    </span>
  </div>
  <section class="github-panel" id="github-sync" aria-labelledby="gh-heading">
    <h3 id="gh-heading">GitHub project</h3>
    <p class="gh-lead">Issues from <a href="https://github.com/{he(GITHUB_REPO)}" target="_blank" rel="noopener noreferrer" style="color:var(--accent4)">{he(GITHUB_REPO)}</a>.
    Open = unchecked · closed = checked (updates when you merge PRs that close issues). Requires this page to be served over <strong>HTTPS</strong> (e.g. GitHub Pages), not <code>file://</code>.</p>
    <div class="gh-stats">
      <span id="github-issue-counts" style="color:var(--muted)">—</span>
      <div class="gh-bar-wrap"><div class="gh-bar-fill" id="github-issue-bar"></div></div>
    </div>
    <p id="github-status"></p>
    <div id="github-issues"></div>
  </section>
  <div class="workspace">
    <nav class="rail" aria-label="Modules">{rail_html}</nav>
    <main class="stage" id="main-stage">
      {"".join(view_parts)}
    </main>
  </div>
  <div class="footer" style="margin-top:48px;border-top:1px solid var(--border);padding-top:24px;">
    <p>C MASTERY · 30 MODULES · MERGED QUESTIONS · <span>BUILD. BREAK. FIX. REPEAT.</span></p>
    <p style="margin-top:8px;font-size:10px;">Progress key: <code>{LS_KEY}</code> (browser localStorage)</p>
  </div>
</div>
<script>
{app_js}
</script>
<script>
{github_js}
</script>
</body>
</html>
"""

    OUT.write_text(html_out, encoding="utf-8")
    print(f"Wrote {OUT} ({len(html_out):,} bytes)")


if __name__ == "__main__":
    main()
