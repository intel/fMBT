"""Pythonshare in parallel and distributed computing

1. Example, launch local workers to run fibonacci:

import psmap
psmap.launch_workers(8) # you could use cpu count here

def fib(n):
    if n <= 1:
        return 1
    else:
        return fib(n-1) + fib(n-2)

print "map..."
print map(fib, [32] * 16)

print "psmap..."
print psmap.psmap(fib, [32] * 16)

---

2. Example, use all workers registered on two pythonshare-server hubs:

import psmap
psmap.use_workers(hub_1_hostspec)
psmap.use_workers(hub_2_hostspec)
...
psmap.psmap(fib, [32] * 16)

---

3. Example, use explicitly listed workers, some may be local, some remote:

import psmap
psmap.use_worker(worker_1_hostspec)
psmap.use_worker(worker_2_hostspec)
...
psmap.use_worker(worker_n_hostspec)

psmap.psmap(fib, [32] * 16)
"""

import atexit
import Queue
import inspect
import os
import pythonshare
import subprocess
import thread
import time

g_hubs = []
g_hubs_kill_at_exit = []
g_workers = []
g_worker_conns = []
g_workers_free = Queue.Queue()

def soe(cmd, stdin="", cwd=None, env=None, bg=False):
    """Run cmd, return (status, stdout, stderr)"""
    run_env = dict(os.environ)
    if not env is None:
        run_env.update(env)
    try:
        p = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds=True,
            cwd=cwd,
            env=run_env)
        if bg:
            return (p, None, None)
        out, err = p.communicate(input=stdin)
    except Exception, e:
        return (None, None, str(e))
    return (p.returncode, out, err)

def use_workers(hub_hostspec):
    g_hubs.append(hub_hostspec)
    conn = pythonshare.connect(hub_hostspec)
    for ns in conn.ls_remote():
        use_worker(hub_hostspec + "/" + ns)

def launch_workers(count, hub_port=9999):
    hub_addr = launch_hub(hub_port)
    for worker_id in xrange(count):
        launch_worker(worker_id, hub_addr)

def launch_hub(port=9999):
    hub_addr = "localhost:%s" % (port,)
    try:
        pythonshare.connect(hub_addr).kill_server()
    except:
        pass
    soe(["pythonshare-server", "-p", hub_addr.split(":")[-1]])
    g_hubs_kill_at_exit.append(hub_addr)
    g_hubs.append(hub_addr)
    return hub_addr

def launch_worker(worker_id, hub_addr):
    if hub_addr is None:
        hub_addr = g_hub_addr
    namespace = str(worker_id)
    soe(["pythonshare-server", "-p", "stdin", "-n", namespace, "-E", hub_addr],
        bg=True)
    worker_addr = hub_addr + "/" + namespace
    use_worker(worker_addr)

def use_worker(worker_hostspec):
    conn = pythonshare.connect(worker_hostspec)
    g_workers.append(worker_hostspec)
    g_worker_conns.append(conn)
    g_workers_free.put(conn)
    thread.start_new_thread(eval_thread, ())

def _clean_up():
    for _ in xrange(len(g_workers)):
        g_workers_free.put(None)
        eval_jobs.put(None)
        time.sleep(0.01)
    for conn in g_worker_conns:
        try:
            conn.close()
        except:
            pass
    for hub_addr in g_hubs_kill_at_exit:
        try:
            pythonshare.connect(hub_addr).kill_server()
        except:
            pass
atexit.register(_clean_up)

eval_results = Queue.Queue()
eval_jobs = Queue.Queue()
def eval_thread():
    while 1:
        conn = g_workers_free.get()
        if conn is None:
            break
        job = eval_jobs.get()
        if job is None:
            break
        try:
            job['conn'] = conn
            job['result'] = job['conn'].eval_(job['code'])
            eval_results.put(job)
        finally:
            g_workers_free.put(conn)

def psmap(func, params_list):
    func_source = inspect.getsource(func)
    results = [None] * len(params_list)
    for worker_conn in g_worker_conns:
        worker_conn.exec_(func_source)
    for job_index, params in enumerate(params_list):
        if isinstance(params, tuple):
            params_tuple = params
        else:
            params_tuple = (params,)
        eval_jobs.put({
            'conn': None,
            'job_index': job_index,
            'code': func.__name__ + repr(params_tuple)})
    for params in params_list:
        job = eval_results.get()
        results[job['job_index']] = job['result']
    return results

def fib(n):
    if n <= 1:
        return 1
    else:
        return fib(n-1) + fib(n-2)

if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1:
        launch_workers(8)
    else:
        print "using workers from hubs: ", ", ".join(sys.argv[1:])
        for hub in sys.argv[1:]:
            use_workers(hub)
    print "running", len(g_worker_conns), "workers"

    job_count = 30
    print "will run", job_count, "jobs"

    print "running local map..."
    s = time.time()
    print map(fib, [31] * job_count)
    e = time.time()
    print "map:", e-s

    print "running psmap..."
    s = time.time()
    print psmap(fib, [31] * job_count)
    e = time.time()
    print "psmap:", e-s
