import time
import random
import threading
import socket
import ipaddress

class DHCPServer:
    
    def __init__(self, ip, cidr, lease_time=60):
        
        #Input examples:
        #network = String: "192.10.54.244"
        #mask = String: "/24"
        #lease_time = int: 50

        self.ip = ip 
        self.mask = cidr 
        self.lease_time = lease_time

        self.free_ips = self.populate_ips()
        self.pending_offers = {}
        self.leases = {}

        print("DHCP Server initialized for:", ip, " mask:", cidr)
    
    
    def get_random_ip(self):
        if not self.free_ips:
            return None
        ip = random.choice(self.free_ips)
        self.free_ips.remove(ip)
        return ip

    def handle_discover(self, client_mac):
        ip = self.get_random_ip()
        self.pending_offers[client_mac] = ip
    
    # def handle_offer(self, client_mac):
    
    def handle_request(self, requested_ip, client_mac):
        if not (client_mac in self.pending_offers and self.pending_offers[client_mac] == requested_ip):
            return None
        
        

        




    def populate_ips(self):

        def ipv4_to_binary(ip):
            #splits each section of the ip into individual sections.
            #converts the split section into its binary representation and pads it to 8 bits
            #joins the bits together to create one large binary value for the ip
            
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
        print(self.free_ips)
    

#Testing

if __name__ == "__main__":
    server = DHCPServer(ip="192.168.1.0", CIDR = "/24")
    server.run()

    server = DHCPServer(ip="192.168.1.0", cidr = "/23")
    server.run()
    server.print()