import requests
import sys
import os
import pprint
import socket
import time

pp = pprint.PrettyPrinter()

server_type = ""


def pretty_print(data):
	print json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))


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


class SyncClient():
	def __init__(self, url = "10.10.1.6", port = 8000):
		self.m_url = url
		self.m_port = port
		self.m_port = self.get_syncserv_port()
		self.m_cwd = os.getcwd()
		if not self.m_port:
			self.inject_sync_server()
		self.m_file_obj_map = {}
			
	def start(self):
		if not self.m_port:
			print "Failed to find port of sync server on remote host - not starting"
			return
		try:
			while True:
				time.sleep(0.01)
				modified_objs = self.get_modified_objs()
				self.sync_objs(modified_objs)
		except KeyboardInterrupt:
			pass 

	def inject_sync_server(self):
		print "Enter a directory to sync changes to: "
		dir_name = raw_input()
		cmd = "cat ./sync_server.py | ssh aduriseti@" + str(self.m_url) + " python &;"
		os.system(cmd)

	#TODO: establish connection open protocol to establish that the server on the other end is a sync server
	def get_syncserv_port(self):
		#try 100 ports above one specified in __init__
		print "Trying: " + str(self.m_url) + ":" + str(self.m_port)
		for retry in range(0, 100):
			#print "Trying: " + str(self.m_url) + ":" + str(self.m_port)
			resp = None
			try:
				resp = requests.get("http://" + self.m_url + ":" + str(self.m_port), params = {"client_type": "sync_client"})
			except Exception, e:
				pass
				#print str(e)
			if resp:
				print resp
				if resp.status_code == 200 and "sync" in resp.text:
					server_type = resp.text
					print "Got port for peer of type: " + server_type
					return self.m_port
			#print "Sync server not serving on: " + self.m_url + ":" + str(self.m_port)
			self.m_port += 1
		return

	def get_modified_objs(self):
		modified_objs = []
		for filename in os.listdir(self.m_cwd):
			# Join the two strings in order to form the full filepath.
			filepath = self.m_cwd + "/" + filename
			if not os.path.isfile(filepath): continue
			if filepath in self.m_file_obj_map:
				file_obj = self.m_file_obj_map[filepath]
				old_size = file_obj.m_size
				file_obj.update()
				if file_obj.m_tmod > file_obj.m_tsync or file_obj.m_size != old_size:
					modified_objs.append(file_obj)
			else:
				self.m_file_obj_map[filepath] = FileObject(filepath)
				modified_objs.append(self.m_file_obj_map[filepath])
		return modified_objs

	def sync_objs(self, modified_objs):
		if not self.m_port:
			return
		for file_obj in modified_objs:
			print file_obj
			filepath = file_obj.m_filepath
			print "Syncing: " + filepath
			try:
				resp = requests.post("http://" + self.m_url + ":" + str(self.m_port), files={"upload_file": open(filepath, 'rb')})
				if resp.status_code == 200:
					file_obj.m_tsync = time.time()
			except Exception, e:
				print str(e)
				continue
			print resp


if __name__ == "__main__":
	if len(sys.argv) > 1:
		endpoint = sys.argv[1]
	else:
		endpoint = "10.10.1.6:8000"
	try:
		[url, port] = endpoint.split(":")
		port = int(port)
	except Exception, e:
		print str(e)
		url = endpoint
		port = 8000
	sync_client = SyncClient(url, port)
	sync_client.start()


