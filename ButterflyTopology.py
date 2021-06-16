#!/usr/bin/python3
# -*- coding: utf-8 -*-

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
# import MininetClient
from mininet.topo import Topo
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.net  import Mininet
from mininet.node import OVSController, OVSSwitch, OVSKernelSwitch
from mininet.cli  import CLI
from mininet.log  import setLogLevel, info
from mininet.term import makeTerms, cleanUpScreens
from mininet.node import Node
from select import poll, POLLIN

import os
import subprocess
import sys
import time
import argparse
import thread
import threading
import signal 

class Topology( Topo ):
    "Topology, Gilles MAILLOT, Lundi  01 mars 2021."

    def __init__( self, n): # nb_clien
        "Create custom topo."
        self.n = n

        # Initialize topology
        Topo.__init__( self )

        # Boucle d'ajout routeur :
        for node in range(self.n):
            router = self.addHost('r%s' % (node + 1) )

        # Boucle d'ajout serveur :
        for node in range(self.n):
            server = self.addHost('srv%s' % (node + 1) )
            # Spécification du lien routeur-serveur : 10 Mbps, 5ms delay, 2% loss, 1000 packet queue
            self.addLink(router, server, bw=10, delay='4ms', loss=0,max_queue_size=10000, use_htb=True )
        
        # Boucle d'ajout client:
        for node in range(self.n): # self.nb_client
            host = self.addHost('h%s' % (node + 1) )
            # Spécification du lien client-routeur : 10 Mbps, 5ms delay, 2% loss, 1000 packet queue
            self.addLink(host, router, bw=10, delay='4ms', loss=0, max_queue_size=10000, use_htb=True )

        # Build
        self.build()

