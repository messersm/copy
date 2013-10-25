# standard imports
import sys

from os.path import basename

PROG = basename(sys.argv[0])

class BaseLogger(object):
	def start_copy(self, src, dst):
		pass
	
	def update_copy(self, bytes_done):
		pass
	
	def finish_copy(self, src, dst):
		pass

	def error(self, msg):
		sys.stderr.write("%s: %s\n" % (PROG, msg) )
	
	def input(self, msg):
		return raw_input("%s: %s" % (PROG, msg) )

	def set_total(self, bytes_total):
		pass

	
	def finish(self):
		pass

class VerboseLogger(BaseLogger):
	def start_copy(self, src, dst):
		sys.stderr.write("'%s' -> '%s'\n" % (src, dst) )

def Logger(verbose=0):
	"""Factory function that returns the wanted logger instance."""
	
	if verbose == 0:
		return BaseLogger()
	
	# 
	elif verbose == 1:
		return VerboseLogger()
