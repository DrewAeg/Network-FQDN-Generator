# Default domain for all entries that don't contain a pre-defined domain.
# default:  DEFAULT_DOMAIN = 'example.com'
DEFAULT_DOMAIN = 'gatesint.com'


# A map of full interface names converted to short two-letter names.
# This list may need to be modified as new interfaces names are discovered.
INTERFACE_MAP = {
    'cellular': 'ce',
    'fortygigabitethernet': 'fo',
    'fortygige': 'fo',
    'tengigabitethernet': 'te',
    'gigabitethernet': 'gi',
    'fastethernet': 'fa',
    'ethernet': 'et',
    'ge': 'gi',
    'loopback': 'lo',
    'loop': 'lo',
    'multilink': 'mu',
    'port-channel': 'po',
    'portchannel': 'po',
    'ether-channel': 'po',
    'etherchannel': 'po',
    'serial': 'se',
    'tunnel': 'tu',
    'vlan': 'vl',
    'bvi': 'bv',
}


# Enable or disable multithreading.  Useful to disable while troubleshooting class Address_FQDN().
# default:  MULTITHREAD = True
MULTITHREAD = True


# If a PTR record already exists for an interface on the device, it will not replace the interface PTR
# with a node PTR, if this setting is set to True.
# default:  PREFER_INTERFACE_FQDN_PTR = True
PREFER_INTERFACE_FQDN_PTR = True


# Save output to a CSV file when hostname generation is completed.
# default:  SAVE_TO_CSV = True
SAVE_TO_CSV = True