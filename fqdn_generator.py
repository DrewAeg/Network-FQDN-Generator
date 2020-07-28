"""
This application helps build valid and standardized FQDN for network devices and layer-3 interfaces.

Input data must be a CSV file with the following headers:
- "ip_address"
    * manditory field
    * can't build a dns record without an ip address
- "device_hostname"
    * manditory field
    * can't build a dns record without a hostname
- "interface_name"
    * optional field
    * include this field if building fqdn for interfaces
- "domain_name"
    * optional field
    * only include this field if you don't want the default ".gatesint.com" domain


Sample SWQL Query for test device data:
    '''
    SELECT n.IPAddress AS [ip_address], n.Caption AS [device_hostname]
    FROM Orion.Nodes AS n
    WHERE n.CustomProperties.Device_Type NOT IN ('Server','Virtual Host','Uninterruptible Power Supply','Wireless','Environmental')
    AND n.CustomProperties.Add8_Region = 'AMER'
    AND n.CustomProperties.Ext_Managed_Flag = FALSE
    '''

Same SWQL Query for test interface data:
    '''
    SELECT TOP 100 n.Caption  AS [device_hostname], ip.IPAddress AS [ip_address], i.Name AS [interface_name]
    FROM Orion.NodeIPAddresses ip
    LEFT JOIN Orion.Nodes n ON n.NodeID = ip.NodeID
    LEFT JOIN Orion.NPM.Interfaces i ON i.NodeID = ip.NodeID AND i.Index = ip.InterfaceIndex
    LEFT JOIN (SELECT ip.IPAddress, COUNT(ip.IPAddress) AS [Cnt]
        FROM Orion.NodeIPAddresses ip
        GROUP BY ip.IPAddress
    ) cnt ON cnt.IPAddress = ip.IPAddress
    WHERE ip.IPAddressType = 'IPv4'
    AND (ip.IPAddress LIKE '10.%'
        OR ip.IPAddress LIKE '172.%'
        OR ip.IPAddress LIKE '192.168.%'
    )
    AND cnt.Cnt = 1
    AND n.CustomProperties.Device_Type NOT IN ('Server','Virtual Host','Uninterruptible Power Supply','Wireless','Environmental')
    AND n.CustomProperties.Add8_Region = 'AMER'
    AND n.CustomProperties.Ext_Managed_Flag = FALSE
    AND i.Name IS NOT NULL
    '''


"""


# Built-in modules
import ipaddress
import socket
import concurrent.futures
import logging
import re

# Local Modules
import tools
import settings as s






class Address_FQDN():
    """An object for tracking address-to-fqdn mappings.  Provides additional functionality like checking forward/reverse lookup existance in dns."""

    def __init__(self, ipv4_address, hostname: str, domain: str = s.DEFAULT_DOMAIN):
        # ipv4_address
        if isinstance(ipv4_address, str):
            try:
                ipv4_address = ipaddress.IPv4Address(ipv4_address)
            except:
                logging.warning(f"{hostname} - Please provide a properly formatted IP Address.")
                raise Exception("Improper argument:  ipv4_address")
        elif isinstance(ipv4_address, ipaddress.IPv4Address):
            ipv4_address = ipv4_address
        else:
            logging.warning(f"{hostname} - Please provide an IP Address as a str() or IPv4Address() object.")
            raise Exception("Improper argument:  ipv4_address")
        self.ipv4_address = ipv4_address
        self.ip_address = str(ipv4_address.compressed).strip()
        
        # hostname
        if not isinstance(hostname, str) or len(hostname) == 0:
            logging.warning(f"{hostname} - Please provide a properly formatted hostname.")
            raise Exception("Improper argument:  hostname")
        self.hostname = hostname.strip().lower()
        
        # domain
        if domain == None:
            domain = s.DEFAULT_DOMAIN
        elif not isinstance(domain, str):
            logging.warning(f"{hostname} - If providing a domain, please properly format it.")
            raise Exception("Improper argument:  domain")
        elif len(domain) == 0:
            logging.info(f"{hostname} - Zero-length domain name provided, setting it to the default: {s.DEFAULT_DOMAIN}.")
            domain = s.DEFAULT_DOMAIN
        domain = domain.strip().lower()
        self.domain = domain

        self.full_name = self.hostname + "." + self.domain

        # forward/reverse lookup data
        self.forward_lookup_existing_value = None
        self.reverse_lookup_existing_value = None
        try:
            address_info = socket.gethostbyname(self.full_name)
            if address_info == self.ip_address:
                self.forward_lookup_exists = True
                self.forward_lookup_needs_update = False
                self.forward_lookup_existing_value = address_info
            else:
                self.forward_lookup_exists = True
                self.forward_lookup_needs_update = True
                self.forward_lookup_existing_value = address_info
        except Exception as error:
            logging.info(f"{self.full_name} : {error}")
            self.forward_lookup_exists = False
            self.forward_lookup_needs_update = True
            self.forward_lookup_existing_value = None
        try:
            hostname_info = socket.gethostbyaddr(self.ip_address)[0]
            if hostname_info == self.full_name:
                self.reverse_lookup_exists = True
                self.reverse_lookup_needs_update = False
                self.reverse_lookup_existing_value = hostname_info
            elif hostname_info.find(self.hostname + "-") == 0 and s.PREFER_INTERFACE_FQDN_PTR:
                self.reverse_lookup_exists = True
                self.reverse_lookup_needs_update = False
                self.reverse_lookup_existing_value = hostname_info
            else:
                self.reverse_lookup_exists = True
                self.reverse_lookup_needs_update = True
                self.reverse_lookup_existing_value = hostname_info
        except Exception as error:
            logging.info(f"{self.full_name} : {error}")
            self.reverse_lookup_exists = False
            self.reverse_lookup_needs_update = True
            self.reverse_lookup_existing_value = None

        
        # ptr record
        self.ptr_record = ipv4_address.reverse_pointer

    def __repr__(self):
        return self.full_name


