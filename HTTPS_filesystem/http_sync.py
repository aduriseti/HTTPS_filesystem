from .sync_client import *
from .sync_server import *
import sys

__version__ = "0.2.0"


def main():
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