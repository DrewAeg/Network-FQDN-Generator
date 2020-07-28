# Network FQDN Generator

This application helps build valid and standardized FQDN for network devices and layer-3 interfaces.

| Input Column Header | Manditory | Description |
|-|-|-|
| "ip_address" | TRUE | can't build a dns record without an ip address |
| "device_hostname" | TRUE | can't build a dns record without a hostname |
| "interface_name" | FALSE | include this field if building fqdn for interfaces |
| "domain_name" | FALSE | only include this field if you don't want the default domain defined in settings.py |

&nbsp;

| Output Column Header | Description |
|-|-|
| "FQDN" | The FQDN produced from the hostname and domain data |
| "PTR" | The pointer record produced from the IP address |
| "IP Address" | The IPv4 address provided from the input data |
| "FLU Exists" | A true/false value which indicates if a forward lookup value already exists |
| "FLU Existing Value" | If a forward lookup value already exists, this is what it currently configured as |
| "FLU Needs Update" | If the current forward lookup doesn't match the FQDN, this will be set to true |
| "RLU Exists" | A true/false value which indicates if a reverse lookup value already exists |
| "RLU Existing Value" | If a reverse lookup value already exists, this is what it currently configured as |
| "RLU Needs Update" | If the current reverse lookup doesn't match the FQDN, this will be set to true |

&nbsp;

---------

# Sample Data from SolarWinds

Using SWQL studio, or a custom report in SoalrWinds, use the below queries to 
obtain sample data which is properly formatted for this application.  Use these 
queries as a guide for developing your own queries.

&nbsp;

## Sample SWQL Query for test device data:

```SQL
SELECT TOP 100 n.IPAddress AS [ip_address], n.Caption AS [device_hostname]
FROM Orion.Nodes AS n
WHERE n.CustomProperties.Device_Type NOT IN ('Server','Virtual Host','Uninterruptible Power Supply','Wireless','Environmental')
AND n.CustomProperties.Device_Category NOT IN ('Voice Router')
AND n.CustomProperties.Add8_Region IN ('AMER')
AND n.CustomProperties.Ext_Managed_Flag = FALSE
ORDER BY n.CustomProperties.Site_Group, n.Caption
```

<i>Sample result data from query:</i>

![Sample Picture](/images/device_list_example.png?raw=true "Sample data for devices.")

&nbsp;

## Sample SWQL Query for test interface data:

```SQL
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
AND n.CustomProperties.Device_Category NOT IN ('Voice Router')
AND n.CustomProperties.Add8_Region IN ('AMER')
AND n.CustomProperties.Ext_Managed_Flag = FALSE
AND i.Name IS NOT NULL
ORDER BY n.CustomProperties.Site_Group, n.Caption
```

<i>Sample result data from query:</i>

![Sample Picture](/images/interface_list_example.png?raw=true "Sample data for devices.")