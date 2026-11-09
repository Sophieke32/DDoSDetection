import argparse
import socket
import time


class Target:
    def __init__(self, bind, port, echo_limit):
        self.bind = bind
        self.port = port
        self.echo_limit = echo_limit

    def start_target(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.bind, self.port))
        print(f"target listening on {self.bind}:{self.port}", flush=True)
        total = 0
        window_start = time.monotonic()
        window_count = 0

        while True:
            data, addr = sock.recvfrom(4096)
            total += 1
            window_count += 1
            #! Maybe remove echo entirely. Only needed for debugging
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--bind", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=10000)
    parser.add_argument("--echo-limit", type=int, default=1000)
    args = parser.parse_args()
    target = Target(args.bind, args.port, args.echo_limit)
    target.start_target()