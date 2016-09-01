import requests
import sys
import os
import subprocess
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
	def __init__(self, user = "aduriseti", url = "10.10.1.6", port = 8000):
		#TODO: create argument for mount point i.e. folder in remote host file system to sync with
		self.m_user = user
		self.m_url = url
		self.m_port = port
		self.m_cwd = os.getcwd()
		self.m_server_type = ""
		self.m_server_proc = None
		self.get_syncserv_port()
		if not self.m_server_type:
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
			#TODO: send server a kill signal to clean up that process on remote host
			#TODO: use disk to persist deltas from previous connection
			#TODO: make associated sync files hidden to avoid cluttering remote host
			if self.m_server_type:
				self.send_kill_signal()
			if self.m_server_proc:
				self.m_server_proc.kill()
			sys.exit(0)

	def inject_sync_server(self):
		print "Enter a directory to sync changes to: "
		dir_name = raw_input()
		#TODO make a more sophisticated bash(or python) script in a separate file to execute with ssh
		cmd = "cat ./sync_server.py | ssh " + str(self.m_user) + "@" + str(self.m_url) + " 'cd " + str(dir_name) + "; python - " + str(self.m_port) +" > sync_serv_log 2>&1' "
		print cmd
		#os.system(cmd)
		self.m_server_proc = subprocess.Popen(cmd, shell=True)
		for retry in range(0, 10):
			time.sleep(1)
			self.get_syncserv_port()
			if self.m_server_type: return
		self.m_server_proc.kill()

	#TODO: establish connection open protocol to establish that the server on the other end is a sync server
	def get_syncserv_port(self):
		#try 100 ports above one specified in __init__
		port = self.m_port
		print "Trying: " + str(self.m_url) + ":" + str(port)
		for retry in range(0, 10):
			#print "Trying: " + str(self.m_url) + ":" + str(port)
			resp = None
			try:
				resp = requests.get("http://" + self.m_url + ":" + str(port), params = {"client_type": "sync_client"})
			except Exception, e:
				pass
				#print str(e)
			if resp:
				print resp
				if resp.status_code == 200:
					if "sync" in resp.text:
						self.m_server_type = resp.text
						print "Got port for peer of type: " + self.m_server_type
						self.m_port = port
						return
					else:
						print "Server on: " + self.m_url + ":" + str(port) + " isn't sync server"
			port += 1
		return

	def send_kill_signal(self):
		print "Attempting to kill server at: " + self.m_user + "@" + self.m_url + ":" + str(self.m_port)
		for retry in range(0, 10):
			#print "Trying: " + str(self.m_url) + ":" + str(port)
			resp = None
			try:
				resp = requests.get("http://" + self.m_url + ":" + str(self.m_port), params = {"hasta_la_vista": "baby"})
			except Exception, e:
				pass
				#print str(e)
			if resp:
				if resp.status_code == 200:
					print "Server successfuly killed"
					return
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
		if not self.m_server_type:
			return
		for file_obj in modified_objs:
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
		endpoint = "aduriseti@10.10.1.6:8000"
	try:
		[user, endpoint] = endpoint.split("@")
		[url, port] = endpoint.split(":")
		port = int(port)
	except Exception, e:
		print str(e)
		user = "aduriseti"
		url = endpoint
		port = 8000
	sync_client = SyncClient(user, url, port)
	sync_client.start()

