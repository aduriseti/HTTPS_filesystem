from BaseHTTPServer import BaseHTTPRequestHandler
from BaseHTTPServer import HTTPServer
import json
import SocketServer
import logging
import cgi
import sys
import os
import shutil
import urlparse
import threading


class SyncRequestHandler(BaseHTTPRequestHandler):
	serving = True
	
	def __init__(self, serving = True, *args):
		print args
		self.serving = serving
		BaseHTTPRequestHandler.__init__(self, *args)
	
	def do_GET(self):
		print "In http get handler".upper()
		print self.headers
		query = urlparse.urlparse(self.path).query
		query_components = dict(qc.split("=") for qc in query.split("&"))
		if "client_type" in query_components:
			self.m_client_type = query_components["client_type"]
			self.send_response(200)
			self.end_headers()
			self.wfile.write("sync_server")
			print "got connection from client of type: " + str(self.m_client_type).upper()
		elif "hasta_la_vista" in query_components:
			print "Client sent a termination signal - exiting".upper()
			self.send_response(200)
			self.end_headers()
			self.serving = False
		return

	def do_POST(self):
		print "In http post handler".upper()
		print self.headers
		query = urlparse.urlparse(self.path).query
		query_components = {}
		if query and "=" in query:
			pass
			query_components = dict(qc.split("=") for qc in query.split("&"))
		form = cgi.FieldStorage(
			fp=self.rfile,
			headers=self.headers,
			environ={'REQUEST_METHOD':'POST',
				'CONTENT_TYPE':self.headers['Content-Type'],
			}
		)
		for key in form.keys():
			try:
				filename = form[key].filename
				print filename
				if "/" in filename or "\\" in filename:
					print "Illegal filename - can only save in current directory"
					continue
				if os.path.exists(filename):
					print filename + " already exists, creating backup"
					backup_filename = "./backup/" + form[key].filename
					if not os.path.exists("./backup/"):
						try:
							print "Making directory: " + os.path.dirname(backup_filename)
							os.makedirs(os.path.dirname(backup_filename))
						except OSError as exc: # Guard against race condition
							print exc
							if exc.errno == errno.EEXIST:
								pass
							else:
								raise
								print "Not syncing: failed to create backup at: " + backup_filename
								continue
					try:
						shutil.copy(filename, backup_filename)
						print "Backup sucessfully created"
					except:
						print "WRITING TO BACKUP FAILED"
						continue
				with open(form[key].filename, "wb") as outfile:
					for line in form[key].file:
						outfile.write(line)
			except:
				print "WRITING TO DISK FAILED"
				print form[key]
				try:
					print form[key].name
					print form[key].filename
					print form[key].file
				except:
					pass
		self.send_response(200)
		self.end_headers()


class StoppableTcpServer(SocketServer.TCPServer):
	def __init__(self, *args):
		self.serving = True
		SocketServer.TCPServer.__init__(self, *args)

	def serve_forever(self):
		while self.serving == True:
			self.handle_request()

	def finish_request(self, request, client_address):
		"""Finish one request by instantiating RequestHandlerClass."""
		req = self.RequestHandlerClass(self.serving, request, client_address, self)
		self.serving = req.serving


class SyncServer(SocketServer.TCPServer):
	def __init__(self, host = "localhost", port = 8000):
		self.m_host = host
		self.m_port = port

	def start(self):
		sync_handler = SyncRequestHandler
		#try 100 ports above one specified
		for retry in range(0, 100):
			try:
				#TODO: make https server for extra security
				httpd = StoppableTcpServer((self.m_host, self.m_port), sync_handler)
				print "serving at port", self.m_port
				httpd.serve_forever()
				httpd.server_close()
				print "prevent additional retries"
				sys.exit(0)
			except SocketServer.socket.error as exc:
				print 'port ' + str(self.m_port) + ' already in use'
				if exc.args[0] != 48 and exc.args[0] != 98:
					print "raise"
					raise
				self.m_port += 1
			else:
				break


if __name__ == "__main__":
	if len(sys.argv) > 1:
		port = int(sys.argv[1])
	else:
		port = 8000
	sync_server = SyncServer("", port)
	sync_server.start()

