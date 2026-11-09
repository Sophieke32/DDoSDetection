import argparse
import random
import socket
import time


def run(host, port, rate, duration, payload_size, mode):
    destination = (host, port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.35)
    payload = b"N" * payload_size
    interval = 1.0 / max(rate, 0.1)
    deadline = time.monotonic() + duration
    sent = received = 0
    rtts_ms = []
    next_send = time.monotonic()

    while time.monotonic() < deadline:
        now = time.monotonic()
        if now < next_send:
            time.sleep(min(next_send - now, 0.01))
            continue

        stamp = time.monotonic_ns()
        packet = (b"N" if mode == "normal" else b"A") + stamp.to_bytes(8, "big") + payload
        try:
            sock.sendto(packet, destination)
            sent += 1
            if mode == "normal":
                try:
                    data, _ = sock.recvfrom(2048)
                    received += 1
                    if len(data) >= 9 and data[:1] == b"N":
                        echoed = int.from_bytes(data[1:9], "big")
                        rtts_ms.append((time.monotonic_ns() - echoed) / 1e6)
                except socket.timeout:
                    pass
        except OSError:
            pass

        # Small jitter avoids perfectly synchronized clients. More realistic, and avoids bursts of dropped packets in the Mininet simulation.
        next_send += interval * random.uniform(0.85, 1.15)

    sock.close()
    if mode == "normal":
        avg = sum(rtts_ms) / len(rtts_ms) if rtts_ms else 0.0
        print(f"normal client: sent={sent}, echoes={received}, avg_rtt_ms={avg:.3f}")
    else:
        print(f"load client: sent={sent}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="10.0.0.100")
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--rate", type=float, default=2)
    parser.add_argument("--duration", type=float, default=30)
    parser.add_argument("--payload-size", type=int, default=256)
    parser.add_argument("--mode", choices=("normal", "load"), default="normal")
    args = parser.parse_args()
    run(args.host, args.port, args.rate, args.duration, args.payload_size, args.mode)
