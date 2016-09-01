from setuptools import setup
import re
import os

version = re.search(
    '^__version__\s*=\s*"(.*)"',
    open('./HTTPS_filesystem/http_sync.py').read(),
    re.M
    ).group(1)

sync_server_path = os.getcwd() + "/HTTPS_filesystem/sync_server.py"
print sync_server_path

with open("./HTTPS_filesystem/http_sync.py", "a") as http_sync_file:
	with open("./HTTPS_filesystem/sync_server.py", "rb") as sync_client_file:
		http_sync_file.write('\nsync_server_path = "' + sync_server_path + '"')

setup(name='HTTPS_filesystem',
	version=version,
	description='A file sync utility that uses https to provide an abstraction of a local filesystem "mounted" on a remote host',
	url='https://github.com/aduriseti/FileSync_2_stage_authentication.git',
	author='Amal Duriseti',
	author_email='aduriseti@gmail.com',
	license='MIT',
	packages=['HTTPS_filesystem'],
	entry_points = {
        "console_scripts": ['http_sync = HTTPS_filesystem.http_sync:main']
        },
	install_requires=[
		'requests',
	],
	zip_safe=False
)
