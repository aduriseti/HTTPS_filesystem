from BaseHTTPServer import BaseHTTPRequestHandler
from BaseHTTPServer import HTTPServer
from sync_server import SyncServer 
from sync_client import SyncClient
import json
import logging
import cgi
import sys
import os
import shutil
import urlparse
import requests
import pprint
import socket
import time
import SocketServer


pp = pprint.PrettyPrinter()

server_type = ""


def pretty_print(data):
	print json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))


class SyncPeer():

	def __init__(self, url, port):
		self.m_url = url
		self.m_port = port
		self.m_sync_server = SyncServer
		self.m_sync_client = SyncClient(self.m_url, self.m_port)

	def start(self):
		#try 100 ports above one specified
		self.m_sync_client.start()
		for retry in range(0, 100):
			try:
				httpd = SocketServer.TCPServer(("", self.m_port), self.m_sync_server)
				print "serving at port", self.m_port
				httpd.serve_forever()
			except SocketServer.socket.error as exc:
				if exc.args[0] != 48:
					raise
				print 'port ', self.m_port, ' already in use'
				self.m_port += 1
			else:
				break


if __name__ == "__main__":
	if len(sys.argv) > 1:
		url = sys.argv[1]
	else:
		url = "10.10.1.6"
	port = 8000
	sync_client = SyncPeer(url, port)
	sync_client.start()

