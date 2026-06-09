import streamlit as st
import threading
import time
import random
from collections import deque
from datetime import datetime

st.set_page_config(
    page_title="OS Semaphore Visualizer",
    page_icon="🔐",
    layout="wide",
)

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

.card {
    background: #161b22; border: 1px solid #30363d;
    border-radius: 8px; padding: 1rem; margin-bottom: 0.75rem;
}
.card-title {
    font-size: 0.75rem; font-weight: 600; color: #8b949e;
    text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem;
}

/* Thread pills */
.thread-pill { display: inline-block; padding: 3px 10px; border-radius: 20px;
    font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; font-weight: 700; margin: 2px; }
.thread-running  { background: #1f6feb; color: #fff; }
.thread-waiting  { background: #6e40c9; color: #fff; }
.thread-done     { background: #238636; color: #fff; }
.thread-idle     { background: #21262d; border: 1px solid #30363d; color: #8b949e; }

/* Semaphore circles */
.sem-circle-wrap { display: inline-flex; flex-direction: column; align-items: center; margin: 0 10px; }
.sem-circle {
    width: 70px; height: 70px; border-radius: 50%;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 1.5rem;
    border: 3px solid; transition: all 0.3s;
}
.sem-circle.available { border-color: #3fb950; background: rgba(63,185,80,0.12); color: #3fb950; }
.sem-circle.blocked   { border-color: #f85149; background: rgba(248,81,73,0.12); color: #f85149; }
.sem-circle.partial   { border-color: #f0883e; background: rgba(240,136,62,0.12); color: #f0883e; }
.sem-name { font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; font-weight: 700;
    color: #8b949e; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.08em; }
.sem-status { font-size: 0.65rem; color: #8b949e; margin-top: 2px; }

/* Variable badges */
.var-badge {
    display: inline-block; font-family: 'JetBrains Mono', monospace; font-size: 0.78rem;
    background: #0d1117; border: 1px solid #30363d; border-radius: 5px;
    padding: 3px 9px; margin: 3px;
}
.var-name { color: #ffa657; font-weight: 700; }
.var-val-pos { color: #3fb950; font-weight: 700; }
.var-val-zero { color: #f85149; font-weight: 700; }
.var-val-mid  { color: #f0883e; font-weight: 700; }

/* Code block */
.code-block {
    background: #0d1117; border: 1px solid #30363d; border-radius: 8px;
    padding: 1rem; font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem; line-height: 1.75; overflow-x: auto;
}
.code-line { display: block; padding: 0 4px; border-left: 3px solid transparent;
    white-space: pre; border-radius: 2px; }
.code-line-hl-p  { background: rgba(31,111,235,0.18); border-left: 3px solid #58a6ff; }
.code-line-hl-v  { background: rgba(63,185,80,0.15);  border-left: 3px solid #3fb950; }
.code-kw  { color: #ff7b72; font-weight: 700; }
.code-fn  { color: #d2a8ff; }
.code-cm  { color: #8b949e; font-style: italic; }
.code-num { color: #79c0ff; }
.code-var { color: #ffa657; font-weight: 700; }

/* Log */
.log-entry { font-family: 'JetBrains Mono', monospace; font-size: 0.72rem;
    color: #8b949e; margin: 1px 0; }
.log-p   { color: #f0883e; font-weight: 700; }
.log-v   { color: #3fb950; font-weight: 700; }
.log-t   { color: #58a6ff; }
.log-c   { color: #d2a8ff; }

/* Metrics */
.metric-box { background: #161b22; border: 1px solid #30363d; border-radius: 8px;
    padding: 0.75rem 1rem; text-align: center; }
.metric-val { font-family: 'JetBrains Mono', monospace; font-size: 1.6rem; font-weight: 700; }
.metric-lbl { font-size: 0.7rem; color: #8b949e; text-transform: uppercase; letter-spacing: .08em; }

/* Buffer slots */
.slot-full  { background: #1f6feb33; border: 1.5px solid #1f6feb; border-radius: 6px;
    padding: 4px 8px; font-family: monospace; font-size: 0.8rem; color: #58a6ff;
    display: inline-block; margin: 2px; }
.slot-empty { background: #21262d; border: 1.5px dashed #30363d; border-radius: 6px;
    padding: 4px 8px; font-family: monospace; font-size: 0.8rem; color: #484f58;
    display: inline-block; margin: 2px; }

.app-header {
    background: #161b22; border: 1px solid #30363d; border-radius: 10px;
    padding: 1.25rem 1.5rem; margin-bottom: 1.5rem;
}
.app-title { font-size: 1.5rem; font-weight: 700; color: #e6edf3; margin: 0; }
.app-sub   { font-size: 0.8rem; color: #8b949e; margin: 0; }

.stButton > button {
    background: #21262d !important; border: 1px solid #30363d !important;
    color: #e6edf3 !important; border-radius: 6px !important;
    font-family: 'Inter', sans-serif !important; font-weight: 600 !important; font-size: 0.85rem !important;
}
.stButton > button:hover { background: #30363d !important; border-color: #58a6ff !important; }
.stProgress > div > div > div { background: #1f6feb !important; }
hr { border-color: #30363d; }
</style>
""", unsafe_allow_html=True)

# ─── State init ───────────────────────────────────────────────────────────────

def init_state():
    defaults = {
        "running": False,
        "log": deque(maxlen=120),
        "thread_states": {},
        "thread_line": {},   # tid -> active code line key
        "buffer": [],
        "buffer_size": 5,
        "sem_values": {},    # name -> int  (live semaphore values)
        "produced_count": 0,
        "consumed_count": 0,
        "p_calls": 0,
        "v_calls": 0,
        "mutex_owner": None,
        "waiting_queue": [],
        "scenario": "Mutex (Critical Section)",
        "stop_event": None,
        "tick": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ─── Semaphore ────────────────────────────────────────────────────────────────

class SimSemaphore:
    def __init__(self, name, value):
        self.name = name
        self._value = value
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)
        st.session_state.sem_values[name] = value

    @property
    def value(self):
        return self._value

    def _sync(self):
        st.session_state.sem_values[self.name] = self._value
        st.session_state.tick += 1

    def P(self, thread_name):
        log(f'<span class="log-p">P({self.name})</span> called by <span class="log-t">{thread_name}</span>')
        st.session_state.p_calls += 1
        with self._cond:
            while self._value <= 0:
                st.session_state.thread_states[thread_name] = "waiting"
                if thread_name not in st.session_state.waiting_queue:
                    st.session_state.waiting_queue.append(thread_name)
                self._cond.wait(timeout=0.15)
                if st.session_state.stop_event and st.session_state.stop_event.is_set():
                    return False
            self._value -= 1
            if thread_name in st.session_state.waiting_queue:
                st.session_state.waiting_queue.remove(thread_name)
            self._sync()
        return True

    def V(self, thread_name):
        log(f'<span class="log-v">V({self.name})</span> called by <span class="log-t">{thread_name}</span>')
        st.session_state.v_calls += 1
        with self._cond:
            self._value += 1
            self._sync()
            self._cond.notify()

    def reset(self, value):
        with self._cond:
            self._value = value
            self._sync()


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    st.session_state.log.appendleft(
        f'<span style="color:#484f58">[{ts}]</span> {msg}'
    )
    st.session_state.tick += 1


def set_line(tid, key):
    st.session_state.thread_line[tid] = key
    st.session_state.tick += 1


# ─── Scenario runners ─────────────────────────────────────────────────────────

def run_mutex(stop_event, n_threads, speed):
    mutex = SimSemaphore("mutex", 1)

    def worker(tid):
        name = f"T{tid}"
        while not stop_event.is_set():
            st.session_state.thread_states[name] = "running"
            set_line(name, "idle")
            log(f'<span class="log-t">{name}</span> wants critical section')
            time.sleep(random.uniform(0.2, 0.6) / speed)

            st.session_state.thread_states[name] = "running"
            set_line(name, "p_call")
            if not mutex.P(name):
                break

            st.session_state.mutex_owner = name
            st.session_state.thread_states[name] = "running"
            set_line(name, "crit")
            log(f'<span class="log-t">{name}</span> 🔐 inside critical section')
            time.sleep(random.uniform(0.3, 0.8) / speed)

            set_line(name, "v_call")
            mutex.V(name)
            st.session_state.mutex_owner = None
            log(f'<span class="log-t">{name}</span> left critical section')
            set_line(name, "idle")
            time.sleep(random.uniform(0.1, 0.4) / speed)

        st.session_state.thread_states[name] = "done"
        set_line(name, "")

    threads = [threading.Thread(target=worker, args=(i,), daemon=True)
               for i in range(1, n_threads + 1)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


def run_producer_consumer(stop_event, n_prod, n_cons, buf_size, speed):
    empty = SimSemaphore("empty", buf_size)
    full  = SimSemaphore("full",  0)
    mutex = SimSemaphore("mutex", 1)
    st.session_state.buffer = []

    def producer(pid):
        name = f"P{pid}"
        while not stop_event.is_set():
            item = random.randint(10, 99)
            set_line(name, "prod_idle")
            time.sleep(random.uniform(0.3, 0.9) / speed)

            st.session_state.thread_states[name] = "running"
            set_line(name, "p_empty")
            if not empty.P(name): break

            set_line(name, "p_mutex")
            if not mutex.P(name): break

            set_line(name, "insert")
            st.session_state.thread_states[name] = "running"
            if len(st.session_state.buffer) < buf_size:
                st.session_state.buffer.append(item)
            st.session_state.produced_count += 1
            log(f'<span class="log-t">{name}</span> produced <b>{item}</b> → buf={len(st.session_state.buffer)}')

            set_line(name, "v_mutex")
            mutex.V(name)

            set_line(name, "v_full")
            full.V(name)
            set_line(name, "")

        st.session_state.thread_states[name] = "done"
        set_line(name, "")

    def consumer(cid):
        name = f"C{cid}"
        while not stop_event.is_set():
            set_line(name, "cons_idle")
            time.sleep(random.uniform(0.4, 1.0) / speed)

            st.session_state.thread_states[name] = "running"
            set_line(name, "p_full")
            if not full.P(name): break

            set_line(name, "p_mutex")
            if not mutex.P(name): break

            set_line(name, "remove")
            st.session_state.thread_states[name] = "running"
            item = st.session_state.buffer.pop(0) if st.session_state.buffer else "?"
            st.session_state.consumed_count += 1
            log(f'<span class="log-c">{name}</span> consumed <b>{item}</b> ← buf={len(st.session_state.buffer)}')

            set_line(name, "v_mutex2")
            mutex.V(name)

            set_line(name, "v_empty")
            empty.V(name)
            set_line(name, "")

        st.session_state.thread_states[name] = "done"
        set_line(name, "")

    threads = (
        [threading.Thread(target=producer, args=(i,), daemon=True) for i in range(1, n_prod + 1)] +
        [threading.Thread(target=consumer, args=(i,), daemon=True) for i in range(1, n_cons + 1)]
    )
    for t in threads:
        t.start()
    for t in threads:
        t.join()


def run_counting(stop_event, n_threads, max_concurrent, speed):
    resource = SimSemaphore("resource", max_concurrent)

    def worker(tid):
        name = f"W{tid}"
        while not stop_event.is_set():
            set_line(name, "idle")
            time.sleep(random.uniform(0.2, 0.5) / speed)

            st.session_state.thread_states[name] = "running"
            log(f'<span class="log-t">{name}</span> requests resource')
            set_line(name, "p_call")
            if not resource.P(name): break

            st.session_state.thread_states[name] = "running"
            set_line(name, "use")
            log(f'<span class="log-t">{name}</span> using resource (resource={resource.value})')
            time.sleep(random.uniform(0.3, 0.8) / speed)

            set_line(name, "v_call")
            resource.V(name)
            log(f'<span class="log-t">{name}</span> released resource')
            set_line(name, "")

        st.session_state.thread_states[name] = "done"
        set_line(name, "")

    threads = [threading.Thread(target=worker, args=(i,), daemon=True)
               for i in range(1, n_threads + 1)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


# ─── Pseudocode renderer ──────────────────────────────────────────────────────

def render_code(active_keys: set, scenario: str) -> str:
    """
    Render highlighted pseudocode.
    active_keys: set of line-key strings currently executing.
    Lines tagged 'p_*' highlight blue on match, 'v_*' highlight green.
    """

    def line(key, code, hl_type=""):
        """hl_type: 'p' = blue, 'v' = green, '' = none"""
        matched = key and key in active_keys
        if matched and hl_type == "p":
            cls = "code-line code-line-hl-p"
        elif matched and hl_type == "v":
            cls = "code-line code-line-hl-v"
        else:
            cls = "code-line"
        return f'<span class="{cls}"> {code}</span>\n'

    kw  = lambda s: f'<span class="code-kw">{s}</span>'
    fn  = lambda s: f'<span class="code-fn">{s}</span>'
    cm  = lambda s: f'<span class="code-cm"># {s}</span>'
    num = lambda s: f'<span class="code-num">{s}</span>'
    var = lambda s: f'<span class="code-var">{s}</span>'

    html = '<div class="code-block">'

    if scenario == "Mutex (Critical Section)":
        html += line("init",   f'{kw("mutex")} = {fn("Semaphore")}({num("1")})   {cm("binary semaphore — init value = 1")}')
        html += line("",       "")
        html += line("thread", f'{kw("def")} {fn("thread")}(id):')
        html += line("idle",   f'    {cm("non-critical work...")}')
        html += line("p_call", f'    {var("P(mutex)")}         {cm("wait — decrement mutex")}', "p")
        html += line("crit",   f'    critical_section()   {cm("🔐 exclusive access")}', "p")
        html += line("v_call", f'    {var("V(mutex)")}         {cm("signal — increment mutex")}', "v")
        html += line("",       f'    {cm("continue...")}')
        html += line("",       "")
        html += line("",       f'{kw("def")} {fn("P")}(sem):                  {cm("wait / down")}')
        html += line("",       f'    {kw("while")} sem.value &lt;= {num("0")}: block()')
        html += line("",       f'    sem.value -= {num("1")}')
        html += line("",       "")
        html += line("",       f'{kw("def")} {fn("V")}(sem):                  {cm("signal / up")}')
        html += line("",       f'    sem.value += {num("1")}')
        html += line("",       f'    wakeup_next()         {cm("notify a waiting thread")}')

    elif scenario in ("Producer / Consumer", "Multi-Producer / Multi-Consumer"):
        html += line("init",      f'{kw("empty")} = {fn("Semaphore")}({num("N")})   {cm("free slots  (init = N)")}')
        html += line("init",      f'{kw("full")}  = {fn("Semaphore")}({num("0")})   {cm("filled slots (init = 0)")}')
        html += line("init",      f'{kw("mutex")} = {fn("Semaphore")}({num("1")})   {cm("mutual exclusion (init = 1)")}')
        html += line("",          "")
        html += line("prod",      f'{kw("def")} {fn("producer")}():')
        html += line("prod_idle", f'    item = produce()')
        html += line("p_empty",   f'    {var("P(empty)")}         {cm("wait: is there a free slot?")}', "p")
        html += line("p_mutex",   f'    {var("P(mutex)")}         {cm("wait: lock the buffer")}', "p")
        html += line("insert",    f'    buffer.append(item)  {cm("critical: insert")}', "p")
        html += line("v_mutex",   f'    {var("V(mutex)")}         {cm("signal: unlock buffer")}', "v")
        html += line("v_full",    f'    {var("V(full)")}          {cm("signal: one more item")}', "v")
        html += line("",          "")
        html += line("cons",      f'{kw("def")} {fn("consumer")}():')
        html += line("cons_idle", f'    {cm("ready to consume...")}')
        html += line("p_full",    f'    {var("P(full)")}          {cm("wait: is there an item?")}', "p")
        html += line("p_mutex",   f'    {var("P(mutex)")}         {cm("wait: lock the buffer")}', "p")
        html += line("remove",    f'    item = buffer.pop(0) {cm("critical: remove")}', "p")
        html += line("v_mutex2",  f'    {var("V(mutex)")}         {cm("signal: unlock buffer")}', "v")
        html += line("v_empty",   f'    {var("V(empty)")}         {cm("signal: one slot freed")}', "v")
        html += line("",          f'    consume(item)')

    else:  # Counting semaphore
        html += line("init",   f'{kw("resource")} = {fn("Semaphore")}(MAX)  {cm("N concurrent workers allowed")}')
        html += line("",       "")
        html += line("worker", f'{kw("def")} {fn("worker")}(id):')
        html += line("idle",   f'    {cm("prepare work...")}')
        html += line("p_call", f'    {var("P(resource)")}    {cm("wait: is a slot available?")}', "p")
        html += line("use",    f'    use_resource()    {cm("limited concurrency zone")}', "p")
        html += line("v_call", f'    {var("V(resource)")}    {cm("signal: slot released")}', "v")
        html += line("",       f'    {cm("continue...")}')

    html += '</div>'
    return html


# ─── Semaphore visual renderer ────────────────────────────────────────────────

def render_semaphore_circles(sem_values: dict) -> str:
    if not sem_values:
        return '<div style="color:#484f58;font-size:0.85rem">No semaphores active.</div>'

    html = '<div style="display:flex;flex-wrap:wrap;gap:8px;align-items:flex-start">'
    for name, val in sem_values.items():
        if val <= 0:
            cls, status = "blocked", "BLOCKED"
        elif val == 1:
            cls, status = "available", "AVAILABLE"
        else:
            cls, status = "partial", f"{val} SLOTS"

        html += f"""
<div class="sem-circle-wrap">
  <div class="sem-circle {cls}">{val}</div>
  <div class="sem-name">{name}</div>
  <div class="sem-status">{'🔴' if val<=0 else '🟢'} {status}</div>
</div>"""

    html += "</div>"

    # Variable badges below circles
    html += '<div style="margin-top:10px">'
    for name, val in sem_values.items():
        if val <= 0:
            val_cls = "var-val-zero"
        elif val == 1:
            val_cls = "var-val-pos"
        else:
            val_cls = "var-val-mid"
        html += (f'<span class="var-badge">'
                 f'<span class="var-name">{name}</span>'
                 f' = <span class="{val_cls}">{val}</span>'
                 f'</span>')
    html += "</div>"
    return html


# ─── Sidebar ──────────────────────────────────────────────────────────────────

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
            "Mutex (Critical Section)", "Producer / Consumer",
            "Multi-Producer / Multi-Consumer", "Counting Semaphore"] else 0,
        disabled=st.session_state.running,
    )
    st.session_state.scenario = scenario
    st.markdown("---")

    if scenario == "Mutex (Critical Section)":
        n_threads = st.slider("Threads", 2, 8, 3, disabled=st.session_state.running)
        n_producers = n_consumers = buf_size = 0
        max_concurrent = sem_init = 1

    elif scenario in ("Producer / Consumer", "Multi-Producer / Multi-Consumer"):
        default_p = 1 if scenario == "Producer / Consumer" else 3
        default_c = 1 if scenario == "Producer / Consumer" else 3
        n_producers = st.slider("Producers", 1, 6, default_p, disabled=st.session_state.running)
        n_consumers = st.slider("Consumers", 1, 6, default_c, disabled=st.session_state.running)
        buf_size    = st.slider("Buffer size", 2, 12, 5, disabled=st.session_state.running)
        n_threads   = n_producers + n_consumers
        max_concurrent = 1
        sem_init    = buf_size

    else:
        n_threads      = st.slider("Workers", 2, 10, 6, disabled=st.session_state.running)
        max_concurrent = st.slider("Max concurrent (semaphore N)", 1, 6, 3,
                                   disabled=st.session_state.running)
        n_producers = n_consumers = buf_size = 0
        sem_init = max_concurrent

    st.markdown("---")
    speed = st.slider("⚡ Speed multiplier", 0.5, 5.0, 2.0, step=0.5,
                      disabled=st.session_state.running)

    st.markdown("---")
    st.markdown("### P / V semantics")
    st.markdown("""
**P(sem)** — *wait / down*
- while sem ≤ 0 → block thread
- sem.value -= 1

**V(sem)** — *signal / up*
- sem.value += 1
- wake one waiting thread

---
### Thread legend
""")
    st.markdown("""
<span class='thread-pill thread-running'>running</span>
<span class='thread-pill thread-waiting'>waiting</span>
<span class='thread-pill thread-idle'>idle</span>
<span class='thread-pill thread-done'>done</span>
""", unsafe_allow_html=True)


# ─── Header ───────────────────────────────────────────────────────────────────

st.markdown("""
<div class='app-header'>
  <p class='app-title'>🔐 OS Semaphore Visualizer</p>
  <p class='app-sub'>Live simulation · P(sem) = wait/decrement · V(sem) = signal/increment · variables update in real time</p>
</div>
""", unsafe_allow_html=True)

# ─── Control buttons ──────────────────────────────────────────────────────────

col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 5])
with col_btn1:
    start_clicked = st.button("▶ Start", disabled=st.session_state.running)
with col_btn2:
    stop_clicked  = st.button("⏹ Stop",  disabled=not st.session_state.running)

if start_clicked and not st.session_state.running:
    st.session_state.running       = True
    st.session_state.log.clear()
    st.session_state.thread_states = {}
    st.session_state.thread_line   = {}
    st.session_state.buffer        = []
    st.session_state.buffer_size   = buf_size if buf_size > 0 else 5
    st.session_state.sem_values    = {}
    st.session_state.produced_count = 0
    st.session_state.consumed_count = 0
    st.session_state.p_calls       = 0
    st.session_state.v_calls       = 0
    st.session_state.mutex_owner   = None
    st.session_state.waiting_queue = []
    st.session_state.stop_event    = threading.Event()

    stop_ev = st.session_state.stop_event

    if scenario == "Mutex (Critical Section)":
        t = threading.Thread(target=run_mutex,
                             args=(stop_ev, n_threads, speed), daemon=True)
    elif scenario in ("Producer / Consumer", "Multi-Producer / Multi-Consumer"):
        st.session_state.buffer_size = buf_size
        t = threading.Thread(target=run_producer_consumer,
                             args=(stop_ev, n_producers, n_consumers, buf_size, speed), daemon=True)
    else:
        t = threading.Thread(target=run_counting,
                             args=(stop_ev, n_threads, max_concurrent, speed), daemon=True)

    t.start()

if stop_clicked and st.session_state.running:
    if st.session_state.stop_event:
        st.session_state.stop_event.set()
    st.session_state.running = False

# ─── Main layout ──────────────────────────────────────────────────────────────

left_col, right_col = st.columns([3, 2])

with left_col:

    # Metrics
    m1, m2, m3, m4 = st.columns(4)
    sem_display = "/".join(str(v) for v in st.session_state.sem_values.values()) \
                  if st.session_state.sem_values else "—"
    with m1:
        st.markdown(f'<div class="metric-box"><div class="metric-val" style="color:#58a6ff">{sem_display}</div>'
                    f'<div class="metric-lbl">Semaphore value(s)</div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-box"><div class="metric-val" style="color:#d2a8ff">{len(st.session_state.waiting_queue)}</div>'
                    f'<div class="metric-lbl">Threads waiting</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="metric-box"><div class="metric-val" style="color:#f0883e">{st.session_state.p_calls}</div>'
                    f'<div class="metric-lbl">P() calls total</div></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="metric-box"><div class="metric-val" style="color:#3fb950">{st.session_state.v_calls}</div>'
                    f'<div class="metric-lbl">V() calls total</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Semaphore circles + variable badges
    st.markdown('<div class="card-title">🔢 Semaphore variables — live values</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="card">{render_semaphore_circles(st.session_state.sem_values)}</div>',
        unsafe_allow_html=True
    )

    # Thread grid
    st.markdown('<div class="card-title">🧵 Thread states</div>', unsafe_allow_html=True)
    thread_states = st.session_state.thread_states
    waiting_q     = st.session_state.waiting_queue
    mutex_owner   = st.session_state.mutex_owner

    if thread_states:
        pills = ""
        for tname, tstate in sorted(thread_states.items()):
            cls  = {"running": "thread-running", "waiting": "thread-waiting",
                    "done": "thread-done"}.get(tstate, "thread-idle")
            icon = " 🔐" if tname == mutex_owner else (" ⏳" if tname in waiting_q else "")
            pills += f'<span class="thread-pill {cls}">{tname}{icon}</span> '
        st.markdown(f'<div class="card">{pills}</div>', unsafe_allow_html=True)

        if waiting_q:
            q_html = " → ".join(
                f'<span class="thread-pill thread-waiting">{t}</span>' for t in waiting_q)
            st.markdown(
                f'<div class="card-title" style="margin-top:6px">⏳ Wait queue</div>'
                f'<div style="margin-bottom:8px">{q_html}</div>',
                unsafe_allow_html=True)
    else:
        st.markdown('<div class="card" style="color:#484f58;font-size:0.85rem">Start a simulation.</div>',
                    unsafe_allow_html=True)

    # Buffer
    if scenario in ("Producer / Consumer", "Multi-Producer / Multi-Consumer"):
        st.markdown("<br>", unsafe_allow_html=True)
        bsize  = st.session_state.buffer_size
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
            f'<span style="color:#8b949e;font-size:0.72rem;font-family:monospace">'
            f'{filled}/{bsize} slots used ({pct}%)</span></div>',
            unsafe_allow_html=True)
        st.progress(pct / 100)

    # Log
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="card-title">📋 Event log</div>', unsafe_allow_html=True)
    log_entries = list(st.session_state.log)[:30]
    log_html = '<div class="card" style="height:220px;overflow-y:auto">'
    for e in log_entries:
        log_html += f'<div class="log-entry">{e}</div>'
    if not log_entries:
        log_html += '<span style="color:#484f58;font-size:0.8rem">No events yet.</span>'
    log_html += "</div>"
    st.markdown(log_html, unsafe_allow_html=True)


with right_col:
    st.markdown('<div class="card-title">💻 Pseudocode — live highlighted</div>',
                unsafe_allow_html=True)

    active_keys = set(st.session_state.thread_line.values())
    st.markdown(
        render_code(active_keys, scenario),
        unsafe_allow_html=True
    )

    # Concurrency gauge for counting semaphore
    if scenario == "Counting Semaphore":
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="card-title">📊 Concurrency gauge</div>', unsafe_allow_html=True)
        active_n = sum(1 for s in thread_states.values() if s == "running")
        gauge_pct = min(active_n / max(max_concurrent, 1), 1.0)
        st.progress(gauge_pct)
        st.markdown(
            f'<span style="font-family:monospace;font-size:0.8rem;color:#8b949e">'
            f'{active_n} / {max_concurrent} resource slots in use</span>',
            unsafe_allow_html=True)

# ─── Auto-refresh ─────────────────────────────────────────────────────────────

if st.session_state.running:
    time.sleep(0.2)
    st.rerun()