# standard imports

import sys

if sys.version_info.major < 3:
	from Queue import Queue
else:
	from queue import Queue

# local imports
from .worker import Walker, CopyWorker, JobHandler, InteractionHandler
from .logger import Logger

class CopyManager(object):
	def __init__(self, options):
		self.options = options
		
		self.jobQ = Queue()
		self.copyQ = Queue()
		self.interactQ = Queue()
		
		self.logger = Logger(verbose=self.options.verbose)
		
		self.workers = [	Walker(self),
							JobHandler(self),
							InteractionHandler(self),
							CopyWorker(self),
						]
		
	def start(self):
		for t in self.workers:
			t.start()
		
		for t in self.workers:
			t.join()

		self.logger.finish()

	def stop(self):
		for t in self.workers:
			t.stop()
