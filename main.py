"""
OS Semaphore Visualizer — Streamlit Cloud compatible
Step-by-step state machine. No background threads.
"""
import streamlit as st
import random
import time
from collections import deque
from datetime import datetime

st.set_page_config(page_title="OS Semaphore Visualizer", page_icon="🔐", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
[data-testid="stAppViewContainer"] { background: #0d1117; }
[data-testid="stSidebar"] { background: #010409; border-right: 1px solid #21262d; }
[data-testid="stSidebar"] * { color: #c9d1d9 !important; }
[data-testid="stSidebar"] .stSlider label,
[data-testid="stSidebar"] .stSelectbox label { color: #8b949e !important; font-size: 0.8rem; }
h1,h2,h3 { color: #e6edf3; }
.stButton > button {
  background: #21262d !important; border: 1px solid #30363d !important;
  color: #c9d1d9 !important; border-radius: 6px !important;
  font-size: 0.82rem !important; font-weight: 600 !important; padding: 4px 14px !important;
}
.stButton > button:hover { background: #30363d !important; border-color: #58a6ff !important; color: #58a6ff !important; }
.stProgress > div > div > div { background: #1f6feb !important; border-radius: 4px !important; }
hr { border-color: #21262d; margin: 0.5rem 0; }

/* ── Variables bar ── */
.vars-bar {
  display: flex; flex-wrap: wrap; gap: 10px; align-items: center;
  background: #010409; border: 1px solid #21262d; border-radius: 10px;
  padding: 12px 16px; margin-bottom: 14px;
}
.var-chip {
  display: flex; flex-direction: column; align-items: center;
  background: #161b22; border: 1px solid #30363d; border-radius: 8px;
  padding: 8px 14px; min-width: 80px; position: relative;
}
.var-chip-name {
  font-family: 'JetBrains Mono', monospace; font-size: 0.7rem;
  color: #8b949e; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 2px;
}
.var-chip-val {
  font-family: 'JetBrains Mono', monospace; font-size: 1.55rem; font-weight: 700; line-height: 1.1;
}
.var-chip-status { font-size: 0.62rem; margin-top: 3px; letter-spacing: 0.04em; font-weight: 600; }
.var-chip.green  { border-color: #238636; }
.var-chip.green  .var-chip-val { color: #3fb950; }
.var-chip.green  .var-chip-status { color: #3fb950; }
.var-chip.red    { border-color: #b62324; }
.var-chip.red    .var-chip-val { color: #f85149; }
.var-chip.red    .var-chip-status { color: #f85149; }
.var-chip.amber  { border-color: #9e6a03; }
.var-chip.amber  .var-chip-val { color: #d29922; }
.var-chip.amber  .var-chip-status { color: #d29922; }
.var-chip.blue   { border-color: #1f6feb; }
.var-chip.blue   .var-chip-val { color: #58a6ff; }
.var-chip.blue   .var-chip-status { color: #58a6ff; }

/* ── Thread lane ── */
.lanes-wrap { display: flex; flex-direction: column; gap: 8px; margin-bottom: 14px; }
.lane {
  display: grid; grid-template-columns: 54px 1fr 110px;
  align-items: center; gap: 0;
  background: #161b22; border: 1px solid #21262d; border-radius: 8px;
  overflow: hidden; height: 48px;
}
.lane.lane-running  { border-color: #1f6feb; background: #0d1f38; }
.lane.lane-waiting  { border-color: #6e40c9; background: #1a0f2e; }
.lane.lane-idle     { border-color: #21262d; background: #161b22; }

.lane-id {
  font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; font-weight: 700;
  text-align: center; padding: 0 6px; border-right: 1px solid #21262d;
  height: 100%; display: flex; align-items: center; justify-content: center;
}
.lane-running  .lane-id { color: #58a6ff; border-color: #1f6feb; }
.lane-waiting  .lane-id { color: #d2a8ff; border-color: #6e40c9; }
.lane-idle     .lane-id { color: #8b949e; }

/* Phase pipeline inside lane */
.lane-phases {
  display: flex; align-items: center; gap: 0; padding: 0 10px;
  overflow-x: auto; scrollbar-width: none; height: 100%;
}
.lane-phases::-webkit-scrollbar { display: none; }
.phase-step {
  display: flex; align-items: center; gap: 0;
  font-family: 'JetBrains Mono', monospace; font-size: 0.66rem;
  white-space: nowrap;
}
.phase-bubble {
  padding: 3px 8px; border-radius: 4px; border: 1px solid #30363d;
  color: #484f58; background: #0d1117;
}
.phase-bubble.active-p { background: #1f3a5c; border-color: #1f6feb; color: #58a6ff; font-weight: 700; }
.phase-bubble.active-v { background: #1a3a1f; border-color: #238636; color: #3fb950; font-weight: 700; }
.phase-bubble.done     { background: #161b22; border-color: #21262d; color: #30363d; text-decoration: line-through; }
.phase-arrow { color: #30363d; margin: 0 2px; font-size: 0.6rem; }
.phase-arrow.active { color: #58a6ff; }

.lane-badge {
  font-size: 0.65rem; font-weight: 700; text-align: center; padding: 0 8px;
  border-left: 1px solid #21262d; height: 100%;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 1px; letter-spacing: 0.06em;
}
.lane-running  .lane-badge { color: #58a6ff; border-color: #1f6feb; }
.lane-waiting  .lane-badge { color: #d2a8ff; border-color: #6e40c9; }
.lane-idle     .lane-badge { color: #484f58; }
.badge-dot { width: 7px; height: 7px; border-radius: 50%; }
.dot-running { background: #1f6feb; box-shadow: 0 0 6px #1f6feb; }
.dot-waiting { background: #6e40c9; box-shadow: 0 0 6px #6e40c9; }
.dot-idle    { background: #30363d; }

/* ── Buffer ── */
.buffer-wrap { display: flex; gap: 6px; flex-wrap: wrap; margin: 6px 0; }
.buf-slot {
  width: 44px; height: 40px; border-radius: 6px; display: flex; align-items: center;
  justify-content: center; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; font-weight: 700;
  transition: all 0.2s;
}
.buf-slot.full  { background: #0d2f5c; border: 1.5px solid #1f6feb; color: #58a6ff; }
.buf-slot.empty { background: #0d1117; border: 1.5px dashed #21262d; color: #21262d; }

/* ── Code panel ── */
.code-block {
  background: #010409; border: 1px solid #21262d; border-radius: 8px;
  padding: 12px 14px; font-family: 'JetBrains Mono', monospace;
  font-size: 0.76rem; line-height: 1.8; overflow-x: auto;
}
.cl { display: block; padding: 1px 6px; border-left: 3px solid transparent;
      white-space: pre; border-radius: 2px; transition: background 0.15s; }
.cl-p { background: rgba(31,111,235,0.18); border-left-color: #1f6feb; }
.cl-v { background: rgba(35,134,54,0.18);  border-left-color: #238636; }
.ck  { color: #ff7b72; font-weight: 700; }
.cf  { color: #d2a8ff; }
.cc  { color: #6e7681; font-style: italic; }
.cn  { color: #79c0ff; }
.cv  { color: #ffa657; font-weight: 700; }
.cs  { color: #a5d6ff; }

/* ── Log ── */
.log-wrap {
  background: #010409; border: 1px solid #21262d; border-radius: 8px;
  padding: 8px 12px; height: 200px; overflow-y: auto; font-family: 'JetBrains Mono', monospace;
}
.log-line { font-size: 0.7rem; color: #8b949e; padding: 1px 0; border-bottom: 1px solid #0d1117; }
.lp  { color: #f0883e; font-weight: 700; }
.lv  { color: #3fb950; font-weight: 700; }
.lt  { color: #58a6ff; }
.lc  { color: #d2a8ff; }
.lts { color: #30363d; }

/* ── Section labels ── */
.sec-label {
  font-size: 0.7rem; font-weight: 700; color: #8b949e; text-transform: uppercase;
  letter-spacing: 0.1em; margin: 12px 0 6px; display: flex; align-items: center; gap: 6px;
}
.sec-label::after { content: ''; flex: 1; height: 1px; background: #21262d; }

/* ── Stats row ── */
.stats-row { display: flex; gap: 8px; margin-bottom: 14px; }
.stat-box {
  flex: 1; background: #161b22; border: 1px solid #21262d; border-radius: 8px;
  padding: 10px 6px; text-align: center;
}
.stat-val { font-family: 'JetBrains Mono', monospace; font-size: 1.4rem; font-weight: 700; }
.stat-lbl { font-size: 0.62rem; color: #8b949e; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 2px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Session state defaults
# ─────────────────────────────────────────────────────────────────────────────

SCENARIOS = [
    "Mutex (Critical Section)",
    "Producer / Consumer",
    "Multi-Producer / Multi-Consumer",
    "Counting Semaphore",
]

def _def(k, v):
    if k not in st.session_state:
        st.session_state[k] = v

_def("running",      False)
_def("scenario",     SCENARIOS[0])
_def("threads",      [])
_def("sems",         {})
_def("buffer",       [])
_def("buf_size",     5)
_def("log",          deque(maxlen=120))
_def("p_calls",      0)
_def("v_calls",      0)
_def("mutex_owner",  None)
_def("step",         0)
_def("speed",        2)

# ─────────────────────────────────────────────────────────────────────────────
# Semaphore helpers (synchronous — runs in main thread)
# ─────────────────────────────────────────────────────────────────────────────

def add_log(msg):
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    st.session_state.log.appendleft(
        f'<span class="lts">[{ts}]</span> {msg}'
    )

def sem_P(name, tid):
    if st.session_state.sems.get(name, 0) > 0:
        st.session_state.sems[name] -= 1
        add_log(f'<span class="lp">P({name})</span> ← <span class="lt">{tid}</span>'
                f'  <span class="lts">→ {name}={st.session_state.sems[name]}</span>')
        st.session_state.p_calls += 1
        return True
    return False

def sem_V(name, tid):
    st.session_state.sems[name] = st.session_state.sems.get(name, 0) + 1
    add_log(f'<span class="lv">V({name})</span> ← <span class="lt">{tid}</span>'
            f'  <span class="lts">→ {name}={st.session_state.sems[name]}</span>')
    st.session_state.v_calls += 1

def rt(lo, hi, spd):
    return max(1, random.randint(lo, hi) // spd)

# ─────────────────────────────────────────────────────────────────────────────
# Phase definitions per role
# ─────────────────────────────────────────────────────────────────────────────

ROLE_PHASES = {
    "mutex":    ["sleep", "P(mutex)", "critical", "V(mutex)"],
    "producer": ["sleep", "P(empty)", "P(mutex)", "insert",  "V(mutex)", "V(full)"],
    "consumer": ["sleep", "P(full)",  "P(mutex)", "remove",  "V(mutex)", "V(empty)"],
    "worker":   ["sleep", "P(resource)", "use",   "V(resource)"],
}

# Map phase name → highlight type ('p' or 'v' or '')
PHASE_HL = {
    "P(mutex)": "p", "P(empty)": "p", "P(full)": "p", "P(resource)": "p",
    "critical": "p", "insert": "p", "remove": "p", "use": "p",
    "V(mutex)": "v", "V(full)": "v", "V(empty)": "v", "V(resource)": "v",
}

# Map phase → code line key
PHASE_LINE = {
    "P(mutex)":    "p_mutex",
    "P(empty)":    "p_empty",
    "P(full)":     "p_full",
    "P(resource)": "p_res",
    "critical":    "crit",
    "insert":      "insert",
    "remove":      "remove",
    "use":         "use",
    "V(mutex)":    "v_mutex",
    "V(full)":     "v_full",
    "V(empty)":    "v_empty",
    "V(resource)": "v_res",
}

# ─────────────────────────────────────────────────────────────────────────────
# Init simulation
# ─────────────────────────────────────────────────────────────────────────────

def init_sim(scenario, n_threads, n_prod, n_cons, buf_size, max_conc, speed):
    st.session_state.threads      = []
    st.session_state.sems         = {}
    st.session_state.buffer       = []
    st.session_state.buf_size     = buf_size
    st.session_state.log          = deque(maxlen=120)
    st.session_state.p_calls      = 0
    st.session_state.v_calls      = 0
    st.session_state.mutex_owner  = None
    st.session_state.step         = 0
    st.session_state.speed        = speed

    def make(tid, role):
        phases = ROLE_PHASES[role]
        return {
            "id":          tid,
            "role":        role,
            "phase_idx":   0,          # index into ROLE_PHASES[role]
            "phase":       phases[0],  # "sleep"
            "state":       "idle",
            "sleep_ticks": random.randint(2, 8),
            "work_ticks":  0,
            "item":        None,
            "phase_done":  set(),      # indices already completed (for rendering)
        }

    if scenario == "Mutex (Critical Section)":
        st.session_state.sems = {"mutex": 1}
        for i in range(1, n_threads + 1):
            st.session_state.threads.append(make(f"T{i}", "mutex"))

    elif scenario in ("Producer / Consumer", "Multi-Producer / Multi-Consumer"):
        st.session_state.sems = {"empty": buf_size, "full": 0, "mutex": 1}
        for i in range(1, n_prod + 1):
            st.session_state.threads.append(make(f"P{i}", "producer"))
        for i in range(1, n_cons + 1):
            st.session_state.threads.append(make(f"C{i}", "consumer"))

    else:
        st.session_state.sems = {"resource": max_conc}
        for i in range(1, n_threads + 1):
            st.session_state.threads.append(make(f"W{i}", "worker"))

# ─────────────────────────────────────────────────────────────────────────────
# Tick — advance each thread one step
# ─────────────────────────────────────────────────────────────────────────────

def tick():
    spd = st.session_state.speed
    for t in st.session_state.threads:
        role  = t["role"]
        phase = t["phase"]
        tid   = t["id"]
        phases = ROLE_PHASES[role]

        def next_phase():
            t["phase_done"].add(t["phase_idx"])
            t["phase_idx"] = (t["phase_idx"] + 1) % len(phases)
            t["phase"]     = phases[t["phase_idx"]]
            if t["phase_idx"] == 0:   # wrapped back to sleep
                t["phase_done"] = set()

        # ── sleep ────────────────────────────────────────────────────────
        if phase == "sleep":
            t["state"] = "idle"
            if t["sleep_ticks"] > 0:
                t["sleep_ticks"] -= 1
            else:
                next_phase()
                if role == "producer":
                    t["item"] = random.randint(10, 99)
                elif role in ("mutex", "worker"):
                    add_log(f'<span class="lt">{tid}</span> <span class="lts">→ requesting...</span>')

        # ── P operations (try to acquire) ────────────────────────────────
        elif phase.startswith("P("):
            sem_name = phase[2:-1]
            t["state"] = "running"
            if sem_P(sem_name, tid):
                if sem_name == "mutex":
                    st.session_state.mutex_owner = tid
                t["state"] = "running"
                next_phase()
            else:
                t["state"] = "waiting"

        # ── V operations ─────────────────────────────────────────────────
        elif phase.startswith("V("):
            sem_name = phase[2:-1]
            t["state"] = "running"
            sem_V(sem_name, tid)
            if sem_name == "mutex" and st.session_state.mutex_owner == tid:
                st.session_state.mutex_owner = None
            next_phase()
            if t["phase"] == "sleep":
                t["sleep_ticks"] = rt(3, 9, spd)
                t["state"] = "idle"

        # ── critical section / use (timed work) ──────────────────────────
        elif phase in ("critical", "use"):
            t["state"] = "running"
            if t["work_ticks"] == 0:
                t["work_ticks"] = rt(3, 8, spd)
                add_log(f'<span class="lt">{tid}</span> <span class="lts">🔐 in {phase}</span>')
            else:
                t["work_ticks"] -= 1
                if t["work_ticks"] == 0:
                    next_phase()

        # ── insert ───────────────────────────────────────────────────────
        elif phase == "insert":
            t["state"] = "running"
            buf = st.session_state.buffer
            if len(buf) < st.session_state.buf_size:
                buf.append(t["item"])
            add_log(f'<span class="lt">{tid}</span> produced <b>{t["item"]}</b>'
                    f'  <span class="lts">buf={len(buf)}</span>')
            next_phase()

        # ── remove ───────────────────────────────────────────────────────
        elif phase == "remove":
            t["state"] = "running"
            buf  = st.session_state.buffer
            item = buf.pop(0) if buf else "?"
            add_log(f'<span class="lc">{tid}</span> consumed <b>{item}</b>'
                    f'  <span class="lts">buf={len(buf)}</span>')
            next_phase()
            t["sleep_ticks"] = rt(4, 10, spd)

    st.session_state.step += 1

# ─────────────────────────────────────────────────────────────────────────────
# Render helpers
# ─────────────────────────────────────────────────────────────────────────────

def render_vars_bar():
    sems = st.session_state.sems
    if not sems:
        return ""

    html = '<div class="vars-bar">'
    html += '<span style="font-size:0.7rem;font-weight:700;color:#8b949e;letter-spacing:0.08em;text-transform:uppercase">Variables</span>'

    for name, val in sems.items():
        if val <= 0:   color, status = "red",   "BLOCKED"
        elif val == 1: color, status = "green",  "FREE"
        else:          color, status = "blue",   f"{val} FREE"
        html += (f'<div class="var-chip {color}">'
                 f'<div class="var-chip-name">{name}</div>'
                 f'<div class="var-chip-val">{val}</div>'
                 f'<div class="var-chip-status">{"🔴" if val<=0 else "🟢"} {status}</div>'
                 f'</div>')

    # buffer fill if prod-cons
    buf = st.session_state.buffer
    bsz = st.session_state.buf_size
    if bsz > 0 and st.session_state.threads and st.session_state.threads[0]["role"] in ("producer","consumer"):
        pct = int(len(buf)/bsz*100)
        color = "amber" if pct > 0 else "red" if pct == 100 else "blue"
        html += (f'<div class="var-chip {color}">'
                 f'<div class="var-chip-name">buffer</div>'
                 f'<div class="var-chip-val">{len(buf)}/{bsz}</div>'
                 f'<div class="var-chip-status">{"▓"*min(5,int(pct/20))}{"░"*(5-min(5,int(pct/20)))} {pct}%</div>'
                 f'</div>')

    # step counter
    html += (f'<div class="var-chip" style="margin-left:auto">'
             f'<div class="var-chip-name">step</div>'
             f'<div class="var-chip-val" style="color:#8b949e">{st.session_state.step}</div>'
             f'<div class="var-chip-status" style="color:#30363d">ticks</div>'
             f'</div>')

    html += '</div>'
    return html


def render_thread_lanes():
    threads = st.session_state.threads
    if not threads:
        return '<div style="color:#484f58;font-size:.85rem;padding:12px">No threads — press Start.</div>'

    html = '<div class="lanes-wrap">'
    for t in sorted(threads, key=lambda x: x["id"]):
        tid    = t["id"]
        state  = t["state"]
        role   = t["role"]
        phases = ROLE_PHASES[role]
        cur_ph = t["phase"]
        done   = t["phase_done"]

        lane_cls = {"running": "lane-running", "waiting": "lane-waiting"}.get(state, "lane-idle")
        dot_cls  = {"running": "dot-running",  "waiting": "dot-waiting"}.get(state,  "dot-idle")

        # owner marker
        owner_icon = " 🔐" if tid == st.session_state.mutex_owner else ""

        # Phase pipeline
        phases_html = ""
        for i, ph in enumerate(phases):
            is_cur  = ph == cur_ph
            is_done = i in done
            hl      = PHASE_HL.get(ph, "")

            if is_done:
                bub_cls = "phase-bubble done"
            elif is_cur and hl == "p":
                bub_cls = "phase-bubble active-p"
            elif is_cur and hl == "v":
                bub_cls = "phase-bubble active-v"
            elif is_cur:
                bub_cls = "phase-bubble active-p"
            else:
                bub_cls = "phase-bubble"

            arrow_cls = "phase-arrow active" if i < len(phases)-1 and phases[i+1] == cur_ph else "phase-arrow"
            phases_html += f'<span class="phase-step"><span class="{bub_cls}">{ph}</span>'
            if i < len(phases) - 1:
                phases_html += f'<span class="{arrow_cls}">›</span>'
            phases_html += '</span>'

        state_label = state.upper()
        if state == "waiting":
            state_label = "BLOCKED"

        html += (f'<div class="lane {lane_cls}">'
                 f'<div class="lane-id">{tid}{owner_icon}</div>'
                 f'<div class="lane-phases">{phases_html}</div>'
                 f'<div class="lane-badge">'
                 f'<div class="badge-dot {dot_cls}"></div>'
                 f'{state_label}</div>'
                 f'</div>')

    html += '</div>'
    return html


def render_buffer():
    buf  = st.session_state.buffer
    bsz  = st.session_state.buf_size
    html = '<div class="buffer-wrap">'
    for i in range(bsz):
        if i < len(buf):
            html += f'<div class="buf-slot full">{buf[i]}</div>'
        else:
            html += '<div class="buf-slot empty">·</div>'
    html += '</div>'
    return html


def render_log():
    entries = list(st.session_state.log)[:35]
    html = '<div class="log-wrap">'
    for e in entries:
        html += f'<div class="log-line">{e}</div>'
    if not entries:
        html += '<div class="log-line" style="color:#21262d">No events yet — press Start.</div>'
    html += '</div>'
    return html


def active_line_keys():
    keys = set()
    for t in st.session_state.threads:
        k = PHASE_LINE.get(t["phase"], "")
        if k:
            keys.add(k)
    return keys


def render_code(scenario, active_keys):
    kw = lambda s: f'<span class="ck">{s}</span>'
    fn = lambda s: f'<span class="cf">{s}</span>'
    cm = lambda s: f'<span class="cc"># {s}</span>'
    nu = lambda s: f'<span class="cn">{s}</span>'
    cv = lambda s: f'<span class="cv">{s}</span>'

    def L(key, code, ht=""):
        matched = key and key in active_keys
        cls = ("cl-p" if ht == "p" else "cl-v") if matched else ""
        return f'<span class="cl {cls}"> {code}</span>\n'

    html = '<div class="code-block">'

    if scenario == "Mutex (Critical Section)":
        html += L("",       f'{kw("mutex")} = {fn("Semaphore")}({nu("1")})')
        html += L("",       "")
        html += L("",       f'{kw("def")} {fn("thread")}(id):')
        html += L("",       f'    {cm("non-critical work...")}')
        html += L("p_mutex",f'    {cv("P(mutex)")}  {cm("wait · decrement")}', "p")
        html += L("crit",   f'    critical_section()  {cm("🔐 exclusive")}', "p")
        html += L("v_mutex",f'    {cv("V(mutex)")}  {cm("signal · increment")}', "v")
        html += L("",       "")
        html += L("",       f'{kw("def")} {fn("P")}(sem):')
        html += L("",       f'    {kw("while")} sem.value ≤ {nu("0")}: block()')
        html += L("",       f'    sem.value -= {nu("1")}')
        html += L("",       "")
        html += L("",       f'{kw("def")} {fn("V")}(sem):')
        html += L("",       f'    sem.value += {nu("1")}')
        html += L("",       f'    wakeup_next()')

    elif scenario in ("Producer / Consumer", "Multi-Producer / Multi-Consumer"):
        html += L("",       f'{kw("empty")} = {fn("Semaphore")}({nu("N")})  {cm("free slots")}')
        html += L("",       f'{kw("full")}  = {fn("Semaphore")}({nu("0")})  {cm("filled slots")}')
        html += L("",       f'{kw("mutex")} = {fn("Semaphore")}({nu("1")})  {cm("mutual exclusion")}')
        html += L("",       "")
        html += L("",       f'{kw("def")} {fn("producer")}():')
        html += L("",       f'    item = produce()')
        html += L("p_empty",f'    {cv("P(empty)")}  {cm("wait: free slot?")}', "p")
        html += L("p_mutex",f'    {cv("P(mutex)")}  {cm("lock buffer")}', "p")
        html += L("insert", f'    buffer.append(item)', "p")
        html += L("v_mutex",f'    {cv("V(mutex)")}  {cm("unlock")}', "v")
        html += L("v_full", f'    {cv("V(full)")}   {cm("signal: new item")}', "v")
        html += L("",       "")
        html += L("",       f'{kw("def")} {fn("consumer")}():')
        html += L("p_full", f'    {cv("P(full)")}   {cm("wait: item exists?")}', "p")
        html += L("p_mutex",f'    {cv("P(mutex)")}  {cm("lock buffer")}', "p")
        html += L("remove", f'    item = buffer.pop(0)', "p")
        html += L("v_mutex",f'    {cv("V(mutex)")}  {cm("unlock")}', "v")
        html += L("v_empty",f'    {cv("V(empty)")}  {cm("signal: slot free")}', "v")
        html += L("",       f'    consume(item)')

    else:
        html += L("",      f'{kw("resource")} = {fn("Semaphore")}(MAX)')
        html += L("",      "")
        html += L("",      f'{kw("def")} {fn("worker")}(id):')
        html += L("",      f'    {cm("prepare...")}')
        html += L("p_res", f'    {cv("P(resource)")}  {cm("wait: slot free?")}', "p")
        html += L("use",   f'    use_resource()       {cm("concurrent zone")}', "p")
        html += L("v_res", f'    {cv("V(resource)")}  {cm("release slot")}', "v")
        html += L("",      f'    {cm("continue...")}')

    html += '</div>'
    return html

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ⚙️ Config")
    st.markdown("---")
    scenario = st.selectbox("Scenario", SCENARIOS,
                            index=SCENARIOS.index(st.session_state.scenario)
                            if st.session_state.scenario in SCENARIOS else 0,
                            disabled=st.session_state.running)
    st.session_state.scenario = scenario
    st.markdown("---")

    if scenario == "Mutex (Critical Section)":
        n_threads = st.slider("Threads", 2, 6, 3, disabled=st.session_state.running)
        n_prod = n_cons = buf_size = 0; max_conc = 1
    elif scenario in ("Producer / Consumer", "Multi-Producer / Multi-Consumer"):
        dp = 1 if "Multi" not in scenario else 3
        dc = 1 if "Multi" not in scenario else 3
        n_prod   = st.slider("Producers", 1, 5, dp, disabled=st.session_state.running)
        n_cons   = st.slider("Consumers", 1, 5, dc, disabled=st.session_state.running)
        buf_size = st.slider("Buffer size", 2, 10, 5, disabled=st.session_state.running)
        n_threads = n_prod + n_cons; max_conc = 1
    else:
        n_threads = st.slider("Workers", 2, 8, 5, disabled=st.session_state.running)
        max_conc  = st.slider("Max concurrent (N)", 1, 5, 2, disabled=st.session_state.running)
        n_prod = n_cons = buf_size = 0

    st.markdown("---")
    speed = st.slider("⚡ Speed", 1, 6, 2,
                      help="Steps executed per tick. 1 = slowest, 6 = fastest.")
    if st.session_state.running:
        st.session_state.speed = speed

    st.markdown("---")
    st.markdown("**P(sem)** — wait / decrement  \n`while sem≤0: block()`  \n`sem -= 1`")
    st.markdown("**V(sem)** — signal / increment  \n`sem += 1`  \n`wakeup_next()`")
    st.markdown("---")
    st.markdown("""
<div style="font-size:.75rem;line-height:2">
<span style="background:#0d2f5c;border:1px solid #1f6feb;color:#58a6ff;padding:2px 8px;border-radius:4px;font-family:monospace">running</span>  executing<br>
<span style="background:#1a0f2e;border:1px solid #6e40c9;color:#d2a8ff;padding:2px 8px;border-radius:4px;font-family:monospace">blocked</span>  waiting on P()<br>
<span style="background:#161b22;border:1px solid #21262d;color:#8b949e;padding:2px 8px;border-radius:4px;font-family:monospace">idle</span>  sleeping
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<div style="background:#010409;border:1px solid #21262d;border-radius:10px;
            padding:14px 20px;margin-bottom:16px;display:flex;align-items:center;gap:12px">
  <div>
    <div style="font-size:1.35rem;font-weight:700;color:#e6edf3">🔐 OS Semaphore Visualizer</div>
    <div style="font-size:.78rem;color:#8b949e;margin-top:2px">
      Step-by-step · &nbsp;<span style="color:#ffa657;font-family:monospace;font-weight:700">P(sem)</span>
      &nbsp;= wait / decrement &nbsp;·&nbsp;
      <span style="color:#3fb950;font-family:monospace;font-weight:700">V(sem)</span>
      &nbsp;= signal / increment
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Controls
# ─────────────────────────────────────────────────────────────────────────────

c1, c2, c3, c4 = st.columns([1, 1, 1, 5])
with c1:
    if st.button("▶ Start", disabled=st.session_state.running):
        init_sim(scenario, n_threads, n_prod, n_cons,
                 buf_size if buf_size else 5, max_conc, speed)
        st.session_state.running = True
        st.rerun()
with c2:
    if st.button("⏹ Stop", disabled=not st.session_state.running):
        st.session_state.running = False
        st.rerun()
with c3:
    if st.button("↺ Reset"):
        st.session_state.running = False
        st.session_state.threads = []
        st.session_state.sems    = {}
        st.session_state.buffer  = []
        st.session_state.log     = deque(maxlen=120)
        st.session_state.p_calls = 0
        st.session_state.v_calls = 0
        st.session_state.step    = 0
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# Advance simulation
# ─────────────────────────────────────────────────────────────────────────────

if st.session_state.running:
    for _ in range(max(1, st.session_state.speed)):
        tick()

# ─────────────────────────────────────────────────────────────────────────────
# ── Variables bar (full width, top) ──────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

st.markdown(render_vars_bar(), unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# ── Stats row ────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

waiting_n = sum(1 for t in st.session_state.threads if t["state"] == "waiting")
running_n = sum(1 for t in st.session_state.threads if t["state"] == "running")
idle_n    = sum(1 for t in st.session_state.threads if t["state"] == "idle")

st.markdown(f"""
<div class="stats-row">
  <div class="stat-box">
    <div class="stat-val" style="color:#58a6ff">{running_n}</div>
    <div class="stat-lbl">running</div>
  </div>
  <div class="stat-box">
    <div class="stat-val" style="color:#d2a8ff">{waiting_n}</div>
    <div class="stat-lbl">blocked</div>
  </div>
  <div class="stat-box">
    <div class="stat-val" style="color:#8b949e">{idle_n}</div>
    <div class="stat-lbl">idle</div>
  </div>
  <div class="stat-box">
    <div class="stat-val" style="color:#f0883e">{st.session_state.p_calls}</div>
    <div class="stat-lbl">P() calls</div>
  </div>
  <div class="stat-box">
    <div class="stat-val" style="color:#3fb950">{st.session_state.v_calls}</div>
    <div class="stat-lbl">V() calls</div>
  </div>
  <div class="stat-box">
    <div class="stat-val" style="color:#6e7681">{st.session_state.step}</div>
    <div class="stat-lbl">steps</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# ── Main columns ─────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

left, right = st.columns([3, 2])

with left:
    # Thread lanes
    st.markdown('<div class="sec-label">Thread execution lanes</div>', unsafe_allow_html=True)
    st.markdown(render_thread_lanes(), unsafe_allow_html=True)

    # Buffer (prod-cons only)
    threads = st.session_state.threads
    if threads and threads[0]["role"] in ("producer", "consumer"):
        st.markdown('<div class="sec-label">Shared buffer</div>', unsafe_allow_html=True)
        st.markdown(render_buffer(), unsafe_allow_html=True)
        buf = st.session_state.buffer
        bsz = st.session_state.buf_size
        pct = len(buf) / bsz if bsz else 0
        st.progress(pct)

    # Log
    st.markdown('<div class="sec-label">Event log</div>', unsafe_allow_html=True)
    st.markdown(render_log(), unsafe_allow_html=True)

with right:
    st.markdown('<div class="sec-label">Pseudocode — live highlighted</div>', unsafe_allow_html=True)
    active_keys = active_line_keys()
    st.markdown(render_code(scenario, active_keys), unsafe_allow_html=True)

    if scenario == "Counting Semaphore" and st.session_state.threads:
        st.markdown('<div class="sec-label" style="margin-top:14px">Concurrency gauge</div>', unsafe_allow_html=True)
        used = sum(1 for t in st.session_state.threads if t["phase"] == "use")
        st.progress(min(used / max(max_conc, 1), 1.0))
        st.markdown(f'<span style="font-family:monospace;font-size:.78rem;color:#8b949e">'
                    f'{used} / {max_conc} slots in use</span>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Auto-rerun loop
# ─────────────────────────────────────────────────────────────────────────────

if st.session_state.running:
    time.sleep(0.22)
    st.rerun()