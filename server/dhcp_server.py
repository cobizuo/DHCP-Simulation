import time
import random
import threading
import socket


class DHCPServer:
    
    def __init__(self, ip, cidr, base_lease_time=60):
        
        #Input examples:
        #network = String: "192.10.54.244"
        #CIDR = String: "/24"
        #base_lease_time = int: 50

        self.ip = ip 
        self.cidr = cidr 
        self.base_lease_time = base_lease_time

        self.free_ips = self.populate_ips() 
        self.pending_offers = {}            # {mac: {'ip': string, 'offer_time': float}}
        self.leases = {}                    # {mac: {'ip': string, 'expiry': float}}
        
        #structure -> client_mac: 0 (interaction counter)
        self.mac_logs = {}                  #{mac: int}

        print("DHCP Server initialized for:", ip, " CIDR:", cidr)
    

    ### THIS FUCTION ONLY WORKS IF THE GIVEN IP IS THE NETWORK ADDRESS
    def populate_ips(self):

        def ipv4_to_binary(ip):
            #splits each section of the ip into individual sections.
            #converts the split section into its binary representation and pads it to 8 bits
            #joins the bits together to create one large binary value for the ip
            
            return ''.join([format(int(octet), '08b') for octet in ip.split('.')])
        
        def binary_to_ipv4(binary):
            return '.'.join(str(int(binary[i:i+8], 2)) for i in range(0, 32, 8))
        
        ip_as_binary = ipv4_to_binary(self.ip)

        subnet_allocated_bits = int(self.cidr[1::])
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
    

    def _get_random_ip(self):
        #handles checking if a free ip is available to be offered
        if not self.free_ips:
            return None
        ip = random.choice(self.free_ips)
        #removes ip from the free_ips list
        self.free_ips.remove(ip)
        return ip
    

    def handle_discover(self, client_mac):
        ip = self._get_random_ip()
        if ip is None:
            return None
        offer_time = time.time()
        #keeps a master log of all the mac_address that interact with the server and initializes the number of times they've interacted to 0
        if client_mac not in self.mac_logs:
            self.mac_logs[client_mac] = 0
        
        
        self.pending_offers[client_mac] = {'ip': ip, 'offer_time' : offer_time} #tracks which ips are pending offers and logs their time of request (ToR)
        return f"OFFER: <{client_mac}>, <{ip}>"
        #Time of request will be used for cleanup of pending offers later
    
    
    def handle_request(self, client_response, requested_ip, client_mac):
        #client_response
        # - > True
        # - - > Reports False
        # - > False
        # - - > Reports True
        has_offer = client_mac in self.pending_offers
        has_lease = client_mac in self.leases

        if not client_response:
            #If client does not want the offer, pull there offer from pending_offers
            #Store it in 'offer'
            #if the offer does exist
            if not has_offer:
                return f"NAK: <{client_mac}> has not requested <{requested_ip}> offer"
            self.free_ips.append(self.pending_offers[client_mac]['ip'])
            del self.pending_offers[client_mac]
            del self.mac_logs[client_mac]
            return f"NAK: <{client_mac}> denied <{requested_ip}> offer"
        
        if has_offer:
            offered_ip = self.pending_offers[client_mac]['ip']
            if offered_ip != requested_ip:
                self.free_ips.append(self.pending_offers[client_mac]['ip'])
                del self.pending_offers[client_mac]
                del self.mac_logs[client_mac]
                return f"NAK: <{client_mac}> has not requested <{requested_ip}> offer"
        else:
            return f"NAK: <{client_mac}> has not requested <{requested_ip}> offer"

        if has_lease:
            if self.leases[client_mac]['ip'] == requested_ip:
                #renews the already existing lease for the client mac
                self.leases[client_mac]['expiry'] = time.time() + self.base_lease_time
                return f"RENEW: <{client_mac}> renewed IP <{requested_ip}> for a new lease"
            else:
                return f"N_RENEW: <{client_mac}> has existing IP on record. Does not match requested ip: <{requested_ip}>"
        #logs the ip being leased in format to self.leases
    
        lease_time = self.base_lease_time + time.time()
        self.leases[client_mac] = {'ip': requested_ip, 'expiry': lease_time}
        del self.pending_offers[client_mac]
        return f"ACK: <{client_mac}> requested offered IP <{requested_ip}>, <{lease_time}>"


    # def _handle_nak(self, client_mac):
    #     #attempts to rediscover a new ip address for the client up to 3 times
    #     if client_mac not in self.mac_logs:
    #         self.mac_logs[client_mac] = 0

    #     while self.mac_logs[client_mac] < 3:
    #         self.mac_logs[client_mac] += 1
    #         offer = self.handle_discover(client_mac)
    #         if offer is not None:
    #             del self.mac_logs[client_mac]
    #             return f"WARNING: NAK occurred\n{offer}"

    #         time.sleep(0.5)
        
    #     del self.mac_logs[client_mac]
    #     return f"NAK: Attempted rediscover and failed to allocate IP for <{client_mac}>"
    
    def handle_release(self, client_mac):
        if client_mac not in self.leases:
            return None
        ip = self.leases[client_mac]['ip']
        self.free_ips.append(ip)
        del self.leases[client_mac]
        return f"RELEASE: <{client_mac}> released IP <{ip}>"

    def run(self):
        print("Server started")

    def debug_print(self):
        print(self.free_ips)
    

#Testing

if __name__ == "__main__":
    server = DHCPServer(ip="192.168.1.0", cidr = "/24")
    server.run()

    server = DHCPServer(ip="192.168.1.0", cidr = "/23")
    server.run()
    server.debug_print()