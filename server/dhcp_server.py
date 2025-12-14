import time
import random
import threading
import socket


def extract_bracket_values(message):
    values = []
    idx = 0
    while True:
        start = message.find('<', idx)
        if start == -1:
            break
        end = message.find('>', start + 1)
        if end == -1:
            break
        values.append(message[start + 1:end])
        idx = end + 1
    return values


def clean_field(value):
    return value.strip() if isinstance(value, str) else value

# Implement catch for current pending offers
class DHCPServer:
    
    def __init__(self, ip, cidr, base_lease_time=60, listening_port = 1067):
        
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

        self.host_ip = '127.0.0.1'
        self.listening_port = listening_port
        self.server_socket = None
        self.server_running = False

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
        client_mac = clean_field(client_mac)
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
        requested_ip = clean_field(requested_ip)
        client_mac = clean_field(client_mac)
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

    # def _clean_up(self):
    
    def handle_release(self, client_mac):
        client_mac = clean_field(client_mac)
        if client_mac not in self.leases:
            return None
        ip = self.leases[client_mac]['ip']
        self.free_ips.append(ip)

        has_lease = self.leases[client_mac]
        if has_lease:
            del self.leases[client_mac]

        has_logs = self.mac_logs[client_mac]
        if has_logs:
            del self.mac_logs[client_mac]

        return f"RELEASE: <{client_mac}> released IP <{ip}>"

    def run(self):
        
        #Defining the socket for communication
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            print("Server socket started")
        except socket.error:
            print("ERROR: Server socket failed to start")

        #Connecting the socket to the host ip and port
        try:
            self.server_socket.bind((self.host_ip, self.listening_port))
            self.server_socket.settimeout(1.0)
            self.server_running = True
            print(f"Server binding to <{self.host_ip}> IP on Port <{self.listening_port}>")
        except socket.error: 
            print("Server failed to bind socket")

        try:
            while self.server_running:
                try:
                    data, addr = self.server_socket.recvfrom(1024)
                except socket.timeout:
                    continue
            
                if not data:
                    continue
        
                client_message = data.decode('utf-8').strip()
                parsed_message = [part.strip() for part in client_message.split(',')]

                #Grabbing the request type
                message_type = parsed_message[0] if parsed_message else ""
                parsed_mac = parsed_message[1] if len(parsed_message) > 1 else None
                message_type = clean_field(message_type)
                parsed_mac = clean_field(parsed_mac)

                response_message = None

                if message_type and parsed_mac:
                    match message_type:
                        case "DISCOVER":
                            response_message = self.handle_discover(parsed_mac)
                        case "REQUEST":
                            parsed_response = parsed_message[2] if len(parsed_message) > 2 else None
                            parsed_ip = parsed_message[3] if len(parsed_message) > 3 else None
                            parsed_response = clean_field(parsed_response)
                            parsed_ip = clean_field(parsed_ip)
                            if parsed_response:
                                response_message = self.handle_request(parsed_response, parsed_ip, parsed_mac)
                        case "RELEASE":
                            parsed_ip = parsed_message[2] if len(parsed_message) > 2 else None
                            parsed_ip = clean_field(parsed_ip)
                            response_message = self.handle_release(parsed_mac)

                        case _:
                            print(f'[DHCP Server]: Unrecognized message <{client_message}>')

                if response_message:
                    self.server_socket.sendto(response_message.encode('utf-8'), addr)
                    print(f"[DHCPServer] Sent response to <{addr}>: {response_message}")

        except Exception as e:
            print("[DHCP Server] Error in server loop", e)

        finally:
            self.server_socket.close()
            print("[DHCP Server] Server shutdown.")


    def stop(self):
        """Stop the server loop and poke the socket to unblock recvfrom."""
        self.server_running = False
        if self.server_socket:
            try:
                # Send an empty packet to self to unblock recvfrom
                end_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                end_sock.sendto(b"", (self.host_ip, self.listening_port))
                end_sock.close()
            except Exception:
                pass


    def debug_print(self):
        print(self.free_ips)


    

#Testing

