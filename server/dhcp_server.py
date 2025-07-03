import time
import random
import threading
import socket
import ipaddress

class DHCPServer:
    
    def __init__(self, network, mask, lease_time=60):
        
        self.network = network
        self.mask = mask
        self.lease_time = lease_time

        self.free_ips = populate_ips(network, mask)
        self.pending_offers = {}
        self.leases = {}

        print("DHCP Server initialized for:", network, " mask:", mask)
    

    def populate_ips(self, network, mask):
        network_mask = self.mask.split('.')
        mask_type
        if network_mask[2] != 0:
            mask_type = "A"
            network_ip = str(network_mask[0])

        elif network_mask[1] != 0:
            mask_type = "B"
        else:
            mask_type = "C"

    

    def run(self):
        print("Server started")
    

#Testing

if __name__ == "__main__":
    server = DHCPServer(network="192.168.1.0", mask = "255.255.255.0")
    server.run