def _clean_device_hostname(hostname: str):
    '''
    Removes the domain, underscores, and multiple instances of dashes.  Makes all characters lowercase.

    Args:
        hostname: a string contiaing the hostname to be cleaned.

    Returns:
        str
    '''
    hostname = hostname.lower()
    if hostname.find(".") >= 0:
        hostname = hostname.split(".")[0]
    hostname = hostname.replace("_","-") 
    hostname = hostname.replace("--","-")
    hostname = hostname.replace("--","-") # This second one catches odd-numbered dashed (3,5,7,etc...)
    return hostname


def _clean_interface_hostname(hostname: str, interface: str):
    interface = interface.lower()
    interface = interface.replace("_","-")
    interface = interface.replace(".","-")
    interface = interface.replace(":","-")
    interface = interface.replace("/","-")
    interface = interface.replace("--","-")
    interface = interface.replace("--","-") # This second one catches odd-numbered dashed (3,5,7,etc...)

    # split the type and number data so we can easily manipulate the information
    #  # match letters up to digit, OR leters to dash to more letters up to digit (this includes "port-channel")
    interface_type = re.findall('^[a-z]+-[a-z]+|^[a-z]+', interface)[0]
    #  # match everything after and including the first digit
    try:
        interface_number = re.findall('[0-9].*', interface)[0]
    except IndexError:
        interface_number = ""

    # rename the "long name" to a "short name" as mapped in global settings INTERFACE_MAP
    if interface_type in s.INTERFACE_MAP.keys():
        interface_type = s.INTERFACE_MAP[interface_type]
    else:
        raise Exception(f"Interface type '{interface_type}' not found in 'INTERFACE_MAP' global settings.")

    # build the new standardized and shortened interface name
    if len(interface_number) == 0:
        interface = hostname + "-" + interface_type
    else:
        interface = hostname + "-" + interface_type + "-" + interface_number
    return interface


def _check_if_interface(hostname: str, existing_hostname: str):
    pass


def _build_address_fqdn_object(container: list, address_data: dict):
    """Internally used function, for mutil-threading the building of FQDN object.
    
    Multi-threaded is needed due to long wait times on DNS lookups.  See docs for the ThreadPoolExecutor() method
    in python's built-in module concurrent.futures."""
    logging.debug(f"Starting to build object data for:  {address_data['hostname']} - {address_data['ipv4_address']}" )
    container.append(Address_FQDN(**address_data))
    logging.debug(f"Finished building object data for:  {address_data['hostname']} - {address_data['ipv4_address']}" )


def main():
    # Collect the arguments, if any were provided.
    parser = tools.argument_parser()
    args = parser.parse_args()

    # Initiate logger settings
    tools.setup_logger(log_level=args.log_level, log_type=args.log_type)

    # Get the input data and convert it to a odered-list of dictionaries
    csv_file = tools.OpenFile.gui_ask_open_csv()
    csv_file = tools.OpenFile.process_csv(csv_file)
    address_table = tools.table_to_dictionary(csv_file)

    if len(address_table) == 0:
        logging.warning("No data was provided.")
        return {'status': False, 'data': None}

    # Convert the address_table to a list of Address_FQDN objects
    # first, clean up hostname data.  remove fqdn and keep only hostname
    for address in address_table:
        address['device_hostname'] = _clean_device_hostname(address['device_hostname'])
        # If an interface name was provided, we'll convert it to a hostname
        if 'interface_name' in address.keys():
            if len(address['interface_name']) > 0:
                try:
                    address['device_hostname'] = _clean_interface_hostname(address['device_hostname'], address['interface_name'])
                except Exception as error:
                    logging.warning(f"Object data build failed on:  {address['device_hostname']} - {address['ip_address']}\n{error}")

    for i, address in enumerate(address_table):
        address_data = {}
        address_data.update({
            'ipv4_address': address['ip_address'], 
            'hostname': address['device_hostname']})
        if 'domain' in address.keys():
            address_data.update({'domain': address['domain']})
        else:
            address_data.update({'domain': None})
        address_table[i] = address_data
    address_objects = []
    if s.MULTITHREAD:
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            for address in address_table:
                try:
                    executor.submit(_build_address_fqdn_object, address_objects, address)
                except Exception as error:
                    logging.warning(f"Object data build failed on:  {address['hostname']} - {address['ipv4_address']}\n{error}")
    else:
        for address in address_table:
            try:
                address_objects.append(Address_FQDN(**address))
            except Exception as error:
                logging.warning(f"Object data build failed on:  {address['hostname']} - {address['ipv4_address']}\n{error}")


    # Reformat and save data to a spreadsheet
    if s.SAVE_TO_CSV:
        output_data = [[
            "FQDN",
            "PTR",
            "IP Address",
            "FLU Exists",
            "FLU Existing Value",
            "FLU Needs Update",
            "RLU Exists",
            "RLU Existing Value",
            "RLU Needs Update"]]
        for obj in address_objects:
            output_data.append([
                obj.full_name,
                obj.ptr_record,
                obj.ip_address,
                obj.forward_lookup_exists,
                obj.forward_lookup_existing_value,
                obj.forward_lookup_needs_update,
                obj.reverse_lookup_exists,
                obj.reverse_lookup_existing_value,
                obj.reverse_lookup_needs_update
            ])
        tools.SaveFile.gui_ask_save_csv(output_data)

    return {'status': True, 'data': address_objects}



if __name__ == "__main__":
    results = main()
    print(f"Finished sucessfully:  {results['status']}")