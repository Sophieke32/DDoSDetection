"""
Manages behaviour for external benign and malicious(DDoSing) hosts.
Always start with benign phase. Benign packet rate is taken from first phase.
"""
from mininet.net import Mininet
from mininet.node import Host

class ExternalBehaviour:
    net: Mininet
    benign_hosts: list[Host]
    malicious_hosts: list[Host]
    target_host: Host
    phases: list[tuple[int, int]] # duration, rate for each phase

    def __init__(
        self,
        net: Mininet,
        benign_hosts: list[Host],
        malicious_hosts: list[Host],
        target_host: Host,
        phases: list[tuple[int, int]]):

        if not phases:
            raise ValueError("At least one phase pls")

        self.net = net
        self.benign_hosts = benign_hosts
        self.malicious_hosts = malicious_hosts
        self.target_host = target_host
        self.phases = phases



    def ditg_command(
        self,
        duration: int,
        rate: int,
        host: Host,
        phase_number: int):
        """Builds the D-ITG command for a host."""

        return (
            f"ITGSend -a {self.target_host.IP()} "
            f"-T UDP -C {rate} -c 1024 "
            f"-t {duration * 1000} "
            f"-l {host.name}_phase{phase_number}_log.txt"
        )

    def send_traffic(
        self,
        duration: int,
        benign_rate: int,
        malicious_rate: int,
        phase_number: int):
        """Start traffic generation on all external hosts."""

        processes = []

        for host in self.benign_hosts:
            ditg_command = self.ditg_command(duration, benign_rate, host, phase_number)
            processes.append(host.popen(ditg_command))

        for host in self.malicious_hosts:
            ditg_command = self.ditg_command(duration, malicious_rate, host, phase_number)
            processes.append(host.popen(ditg_command))

        # Wait for all traffic generators to finish.
        for process in processes:
            process.wait()
            if process.returncode != 0:
                print(f"[external] WARNING: traffic generator exited with code {process.returncode}")

    def start(self):
        """
        Execute all traffic phases.
        """
        benign_rate = self.phases[0][1]
        for phase_number, (duration, malicious_rate) in enumerate(self.phases, start=0):
            self.send_traffic(
                duration,
                benign_rate,
                malicious_rate,
                phase_number)

    def stop(self):
        """
        Stop all traffic generators.
        """
        for host in self.benign_hosts + self.malicious_hosts:
            host.popen("killall ITGSend")