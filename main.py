"""
OS Semaphore Visualizer — Streamlit Cloud compatible
Step-by-step state machine. Manual step + auto-run with speed control.
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

/* ── Step explanation box ── */
.step-box {
  background: #0d1f38; border: 1px solid #1f6feb; border-radius: 10px;
  padding: 14px 18px; margin-bottom: 14px;
}
.step-box-num {
  font-family: 'JetBrains Mono', monospace; font-size: 0.68rem;
  color: #58a6ff; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 4px;
}
.step-box-msg {
  font-size: 0.92rem; color: #e6edf3; line-height: 1.55;
}
.step-box-msg .hi-p  { color: #f0883e; font-weight: 700; }
.step-box-msg .hi-v  { color: #3fb950; font-weight: 700; }
.step-box-msg .hi-t  { color: #58a6ff; font-weight: 700; }
.step-box-msg .hi-w  { color: #d2a8ff; font-weight: 700; }

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
.var-chip.flash  { border-color: #d29922 !important; box-shadow: 0 0 8px #d2992240; }

/* ── Thread lane ── */
.lanes-wrap { display: flex; flex-direction: column; gap: 8px; margin-bottom: 14px; }
.lane {
  display: grid; grid-template-columns: 54px 1fr 110px;
  align-items: center; gap: 0;
  background: #161b22; border: 1px solid #21262d; border-radius: 8px;
  overflow: hidden; height: 48px;
}
.lane.lane-running  { border-color: #1f6feb; background: #0d1f38; }
.lane.lane-waiting  { border-color: #b62324; background: #2a0f0f; }
.lane.lane-idle     { border-color: #21262d; background: #161b22; }

.lane-id {
  font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; font-weight: 700;
  text-align: center; padding: 0 6px; border-right: 1px solid #21262d;
  height: 100%; display: flex; align-items: center; justify-content: center;
}
.lane-running  .lane-id { color: #58a6ff; border-color: #1f6feb; }
.lane-waiting  .lane-id { color: #f85149; border-color: #b62324; }
.lane-idle     .lane-id { color: #8b949e; }

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
.phase-bubble.active-p { background: #2d1f00; border-color: #d29922; color: #f0883e; font-weight: 700; }
.phase-bubble.active-v { background: #1a3a1f; border-color: #238636; color: #3fb950; font-weight: 700; }
.phase-bubble.active-w { background: #1a1f3a; border-color: #6e40c9; color: #d2a8ff; font-weight: 700; }
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
.lane-waiting  .lane-badge { color: #f85149; border-color: #b62324; }
.lane-idle     .lane-badge { color: #484f58; }
.badge-dot { width: 7px; height: 7px; border-radius: 50%; }
.dot-running { background: #1f6feb; box-shadow: 0 0 6px #1f6feb; }
.dot-waiting { background: #f85149; box-shadow: 0 0 6px #f85149; }
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
.cl-p { background: rgba(240,136,62,0.18); border-left-color: #d29922; }
.cl-v { background: rgba(35,134,54,0.18);  border-left-color: #238636; }
.cl-w { background: rgba(110,64,201,0.18); border-left-color: #6e40c9; }
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
.log-line.log-new { color: #e6edf3; }
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

_def("running",      False)   # auto-run mode
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
_def("auto_delay",   0.6)     # seconds between auto steps
_def("flash_sems",   set())   # semaphores changed in last step
_def("step_msg",     "Press <b>▶ Step</b> or <b>▶▶ Auto</b> to begin.")
_def("initialized",  False)

# ─────────────────────────────────────────────────────────────────────────────
# Phase / role definitions
# ─────────────────────────────────────────────────────────────────────────────

ROLE_PHASES = {
    "mutex":    ["sleep", "P(mutex)", "critical", "V(mutex)"],
    "producer": ["sleep", "P(empty)", "P(mutex)", "insert",  "V(mutex)", "V(full)"],
    "consumer": ["sleep", "P(full)",  "P(mutex)", "remove",  "V(mutex)", "V(empty)"],
    "worker":   ["sleep", "P(resource)", "use",   "V(resource)"],
}
PHASE_HL = {
    "P(mutex)": "p", "P(empty)": "p", "P(full)": "p", "P(resource)": "p",
    "critical": "w", "insert": "w", "remove": "w", "use": "w",
    "V(mutex)": "v", "V(full)": "v", "V(empty)": "v", "V(resource)": "v",
}
PHASE_LINE = {
    "P(mutex)": "p_mutex", "P(empty)": "p_empty", "P(full)": "p_full",
    "P(resource)": "p_res", "critical": "crit", "insert": "insert",
    "remove": "remove", "use": "use", "V(mutex)": "v_mutex",
    "V(full)": "v_full", "V(empty)": "v_empty", "V(resource)": "v_res",
}

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def add_log(msg, new=False):
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    cls = "log-new" if new else ""
    st.session_state.log.appendleft(
        (f'<span class="lts">[{ts}]</span> {msg}', cls)
    )

def sem_P(name, tid):
    if st.session_state.sems.get(name, 0) > 0:
        st.session_state.sems[name] -= 1
        add_log(
            f'<span class="lp">P({name})</span> ← <span class="lt">{tid}</span>'
            f'  <span class="lts">→ {name}={st.session_state.sems[name]}</span>',
            new=True,
        )
        st.session_state.p_calls += 1
        st.session_state.flash_sems.add(name)
        return True
    return False

def sem_V(name, tid):
    st.session_state.sems[name] = st.session_state.sems.get(name, 0) + 1
    add_log(
        f'<span class="lv">V({name})</span> ← <span class="lt">{tid}</span>'
        f'  <span class="lts">→ {name}={st.session_state.sems[name]}</span>',
        new=True,
    )
    st.session_state.v_calls += 1
    st.session_state.flash_sems.add(name)

def rt(lo, hi):
    return random.randint(lo, hi)

# ─────────────────────────────────────────────────────────────────────────────
# Init simulation
# ─────────────────────────────────────────────────────────────────────────────

def init_sim(scenario, n_threads, n_prod, n_cons, buf_size, max_conc):
    st.session_state.threads      = []
    st.session_state.sems         = {}
    st.session_state.buffer       = []
    st.session_state.buf_size     = buf_size
    st.session_state.log          = deque(maxlen=120)
    st.session_state.p_calls      = 0
    st.session_state.v_calls      = 0
    st.session_state.mutex_owner  = None
    st.session_state.step         = 0
    st.session_state.flash_sems   = set()
    st.session_state.step_msg     = "Simulation ready. Press <b>▶ Step</b> to advance one event."
    st.session_state.initialized  = True

    def make(tid, role):
        phases = ROLE_PHASES[role]
        return {
            "id":          tid,
            "role":        role,
            "phase_idx":   0,
            "phase":       phases[0],
            "state":       "idle",
            "sleep_ticks": random.randint(2, 5),
            "work_ticks":  0,
            "item":        None,
            "phase_done":  set(),
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
# Single tick — one thread advances ONE phase
# ─────────────────────────────────────────────────────────────────────────────

def tick_once():
    """Advance exactly one thread by one phase. Returns a human-readable explanation."""
    st.session_state.flash_sems = set()
    threads = st.session_state.threads
    if not threads:
        return "No threads."

    # prefer non-idle threads first, then pick randomly
    candidates = [t for t in threads if t["state"] != "idle"] or threads
    t = random.choice(candidates)

    role   = t["role"]
    phase  = t["phase"]
    tid    = t["id"]
    phases = ROLE_PHASES[role]
    msg    = ""

    def next_phase():
        t["phase_done"].add(t["phase_idx"])
        t["phase_idx"] = (t["phase_idx"] + 1) % len(phases)
        t["phase"]     = phases[t["phase_idx"]]
        if t["phase_idx"] == 0:
            t["phase_done"] = set()

    # ── sleep ────────────────────────────────────────────────────────────────
    if phase == "sleep":
        t["state"] = "idle"
        if t["sleep_ticks"] > 0:
            t["sleep_ticks"] -= 1
            msg = (f'<span class="hi-t">{tid}</span> is <b>sleeping</b> '
                   f'({t["sleep_ticks"]} ticks remaining before it tries to enter)')
        else:
            next_phase()
            t["state"] = "running"
            if t["role"] == "producer":
                t["item"] = random.randint(10, 99)
                msg = (f'<span class="hi-t">{tid}</span> woke up and produced item '
                       f'<b>{t["item"]}</b> → now attempting <span class="hi-p">{t["phase"]}</span>')
            else:
                msg = (f'<span class="hi-t">{tid}</span> woke up → '
                       f'now attempting <span class="hi-p">{t["phase"]}</span>')

    # ── P operations ─────────────────────────────────────────────────────────
    elif phase.startswith("P("):
        sem_name = phase[2:-1]
        val_before = st.session_state.sems.get(sem_name, 0)
        if sem_P(sem_name, tid):
            if sem_name == "mutex":
                st.session_state.mutex_owner = tid
            t["state"] = "running"
            next_phase()
            val_after = st.session_state.sems[sem_name]
            msg = (f'<span class="hi-t">{tid}</span> called '
                   f'<span class="hi-p">P({sem_name})</span> — '
                   f'<b>{sem_name} was {val_before} &gt; 0</b>, so it decremented to {val_after} '
                   f'and proceeds to <b>{t["phase"]}</b>')
        else:
            t["state"] = "waiting"
            msg = (f'<span class="hi-t">{tid}</span> called '
                   f'<span class="hi-p">P({sem_name})</span> — '
                   f'<b>{sem_name} = 0 (blocked!)</b> Thread must wait until another thread calls '
                   f'<span class="hi-v">V({sem_name})</span>')

    # ── V operations ─────────────────────────────────────────────────────────
    elif phase.startswith("V("):
        sem_name = phase[2:-1]
        sem_V(sem_name, tid)
        if sem_name == "mutex" and st.session_state.mutex_owner == tid:
            st.session_state.mutex_owner = None
        next_phase()
        val_after = st.session_state.sems[sem_name]
        t["state"] = "idle" if t["phase"] == "sleep" else "running"
        if t["phase"] == "sleep":
            t["sleep_ticks"] = rt(3, 6)
        # try to unblock a waiting thread
        unblocked = []
        for other in threads:
            if other is t or other["state"] != "waiting":
                continue
            bph = other["phase"]
            if bph.startswith("P(") and bph[2:-1] == sem_name:
                if st.session_state.sems.get(sem_name, 0) > 0:
                    st.session_state.sems[sem_name] -= 1
                    other["phase_done"].add(other["phase_idx"])
                    other["phase_idx"] = (other["phase_idx"] + 1) % len(ROLE_PHASES[other["role"]])
                    other["phase"]     = ROLE_PHASES[other["role"]][other["phase_idx"]]
                    other["state"]     = "running"
                    if sem_name == "mutex":
                        st.session_state.mutex_owner = other["id"]
                    unblocked.append(other["id"])
                    add_log(
                        f'<span class="lt">{other["id"]}</span> unblocked by '
                        f'<span class="lv">V({sem_name})</span>', new=True
                    )
                    st.session_state.flash_sems.add(sem_name)
        unblock_note = ""
        if unblocked:
            unblock_note = f' → <span class="hi-w">unblocked {", ".join(unblocked)}</span>'
        msg = (f'<span class="hi-t">{tid}</span> called '
               f'<span class="hi-v">V({sem_name})</span> — '
               f'incremented to <b>{val_after}</b>{unblock_note}')

    # ── critical / use (timed work) ──────────────────────────────────────────
    elif phase in ("critical", "use"):
        t["state"] = "running"
        if t["work_ticks"] == 0:
            t["work_ticks"] = rt(2, 4)
            add_log(f'<span class="lt">{tid}</span> entered <span class="lc">{phase}</span>', new=True)
        t["work_ticks"] -= 1
        if t["work_ticks"] == 0:
            next_phase()
            msg = (f'<span class="hi-t">{tid}</span> finished <span class="hi-w">{phase}</span> '
                   f'→ now moves to <span class="hi-v">{t["phase"]}</span>')
        else:
            msg = (f'<span class="hi-t">{tid}</span> is inside <span class="hi-w">{phase}</span> '
                   f'({t["work_ticks"]} tick{"s" if t["work_ticks"]!=1 else ""} of work remaining)')

    # ── insert ───────────────────────────────────────────────────────────────
    elif phase == "insert":
        t["state"] = "running"
        buf = st.session_state.buffer
        if len(buf) < st.session_state.buf_size:
            buf.append(t["item"])
        add_log(
            f'<span class="lt">{tid}</span> inserted <b>{t["item"]}</b>'
            f'  <span class="lts">buf=[{", ".join(str(x) for x in buf)}]</span>', new=True
        )
        msg = (f'<span class="hi-t">{tid}</span> <b>inserted {t["item"]}</b> into the buffer '
               f'(now {len(buf)}/{st.session_state.buf_size} full)')
        next_phase()

    # ── remove ───────────────────────────────────────────────────────────────
    elif phase == "remove":
        t["state"] = "running"
        buf  = st.session_state.buffer
        item = buf.pop(0) if buf else "?"
        add_log(
            f'<span class="lc">{tid}</span> removed <b>{item}</b>'
            f'  <span class="lts">buf=[{", ".join(str(x) for x in buf)}]</span>', new=True
        )
        msg = (f'<span class="hi-t">{tid}</span> <b>removed {item}</b> from the buffer '
               f'(now {len(buf)}/{st.session_state.buf_size} full)')
        next_phase()
        t["sleep_ticks"] = rt(3, 6)

    st.session_state.step += 1
    return msg or "…"

# ─────────────────────────────────────────────────────────────────────────────
# Render helpers
# ─────────────────────────────────────────────────────────────────────────────

def render_step_box():
    msg  = st.session_state.step_msg
    step = st.session_state.step
    label = f"Step {step}" if step > 0 else "Ready"
    return (f'<div class="step-box">'
            f'<div class="step-box-num">{label}</div>'
            f'<div class="step-box-msg">{msg}</div>'
            f'</div>')

def render_vars_bar():
    sems  = st.session_state.sems
    flash = st.session_state.flash_sems
    if not sems:
        return ""
    html = '<div class="vars-bar">'
    html += '<span style="font-size:0.7rem;font-weight:700;color:#8b949e;letter-spacing:0.08em;text-transform:uppercase">Variables</span>'
    for name, val in sems.items():
        if val <= 0:   color, status = "red",   "BLOCKED"
        elif val == 1: color, status = "green",  "FREE"
        else:          color, status = "blue",   f"{val} FREE"
        fl = " flash" if name in flash else ""
        html += (f'<div class="var-chip {color}{fl}">'
                 f'<div class="var-chip-name">{name}</div>'
                 f'<div class="var-chip-val">{val}</div>'
                 f'<div class="var-chip-status">{"🔴" if val<=0 else "🟢"} {status}</div>'
                 f'</div>')
    buf = st.session_state.buffer
    bsz = st.session_state.buf_size
    if bsz > 0 and st.session_state.threads and st.session_state.threads[0]["role"] in ("producer","consumer"):
        pct = int(len(buf)/bsz*100)
        color = "amber" if 0 < pct < 100 else ("red" if pct == 0 else "blue")
        html += (f'<div class="var-chip {color}">'
                 f'<div class="var-chip-name">buffer</div>'
                 f'<div class="var-chip-val">{len(buf)}/{bsz}</div>'
                 f'<div class="var-chip-status">{"▓"*min(5,int(pct/20))}{"░"*(5-min(5,int(pct/20)))} {pct}%</div>'
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
        owner_icon = " 🔐" if tid == st.session_state.mutex_owner else ""
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
            elif is_cur and hl == "w":
                bub_cls = "phase-bubble active-w"
            elif is_cur:
                bub_cls = "phase-bubble active-w"
            else:
                bub_cls = "phase-bubble"
            arrow_cls = "phase-arrow active" if i < len(phases)-1 and phases[i+1] == cur_ph else "phase-arrow"
            phases_html += f'<span class="phase-step"><span class="{bub_cls}">{ph}</span>'
            if i < len(phases) - 1:
                phases_html += f'<span class="{arrow_cls}">›</span>'
            phases_html += '</span>'
        state_label = "BLOCKED" if state == "waiting" else state.upper()
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
    for text, cls in entries:
        html += f'<div class="log-line {cls}">{text}</div>'
    if not entries:
        html += '<div class="log-line" style="color:#21262d">No events yet.</div>'
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
        cls = (f"cl-{ht}") if matched else ""
        return f'<span class="cl {cls}"> {code}</span>\n'

    html = '<div class="code-block">'

    if scenario == "Mutex (Critical Section)":
        html += L("",       f'{kw("mutex")} = {fn("Semaphore")}({nu("1")})')
        html += L("",       "")
        html += L("",       f'{kw("def")} {fn("thread")}(id):')
        html += L("",       f'    {cm("non-critical work...")}')
        html += L("p_mutex",f'    {cv("P(mutex)")}  {cm("wait — decrement")}', "p")
        html += L("crit",   f'    critical_section()  {cm("🔐 exclusive zone")}', "w")
        html += L("v_mutex",f'    {cv("V(mutex)")}  {cm("signal — increment")}', "v")
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
        html += L("insert", f'    buffer.append(item)', "w")
        html += L("v_mutex",f'    {cv("V(mutex)")}  {cm("unlock")}', "v")
        html += L("v_full", f'    {cv("V(full)")}   {cm("signal: new item")}', "v")
        html += L("",       "")
        html += L("",       f'{kw("def")} {fn("consumer")}():')
        html += L("p_full", f'    {cv("P(full)")}   {cm("wait: item exists?")}', "p")
        html += L("p_mutex",f'    {cv("P(mutex)")}  {cm("lock buffer")}', "p")
        html += L("remove", f'    item = buffer.pop(0)', "w")
        html += L("v_mutex",f'    {cv("V(mutex)")}  {cm("unlock")}', "v")
        html += L("v_empty",f'    {cv("V(empty)")}  {cm("signal: slot free")}', "v")
        html += L("",       f'    consume(item)')

    else:
        html += L("",      f'{kw("resource")} = {fn("Semaphore")}(MAX)')
        html += L("",      "")
        html += L("",      f'{kw("def")} {fn("worker")}(id):')
        html += L("",      f'    {cm("prepare...")}')
        html += L("p_res", f'    {cv("P(resource)")}  {cm("wait: slot free?")}', "p")
        html += L("use",   f'    use_resource()       {cm("concurrent zone")}', "w")
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
    auto_delay = st.slider(
        "⏱ Auto-run delay (sec)", 0.2, 3.0, 0.8, step=0.1,
        help="Time between steps in auto-run mode"
    )
    st.session_state.auto_delay = auto_delay

    st.markdown("---")
    st.markdown("**P(sem)** — wait / decrement  \n`while sem≤0: block()`  \n`sem -= 1`")
    st.markdown("**V(sem)** — signal / increment  \n`sem += 1`  \n`wakeup_next()`")
    st.markdown("---")
    st.markdown("""
