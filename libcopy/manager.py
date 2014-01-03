# Copyright (C) 2013-2014 Maik Messerschmidt

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

"""Very simple copymanager module."""

# standard imports
import sys

# local imports
from .logger import Logger
from .walk import ModeError

class CopyManager(object):
    """Takes care of letting the workers work (one after another)."""
    
    def __init__(self, options):
        self.options = options
        
        self.logger = Logger(verbose=self.options.verbose)
        self.workers = []
    
    def start(self):
        # fatal exceptions should be caught here.
        
        try:
            for worker in self.workers:
                worker.run()
        
        except ModeError as e:
            self.logger.error( str(e) )
            return
        
        self.logger.finish()
