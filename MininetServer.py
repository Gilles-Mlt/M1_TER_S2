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
verrou = RLock()
# ############################################################################################################
#                                               METHODES
# ############################################################################################################

class ServerThread(threading.Thread):
    
    def __init__(self, ip, port, clientSocketTemp, logs):

        threading.Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.clientsocket = clientSocketTemp
        self.logs = logs

    def run(self):
        #print( "ENTREE : run()")
        #Reception du message
        msg_recu = self.clientsocket.recv(100)
        #print("RECEPTION msg_recu")

        #Je recupere la taille le temps ou le paquet a ete envoye et la longueur
        a = (msg_recu.decode()).split('/')
        taille = int(a[0])
        temps = float(a[1])
        longueur = int(a[2])

        #On retire la longeur de la taille du message a la taille du message
        taille_recu = len(msg_recu.decode()) - len(a[0])

        #Lecture de l'ensemble du message
        while msg_recu:
           # print("RECEPTION par paquet de 1500 octs")
            msg_recu = self.clientsocket.recv(1500)
            taille_recu += len(msg_recu.decode())

        #Affichahe si la taille ne correspond pas
        if taille != taille_recu :
            print("pb : " + str(taille) + " ; " + str(taille_recu))

        #print("...Fermeture clientsocket...")
        self.clientsocket.close()

        #instant t soustrait au temps envoyé par le client
        temps = time.time() - temps
        #Recuperation du verrou et écriture dans le fichier
        with verrou :
            print("/!\ ECRITURE dans logs !")
            self.logs.write(str(temps)+ " ; " + str(taille) + " ; " + str(taille_recu) + "\n")

def receiving_loop(serverSocket, timeout ,name_file):
    logs = open(name_file + ".txt",'w')
    begining_time = time.time()
    while (time.time() < begining_time + timeout ):
        print("Temps en cours : " + str(time.time()))
        print("Temps d arrive : " + str(begining_time + timeout))
        print("En ecoute !")
        try:
            serverSocket.settimeout( ((begining_time + timeout) - time.time()) )
            serverSocket.listen(1)
            (clientsocket, (ip, port)) = serverSocket.accept()
        except error as message :
          print ("ERROR: %s" % message)
          break
        newthreadServer = ServerThread(ip, port, clientsocket, logs)
        print("Lancement d'un thread")
        newthreadServer.start()
        print("Fermeture d'un thread")
        newthreadServer.join()
    #A la fin du temps on ferme la socket serveur (le client est normalement fermé avant)
    print("Fin boucle while")
    serverSocket.close()

def server_app(serverIPaddr, serverPort):
    #Mon serveur va stocker les temps de transfert et le nombre d'octet transmis dans un fichier dont 
    # le nom est donnée par le client distant.

    #Creation de ma socket serveur
    print("\n****** Creation socket SERVEUR ******")
    serverSocket = socket(AF_INET, SOCK_STREAM)
    
    print("\n****** Demarrage de TCPDUMP ******")
    file_tcpdump = serverName +"_trace.pcap"
    interface  = serverName + "-eth0"
    process_tcpdump = begin_tcpdump(file_tcpdump, interface)

    time.sleep(2)

    #J associe a ma socket serveur une adresse choisie par Mininet ici et un port libre, choisie fixe 
    # afin que le client puisse se connecter
    try :
        print(" =>=> Liaison de la socket a l'adr. IP : " + serverIPaddr + " et au port : "+ str(serverPort) +" <=<= \n")
        serverSocket.bind((serverIPaddr,serverPort))
    except error as message :
          print ("ERROR: %s" % message) ;  sys.exit(1)

    #Permet une reutilisation direct des parametres de ma socket
    serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

    print("...Mise en ecoute pour 1 client...\n" )
    serverSocket.listen(1) #mise en ecoute pour un seul client pour le moment
    (clientSocket, (ip, port)) = serverSocket.accept() #Accepte
    print(" /!\ 1 client connecte  :" + str(clientSocket.getsockname()))
    
    #RECEPTION
    intialisation = clientSocket.recv(1024).decode()
    print("Initialisation : " + intialisation)

    #ENVOIE : 
    clientSocket.sendall(b'ACK_initialisaiton'.encode())
    print("FIN : Initialisation...")

    # FERMETURE
    print("Fermeture clientSocket..")
    clientSocket.close()

    #TRAITEMENT DES PARAMETRES :
    parametres  = intialisation.split(',')
    timeout = int(parametres[0]) + 10
    name_file = parametres[1]
    print("Timeout : " + str(timeout))
    print("Name_file : " + name_file)

    print("Lancement de la boucle de reception")
    receiving_loop(serverSocket, timeout ,name_file)

    time.sleep(1)
    end_tcpdump(process_tcpdump)

    print(" \n****** FIN : methode server_app ******\n")

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

if len(sys.argv[1:]) == 3 :
    serverName = sys.argv[1]
    serverIPaddr = sys.argv[2]
    serverPort = int(sys.argv[3])
else:
    print('ERROR: It missing parameter(s)')

server_app(serverIPaddr, serverPort)

# def call_with_timeout(name_file,timeout,clientSocket):
#     print("ENTREE : call_with_timeout\n")
#     logs = open(name_file,'w')
#     try:
#         print(" => Creation d'une socket : socketTemp")
#         socketTemp = socket(AF_INET, SOCK_STREAM)
#         socketTemp.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
#         socketTemp.bind(('0.0.0.0',6696))
#         print(" => Liaison de la socket a l'adr. IP et au port : "+ str(socketTemp.getsockname()))
#         time.sleep(1)
#         fin = False
#         print("/!\ Entree boucle while ")
#         while not fin:
#             try :
#                 print("..Socket mise en ecoute pour 1 client...")
#                 socketTemp.listen(1)
#                 (clientSocketTemp, (ip, port)) = socketTemp.accept()
#                 print("/!\ 1 client connecte : " + str(clientSocketTemp.getsockname()))
#                 server = ServerThread(ip, port, clientSocketTemp, logs)
#                 print("Lancement du thread serveur  : server\n")
#                 server.start()
#                 print(" RETOUR dans call_with_timeout()")
#                 msg = clientSocket.recv(100).decode()
#                 print(" msg est  : " + msg)
#                 if  msg == 'fin_test':
#                     print(" /!\ find_test detecte !")
#                     fin = True
#                 clientSocket.sendall('fin_test'.encode())
#             except OSError as e :
#                 print("Erreur : ",e)
#     except error as message:
#         print ("ERROR: %s" % message) ;  sys.exit(1)
#         logs.close()
#     finally:
#         logs.close()

# def test(name_file,timeout,clientSocket):
#     try:
#         print("=>=> ENTREE : test <=<=\n")
#         print(" /!\ Lancement de la methode : call_with_timeout\n")
#         call_with_timeout(name_file,timeout,clientSocket)
#     except error as message:
#         print ("ERROR: %s" % message) ;  sys.exit(1)
