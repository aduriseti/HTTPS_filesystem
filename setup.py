from setuptools import setup

setup(name='2factorauth_filesync',
	version='1.0',
	description='A file sync utility that mimics the functionality of WinSCP for Unix based platforms and only requires approval once from 2 stage authentication',
	url='https://github.com/aduriseti/FileSync_2_stage_authentication.git',
	author='Amal Duriseti',
	author_email='aduriseti@gmail.com',
	license='MIT',
	packages=['2factorauth_filesync'],
	install_requires=[
		'requests',
	],
	zip_safe=False)
