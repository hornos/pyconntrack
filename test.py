#!/usr/bin/env python
from socket import AF_INET
import pyconntrack
from pyconntrack.constant import TCP_STATE_MSG

# https://github.com/sam-github/netfilter-lua
# Print source ip, port and sent bytes
ct = pyconntrack.Conntrack()

(items,count) =  ct.dump_table(AF_INET)
for item in items:
   print(TCP_STATE_MSG[item.tcp_state], item.orig_ipv4_src, item.orig_port_src, item.orig_port_dst, item.orig_counter_bytes, item.repl_counter_bytes)