if __name__ == "__main__":

    def simulate_client(server_ip, server_port, client_mac):
        print("Running simulation")
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # client_socket.timeout(2.0)

        discover_msg = f"DISCOVER, {client_mac}"
        client_socket.sendto(discover_msg.encode('utf-8'), (server_ip, server_port))
        print("Discover sent")

        try:
            data, addr = client_socket.recvfrom(1024)
        except socket.timeout:
            print(f"[Client {client_mac}] !! No response to DISCOVER (timeout)")
            client_socket.close()
            return
        
        returned_data = data.decode('utf-8').strip()
        offer_message = extract_bracket_values(returned_data)

        print(f"[Client {client_mac}] <- Received: {returned_data}")

        if not returned_data.startswith("OFFER"):
            print("Unexpected return message")
            client_socket.close()
            return
        
        offered_ip = offer_message[1]

        if offered_ip:
            request_message = f"REQUEST, {client_mac}, {True}, {offered_ip}"
            client_socket.sendto(request_message.encode('utf-8'), (server_ip, server_port))
            print("Request sent")

            try:
                data, addr = client_socket.recvfrom(1024)
            except socket.timeout:
                print(f"[Client {client_mac}] !! No response to REQUEST (timeout)")
                client_socket.close()
                return
            
            response_message = data.decode('utf-8').strip()
            print(f"[Client {client_mac}] <- Received: {response_message}")

            if response_message.startswith("ACK"):
                parts = extract_bracket_values(response_message)
                leased_ip = parts[1] if len(parts) > 2 else offered_ip
                print(f"[Client {client_mac}] ** Lease acquired: IP {leased_ip} **")
            elif response_message.startswith("NAK"):
                print(f"[Client {client_mac}] ** Request denied by server:{response_message} **") 

        client_socket.close()


    simulate_server = DHCPServer(ip="84.227.53.129", cidr="/18", base_lease_time=30)
    sServer_thread = threading.Thread(target=simulate_server.run, daemon=True)
    sServer_thread.start()
    time.sleep(0.2)

    simulate_client("127.0.0.1", 1067, "AA:BB:CC:DD:01")
    simulate_server.stop()
    sServer_thread.join()
    print("Test complete")

    # Socket-based test helpers
    def send_message(message, expect_reply=True, timeout=1.0):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        sock.sendto(message.encode('utf-8'), ("127.0.0.1", 1068))
        try:
            if expect_reply:
                data, _ = sock.recvfrom(1024)
                return data.decode('utf-8').strip()
        except socket.timeout:
            return None
        finally:
            sock.close()
        return None

    # Start dedicated server for socket tests on a different port to avoid conflicts
    test_server = DHCPServer(ip="192.168.1.0", cidr="/23", listening_port=1068)
    test_thread = threading.Thread(target=test_server.run, daemon=True)
    test_thread.start()
    time.sleep(0.2)

    # Testing different ip discover and ip request attempts for different MAC Addresses
    # All test either are fully correct or only 1 variable wrong
    # Testing a correct call
    # - > Expected ACK Message
    discover_msg = "DISCOVER, ABCD"
    offer_resp = send_message(discover_msg)
    print(offer_resp)
    offered_ip = extract_bracket_values(offer_resp)[1] if offer_resp else None
    request_msg = f"REQUEST, ABCD, {True}, {offered_ip}"
    print(send_message(request_msg))

    # Testing a mismatched mac
    # - > Expected NAK Message
    discover_msg = "DISCOVER, EFGH"
    offer_resp = send_message(discover_msg)
    print(offer_resp)
    offered_ip = extract_bracket_values(offer_resp)[1] if offer_resp else None
    request_msg = f"REQUEST, EFGZ, {True}, {offered_ip}"
    print(send_message(request_msg))

    # Testing a mismatched ip request
    # - > Expected NAK Message
    discover_msg = "DISCOVER, IJKL"
    offer_resp = send_message(discover_msg)
    print(offer_resp)
    request_msg = "REQUEST, IJKL, True, 12.96.122.241"
    print(send_message(request_msg))

    # Testing a Deny response
    # - > Expected NAK Message
    discover_msg = "DISCOVER, MNOP"
    offer_resp = send_message(discover_msg)
    print(offer_resp)
    offered_ip = extract_bracket_values(offer_resp)[1] if offer_resp else None
    request_msg = f"REQUEST, MNOP, {False}, {offered_ip}"
    print(send_message(request_msg))

    print("\nMulti-Variable failure tests\n")
    # Testing multiple variables incorrect
    # Missing client_response
    discover_msg = "DISCOVER, ABCDE"
    offer_resp = send_message(discover_msg)
    print(offer_resp)
    offered_ip = extract_bracket_values(offer_resp)[1] if offer_resp else None
    request_msg = f"REQUEST, ABCDE, , {offered_ip}"
    print(send_message(request_msg))

    # MAC Address mismatch and Requested IP Mismatch
    discover_msg = "DISCOVER, EFGHI"
    offer_resp = send_message(discover_msg)
    print(offer_resp)
    request_msg = "REQUEST, EFGHZ, True, 12.96.122.241"
    print(send_message(request_msg))

    # Missing MAC Address
    discover_msg = "DISCOVER, IJKLM"
    offer_resp = send_message(discover_msg)
    print(offer_resp)
    request_msg = "REQUEST, , True, 12.96.122.231"
    print(send_message(request_msg))

    # Missing Requested IP 
    discover_msg = "DISCOVER, MNOPQ"
    offer_resp = send_message(discover_msg)
    print(offer_resp)
    request_msg = "REQUEST, MNOPQ, True, "
    print(send_message(request_msg))

    # Orphaned Request Simulation
    # Client does a request call
    # - > No previous discover
    # - > Sends a "True" client response
    # - > Hard requests an ip that is available
    print("\nOrphaned Request simulation\n")
    print(send_message("REQUEST, WXYZ, True, 192.168.1.200"))

    # Testing release of IP
    # Correct MAC Address given
    print("\nIP Release tests\n")
    discover_msg = "DISCOVER, QWERTY"
    offer_resp = send_message(discover_msg)
    print(offer_resp)
    offered_ip = extract_bracket_values(offer_resp)[1] if offer_resp else None
    request_msg = f"REQUEST, QWERTY, {True}, {offered_ip}"
    print(send_message(request_msg))
    print(send_message("RELEASE, QWERTY, " + (offered_ip or "")))

    # Mismatched MAC Address given
    print("\nIP Release tests\n")
    discover_msg = "DISCOVER, WASD"
    offer_resp = send_message(discover_msg)
    print(offer_resp)
    offered_ip = extract_bracket_values(offer_resp)[1] if offer_resp else None
    request_msg = f"REQUEST, WASD, {True}, {offered_ip}"
    print(send_message(request_msg))
    print(send_message("RELEASE, WADS, " + (offered_ip or "")))

    test_server.stop()
    test_thread.join()

    # Set to True to run a manual blocking server session after tests
    RUN_MANUAL_SERVER = False
    if RUN_MANUAL_SERVER:
        server = DHCPServer(ip="192.168.1.0", cidr = "/23")
        server.run()
    