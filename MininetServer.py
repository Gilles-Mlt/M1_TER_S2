#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Les imports :
#======================================================================================================================
import os
from socket import *
import subprocess
import sys
import time
import threading
from threading import RLock
import math
import datetime
#======================================================================================================================

temps_debut_emission = None
temps_trfrt = 0
thread_dict = {}
verrou_write = threading.RLock()
class ServerThread(threading.Thread):

    def __init__(self, clientsocket, names_files):
        threading.Thread.__init__(self)
        self.clientsocket = clientsocket
        self.infos_thread = ''
        self.taille = None
        self.names_files  = names_files
        self.name_file = None
        self.thread_name = None
        self.taille_recu = None
        self.msg_recu = None

    def run(self):
        try:
            global thread_dict
            global temps_trfrt
            global temps_debut_emission
            # Reception du message
            self.infos_thread = self.clientsocket.recv(18)
            #Je recupere la taille des données à receptionner et le nom du thread :
            self.infos_thread = self.infos_thread.decode().split('/')
            self.taille = int(self.infos_thread[0])
            self.thread_name = self.infos_thread[1]
            for index in self.names_files:
                if self.thread_name in index:
                    self.name_file = index
            # Récupération si dernier paquet ou pas :
            self.flag_pkt = self.infos_thread[2]
            if not(self.thread_name in thread_dict):
                thread_dict[self.thread_name] = 0
            # Lecture de l'ensemble du message
            self.taille_recu = 0
            self.msg_recu = self.clientsocket.recv(1448)
            while self.msg_recu:
                self.taille_recu += len(self.msg_recu)
                thread_dict[self.thread_name] = thread_dict.get(self.thread_name) + len(self.msg_recu)
                # Si instant t soustrait au de début d'emission est plus grand que le temps mesuré et est plus petit que temps mesuré + 1 alors nous n'écrivons pas encore. (1 seconde n'est pas encore passé) :
                if ((time.perf_counter() - temps_debut_emission) > temps_trfrt and (time.perf_counter() - temps_debut_emission) < temps_trfrt+1):
                    self.write = False
                # Sinon c'est qu'une seonce est écoulé, nous écrivons :
                else:
                    with verrou_write:
                        # Ouvre le fichier et on récupère le contenue :
                        self.file_thread = open(self.name_file,'r')
                        self.lines = self.file_thread.readlines()
                        self.file_thread.close()
                        # Si le fichier n'est pas vide alors :
                        if self.lines != []:
                            # Si la dernière ligne du fichier est le même que le temps mesuré alors :
                            if self.lines[len(self.lines)-1].split()[0] == str(temps_trfrt+1):
                                # On récupère le débit :
                                self.value_dict = thread_dict.get(self.thread_name)
                                # Réinitialise le débit du thread dans le dictionnaire :
                                thread_dict[self.thread_name] = 0
                                # Fait la somme de celui du fichier et celui du dictionnaire et réécrit au même temps:
                                self.value_dict  = self.value_dict + int(self.lines[len(self.lines)-1].split()[2])
                                self.lines[len(self.lines)-1] = str(temps_trfrt+1) + " ; " + str(self.value_dict) + "\n"
                                self.file_thread = open(self.name_file, 'w')
                                self.file_thread.writelines(self.lines)
                                self.file_thread.close()
                            # Sinon on écrit avec un nouveau temps :
                            else:
                                open(self.name_file, 'a').write(str(temps_trfrt+1) + " ; " + str(thread_dict.get(self.thread_name)) + "\n")
                                open(self.name_file, 'a').close()
                                # Réinitialisation du thread :
                                thread_dict[self.thread_name] = 0
                        # Sinon le fichier est vide alors :
                        else:
                            open(self.name_file, 'a').write(str(temps_trfrt+1) + " ; " + str(thread_dict.get(self.thread_name)) + "\n")
                            open(self.name_file, 'a').close()
                            thread_dict[self.thread_name] = 0

                    # Temps en seconde:
                    temps_trfrt = round(time.perf_counter() - temps_debut_emission)
                    self.write = True

                self.msg_recu = self.clientsocket.recv(1448)


            # Si c'est le dernier paquet alors :
            if (not self.write) and self.flag_pkt == 'L':
                with verrou_write:
                    self.file_thread = open(self.name_file,'r')
                    self.lines = self.file_thread.readlines()
                    self.file_thread.close()
                    if self.lines != []:
                        if self.lines[len(self.lines)-1].split()[0] == str(temps_trfrt+1):
                            self.value_dict = thread_dict.get(self.thread_name)
                            thread_dict[self.thread_name] = 0
                            self.value_dict  = self.value_dict + int(self.lines[len(self.lines)-1].split()[2])
                            self.lines[len(self.lines)-1] = str(temps_trfrt+1) + " ; " + str(self.value_dict) + "\n"
                            self.file_thread = open(self.name_file, 'w')
                            self.file_thread.writelines(self.lines)
                            self.file_thread.close()
                        else:
                            open(self.name_file, 'a').write(str(temps_trfrt+1) + " ; " + str(thread_dict.get(self.thread_name)) + "\n")
                            open(self.name_file, 'a').close()
                            thread_dict[self.thread_name] = 0
                    else:
                        open(self.name_file, 'a').write(str(temps_trfrt+1) + " ; " + str(thread_dict.get(self.thread_name)) + "\n")
                        open(self.name_file, 'a').close()
                        thread_dict[self.thread_name] = 0
            # Si c'est un paquet courant :
            elif (not self.write) and self.flag_pkt == 'C':
                with verrou_write:
                    self.file_thread = open(self.name_file,'r')
                    self.lines = self.file_thread.readlines()
                    self.file_thread.close()
                    if self.lines != []:
                        if self.lines[len(self.lines)-1].split()[0] == str(temps_trfrt+1):
                            self.value_dict = thread_dict.get(self.thread_name)
                            thread_dict[self.thread_name] = 0
                            self.value_dict = self.value_dict + int(self.lines[len(self.lines)-1].split()[2])
                            self.lines[len(self.lines)-1] = str(temps_trfrt+1) + " ; " + str(self.value_dict) + "\n"
                            self.file_thread = open(self.name_file, 'w')
                            self.file_thread.writelines(self.lines)
                            self.file_thread.close()
                        else:
                            open(self.name_file, 'a').write(str(temps_trfrt+1) + " ; " + str(thread_dict.get(self.thread_name)) + "\n")
                            open(self.name_file, 'a').close()
                            thread_dict[self.thread_name] = 0
                    else:
                        open(self.name_file, 'a').write(str(temps_trfrt+1) + " ; " + str(thread_dict.get(self.thread_name)) + "\n")
                        open(self.name_file, 'a').close()
                        thread_dict[self.thread_name] = 0
            #Affichage si la taille ne correspond pas
            if self.taille != self.taille_recu :
                print("pb : " + str(self.taille) + " ; " + str(self.taille_recu))
            self.clientsocket.close()
        except error as message :
            print("ERROR THREAD SERVER : %s" %message)