<div style="font-size:.75rem;line-height:2.2">
<span style="background:#0d1f38;border:1px solid #1f6feb;color:#58a6ff;padding:2px 8px;border-radius:4px;font-family:monospace">running</span>  executing<br>
<span style="background:#2a0f0f;border:1px solid #b62324;color:#f85149;padding:2px 8px;border-radius:4px;font-family:monospace">blocked</span>  waiting on P()<br>
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
      Step-by-step mode &nbsp;·&nbsp;
      <span style="color:#f0883e;font-family:monospace;font-weight:700">P(sem)</span>
      &nbsp;= wait / decrement &nbsp;·&nbsp;
      <span style="color:#3fb950;font-family:monospace;font-weight:700">V(sem)</span>
      &nbsp;= signal / increment
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Controls row
# ─────────────────────────────────────────────────────────────────────────────

c1, c2, c3, c4, c5 = st.columns([1.2, 1.2, 1.2, 1.2, 4])

with c1:
    if st.button("▶ Step", help="Advance exactly one event"):
        if not st.session_state.initialized:
            init_sim(scenario, n_threads, n_prod, n_cons,
                     buf_size if buf_size else 5, max_conc)
        st.session_state.running = False          # stop auto if running
        msg = tick_once()
        st.session_state.step_msg = msg
        st.rerun()

