import json
import os
import shutil
import socket
import subprocess
import time

try:
    from router import (CONTROL_PORT, PacketMonitor, Router,
                        recv_line, run_agent)
except ImportError as e:
    from internal_behaviour.router import (CONTROL_PORT, PacketMonitor, Router,
                                            recv_line, run_agent)



def aggregate(snapshots): #Hard coded for the snapshots right now. Will be changed when we have a finished sketch
    record = {"t": time.time(), "nodes": {}, "name": {}}

    for snap in snapshots:
        name = snap["node"]
        if "error" in snap:
            record["nodes"][name] = {"error": snap["error"]}
            continue
        record["nodes"][name] = {
            "t_start": snap["t_start"], "t_end": snap["t_end"],
            "packets": snap["packets"], "bytes": snap["bytes"],
            "total_packets": snap["total_packets"], "total_bytes": snap["total_bytes"],
        }
        entry = record["name"].setdefault(name, {"nodes": 0, "packets": 0, "bytes": 0})
        entry["nodes"] += 1
        entry["packets"] += snap["packets"]
        entry["bytes"] += snap["bytes"]
    return record


class EdgeMonitor(PacketMonitor):
    def __init__(self, cfg):
        super().__init__(cfg)
        self.routers = cfg.get("routers", [])
        self.poll_interval = cfg.get("poll_interval", 1.0)
        self.poll_timeout = cfg.get("poll_timeout", 2.0)
        self.reset_on_poll = cfg.get("reset_on_poll", True)
        self.start_itg_recv = cfg.get("start_itg_recv", True)
        self.itg = None
        self._itg_log = None

    def start(self):
        super().start()
        if self.start_itg_recv:
            self.start_itg_recv()
        self._spawn(self._poll_loop)

    def stop(self):
        super().stop()
        if self.itg and self.itg.poll() is None:
            self.itg.terminate()
            try:
                self.itg.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.itg.kill()
        if self._itg_log:
            self._itg_log.close()

    def start_itg_recv(self):
        if not shutil.which("ITGRecv"):
            print(f"[{self.name}] ITGRecv not found in PATH, no receiver-side D-ITG logs", flush=True)
            return
        self._itg_log = open(os.path.join(self.outdir, f"{self.name}_ITGRecv_stdout.txt"), "w")
        # Decode later with: ITGDec <edge>_ITGRecv_log.txt
        self.itg = subprocess.Popen(
            ["ITGRecv", "-l", os.path.join(self.outdir, f"{self.name}_ITGRecv_log.txt")],
            stdout=self._itg_log, stderr=subprocess.STDOUT)

    def fetch(self, router):
        try:
            with socket.create_connection((router["ip"], CONTROL_PORT), timeout=self.poll_timeout) as s:
                s.settimeout(self.poll_timeout)
                s.sendall((json.dumps({"cmd": "snapshot", "reset": self.reset_on_poll}) + "\n").encode())
                return json.loads(recv_line(s))
        except Exception as e:     # a dead/overloaded router must not stop the polling
            return {"node": router["name"], "error": str(e)}

    def _poll_loop(self):
        path = os.path.join(self.outdir, f"{self.name}_aggregate.jsonl")
        with open(path, "a") as f:
            next_t = time.time() + self.poll_interval
            while not self.stop_event.wait(max(0.0, next_t - time.time())):
                next_t += self.poll_interval
                snaps = [self.snapshot(reset=self.reset_on_poll)]
                snaps += [self.fetch(r) for r in self.routers]
                f.write(json.dumps(aggregate(snaps)) + "\n")
                f.flush()




class Edge(Router):
    """Controller side of the edge router."""
    AGENT_SCRIPT = os.path.abspath(__file__)

    def __init__(self, host, ingress_intfs, all_intfs, outdir, routers,
                 sketches=None, log_interval=1.0, poll_interval=1.0,
                 reset_on_poll=True, start_itg_recv=True):
        super().__init__(host, "edge", ingress_intfs, all_intfs, outdir, sketches, log_interval)
        self.routers = routers              # list of Router objects to poll
        self.poll_interval = poll_interval
        self.reset_on_poll = reset_on_poll
        self.start_itg_recv = start_itg_recv

    def build_config(self):
        cfg = super().build_config()
        cfg.update(routers=[{"name": r.name, "ip": r.ip} for r in self.routers],
                   poll_interval=self.poll_interval, reset_on_poll=self.reset_on_poll,
                   start_itg_recv=self.start_itg_recv)
        return cfg


if __name__ == "__main__":
    run_agent(EdgeMonitor)