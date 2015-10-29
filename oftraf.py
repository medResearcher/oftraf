# Copyright (c) 2015 Intracom S.A. Telecom Solutions. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License v1.0 which accompanies this distribution,
# and is available at http://www.eclipse.org/legal/epl-v10.html

""" OpenFlow traffic monitor """

import argparse
import bottle
import curses
import dpkt
import json
import os
import pcap
import time
import threading
from sets import Set

of10_valid_types = Set(['\x00', '\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x07', '\x08', '\x09', '\x0a', '\x0b', '\x0c', '\x0d', '\x0e', '\x0f',
                        '\x10', '\x11', '\x12', '\x13', '\x14', '\x15'])
"""set of str: the valid OpenFlow 1.0 message types
"""

of10_types = {
    '\x00': 'OFPT_HELLO',
    '\x01': 'OFPT_ERROR',
    '\x02': 'OFPT_ECHO_REQUEST',
    '\x03': 'OFPT_ECHO_REPLY',
    '\x04': 'OFPT_VENDOR',
    '\x05': 'OFPT_FEATURES_REQUEST',
    '\x06': 'OFPT_FEATURES_REPLY',
    '\x07': 'OFPT_GET_CONFIG_REQUEST',
    '\x08': 'OFPT_GET_CONFIG_REPLY',
    '\x09': 'OFPT_SET_CONFIG',
    '\x0a': 'OFPT_PACKET_IN',
    '\x0b': 'OFPT_FLOW_REMOVED',
    '\x0c': 'OFPT_PORT_STATUS',
    '\x0d': 'OFPT_PACKET_OUT',
    '\x0e': 'OFPT_FLOW_MOD',
    '\x0f': 'OFPT_PORT_MOD',
    '\x10': 'OFPT_STATS_REQUEST',
    '\x11': 'OFPT_STATS_REPLY',
    '\x12': 'OFPT_BARRIER_REQUEST',
    '\x13': 'OFPT_BARRIER_REPLY',
    '\x14': 'OFPT_QUEUE_GET_CONFIG_REQUEST',
    '\x15': 'OFPT_QUEUE_GET_CONFIG_REPLY'
}
"""dict of str:str: maps a packet type to an OpenFlow 1.0 message type
"""

of13_valid_types = Set(['\x00', '\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x07', '\x08', '\x09', '\x0a', '\x0b', '\x0c', '\x0d', '\x0e', '\x0f',
                        '\x10', '\x11', '\x12', '\x13', '\x14', '\x15', '\x16', '\x17', '\x18', '\x19', '\x1a', '\x1b', '\x1c', '\x1d'])
"""set of str: the valid OpenFlow 1.3 message types
"""

of13_types = {
    '\x00': 'OFPT_HELLO',
    '\x01': 'OFPT_ERROR',
    '\x02': 'OFPT_ECHO_REQUEST',
    '\x03': 'OFPT_ECHO_REPLY',
    '\x04': 'OFPT_EXPERIMENTER',
    '\x05': 'OFPT_FEATURES_REQUEST',
    '\x06': 'OFPT_FEATURES_REPLY',
    '\x07': 'OFPT_GET_CONFIG_REQUEST',
    '\x08': 'OFPT_GET_CONFIG_REPLY',
    '\x09': 'OFPT_SET_CONFIG',
    '\x0a': 'OFPT_PACKET_IN',
    '\x0b': 'OFPT_FLOW_REMOVED',
    '\x0c': 'OFPT_PORT_STATUS',
    '\x0d': 'OFPT_PACKET_OUT',
    '\x0e': 'OFPT_FLOW_MOD',
    '\x0f': 'OFPT_GROUP_MOD',
    '\x10': 'OFPT_PORT_MOD',
    '\x11': 'OFPT_TABLE_MOD',
    '\x12': 'OFPT_MULTIPART_REQUEST',
    '\x13': 'OFPT_MULTIPART_REPLY',
    '\x14': 'OFPT_BARRIER_REQUEST',
    '\x15': 'OFPT_BARRIER_REPLY',
    '\x16': 'OFPT_QUEUE_GET_CONFIG_REQUEST',
    '\x17': 'OFPT_QUEUE_GET_CONFIG_REPLY',
    '\x18': 'OFPT_ROLE_REQUEST',
    '\x19': 'OFPT_ROLE_REPLY',
    '\x1a': 'OFPT_GET_ASYNC_REQUEST',
    '\x1b': 'OFPT_GET_ASYNC_REPLY',
    '\x1c': 'OFPT_SET_ASYNC',
    '\x1d': 'OFPT_METER_MOD'
}
"""dict of str:str: maps a packet type to an OpenFlow 1.3 message type
"""

