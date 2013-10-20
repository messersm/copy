import os
import stat

from os.path import islink, join

# file types
NOSTAT		= -1	# does not exist
IGNORE		= -2	# wants to be ignored
		
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
	"""Walks along the paths yielding a 3-tuple (TYPE, SRC, DST).
	
	TYPE is one of these module level constants:
	 - NOSTAT       File does not exist
	 - IGNORE       File wants to be ignored
	 - REG          Regular file
	 - DIR          Directory
	 - LINK         Symbolic link
	 - HARDLINK     Hardlink (regular file)
	 - BLOCK        Block device
	 - CHAR         Character device
	 - SOCK         Socket
	 
	SRC is the name of the file to operate on. It's equal to the file
	we just walked except in cases where the walked file is a hardlink
	to an already walked file and you want to preserve hardlinks. In
	this case it's equal to the name of the already walked file with the
	same inode.
	
	DST is the name of the destination file of the operation. It's
	always equal to the name of the file we just walked. You still need
	to adjust this name (e.g. join it with a name of the target
	directory).
		
	Accepted keywords:
	 - links:     L_FOLLOW_TOP    Follow top-level symlinks only
	              L_FOLLOW_ALL    Follow all symlinks
	              L_PRESERVE      Preserve symlinks
						
	 - recurse:   True            Recurse into directories
	              False           Don't

	"""
	
	inodes = {}
	
	links = kwargs.pop('links', L_FOLLOW_TOP)
	recurse = kwargs.pop('recurse', False)
	
	for key in kwargs:
		raise TypeError("walk() got an unexpected keyword argument '%s'" % key)
			
	for path in paths:
		for result in _walk_path(path,
							top=path,
							recurse=recurse,
							links=links,
							inodes=inodes):
			yield result

def _walk_path(path, top=None, recurse=False, links=L_FOLLOW_TOP, inodes={}):
	"""Walks along the given paths. Yields (TYPE, SRC, DST) tuple.
	
	This is an internal function and does the real work described by
	walk().
	"""
		
	# handle non-existent files
	try:
		st = os.stat(path)
	except OSError:
		st = None
		yield (NOSTAT, path, path)
		
	as_link = False
			
	# handle symlinks
	if st and islink(path):
		if links == L_PRESERVE:
			as_link = True
			yield (LINK, path, path)

		elif links == L_FOLLOW_TOP and path != top:
			as_link = True
			yield (LINK, path, path)

		
	if st and not as_link:
		if stat.S_ISDIR(st.st_mode):
			if not recurse:
				yield (IGNORE, path, path)
			else:
				yield (DIR, path, path)
				
				# recurse into dir
				for item in os.listdir(path):
					fullname = join(path, item)
					for result in _walk_path(fullname,
										top=top,
										recurse=recurse,
										links=links,
										inodes=inodes):
						yield result
			
		elif stat.S_ISREG(st.st_mode):
			# check for hardlinks
			if links == L_PRESERVE:
				old_path = inodes.get(st.st_ino, None)
				if old_path:
					yield (HARDLINK, old_path, path)
				else:
					# track this file:
					inodes[st.st_ino] = path
					yield (REG, path, path)
				
			else:
				# no need to keep track of inodes if
				# links is not L_PRESERVE
				yield (REG, path, path)
			
		elif stat.S_ISBLK(st.st_mode):
			yield (BLOCK, path, path)
				
		elif stat.S_ISCHR(st.st_mode):
			yield (CHAR, path, path)
			
		elif stat.S_ISSOCK(st.st_mode):
			yield (SOCK, path, path)
			
