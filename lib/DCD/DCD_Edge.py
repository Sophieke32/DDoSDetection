import glob
import json
import os
import socket
import time
from dataclasses import asdict, dataclass
import random

TEST = True # a test mode selector
TEST_INTERVAL = 5
TEST_RX_BASE = 1000
TEST_TX_BASE = 500

COLLECT_TIME = 60  # Time interval for collecting network data in seconds`
SAMPLE_INERVAL = 1 
CAT_SERVER_IP = "10.0.0.100" #NOTE Remember to update
CAT_SERVER_PORT = 9000
THRESHOLD = 100
NODE_ID = socket.gethostname()  # Get minin hostname 
#INTERFACE = f"{NODE_ID}eth0"
INTERFACES = sorted(
    os.path.basename(path)
    for path in glob.glob(f"/sys/class/net/*")
    if "-eth" in os.path.basename(path)
)
'''old attempt at geting interfaces to get data
    [
    os.path.basename(path)
    for path in glob.glob(f"/sys/class/net/*")
    if "-eth0" in os.path.basename(path) ]
'''
if INTERFACES:
    NODE_ID = INTERFACES[0].split("-eth")[0]
else:
    print("No host name --> broken") 
    NODE_ID = socket.gethostname()
    

#rx_pacets_path = "/sys/class/net/{INTERFACES}/statistics/rx_packets" #Recived packets path
#tx_pacets_path = "/sys/class/net/{INTERFACES}/statistics/tx_packets" # path Transmitted packets
cycle_id = 0
previous_data = {}


@dataclass
class AlertMessage:
    nd_id: str #Router ID
    fl_id: str #Flow ID
    up_num: int #Number of upstream nodes
    dn_num: int #Number of downstream nodes
    up_id: list[str] #Node ID of upstream node
    dn_id: list[str] #Node ID of downstream node
    #NOTE belive these are usefull
    rx_packets: float
    tx_packets: float
    rx_change: float
    tx_change: float
    router_status: str = "normal" #Suspicious attack or normal traffic |#NOTE changed RouterStatus to router_status(Thik the previous was mistype)
    cycle_id: int = 0

def send_network_data(alert: AlertMessage) -> None:
    """Serialize the alert to JSON and send it via UDP to the CAT server."""
    payload = json.dumps(asdict(alert)).encode("utf-8")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(payload, (CAT_SERVER_IP, CAT_SERVER_PORT))
    print(f"[{NODE_ID}] Sent alert -> {alert.router_status} for {alert.fl_id}")

def collect_network_data():    
    Time_Start = time.monotonic()
    Data = {
        "node_id": NODE_ID,
        "interfaces": {},
    }
    for interface in INTERFACES:
        Data["interfaces"][interface] = {
            "rx_packets": [],
            "tx_packets": [],
            "Counter": 0,
        }
        
    while time.monotonic() - Time_Start < COLLECT_TIME:
        # network data
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
                    
                Data["interfaces"][interface]["rx_packets"].append(rx_packets)
                Data["interfaces"][interface]["tx_packets"].append(tx_packets)
                Data["interfaces"][interface]["Counter"] += 1
            except FileNotFoundError:
                print(f"Error: Could not find the statistics files for interface {interface}.")
            
        sample_count = Data["interfaces"][INTERFACES[0]]["Counter"]
        if sample_count > 0 and sample_count % 10 == 0:
            elsapsed_time = time.monotonic() - Time_Start
            print(f"Node:{NODE_ID} - Collected {sample_count} samples in {elsapsed_time:.2f} seconds.")
            
            
            
                   
    return Data
    
    # def Send_Network_Data(Data):  # Send the collected data to the DCD server
if TEST:
    def TestDataGen():
        global previous_data
        for interface in INTERFACES:
            rx_average = random.randint(900, 1200)
            tx_average = random.randint(400, 600)
            if interface not in previous_data:
                previous_data[interface] = {
                    "RX_Avr": rx_average, "TX_Avr": tx_average}
                continue
        rx_difference = rx_average - previous_data[interface]["RX_Avr"]
        tx_difference = tx_average - previous_data[interface]["TX_Avr"]
        send_network_data(AlertMessage(
            nd_id=NODE_ID,
            fl_id=interface,
            up_num=0,
            dn_num=0,
            up_id=[],
            dn_id=[],
            rx_packets=rx_average,
            tx_packets=tx_average,
            rx_change=rx_difference,
            tx_change=tx_difference,
            router_status="Test",
            cycle_id=cycle_id
        ))
        previous_data[interface]["RX_Avr"] = rx_average
        previous_data[interface]["TX_Avr"] = tx_average
        
    pass

