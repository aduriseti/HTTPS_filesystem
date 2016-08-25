import SimpleHTTPServer
import SocketServer
import logging
import cgi
import sys
import os
import shutil

'''
if len(sys.argv) > 1:
	PORT = int(sys.argv[1])
else:
	PORT = 8000
'''

class ServerHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):	
	def do_GET(self):
		print self.headers
		SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

	def do_POST(self):
		print self.headers
		try:
			form = cgi.FieldStorage(
				fp=self.rfile,
				headers=self.headers,
				environ={'REQUEST_METHOD':'POST',
					'CONTENT_TYPE':self.headers['Content-Type'],
				}
			)
		except Exception, e:
			print str(e)
			SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)
			return
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

Handler = ServerHandler

PORT = 8000

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