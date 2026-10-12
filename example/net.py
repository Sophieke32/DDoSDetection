from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.node import RemoteController
from mininet.log import setLogLevel, info
from subprocess import Popen
from time import sleep
import csv
from topo import CustomTopology
import matplotlib.pyplot as plt
from random import randrange, choice


class Net:

    def __init__(self):
        self.tmp = 'tmp.txt'
        self.data = {}
        self.controller_ip = '192.168.1.26'
        self.controller_port = 6633

    # Clears everything going on the network
    def clear_net(self):
        info('*** Clearing net... ***')
        cmd = "mn -c"
        Popen(cmd, shell=True).wait()

    # Starts the net with the given topo and enables STP for all the switches
    def start_net(self):
        topo = CustomTopology()
        self.net = Mininet(topo=topo)
        # self.net = Mininet(topo=topo, controller=lambda name: RemoteController(name, ip=self.controller_ip,
        #                                                                        port=self.controller_port))
        self.net.start()
        for i in range(1, 4):
            s = self.net.get(f's{i}')
            s.cmd(f'ovs-vsctl set bridge s{i} stp-enable=true')
        info("Dumping host connections\n")
        dumpNodeConnections(self.net.hosts)
        info("Testing network connectivity\n")
        self.net.pingAll()
        self.net.pingAll()

    # Stops the net
    def stop_net(self):
        info('*** Stopping net ***\n')
        self.net.stop()

    # Starts monitoring the net (data transmitted/received by time) then saves data in a file
    def start_monitor(self):
        info('*** Start monitor ***\n')
        cmd = f"bwm-ng -o csv -T rate -C ',' > {self.tmp} &"
        Popen(cmd, shell=True).wait()

    # Stops monitoring the net
    def stop_monitor(self):
        info('*** Stop monitor ***\n')
        cmd = "killall bwm-ng"
        Popen(cmd, shell=True).wait()

    # Read the monitoring file and fill up data structure
    def fill_data(self):
        info('*** Filling data ***\n')
        with open(self.tmp) as csvf:
            csvr = csv.reader(csvf, delimiter=',')
            for row in csvr:
                key = row[1]
                tme = float(row[0])
                load = float(row[4]) * 8
                if key in self.data:
                    self.data[key]['time'].append(tme)
                    self.data[key]['load'].append(load)
                else:
                    self.data[key] = {}
                    self.data[key]['time'] = []
                    self.data[key]['load'] = []

    # Starts a server on the given host
    def start_server(self, host):
        info(f'*** Starting server on {host} ***\n')
        h = self.net.get(host)
        h.cmd("python3 -m http.server 80 &")

    # Generate flood of udp packets
    def start_attack(self):
        info('*** Starting attack ***\n')

        h1 = self.net.get('h1')
        h3 = self.net.get('h3')
        h4 = self.net.get('h4')
        ip2 = self.net.get('h2').IP()

        h1.cmd(f"hping3 --flood --rand-source --udp -p 80 {ip2} &")
        h3.cmd(f"hping3 --flood --rand-source --udp -p 80 {ip2} &")
        h4.cmd(f"hping3 --flood --rand-source --udp -p 80 {ip2} &")

    # Stops all flooding flows
    def stop_attack(self):
        info('*** Stopping attack ***\n')
        cmd = "killall hping3"
        Popen(cmd, shell=True).wait()

    # Generates a plot and save it as image
    def plot_latency_for_all_switches(self, output_file):
        info('*** Printing data ***\n')
        for switch_key in self.data.keys():
            values = self.data[switch_key]
            plt.scatter(values['time'], values['load'], label=f'{switch_key} - Load', alpha=0.5)

        plt.legend()
        plt.xlabel('Time')
        plt.ylabel('Load')
        plt.title('Load over Time for Each Switch')
        plt.savefig(output_file)

    # Check the connectivity between two hosts
    def check_host_connettivity(self, host, target):
        h = self.net.get(host)
        ip_target = self.net.get(target).IP()

        h.cmdPrint(f"ping -c 5 {ip_target}")

    # Generate an ip among the net ones
    def ip_generator(self):
        ip = ".".join(["10", "0", "0", str(randrange(1, 5))])
        return ip

    # Generate regular traffic in the net
    def generate_legitimate_traffic(self):
        info('*** Generating legitimate traffic ***\n')
        h1 = self.net.get('h1')
        h2 = self.net.get('h1')
        h3 = self.net.get('h3')
        h4 = self.net.get('h4')

        hosts = [h1, h2, h3, h4]

        for i in range(5):
            src = choice(hosts)
            dst = self.ip_generator()

            src.cmd("ping {} -c 5 &".format(dst))

    def run(self):

        setLogLevel('info')
        self.start_net()
        self.start_monitor()
        sleep(5)
        self.start_server('h2')
        sleep(1)

        self.generate_legitimate_traffic()

        sleep(30)

        self.start_attack()
        sleep(60)

        self.stop_attack()
        sleep(5)
        self.stop_monitor()
        self.fill_data()
        self.plot_latency_for_all_switches('all_switches.png')
        self.stop_net()