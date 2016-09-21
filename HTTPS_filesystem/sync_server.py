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
import urllib
import threading
import errno


class SyncRequestHandler(BaseHTTPRequestHandler):
	serving = True
	
	def __init__(self, serving = True, *args):
		self.serving = serving
		BaseHTTPRequestHandler.__init__(self, *args)
	
	def do_GET(self):
		print "In http get handler".upper()
		print self.headers
		try:
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
		except Exception, e:
			print str(e)
			self.send_response(400)
			self.end_headers()
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
		#TODO: support recursive sync mode
		abs_path = urllib.unquote(query_components["abs_path"])
		rel_path = urllib.unquote(query_components["rel_path"])
		for key in form.keys():
			try:
				filename = form[key].filename
				filename = rel_path
				print filename
				if "/" in filename or "\\" in filename:
					if filename[0] != ".":
						print "Illegal filename - can only save in or relative to current directory"
						continue
				if os.path.exists(filename):
					print filename + " already exists, creating backup"
					if filename[0] == ".":
						backup_filename = "./backup" + filename[1:]
					else:
						backup_filename = "./backup/" + filename
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
				try:		
					os.makedirs(os.path.dirname(filename))
				except Exception, e:
					print str(e)
				with open(filename, "wb") as outfile:
					for line in form[key].file:
						outfile.write(line)
				self.send_response(200)
				self.end_headers()
				return
			except Exception, e:
				print "WRITING TO DISK FAILED"
				print str(e)
				#print form[key]
				try:
					print form[key].name
					print form[key].filename
					#print form[key].file
				except:
					pass
				self.send_response(500)
				self.end_headers()
				return
		self.send_response(400)
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
	def __init__(self, host = "", port = 8000):
		self.m_host = host
		self.m_port = port

	def start(self):
		print "Serving at " + self.m_host + ":" + str(self.m_port)
		sync_handler = SyncRequestHandler
		#try 100 ports above one specified
		for retry in range(0, 100):
			try:
				#TODO: make https server for extra security
				#TODO: only accept connections from ip that injected this server
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
	if len(sys.argv) == 3:
		host = sys.argv[1]
		port = sys.argv[2]
	if len(sys.argv) == 2:
		split_endpoint = sys.argv[1].split(":")
		try:
			[host, port] = split_endpoint
		except Exception, e:
			print str(e)
			[port] = split_endpoint
			host = ""
	else:
		host = ""
		port = "8000"
	port = int(port)
	sync_server = SyncServer(host, port)
	sync_server.start()

