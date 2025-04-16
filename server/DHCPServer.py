import time


class DHCPServer:
    # pool = list of available IP Strings to be leased
    # offers = dictionary containing IPs being offered and waiting for response
    # leases = dictionary containig IPs that are being actively leased
    # lease_time = legnth of time each lease will last (minutes)
    def __init__(self, pool, lease_time=60):
        self.pool = pool
        self.offers = {}
        self.leases = {}
        self.lease_time = lease_time

    #Handling (D)iscover requests in the DORA process 
    #Recieves a client_id and allocates an IP address from the given range 
    def process_discover(self, client_id):
        if not self.pool:
            return None
        ip = self.pool.pop(0)
        self.offers[client_id] = ip
        print(f"Offering IP: {ip} to client {client_id}")
        return ip
    
    #Handling the (R)equest requests in the DORA process
    #Receives a client_id and the reuqested_id to prepare the lease for the client and update the logs for authentication
    def process_request(self, client_id, requested_ip):
        offered_ip = self.offers[client_id]
        #checks to see if the requestedip matches what is being offered
        if offered_ip is None or offered_ip != requested_ip:
            print(f"Server: Received REQUEST for {requested_ip} from {client_id}, but no matching offer")
            return False
        #sets the expiration for the lease to current_time + lease_time
        lease_expiration = time.time() + self.lease_time
        self.leases[client_id] = {"ip": requested_ip, "expires": lease_expiration}
        del self.offers[client_id]
        print(f"Server: Acknowledged IP {requested_ip} to client {client_id} (lease {self.lease_time}s)")
        return True
    
    #Handling the release of IP's at the end of their lease time#
    #Takes a client_id to be released, checks if it has a leased ip and removes that client_id
    def release_ip(self, client_id):
        if client_id in self.leases:
            ip = self.leases[client_id]["id"]
            del self.leases[client_id]
            self.pool.append(ip)
            print(f"Server: Released {ip} from client {client_id} back to the IP pool.")

server = DHCPServer(pool=["192.0.0.0", "192.0.0.1", "192.0.0.2"], lease_time=25)
temp_client_id = "AA:BB:CC:DD:EE:FF"

offered_ip = server.process_discover(temp_client_id)
if offered_ip:
    success = server.process_request(temp_client_id, offered_ip)
    if success:
        print(f"Server; IP Successfully secured for {temp_client_id} on ip {offered_ip}")