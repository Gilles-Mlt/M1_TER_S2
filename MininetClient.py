# -*-coding:Latin-1 -*
#!/usr/bin/python

#================================================================
#    Import
import os
from socket import *
import subprocess
import sys
import time
import threading
from threading import RLock
#================================================================

#================================================================
#   Constantes & Variables
TIMEOUT= 240 #  secondes - test duration
NAME_FILE  = "Client_File"
verrou = RLock()
# ############################################################################################################
#                                               METHODES
# ############################################################################################################

def sending_loop(timeout, serverParam):
    #longueur de la requete
    longueur  = 10

    #Temps debut bouclage
    temps_debut  = time.time()

    #Generation de message pendant timeout : 180 seconde  
    while(time.time() < temps_debut + timeout) :

        #Affichage du temps pour vérification
        print( "Temps en cours : " + str(time.time()))
        print("Temps d'arrive : " + str(temps_debut + timeout))

        try :
            #Creation d'une socket temporaire
            print("...Creation d une socket temporaire...")
            socketTemp = socket(AF_INET, SOCK_STREAM)
            socketTemp.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            socketTemp.settimeout(None)
            socketTemp.bind(('', 0))

            #Connexion au serveur
            print(" /!\ Tentative de connexion au serveur :" + str(serverParam))
            socketTemp.connect(serverParam)

            #Instant t de l'envoie 
            temps_DebEnvoie  = time.time()

            # Creation du message
            print("...Creation d'un message...")
            msg = '/'+str(temps_DebEnvoie)+'/'+str(longueur)+'/'+("01"*1400*longueur)
            taille = len(msg)
            msg = str(taille) + msg
            
            #Envoie du message
            print ("/!\Envoie du message !")
            socketTemp.sendall(msg.encode())

            #Empeche l'envoie d'autre paquet
            socketTemp.shutdown(SHUT_WR)

            #Reception ACK serveur
            #print("/!\ Reception ACK serveur !")
            #msg_recu = socketTemp.recv(10)
            #print("ACK : " + msg_recu)

            #Fermeture socket temporaire
            print("/!\ Fermeture socket temporaire...")
            socketTemp.close()
            time.sleep(0.2)
        except Exception as e:
            print("Erreur ", e)
    print("FIN BOUCLE WHILE !!!")

def client_app(clientName ,clientIPaddr, serverParam):
    #Mon client genere des traffics comme dans la réalité.

    #Creation de ma socket client
    print("\n****** Creation socket CLIENT ******")
    clientSocket = socket(AF_INET, SOCK_STREAM)
    
    print("\n****** Demarrage de TCPDUMP ******")
    file_tcpdump = clientName +"_trace.pcap"
    interface  = clientName + "-eth0"
    process_tcpdump = begin_tcpdump(file_tcpdump, interface)

    time.sleep(2)

    #J associe a ma socket client une adresse choisie par Mininet ici et un port libre, choisie ici au hasard
    try : 
        clientSocket.bind((clientIPaddr,0))
        print(" =>=> Liaison de la socket a l'adr. IP et au port :  "+ str(clientSocket.getsockname()) +" <=<= \n")
    except error as message :
          print ("ERROR: %s" % message) ;  sys.exit(1)

    #Permet une reutilisation direct des parametres de ma socket
    clientSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

    #La socket client se connecte au serveur (adresse IP fournit par Mininet)
    print("...Connexion au serveur distant : " + str(serverParam) + " ...")
    clientSocket.connect(serverParam)

    #Parametre d'initialisation
    #TIMEOUT : Duree du traffic
    #NAME_FILE: nom de fichier ou le temps et le nombre d'octet va etre transfere
    intialisation = str(TIMEOUT) + "," + str(clientName)

    #ENVOIE:
    clientSocket.sendall(intialisation.encode())

    #RECEPTION:
    ack_initialisation = clientSocket.recv(1024).decode()
    print("ACK recu : "+ ack_initialisation)

    #FERMETURE
    print("Fermeture : clientSocket")
    clientSocket.close()

    print("Lancement de la boucle d'envoie dans 1s")
    time.sleep(1)
    sending_loop(TIMEOUT, serverParam)

    time.sleep(1)
    end_tcpdump(process_tcpdump)

    print(" \n****** FIN : methode client_app ******\n")


