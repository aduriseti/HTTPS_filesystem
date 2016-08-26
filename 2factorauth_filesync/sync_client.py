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

class SyncClient():
	def __init__(self, url = "10.10.1.6", port = 8000):
		self.m_port = port
		self.m_port = self.get_syncserv_port()
		self.m_url = url
		self.m_cwd = os.getcwd()
		if not self.port:
			print "TODO: write sync server injecection script"
			#TODO: inject the sync server onto the host if it can't be found
		self.m_file_obj_map = {}
			
	def start(self):
		try:
			while True:
				time.sleep(0.01)
				[modified_objs, self.m_file_obj_map] = get_modified_objs(self.m_CWD, self.m_file_obj_map)
				sync_objs(modified_objs, self.m_URL, self.m_port)
		except KeyboardInterrupt:
			pass 

	#TODO: establish connection open protocol to establish that the server on the other end is a sync server
	def get_syncserv_port(self):
		#try 100 ports above one specified in __init__
		for retry in range(0, 100):
			print "Trying: " + str(url) + ":" + str(port)
			resp = None
			try:
				resp = requests.get("http://" + url + ":" + str(port), params = {"client_type": "sync_client"})
			except Exception, e:
				print str(e)
			if resp:
				print resp
				if resp.status_code == 200 and "sync" in resp.text:
					server_type = resp.text
					print "Got port for peer of type: " + server_type
					return port
			print "Sync server not serving on: " + url + ":" + str(port)
			port += 1
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

	def sync_objs(modified_objs, url, port):
		for file_obj in modified_objs:
			filepath = file_obj.m_filepath
			print "Syncing: " + filepath
			try:
				resp = requests.post("http://" + url + ":" + str(port), files={"upload_file": open(filepath, 'rb')})
				if resp.status_code == 200:
					file_obj.m_tsync = time.time()
			except Exception, e:
				print str(e)
				continue
			print resp


if __name__ == "__main__":
	if len(sys.argv) > 1:
		url = sys.argv[1]
	else:
		url = "10.10.1.6"
	port = 8000
	sync_client = SyncClient(url, port)
	sync_client.start()


