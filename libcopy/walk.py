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
import stat

from collections import namedtuple
from fnmatch import fnmatch
from os.path import islink, join


# file types
NOSTAT		= -1	# does not exist
IGNORE		= -2	# directory, we don't want to recurse into
EXCLUDE		= -3	# pathname was explicitly excluded
		
REG			= 1		# regular file
DIR			= 2		# directory
LINK		= 3		# symlink
HARDLINK	= 4		# hardlink (regular file)
BLOCK		= 5		# block device
CHAR		= 6		# character device
PIPE		= 7		# pipe
SOCK		= 8		# socket
		
# LINK POLICIES
L_FOLLOW_TOP	= 1
L_FOLLOW_ALL	= 2
L_PRESERVE		= 3

def walk(*paths, **kwargs):
	"""Walks along the paths yielding a 4-tuple (TYPE, TOP, SRC, DST).
	
	TYPE is one of these module level constants:
	 - NOSTAT       File does not exist
	 - IGNORE       Directory, we don't want to recurse into
	 - EXCLUDE      Pathname as been excluded
	 
	 - REG          Regular file
	 - DIR          Directory
	 - LINK         Symbolic link
	 - HARDLINK     Hardlink (regular file)
	 - BLOCK        Block device
	 - CHAR         Character device
	 - SOCK         Socket
	
	TOP is one of the paths that was given to walk(). This is useful
	if you want to use the relative path of SRC or DST.
	
	SRC is the name of the file to operate on. It's equal to the file
	we just walked except in cases where the walked file is a hardlink
	to an already walked file and you want to preserve hardlinks. In
	this case it's equal to the name of the already walked file with the
	same inode.
	
	DO NOTE: The current implementation of walk allows tracking
	hardlinks across different path-tops. That means, that SRC doesn't
	have to lie under TOP, if TYPE is HARDLINK.
	
	DST is the name of the destination file of the operation. It's
	always equal to the name of the file we just walked. You still need
	to adjust this name (e.g. join it with a name of the target
	directory).
	
	Accepted keywords:
	 - links:     L_FOLLOW_TOP    Follow top-level symlinks only
	              L_FOLLOW_ALL    Follow all symlinks
	              L_PRESERVE      Preserve symlinks
	              
	              default = L_FOLLOW_TOP
						
	 - recurse:   True            Recurse into directories
	              False           Don't
	              
	              default = False
	 
	 - excludes:  List of pathname patterns to exclude
	 
	              default = []

	"""
	
	inodes = {}
	
	links = kwargs.pop('links', L_FOLLOW_TOP)
	recurse = kwargs.pop('recurse', False)
	excludes = kwargs.pop('excludes', [])
	
	for key in kwargs:
		raise TypeError("walk() got an unexpected keyword argument '%s'" % key)
			
	for path in paths:
		for result in _walk_path(path,
							top=path,
							recurse=recurse,
							links=links,
							excludes=excludes,
							inodes=inodes):
			yield result

def _is_excluded(path, excludes):
	for exclude in excludes:
		if fnmatch(path, exclude):
			return True
	
	return False

def _walk_path( path, top=None, recurse=False, links=L_FOLLOW_TOP,
				excludes=[], inodes={}):
	"""Walks along the given paths. Yields (TYPE, TOP, SRC, DST) tuple.
	
	This is an internal function and does the real work described by
	walk().
	"""
	
	if _is_excluded(path, excludes):
		st = None
		yield (EXCLUDE, top, path, path)
	else:
		# handle non-existent files
		try:
			st = os.stat(path)
		except OSError:
			st = None
			yield (NOSTAT, top, path, path)
		
	as_link = False
			
	# handle symlinks
	if st and islink(path):
		if links == L_PRESERVE:
			as_link = True
			yield (LINK, top, path, path)

		elif links == L_FOLLOW_TOP and path != top:
			as_link = True
			yield (LINK, top, path, path)

		
	if st and not as_link:
		if stat.S_ISDIR(st.st_mode):
			if not recurse:
				yield (IGNORE, top, path, path)
			else:
				yield (DIR, top, path, path)
				
				# recurse into dir
				for item in os.listdir(path):
					fullname = join(path, item)
					for result in _walk_path(fullname,
										top=top,
										recurse=recurse,
										links=links,
										excludes=excludes,
										inodes=inodes):
						yield result
			
		elif stat.S_ISREG(st.st_mode):
			# check for hardlinks
			if links == L_PRESERVE:
				old_path = inodes.get(st.st_ino, None)
				if old_path:
					yield (HARDLINK, top, old_path, path)
				else:
					# track this file:
					inodes[st.st_ino] = path
					yield (REG, top, path, path)
				
			else:
				# no need to keep track of inodes if
				# links is not L_PRESERVE
				yield (REG, top, path, path)
			
		elif stat.S_ISBLK(st.st_mode):
			yield (BLOCK, top, path, path)
				
		elif stat.S_ISCHR(st.st_mode):
			yield (CHAR, top, path, path)
			
		elif stat.S_ISSOCK(st.st_mode):
			yield (SOCK, top, path, path)
			
