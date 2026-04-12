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
LS_KEY = "c_mastery_claude_site_v1"


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


def md_lines_to_html(text: str) -> str:
    chunks: list[str] = []
    list_mode: str | None = None  # 'ul' | 'ol'

    def close_list() -> None:
        nonlocal list_mode
        if list_mode == "ul":
            chunks.append("</ul>")
        elif list_mode == "ol":
            chunks.append("</ol>")
        list_mode = None

    for line in text.splitlines():
        line = line.rstrip()
        if not line.strip():
            close_list()
            continue
        if line.startswith("## "):
            close_list()
            chunks.append(f"<h4>{he(line[3:].strip())}</h4>")
        elif line.startswith("- ") or line.startswith("* "):
            if list_mode != "ul":
                close_list()
                chunks.append("<ul>")
                list_mode = "ul"
            chunks.append(f"<li>{he(line[2:].strip())}</li>")
        elif re.match(r"^\d+\.\s", line):
            if list_mode != "ol":
                close_list()
                chunks.append("<ol>")
                list_mode = "ol"
            item = re.sub(r"^\d+\.\s", "", line)
            chunks.append(f"<li>{he(item)}</li>")
        elif line.startswith(">"):
            close_list()
            chunks.append(f"<blockquote>{he(line.lstrip('> '))}</blockquote>")
        else:
            close_list()
            chunks.append(f"<p>{he(line)}</p>")
    close_list()
    return "\n".join(chunks)


def parse_phase_sections(md: str) -> list[dict]:
    parts = re.split(r"\n(?=# [^#])", md.strip())
    sections = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        lines = p.split("\n", 1)
        title = lines[0].lstrip("# ").strip()
        body = lines[1] if len(lines) > 1 else ""
        sections.append({"title": title, "html": md_lines_to_html(body)})
    return sections


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


def render_coding_block(cq_topics: list[dict], indices: list[int]) -> str:
    seen = []
    for i in indices:
        if i not in seen:
            seen.append(i)
    parts = []
    for i in seen:
        t = cq_topics[i]
        parts.append(f'<div class="merge-block"><h3 class="merge-block-title">{he(t["title"])}</h3>')
        for label, key in (("Beginner", "beginner"), ("Intermediate", "intermediate"), ("Advanced", "advanced")):
            qs = t.get(key) or []
            if not qs:
                continue
            parts.append(f'<h4 class="lvl">{label}</h4><ol class="q-ol">')
            for q in qs:
                parts.append(f"<li>{he(q)}</li>")
            parts.append("</ol>")
        parts.append("</div>")
    return "\n".join(parts) if parts else '<p class="empty-note">No coding prompts mapped for this module.</p>'


def render_pq_block(pq_topics: list[dict], indices: list[int]) -> str:
    seen = []
    for i in indices:
        if i not in seen:
            seen.append(i)
    parts = []
    for i in seen:
        t = pq_topics[i]
        name = t.get("name", f"Topic {i}")
        parts.append(f'<div class="merge-block"><h3 class="merge-block-title">{he(name)}</h3>')
        for label, key in (("Beginner", "beginner"), ("Intermediate", "intermediate"), ("Advanced", "advanced")):
            qs = t.get(key) or []
            if not qs:
                continue
            parts.append(f'<h4 class="lvl">{label}</h4><ol class="q-ol">')
            for q in qs:
                parts.append(f"<li>{he(str(q))}</li>")
            parts.append("</ol>")
        parts.append("</div>")
    return "\n".join(parts) if parts else '<p class="empty-note">No concept drills mapped.</p>'


