"""
Run D-ITG

"""
import argparse
import csv
import os
import signal
import subprocess
import time
from datetime import datetime, timezone


class Monitor:
    def __init__(self, name, interfaces, interval, out_dir, pcap):
        self.name = name
        self.interfaces = [x.strip() for x in interfaces.split(",") if x.strip()]
        self.interval = interval
        self.out_dir = out_dir
        self.pcap = pcap
        os.makedirs(self.out_dir, exist_ok=True)
        self.csv_path = os.path.join(self.out_dir, f"{self.name}.csv")
        self.captures = []

    def read_stats(self, interface):
        stats_path = f"/sys/class/net/{interface}/statistics"
        names = ("received_bytes", "received_packets", "received_dropped", "received_errors",
                 "transmitted_bytes", "transmitted_packets", "transmitted_dropped", "transmitted_errors")
        result = {}
        for name in names:
            try:
                with open(os.path.join(stats_path, name), encoding="utf-8") as f:
                    result[name] = int(f.read().strip())
            except (OSError, ValueError):
                result[name] = 0
        return result

    def start_captures(self):
        if self.pcap:
            for intf in self.interfaces:
                pcap_path = os.path.join(self.out_dir, f"{self.name}_{intf}.pcap")
                proc = subprocess.Popen(
                    ["tcpdump", "-U", "-n", "-i", intf, "-w", pcap_path],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                self.captures.append(proc)
        
        previous = {i: self.read_stats(i) for i in self.interfaces}
        previous_time = time.monotonic()

        with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
            fields = ["timestamp_utc", "elapsed_s", "interface",
                      "received_bytes", "received_packets", "received_dropped", "received_errors",
                      "transmitted_bytes", "transmitted_packets", "transmitted_dropped", "transmitted_errors",
                      "received_bytes_per_s", "transmitted_bytes_per_s", "received_packets_per_s",
                      "transmitted_packets_per_s"]
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            start = time.monotonic()
            try:
                while True:
                    time.sleep(self.interval)
                    now = time.monotonic()
                    dt = max(now - previous_time, 1e-6)
                    for intf in self.interfaces:
                        current = self.read_stats(intf)
                        row = {
                            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                            "elapsed_s": round(now - start, 3),
                            "interface": intf,
                            **current,
                            "received_bytes_per_s": round((current["received_bytes"] - previous[intf]["received_bytes"]) / dt, 2),
                            "transmitted_bytes_per_s": round((current["transmitted_bytes"] - previous[intf]["transmitted_bytes"]) / dt, 2),
                            "received_packets_per_s": round((current["received_packets"] - previous[intf]["received_packets"]) / dt, 2),
                            "transmitted_packets_per_s": round((current["transmitted_packets"] - previous[intf]["transmitted_packets"]) / dt, 2),
                        }
                        writer.writerow(row)
                        f.flush()
                        previous[intf] = current
                    previous_time = now
            except KeyboardInterrupt:
                pass
            finally:
                for proc in self.captures:
                    proc.send_signal(signal.SIGINT)
                for proc in self.captures:
                    try:
                        proc.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        proc.kill()


    def stop_captures(self):
        for proc in self.captures:
            proc.send_signal(signal.SIGINT)
        for proc in self.captures:
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--interfaces", required=True, help="Comma-separated list of interfaces to monitor")
    parser.add_argument("--interval", type=float, default=1.0, help="Interval in seconds between readings")
    parser.add_argument("--out-dir", default=".", help="Directory to store output files")
    parser.add_argument("--pcap", action="store_true", help="Capture packets to pcap files")
    args = parser.parse_args()

    monitor = Monitor(args.name, args.interfaces, args.interval, args.out_dir, args.pcap)
    monitor.start_captures()