with c2:
    auto_label = "⏹ Pause" if st.session_state.running else "▶▶ Auto"
    if st.button(auto_label):
        if not st.session_state.initialized:
            init_sim(scenario, n_threads, n_prod, n_cons,
                     buf_size if buf_size else 5, max_conc)
        st.session_state.running = not st.session_state.running
        st.rerun()

with c3:
    if st.button("⏮ Reset"):
        st.session_state.running     = False
        st.session_state.initialized = False
        init_sim(scenario, n_threads, n_prod, n_cons,
                 buf_size if buf_size else 5, max_conc)
        st.rerun()

with c4:
    if st.button("↺ New sim"):
        st.session_state.running     = False
        st.session_state.initialized = False
        st.session_state.threads     = []
        st.session_state.sems        = {}
        st.session_state.buffer      = []
        st.session_state.log         = deque(maxlen=120)
        st.session_state.step        = 0
        st.session_state.step_msg    = "Press <b>▶ Step</b> or <b>▶▶ Auto</b> to begin."
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# Auto-run: advance one step then sleep then rerun
# ─────────────────────────────────────────────────────────────────────────────

if st.session_state.running:
    msg = tick_once()
    st.session_state.step_msg = msg

# ─────────────────────────────────────────────────────────────────────────────
# Step explanation box
# ─────────────────────────────────────────────────────────────────────────────

