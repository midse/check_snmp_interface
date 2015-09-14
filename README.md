# check_snmp_interface

You can either define a config file (a set of credentials by GROUP_NAME) or specify all the parameters. 

## Usage

```
Usage:
    check_snmp_interface.py (-h|--help)
    check_snmp_interface.py [ -f <filename> | --file <filename> ] [ -s <redis_socket_path> | --sock <redis_socket_path> ]
                            [-m <mib_path> | --mib <mib_path> ] [ --fields=<list> ] [ -i <if_name> | --ifname <if_name> ]  HOST INTERFACE_ID GROUP_NAME
    check_snmp_interface.py [ -s <redis_socket_path> | --sock <redis_socket_path> ] [-m <mib_path> | --mib <mib_path> ]  [ --fields=<list> ]
                            [ -i <if_name> | --ifname <if_name> ] (-a <auth_prot> | --auth-prot <auth_prot>) (-A <auth_pass> | --auth-pass <auth_pass>)
                            (-x <priv_prot> | --priv-pass <priv_prot>) (-X <priv_pass> | --priv-pass <priv_pass>)
                            (-u <secname> | --username <secname>) HOST INTERFACE_ID
                            
Arguments:
    HOST           ip address of the device
    INTERFACE_ID   last number of the interface OID
    GROUP_NAME    should be defined in your config file as a new section
    
Options:
    -h --help       show this help message and exit
    -s --sock       set redis unix socket path (default: /tmp/redis.sock)
    -f --file       load configuration file (default: ./check_snmp_interface.conf)
    -m --mib        set path to IF-MIB  (default: /usr/share/mibs/ietf/IF-MIB)
    --fields=<list> set MIB fields to be polled (default: ifHCInOctets,ifHCOutOctets)
    -i --ifname     set interface name to avoid an unnecessary SNMP call (ex: Te7/2)
    -a --auth-prot  set authentication protocol (MD5|SHA)
    -A --auth-pass  set authentication protocol pass phrase
    -x --priv-prot  set privacy protocol (DES|AES)
    -X --priv-pass  set privacy protocol pass phrase
    -u --username   set security name
```

## Installation

Just download the zip file from Github.

### Requirements

Script not tested with Python 2.X. We recommend using Python 3.X.

```bash
pip install -r requirements.txt 
```

### Redis

```bash
port 0 # Will not listen on a TCP socket
unixsocket /tmp/redis.sock
```