"""
OS Semaphore Visualizer — Streamlit Cloud compatible
No background threads. Simulation advances one micro-step per rerun.
"""
import streamlit as st
import random
from collections import deque
from datetime import datetime

st.set_page_config(page_title="OS Semaphore Visualizer", page_icon="🔐", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif}
.main{background:#0d1117;color:#e6edf3}
[data-testid="stAppViewContainer"]{background:#0d1117}
[data-testid="stSidebar"]{background:#161b22;border-right:1px solid #30363d}
[data-testid="stSidebar"] *{color:#e6edf3 !important}
h1,h2,h3{color:#e6edf3}
.stSelectbox label,.stSlider label,.stRadio label{color:#8b949e !important;font-size:.85rem}
.card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:1rem;margin-bottom:.75rem}
.card-title{font-size:.75rem;font-weight:600;color:#8b949e;text-transform:uppercase;letter-spacing:.08em;margin-bottom:.5rem}
.thread-pill{display:inline-block;padding:3px 10px;border-radius:20px;font-family:'JetBrains Mono',monospace;font-size:.75rem;font-weight:700;margin:2px}
.thread-running{background:#1f6feb;color:#fff}
.thread-waiting{background:#6e40c9;color:#fff}
.thread-done{background:#238636;color:#fff}
.thread-idle{background:#21262d;border:1px solid #30363d;color:#8b949e}
.sem-circle-wrap{display:inline-flex;flex-direction:column;align-items:center;margin:0 10px}
.sem-circle{width:70px;height:70px;border-radius:50%;display:flex;flex-direction:column;align-items:center;justify-content:center;font-family:'JetBrains Mono',monospace;font-weight:700;font-size:1.5rem;border:3px solid}
.sem-available{border-color:#3fb950;background:rgba(63,185,80,.12);color:#3fb950}
.sem-blocked{border-color:#f85149;background:rgba(248,81,73,.12);color:#f85149}
.sem-partial{border-color:#f0883e;background:rgba(240,136,62,.12);color:#f0883e}
.sem-name{font-family:'JetBrains Mono',monospace;font-size:.72rem;font-weight:700;color:#8b949e;margin-top:4px;text-transform:uppercase;letter-spacing:.08em}
.sem-status{font-size:.65rem;color:#8b949e;margin-top:2px}
.var-badge{display:inline-block;font-family:'JetBrains Mono',monospace;font-size:.78rem;background:#0d1117;border:1px solid #30363d;border-radius:5px;padding:3px 9px;margin:3px}
.var-name{color:#ffa657;font-weight:700}
.var-val-pos{color:#3fb950;font-weight:700}
.var-val-zero{color:#f85149;font-weight:700}
.var-val-mid{color:#f0883e;font-weight:700}
.code-block{background:#0d1117;border:1px solid #30363d;border-radius:8px;padding:1rem;font-family:'JetBrains Mono',monospace;font-size:.78rem;line-height:1.75;overflow-x:auto}
.code-line{display:block;padding:0 4px;border-left:3px solid transparent;white-space:pre;border-radius:2px}
.code-line-hl-p{background:rgba(31,111,235,.18);border-left:3px solid #58a6ff}
.code-line-hl-v{background:rgba(63,185,80,.15);border-left:3px solid #3fb950}
.code-kw{color:#ff7b72;font-weight:700}
.code-fn{color:#d2a8ff}
.code-cm{color:#8b949e;font-style:italic}
.code-num{color:#79c0ff}
.code-var{color:#ffa657;font-weight:700}
.slot-full{background:#1f6feb33;border:1.5px solid #1f6feb;border-radius:6px;padding:4px 8px;font-family:monospace;font-size:.8rem;color:#58a6ff;display:inline-block;margin:2px}
.slot-empty{background:#21262d;border:1.5px dashed #30363d;border-radius:6px;padding:4px 8px;font-family:monospace;font-size:.8rem;color:#484f58;display:inline-block;margin:2px}
.log-entry{font-family:'JetBrains Mono',monospace;font-size:.72rem;color:#8b949e;margin:1px 0}
.log-p{color:#f0883e;font-weight:700}
.log-v{color:#3fb950;font-weight:700}
.log-t{color:#58a6ff}
.log-c{color:#d2a8ff}
.metric-box{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:.75rem 1rem;text-align:center}
.metric-val{font-family:'JetBrains Mono',monospace;font-size:1.6rem;font-weight:700}
.metric-lbl{font-size:.7rem;color:#8b949e;text-transform:uppercase;letter-spacing:.08em}
.app-header{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:1.25rem 1.5rem;margin-bottom:1.5rem}
.stButton>button{background:#21262d !important;border:1px solid #30363d !important;color:#e6edf3 !important;border-radius:6px !important;font-weight:600 !important;font-size:.85rem !important}
.stButton>button:hover{background:#30363d !important;border-color:#58a6ff !important}
.stProgress>div>div>div{background:#1f6feb !important}
hr{border-color:#30363d}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Simulation state machine
#
# Each "thread" is a Python dict acting as a coroutine-like state machine:
#   { id, state, phase, wait_sem, pc, sleep_ticks, item }
#
# On every rerun we advance each thread by one micro-step, then st.rerun().
# "sleep_ticks" counts down through idle/work phases so threads don't
# all move in lockstep.
# ─────────────────────────────────────────────────────────────────────────────

SCENARIOS = ["Mutex (Critical Section)", "Producer / Consumer",
             "Multi-Producer / Multi-Consumer", "Counting Semaphore"]

def _def(key, val):
    if key not in st.session_state:
        st.session_state[key] = val

_def("running", False)
_def("scenario", SCENARIOS[0])
_def("threads", [])        # list of thread dicts
_def("sems", {})           # name -> int  (semaphore values)
_def("buffer", [])
_def("buf_size", 5)
_def("log", deque(maxlen=100))
_def("p_calls", 0)
_def("v_calls", 0)
_def("mutex_owner", None)
_def("step", 0)
_def("speed", 2)

# ── helpers ──────────────────────────────────────────────────────────────────

def add_log(msg):
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    st.session_state.log.appendleft(f'<span style="color:#484f58">[{ts}]</span> {msg}')

def sem_P(name, tid_label):
    """Try to decrement semaphore. Returns True if acquired, False if must wait."""
    if st.session_state.sems.get(name, 0) > 0:
        st.session_state.sems[name] -= 1
        add_log(f'<span class="log-p">P({name})</span> acquired by <span class="log-t">{tid_label}</span> → {name}={st.session_state.sems[name]}')
        st.session_state.p_calls += 1
        return True
    return False

def sem_V(name, tid_label):
    st.session_state.sems[name] = st.session_state.sems.get(name, 0) + 1
    add_log(f'<span class="log-v">V({name})</span> released by <span class="log-t">{tid_label}</span> → {name}={st.session_state.sems[name]}')
    st.session_state.v_calls += 1

def rand_ticks(lo, hi, speed):
    """Return tick count for a sleep, scaled by speed."""
    base = random.randint(lo, hi)
    return max(1, base // speed)

# ── Thread phase constants ────────────────────────────────────────────────────
# Each scenario uses a set of named phases; the step() function is a big
# state machine switch on (scenario, phase).

MUTEX_PHASES   = ["idle_sleep", "want_lock", "p_mutex", "in_critical", "v_mutex", "post_sleep"]
PC_PROD_PHASES = ["idle_sleep", "p_empty", "p_mutex", "insert", "v_mutex", "v_full"]
PC_CONS_PHASES = ["idle_sleep", "p_full",  "p_mutex", "remove", "v_mutex", "v_empty"]
CNT_PHASES     = ["idle_sleep", "p_resource", "using", "v_resource"]

# Phase → code line key (for highlighting)
PHASE_TO_LINE = {
    # mutex
    "want_lock":   "p_call",
    "p_mutex":     "p_call",
    "in_critical": "crit",
    "v_mutex":     "v_call",
    # prod-cons producer
    "p_empty":     "p_empty",
    "insert":      "insert",
    "v_full":      "v_full",
    "v_mutex_p":   "v_mutex",
    # prod-cons consumer
    "p_full":      "p_full",
    "remove":      "remove",
    "v_empty":     "v_empty",
    "v_mutex_c":   "v_mutex2",
    # p_mutex shared
    "p_mutex":     "p_mutex",
    # counting
    "p_resource":  "p_call",
    "using":       "use",
    "v_resource":  "v_call",
}

# ── Simulation init ───────────────────────────────────────────────────────────

def init_simulation(scenario, n_threads, n_prod, n_cons, buf_size, max_conc, speed):
    st.session_state.threads   = []
    st.session_state.sems      = {}
    st.session_state.buffer    = []
    st.session_state.buf_size  = buf_size
    st.session_state.log       = deque(maxlen=100)
    st.session_state.p_calls   = 0
    st.session_state.v_calls   = 0
    st.session_state.mutex_owner = None
    st.session_state.step      = 0
    st.session_state.speed     = speed

    if scenario == "Mutex (Critical Section)":
        st.session_state.sems = {"mutex": 1}
        for i in range(1, n_threads + 1):
            st.session_state.threads.append({
                "id": f"T{i}", "role": "mutex",
                "phase": "idle_sleep",
                "sleep_ticks": random.randint(1, 6),
                "item": None, "state": "idle",
            })

    elif scenario in ("Producer / Consumer", "Multi-Producer / Multi-Consumer"):
        st.session_state.sems = {"empty": buf_size, "full": 0, "mutex": 1}
        for i in range(1, n_prod + 1):
            st.session_state.threads.append({
                "id": f"P{i}", "role": "producer",
                "phase": "idle_sleep",
                "sleep_ticks": random.randint(1, 5),
                "item": None, "state": "idle",
            })
        for i in range(1, n_cons + 1):
            st.session_state.threads.append({
                "id": f"C{i}", "role": "consumer",
                "phase": "idle_sleep",
                "sleep_ticks": random.randint(2, 7),
                "item": None, "state": "idle",
            })

    else:  # Counting semaphore
        st.session_state.sems = {"resource": max_conc}
        for i in range(1, n_threads + 1):
            st.session_state.threads.append({
                "id": f"W{i}", "role": "worker",
                "phase": "idle_sleep",
                "sleep_ticks": random.randint(1, 5),
                "item": None, "state": "idle",
            })

# ── Advance simulation by one tick ───────────────────────────────────────────

def tick_simulation():
    speed = st.session_state.speed

    for t in st.session_state.threads:
        tid   = t["id"]
        role  = t["role"]
        phase = t["phase"]

        # ── sleep countdown (idle / work phases) ──────────────────────────
        if phase == "idle_sleep":
            t["state"] = "idle"
            if t["sleep_ticks"] > 0:
                t["sleep_ticks"] -= 1
            else:
                # move to first active phase
                if role == "mutex":
                    t["phase"] = "want_lock"
                    add_log(f'<span class="log-t">{tid}</span> wants critical section')
                elif role == "producer":
                    t["item"]  = random.randint(10, 99)
                    t["phase"] = "p_empty"
                elif role == "consumer":
                    t["phase"] = "p_full"
                elif role == "worker":
                    t["phase"] = "p_resource"
                    add_log(f'<span class="log-t">{tid}</span> requests resource')
            continue

        # ── mutex scenario ────────────────────────────────────────────────
        if role == "mutex":
            if phase == "want_lock":
                t["state"] = "running"
                t["phase"] = "p_mutex"

            elif phase == "p_mutex":
                if sem_P("mutex", tid):
                    st.session_state.mutex_owner = tid
                    t["state"] = "running"
                    t["phase"] = "in_critical"
                    t["sleep_ticks"] = rand_ticks(3, 8, speed)
                    add_log(f'<span class="log-t">{tid}</span> 🔐 inside critical section')
                else:
                    t["state"] = "waiting"

            elif phase == "in_critical":
                if t["sleep_ticks"] > 0:
                    t["sleep_ticks"] -= 1
                else:
                    t["phase"] = "v_mutex"

            elif phase == "v_mutex":
                sem_V("mutex", tid)
                if st.session_state.mutex_owner == tid:
                    st.session_state.mutex_owner = None
                add_log(f'<span class="log-t">{tid}</span> left critical section')
                t["phase"] = "idle_sleep"
                t["sleep_ticks"] = rand_ticks(2, 6, speed)
                t["state"] = "idle"

        # ── producer ──────────────────────────────────────────────────────
        elif role == "producer":
            if phase == "p_empty":
                if sem_P("empty", tid):
                    t["phase"] = "p_mutex"
                    t["state"] = "running"
                else:
                    t["state"] = "waiting"

            elif phase == "p_mutex":
                if sem_P("mutex", tid):
                    t["phase"] = "insert"
                    t["state"] = "running"
                else:
                    t["state"] = "waiting"

            elif phase == "insert":
                buf = st.session_state.buffer
                if len(buf) < st.session_state.buf_size:
                    buf.append(t["item"])
                add_log(f'<span class="log-t">{tid}</span> produced <b>{t["item"]}</b> → buf={len(buf)}')
                t["phase"] = "v_mutex"

            elif phase == "v_mutex":
                sem_V("mutex", tid)
                t["phase"] = "v_full"

            elif phase == "v_full":
                sem_V("full", tid)
                t["phase"] = "idle_sleep"
                t["sleep_ticks"] = rand_ticks(3, 8, speed)
                t["state"] = "idle"

        # ── consumer ──────────────────────────────────────────────────────
        elif role == "consumer":
            if phase == "p_full":
                if sem_P("full", tid):
                    t["phase"] = "p_mutex"
                    t["state"] = "running"
                else:
                    t["state"] = "waiting"

            elif phase == "p_mutex":
                if sem_P("mutex", tid):
                    t["phase"] = "remove"
                    t["state"] = "running"
                else:
                    t["state"] = "waiting"

            elif phase == "remove":
                buf  = st.session_state.buffer
                item = buf.pop(0) if buf else "?"
                add_log(f'<span class="log-c">{tid}</span> consumed <b>{item}</b> ← buf={len(buf)}')
                t["phase"] = "v_mutex2"

            elif phase == "v_mutex2":
                sem_V("mutex", tid)
                t["phase"] = "v_empty"

            elif phase == "v_empty":
                sem_V("empty", tid)
                t["phase"] = "idle_sleep"
                t["sleep_ticks"] = rand_ticks(4, 10, speed)
                t["state"] = "idle"

        # ── counting semaphore worker ─────────────────────────────────────
        elif role == "worker":
            if phase == "p_resource":
                if sem_P("resource", tid):
                    t["state"] = "running"
                    t["phase"] = "using"
                    t["sleep_ticks"] = rand_ticks(3, 8, speed)
                    add_log(f'<span class="log-t">{tid}</span> using resource (resource={st.session_state.sems["resource"]})')
                else:
                    t["state"] = "waiting"

            elif phase == "using":
                if t["sleep_ticks"] > 0:
                    t["sleep_ticks"] -= 1
                else:
                    t["phase"] = "v_resource"

            elif phase == "v_resource":
                sem_V("resource", tid)
                add_log(f'<span class="log-t">{tid}</span> released resource')
                t["phase"] = "idle_sleep"
                t["sleep_ticks"] = rand_ticks(2, 5, speed)
                t["state"] = "idle"

    st.session_state.step += 1

# ─────────────────────────────────────────────────────────────────────────────
# Rendering helpers
# ─────────────────────────────────────────────────────────────────────────────

def render_sem_circles():
    sems = st.session_state.sems
    if not sems:
        return '<div style="color:#484f58;font-size:.85rem">No semaphores active.</div>'
    html = '<div style="display:flex;flex-wrap:wrap;gap:8px;align-items:flex-start">'
    for name, val in sems.items():
        if val <= 0:   cls, icon, status = "sem-blocked",  "🔴", "BLOCKED"
        elif val == 1: cls, icon, status = "sem-available","🟢", "AVAILABLE"
        else:          cls, icon, status = "sem-partial",  "🟠", f"{val} FREE"
        html += (f'<div class="sem-circle-wrap">'
                 f'<div class="sem-circle {cls}">{val}</div>'
                 f'<div class="sem-name">{name}</div>'
                 f'<div class="sem-status">{icon} {status}</div>'
                 f'</div>')
    html += "</div><div style='margin-top:10px'>"
    for name, val in sems.items():
        vc = "var-val-zero" if val <= 0 else ("var-val-mid" if val > 1 else "var-val-pos")
        html += (f'<span class="var-badge">'
                 f'<span class="var-name">{name}</span>'
                 f' = <span class="{vc}">{val}</span></span>')
    html += "</div>"
    return html


def active_line_keys():
    keys = set()
    for t in st.session_state.threads:
        k = PHASE_TO_LINE.get(t["phase"], "")
        if k:
            keys.add(k)
    return keys


def render_code(scenario, active_keys):
    kw  = lambda s: f'<span class="code-kw">{s}</span>'
    fn  = lambda s: f'<span class="code-fn">{s}</span>'
    cm  = lambda s: f'<span class="code-cm"># {s}</span>'
    num = lambda s: f'<span class="code-num">{s}</span>'
    var = lambda s: f'<span class="code-var">{s}</span>'

    def L(key, code, ht=""):
        matched = key and key in active_keys
        cls = ("code-line-hl-p" if ht == "p" else "code-line-hl-v") if matched else ""
        return f'<span class="code-line {cls}"> {code}</span>\n'

    html = '<div class="code-block">'

    if scenario == "Mutex (Critical Section)":
        html += L("init",   f'{kw("mutex")} = {fn("Semaphore")}({num("1")})   {cm("binary — init 1 = unlocked")}')
        html += L("",       "")
        html += L("",       f'{kw("def")} {fn("thread")}(id):')
        html += L("idle",   f'    {cm("non-critical work...")}')
        html += L("p_call", f'    {var("P(mutex)")}         {cm("wait — decrement mutex")}', "p")
        html += L("crit",   f'    critical_section()   {cm("🔐 exclusive access")}', "p")
        html += L("v_call", f'    {var("V(mutex)")}         {cm("signal — increment mutex")}', "v")
        html += L("",       f'    {cm("continue...")}')
        html += L("",       "")
        html += L("",       f'{kw("def")} {fn("P")}(sem):')
        html += L("",       f'    {kw("while")} sem.value &lt;= {num("0")}: block()')
        html += L("",       f'    sem.value -= {num("1")}')
        html += L("",       "")
        html += L("",       f'{kw("def")} {fn("V")}(sem):')
        html += L("",       f'    sem.value += {num("1")}')
        html += L("",       f'    wakeup_next()')

    elif scenario in ("Producer / Consumer", "Multi-Producer / Multi-Consumer"):
        html += L("",        f'{kw("empty")} = {fn("Semaphore")}({num("N")})   {cm("free slots  (init=N)")}')
        html += L("",        f'{kw("full")}  = {fn("Semaphore")}({num("0")})   {cm("filled slots (init=0)")}')
        html += L("",        f'{kw("mutex")} = {fn("Semaphore")}({num("1")})   {cm("mutual exclusion")}')
        html += L("",        "")
        html += L("",        f'{kw("def")} {fn("producer")}():')
        html += L("",        f'    item = produce()')
        html += L("p_empty", f'    {var("P(empty)")}         {cm("wait: free slot?")}', "p")
        html += L("p_mutex", f'    {var("P(mutex)")}         {cm("wait: lock buffer")}', "p")
        html += L("insert",  f'    buffer.append(item) {cm("critical: insert")}', "p")
        html += L("v_mutex", f'    {var("V(mutex)")}         {cm("signal: unlock")}', "v")
        html += L("v_full",  f'    {var("V(full)")}          {cm("signal: new item")}', "v")
        html += L("",        "")
        html += L("",        f'{kw("def")} {fn("consumer")}():')
        html += L("p_full",  f'    {var("P(full)")}          {cm("wait: item exists?")}', "p")
        html += L("p_mutex", f'    {var("P(mutex)")}         {cm("wait: lock buffer")}', "p")
        html += L("remove",  f'    item = buffer.pop(0) {cm("critical: remove")}', "p")
        html += L("v_mutex2",f'    {var("V(mutex)")}         {cm("signal: unlock")}', "v")
        html += L("v_empty", f'    {var("V(empty)")}         {cm("signal: slot freed")}', "v")
        html += L("",        f'    consume(item)')

    else:
        html += L("",        f'{kw("resource")} = {fn("Semaphore")}(MAX) {cm("N concurrent slots")}')
        html += L("",        "")
        html += L("",        f'{kw("def")} {fn("worker")}(id):')
        html += L("",        f'    {cm("prepare...")}')
        html += L("p_call",  f'    {var("P(resource)")}    {cm("wait: slot free?")}', "p")
        html += L("use",     f'    use_resource()    {cm("limited concurrency")}', "p")
        html += L("v_call",  f'    {var("V(resource)")}    {cm("signal: slot released")}', "v")
        html += L("",        f'    {cm("continue...")}')

    html += "</div>"
    return html

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    st.markdown("---")
    scenario = st.selectbox("Scenario", SCENARIOS,
                            index=SCENARIOS.index(st.session_state.scenario)
                            if st.session_state.scenario in SCENARIOS else 0,
                            disabled=st.session_state.running)
    st.session_state.scenario = scenario
    st.markdown("---")

    if scenario == "Mutex (Critical Section)":
        n_threads = st.slider("Threads", 2, 8, 3, disabled=st.session_state.running)
        n_prod = n_cons = buf_size = 0; max_conc = 1
    elif scenario in ("Producer / Consumer", "Multi-Producer / Multi-Consumer"):
        dp = 1 if scenario == "Producer / Consumer" else 3
        dc = 1 if scenario == "Producer / Consumer" else 3
        n_prod   = st.slider("Producers", 1, 6, dp, disabled=st.session_state.running)
        n_cons   = st.slider("Consumers", 1, 6, dc, disabled=st.session_state.running)
        buf_size = st.slider("Buffer size", 2, 12, 5, disabled=st.session_state.running)
        n_threads = n_prod + n_cons; max_conc = 1
    else:
        n_threads = st.slider("Workers", 2, 10, 6, disabled=st.session_state.running)
        max_conc  = st.slider("Max concurrent (N)", 1, 6, 3, disabled=st.session_state.running)
        n_prod = n_cons = buf_size = 0

    st.markdown("---")
    speed = st.slider("⚡ Speed", 1, 5, 2, help="Steps per tick (higher = faster)")

    st.markdown("---")
    st.markdown("### P / V semantics")
    st.markdown("""
**P(sem)** — *wait / down*  
while sem ≤ 0 → block  
sem.value -= 1

**V(sem)** — *signal / up*  
sem.value += 1  
wake one waiter
""")
    st.markdown("---")
    st.markdown("""
<span class='thread-pill thread-running'>running</span>
<span class='thread-pill thread-waiting'>waiting</span>
<span class='thread-pill thread-idle'>idle</span>
<span class='thread-pill thread-done'>done</span>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Header + controls
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<div class='app-header'>
  <p style='font-size:1.5rem;font-weight:700;color:#e6edf3;margin:0'>🔐 OS Semaphore Visualizer</p>
  <p style='font-size:.8rem;color:#8b949e;margin:0'>
    P(sem) = wait / decrement &nbsp;·&nbsp; V(sem) = signal / increment &nbsp;·&nbsp; variables update live
  </p>
</div>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns([1, 1, 5])
with c1:
    if st.button("▶ Start", disabled=st.session_state.running):
        init_simulation(scenario, n_threads, n_prod, n_cons,
                        buf_size if buf_size else 5, max_conc, speed)
        st.session_state.running = True
        st.rerun()
with c2:
    if st.button("⏹ Stop", disabled=not st.session_state.running):
        st.session_state.running = False
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# Advance simulation (runs on every rerun while running=True)
# ─────────────────────────────────────────────────────────────────────────────

if st.session_state.running:
    # advance `speed` micro-steps per rerun so higher speed = more progress
    for _ in range(st.session_state.speed):
        tick_simulation()

# ─────────────────────────────────────────────────────────────────────────────
# Main layout
# ─────────────────────────────────────────────────────────────────────────────

left_col, right_col = st.columns([3, 2])

with left_col:
    # Metrics
    sems = st.session_state.sems
    sem_display = " / ".join(f"{n}={v}" for n, v in sems.items()) if sems else "—"
    waiting_n   = sum(1 for t in st.session_state.threads if t["state"] == "waiting")

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="metric-box"><div class="metric-val" style="color:#58a6ff">'
                    f'{" / ".join(str(v) for v in sems.values()) if sems else "—"}'
                    f'</div><div class="metric-lbl">Semaphore(s)</div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-box"><div class="metric-val" style="color:#d2a8ff">'
                    f'{waiting_n}</div><div class="metric-lbl">Waiting</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="metric-box"><div class="metric-val" style="color:#f0883e">'
                    f'{st.session_state.p_calls}</div><div class="metric-lbl">P() calls</div></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="metric-box"><div class="metric-val" style="color:#3fb950">'
                    f'{st.session_state.v_calls}</div><div class="metric-lbl">V() calls</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Semaphore circles
    st.markdown('<div class="card-title">🔢 Semaphore variables — live values</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="card">{render_sem_circles()}</div>', unsafe_allow_html=True)

    # Thread pills
    st.markdown('<div class="card-title">🧵 Thread states</div>', unsafe_allow_html=True)
    threads = st.session_state.threads
    if threads:
        pills = ""
        for t in sorted(threads, key=lambda x: x["id"]):
            cls  = {"running": "thread-running", "waiting": "thread-waiting",
                    "idle": "thread-idle"}.get(t["state"], "thread-idle")
            icon = " 🔐" if t["id"] == st.session_state.mutex_owner else \
                   (" ⏳" if t["state"] == "waiting" else "")
            pills += f'<span class="thread-pill {cls}">{t["id"]}{icon}</span> '
        waiting_ids = [t["id"] for t in threads if t["state"] == "waiting"]
        queue_html  = ""
        if waiting_ids:
            queue_html = ("<br><span style='font-size:.72rem;color:#8b949e'>⏳ wait queue: "
                         + " → ".join(
                             f'<span class="thread-pill thread-waiting">{tid}</span>'
                             for tid in waiting_ids)
                         + "</span>")
        st.markdown(f'<div class="card">{pills}{queue_html}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="card" style="color:#484f58;font-size:.85rem">Start a simulation.</div>',
                    unsafe_allow_html=True)

    # Buffer (producer-consumer only)
    if scenario in ("Producer / Consumer", "Multi-Producer / Multi-Consumer") and st.session_state.threads:
        st.markdown("<br>", unsafe_allow_html=True)
        bsize  = st.session_state.buf_size
        buf    = st.session_state.buffer
        filled = len(buf)
        slots  = "".join(
            f'<span class="slot-full">{buf[i]}</span>' if i < filled
            else '<span class="slot-empty">—</span>'
            for i in range(bsize)
        )
        pct = int(filled / bsize * 100) if bsize else 0
        st.markdown('<div class="card-title">📦 Shared buffer</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="card">{slots}<br>'
            f'<span style="color:#8b949e;font-size:.72rem;font-family:monospace">'
            f'{filled}/{bsize} slots  ({pct}%)</span></div>',
            unsafe_allow_html=True)
        st.progress(pct / 100)

    # Log
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="card-title">📋 Event log</div>', unsafe_allow_html=True)
    entries = list(st.session_state.log)[:30]
    log_html = '<div class="card" style="height:220px;overflow-y:auto">'
    for e in entries:
        log_html += f'<div class="log-entry">{e}</div>'
    if not entries:
        log_html += '<span style="color:#484f58;font-size:.8rem">No events yet — press Start.</span>'
    log_html += "</div>"
    st.markdown(log_html, unsafe_allow_html=True)


with right_col:
    st.markdown('<div class="card-title">💻 Pseudocode — live highlighted</div>', unsafe_allow_html=True)
    active_keys = active_line_keys()
    st.markdown(render_code(scenario, active_keys), unsafe_allow_html=True)

    if scenario == "Counting Semaphore" and st.session_state.threads:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="card-title">📊 Concurrency gauge</div>', unsafe_allow_html=True)
        active_n = sum(1 for t in st.session_state.threads if t["state"] == "running")
        st.progress(min(active_n / max(max_conc, 1), 1.0))
        st.markdown(f'<span style="font-family:monospace;font-size:.8rem;color:#8b949e">'
                    f'{active_n} / {max_conc} resource slots in use</span>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Auto-rerun loop
# ─────────────────────────────────────────────────────────────────────────────

if st.session_state.running:
    import time
    time.sleep(0.18)
    st.rerun()