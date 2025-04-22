import random
import time
import ipaddress

class dhcp_server:
    # pool = list of available IP Strings to be leased
    # offers = dictionary containing IPs being offered and waiting for response
    # leases = dictionary containig IPs that are being actively leased
    # lease_time = legnth of time each lease will last (minutes)
    def __init__(self, subnet_cidr='192.168.0.0/24', lease_time=30):
        self.subnet = ipaddress.ip_network(subnet_cidr)
        self.offers = {}    # { client_id: ip}
        self.leases = {}    # {client_id: {'ip': ..., 'expires': ...}}
        self.lease_time = lease_time

    def _get_random_available_ip(self):
        leased_ips = {entry['ip'] for entry in self.leases.values()}
        offered_ips = set(self.offers.values())
        usable_hosts = list(self.subnet.hosts())
        random.shuffle(usable_hosts)
        for ip in usable_hosts:
            ip_str = str(ip)
            if ip_str not in leased_ips and ip_str not in offered_ips:
                return ip_str
        return None

    #Handling (D)iscover requests in the DORA process 
    #Recieves a client_id and allocates an IP address from the given range 
    def process_discover(self, client_id):
        ip = self._get_random_available_ip()
        if not ip:
            print("SERVER: No available IPs to offer.")
            return None
        
        self.offers[client_id]  = ip
        print(f"SERVER: Offering IP {ip} to client {client_id}")
        return ip
    
    #Handling the (R)equest requests in the DORA process
    #Receives a client_id and the reuqested_id to prepare the lease for the client and update the logs for authentication
    def process_request(self, client_id, requested_ip):
        offered_ip = self.offers.get(client_id)
        if client_id in self.leases:
            if self.leases[client_id]['ip'] == requested_ip:
                self.leases[client_id]['expires'] = time.time() + self.lease_time
                print(f"SERVER: Renewed lease for {client_id} -> {requested_ip} (new lease {self.lease_time}s)")
                return True
            else:
                print(f"SERVER: {client_id} requested IP {requested_ip} not matching current lease.")
                return False
        
        if offered_ip is None or offered_ip != requested_ip:
            print(f"SERVER: Received REQUEST for {requested_ip} from {client_id},  but no match.")
            return False

        lease_expiration = time.time() + self.lease_time
        self.leases[client_id] = {"ip": requested_ip, "expires": lease_expiration}
        del self.offers[client_id]
        print(f"SERVER: Acknowledged IP {requested_ip} top client {client_id} (lease {self.lease_time}s)")
        return True            
    
    #Handling the release of IP's at the end of their lease time#
    #Takes a client_id to be released, checks if it has a leased ip and removes that client_id
    def release_ip(self, client_id):
        if client_id in self.leases:
            ip = self.leases[client_id]["id"]
            del self.leases[client_id]
            print(f"SERVER: Released {ip} from client {client_id} back to the IP pool.")



        
