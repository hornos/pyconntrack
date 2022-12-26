#!/usr/bin/env python

from pyconntrack import Conntrack, NFCT_O_DEFAULT, NFCT_O_XML
from socket import AF_INET
from subprocess import call
import sys

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

OUTPUT_FORMAT = {
    "list": NFCT_O_DEFAULT,
    "xml": NFCT_O_XML,
}

def checkKernelModule(module_name, symbol):
    allsyms = open('/proc/kallsyms')
    try:
        for line in allsyms:
            if symbol in line:
                print( "Module %s is loaded: symbol %r is present" % (module_name, symbol) )
                return
    finally:
        allsyms.close()
    print( "Load kernel module %s" % module_name )
    exitcode = call("modprobe %s" % (module_name), shell = True)
    if exitcode:
        raise RuntimeError("modprobe error (exit code %d)" % exitcode)

def main():
    if len(sys.argv) != 2 or sys.argv[1] not in OUTPUT_FORMAT:
        eprint( "usage: %s command" % sys.argv[0] )
        eprint( "command: list or xml" )
        sys.exit(1)
    mode = sys.argv[1]
    output = OUTPUT_FORMAT[mode]

    checkKernelModule('nf_conntrack', 'nf_ct_attach')
    checkKernelModule('nf_conntrack_netlink', 'ctnetlink_net_init')
    try:
        if mode == "xml":
            print( '<?xml version="1.0" encoding="ISO-8859-1"?>' )
            print( '<flows>' )
        nf = Conntrack()
        (table, count) = nf.dump_table(AF_INET)
        for entry in table:
            print( entry.format(output).decode() )
        if mode == "xml":
            print( '</flows>' )
    except RuntimeError as err:
        print( "ERROR: %s" % err )
    except KeyboardInterrupt:
        print( "Interrupted." )

if __name__ == "__main__":
    main()
