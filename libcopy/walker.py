# Copyright (C) 2013 Maik Messerschmidt

# This file is part of copy.

# copy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# copy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with copy.  If not, see <http://www.gnu.org/licenses/>.


# standard imports
import os
import sys

from os import mkdir
from os.path import exists, getsize
from shutil import copystat

# local imports
from .copy import copyfile, copylink, Error
from .walk import (NOSTAT, IGNORE, EXCLUDE,
					REG, DIR, LINK, HARDLINK, BLOCK, CHAR, PIPE, SOCK,
					walk)

class PathWalker(object):
	"""Feeds jobs to the jobQ and counts bytes to copy."""
	
	def __init__(self, manager, *args, **kwargs):
		self.manager = manager
		self.logger = manager.logger
		self.options = manager.options
	
		self.actions = {}
		self.default_action = None
	
	def run(self):
		for result in walk(*self.options.sources,
			target=self.options.target,
			recurse=self.options.recurse,
			excludes=self.options.excludes,
			links=self.options.links):
			
			type, top, src, dst = result
			
			action = self.actions.get(type, self.default_action)
			if action:
				self.execute(action, type, top, src, dst)
	
	def execute(self, func, type, top, src, dst):
		try:
			func(type, top, src, dst)
		except Error as e:
			self.logger.error( str(e) )


class FilesizeWalker(PathWalker):
	def __init__(self, *args, **kwargs):
		super(self.__class__, self).__init__(*args, **kwargs)
		
		self.actions = { REG : self.file_action }
		self.bytes_total = 0
	
	def file_action(self, type, top, src, dst):
		self.bytes_total += getsize(src)
	
	def run(self):
		super(self.__class__, self).run()
		self.logger.set_total(self.bytes_total)


class CopyWalker(PathWalker):
	def __init__(self, *args, **kwargs):
		super(self.__class__, self).__init__(*args, **kwargs)

		self.actions = {	# errors
							NOSTAT : self.error_action,
							IGNORE : self.error_action,
							
							# directories
							DIR		: self.dir_action,
							
							# 'regular files'
							REG			: self.file_action,
							BLOCK		: self.file_action,
							CHAR		: self.file_action,
							PIPE		: self.file_action,
							SOCK		: self.file_action,
							
							# links
							HARDLINK	: self.link_action,
							LINK		: self.link_action
						}
						
		self.interactive_list = []
	
	def error_action(self, type, top, src, dst):
		if type == NOSTAT:
			self.logger.error("cannot stat '%s': No such file or directory" % src)
				
		elif type == IGNORE:
			self.logger.error("omitting directory '%s'" % src)
	
	def dir_action(self, type, top, src, dst):
		if not exists(dst):
			mkdir(dst)
			self.copystat_if_wanted(src, dst)			
					
	def link_action(self, type, top, src, dst):
		if type == HARDLINK:
			copylink(src, dst, force=self.options.force, hardlink=True)
			self.copystat_if_wanted(src, dst)
		elif type == LINK:
			copylink(src, dst, force=self.options.force, hardlink=False)

	def file_action(self, type, top, src, dst):
		if exists(dst) and self.options.interactive:
			self.interactive_list.append( (type, top, src, dst) )
		else:
			self._real_file_action(type, top, src, dst)

	def _real_file_action(self, type, top, src, dst):
		self.logger.start_copy(src, dst)
		
		copyfile(src, dst, resume=self.options.resume,
			force=self.options.force, callback=self.logger.update_copy)
		self.copystat_if_wanted(src, dst)
		
		self.logger.finish_copy(src, dst)

	def handle_interactive(self):
		for type, top, src, dst in self.interactive_list:
			answer = self.logger.input("overwrite '%s'?" % dst)
			if answer.lower() in ['yes', 'ye', 'y']:
				self._real_file_action(type, top, src, dst)

	def run(self):
		super(self.__class__, self).run()
		self.handle_interactive()

	def copystat_if_wanted(self, src, dst):
		if self.options.preserve_attributes:
			copystat(src, dst)	

class TestWalker(PathWalker):
	def file_action(self, type, top, src, dst):
		print("'%s' -> '%s'" % (src, dst) )
	
	def hardlink_action(self, type, top, src, dst):
		print("'%s' -> '%s'" % (src, dst) )
	
	def link_action(self, type, top, src, dst):
		print("'%s' -> '%s'" % (src, dst) )
	
	def dir_action(self, type, top, src, dst):
		print("'%s' -> '%s'" % (src, dst) )
		
	def error(self, type, top, src, dst):
		pass

