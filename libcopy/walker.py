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


from os.path import (	isfile, isdir, islink, exists, basename,
						join, relpath, normpath, getsize)
from os import listdir, mkdir

from shutil import copystat

# local imports
from .copy import copyfile, copylink, Error, isdevfile
from .helpers import readable_filesize

# constants
PROG = basename(sys.argv[0])

class PathWalker(object):
	def __init__(self, options):
		self.options = options
		
		# link policies
		# self.LINK_PRESERVE = 1
		# self.LINK_FOLLOW_COMMAND_LINE = 2
		# self.LINK_FOLLOW_ALL = 3
		
		self.inodes = {}
	
	def hardlink_action(self, src, dst):
		pass
	
	def link_action(self, src, dst):
		pass
	
	def file_action(self, src, dst):
		pass
	
	def dir_action(self, src, dst):
		pass

	def compose_dstname(self, commandline, src):
		target = self.options.dest
		
		if src == commandline and isfile(src) and not exists(target):
			return target
		
		elif not isdir(target):
			rel = relpath(src, commandline)
			dst = normpath( join(target, rel) )
			return dst
	
		else:
			rel = relpath(src, join(commandline, '..') )
			dst = join(target, rel)
			return dst

	def error(self, src, dst, msg):
		pass

	def walk_all(self):
		for src in self.options.sources:
			self.walk(src)

	def walk(self, src, commandline=None):
		if commandline == None:
			commandline = src

		dst = self.compose_dstname(commandline, src)

		if not exists(src):
			self.error(src, dst, "cannot stat `%s': No such file or directory" % src)
			return
		
		if islink(src):
			if self.options.link_policy == 'preserve':
				self.link_action(src, dst)
				return
				
			elif self.options.link_policy == 'follow_commandline' and src != commandline:
				link_action(src, dst)
				return
			
		if isdir(src):
			if not self.options.recursive:
				self.error(src, dst, "omitting directory `%s'" % src)
				return
		
			if isfile(dst):
				self.error(src, dst, "cannot overwrite non-directory `%s' with directory `%s'" % (dst, src) )
				return
			
			self.dir_action(src, dst)
			
			for item in listdir(src):
				fullname = join(src, item)
				self.walk(fullname, commandline=commandline)
				
		elif isfile(src):
			try:
				st = os.stat(src)
				old_dst = self.inodes.get(st.st_ino, None)
				
				if old_dst and self.options.link_policy == 'preserve':
					self.hardlink_action(old_dst, dst)
				else:
					self.inodes[st.st_ino] = dst
			except OSError:
				pass
			
			self.file_action(src, dst)
		elif isdevfile(src):
			self.file_action(src, dst)

class FilesizeWalker(PathWalker):
	def __init__(self, *args, **kwargs):
		super(self.__class__, self).__init__(*args, **kwargs)
		
		self.bytes_total = 0
	
	def file_action(self, src, dst):
		self.bytes_total += getsize(src)

class CopyWalker(PathWalker):
	def file_action(self, src, dst):
		try:
			copyfile(src, dst, resume=self.options.resume, force=self.options.force)
			self.copystat_if_wanted(src, dst)
		except Error as e:
			self.error(src, dst, str(e))
	
	def hardlink_action(self, src, dst):
		try:
			copylink(src, dst, force=self.options.force, hardlink=True)
		except Error as e:
			self.error(src, dst, str(e))
		
	def link_action(self, src, dst):
		try:
			copylink(src, dst, force=self.options.force)
			# we don't copy stats of links, since they are ignored anyway...
			# Additional this causes errors if copying links that are broken.
			# self.copystat_if_wanted(src, dst)
		except Error as e:
			self.error(src, dst, str(e))
	
	def dir_action(self, src, dst):
		try:
			if not exists(dst):
				mkdir(dst)
				self.copystat_if_wanted(src, dst)
		except Error as e:
			self.error(src, dst, str(e))
		
	def copystat_if_wanted(self, src, dst):
		if self.options.preserve_attributes:
			copystat(src, dst)
		
	def error(self, src, dst, msg):
		sys.stderr.write("%s: %s\n" % (PROG, msg) )

class NoisyCopyWalker(CopyWalker):
	def __init__(self, bytes_total, *args, **kwargs):
		super(self.__class__, self).__init__(*args, **kwargs)
		
		self.bytes_total = bytes_total
		self.bytes_done = 0
		
		self.f_bytes_done = 0
		self.f_bytes_total = 0
		
		self.f_name = ''
	
	def file_action(self, src, dst):
		self.f_name = basename(src)
		self.f_bytes_done = 0
		self.f_bytes_total = getsize(src)
		copyfile(src, dst, resume=self.options.resume, callback=self.update_state)
	
	def update_state(self, bytes_step):
		self.bytes_done += bytes_step
		self.f_bytes_done += bytes_step
		
		s = "%s: " % self.f_name
		i = 0
		
		for (a, b) in (	(self.f_bytes_done, self.f_bytes_total),
						(self.bytes_done, self.bytes_total) ):
			
			c = float(a) * 100 / b
			s += "%s/%s" % (readable_filesize(a), readable_filesize(b) )
			s += " (%.1f%%)" % c
			
			if i == 0:
				s += ", total: "
				i += 1

		sys.stderr.write("\r%s" % s)
		

class TestWalker(PathWalker):
	def file_action(self, src, dst):
		print("file: %s -> %s" % (src, dst) )
	
	def link_action(self, src, dst):
		print("link: %s -> %s" % (src, dst) )
	
	def dir_action(self, src, dst):
		print("dir: %s -> %s" % (src, dst) )
		
	def error(self, src, dst, msg):
		print("ERROR: %s" % msg)

