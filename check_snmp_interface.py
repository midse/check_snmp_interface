#!/usr/bin/python3.4
# -*- coding: utf8 -*-

"""
check_snmp_interface.py - Icinga plugin (SNMP v3 only)

Usage:
    check_snmp_interface.py (-h|--help)
    check_snmp_interface.py [ -f <filename> | --file <filename> ] [ -s <redis_socket_path> | --sock <redis_socket_path> ]
                            [-m <mib_path> | --mib <mib_path> ] [ --fields=<list> ] [ -i <if_name> | --ifname <if_name> ]  HOST INTERFACE_ID DEVICE_TYPE
    check_snmp_interface.py [ -s <redis_socket_path> | --sock <redis_socket_path> ] [-m <mib_path> | --mib <mib_path> ]  [ --fields=<list> ]
                            [ -i <if_name> | --ifname <if_name> ] (-a <auth_prot> | --auth-prot <auth_prot>) (-A <auth_pass> | --auth-pass <auth_pass>)
                            (-x <priv_prot> | --priv-pass <priv_prot>) (-X <priv_pass> | --priv-pass <priv_pass>)
                            (-u <secname> | --username <secname>) HOST INTERFACE_ID

Arguments:
    HOST           ip address of the device
    INTERFACE_ID   last number of the interface OID
    DEVICE_TYPE    should be defined in your config file as a new section

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
"""
from docopt import docopt

from snimpy.manager import Manager as M
from snimpy.manager import load
from snimpy.mib import SMIException

import time
import sys
import os
import redis
import configparser

def generate_icinga_output(m, redis, if_name, if_id, host, mib_fields):
    oper_status = m.ifOperStatus[if_id]

    # Create key from host + interface name (will be used to store values in Redis)
    key = '{}#{}'.format(host, if_name)

    # Checking interface status to set icinga status
    status = 0 if oper_status == 1 else 2

    # Format output for icinga
    output = '{} {} | '.format(if_name, oper_status)

    for mib_field in mib_fields:
        # Get mib_field value from snmp
        try:
            last_snmp_value = getattr(m, mib_field)[if_id]
        except AttributeError as e:
            print("Error: {}".format(e))
            exit(1)

        redis_time = 0
        bits = 0

        try:
            # Get from redis the last values (timestamp and mib_field value)
            redis_value = int(redis.hget(mib_field, key))
            redis_time = float(redis.hget(mib_field, key+'#time'))

            bits = last_snmp_value - redis_value
        except TypeError:
                # If the key in Redis doesn't exist yet we pass
                pass

        last_time = time.time()

        # Set the last snmp value + timestamp to Redis
        redis.hset(mib_field, key, last_snmp_value)
        redis.hset(mib_field, key+"#time", last_time)

        time_diff = last_time - redis_time

        # Format perfdata output for icinga
        # More details about perfdata : http://docs.icinga.org/latest/en/pluginapi.html
        output += '{}={} '.format(mib_field, round((float(bits)) / time_diff, 2))

    return output, status

def main():
    arguments = docopt(__doc__, version='0.5')

    #print(arguments)

    host = arguments['HOST']
    if_id = arguments['INTERFACE_ID']
    config_file = 'check_snmp_interface.conf'
    config = None
    device_type = ''
    if_name = ''
    path_to_if_mib = ''
    redis_socket_path = '/tmp/redis.sock'
    all_mib_fields = []
    using_config_file = True
    secname = ''
    authprotocol = ''
    authpassword = ''
    privprotocol = ''
    privpassword = ''

    if arguments["--file"]:
        config_file = arguments["<filename>"]

    if arguments["--ifname"]:
        if_name = arguments['<if_name>']

    if arguments["--sock"]:
        redis_socket_path = arguments['<redis_socket_path>']

    if arguments["--fields"]:
        all_mib_fields = arguments["--fields"].strip(',').split(',')

    if arguments["--mib"]:
        path_to_if_mib = arguments['<mib_path>']

    if not arguments['DEVICE_TYPE']:
        using_config_file = False
        secname = arguments['<secname>']
        authprotocol = arguments['<auth_prot>'].upper()
        authpassword = arguments['<auth_pass>']
        privprotocol = arguments['<priv_prot>'].upper()
        privpassword = arguments['<priv_pass>']

        if authprotocol not in ['MD5', 'SHA'] or privprotocol not in ['AES', 'DES']:
            print("Error: check your authentication/private protocol")
            exit(1)
    else:
        device_type = arguments['DEVICE_TYPE'].upper()

    if using_config_file:
        # Check if config file readable and exist
        if not os.access(config_file, os.R_OK):
            print('Error: can\'t access to "{}" configuration file!'.format(config_file))
            exit(1)

        config = configparser.SafeConfigParser()
        config.read(config_file)

        sections = [my_section[0] for my_section in config.items() if my_section[0].startswith('SNMP_')]
        section = "SNMP_"+device_type

        if section not in sections:
            print('"{}" is not a valid device type.'.format(device_type))
            print("Valide device types are : "+', '.join([my_section.split('_')[1] for my_section in sections]))
            exit(1)

    # Connect to Redis
    r = redis.StrictRedis(unix_socket_path=redis_socket_path)

    # More details about IF-MIB
    # http://monitortools.com/tech/snmp/mib/RFC/IF-MIB/

    try:
        if path_to_if_mib:
            load(path_to_if_mib, True)
        elif using_config_file:
            load(config['DEFAULT']['path_to_if_mib'], True)
        else:
            load('/usr/share/mibs/ietf/IF-MIB', True) # last resort we try to load the default path
    except SMIException as e:
        print('Error: {}'.format(e))
        exit(1)

    secname = secname if secname else config[section]['secname']
    authprotocol = authprotocol if authprotocol else config[section]["authprotocol"]
    authpassword = authpassword if authpassword else config[section]["authpassword"]
    privprotocol = privprotocol if privprotocol else config[section]["privprotocol"]
    privpassword = privpassword if privpassword else config[section]["privpassword"]

    m = M(version=3, host=host, secname=secname,
          authprotocol=authprotocol, authpassword=authpassword,
          privprotocol=privprotocol, privpassword=privpassword)


    if using_config_file:
        all_mib_fields = config[section]["mib_fields"].strip(',').split(',')
    else:
        all_mib_fields = ['ifHCInOctets', 'ifHCOutOctets'] if not all_mib_fields else all_mib_fields

    # Get from interface name and status from SNMP
    if not if_name:
        if_name = m.ifName[if_id]

    output, status = generate_icinga_output(m, r, if_name, if_id, host, all_mib_fields)

    # Print output for inciga and exit with status
    print(output)
    exit(status)

if __name__ == '__main__':
    main()
