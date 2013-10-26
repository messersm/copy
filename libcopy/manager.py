# standard imports

import sys

# local imports
from .logger import Logger

class CopyManager(object):
	def __init__(self, options):
		self.options = options
		
		self.logger = Logger(verbose=self.options.verbose)
		self.workers = []
	
	def start(self):
		for worker in self.workers:
			worker.run()
		
		self.logger.finish()
