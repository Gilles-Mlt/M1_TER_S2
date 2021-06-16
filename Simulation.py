#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Les imports :
#======================================================================================================================
import os
import sys
import DropTail
import MininetServer
import MininetClient
#======================================================================================================================

#======================================================================================================================
#                                                               FONCTION PRINCIPAL
#======================================================================================================================

if __name__ == "__main__":
    if (sys.argv[1] == "drop_tail" and len(sys.argv[1:]) == 2):
        list_pktToDrop = sys.argv[2]
        drop_tail = DropTail.DropTail(list_pktToDrop)
        drop_tail.nfqueue_app()
    elif (sys.argv[1] == "server" and len (sys.argv[1:]) == 5):
        serverName = sys.argv[2]
        serverIPaddr = sys.argv[3]
        serverPort = int(sys.argv[4])
        nb_client = int(sys.argv[5])
        server = MininetServer.Serveur(serverName, serverIPaddr, serverPort, nb_client)
        server.server_app()
    elif ((sys.argv[1] == "client" and len (sys.argv[1:]) == 9)):
        clientName = sys.argv[2]
        clientIPaddr = sys.argv[3]
        serverParam = (sys.argv[4], int(sys.argv[5]))
        nb_pkt = sys.argv[6]
        nb_client = int(sys.argv[7])
        list_pktToDrop = sys.argv[8]
        nb_time = sys.argv[9]
        client = MininetClient.Client(clientName, clientIPaddr, serverParam, nb_pkt, nb_client, list_pktToDrop, nb_time)
        client.client_app()
    else: print(" /!\ Erreur sur paramètres Simaltion.py!")

# # Serveur : 
# if len(sys.argv[1:]) == 3 :
#     serverName = sys.argv[1]
#     serverIPaddr = sys.argv[2]
#     serverPort = int(sys.argv[3])
# else:
#     print('ERROR: It missing parameter(s)')

# server = Serveur(serverName, serverIPaddr, serverPort)
# server.server_app()

# # Client : 
# # sys.argv[1] sera ici donne par le Node.IP() dans mininet
# # Sur mac 2 adresses connues qui sont fonctionnelles 0.0.0.0 ou 127.0.0.1 => loopback
# if len(sys.argv[1:]) == 4 :
#     clientName = sys.argv[1]
#     clientIPaddr = sys.argv[2]
#     serverParam = (sys.argv[3], int(sys.argv[4]))
# else:
#     usage('ERROR: It missing parameter(s)')

# client = Client (clientName, clientIPaddr, serverParam)
# client.client_app()

# # DropTail : 
# if __name__ == "__main__":
# 	# execute only if run as a script
# 	dropTail = DropTail()
# 	dropTail.nfqueue_app()
