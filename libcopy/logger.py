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

from os.path import basename, getsize

# local imports
from .helpers import readable_filesize, shortname


PROG = basename(sys.argv[0])
TERMINAL_WIDTH = 80

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
        # raw_input writes to stdout, we want stderr
        sys.stderr.write("%s: %s " % (PROG, msg) )
        return raw_input()

    def set_total(self, bytes_total):
        pass

    
    def finish(self):
        pass

class VerboseLogger(BaseLogger):
    def start_copy(self, src, dst):
        sys.stderr.write("'%s' -> '%s'\n" % (src, dst) )

class ProgressLogger(BaseLogger):
    def __init__(self, *args, **kwargs):
        super(ProgressLogger, self).__init__(*args, **kwargs)
        
        self.bytes_done = 0
        self.bytes_total = 0
        
        self.f_bytes_done = 0
        self.f_bytes_total = 0
        self.f_name = ""
    
    def start_copy(self, src, dst):
        self.f_name = basename(src)
        self.f_bytes_total = getsize(src)
        self.f_bytes_done = 0
    
    def finish_copy(self, src, dst):
        self.f_name = ""

    def set_total(self, bytes_total):
        self.bytes_total = bytes_total

    def update_copy(self, bytes_step):
        self.bytes_done += bytes_step
        self.f_bytes_done += bytes_step
        
        s = '' 
        i = 0
        
        for (a, b) in ( (self.f_bytes_done, self.f_bytes_total),
                        (self.bytes_done, self.bytes_total) ):
            
            if b == 0:
                c = 100
            else:
                c = float(a) * 100 / b
            s += "%s/%s" % (readable_filesize(a), readable_filesize(b) )
            s += " (%.1f%%)" % c
            
            if i == 0:
                s += ", total: "
                i += 1

        fname = shortname(self.f_name + ': ', TERMINAL_WIDTH - len(s) )
        s = fname + s
        sys.stderr.write("\r%s" % s)
    
    def finish(self):
        sys.stderr.write('\n')

def Logger(verbose=0):
    """Factory function that returns the wanted logger instance."""
    
    if verbose == 0:
        return BaseLogger()
    
    # 
    elif verbose == 1:
        return VerboseLogger()
        
    else:
        return ProgressLogger()