# Classe Serveur : Génération de threads pour répondre au requêtes client.
class Serveur :

    # Je figes les attributs, de cette façon je ne peux plus crée d'attribut à la volé. Seul ces attributs peuvent et existeront : 
    __slots__  ="serverSocket", "serverName", "file_tcpdump", "interface", "process_tcpdump", "serverIPaddr", "serverPort", "names_files", "thread_list", "nb_client", "newthreadServer" 

    # Attributs qui sont propre à tous les instances : 
    #    (vide)

    # Attributs qui sont propres à l'instance : 
    def __init__(self, serverName, serverIPaddr, serverPort, nb_client):
        self.serverSocket = None
        self.serverName = serverName
        self.file_tcpdump = None
        self.interface = None
        self.process_tcpdump  = None
        self.serverIPaddr = serverIPaddr
        self.serverPort = serverPort
        self.names_files = []
        self.thread_list = []
        self.nb_client = int(nb_client)
        self.newthreadServer = None

    #________________________________________________METHODES:_________________________________________________________
    # Boucle de réception du côté serveur pour acceuillir les clients :
    def receiving_loop(self):
        global temps_debut_emission
        try:
            self.serverSocket.settimeout(20)
            self.serverSocket.listen(self.nb_client)
            (clientsocket, (ip, port)) = self.serverSocket.accept()
        except (KeyboardInterrupt, error) as message :
            print ("ERROR IN LOOP SERVER : %s" % message)
            exit(1)
        # Récupération du temps du début d'émission :
        temps_debut_emission = time.perf_counter()
        self.newthreadServer = ServerThread(clientsocket, self.names_files)
        self.newthreadServer.start()
        self.thread_list.append(self.newthreadServer)
        while (True):
            try:
                self.serverSocket.settimeout(10)
                self.serverSocket.listen(self.nb_client)
                (clientsocket, (ip, port)) = self.serverSocket.accept()
            except (KeyboardInterrupt, error) as message :
                # print ("ERROR IN LOOP SERVER : %s" % message)
                f =  open(".final_term.txt",'r+')
                line = f.readline()
                line = line.strip('\n')
                f.close()
                if line == 'FIN':
                    break
                else:
                    print ("ERROR: %s" % message)
                    continue
            # Lancement d'un nouveu thread
            self.newthreadServer = ServerThread(clientsocket, self.names_files)
            self.newthreadServer.start()
            # On l'ajoute à la liste :
            self.thread_list.append(self.newthreadServer)
        #A la fin de la transmission de tous les clients on attend la fin des threads serveurs :
        for thread in self.thread_list : 
            thread.join()
        # On ferme la socket de réception :
        self.serverSocket.close()
        for name_file in self.names_files:
            open(".infos.txt",'a').write(name_file + '\n')
            open(".infos.txt",'a').close()
        print("** SERVEUR : Fermeture !**")
        # On arrête la capture :
        self.end_tcpdump(self.process_tcpdump)

    # Application côté serveur :
    def server_app(self):
        print("\n** SERVEUR : Creation socket **")
        self.serverSocket = socket(AF_INET, SOCK_STREAM)
        print("\n** SERVEUR : Demarrage de TCPDUMP **")
        # Paramètres de la trace pour tcpdump: 
        self.file_tcpdump = self.serverName +"_trace.pcap"
        self.interface  = self.serverName + "-eth0"
        # Lancement de tcpdump :
        self.process_tcpdump = self.begin_tcpdump(self.file_tcpdump, self.interface)
        #J associe ma socket serveur à une adresse choisie et un port libre, choisie et fixe. Afin que le client puisse se connecter :
        try :
            print("** SERVEUR : Liaison de la socket a l'IP : " + self.serverIPaddr + " et au port : "+ str(self.serverPort) +" **\n")
            self.serverSocket.bind((self.serverIPaddr,self.serverPort))
        except error as message :
            print ("ERROR: %s" % message) ;  sys.exit(1)
        #Permet une reutilisation direct des parametres de ma socket
        self.serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        # Fichier d'infomation :
        open(".infos.txt", 'w').close()
        # Fichier d'écriture débit :
        # self.names_files.append(".infos.txt")
        # Noms des fichiers d'écriture :
        for i in range(1,self.nb_client+1):
            name_file_i = "Thread-%i_%s.txt"%(i, datetime.datetime.now())
            open(name_file_i, 'w').close()
            self.names_files.append(name_file_i)
        print("** SERVEUR : Les noms de fichiers seront : **")
        print(self.names_files)
        print("** SERVEUR : Lancement boucle de reception client. **")
        self.receiving_loop()

    #tcpdump: start
    def begin_tcpdump(self, trace_file, interface ):
        print("dumpstart")
        process = subprocess.Popen(['tcpdump', '-i', interface,'-ttttt', '-n', '-s0', '-w', trace_file,'tcp'])
        return process

    #tcpdump: stop
    def end_tcpdump(self, process ):
        print("** SERVEUR : Fin TCPDUMP **")
        process.terminate()
        (stdout_data, stderr_data) = process.communicate()
        if stdout_data: print (stdout_data)
        if stderr_data: print (stderr_data)