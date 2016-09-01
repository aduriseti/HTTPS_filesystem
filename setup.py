from setuptools import setup
import re

version = re.search(
    '^__version__\s*=\s*"(.*)"',
    open('./HTTPS_filesystem/http_sync.py').read(),
    re.M
    ).group(1)
 
 

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