def render_phase_block(phase_sections: list[dict], indices: list[int]) -> str:
    if not indices:
        return '<p class="empty-note">No phase notes mapped.</p>'
    seen = sorted(set(indices))
    parts = []
    for i in seen:
        if 0 <= i < len(phase_sections):
            s = phase_sections[i]
            parts.append(
                f'<details class="phase-details" open><summary>{he(s["title"])}</summary>'
                f'<div class="phase-body">{s["html"]}</div></details>'
            )
    return "\n".join(parts) if parts else '<p class="empty-note">No phase notes.</p>'


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
    phase_sections = parse_phase_sections(phase_path.read_text(encoding="utf-8"))
    base_css = extract_roadmap_css(roadmap_raw)

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
  .tab-row { display: flex; flex-wrap: wrap; gap: 8px; padding: 16px 20px; background: var(--bg2); border-bottom: 1px solid var(--border); }
  .tab-btn {
    font-family: 'JetBrains Mono', monospace; font-size: 10px; letter-spacing: 1px; text-transform: uppercase;
    padding: 10px 14px; border: 1px solid var(--border); background: var(--panel); color: var(--muted); cursor: pointer; border-radius: 2px;
  }
  .tab-btn:hover { border-color: var(--accent); color: var(--accent); }
  .tab-btn.active { border-color: var(--accent); color: var(--accent); background: rgba(0,255,157,0.08); }
  .tab-btn:disabled { opacity: .35; cursor: not-allowed; }
  .tab-panels { padding: 20px 24px 28px; }
  .tab-panel { display: none; }
  .tab-panel.active { display: block; }
  .panel-intro { font-size: 11px; color: var(--muted); margin-bottom: 16px; line-height: 1.6; }
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
  .type-debug { color: var(--accent3); border: 1px solid rgba(255,165,2,0.25); }
  .type-concept { color: #a78bfa; border: 1px solid rgba(167,139,250,0.25); }
  .prog-inline { display: flex; align-items: center; gap: 14px; margin-bottom: 16px; flex-wrap: wrap; }
  .prog-inline .bar { flex: 1; min-width: 120px; height: 4px; background: var(--border); border-radius: 2px; overflow: hidden; }
  .prog-inline .fill { height: 100%; background: var(--accent); width: 0%; transition: width .3s; }
  .merge-block { margin-bottom: 28px; padding-bottom: 20px; border-bottom: 1px solid var(--border); }
  .merge-block:last-child { border-bottom: none; }
  .merge-block-title { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: var(--accent4); margin-bottom: 12px; }
  .lvl { font-size: 10px; color: var(--accent3); text-transform: uppercase; letter-spacing: 2px; margin: 14px 0 8px; }
  .q-ol { margin: 0 0 8px 20px; color: var(--text); line-height: 1.6; font-size: 12px; }
  .q-ol li { margin-bottom: 6px; }
  .empty-note { color: var(--muted); font-size: 12px; font-style: italic; }
  .phase-details { margin-bottom: 12px; border: 1px solid var(--border); background: var(--panel); }
  .phase-details summary { padding: 12px 16px; cursor: pointer; font-weight: 600; color: var(--accent); font-size: 12px; }
  .phase-body { padding: 0 16px 16px; font-size: 12px; color: var(--muted); line-height: 1.65; }
  .phase-body h4 { color: var(--accent3); margin: 12px 0 6px; font-size: 11px; }
  .phase-body ul, .phase-body ol { margin-left: 18px; }
  .top-stats { display: flex; flex-wrap: wrap; gap: 20px; align-items: center; justify-content: center; padding: 20px 0 8px; border-bottom: 1px solid var(--border); margin-bottom: 24px; }
  .top-stats .chip { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--muted); }
  .top-stats .chip strong { color: var(--accent); }
  .hdr-mini { text-align: center; padding: 32px 16px 8px; }
  .hdr-mini .subtitle { margin-bottom: 0; }
  .sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0,0,0,0); border: 0; }
  .meta-hid span { position: absolute; left: -9999px; width: 1px; height: 1px; overflow: hidden; }
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

    # Module views
    view_parts = []
    for c in cards:
        mid = c["id"]
        mg = MERGE[mid]
        coding_html = render_coding_block(cq_topics, mg["cq"])
        pq_html = render_pq_block(pq_topics, mg["pq"])
        ph_html = render_phase_block(phase_sections, mg["ph"])
        total_q = 15 if c["phase"] == "beginner" else 20 if c["phase"] == "intermediate" else 30
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
    <div class="tab-row" role="tablist">
      <button type="button" class="tab-btn active" data-tab="claude">Checklist · Claude ({total_q})</button>
      <button type="button" class="tab-btn" data-tab="coding">Coding · ChatGPT</button>
      <button type="button" class="tab-btn" data-tab="concepts">Concepts · Perplexity</button>
      <button type="button" class="tab-btn" data-tab="phase">Phase · ChatGPT</button>
    </div>
    <div class="tab-panels">
      <div class="tab-panel active" data-panel="claude">
        <p class="panel-intro">Same checklist as the original tracker. Check boxes persist in your browser.</p>
        <div class="prog-inline">
          <span id="{mid}-prog" class="chip">0/{total_q}</span>
          <span id="{mid}-status" class="module-status status-notstarted" style="font-size:10px;color:var(--muted)">Not started</span>
          <div class="bar"><div class="fill" id="{mid}-bar"></div></div>
          <span id="{mid}-barpct" style="font-size:10px;color:var(--muted)">0%</span>
        </div>
        <table class="q-table"><thead><tr><th style="width:36px">✓</th><th style="width:44px">#</th><th>Question</th><th style="width:72px">Type</th></tr></thead>
        <tbody id="{mid}-tbody"></tbody></table>
      </div>
      <div class="tab-panel" data-panel="coding"><p class="panel-intro">Coding prompts from <code>Code-Questions.md</code>, merged for this module.</p>{coding_html}</div>
      <div class="tab-panel" data-panel="concepts"><p class="panel-intro">Question templates from <code>c-roadmap-full-questions.json</code>.</p>{pq_html}</div>
      <div class="tab-panel" data-panel="phase"><p class="panel-intro">Excerpts from the ChatGPT phase roadmap that match this module.</p>{ph_html}</div>
    </div>
  </div>