of10_counts = {}
"""dict of str:list: maps an OF10 message type to a list with total counts and
bytes for that type
"""

of13_counts = {}
"""dict of str:list: maps an OF13 message type to a list with total counts and
bytes for that type
"""

ofin_counts = [0L, 0L]
"""list of long: list with total counts and bytes for the incoming OF packets
"""

ofout_counts = [0L, 0L]
"""list of long: list with total counts and bytes for the outgoing OF packets
"""


def of_sniff(ifname, ofport):
    """Sniff the specified interface for OF packets at the specified OF port.

    Packets will be filtered based on whether their TCP src port or TCP dst port
    equals the OF port given.

    Args:
        ifname (str): network interface name
        ofport (int): OF port number used for packet filtering
    """

    tcp_pkts_malformed = 0L
    of10_pkts_malformed = 0L
    of13_pkts_malformed = 0L

    try:
        for _, pkt in pcap.pcap(name=ifname, immediate=True):

            eth = dpkt.ethernet.Ethernet(pkt)
            tcp = eth.data.data
            nbytes = len(eth.data)

            if type(tcp) != dpkt.tcp.TCP:
                tcp_pkts_malformed += 1
                continue

            # element 0: packet count
            # element 1: total packet bytes
            if tcp.dport == int(ofport):
                ofin_counts[0] += 1
                ofin_counts[1] += nbytes
            elif tcp.sport == int(ofport):
                ofout_counts[0] += 1
                ofout_counts[1] += nbytes
            else:
                continue

            payload = tcp.data

            # do not further analyze the packet if it does not have any
            # OpenFlow payload
            if len(payload) <= 1:
                continue

            of_version = payload[0]
            of_type = payload[1]

            # OF1.0
            if of_version == '\x01':
                if of_type not in of10_valid_types:
                    of10_pkts_malformed += 1
                    continue
                if not of10_types[of_type] in of10_counts:
                    of10_counts[of10_types[of_type]] = [1L, long(nbytes)]
                else:
                    of10_counts[of10_types[of_type]][0] += 1L
                    of10_counts[of10_types[of_type]][1] += long(nbytes)
            # OF1.3
            elif of_version == '\x04':
                if of_type not in of13_valid_types:
                    of13_pkts_malformed += 1
                    continue
                if not of13_types[of_type] in of13_counts:
                    of13_counts[of13_types[of_type]] = [1L, long(nbytes)]
                else:
                    of13_counts[of13_types[of_type]][0] += 1L
                    of13_counts[of13_types[of_type]][1] += long(nbytes)

    except KeyboardInterrupt:
        os._exit(1)

