# Network
# Maintainer(s): SzaBee13
# Contributor(s): SzaBee13
# Reviewer(s): SzaBee13
import ipaddress

try:
  from dns import resolver as dns_resolver
except ModuleNotFoundError:
  dns_resolver = None


def _dns_client(nameserver: str):
  if dns_resolver is None:
    return None

  client = dns_resolver.Resolver()
  client.nameservers = [nameserver]
  return client

def dns_request(domain: str, type: str = 'A', nameserver: str = "1.1.1.1") -> dict:
  """
  Perform a DNS request for the given domain and record type.

  Args:
    domain (str): The domain to query.
    type (str): The type of DNS record to query (e.g., 'A', 'MX', 'CNAME').
    nameserver (str): The DNS server to use for the query (default is "1.1.1.1").
  Returns:
    dict: A dictionary containing the DNS response.
  """
  try:
    client = _dns_client(nameserver)
    if client is None:
      return {"error": "dnspython is not installed."}

    answers = client.resolve(domain, type)
    return {"answers": [str(answer) for answer in answers]}
  except Exception as e:
    return {"error": str(e)}

def reverse_dns(ip: str, nameserver: str = "1.1.1.1") -> dict:
  """
  Perform a reverse DNS lookup for the given IP address.

  Args:
    ip (str): The IP address to query.
    nameserver (str): The DNS server to use for the query (default is "1.1.1.1").
  Returns:
    dict: A dictionary containing the reverse DNS response.
  """  
  try:
    client = _dns_client(nameserver)
    if client is None:
      return {"error": "dnspython is not installed."}

    answers = client.resolve_address(ip)
    return {"answers": [str(answer) for answer in answers]}
  except Exception as e:
    return {"error": str(e)}

def subnet_mask_to_cidr(subnet_mask: str) -> dict:
  """
  Convert a subnet mask to CIDR notation.

  Args:
    subnet_mask (str): The subnet mask in dotted decimal notation (e.g., '255.255.255.0').
  Returns:
    dict: A dictionary containing the CIDR notation.
  """
  try:
    # Convert subnet mask to CIDR notation
    cidr = sum(bin(int(x)).count('1') for x in subnet_mask.split('.'))
    return {"subnet_mask": subnet_mask, "cidr": cidr}
  except Exception as e:
    return {"error": str(e)}

def cidr_to_subnet_mask(cidr: int) -> dict:
  """
  Convert CIDR notation to a subnet mask.

  Args:
    cidr (int): The CIDR notation (e.g., 24).
  Returns:
    dict: A dictionary containing the subnet mask in dotted decimal notation.
  """
  try:
    # Convert CIDR notation to subnet mask
    mask = (0xffffffff >> (32 - cidr)) << (32 - cidr)
    subnet_mask = f"{(mask >> 24) & 0xff}.{(mask >> 16) & 0xff}.{(mask >> 8) & 0xff}.{mask & 0xff}"
    return {"subnet_mask": subnet_mask, "cidr": cidr}
  except Exception as e:
    return {"error": str(e)}

def ip_range(cidr: str) -> dict:
  """
  Generate a list of IP addresses from a given subnet mask.

  Args:
    cidr (str): The subnet mask in CIDR notation (e.g., '255.255.255.0' or '24').
  Returns:
    dict: A dictionary containing the list of IP addresses in the subnet.
  """
  try:
    if cidr.isdigit():
      network = ipaddress.ip_network(f"0.0.0.0/{cidr}", strict=False)
    else:
      network = ipaddress.ip_network(cidr, strict=False)
    range = [str(ip) for ip in network.hosts()]
    return {"cidr": str(network), "ip_range": range, "total_hosts": len(range), "from": range[0], "to": range[-1]}
  except Exception as e:
    return {"error": str(e)}

def recommended_ip_ranges(type: str = 'private', devices: int = 254, id: int = 1) -> dict:
  """
  Get recommended IP ranges for a given type (e.g., 'private', 'public', 'iot'...).

  Args:
    type (str): The type of IP ranges to retrieve (default is 'private').
    devices (int): The number of devices to accommodate in the IP range (default is 254).
    id (int): The ID of the IP range to retrieve (default is 1).
  Returns:
    dict: A dictionary containing the recommended IP ranges.
  """
  try:
    if devices < 1:
      return {"error": "Number of devices must be at least 1.", "code": 400}
    elif devices <= 254:
      return {"cidr": f"192.168.{id}.0/24", "subnet_mask": "255.255.255.0"}
    elif devices <= 65534:
      return {"cidr": f"10.{id}.0.0/16", "subnet_mask": "255.255.0.0"}
    else:
      return {"error": "Number of devices exceeds the maximum for private IP ranges.", "code": 400}
  except Exception as e:
    return {"error": str(e), "code": 500}