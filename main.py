from server.dhcp_server import dhcp_server
from config.settings import SUBNET_CIDR, LEASE_TIME
DHCP = dhcp_server(subnet_cidr=SUBNET_CIDR, lease_time=LEASE_TIME)