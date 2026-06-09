import streamlit as st
import threading
import time
import random
import queue
from collections import deque
from datetime import datetime

# ─────────────────────────────────────────────────────────────
#  Page config
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="OS Semaphore Visualizer",
    page_icon="🔐",
    layout="wide",
)

# ─────────────────────────────────────────────────────────────
#  Custom CSS
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.main { background: #0d1117; color: #e6edf3; }
[data-testid="stAppViewContainer"] { background: #0d1117; }
[data-testid="stSidebar"] { background: #161b22; border-right: 1px solid #30363d; }
[data-testid="stSidebar"] * { color: #e6edf3 !important; }

h1, h2, h3 { color: #e6edf3; }
.stSelectbox label, .stSlider label, .stRadio label { color: #8b949e !important; font-size: 0.85rem; }

/* Cards */
.card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.75rem;
}
.card-title {
    font-size: 0.75rem;
    font-weight: 600;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.5rem;
}

/* Thread pills */
.thread-pill {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    font-weight: 700;
    margin: 2px;
}
.thread-running  { background: #1f6feb; color: #fff; }
.thread-waiting  { background: #6e40c9; color: #fff; }
.thread-done     { background: #238636; color: #fff; }
.thread-blocked  { background: #b62324; color: #fff; }

/* Semaphore counter badge */
.sem-badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 2.5rem;
    font-weight: 700;
    color: #58a6ff;
    line-height: 1;
}
.sem-label { font-size: 0.75rem; color: #8b949e; margin-top: 2px; }

/* Buffer slots */
.slot-full  { background: #1f6feb33; border: 1.5px solid #1f6feb; border-radius: 6px;
              padding: 4px 8px; font-family: monospace; font-size: 0.8rem; color: #58a6ff;
              display: inline-block; margin: 2px; }
.slot-empty { background: #21262d; border: 1.5px solid #30363d; border-radius: 6px;
              padding: 4px 8px; font-family: monospace; font-size: 0.8rem; color: #484f58;
              display: inline-block; margin: 2px; }

/* Code block */
.code-block {
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 1rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    line-height: 1.7;
    overflow-x: auto;
}
.code-kw   { color: #ff7b72; font-weight: 700; }
.code-fn   { color: #d2a8ff; }
.code-com  { color: #8b949e; font-style: italic; }
.code-str  { color: #a5d6ff; }
.code-num  { color: #79c0ff; }
.code-hl   { background: #1f6feb33; border-left: 3px solid #1f6feb;
             display: block; margin: 0 -1rem; padding: 0 1rem; }

/* Log */
.log-entry { font-family: 'JetBrains Mono', monospace; font-size: 0.72rem;
             color: #8b949e; margin: 1px 0; }
.log-p     { color: #f0883e; }
.log-v     { color: #3fb950; }
.log-entry-prod { color: #58a6ff; }
.log-entry-cons { color: #d2a8ff; }
.log-mutex { color: #ffa657; }

/* Header */
.app-header {
    background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
}
.app-title { font-size: 1.5rem; font-weight: 700; color: #e6edf3; margin: 0; }
.app-sub   { font-size: 0.8rem; color: #8b949e; margin: 0; }

/* Metric */
.metric-box {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    text-align: center;
}
.metric-val { font-family: 'JetBrains Mono', monospace; font-size: 1.6rem; font-weight: 700; }
.metric-lbl { font-size: 0.7rem; color: #8b949e; text-transform: uppercase; letter-spacing: .08em; }
.col-blue  { color: #58a6ff; }
.col-green { color: #3fb950; }
.col-orange{ color: #f0883e; }
.col-purple{ color: #d2a8ff; }

/* Buttons */
.stButton > button {
    background: #21262d !important;
    border: 1px solid #30363d !important;
    color: #e6edf3 !important;
    border-radius: 6px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
}
.stButton > button:hover {
    background: #30363d !important;
    border-color: #58a6ff !important;
}

/* Progress bars */
.stProgress > div > div > div { background: #1f6feb !important; }

hr { border-color: #30363d; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  State init
# ─────────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "running": False,
        "log": deque(maxlen=120),
        "thread_states": {},
        "buffer": [],
        "buffer_size": 5,
        "semaphore_value": 1,
        "produced_count": 0,
        "consumed_count": 0,
        "mutex_owner": None,
        "waiting_queue": [],
        "scenario": "Mutex (Critical Section)",
        "stop_event": None,
        "sim_threads": [],
        "tick": 0,
        "highlights": {},      # line_key -> True for currently executing lines
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ─────────────────────────────────────────────────────────────
#  Simulation engine
# ─────────────────────────────────────────────────────────────

class SimSemaphore:
    """Simple counting semaphore with logging."""
    def __init__(self, value, name="sem"):
        self._value = value
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)
        self.name = name

    @property
    def value(self):
        return self._value

    def P(self, thread_name):
        """Wait / decrement."""
        log(f"<span class='log-p'>P({self.name})</span> called by <b>{thread_name}</b>")
        with self._cond:
            while self._value <= 0:
                st.session_state.thread_states[thread_name] = "waiting"
                if thread_name not in st.session_state.waiting_queue:
                    st.session_state.waiting_queue.append(thread_name)
                self._cond.wait(timeout=0.2)
                if st.session_state.stop_event and st.session_state.stop_event.is_set():
                    return False
            self._value -= 1
            st.session_state.semaphore_value = self._value
            if thread_name in st.session_state.waiting_queue:
                st.session_state.waiting_queue.remove(thread_name)
        return True

    def V(self, thread_name):
        """Signal / increment."""
        log(f"<span class='log-v'>V({self.name})</span> called by <b>{thread_name}</b>")
        with self._cond:
            self._value += 1
            st.session_state.semaphore_value = self._value
            self._cond.notify()

    def reset(self, value):
        with self._cond:
            self._value = value
            st.session_state.semaphore_value = value


def log(msg, kind=""):
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    st.session_state.log.appendleft(f'<span style="color:#484f58">[{ts}]</span> {msg}')
    st.session_state.tick += 1


# ── Scenario runners ─────────────────────────────────────────

def run_mutex(stop_event, n_threads, speed):
    mutex = SimSemaphore(1, "mutex")
    st.session_state.semaphore_value = 1

    def critical_section(tid):
        name = f"T{tid}"
        while not stop_event.is_set():
            st.session_state.thread_states[name] = "running"
            log(f'<span class="log-mutex">Thread {name}</span> wants to enter critical section')
            st.session_state.highlights[name] = "p_call"
            if not mutex.P(name):
                break
            st.session_state.thread_states[name] = "running"
            st.session_state.mutex_owner = name
            st.session_state.highlights[name] = "critical"
            log(f'<span class="log-mutex">Thread {name}</span> <b>inside critical section</b> 🔐')
            time.sleep(random.uniform(0.3, 0.8) / speed)
            st.session_state.highlights[name] = "v_call"
            mutex.V(name)
            st.session_state.mutex_owner = None
            log(f'<span class="log-mutex">Thread {name}</span> left critical section')
            st.session_state.highlights[name] = "idle"
            time.sleep(random.uniform(0.2, 0.6) / speed)
        st.session_state.thread_states[name] = "done"

    threads = [threading.Thread(target=critical_section, args=(i,), daemon=True)
               for i in range(1, n_threads + 1)]
    st.session_state.sim_threads = threads
    for t in threads:
        t.start()
    for t in threads:
        t.join()


def run_producer_consumer(stop_event, n_prod, n_cons, buf_size, speed):
    empty = SimSemaphore(buf_size, "empty")
    full  = SimSemaphore(0,        "full")
    mutex = SimSemaphore(1,        "mutex")
    st.session_state.semaphore_value = buf_size
    st.session_state.buffer = []

    def producer(pid):
        name = f"P{pid}"
        while not stop_event.is_set():
            item = random.randint(10, 99)
            time.sleep(random.uniform(0.3, 0.9) / speed)
            st.session_state.thread_states[name] = "running"
            st.session_state.highlights[name] = "p_empty"
            if not empty.P(name): break
            st.session_state.highlights[name] = "p_mutex"
            if not mutex.P(name): break
            # critical: insert
            st.session_state.thread_states[name] = "running"
            st.session_state.highlights[name] = "insert"
            if len(st.session_state.buffer) < buf_size:
                st.session_state.buffer.append(item)
            st.session_state.produced_count += 1
            log(f'<span class="log-entry-prod">Producer {name}</span> produced <b>{item}</b> (buf={len(st.session_state.buffer)})')
            mutex.V(name)
            st.session_state.highlights[name] = "v_full"
            full.V(name)
            st.session_state.highlights[name] = "idle"
        st.session_state.thread_states[name] = "done"

    def consumer(cid):
        name = f"C{cid}"
        while not stop_event.is_set():
            time.sleep(random.uniform(0.4, 1.0) / speed)
            st.session_state.thread_states[name] = "running"
            st.session_state.highlights[name] = "p_full"
            if not full.P(name): break
            st.session_state.highlights[name] = "p_mutex"
            if not mutex.P(name): break
            # critical: remove
            st.session_state.thread_states[name] = "running"
            st.session_state.highlights[name] = "remove"
            item = None
            if st.session_state.buffer:
                item = st.session_state.buffer.pop(0)
            st.session_state.consumed_count += 1
            log(f'<span class="log-entry-cons">Consumer {name}</span> consumed <b>{item}</b> (buf={len(st.session_state.buffer)})')
            mutex.V(name)
            st.session_state.highlights[name] = "v_empty"
            empty.V(name)
            st.session_state.highlights[name] = "idle"
        st.session_state.thread_states[name] = "done"

    threads = (
        [threading.Thread(target=producer, args=(i,), daemon=True) for i in range(1, n_prod + 1)] +
        [threading.Thread(target=consumer, args=(i,), daemon=True) for i in range(1, n_cons + 1)]
    )
    st.session_state.sim_threads = threads
    for t in threads:
        t.start()
    for t in threads:
        t.join()


def run_counting_semaphore(stop_event, n_threads, max_concurrent, speed):
    sem = SimSemaphore(max_concurrent, "resource")
    st.session_state.semaphore_value = max_concurrent

    def worker(tid):
        name = f"W{tid}"
        while not stop_event.is_set():
            time.sleep(random.uniform(0.2, 0.5) / speed)
            st.session_state.thread_states[name] = "running"
            log(f'<span class="log-entry-prod">Worker {name}</span> requests resource')
            st.session_state.highlights[name] = "p_call"
            if not sem.P(name): break
            st.session_state.thread_states[name] = "running"
            st.session_state.highlights[name] = "use"
            log(f'<span class="log-entry-prod">Worker {name}</span> using resource (sem={sem.value})')
            time.sleep(random.uniform(0.3, 0.8) / speed)
            st.session_state.highlights[name] = "v_call"
            sem.V(name)
            log(f'<span class="log-entry-prod">Worker {name}</span> released resource')
            st.session_state.highlights[name] = "idle"
        st.session_state.thread_states[name] = "done"

    threads = [threading.Thread(target=worker, args=(i,), daemon=True)
               for i in range(1, n_threads + 1)]
    st.session_state.sim_threads = threads
    for t in threads:
        t.start()
    for t in threads:
        t.join()


# ─────────────────────────────────────────────────────────────
#  Code highlight renderer
# ─────────────────────────────────────────────────────────────

def mutex_code(active_lines):
    lines = [
        ("init",     '<span class="code-kw">mutex</span> = Semaphore(<span class="code-num">1</span>)   <span class="code-com"># binary semaphore</span>'),
        ("",         ""),
        ("thread",   '<span class="code-kw">def</span> <span class="code-fn">thread</span>(id):'),
        ("idle",     '    <span class="code-com"># ... do non-critical work ...</span>'),
        ("p_call",   '    P(mutex)          <span class="code-com"># wait / acquire 🔒</span>'),
        ("critical", '    <span class="code-kw">critical_section</span>()   <span class="code-com"># protected code</span>'),
        ("v_call",   '    V(mutex)          <span class="code-com"># signal / release 🔓</span>'),
    ]
    return _render_code(lines, active_lines)


def prod_cons_code_producer(active_lines):
    lines = [
        ("init",      '<span class="code-kw">empty</span> = Semaphore(N)   <span class="code-com"># free slots</span>'),
        ("init",      '<span class="code-kw">full</span>  = Semaphore(0)   <span class="code-com"># filled slots</span>'),
        ("init",      '<span class="code-kw">mutex</span> = Semaphore(1)   <span class="code-com"># mutual exclusion</span>'),
        ("",          ""),
        ("producer",  '<span class="code-kw">def</span> <span class="code-fn">producer</span>():'),
        ("idle",      '    item = produce()'),
        ("p_empty",   '    P(empty)          <span class="code-com"># wait for free slot</span>'),
        ("p_mutex",   '    P(mutex)          <span class="code-com"># lock buffer</span>'),
        ("insert",    '    buffer.append(item)'),
        ("",          '    V(mutex)'),
        ("v_full",    '    V(full)           <span class="code-com"># signal new item</span>'),
    ]
    return _render_code(lines, active_lines)


def prod_cons_code_consumer(active_lines):
    lines = [
        ("consumer",  '<span class="code-kw">def</span> <span class="code-fn">consumer</span>():'),
        ("p_full",    '    P(full)           <span class="code-com"># wait for item</span>'),
        ("p_mutex",   '    P(mutex)          <span class="code-com"># lock buffer</span>'),
        ("remove",    '    item = buffer.pop(0)'),
        ("",          '    V(mutex)'),
        ("v_empty",   '    V(empty)          <span class="code-com"># free a slot</span>'),
        ("",          '    consume(item)'),
    ]
    return _render_code(lines, active_lines)


def counting_sem_code(active_lines):
    lines = [
        ("init",   '<span class="code-kw">sem</span> = Semaphore(MAX)  <span class="code-com"># N concurrent threads</span>'),
        ("",       ""),
        ("worker", '<span class="code-kw">def</span> <span class="code-fn">worker</span>(id):'),
        ("idle",   '    <span class="code-com"># ... prepare work ...</span>'),
        ("p_call", '    P(sem)    <span class="code-com"># decrement counter</span>'),
        ("use",    '    <span class="code-fn">use_resource</span>()  <span class="code-com"># limited concurrency</span>'),
        ("v_call", '    V(sem)    <span class="code-com"># increment counter</span>'),
    ]
    return _render_code(lines, active_lines)


def _render_code(lines, active_set):
    html = '<div class="code-block">'
    for key, code in lines:
        hl = "code-hl" if key and key in active_set else ""
        html += f'<span class="{hl}">{code}</span>\n'
    html += "</div>"
    return html


# ─────────────────────────────────────────────────────────────
#  Sidebar — configuration
# ─────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    st.markdown("---")

    scenario = st.selectbox(
        "Scenario",
        ["Mutex (Critical Section)",
         "Producer / Consumer",
         "Multi-Producer / Multi-Consumer",
         "Counting Semaphore"],
        index=["Mutex (Critical Section)",
               "Producer / Consumer",
               "Multi-Producer / Multi-Consumer",
               "Counting Semaphore"].index(st.session_state.scenario)
        if st.session_state.scenario in [
            "Mutex (Critical Section)",
            "Producer / Consumer",
            "Multi-Producer / Multi-Consumer",
            "Counting Semaphore"] else 0,
        disabled=st.session_state.running,
    )
    st.session_state.scenario = scenario

    st.markdown("---")

    if scenario == "Mutex (Critical Section)":
        n_threads = st.slider("Number of threads", 2, 8, 3,
                              disabled=st.session_state.running)
        n_producers = n_consumers = 0
        buf_size = 0
        max_concurrent = 1
        sem_init = 1

    elif scenario in ("Producer / Consumer", "Multi-Producer / Multi-Consumer"):
        default_p = 1 if scenario == "Producer / Consumer" else 3
        default_c = 1 if scenario == "Producer / Consumer" else 3
        n_producers = st.slider("Producers", 1, 6, default_p,
                                disabled=st.session_state.running)
        n_consumers = st.slider("Consumers", 1, 6, default_c,
                                disabled=st.session_state.running)
        buf_size = st.slider("Buffer size", 2, 12, 5,
                             disabled=st.session_state.running)
        n_threads = n_producers + n_consumers
        max_concurrent = 1
        sem_init = buf_size

    else:  # Counting semaphore
        n_threads = st.slider("Number of workers", 2, 10, 6,
                              disabled=st.session_state.running)
        max_concurrent = st.slider("Max concurrent (semaphore value)", 1, 6, 3,
                                   disabled=st.session_state.running)
        n_producers = n_consumers = 0
        buf_size = 0
        sem_init = max_concurrent

    st.markdown("---")
    speed = st.slider("⚡ Speed multiplier", 0.5, 5.0, 1.5, step=0.5,
                      disabled=st.session_state.running)

    st.markdown("---")
    st.markdown("### 📖 Legend")
    st.markdown("""
<span class='thread-pill thread-running'>running</span>
<span class='thread-pill thread-waiting'>waiting</span>
<span class='thread-pill thread-blocked'>blocked</span>
<span class='thread-pill thread-done'>done</span>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  Header
# ─────────────────────────────────────────────────────────────

st.markdown("""
<div class='app-header'>
  <div>
    <p class='app-title'>🔐 OS Semaphore Visualizer</p>
    <p class='app-sub'>Live simulation of semaphores, mutex, P/V operations & producer-consumer patterns</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  Control buttons
# ─────────────────────────────────────────────────────────────

col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 5])

with col_btn1:
    start_clicked = st.button("▶ Start", disabled=st.session_state.running)
with col_btn2:
    stop_clicked  = st.button("⏹ Stop",  disabled=not st.session_state.running)

if start_clicked and not st.session_state.running:
    # reset state
    st.session_state.running = True
    st.session_state.log.clear()
    st.session_state.thread_states = {}
    st.session_state.buffer = []
    st.session_state.buffer_size = buf_size if buf_size > 0 else 5
    st.session_state.semaphore_value = sem_init
    st.session_state.produced_count = 0
    st.session_state.consumed_count = 0
    st.session_state.mutex_owner = None
    st.session_state.waiting_queue = []
    st.session_state.highlights = {}
    st.session_state.stop_event = threading.Event()

    stop_ev = st.session_state.stop_event

    if scenario == "Mutex (Critical Section)":
        t = threading.Thread(
            target=run_mutex,
            args=(stop_ev, n_threads, speed),
            daemon=True)
    elif scenario in ("Producer / Consumer", "Multi-Producer / Multi-Consumer"):
        st.session_state.buffer_size = buf_size
        t = threading.Thread(
            target=run_producer_consumer,
            args=(stop_ev, n_producers, n_consumers, buf_size, speed),
            daemon=True)
    else:
        t = threading.Thread(
            target=run_counting_semaphore,
            args=(stop_ev, n_threads, max_concurrent, speed),
            daemon=True)

    t.daemon = True
    t.start()

if stop_clicked and st.session_state.running:
    if st.session_state.stop_event:
        st.session_state.stop_event.set()
    st.session_state.running = False

# ─────────────────────────────────────────────────────────────
#  Main layout
# ─────────────────────────────────────────────────────────────

left_col, right_col = st.columns([3, 2])

# ── LEFT: Metrics + Threads + Buffer + Log ───────────────────
with left_col:

    # ── Metrics row ──
    m1, m2, m3, m4 = st.columns(4)

    sem_val  = st.session_state.semaphore_value
    n_wait   = len(st.session_state.waiting_queue)
    produced = st.session_state.produced_count
    consumed = st.session_state.consumed_count

    with m1:
        st.markdown(f"""
        <div class="metric-box">
          <div class="metric-val col-blue">{sem_val}</div>
          <div class="metric-lbl">Semaphore value</div>
        </div>""", unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-box">
          <div class="metric-val col-purple">{n_wait}</div>
          <div class="metric-lbl">Threads waiting</div>
        </div>""", unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="metric-box">
          <div class="metric-val col-green">{produced}</div>
          <div class="metric-lbl">Produced</div>
        </div>""", unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="metric-box">
          <div class="metric-val col-orange">{consumed}</div>
          <div class="metric-lbl">Consumed</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Thread grid ──
    st.markdown('<div class="card-title">🧵 Thread States</div>', unsafe_allow_html=True)
    thread_states = st.session_state.thread_states
    waiting_q     = st.session_state.waiting_queue
    mutex_owner   = st.session_state.mutex_owner

    if thread_states:
        pills_html = ""
        for tname, tstate in sorted(thread_states.items()):
            if tstate == "running":
                cls = "thread-running"
            elif tstate == "waiting":
                cls = "thread-waiting"
            elif tstate == "blocked":
                cls = "thread-blocked"
            else:
                cls = "thread-done"

            icon = ""
            if tname == mutex_owner:
                icon = " 🔐"
            elif tname in waiting_q:
                icon = " ⏳"

            pills_html += f'<span class="thread-pill {cls}">{tname}{icon}</span> '
        st.markdown(f'<div class="card">{pills_html}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="card" style="color:#484f58;font-size:0.85rem;">Start a simulation to see thread states.</div>',
                    unsafe_allow_html=True)

    # ── Waiting queue ──
    if waiting_q:
        q_html = " → ".join(
            f'<span class="thread-pill thread-waiting">{t}</span>'
            for t in waiting_q)
        st.markdown(f'<div class="card-title">⏳ Wait Queue</div>{q_html}',
                    unsafe_allow_html=True)

    # ── Buffer (producer-consumer only) ──
    if scenario in ("Producer / Consumer", "Multi-Producer / Multi-Consumer"):
        st.markdown("<br>", unsafe_allow_html=True)
        bsize  = st.session_state.buffer_size
        buf    = st.session_state.buffer
        filled = len(buf)

        st.markdown('<div class="card-title">📦 Shared Buffer</div>', unsafe_allow_html=True)
        slots_html = ""
        for i in range(bsize):
            if i < filled:
                slots_html += f'<span class="slot-full">{buf[i]}</span>'
            else:
                slots_html += '<span class="slot-empty">—</span>'

        pct = int((filled / bsize) * 100) if bsize else 0
        st.markdown(f'<div class="card">{slots_html}<br><span style="color:#8b949e;font-size:0.72rem;font-family:monospace">{filled}/{bsize} slots used ({pct}%)</span></div>',
                    unsafe_allow_html=True)
        st.progress(pct / 100)

    # ── Log ──
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="card-title">📋 Event Log</div>', unsafe_allow_html=True)
    log_entries = list(st.session_state.log)[:30]
    log_html = '<div class="card" style="height:220px;overflow-y:auto">'
    for entry in log_entries:
        log_html += f'<div class="log-entry">{entry}</div>'
    if not log_entries:
        log_html += '<span style="color:#484f58;font-size:0.8rem">No events yet.</span>'
    log_html += "</div>"
    st.markdown(log_html, unsafe_allow_html=True)

# ── RIGHT: Code viewer ───────────────────────────────────────
with right_col:
    st.markdown('<div class="card-title">💻 Pseudocode (live-highlighted)</div>',
                unsafe_allow_html=True)

    # Collect all active highlight keys across all threads
    all_hl = set(st.session_state.highlights.values())

    if scenario == "Mutex (Critical Section)":
        st.markdown(mutex_code(all_hl), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="card-title">ℹ️ P & V functions</div>', unsafe_allow_html=True)
        st.markdown("""
<div class="code-block">
<span class="code-kw">def</span> <span class="code-fn">P</span>(sem):         <span class="code-com"># wait / down</span>
    <span class="code-kw">while</span> sem.value &lt;= <span class="code-num">0</span>:
        block_thread()     <span class="code-com"># sleep</span>
    sem.value -= <span class="code-num">1</span>

<span class="code-kw">def</span> <span class="code-fn">V</span>(sem):         <span class="code-com"># signal / up</span>
    sem.value += <span class="code-num">1</span>
    wakeup_one()       <span class="code-com"># notify waiting</span>
</div>
""", unsafe_allow_html=True)

    elif scenario in ("Producer / Consumer", "Multi-Producer / Multi-Consumer"):
        st.markdown("**Producer**", unsafe_allow_html=False)
        st.markdown(prod_cons_code_producer(all_hl), unsafe_allow_html=True)
        st.markdown("<br>**Consumer**", unsafe_allow_html=False)
        st.markdown(prod_cons_code_consumer(all_hl), unsafe_allow_html=True)

    else:  # Counting
        st.markdown(counting_sem_code(all_hl), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="card-title">📊 Concurrency gauge</div>', unsafe_allow_html=True)
        active = sum(1 for s in st.session_state.thread_states.values()
                     if s == "running") if st.session_state.thread_states else 0
        cap = max_concurrent if scenario == "Counting Semaphore" else 1
        gauge_pct = min(active / max(cap, 1), 1.0)
        st.progress(gauge_pct)
        st.markdown(
            f'<span style="font-family:monospace;font-size:0.8rem;color:#8b949e">'
            f'{active} / {cap} resource slots in use</span>',
            unsafe_allow_html=True)

    # ── Semaphore state box ──
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="card-title">🔢 Semaphore state</div>', unsafe_allow_html=True)
    val_color = "#3fb950" if sem_val > 0 else "#f85149"
    st.markdown(f"""
<div class="card" style="text-align:center">
  <div class="sem-badge" style="color:{val_color}">{sem_val}</div>
  <div class="sem-label">Current semaphore value</div>
  <div style="margin-top:0.5rem;font-family:monospace;font-size:0.72rem;color:#8b949e">
    {'🟢 AVAILABLE' if sem_val > 0 else '🔴 BLOCKED'}
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  Auto-refresh while running
# ─────────────────────────────────────────────────────────────

if st.session_state.running:
    time.sleep(0.25)
    st.rerun()