def DataCalculation():
    global previous_data, cycle_id
    cycle_id +=1
    Curent_Data = collect_network_data()
    Resultes = {}
    
    
    for interface, measurements in Curent_Data["interfaces"].items():
        
        rx_values = measurements["rx_packets"]
        tx_values = measurements["tx_packets"]
        
        if len(rx_values) < 2 or len(tx_values) < 2:
            print(f"Node: {NODE_ID}, Interface: {interface} - not enough data to calc")
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
        print(f"Avrage values. Rx:{Curent_RX_Avr}, Tx:{Current_TX_Avr} for interfaces {interface}, node {NODE_ID}")
        #Curent_RX_Avr = sum(measurements["rx_packets"]) / counter
        #Current_TX_Avr = sum(measurements["tx_packets"]) / counter
        
        if interface not in previous_data:
            previous_data[interface] = {
                "RX_Avr": Curent_RX_Avr,
                "TX_Avr": Current_TX_Avr,
            }
            ''' #NOTE Dont think we need to send data here
            send_network_data(AlertMessage(  
                nd_id=NODE_ID,
                fl_id=f"{NODE_ID}-{interface}",
                up_num=0,
                dn_num=0,
                up_id=[],
                dn_id=[],
                router_status="normal",
                cycle_id=0
            )) '''
            continue
        
        # Maby use abs 
        Diffrence_RX = (Curent_RX_Avr - previous_data[interface]["RX_Avr"])
        Diffrence_TX = (Current_TX_Avr - previous_data[interface]["TX_Avr"])
        print(f"Node: {NODE_ID}, Interface: {interface} - RX Difference: {Diffrence_RX}, TX Difference: {Diffrence_TX}")
        
        #TODO: Add logic to send alert if difference exceeds threshold
        if Diffrence_RX > THRESHOLD: 
            print("Received increase")
        elif Diffrence_RX < -THRESHOLD: 
            print("Received decrease")
        else:
            print("Stable recive")
             
        if Diffrence_TX > THRESHOLD:
            print("Transmitted increase")
        elif Diffrence_TX < -THRESHOLD:
            print("Transmitted decrease")
        else:
            print("stable transmit")
            
        # Either move into the above if or apply values adjusted in the if
        
        send_network_data(AlertMessage(
            nd_id=NODE_ID,
            fl_id=f"{NODE_ID}-{interface}",
            up_num=0,
            dn_num=0,
            up_id=[],
            dn_id=[],
            #NOTE For it to fit with the one up top
            rx_packets=Curent_RX_Avr,
            tx_packets=Current_TX_Avr,
            rx_change=Diffrence_RX,
            tx_change=Diffrence_TX,
            router_status="Test",
            cycle_id=cycle_id
))
        
        Resultes[interface] = {
            "Diffrence_RX": Diffrence_RX,
            "Diffrence_TX": Diffrence_TX,
        }
        previous_data[interface]["RX_Avr"] = Curent_RX_Avr
        previous_data[interface]["TX_Avr"] = Current_TX_Avr
  
        
    return Resultes

'''
if __name__ == "__main__":
    print("Name: ", NODE_ID)
    data_calculation()
#'''
#'''
 # run continuously 
if __name__ == "__main__":

    print(f"Starting DCD edge program")
    print(f"Node: {NODE_ID}")
    print(f"Interfaces: {INTERFACES}")

    if not INTERFACES:
        print("No interfaces found. Exiting.")
    else:
        try:
            while True:
                cycle_id +=1
                if TEST:
                    TestDataGen()
                    time.sleep(TEST_INTERVAL)
                    print("Test data generation started")
                else:
                    print("Data calculation started")
                    DataCalculation()
                    time.sleep(1)
        except KeyboardInterrupt:
            print("Keyboard inerrupt ")

#'''    
