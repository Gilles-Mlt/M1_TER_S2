#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Création 06/05/2021, Gilles MAILLOT, 35004091.

""" Drop Tail """
# Les imports :
#======================================================================================================================
import sys
import socket

from socket import AF_INET
from netfilterqueue import NetfilterQueue
#======================================================================================================================

dict_drop = {}

# Creation de la classe DropTail : 
class DropTail:

	# Description du corps de la classe DropTail: Chute des paquets marqués.

	# Je figes les attributs, de cette façon je ne peux plus crée d'attribut à la volé. Seul ces attributs peuvent et existeront : 
	__slots__  = "nfqueue", "socket"

	# Attributs qui sont propre à tous les instance : (vide)

	# Attributs qui sont propres à l'instance : 
	def __init__(self, list_pktToDrop):
		self.nfqueue = None
		self.socket = None
	#==================================================================================================================
	#                                                          METHODES
	#==================================================================================================================
	@staticmethod
	def print_and_accept(pkt):
		global dict_drop
		# Vérification de terminaison pour les threads :
		f =  open(".term.txt",'r+')
		line = f.readline()
		f.seek(0)
		f.truncate()
		f.close()
		line = line.strip('\n')
		list_key = []
		# Si un thread a terminé :
		if line != '':
			for cle in dict_drop:
				if line in cle and dict_drop[cle] == 0: 
					list_key.append(cle)
			for cle in list_key:
				# Supression du thread de le dictionnaire :
				del dict_drop[cle]	
		# Gestion paquets :
		if(pkt.get_payload_len() == 1500):
			payload = pkt.get_payload()[53:pkt.get_payload_len()]
			payload = payload.decode()
			payload = payload.split('Pr')
			payload = payload[1]
			payload = payload.split('/')
			# Si la décision est : D
			if(payload[3] == 'D'):
				client_name = payload[4]
				decision = payload[3]
				index_pkt = payload[2]
				nbTimeToDrop = int(payload[1])
				# Clé unique :
				cle = client_name+index_pkt+decision
				# Si la clé est connue :
				if cle in dict_drop:
					# Si le nombre de chutes est atteint :
					if dict_drop.get(cle) == 0:
						pkt.accept()
					else: 
						dict_drop[cle] = dict_drop.get(cle)-1
						pkt.drop()
				else :
					# Ajout de la clé et de la valeur :
					dict_drop[cle] = nbTimeToDrop
					if cle in dict_drop:
						if dict_drop.get(cle) == 0:
							pkt.accept()
						else:
							# On effectue la première chute :
							dict_drop[cle] = dict_drop.get(cle)-1
							pkt.drop()
			elif (payload[3] == 'P') : pkt.accept()
		else: pkt.accept()

	def nfqueue_app(self):
		open(".term.txt",'w').close()
		self.nfqueue = NetfilterQueue()
		self.nfqueue.bind(0, self.print_and_accept)
		self.socket = socket.fromfd(self.nfqueue.get_fd(), socket.AF_UNIX, socket.SOCK_STREAM)
		try:
			self.nfqueue.run_socket(self.socket)
		except KeyboardInterrupt:
			print('')

		socket.close()
		self.nfqueue.unbind()