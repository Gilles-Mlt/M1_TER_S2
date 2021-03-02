#!/usr/bin/python
"""Custom topology example

Two directly connected switches plus a host for each switch:

        h1			   srv1
           \		  /
    h2 --- sw1 --- sw2 --- srv2
    	   /		  \
    	h3 			   srv3
   	
Adding the 'topos' dict with a key/value pair to generate our newly defined
topology enables one to pass in '--topo=mytopo' from the command line.
"""

from mininet.topo import Topo
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.net  import Mininet
from mininet.node import Controller, OVSSwitch
from mininet.cli  import CLI
from mininet.log  import setLogLevel, info
from mininet.term import makeTerms, cleanUpScreens
from mininet.node import Node

import os
import subprocess
import sys
import time
import argparse
import thread
import threading

from select import poll, POLLIN
from time import time

class Topology( Topo ):
    "Topology, Gilles MAILLOT, Lundi  01 mars 2021."

    def __init__( self, n ):
        "Create custom topo."
        self.n = n

        # Initialize topology
        Topo.__init__( self )

        sw1 = self.addSwitch('sw1', dpid="0000000000000001")
        sw2 = self.addSwitch('sw2', dpid="0000000000000002")

        for h in range(self.n):
            host = self.addHost( 'h%s' % (h + 1) )
            server = self.addHost( 'srv%s' % (h + 1) )
            # 10 Mbps, 5ms delay, 2% loss, 1000 packet queue
            self.addLink( host, sw1, bw=10, delay='0ms', loss=0,
                                max_queue_size=1000, use_htb=True )
            self.addLink( server, sw2, bw=10, delay='0ms', loss=0,
                                max_queue_size=1000, use_htb=True )

        self.addLink( sw1, sw2, bw=5, delay='0ms', loss=15, max_queue_size=1000)

        # Build
        self.build()        

