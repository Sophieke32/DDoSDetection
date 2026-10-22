from mininet.log import info


def perform_dumb_attack(network):
    info('*** Starting attack ***\n')

    print(network.topology.internal_hosts[0].mn_representation)
    target_ip = network.topology.internal_hosts[0].mn_representation.IP()

    for i in network.topology.malicious_hosts:
        i.cmd(f"hping3 --flood --rand-source --udp -p 80 {target_ip} &")