#tcpdump: start
def begin_tcpdump( trace_file, interface ):
    print("dumpstart")
    process = subprocess.Popen(['tcpdump', '-i', interface,'-ttttt', '-n', '-s0', '-w', trace_file,'tcp'])
    return process

#tcpdump: stop
def end_tcpdump( process ):
    #SIGTERM
    print("dumpend")
    process.terminate() #process.kill()
    (stdout_data, stderr_data) = process.communicate()
    if stdout_data: print stdout_data
    if stderr_data: print stderr_data


# ############################################################################################################
#                                               FONCTION PRINCIPAL
# ############################################################################################################

# sys.argv[1] sera ici donne par le Node.IP() dans mininet
# Sur mac 2 adresses connues qui sont fonctionnelles 0.0.0.0 ou 127.0.0.1 => loopback
if len(sys.argv[1:]) == 4 :
    clientName = sys.argv[1]
    clientIPaddr = sys.argv[2]
    serverParam = (sys.argv[3], int(sys.argv[4]))
else:
    usage('ERROR: It missing parameter(s)')

client_app(clientName ,clientIPaddr, serverParam)



# class ClientThread(threading.Thread):
#     def __init__(self, tempsDebt, timeout, serverParam):
    
#         threading.Thread.__init__(self)
#         self.temps_debut = tempsDebt
#         self.timeout = timeout
#         self.serverParam = serverParam

#     def run(self):
#         print("ENTREE : run()")
#         print("/!\ Entree dans le while dans 3secds : ")
#         time.sleep(3)
#         while(time.time() < self.temps_debut + self.timeout) :
#             print( "Temps en cours : " + str(time.time()))
#             print("Temps d'arrive : " + str(self.temps_debut + self.timeout))
#             nb_socket  = 0
#             try :
#                 print("...Creation socket temporaire...")
#                 s = socket(AF_INET, SOCK_STREAM)
#                 s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
#                 s.settimeout(None)
#                 s.bind(('', 0))
#                 print("Liaison socket temporaire : " + str(s.getsockname()))
#                 nb_socket = nb_socket + 1
#                 temps_DebEnvoie = time.time()
#                 print(" /!\ Tentative de connexion au serveur :" + str(serverParam))
#                 s.connect(('0.0.0.0',6696))
#                 print(str(nb_socket) + "socket connecte au serveur")
#                 longueur = 10
#                 msg = '/'+str(temps_DebEnvoie)+'/'+str(longueur)+'/'+("a"*1400*longueur)
#                 taille = len(msg)
#                 msg = str(taille) + msg
#                 print ("...Envoie message...")
#                 s.sendall(msg.encode())
#                 s.shutdown(SHUT_WR)
#                 print("Reception ACK")
#                 msg_recu = s.recv(10)
#                 print("Fermeture socket !\n")
#                 s.close()
#                 time.sleep(0.2)
#             except Exception as e:
#                 print("Erreur ", e)

# def call_with_timeout(timeout):
#     print("ENTREE : call_with_timeout")
#     try:
#         tempsDebt = time.time()
#         clientThread = ClientThread(tempsDebt, timeout, serverParam)
#         print(" /!\ Lancement du thread client dans 3 secondes\n")
#         time.sleep(3)
#         clientThread.start()
#         time.sleep(1)
#         clientThread.join()
#     except error as message:
#         print ("ERROR: %s" % message) ;  sys.exit(1)

# def test(name_file):
#     try:
#         global TIMEOUT
#         call_with_timeout(TIMEOUT)
#     except error as message:
#         print ("ERROR: %s" % message) ;  sys.exit(1)



