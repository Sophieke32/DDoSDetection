import argparse
import json
import os
import re
import select
import signal
import socket
import struct
import subprocess
import sys
import threading
import time

# D-ITG's signalling channel uses TCP 9000, so the control channel must not.
CONTROL_PORT = 9500
ETH_P_ALL = 0x0003


def parse_ipv4(frame):
    """Returns (src, dst, ip_len, proto, sport, dport) or None if not IPv4."""
    if len(frame) < 34 or frame[12:14] != b"\x08\x00":
        return None
    ver_ihl, _, total_len, _, _, _, proto, _, src, dst = struct.unpack_from("!BBHHHBBH4s4s", frame, 14)
    sport = dport = 0
    if proto in (6, 17):
        ihl = (ver_ihl & 0x0F) * 4
        if len(frame) >= 14 + ihl + 4:
            sport, dport = struct.unpack_from("!HH", frame, 14 + ihl)
    return int.from_bytes(src, "big"), int.from_bytes(dst, "big"), total_len, proto, sport, dport

def recv_line(sock):
    buf = b""
    while not buf.endswith(b"\n"):
        chunk = sock.recv(65536)
        if not chunk:
            break
        buf += chunk
    return buf.decode()

def read_intf_stats(names):
    stats = {}
    try:
        with open("/proc/net/dev") as f:
            for line in f.readlines()[2:]:
                name, rest = line.split(":", 1)
                name = name.strip()
                if name in names:
                    v = rest.split()
                    stats[name] = {"rx_bytes": int(v[0]), "rx_packets": int(v[1]), "rx_drop": int(v[3]),
                                   "tx_bytes": int(v[8]), "tx_packets": int(v[9]), "tx_drop": int(v[11])}
    except OSError:
        pass
    for name in names:
        try:
            out = subprocess.run(["tc", "-s", "qdisc", "show", "dev", name],
                                 capture_output=True, text=True, timeout=2).stdout
            m = re.search(r"dropped (\d+)", out)
            stats.setdefault(name, {})["qdisc_dropped"] = int(m.group(1)) if m else None
        except (OSError, subprocess.SubprocessError):
            pass
    return stats


