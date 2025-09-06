import time
import random
import threading
import socket
import ipaddress

class DHCPServer:
    
    def __init__(self, ip, CIDR, lease_time=60):
        
        #Input examples:
        #network = String: "192.10.54.244"
        #mask = String: "/24"
        #lease_time = int: 50

        self.ip = ip 
        self.mask = CIDR 
        self.lease_time = lease_time

        self.free_ips = self.populate_ips()
        self.pending_offers = {}
        self.leases = {}

        print("DHCP Server initialized for:", ip, " mask:", CIDR)
    
    
    
    def populate_ips(self):

        def ipv4_to_binary(ip):
            return ''.join([format(int(octet), '08b') for octet in ip.split('.')])
        
        def binary_to_ipv4(binary):
            return '.'.join(str(int(binary[i:i+8], 2)) for i in range(0, 32, 8))
        
        ip_as_binary = ipv4_to_binary(self.ip)

        subnet_allocated_bits = int(self.mask[1::])
        host_bits = 32 - subnet_allocated_bits 
        network_mask = '1' * subnet_allocated_bits + '0' * host_bits
        
        #calculating the network_address as binary
        network_address_binary = ''.join(
        '1' if ip_as_binary[i] == '1' and network_mask[i] == '1' else '0'
        for i in range(32)
        )

        #generate the host bits and conjoin them with network_address_binary
        list_of_ips = []
        total_hosts = 2**host_bits

        for i in range(1, total_hosts - 1): #skips the .0 and .255 broadcast and network ips
            host_binary = format(i, f'0{host_bits}b')  # padded to host_bits
            full_binary = network_address_binary[:subnet_allocated_bits] + host_binary
            list_of_ips.append(binary_to_ipv4(full_binary))

        return list_of_ips                   


    

    def run(self):
        print("Server started")

    def print(self):
        for x in self.free_ips:
            print(x)
    

#Testing

if __name__ == "__main__":
    server = DHCPServer(ip="192.168.1.0", CIDR = "/24")
    server.run()

    server.print()