def print_stats():
    """ Print statistics in an endless loop
    """
    start = time.time()
    prev_in = [0,0]
    prev_out = [0,0]
    sleep_secs = 1

    try:
        win = curses.initscr()
        while True:
            time.sleep(sleep_secs)
            curr_in = ofin_counts
            curr_out = ofout_counts
            curr_of10 = of10_counts
            curr_of13 = of13_counts

            in_rate = [(b-a)/float(sleep_secs) for (a,b) in zip(prev_in, curr_in)]
            out_rate = [(b-a)/float(sleep_secs) for (a,b) in zip(prev_out, curr_out)]

            elapsed_secs = '%.4f' % (time.time() - start)
            out = '{0}{1:15}\n'.format('Elapsed seconds:', elapsed_secs)
            out += '{0:15}{1:15}\n'.format('OF in pps:', in_rate[0])
            out += '{0:15}{1:15}\n'.format('OF in Bps:', in_rate[1])
            out += '{0:15}{1:15}\n'.format('OF out pps:', out_rate[0])
            out += '{0:15}{1:15}\n'.format('OF out Bps:', out_rate[1])
            out += '\n'
            out += '{0:38}{1:15}{2:15}\n'.format('Packet Type', 'Count', 'Bytes')
            out += '--------------------------------------------------------------\n'
            out += '{0:38}{1:15}{2:15}\n'.format('Total OF in:',
                                                 str(curr_in[0]),
                                                 str(curr_in[1]))
            out += '{0:38}{1:15}{2:15}\n'.format('Total OF out:',
                                                 str(curr_out[0]),
                                                 str(curr_out[1]))
            for key in sorted(of13_counts):
                out += '{0:38}{1:15}{2:15}\n'.format('OF13_' + key + ':',
                                                     str(curr_of13[key][0]),
                                                     str(curr_of13[key][1]))
            for key in sorted(of10_counts):
                out += '{0:38}{1:15}{2:15}\n'.format('OF10_' + key + ':',
                                                     str(curr_of10[key][0]),
                                                     str(curr_of10[key][1]))
            prev_in = list(curr_in)
            prev_out = list(curr_out)
            win.addstr(0,0, out)
            win.refresh()
    except KeyboardInterrupt:
        os._exit(1)

@bottle.route('/get_of_counts', method='GET')
def get_of_counts():
    """ Callback function for summary statistics

    Returns:
        str: JSON object with total OF in and OF out counts
    """
    cnts = {}
    cnts["OF_in_counts"] = ofin_counts
    cnts["OF_out_counts"] = ofout_counts
    return json.dumps(cnts)

@bottle.route('/get_of10_counts', method='GET')
def get_of10_counts():
    """ Callback function for detailed OF10 statistics

    Returns:
        str: JSON object with detailed OF10 counts
    """
    return json.dumps(of10_counts)

@bottle.route('/get_of13_counts', method='GET')
def get_of13_counts():
    """ Callback function for detailed OF13 statistics

    Returns:
        str: JSON object with detailed OF13 counts
    """
    return json.dumps(of13_counts)

@bottle.route('/stop', method='GET')
def stop():
    """ Callback function for stopping oftraf
    """
    os._exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--rest-host',
                        required=True,
                        type=str,
                        dest='rest_host',
                        action='store',
                        help='IP address or hostname of the interface the REST'
                             ' server should listen to')
    parser.add_argument('--rest-port',
                        required=True,
                        type=str,
                        dest='rest_port',
                        action='store',
                        help='Port number the REST server should listen to')
    parser.add_argument('--of-port',
                        required=True,
                        type=str,
                        dest='of_port',
                        action='store',
                        help='OpenFlow port number based on which packet'
                             ' filtering will take place')
    parser.add_argument('--ifname',
                        required=True,
                        type=str,
                        dest='ifname',
                        action='store',
                        help='Network interface to sniff OF packets from')
    parser.add_argument('--server',
                        required=False,
                        dest='is_server',
                        action='store_true',
                        default=False,
                        help='Run oftraf as server only without printing stats')
    args = parser.parse_args()

    sniffer = threading.Thread(target=of_sniff, args=(args.ifname, args.of_port))
    sniffer.daemon = True
    sniffer.start()

    if not args.is_server:
        poller = threading.Thread(target=print_stats)
        poller.daemon = True
        poller.start()

    bottle.run(host=args.rest_host, port=args.rest_port, quiet=True)
