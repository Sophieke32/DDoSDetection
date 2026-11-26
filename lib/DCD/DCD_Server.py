import json
import socket
import threading

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
    
def Create_Tree() -> dict: #Don't know how to do this yet, but this is the function that will create the tree structure for the CAT server.
   """Initialize the intra-domain CAT subtree."""
   return {
        "nodes": {},          # Maps nd_id -> {"fl_id", "up_id", "dn_id"}
        "router_count": 0,
    }

def Update_Tree(previous_data, Curent_Data):
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
    tree_receiver_thread = threading.Thread(target=receive_tree_data, args=(tree,), daemon=True)

    receiver_thread.start()
    sharer_thread.start()
    tree_receiver_thread.start()

    # Keep main thread alive
    receiver_thread.join()