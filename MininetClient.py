#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Import:
#======================================================================================================================
import os
import socket
from socket import *
import subprocess
import sys
import time
import threading
from threading import RLock
from subprocess import check_output 
import struct
#======================================================================================================================

#======================================================================================================================
#                                                    Thread Client
#=====================================================================================================================
class ClientThread(threading.Thread):
    verrou = threading.RLock()
    __slots__  = "serverParam", "nb_pkt", "list_pktToDrop", "elements", "listOfPkt", "index_PktToDrop", "decision", "nbTimeToDrop", "nb_time", "socketTemp"
    def __init__(self, serverParam, nb_pkt, list_pktToDrop, nb_time):
        threading.Thread.__init__(self)
        self.serverParam = serverParam
        self.nb_pkt = nb_pkt
        self.list_pktToDrop = []
        self.elements = list_pktToDrop.split('/')
        self.listOfPkt = []
        self.index_PktToDrop = []
        self.decision = None
        self.nbTimeToDrop = None
        self.nb_time = int(nb_time)
        self.socketTemp = None

    def run(self):
        try: 
            # Traitement de la liste des paquets à faire tomber :
            for self.i in range(len(self.elements)):
                self.splitElement = self.elements[self.i].split(',')
                self.list_pktToDrop.append((int(self.splitElement[0]),int(self.splitElement[1])))
            # Récupération des indexs des paquets à faire tomber:
            for index in self.list_pktToDrop:
                self.index_PktToDrop.append(index[0])
            # Formation des paquets :
            for index in range(self.nb_pkt):
                if index+1 in self.index_PktToDrop:
                    self.decision = 'D' # D : Drop
                    for i in range(len(self.list_pktToDrop)):
                        self.index_pkt, self.index_Drop = self.list_pktToDrop[i]
                        if self.index_pkt == index+1:
                            self.nbTimeToDrop  = self.index_Drop
                else : 
                    self.decision = 'P'# P : Pass
                    self.nbTimeToDrop = 0
                self.msg = "Pr/%i/%i/%s/%s"%(self.nbTimeToDrop, index+1,self.decision, self.name)
                self.msg  = self.msg.zfill(1448)
                self.listOfPkt.append(self.msg)
            #Generation de message x fois:
            while self.nb_time > 0:
                self.nb_time-=1
                try :
                    #Creation d'une socket temporaire
                    self.socketTemp = socket(AF_INET, SOCK_STREAM)
                    self.socketTemp.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
                    self.socketTemp.settimeout(None)
                    self.socketTemp.bind(('', 0))
                    #Connexion au serveur
                    self.socketTemp.connect(self.serverParam)
                    # Phase d'envoie :
                    if self.nb_time == 0:
                        self.msg = str(1448*self.nb_pkt) + '/' + self.name + '/L/' # Last
                    else:
                        self.msg = str(1448*self.nb_pkt) + '/' + self.name + '/C/' # Current
                    self.msg = self.msg.ljust(18,'0')
                    self.socketTemp.sendall(self.msg.encode())
                    self.msg = ''.join(self.listOfPkt)
                    self.socketTemp.sendall(self.msg.encode())
                    # Fermeture de la socket temporaire :
                    self.socketTemp.shutdown(SHUT_WR)
                    self.socketTemp.close()
                    with self.verrou :
                        # Ecriture pour prévenir de la fin de la transmission côté client :
                        open(".term.txt", 'a').write('%s\n'%self.name)
                        open(".term.txt", 'a').close()
                except Exception as e:
                    print("Erreur thread %s." %self.name, e)
        except error as message :
            print("ERROR : %s" %message)

#======================================================================================================================
#                                                   Classe Client
#======================================================================================================================
class Client :
    __slots__  = "file_tcpdump", "interface", "process_tcpdump", "threadClient", "nb_client", "name_thread", "clientIPaddr", "serverParam", "nb_pkt", "list_pktToDrop", "nb_time"
    def __init__(self, clientName, clientIPaddr, serverParam, nb_pkt, nb_client, list_pktToDrop, nb_time):
        # Code du constructeur :
        # Nom du fichier .pcap pour tcpdump :
        self.file_tcpdump = clientName +"_trace.pcap"
        # Interface de capture :
        self.interface  = clientName + "-eth0"
        # Processus tcpdump :
        self.process_tcpdump = None
        # Liste de thread client :
        self.threadClient = []
        # Nombre de client à générer :
        self.nb_client = nb_client
        # Nom de thread client
        self.name_thread = None
        # Adresse du client :
        self.clientIPaddr = clientIPaddr
        # Les paramètres du serveur (adresse, port) :
        self.serverParam  = serverParam
        # Nombre de paquets à envoyer
        self.nb_pkt = int(nb_pkt)
        # Liste des paquets à faire tomber :
        self.list_pktToDrop = list_pktToDrop
        # Nombre d'éxecution :
        self.nb_time = nb_time
    #________________________________________________METHODES:_________________________________________________________
    # Méthode pour lancement des threads client, et de tcpdump :
    def client_app(self):
        self.process_tcpdump = self.begin_tcpdump(self.file_tcpdump, self.interface)
        print("\n** CLIENT : Creation et lancement de %i thread(s) **"%(self.nb_client))
        for index in range(self.nb_client):
            self.threadClient.append(index+1)
            self.threadClient[index] = ClientThread(self.serverParam, self.nb_pkt, self.list_pktToDrop, self.nb_time)
            self.threadClient[index].start()
        for index in range(self.nb_client):
             self.threadClient[index].join()
        print(" \n*** CLIENT : FIN exécution. ***\n")
        f  = open(".final_term.txt", 'w')
        f.write("FIN\n")
        f.close()
        self.end_tcpdump(self.process_tcpdump)

    #tcpdump: start
    def begin_tcpdump(self, trace_file, interface ):
        print("\n** CLIENT : Demarrage de TCPDUMP. **")
        process = subprocess.Popen(['tcpdump', '-i', interface,'-ttttt', '-n', '-s0', '-w', trace_file,'tcp'])
        return process

    #tcpdump: stop
    def end_tcpdump(self, process ):
        #SIGTERM
        print(" \n** CLIENT : Fin de TCPDUMP. **")
        process.terminate() #process.kill()
        (stdout_data, stderr_data) = process.communicate()
        if stdout_data: print(stdout_data)
        if stderr_data: print(stderr_data)