def simulate(numberOfHost, nb_client, nb_pkt, list_pktToDrop, nb_time, tlpRack_activation):
    nb_host = 1
    # Création d'une topologie :
    topology = Topology(numberOfHost) #nb_client
    # Création d'un réseau prenant en compte la topologie :
    network  = Mininet(controller=OVSController, topo=topology, host=CPULimitedHost, link=TCLink, autoPinCpus=True, build=False)
    print("\n ** Création du réseau : n_hosts ----- r1 ----- svr1\n")
    # Construction et démarrage réseau :
    network.build()
    network.start()
    # network.startTerms()

    # Mise en place des adresses IP pour le client
    for node in range(nb_host):#nb_client
        host = network.get('h%s'%(node+1))
        host.setIP(ip = '10.0.%s.%s' %(node+1, node+1), prefixLen = 24, intf = 'h%s-eth0'%(node+1))
    # Récupération serveur et routeur
    srv1 = network.get('srv1')
    r1 = network.get('r1')

    # Mise en place des adresses IP routeur côté client :
    for node in range(nb_host): # nb_client
        r1.setIP(ip = '10.0.%s.%s'%(node+1,node+128), prefixLen = 24, intf = 'r1-eth%s'%(node+1))
    # Mise en place des adresses IP pour serveur et routeur :
    srv1.setIP(ip = '10.0.2.1', prefixLen = 24, intf = 'srv1-eth0')
    r1.setIP(ip = '10.0.2.2', prefixLen = 24, intf = 'r1-eth0')

    # Setting Default Gateway for client :
    for node in range(nb_host): # nb_client
        host = network.get('h%s'%(node+1))
        host.setDefaultRoute('dev h%s-eth0 via 10.0.%s.%s'%(node+1,node+1,(node+128)))
    # Mise en place route par défaut côté serveur:
    srv1.setDefaultRoute('dev srv1-eth0 via 10.0.2.2')
    # Mise en place route par défaut côté client:
    for node in range(1): # nb_client
        r1.setHostRoute(ip="10.0.%s.%s/24"%(node+1,node+1), intf="r1-eth0")

    rp_disable(network.get('h1'))

    # Affichage :
    for node in range(nb_host): # nb_client
        print("Adresse IP h%s interface h%s-eth0: " %(node+1,node+1) + network.get('h%s'%(node+1)).IP() + "/24")
    print("Adresse IP srv1 srv1-eth0: " + srv1.IP() + "/24")
    print("Adresse IP r1 r1-eth1: " + str(r1.connectionsTo(network.get('h1'))))
    print("Adresse IP r1 r1-eth0: " + str(r1.connectionsTo(srv1)) + "\n")
    print("Activation du forwarding pour r1 : " + r1.cmd('sysctl net.ipv4.ip_forward=1') + "\n")
    print("#################################################################")

    # Activation de RACK-TLP :
    if (tlpRack_activation == "y"):
        TLP_activation = "sysctl -w net.ipv4.tcp_early_retrans=3"
        RACK_activation = "sysctl -w net.ipv4.tcp_recovery=1"
    elif(tlpRack_activation == "n"):
        TLP_activation = "sysctl -w net.ipv4.tcp_early_retrans=0"
        RACK_activation = "sysctl -w net.ipv4.tcp_recovery=0"

    # SACK et DSACK sont toujours à activer:
    SACK_activation  = "sysctl -w net.ipv4.tcp_sack=1"
    DSACK_activation = "sysctl -w net.ipv4.tcp_dsack=1"

    # Test du bon fonctionnement des consoles au lancement :
    print("Test des consoles : ")
    for node in range(nb_host): # nb_clien
        print(network.get('h%s'%(node+1)).cmd(" echo 'Hello world ! From host h%s'" %(node+1)))
    print(srv1.cmd(" echo 'Hello world ! From sever srv1'"))
    print(r1.cmd(" echo 'Hello world ! From router r1'"))
    print("##################################################################")

    # Activation de RACK-TLP sur tout les hôtes :
    print("TLP-RACK Activation on whole host ansd servers : \n")
    for node in range(nb_host): # nb_client
        print ( "From host h%s " % (node+1) + network.get('h%s' % (node+1)).cmd(TLP_activation + " ; " + RACK_activation + " ; " + SACK_activation + " ; " + DSACK_activation))
    print ( "From host srv1 " + srv1.cmd(TLP_activation + " ; " + RACK_activation + " ; " + SACK_activation + " ; " + DSACK_activation))
    print ( "From host r1 " + r1.cmd(TLP_activation + " ; " + RACK_activation + " ; " + SACK_activation + " ; " + DSACK_activation))
    print("##################################################################")

    # Récupération de l'interface du client connecté à r1
    intfCnctdToh1= r1.connectionsTo(network.get('h1'))
    # Récupération de l'interface du serveur connecté à r1
    intfCnctdTosrv1 = r1.connectionsTo(network.get('srv1'))
    # Affichage:
    print('Interface de r1 connecté au client [%s]' % ', '.join(map(str, r1.connectionsTo(network.get('h1')))))
    # print('Interface de r1 connecté aux clients [%s]' % ', '.join(map(str, r1.connectionsTo(network.get('h2')))))
    print('Interface de r1 connecté à srv1 [%s] \n' % ', '.join(map(str, r1.connectionsTo(network.get('srv1')))))

    # Récupération des interface pour iptable :
    intfInr1, intfOuth1 = intfCnctdToh1[0]
    intfOutr1, intfIntsrv1 = intfCnctdTosrv1[0]
    print("Application règle iptables à r1 :") 
    # intfInr1 et intfOutr1 : Sens client -> serveur (le client envoie).
    print(r1.cmd("iptables -A FORWARD -i " + str(intfInr1)+ " -o " + str(intfOutr1)+ " -p tcp -j NFQUEUE --queue-num 0"))

    # Lancement de tcpdump sur le routeur
    print(r1.cmd("tcpdump -i r1-eth0 -ttttt -n -s0 -w r1_trace.pcap tcp &"))
    # Lancement de DropTail.py  sur le routeur
    print(r1.cmd("python3 Simulation.py drop_tail %s &" %list_pktToDrop))
    # pid_cmd_r1 = r1.cmd("python3 Simulation.py drop_tail %s &" %list_pktToDrop)

    # Lancement du serveur :
    print("Launch of server application for srv1")
    srvName = 'srv1'
    srvIP = network.get('srv1').IP()
    print("AdIP serveur : " +srvIP)
    port  = 6666
    print(srvName, srvIP, port)
    pid_cmd_srv1 = srv1.cmd("python3 Simulation.py server %s %s %s %s &" % (srvName,srvIP, port, nb_client))
    # Lancement du client :
    for client in range(nb_host): # nb_client
        hostName = 'h%s' % (client+1)
        hostIP = network.get('h%s' % (client+1)).IP()
        rIP = r1.IP()
        print(hostName, hostIP, srvIP,port)
        network.get('h%s' % (client+1)).cmd("python3 Simulation.py client %s %s %s %s %s %s %s %s &" % (hostName, hostIP, srvIP, port, nb_pkt, nb_client, list_pktToDrop, nb_time))
    # Code pour l'affichage du contenue des nodes de ma topologie :
    # Récupération des hôtes :
    nodes = network.hosts 
    #Récupération, des files descriptors : 
    fds = [ node.stdout.fileno() for node in nodes ]
    # Création d'un objet interrogateur : 
    poller = poll()
    # Boucle for afin d'inscrire chaque fd à un objet poll() (interrogateur).
    # Ce dernier veillera aux évènement entrant ou sortant.
    for fd in fds :
        poller.register(fd,POLLIN) # Inscription des fd à l'objet interrogateur
                                    # POLLIN : Il y a des données à lire
    # time_empty = 0
    while True:
        try:
            readable = poller.poll(30000)
            if len(readable) == 0:
                f =  open(".final_term.txt",'r+')
                line = f.readline()
                line = line.strip('\n')
                f.close()
                if line == 'FIN':
                    f =  open(".final_term.txt",'r+')
                    f.seek(0)
                    f.truncate()
                    f.close()
                    try:
                        os.remove(".term.txt")
                        os.remove(".final_term.txt")
                    except OSError as message:
                        print("ERROR : %s"%message)
                    break
            else:
                for fd, _bitmask in readable:
                    # Récupération du noeud concerné
                    node = Node.outToNode [fd]
                    # Affichage du contenue lié au noeud
                    print("%s, %s" %(node.name, node.monitor().strip()))
        except (KeyboardInterrupt, Exception) as message :
                print("ERROR : %s"%message )
                break

    print(r1.cmd("pkill -9 -f tcpdump"))
    print(r1.cmd("pkill -9 -f DropTail.py"))
    network.get('h1').terminate()
    srv1.terminate()
    r1.terminate()
    # srv1.sendInt()
    print("*** FIN DE LA SIMULATION ***")

