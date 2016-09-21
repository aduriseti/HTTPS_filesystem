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
		self.m_abs_path = filepath
		self.m_size = os.stat(filepath).st_size
		self.m_tmod = os.stat(filepath).st_mtime
		self.m_sync_created = sync_created
		self.m_tsync = 0

	def update(self, filepath = None):
		if not filepath:
			filepath = self.m_abs_path
		self.m_size = os.stat(filepath).st_size
		self.m_tmod = os.stat(filepath).st_mtime


class SyncClient():
	def __init__(self, user = "aduriseti", url = "10.10.1.6", port = 8000):
		#TODO: create recursive argument for recursive sync
		#TODO: create argument for mount point i.e. folder in remote host file system to sync with
		#	-this feature should support multiple servers running on the remote host so that multiple mount points
		#	 can be maintained independently
		self.m_sync_server_path = ""
		self.m_user = user
		self.m_url = url
		self.m_port = port
		self.m_cwd = os.getcwd()
		self.m_server_type = ""
		self.m_server_proc = None
		self.get_syncserv_port()
		self.m_file_obj_map = {}
			
	def start(self):
		if not self.m_server_type:
			self.inject_sync_server()
		if not self.m_port and not self.m_server_type:
			print "Failed to find port of sync server on remote host - not starting"
			return
		try:
			while True:
				time.sleep(0.01)
				modified_objs = self.get_modified_objs()
				self.sync_objs(modified_objs)
		except KeyboardInterrupt:
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
		if not self.m_sync_server_path:
			self.m_sync_server_path = "./sync_server.py"
		if not os.path.exists(self.m_sync_server_path):
			return
		#TODO: send the local ip address as argument to sync server so only connections from this machine are accepted
		cmd = "cat " + self.m_sync_server_path + " | ssh " + str(self.m_user) + "@" + str(self.m_url) + " 'cd " + str(dir_name) + "; python - " + str(self.m_port) +" > sync_serv_log 2>&1' "
		print cmd
		self.m_server_proc = subprocess.Popen(cmd, shell=True)
		for retry in range(0, 10):
			time.sleep(1)
			self.get_syncserv_port()
			if self.m_server_type: return
		self.m_server_proc.kill()

	def get_syncserv_port(self):
		#try 100 ports above one specified in __init__
		port = self.m_port
		print "Trying: " + str(self.m_url) + ":" + str(port)
		for retry in range(0, 10):
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

	#SHALLOW IMPLEMENTATION
	'''
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
	'''

	#RECURSIVE IMPL
	def get_modified_objs(self):
		modified_objs = []
		dir_nodes = [self.m_cwd]
		dir_nodes = [self.m_cwd]
		while len(dir_nodes) > 0:
			dir_node, sub_dirs, filenames = os.walk(dir_nodes.pop()).next()
			# Join the two strings in order to form the full filepath.
			dir_nodes += [dir_node + "/" + sub_dir for sub_dir in sub_dirs]
			filepaths = [dir_node + "/" + filename for filename in filenames]
			for filepath in filepaths:
				if not os.path.isfile(filepath): continue
				if filepath in self.m_file_obj_map:
					file_obj = self.m_file_obj_map[filepath]
					old_size = file_obj.m_size
					file_obj.update()
					if file_obj.m_tmod > file_obj.m_tsync or file_obj.m_size != old_size:
						modified_objs.append(file_obj)
				else:
					file_obj = FileObject(filepath)
					file_obj.m_rel_path = "." + filepath.split(self.m_cwd)[1]
					self.m_file_obj_map[filepath] = file_obj
					modified_objs.append(file_obj)
		return modified_objs

	def sync_objs(self, modified_objs):
		#TODO: support recursive sync mode
		if not self.m_server_type:
			return
		for file_obj in modified_objs:
			filepath = file_obj.m_abs_path
			print "Syncing: " + filepath
			print "Rel path: " + file_obj.m_rel_path
			try:
				resp = requests.post(
					"http://" + self.m_url + ":" + str(self.m_port), 
					files={"upload_file": open(filepath, 'rb')}, 
					params = {"rel_path": file_obj.m_rel_path, "abs_path": file_obj.m_abs_path}
				)
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

