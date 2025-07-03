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

        self.free_ips = self.populate_ips()
        self.pending_offers = {}
        self.leases = {}

        print("DHCP Server initialized for:", network, " mask:", mask)
    
    
    
    def populate_ips(self):

        def ip_generation(nat, mask):
            ip_pool = []
            mask_ascii = ord(mask)
            while (mask_ascii < 68):
                for value in range(1, 255):
                    current = nat + "." + str(value)
                    ip_pool.append(current)

                mask_ascii += 1
            return ip_pool

        network_mask = self.mask.split('.')
        if int(network_mask[1]) != 0:
            mask_type = "A"
            network_nat = str(network_mask[0])
            return ip_generation(network_nat, mask_type)

        elif int(network_mask[2]) != 0:
            mask_type = "B"
            network_nat = str(network_mask[0]) + "." + str(network_mask[1])
            return ip_generation(network_nat, mask_type)
        else:
            mask_type = "C"
            network_nat = str(network_mask[0]) + "." + str(network_mask[1]) + "." + str(network_mask[2])
            return ip_generation(network_nat, mask_type)
        
    
                    


    

    def run(self):
        print("Server started")
    

#Testing

if __name__ == "__main__":
    server = DHCPServer(network="192.168.1.0", mask = "255.255.255.0")
    server.run