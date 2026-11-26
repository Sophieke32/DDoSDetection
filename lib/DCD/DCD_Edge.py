import glob
import json
import os
import socket
import time
from dataclasses import asdict, dataclass

COLLECT_TIME = 60  # Time interval for collecting network data in seconds`
SAMPLE_INERVAL = 1 
CAT_SERVER_IP = "localhost"
CAT_SERVER_PORT = 9000
THRESHOLD = 100
NODE_ID = socket.gethostname()  # Get the hostname of the current machine
#INTERFACE = f"{NODE_ID}eth0"
INTERFACES = [
    os.path.basename(path)
    for path in glob.glob(f"/sys/class/net/*")
    if "-eth0" in os.path.basename(path)
]
if INTERFACES:
    NODE_ID = INTERFACES[0].split("-eth:")[0]
else:
    print("No host name --> broken") 
    NODE_ID = socket.gethostname()
    

rx_pacets_path = "/sys/class/net/{INTERFACES}/statistics/rx_packets" #Recived packets path
tx_pacets_path = "/sys/class/net/{INTERFACES}/statistics/tx_packets" # path Transmitted packets

previous_data = {}


@dataclass
class AlertMessage:
    nd_id: str #Router ID
    fl_id: str #Flow ID
    up_num: int #Number of upstream nodes
    dn_num: int #Number of downstream nodes
    up_id: list[str] #Node ID of upstream node
    dn_id: list[str] #Node ID of downstream node
    router_status: str = "normal" #Suspicious attack or normal traffic
    cycle_id: int = 0

def send_network_data(alert: AlertMessage) -> None:
    """Serialize the alert to JSON and send it via UDP to the CAT server."""
    payload = json.dumps(asdict(alert)).encode("utf-8")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(payload, (CAT_SERVER_IP, CAT_SERVER_PORT))
    print(f"[{NODE_ID}] Sent alert -> {alert.router_status} for {alert.fl_id}")

def collect_network_data():
    
    # Implementation for collecting network data
    time_start = time.monotonic()
    previous_time = time_start
    data = {
        "node_id": NODE_ID,
        "insterfaces": {},
        "rx_packets": [],
        "tx_packets": [],
    }
    for interface in INTERFACES:
        data["insterfaces"][interface] = {
            "rx_packets": [],
            "tx_packets": [],
            "Counter": 0,
        }
    while time.monotonic() - time_start < COLLECT_TIME:
        # Collect network data here
        time.sleep(SAMPLE_INERVAL)
        
        if not INTERFACES:
            print(f"[{NODE_ID}] No Linux interfaces found (not running in Mininet/Linux).")
            break
        
        for interface in INTERFACES:
            rx_packets_path = (f"/sys/class/net/{interface}/statistics/rx_packets")
            tx_packets_path = (f"/sys/class/net/{interface}/statistics/tx_packets")
        
            try:
                with open(rx_packets_path, "r") as file:
                    rx_packets = int(file.read())
                with open(tx_packets_path, "r") as file:
                    tx_packets = int(file.read())
                    
                data["insterfaces"][interface]["rx_packets"].append(rx_packets)
                data["insterfaces"][interface]["tx_packets"].append(tx_packets)
                data["insterfaces"][interface]["Counter"] += 1
            except FileNotFoundError:
                print(f"Error: Could not find the statistics files for interface {interface}.")       
    return data
    
    def Send_Network_Data(data):  # Send the collected data to the DCD server
        return data




def data_calculation():
    
    global previous_data
    curent_data = collect_network_data()
    resultes = {}
    
    
    for interface, measurements in curent_data["insterfaces"].items():
        
        rx_values = measurements["rx_packets"]
        tx_values = measurements["tx_packets"]
        
        if len(rx_values) < 2 or len(tx_values) < 2:
            continue
        
        rx_difference = [
            current - previous
            for previous, current in zip(rx_values, rx_values[1:])
        ]
        tx_difference = [
            current - previous
            for previous, current in zip(tx_values, tx_values[1:])
        ]
        '''
        counter = measurements["Counter"]
        if counter == 0: # skip inter if empty
            continue
        '''
        Curent_RX_Avr = sum(rx_difference) / len(rx_difference)
        Current_TX_Avr = sum(tx_difference) / len(tx_difference)
        
        #Curent_RX_Avr = sum(measurements["rx_packets"]) / counter
        #Current_TX_Avr = sum(measurements["tx_packets"]) / counter
        
        if interface not in previous_data:
            previous_data[interface] = {
                "RX_Avr": Curent_RX_Avr,
                "TX_Avr": Current_TX_Avr,
            }
            continue
        
        # Maby use abs 
        Diffrence_RX = (Curent_RX_Avr - previous_data[interface]["RX_Avr"])
        Diffrence_TX = (Current_TX_Avr - previous_data[interface]["TX_Avr"])
        
        if Diffrence_RX > THRESHOLD: # increasse 
            print("Received increase")
        elif Diffrence_RX < THRESHOLD: # decrease
            print("Received decrease")
        else:
            print("shit broken recive")
             
        if Diffrence_TX > THRESHOLD:
            print("Transmitted increase")
        elif Diffrence_TX < THRESHOLD:
            print("Transmitted decrease")
        else:
            print("shit broken transmit")
                
            
        resultes[interface] = {
            "Diffrence_RX": Diffrence_RX,
            "Diffrence_TX": Diffrence_TX,
        }
        previous_data[interface]["RX_Avr"] = Curent_RX_Avr
        previous_data[interface]["TX_Avr"] = Current_TX_Avr
  
        
    return resultes
'''
if __name__ == "__main__":
    print("Name: ", NODE_ID)
    data_calculation()
#'''
#'''
 # Make run continuously 
if __name__ == "__main__":

    print(f"Starting DCD edge program")
    print(f"Node: {NODE_ID}")
    print(f"Interfaces: {INTERFACES}")

    if not INTERFACES:
        print("No interfaces found. Exiting.")
    else:
        while True:
            data_calculation()
#'''