st.markdown(render_step_box(), unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Variables bar
# ─────────────────────────────────────────────────────────────────────────────

st.markdown(render_vars_bar(), unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Stats row
# ─────────────────────────────────────────────────────────────────────────────

waiting_n = sum(1 for t in st.session_state.threads if t["state"] == "waiting")
running_n = sum(1 for t in st.session_state.threads if t["state"] == "running")
idle_n    = sum(1 for t in st.session_state.threads if t["state"] == "idle")

st.markdown(f"""
<div class="stats-row">
  <div class="stat-box"><div class="stat-val" style="color:#58a6ff">{running_n}</div><div class="stat-lbl">running</div></div>
  <div class="stat-box"><div class="stat-val" style="color:#f85149">{waiting_n}</div><div class="stat-lbl">blocked</div></div>
  <div class="stat-box"><div class="stat-val" style="color:#8b949e">{idle_n}</div><div class="stat-lbl">idle</div></div>
  <div class="stat-box"><div class="stat-val" style="color:#f0883e">{st.session_state.p_calls}</div><div class="stat-lbl">P() calls</div></div>
  <div class="stat-box"><div class="stat-val" style="color:#3fb950">{st.session_state.v_calls}</div><div class="stat-lbl">V() calls</div></div>
  <div class="stat-box"><div class="stat-val" style="color:#6e7681">{st.session_state.step}</div><div class="stat-lbl">steps</div></div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Main columns — threads + code
# ─────────────────────────────────────────────────────────────────────────────

left, right = st.columns([3, 2])

with left:
    st.markdown('<div class="sec-label">Thread execution lanes</div>', unsafe_allow_html=True)
    st.markdown(render_thread_lanes(), unsafe_allow_html=True)

    threads = st.session_state.threads
    if threads and threads[0]["role"] in ("producer", "consumer"):
        st.markdown('<div class="sec-label">Shared buffer</div>', unsafe_allow_html=True)
        st.markdown(render_buffer(), unsafe_allow_html=True)
        buf = st.session_state.buffer
        bsz = st.session_state.buf_size
        st.progress(len(buf) / bsz if bsz else 0)

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
        st.markdown(
            f'<span style="font-family:monospace;font-size:.78rem;color:#8b949e">'
            f'{used} / {max_conc} slots in use</span>',
            unsafe_allow_html=True
        )

# ─────────────────────────────────────────────────────────────────────────────
# Auto-run rerun loop
# ─────────────────────────────────────────────────────────────────────────────

if st.session_state.running:
    time.sleep(st.session_state.auto_delay)
    st.rerun()