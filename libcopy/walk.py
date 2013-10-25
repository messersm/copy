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

"""Walk along paths yielding copy jobs."""

# standard imports
import os
import stat

from fnmatch import fnmatch
from os.path import isdir, islink, join, normpath, relpath


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

# COPY MODES - represents one of the three cases possible:
COPY_FILE		= 1	# copy file to file
COPY_EX_DIR		= 2	# copy files and directories to an existing directory
COPY_NEW_DIR	= 3 # copy one directory tree to a new name

class ModeError(Exception):
	"""Indicates an invalid file/dir state for the copy operation."""
	pass

def walk(*paths, **kwargs):
	"""Walks along the paths yielding a 4-tuple (TYPE, TOP, SRC, DST).
	
	Raises a ModeError if target is invalid for paths.
	
	TYPE is one of these module level constants:
	 - NOSTAT       File does not exist
	 - IGNORE       Directory, we don't want to recurse into
	 - EXCLUDE      Pathname has been excluded
	 
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
	
	DST is the name of the destination file of the operation under target.
		
	Accepted keywords:
	 - links:       L_FOLLOW_TOP    Follow top-level symlinks only
	                L_FOLLOW_ALL    Follow all symlinks
	                L_PRESERVE      Preserve symlinks
	              
	                default = L_FOLLOW_TOP
						
	 - recurse:     True            Recurse into directories
	                False           Don't
	              
	                default = False
	 
	 - excludes:    List of pathname patterns to exclude
	 
	                default = []
	 
	 - target:      Name of the target.
	 
	                default = None (invalid)

	"""
	
	inodes = {}
	
	links = kwargs.pop('links', L_FOLLOW_TOP)
	recurse = kwargs.pop('recurse', False)
	excludes = kwargs.pop('excludes', [])
	target = kwargs.pop('target', None)
	
	if target == None:
		raise TypeError("walk() expects keyword argument 'target'.")
	
	for key in kwargs:
		raise TypeError("walk() got an unexpected keyword argument '%s'" % key)

	# detect the copy mode
	mode = _detect_mode(*paths, target=target)
		
	for path in paths:
		for result in _walk_path(path,
							top=path,
							target=target,
							recurse=recurse,
							links=links,
							excludes=excludes,
							inodes=inodes,
							mode=mode):
			yield result

def _detect_mode(*paths, **kwargs):
	"""Detects the file/dir state for src paths and target and returns MODE.
	
	MODE is one of:
	 - COPY_FILE    copy file to file
	 - COPY_EX_DIR	copy files and directories to an existing directory
	 - COPY_NEW_DIR	copy one directory tree to a new name
	
	Raises a ModeError for an invalid file/dir state.
	"""
	
	target = kwargs.pop('target', None)

	for key in kwargs:
		raise TypeError("_detect_mode() got an unexpected keyword argument '%s'" % key)
	
	if len(paths) > 1:
		if not isdir(target):
			raise ModeError("target '%s' is not a directory" % target)
		else:
			return COPY_EX_DIR
	elif isdir(target):
		return COPY_EX_DIR
		
	elif isdir(paths[0]):
		return COPY_NEW_DIR
		
	else:
		return COPY_FILE

def _compose_dst(top, src, target, mode=COPY_EX_DIR):
	"""Returns a destination path for the copy src -> target."""
	if mode == COPY_FILE:
		return target
		
	elif mode == COPY_EX_DIR:
		rel = relpath(src, join(top, '..') )
		return join(target, rel)

	elif mode == COPY_NEW_DIR:
		return normpath( join(target, relpath(src, top) ) )
		
def _is_excluded(path, excludes):
	for exclude in excludes:
		if fnmatch(path, exclude):
			return True
	
	return False

def _walk_path( path, top=None, target=None, recurse=False,
				links=L_FOLLOW_TOP, excludes=[], inodes={},
				mode=COPY_EX_DIR):
	"""Walks along the given paths. Yields (TYPE, TOP, SRC, DST) tuple.
	
	This is an internal function and does the real work described by
	walk().
	"""
	
	dst = _compose_dst(top, path, target, mode=mode)
	
	if _is_excluded(path, excludes):
		st = None
		yield (EXCLUDE, top, path, dst)
	else:
		# handle non-existent files
		try:
			st = os.stat(path)
		except OSError:
			st = None
			yield (NOSTAT, top, path, dst)
		
	as_link = False
			
	# handle symlinks
	if st and islink(path):
		if links == L_PRESERVE:
			as_link = True
			yield (LINK, top, path, dst)

		elif links == L_FOLLOW_TOP and path != top:
			as_link = True
			yield (LINK, top, path, dst)

		
	if st and not as_link:
		if stat.S_ISDIR(st.st_mode):
			if not recurse:
				yield (IGNORE, top, path, dst)
			else:
				yield (DIR, top, path, dst)
				
				# recurse into dir
				for item in os.listdir(path):
					fullname = join(path, item)
					for result in _walk_path(fullname,
										top=top,
										target=target,
										recurse=recurse,
										links=links,
										excludes=excludes,
										inodes=inodes,
										mode=mode):
						yield result
			
		elif stat.S_ISREG(st.st_mode):
			# check for hardlinks
			if links == L_PRESERVE:
				old_path = inodes.get(st.st_ino, None)
				if old_path:
					yield (HARDLINK, top, old_path, dst)
				else:
					# track this file:
					inodes[st.st_ino] = dst
					yield (REG, top, path, dst)
				
			else:
				# no need to keep track of inodes if
				# links is not L_PRESERVE
				yield (REG, top, path, dst)
			
		elif stat.S_ISBLK(st.st_mode):
			yield (BLOCK, top, path, dst)
				
		elif stat.S_ISCHR(st.st_mode):
			yield (CHAR, top, path, dst)
			
		elif stat.S_ISSOCK(st.st_mode):
			yield (SOCK, top, path, dst)
			
