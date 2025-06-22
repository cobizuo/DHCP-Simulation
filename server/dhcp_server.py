import time
import random
import threading
import socket

class DHCPServer:
    
    def __init__(self, network, mask, lease_time=60):
        
        self.network = network
        self.mask = mask
        self.lease_time = lease_time

        self.free_ips = []
        self.pending_offers = {}
        self.leases = {}

        print("DHCP Server initialized for:", network, " mask:", mask)
    

    def run(self):
        print("Server started")
    

#Testing

if __name__ == "__main__":
    server = DHCPServer(network="192.168.1.0", mask = "255.255.255.0")
    server.run