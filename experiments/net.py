import os
import time
from mininet.net import Mininet
from mininet.node import OVSSwitch
from mininet.link import TCLink
from mininet.log import setLogLevel, info
from mininet.cli import CLI

from topology import CompanyTopo


# Alle config ting
TOTAL_USERS = 9
ATTACKER_COUNT = 3
BASELINE_SECONDS = 10
ATTACK_SECONDS = 30
NORMAL_PACKETS_PER_SECOND = 2
ATTACK_PACKETS_PER_SECOND = 1500
PAYLOAD_BYTES = 256
LINK_BANDWIDTH_MBPS = 10
MONITOR_INTERVAL_SECONDS = 0.5
ENABLE_PCAP = True
RESULTS_DIR = "results"
TARGET_IP = "10.0.0.100"
TARGET_PORT = 9000



def attach_ovs_mirrors(net):
    """Mirror distribution-switch traffic to monitor nodes."""
    mirror_map = {
        "s1": ["mon1", "mon2"],
        "s2": ["mon2", "mon3"],
    }
    for switch_name, monitors in mirror_map.items():
        switch = net.get(switch_name)
        mirror_ids = []
        args = ["ovs-vsctl"]
        for idx, monitor_name in enumerate(monitors, start=1):
            monitor = net.get(monitor_name)
            link = next(
                link for link in net.links
                if {link.intf1.node.name, link.intf2.node.name}
                == {switch_name, monitor_name}
            )
            switch_intf = (link.intf1 if link.intf1.node.name == switch_name else link.intf2)
            mirror_id = f"@m{idx}"
            port_id = f"@p{idx}"
            args += ["--", "--id=" + port_id, "get", "Port", switch_intf.name,
                     "--", "--id=" + mirror_id, "create", "Mirror",
                     f"name={switch_name}_{monitor_name}",
                     "select-all=true", f"output-port={port_id}"]
            mirror_ids.append(mirror_id)
        args += ["--", "set", "Bridge", switch_name,
                 "mirrors=" + ",".join(mirror_ids)]
        result = os.system(" ".join(args) + " >/dev/null 2>&1")
        if result != 0:
            info(f"OVS failed on {switch_name}\\n")


def start_monitor(net, name, interfaces):
    host = net.get(name)
    args = [
        "python3", "monitor.py", "--name", name,
        "--interfaces", ",".join(interfaces),
        "--interval", str(MONITOR_INTERVAL_SECONDS),
        "--out", RESULTS_DIR,
    ]
    if ENABLE_PCAP:
        args.append("--pcap")
    host.cmd(" ".join(args) + " > " + RESULTS_DIR + f"/{name}_monitor.log 2>&1 &")




def main():
    if TOTAL_USERS < 1:
        raise ValueError("TOTAL_USERS must be at least 1")
    if not 0 <= ATTACKER_COUNT <= TOTAL_USERS:
        raise ValueError("ATTACKER_COUNT must be between 0 and TOTAL_USERS")


    os.makedirs(RESULTS_DIR, exist_ok=True)
    topo = CompanyTopo(users=TOTAL_USERS)
    net = Mininet(
        topo=topo,
        controller=None,
        switch=OVSSwitch,
        link=TCLink,
        autoSetMacs=True,
        build=True,
    )


    try:
        net.start()
        info("Configuring link bandwidth and OVS monitoring mirrors\\n")
        for link in net.links:
            try:
                link.intf1.config(bw=LINK_BANDWIDTH_MBPS)
                link.intf2.config(bw=LINK_BANDWIDTH_MBPS)
            except Exception:
                pass

        attach_ovs_mirrors(net)

        # Makes sure all hosts can reach the target before starting the test
        target = net.get("target")
        target.cmd("python3 target.py --bind 0.0.0.0 --port "
                   + str(TARGET_PORT) + " > " + RESULTS_DIR + "/target.log 2>&1 &")

        # The target also records its own interface counters.
        start_monitor(net, "target", ["target-eth0"])
        start_monitor(net, "mon1", ["mon1-eth0"])
        start_monitor(net, "mon2", ["mon2-eth0", "mon2-eth1"])
        start_monitor(net, "mon3", ["mon3-eth0"])

        info("Starting baseline traffic for 10 seconds\\n")
        baseline_procs = []
        for i in range(1, TOTAL_USERS + 1):
            user = net.get(f"user{i}")
            cmd = (
                f"python3 client.py --host {TARGET_IP} --port {TARGET_PORT} "
                f"--rate {NORMAL_PACKETS_PER_SECOND} --duration {BASELINE_SECONDS} "
                f"--payload-size {PAYLOAD_BYTES} --mode normal"
            )
            baseline_procs.append(user.popen(cmd, stdout=open(os.devnull, "w"),
                                             stderr=open(os.devnull, "w")))
        time.sleep(BASELINE_SECONDS)
        for proc in baseline_procs:
            proc.wait()

        info("Baseline complete. Starting DDoS\n")
        attack_procs = []
        for i in range(1, ATTACKER_COUNT + 1):
            user = net.get(f"user{i}")
            cmd = (
                f"python3 client.py --host {TARGET_IP} --port {TARGET_PORT} "
                f"--rate {ATTACK_PACKETS_PER_SECOND} --duration {ATTACK_SECONDS} "
                f"--payload-size {PAYLOAD_BYTES} --mode load"
            )
            attack_procs.append(user.popen(cmd, stdout=open(os.devnull, "w"),
                                           stderr=open(os.devnull, "w")))

        # Non atticking users continue as normal
        for i in range(ATTACKER_COUNT + 1, TOTAL_USERS + 1):
            user = net.get(f"user{i}")
            cmd = (
                f"python3 client.py --host {TARGET_IP} --port {TARGET_PORT} "
                f"--rate {NORMAL_PACKETS_PER_SECOND} --duration {ATTACK_SECONDS} "
                f"--payload-size {PAYLOAD_BYTES} --mode normal"
            )
            attack_procs.append(user.popen(cmd, stdout=open(os.devnull, "w"),
                                           stderr=open(os.devnull, "w")))

        for proc in attack_procs:
            proc.wait()

        info("Så det slut, færdig æ mere.\n")
        info("æ slut, se æ filer i mappe\n")
        CLI(net)

    finally:
        net.stop()


if __name__ == "__main__":
    setLogLevel("info")
    main()
