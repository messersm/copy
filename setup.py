#!/usr/bin/env python
# -*- coding: utf-8 -*-

# standard imports
from distutils.core import setup

# local imports
from libcopy import VERSION

if __name__ == '__main__':
	setup(name='copy',
		version=VERSION,
		description='Advanced command line copy tool',
		long_description=open('README.txt', 'r').read(),
		license='GPLv3+',
		author='Maik Messerschmidt',
		author_email='maik.messerschmidt@gmx.net',
		url='http://sourceforge.net/projects/python-copy/',
		packages=['libcopy'],
		scripts=['copy'],
		data_files=[	('share/copy', ['LICENSE.txt', 'README.txt', 'CHANGES.txt']),
					],
     )
