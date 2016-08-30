from setuptools import setup

setup(name='HTTPS_filesystem',
	version='1.1',
	description='A file sync utility that uses https to provide an abstraction of a local filesystem "mounted" on a remote host',
	url='https://github.com/aduriseti/FileSync_2_stage_authentication.git',
	author='Amal Duriseti',
	author_email='aduriseti@gmail.com',
	license='MIT',
	packages=['HTTPS_filesystem'],
	install_requires=[
		'requests',
	],
	zip_safe=False)
