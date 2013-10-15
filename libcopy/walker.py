# standard imports
import sys

from os.path import (	isfile, isdir, islink, exists, basename,
						join, relpath, normpath, getsize)
from os import listdir, mkdir


# local imports
from .copy import copyfile, copylink
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
			self.file_action(src, dst)

class FilesizeWalker(PathWalker):
	def __init__(self, *args, **kwargs):
		super(self.__class__, self).__init__(*args, **kwargs)
		
		self.bytes_total = 0
	
	def file_action(self, src, dst):
		self.bytes_total += getsize(src)

class CopyWalker(PathWalker):
	def file_action(self, src, dst):
		copyfile(src, dst, resume=self.options.resume)
	
	def link_action(self, src, dst):
		copylink(src, dst)
	
	def dir_action(self, src, dst):
		if not exists(dst):
			mkdir(dst)
		
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