def rp_disable(host):
    ifaces = host.cmd('ls /proc/sys/net/ipv4/conf')
    ifacelist = ifaces.split()    # default is to split on whitespace
    for iface in ifacelist:
       if iface != 'lo': host.cmd('sysctl net.ipv4.conf.' + iface + '.rp_filter=0')

def end_prog():
    print (" \n  /!\ Le temps de saisie est ecoule !\n")

#======================================================================================================================
#                                                               FONCTION PRINCIPAL
#======================================================================================================================

class AlarmException(Exception):
    pass

def alarmHandler(signum, frame):
    raise AlarmException

def raw_input_withTimeout(prompt):
    signal.signal(signal.SIGALRM, alarmHandler)
    signal.alarm(60)
    try:
        astring = raw_input(prompt)
        signal.alarm(0)
        return astring
    except AlarmException:
        print("\n Utilisation du programme : ")

if __name__ == "__main__":
    if (len(sys.argv) > 1):
        for index in range(1,len(sys.argv),2):
            if(sys.argv[index] == "-c"):
                nb_client = sys.argv[index+1]
            elif(sys.argv[index] == "-pkt"):
                nb_pkt = sys.argv[index+1]
            elif(sys.argv[index] == "-ld"):
                list_pktToDrop = sys.argv[index+1]
            elif(sys.argv[index] == "-t"):
                nb_time = sys.argv[index+1]
            elif(sys.argv[index] == "-rt"):
                tlpRack_activation = sys.argv[index+1]
            else :
                print("\nOptions possibles en paramètres sont :")
                print(" <-c nombre_de_client> <-pkt nombre_de_paquets> <-ld liste_paquet_drop> <-t nombre_exécution> <-rt y_ou_n >")
                print(" Format liste de chute : index_paquet,nombre_de_chute/index2,nb_chute2...")
            
    elif (len(sys.argv) == 1):
        print("\n...Lancement du programme de test...")
        time.sleep(1)
        prompt = "Entrer le nombre de clients : "
        nb_client = raw_input_withTimeout(prompt)

        print("\nSachant qu'un paquet à une taille de 1448 octet.")
        prompt = "Entrer le nombre de paquet que générera un client : "
        nb_pkt = raw_input_withTimeout(prompt)

        prompt = "\nCombien de fois voulez-vous exécuter les clients ? "
        nb_time = raw_input_withTimeout(prompt)

        print("\nLes paquets vont donc de 1 à %s" %nb_pkt)
        prompt = "Listez les paquets à faire tomber :\nSyntaxe : 1,2/2,4 le paquet 1 tombera 2 fois et le 2, 4 fois.\nSi aucun paquet n'est à faire tomber entrer 0,0 : "
        list_pktToDrop = raw_input_withTimeout(prompt)

        prompt = "Souhaitez-vous activer TLP-RACK (y/n): "
        tlpRack_activation = raw_input_withTimeout(prompt)

    if not(isinstance( int (nb_client), int) and int(nb_client) >= 0):
        print("\n /!\ Err : type int >= 0 for %s" %nb_client) 
        exit(1)
    if not(isinstance(int(nb_pkt), int) and int(nb_pkt) >= 0):
        print("\n /!\nb_pkt Err : type int >= 0 for %s" %nb_pkt) 
        exit(1)
    if not(isinstance( int (nb_time), int) and int(nb_time) >= 0):
        print("\n /!\ Err : type int >= 0 for %s" %nb_time) 
        exit(1)

    element = list_pktToDrop.split('/')
    for index in element:
        for i in index.split(','):
            if not((isinstance(int(i), int) and int(i) >= 0)):
                print("\n /!\ Err : type int >= 0 for %s"%i) 
                exit(1)

    if not(tlpRack_activation == "y" or tlpRack_activation == "n"):
        print("\n /!\ Err : entrée invalide ! for %s"%tlpRack_activation)
        print("Entrée possible : y ou n") 
        exit(1)
    
    if tlpRack_activation == "y": display_tlpRack_activation = "activation de TLP requise"
    elif tlpRack_activation == "n": display_tlpRack_activation = "activation de TLP non requise"

    print("\nRécapitulatif des paramètres : %s client(s), %s paquets à faire tomber et les paquet à faire tomber [ %s ], nombre d'éxécution : %s , %s."%(nb_client, nb_pkt, list_pktToDrop, nb_time, display_tlpRack_activation))

    print("\n**************************************")
    print("*Lancement de la topologie et du test*")
    print("**************************************\n")

    topos = { 'mytopo': ( lambda: Topology(1) ) }
    simulate(1, int(nb_client), int(nb_pkt), list_pktToDrop, nb_time, tlpRack_activation)

    # Traçage :
    os.system('python3 Graph.py %s'%nb_client)