# standard imports
import os

from os.path import exists, getsize, isdir, islink, isfile
from shutil import _samefile, Error, SpecialFileError, stat

# local imports
from .helpers import dummy

def copylink(src, dst, force=False):
	target = os.readlink(src)
	
	# cp unlinks files, which exist and overwrites them with links...
	# ... so do we. :)
	
	if exists(dst):
		# Don't unlink the file if -f is not set and dst
		# is not writeable by us.
		if force == False:
			try:
				fdst = open(dst, 'ab')
				fdst.close()
			except:
				raise Error("Can't create '%s': Permission denied" % dst)
		
		if isfile(dst) or islink(dst):
			try:
				os.unlink(dst)
			except OSError:
				raise Error("Can't remove '%s': Permission denied" % dst)
				
		elif isdir(dst):
			raise Error("cannot overwrite directory '%s' with non-directory" % dst)
		
	os.symlink(target, dst)

def copyfileobj(fsrc, fdst, length=16*1024, callback=dummy):
	"""copy data from file-like object fsrc to file-like object fdst"""
	while 1:
		buf = fsrc.read(length)
		if not buf:
			break
		   
		callback( len(buf) )
		fdst.write(buf)

def copyfile(src, dst, length=16*1024, resume=False, force=False, callback=dummy):
	"""Copy data from src to dst"""
	if _samefile(src, dst):
		raise Error("'%s' and '%s' are the same file" % (src, dst))

	for fn in [src, dst]:
		try:
			st = os.stat(fn)
		except OSError:
			# File most likely does not exist
			pass
		else:
			# XXX What about other special files? (sockets, devices...)
			if stat.S_ISFIFO(st.st_mode):
				raise SpecialFileError("'%s' is a named pipe" % fn)

	if exists(dst) and resume and ispartfile(src, dst):
		offset = getsize(dst)
		dst_mode = 'ab'
	else:
		offset = 0
		dst_mode = 'wb'

	with open(src, 'rb') as fsrc:
		try:
			with open(dst, dst_mode) as fdst:
				if offset > 0:
					fsrc.seek(offset)
					callback(offset)
			
				copyfileobj(fsrc, fdst, length=length, callback=callback)
		except IOError as e:
			if force:
				try:
					os.unlink(dst)
				except OSError:
					raise Error("Can't remove '%s': Permission denied" % dst)
				copyfile(src, dst, length=length, resume=resume, force=False, callback=callback)
			else:
				raise Error("Can't create '%s': Permission denied" % dst)

def _checkpart(fsrc, fdst, offset, length=512):
	fsrc.seek(offset)
	fdst.seek(offset)
			
	src_buf = fsrc.read(length)
	dst_buf = fdst.read(length)
	
	if src_buf == dst_buf:
		return True
	else:
		return False

def ispartfile(src, dst, length=512, step=1024**2):
	"""Checks whether dst is the beginning of the file src.
	Returns True or False.
	
	DO NOTE: Not all bytes in both files are checked - the default
	settings make sure, that blocks of 512 bytes of both files
	every 1M as well as the last 512 bytes are equal.
	"""
	
	srcsize = getsize(src)
	dstsize = getsize(dst)
	
	if srcsize < dstsize:
		return False
	
	if dstsize < length:
		return False
	
	offset = 0
	
	with open(src, 'rb') as fsrc:
		with open(dst, 'rb') as fdst:
			while 1:
				# check end
				if offset > dstsize - length:
					ret = _checkpart(fsrc, fdst, dstsize - length, length=length)
					# is this needed ?:
					fsrc.close()
					fdst.close()
				
					return ret
								
				if not _checkpart(fsrc, fdst, offset, length=length):
					fsrc.close()
					fdst.close()
					return False
				
				offset += step



