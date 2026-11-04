import argparse
import socket
import time


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--bind", default="0.0.0.0")
    p.add_argument("--port", type=int, default=9000)
    p.add_argument("--echo-limit", type=int, default=100)
    args = p.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((args.bind, args.port))
    print(f"target listening on {args.bind}:{args.port}", flush=True)
    total = 0
    window_start = time.monotonic()
    window_count = 0

    while True:
        data, addr = sock.recvfrom(4096)
        total += 1
        window_count += 1
        # Only normal non attacking users get echoed.
        # Attackers send a different first byte "A" not "N"
        if data[:1] == b"N" and len(data) <= 300:
            try:
                sock.sendto(data, addr)
            except OSError:
                pass

        now = time.monotonic()
        if now - window_start >= 1:
            print(f"received_pps={window_count} total_received={total}", flush=True)
            window_count = 0
            window_start = now


if __name__ == "__main__":
    main()