# Monitor, is run by hosts themselves
class PacketMonitor:
    def __init__(self, config):
        self.config = config
        self.name = config["name"]
        self.ingress_interfaces = config["ingress_interfaces"]
        self.all_interfaces = config["all_interfaces"]
        self.outdir = config["outdir"]
        self.log_interval = config.get("log_interval", 1.0)
        self.sketch_config = config.get("sketch", [])

        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.threads = []
        self.total_packets = self.total_bytes = 0
        self.win_packets = self.win_bytes = 0
        self.win_start = time.time()

    def _spawn(self, target):
        t = threading.Thread(target=target, daemon=True)
        t.start()
        self.threads.append(t)

    def start(self):
        os.makedirs(self.outdir, exist_ok=True)
        self._spawn(self._control)
        self._spawn(self._sniff)
        self._spawn(self._log)
        print(f"[{self.name}] monitor started, ingress={self.ingress_interfaces}", flush=True)

    def stop(self):
        self.stop_event.set()
        for t in self.threads:
            t.join(timeout=3)

    def _sniff(self):
        socks = []
        for ifname in self.ingress_interfaces:
            try:
                s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P_ALL))
                s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 64 * 1024 * 1024)
                s.bind((ifname, 0))
                s.setblocking(False)
                socks.append(s)
            except OSError as e:
                print(f"[{self.name}] cannot sniff {ifname}: {e}", flush=True)
        if not socks:
            return
        while not self.stop_event.is_set():
            readable, _, _ = select.select(socks, [], [], 0.5)
            for s in readable:
                for _ in range(512):            # drain the socket before select again
                    try:
                        frame, addr = s.recvfrom(65535)
                    except BlockingIOError:
                        break
                    self._handle_frame(frame, addr[2])

    def _handle_frame(self, frame, pkttype):
        if pkttype == 4: # skip outgoing packets, type 4 are outgoing
            return
        packet = parse_ipv4(frame)
        if packet is None:
            return
        src, dst, size, _, sport, dport = packet
        if CONTROL_PORT in (sport, dport): # dont count 
            return
        with self.lock:
            self.total_packets += 1
            self.total_bytes += size
            self.win_packets += 1
            self.win_bytes += size
            #! send data to sketch here

    # snapshot for edge router. Essentially a test sketch.
    def snapshot(self, reset=True):
        now = time.time()
        with self.lock:
            snap = {"node": self.name,
                    "t_start": self.win_start, "t_end": now,
                    "packets": self.win_packets, "bytes": self.win_bytes,
                    "total_packets": self.total_packets, "total_bytes": self.total_bytes}
            if reset:
                self.win_packets = self.win_bytes = 0
                self.win_start = now
        return snap

    def handle_request(self, req): # requests come from the edge router. Will ask for sketches here
        cmd = req.get("cmd")
        if cmd == "snapshot":
            return self.snapshot(reset=req.get("reset", True))
        if cmd == "ping":
            return {"node": self.name, "pong": True}
        return {"error": f"unknown cmd {cmd}"}

    def _control(self): # socket setup
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("0.0.0.0", CONTROL_PORT))
        srv.listen(8)
        srv.settimeout(0.5)
        while not self.stop_event.is_set():
            try:
                conn, _ = srv.accept()
            except socket.timeout:
                continue
            with conn:
                try:
                    conn.settimeout(2)
                    reply = self.handle_request(json.loads(recv_line(conn)))
                    conn.sendall((json.dumps(reply) + "\n").encode())
                except Exception as e:
                    print(f"[{self.name}] control error: {e}", flush=True)
        srv.close()

    # tracks packets and bytes over time
    def _log(self):
        path = os.path.join(self.outdir, f"{self.name}_logMonitor.jsonl")
        with open(path, "a") as f:
            last_t, last_p, last_b = time.time(), 0, 0
            while not self.stop_event.wait(self.log_interval):
                now = time.time()
                with self.lock:
                    p, b = self.total_packets, self.total_bytes
                dt = now - last_t
                rec = {"t": now, "interval": dt,
                       "packets": p - last_p, "bytes": b - last_b,
                       "pps": (p - last_p) / dt, "bps": 8 * (b - last_b) / dt,
                       "total_packets": p, "total_bytes": b,
                       "interfaces": read_intf_stats(self.all_interfaces)}
                f.write(json.dumps(rec) + "\n")
                f.flush()
                last_t, last_p, last_b = now, p, b


def run_monitor(monitor_cls=PacketMonitor):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    with open(ap.parse_args().config) as f:
        config = json.load(f)
    mon = monitor_cls(config)
    signal.signal(signal.SIGTERM, lambda *_: mon.stop_event.set())
    signal.signal(signal.SIGINT, lambda *_: mon.stop_event.set())
    mon.start()
    mon.stop_event.wait()
    mon.stop()


# router controller, only used by internal_behaviour.py, not by the external hosts
class Router:
    MONITOR_SCRIPT = os.path.abspath(__file__)
    def __init__(self, host, ingress_interfaces, all_interfaces, outdir,
                 sketch=None, log_interval=1.0):
        self.host = host
        self.name = host.name
        self.ip = host.IP()
        self.ingress_interfaces = ingress_interfaces
        self.all_interfaces = all_interfaces
        self.outdir = os.path.abspath(outdir)
        self.sketch = sketch
        self.log_interval = log_interval
        self.proc = None
        self._log = None

    def build_config(self):
        return {"name": self.name,
                "ingress_interfaces": self.ingress_interfaces, "all_interfaces": self.all_interfaces,
                "outdir": self.outdir, "sketch": self.sketch,
                "log_interval": self.log_interval}

    def start(self):
        os.makedirs(self.outdir, exist_ok=True)
        config_path = os.path.join(self.outdir, f"{self.name}_monitor_config.json")
        with open(config_path, "w") as f:
            json.dump(self.build_config(), f, indent=2)
        self._log = open(os.path.join(self.outdir, f"{self.name}_monitor.log"), "w")
        self.proc = self.host.popen(
            [sys.executable, "-u", self.MONITOR_SCRIPT, "--config", config_path],
            stdout=self._log, stderr=subprocess.STDOUT)

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        if self._log:
            self._log.close()


if __name__ == "__main__":
    run_monitor()