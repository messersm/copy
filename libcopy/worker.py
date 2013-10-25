
# standard imports
import sys

if sys.version_info.major < 3:
	from Queue import Empty as QueueEmpty
else:
	from queue import Empty as QueueEmpty

from os import mkdir
from os.path import getsize, exists
from threading import Thread


# local imports
from .copy import copyfile, copylink, Error

from .walk import (NOSTAT, IGNORE, EXCLUDE,
					REG, DIR, LINK, HARDLINK, BLOCK, CHAR, PIPE, SOCK,
					walk)

class BaseWorker(Thread):
	def __init__(self, manager, *args, **kwargs):
		Thread.__init__(self, *args, **kwargs)
		
		self.manager = manager
		self.options = self.manager.options
		self.logger = self.manager.logger
		self.jobQ = self.manager.jobQ
		self.copyQ = self.manager.copyQ
		self.interactQ = self.manager.interactQ
		
		self.running = 1
		self.daemon = 1
	
	# not quite sure, if this sets different running variables
	# or if they're all the same for all threads...
	def stop(self):
		self.running = 0

class Walker(BaseWorker):
	"""Feeds jobs to the jobQ and counts bytes to copy."""
	
	def run(self):
		bytes_total = 0
		
		for result in walk(*self.options.sources,
			target=self.options.target,
			recurse=self.options.recurse,
			excludes=self.options.excludes,
			links=self.options.links):
			
			type, top, src, dst = result
			
			if type == REG:
				bytes_total += getsize(src)
		
			self.jobQ.put(result)
			
			if not self.running:
				return
		
		# this could also be done by a second thread, but that's overhead.
		self.logger.set_total(bytes_total)

class Worker(BaseWorker):
	def execute(self, func, src, dst):
		try:
			func(src, dst)
		except Error as e:
			self.logger.error( str(e) )
			
	def copystat_if_wanted(self, src, dst):
		if self.options.preserve_attributes:
			copystat(src, dst)	

class InteractionHandler(BaseWorker):
	def run(self):
		while self.running:
			try:
				result = self.interactQ.get(timeout=0.5)
			except QueueEmpty:
				continue
				
			(type, top, src, dst) = result
			
			answer = self.logger.input("overwrite '%s'?" % dst)
			if answer.lower() in ['yes', 'ye', 'y']:
				self.copyQ.put(result)

class JobHandler(Worker):
	"""Does all work except copying files."""
	def run(self):
		while self.running:
			try:
				result = self.jobQ.get(timeout=0.5)
			except QueueEmpty:
				continue
				
			(type, top, src, dst) = result
			
			if type == REG and exists(dst) and self.options.interactive:
				self.interactQ.put(result)
				continue
			
			if type == NOSTAT:
				self.logger.error("cannot stat '%s': No such file or directory" % src)
				
			elif type == IGNORE:
				self.logger.error("omitting directory '%s'" % src)
			
			elif type in [REG, BLOCK, CHAR, PIPE, SOCK]:
				self.copyQ.put(result)
			
			elif type == DIR:
				self.execute(self.dir_action, src, dst)
			
			elif type == LINK:
				self.execute(self.link_action, src, dst)
				
			elif type == HARDLINK:
				self.execute(self.hardlink_action, src, dst)

	def hardlink_action(self, src, dst):
		copylink(src, dst, force=self.options.force, hardlink=True)
		self.copystat_if_wanted(src, dst)

	def link_action(self, src, dst):
		copylink(src, dst, force=self.options.force, hardlink=False)

	def dir_action(self, src, dst):
		if not exists(dst):
			mkdir(dst)
			self.copystat_if_wanted(src, dst)

class CopyWorker(Worker):
	def run(self):
		while self.running:
			try:
				result = self.copyQ.get(timeout=0.5)
			except QueueEmpty:
				continue

			(type, top, src, dst) = result
			self.execute(self.file_action, src, dst)
	
	def file_action(self, src, dst):
		self.logger.start_copy(src, dst)
		
		copyfile(src, dst, resume=self.options.resume,
			force=self.options.force, callback=self.logger.update_copy)
		self.copystat_if_wanted(src, dst)
		
		self.logger.finish_copy(src, dst)