def simulate(numberOfHost):
    topology = Topology(numberOfHost)
    network  = Mininet(controller=Controller, topo=topology, host=CPULimitedHost, 
                                    link=TCLink, autoPinCpus=True, build=False)

    network.build()

    #Add hosts
    # h1 = network.get( 'h1' )
    # h2 = network.get( 'h2' )
    # h3 = network.getfor h in range(self.n):( 'h3' )

    #Server
    # srv1 = network.get( 'srv1' )
    # srv2 = network.get( 'srv2' )
    # srv3 = network.get( 'srv3' )

    #Add switch
    sw1  = network.get('sw1')
    sw2  = network.get('sw2')

    #appServer1.setIP('::FFFF:127.0.0.1')
    #appClient1.setIP('::FFFF:127.0.0.1')

    network.start()
    #network.startTerms()
    
    #On active TLP sur les hotes
    TLP_activation = "sysctl -w net.ipv4.tcp_early_retrans=3"
    #TLP_desactivation = "sysctl -w net.ipv4.tcp_early_retrans=0"

    for h in range(numberOfHost):
        print (network.get('h%s' % (h + 1)).cmd(" echo 'Hello world ! From host h%s'" % (h + 1) ))
        print (network.get('srv%s' % (h + 1)).cmd(" echo 'Hello world ! From sever srv%s'" % (h+1) ))
        
    for h in range(numberOfHost):
        print("TLP Activation on whole host ansd servers")
        print ( "From host h%s " % (h + 1) + network.get('h%s' % (h + 1)).cmd(TLP_activation))
        print ( "From server srv%s " % (h + 1) + network.get('srv%s' % (h + 1)).cmd(TLP_activation))

    for srv in range(numberOfHost):
        print("Launch of server application for srv%s" % (srv + 1))
        srvName = 'srv%s' % (srv + 1)
        srvIP = network.get('srv%s' % (srv + 1)).IP()
        port  = 6666
        print(srvName, srvIP, port)
        #print ( "From server srv%s " % (srv + 1) + network.get('srv%s' % (srv + 1)).cmd("python MininetServer.py %s %s %s" % (srvName,srvIP, port) ))
        network.get('srv%s' % (srv + 1)).sendCmd("python MininetServer.py %s %s %s" % (srvName,srvIP, port) )

    for h in range(numberOfHost):
        print("Launch of server application for h%s" % (h + 1))
        hostName = 'h%s' % (h + 1)
        hostIP = network.get('h%s' % (h + 1)).IP()
        srvIP = network.get('srv%s' % (h + 1)).IP()
        port  = 6666
        print(hostName, hostIP, srvIP,port)
        network.get('h%s' % (h + 1)).sendCmd("python MininetClient.py %s %s %s %s" % (hostName, hostIP, srvIP, port))
    
    hosts = network.hosts
    # Create polling object
    fds = [ host.stdout.fileno() for host in hosts ]
    # The poll() system call, supported on most Unix systems, provides better scalability for network servers that service many, 
    # many clients at the same time. poll() scales better because the system call only requires listing the file descriptors of interest,
    #  while select() builds a bitmap, turns on bits for the fds of interest, and then afterward the whole bitmap has to be linearly scanned again. 
    # select() is O(highest file descriptor), while poll() is O(number of file descriptors).
    poller = poll()
    for fd in fds:
        # Register a file descriptor with the polling object. Future calls to the poll() method
        #  will then check whether the file descriptor has any pending I/O events. fd can be either an integer, 
        # or an object with a fileno() method that returns an integer. File objects implement fileno(), 
        # so they can also be used as the argument.
        poller.register( fd, POLLIN ) # POLLIN There is data to read
    # Monitor output
    endTime = time() + 300
    while time() < endTime:
    # When poll() is called on the poll object, it blocks for specified number of milliseconds waiting 
    # for I/O events that were registered through the register() method.
        readable = poller.poll(1000)
        for fd, _bitmask in readable:
            node = Node.outToNode[ fd ] # mapping of output fds to nodes
            print '%s:' % node.name, node.monitor().strip()

    #print(network.get('h1').monitor(timeoutms = 240000))

    # listHost[0].cmd(TLP_activation)
    # listHost[0].cmd(" python MininetClient.py ")

    #h1.cmd(TLP_desactivation)
    # listHost[1].cmd(TLP_activation)
    #h2.cmd(TLP_desactivation)
    # listHost[1].cmd(TLP_activation)
    #h3.cmd(TLP_desactivation)
    #On active TLP sur les switches
    # sw1.cmd(TLP_activation)
    #sw1.cmd(TLP_desactivation)
    # sw2.cmd(TLP_activation)
    #sw2.cmd(TLP_desactivation)
    #On active TLP sur les serveurs
    # listSrv[0].cmd(TLP_activation)
    #srv1.cmd(TLP_desactivation)
    # listHost[0].cmd(TLP_activation)
    #srv2.cmd(TLP_desactivation)
    # srv3.cmd(TLP_activation)
    #srv3.cmd(TLP_desactivation)
    #Affichage pour les addresses IP clients et serveurs
    # print("Adresse IP de l'hote client 1: " + h1.IP())	
    # print("Adresse IP de l'hote serveur 1: " +srv1.IP())
    # print("############################################")
    # print("Adresse IP de l'hote client 2: " + h2.IP())	
    # print("Adresse IP de l'hote serveur 2: " +srv2.IP())
    # print("############################################")
    # print("Adresse IP de l'hote client 3: " + h3.IP())	
    # print("Adresse IP de l'hote serveur 3: " +srv3.IP())

    #network.iperf((h1, srv1), l4Type = 'TCP',fmt = None, seconds = 5, port = 5010)
    #sys.stdout.flush()
    #srv1.cmd("iperf -s -p 5010 -i 1")
    #time.sleep(1)
    #IP_str = str(srv1.IP())
    #print (IP_str)
    #h1.cmd("iperf -c " + IP_str + " -p 5010 -t 5")
    #sys.stdout.flush()
    #network.iperf((h2, srv2), l4Type = 'TCP',fmt = None, seconds = 5, port = 5020)
    #sys.sdtout.flush()
    #network.iperf((h3, srv3), l4Type = 'TCP',fmt = None, seconds = 5, port = 5030)
    #sys.sdtout.flush()
    #sendingTCP(appClient1, appServer1)
    
	#cli_network = CLI(network)
	#cli_network.do_xterm("host1")
	#network.startTerms()	
    #CLI(network)
    #network.stop()
        
# def sendingTCP(sendingHost, receivingHost):	
# 	""" Function for transferring segments from Host A to Host C """
#         segmentsSize  = 500
# 	print "### tcp transfer begins ###"
#         ipReceivingHost_str = str(sendingHost.IP())
# 	sendingHost.cmd('dd if=/dev/zero count=' + str(segmentsSize) + ' bs=1448 | nc6 -X ' + ipReceivingHost_str +' -p 4567 &')
#         #ipSendingHost_str = str(sendingHost.IP())
# 	receivingHost.cmd('nc6 -X -lp 4567 > /dev/null')
# 	#receivingHost.cmd('nc6 -X 10.0.1.1 7777 > target ')
# 	print "### Total Bytes transferred : " + str(segmentsSize) + " bytes ###"

def end_prog():
    print (" \n  /!\ Le temps de saisie est ecoule !\n")

def raw_input_withTimeout(prompt):
    t = threading.Timer(5.0, thread.interrupt_main)
    astring = None
    try:
        t.start()  # after 30 seconds, "hello, world" will be printed
        astring = raw_input(prompt)
    except KeyboardInterrupt:
        print("Temps temps de saisie depasse, pressez Entree") ; sys.exit(1)
    t.cancel()
    return astring

topos = { 'mytopo': ( lambda: Topology(3) ) }

# prompt = " Entrer votre nom : "
# raw_input_withTimeout(prompt)

simulate(3)
