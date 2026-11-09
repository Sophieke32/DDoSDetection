import argparse
import csv
import os
import signal
import subprocess
import time
from datetime import datetime, timezone


def read_stats(interface):
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


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--name", required=True)
    p.add_argument("--interfaces", required=True,
                   help="Comma-separated interface names, e.g. mon1-eth0")
    p.add_argument("--interval", type=float, default=0.5)
    p.add_argument("--out", default="results")
    p.add_argument("--pcap", action="store_true")
    args = p.parse_args()

    os.makedirs(args.out, exist_ok=True)
    interfaces = [x.strip() for x in args.interfaces.split(",") if x.strip()]
    csv_path = os.path.join(args.out, f"{args.name}.csv")
    captures = []

    if args.pcap:
        for intf in interfaces:
            pcap_path = os.path.join(args.out, f"{args.name}_{intf}.pcap")
            proc = subprocess.Popen(
                ["tcpdump", "-U", "-n", "-i", intf, "-w", pcap_path],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            captures.append(proc)

    previous = {i: read_stats(i) for i in interfaces}
    previous_time = time.monotonic()

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
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
                time.sleep(args.interval)
                now = time.monotonic()
                dt = max(now - previous_time, 1e-6)
                for intf in interfaces:
                    current = read_stats(intf)
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
            for proc in captures:
                proc.send_signal(signal.SIGINT)
            for proc in captures:
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()


if __name__ == "__main__":
    main()
