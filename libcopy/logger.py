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

"""Simple logger module."""

# standard imports
import sys

from os.path import basename


PROG = basename(sys.argv[0])


class BaseLogger(object):
	def __init__(self):
		self.had_errors = 0
	
	def start_copy(self, src, dst):
		pass
	
	def update_copy(self, bytes_done):
		pass
	
	def finish_copy(self, src, dst):
		pass

	def error(self, msg):
		self.had_errors = 1
		
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
