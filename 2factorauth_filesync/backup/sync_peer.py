from BaseHTTPServer import BaseHTTPRequestHandler
from BaseHTTPServer import HTTPServer
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

pp = pprint.PrettyPrinter()

server_type = ""


def pretty_print(data):
	print json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))


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


#TODO: establish connection open protocol to establish that the server on the other end is a sync server
#TODO: inject the sync server onto the host if it can't be found
def get_syncserv_port():
	#try 100 ports above one specified
	PORT = 8000
	for retry in range(0, 10):
		print "Trying: " + str(url) + ":" + str(PORT)
		resp = None
		try:
			resp = requests.get("http://" + url + ":" + str(PORT), params = {"client_type": "sync_client"})
		except Exception, e:
			print str(e)
		if resp:
			print resp
			if resp.status_code == 200 and "sync" in resp.text:
				server_type = resp.text
				print "Got port for peer of type: " + server_type
				return PORT
		print "Sync server not serving on: " + url + ":" + str(PORT)
		PORT += 1
	return


class FileObject:
	def __init__(self, filepath, sync_created = False):
		self.m_filepath = filepath
		self.m_size = os.stat(filepath).st_size
		self.m_tmod = os.stat(filepath).st_mtime
		self.m_sync_created = sync_created
		self.m_tsync = 0

	def update(self, filepath = None):
		if not filepath:
			filepath = self.m_filepath
		self.m_size = os.stat(filepath).st_size
		self.m_tmod = os.stat(filepath).st_mtime


def get_modified_objs(dirpath, file_obj_map):
	modified_objs = []
	for filename in os.listdir(dirpath):
		# Join the two strings in order to form the full filepath.
		filepath = dirpath + "/" + filename
		if not os.path.isfile(filepath): continue
		if filepath in file_obj_map:
			file_obj = file_obj_map[filepath]
			old_size = file_obj.m_size
			file_obj.update()
			if file_obj.m_tmod > file_obj.m_tsync or file_obj.m_size != old_size:
				modified_objs.append(file_obj)
		else:
			file_obj_map[filepath] = FileObject(filepath)
			modified_objs.append(file_obj_map[filepath])
	return [modified_objs, file_obj_map]


def sync_objs(modified_objs, url, PORT):
	for file_obj in modified_objs:
		filepath = file_obj.m_filepath
		print "Syncing: " + filepath
		try:
			resp = requests.post("http://" + url + ":" + str(PORT), files={"upload_file": open(filepath, 'rb')})
			if resp.status_code == 200:
				file_obj.m_tsync = time.time()
		except Exception, e:
			print str(e)
			continue
		print resp


if len(sys.argv) > 1:
	url = sys.argv[1]
else:
	url = "10.10.1.6"

PORT = get_syncserv_port()
if not PORT:
	sys.exit()

cwd = os.getcwd()
file_obj_map = {}
try:
	while True:
		time.sleep(0.01)
		[modified_objs, file_obj_map] = get_modified_objs(cwd, file_obj_map)
		sync_objs(modified_objs, url, PORT)
except KeyboardInterrupt:
	pass
			