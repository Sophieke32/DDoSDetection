import json
import socket
import threading
import traceback

#NOTE Trying to get it to work not quite there yet WIP in TEST=True
# The other stuff dont work either so a bit broken at the moment
# Commands for starting stuf: (target tail -f /tmp/server.log), (target python3 -u /home/alfred/DDoSDetection/lib/DCD/DCD_Server.py > /tmp/server.log 2>&1 &), 
# (mon1 python3 /home/alfred/DDoSDetection/lib/DCD/DCD_Edge.py &), (sudo mn --custom lib/topologies/topology_redundnet.py --topo company)

TEST = True #Change between test code and the oter stuff
LISTEN_IP = "0.0.0.0"
LISTEN_PORT_INTRA = 9000
LISTEN_PORT_INTER = 9001

data_lock = threading.Lock()
tree_updated = threading.Event()

previous_data = {
    "Previous_RX_Avr": 0,
    "Previous_TX_Avr": 0,
    "Counter": 0,
    "Previous_rx_packets": [],
    "Previous_tx_packets": []
}

def get_data(tree: dict):
    if not TEST:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind((LISTEN_IP, LISTEN_PORT_INTRA))
            print(f"[CAT SERVER] Listening on {LISTEN_IP}:{LISTEN_PORT_INTRA}...")

            while True:
                raw_bytes, addr = sock.recvfrom(4096)  # Blocks until a packet arrives
                try:
                    alert = json.loads(raw_bytes.decode("utf-8"))
                    print(f"[CAT SERVER] Received from {addr[0]}: {alert['nd_id']} -> {alert['router_status']}")
                    Update_Tree(previous_data, alert)
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"[CAT SERVER] Malformed packet from {addr[0]}: {e}")
    #NOTE Alternatively below
    elif TEST:            
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((LISTEN_IP, LISTEN_PORT_INTRA))
            print(f"Server listening on: {LISTEN_IP}:{LISTEN_PORT_INTRA}")
            
            while True:
                raw_bytes, addr = sock.recvfrom(65535)
                try:
                    alert = json.loads(raw_bytes.decode("utf-8"))
                    required_fields = ["nd_id",
                        "fl_id",
                        "cycle_id",
                        "rx_packets",
                        "tx_packets",
                        "rx_change",
                        "tx_change",
                        "router_status"]
                    if not all(field in alert for field in required_fields):
                        print(f"data missing from {addr[0]}")
                        continue
                    Update_Tree(tree, alert)
                except Exception as error:
                    print(f"Server Error with packet (get_data). From {addr[0]}: {error!r}")
                    traceback.print_exc()    
def Create_Tree() -> dict: #Don't know how to do this yet, but this is the function that will create the tree structure for the CAT server.
   """Initialize the intra-domain CAT subtree."""
   return {
        "nodes": {},          # Maps nd_id -> {"fl_id", "up_id", "dn_id"}
        "router_count": 0,
    }

def Update_Tree(tree, alert):
    if not TEST:
        # Add there to the funciton() previous_data, Curent_Data, 
        """
        Update the tree structure with new data.
        
        Args:
            previous_data (dict): The previous data stored in the tree.
            Curent_Data (dict): The current data to be added to the tree.
        """
        # Update the counter
        previous_data["Counter"] += 1
        
        # Append current data to the lists
        previous_data["Previous_rx_packets"].append(Curent_Data["rx_packets"])
        previous_data["Previous_tx_packets"].append(Curent_Data["tx_packets"])
    
    #NOTE Belive it would work better with the below code
    elif TEST:
        node_id = alert["nd_id"]
        interface_id = alert["fl_id"]
        with data_lock:
            if node_id not in tree["nodes"]:
                tree["nodes"][node_id] = {"interfaces": {}}
                tree["router_count"] += 1
            node = tree["nodes"][node_id]
            if interface_id not in node["interfaces"]:
                node["interfaces"][interface_id]={"history": [],"latest":{}}
            interface = node["interfaces"][interface_id]
            
            measurement = {
                "cycle_id": alert["cycle_id"],
                "rx_packets": alert["rx_packets"],
                "tx_packets": alert["tx_packets"],
                "rx_change": alert["rx_change"],
                "tx_change": alert["tx_change"],
                "router_status": alert["router_status"]
            }
            interface["latest"] = measurement
            interface["history"].append(measurement)
            if len(interface["history"]) > 100:
                interface["history"].pop(0)
        tree_updated.set()
        
def share_data_interdomain(tree: dict) -> None:
    while True:
        tree_updated.wait()
        with data_lock:
            print(f"[CAT SERVER] Tree updated ({tree['router_count']} routers): {tree['nodes']}")
        tree_updated.clear()

def receive_tree_data(external_tree: dict) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((LISTEN_IP, LISTEN_PORT_INTER))  # Use a different port for tree data
        print(f"[CAT SERVER] Listening for tree data on {LISTEN_IP}:{LISTEN_PORT_INTER}...")

        while True:
            raw_bytes, addr = sock.recvfrom(4096)
            try:
                tree_data = json.loads(raw_bytes.decode("utf-8"))
                with data_lock:
                    combine_tree_data(external_tree, tree_data)
            except (json.JSONDecodeError, KeyError) as e:
                print(f"[CAT SERVER] Malformed tree packet from {addr[0]}: {e}")

def combine_tree_data(external_tree: dict, internal_tree: dict) -> None:
    """
    Combine the external tree data with the internal tree data.
    
    Args:
        external_tree (dict): The external tree data received from another domain.
        internal_tree (dict): The internal tree data to be updated.
    """
    # Update the router count
    external_tree["router_count"] += internal_tree.get("router_count", 0)
    
    # Merge nodes
    for nd_id, node_info in internal_tree.get("nodes", {}).items():
        if nd_id not in external_tree["nodes"]:
            external_tree["nodes"][nd_id] = node_info
        else:
            # Handle potential conflicts or updates here if necessary
            pass
    
    # Signal that the tree has been updated
    tree_updated.set()

if __name__ == "__main__":
    tree = Create_Tree()

    # Start both threads ONCE before keeping the main thread alive
    receiver_thread = threading.Thread(target=get_data, args=(tree,), daemon=True)
    sharer_thread = threading.Thread(target=share_data_interdomain, args=(tree,), daemon=True)
    if not TEST:
        tree_receiver_thread = threading.Thread(target=receive_tree_data, args=(tree,), daemon=True)

    receiver_thread.start()
    print("Server started\n")
    sharer_thread.start()
    if not TEST:
        tree_receiver_thread.start()

    # Keep main thread alive
    receiver_thread.join()