</section>'''
        )

    js_modules = "const MODULES = " + modules_obj + ";"

    app_js = """
const LS_KEY = "__LS_KEY__";
const TYPE_MAP = { theory:'type-theory', code:'type-code', debug:'type-debug', concept:'type-concept' };
""" + js_modules + """
const TOTAL_QS = Object.values(MODULES).reduce((s,m)=>s+m.total,0);

const saved = JSON.parse(localStorage.getItem(LS_KEY) || '{}');
let currentMid = 'm01';
let rendered = {};

function renderModule(mid) {
  const m = MODULES[mid];
  const tbody = document.getElementById(mid + '-tbody');
  if (!tbody || !m) return;
  tbody.innerHTML = '';
  m.questions.forEach((q, i) => {
    const key = mid + '_q' + i;
    const isDone = saved[key] === true;
    const tr = document.createElement('tr');
    tr.className = 'q-row' + (isDone ? ' checked' : '');
    tr.innerHTML = '<td><div class="q-check'+(isDone?' checked':'')+'" onclick="toggleQ(\\''+key+'\\',\\''+mid+'\\',this)"></div></td>'+
      '<td class="q-num">Q'+String(i+1).padStart(2,'0')+'</td>'+
      '<td class="q-text">'+escapeHtml(q.t)+'</td>'+
      '<td><span class="q-type '+(TYPE_MAP[q.type]||'type-concept')+'">'+(q.type||'concept')+'</span></td>';
    tbody.appendChild(tr);
  });
  updateModuleProgress(mid);
}

function escapeHtml(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

function toggleQ(key, mid, el) {
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
  const m = MODULES[mid];
  if (!m) return;
  let done = 0;
  for (let i = 0; i < m.total; i++) if (saved[mid + '_q' + i]) done++;
  const pct = Math.round(done / m.total * 100);
  const prog = document.getElementById(mid + '-prog');
  const bar = document.getElementById(mid + '-bar');
  const barpct = document.getElementById(mid + '-barpct');
  const status = document.getElementById(mid + '-status');
  if (prog) prog.textContent = done + '/' + m.total;
  if (bar) bar.style.width = pct + '%';
  if (barpct) barpct.textContent = pct + '%';
  if (status) {
    if (done === 0) { status.textContent = 'Not started'; status.className = 'module-status status-notstarted'; }
    else if (done === m.total) { status.textContent = 'Complete ✓'; status.className = 'module-status status-done'; }
    else { status.textContent = 'In progress'; status.className = 'module-status status-inprogress'; }
  }
}

function updateGlobal() {
  let totalDone = 0, modulesDone = 0;
  Object.keys(MODULES).forEach(mid => {
    const m = MODULES[mid];
    let done = 0;
    for (let i = 0; i < m.total; i++) if (saved[mid + '_q' + i]) done++;
    totalDone += done;
    if (done === m.total) modulesDone++;
  });
  const pct = Math.round(totalDone / TOTAL_QS * 100);
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

function initTabs(root) {
  root.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const panel = btn.dataset.tab;
      const wrap = btn.closest('.detail-panel');
      wrap.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b === btn));
      wrap.querySelectorAll('.tab-panel').forEach(p => p.classList.toggle('active', p.dataset.panel === panel));
    });
  });
}

document.querySelectorAll('.module-view').forEach(initTabs);

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
  updateGlobal();
  Object.keys(MODULES).forEach(mid => updateModuleProgress(mid));
  bootFromHash();
});
"""
    app_js = app_js.replace("__LS_KEY__", LS_KEY)

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
      <div class="stat"><div class="stat-num">720+</div><div class="stat-label">Checklist</div></div>
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
    <span class="chip"><strong id="total-done">0</strong> / {720} checklist items done</span>
    <span class="chip"><strong id="pct-done">0%</strong> overall</span>
    <span class="chip"><strong id="modules-done">0</strong> / 30 modules complete</span>
    <span class="chip" style="flex:1;min-width:200px;max-width:420px;display:flex;align-items:center;gap:10px">
      <span style="flex:1;height:4px;background:var(--border);border-radius:2px;overflow:hidden">
        <span id="main-bar" style="display:block;height:100%;width:0%;background:var(--accent);transition:width .3s"></span>
      </span>
      <span id="bar-pct" style="min-width:36px">0%</span>
    </span>
  </div>
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
</body>
</html>
"""

    OUT.write_text(html_out, encoding="utf-8")
    print(f"Wrote {OUT} ({len(html_out):,} bytes)")


if __name__ == "__main__":
    main()
