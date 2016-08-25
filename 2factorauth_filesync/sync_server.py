from BaseHTTPServer import BaseHTTPRequestHandler
from BaseHTTPServer import BaseHTTPServer
import SocketServer
import logging
import cgi
import sys
import os
import shutil
import urlparse


class ServerHandler(BaseHTTPRequestHandler):
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


	def do_POST(self):

		return
		print "In http post handler".upper()
		print self.headers
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
		SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)


if __name__ == "__main__":
	if len(sys.argv) > 1:
		PORT = int(sys.argv[1])
	else:
		PORT = 8000
	Handler = ServerHandler
	#try 100 ports above one specified
	for retry in range(0, 100):
		try:
			httpd = SocketServer.TCPServer(("", PORT), Handler)
			print "serving at port", PORT
			httpd.serve_forever()
		except SocketServer.socket.error as exc:
			if exc.args[0] != 48:
				raise
			print 'Port ', PORT, ' already in use'
			PORT += 1
		else:
			break