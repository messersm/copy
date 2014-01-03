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

"""Module that takes care of the actual copying."""

__docformat__ = 'restructuredtext'

# standard imports
import os

from os.path import exists, getsize, isdir, islink, isfile
from shutil import _samefile, Error, SpecialFileError, stat

# local imports
from .helpers import dummy

def isdevfile(filename):
    """Test, if filename points to a device file.
    
    :Parameters:
        `filename` : str
            The filename of the file to check.
    
    :rtype: bool
    
    """
    
    try:
        st = os.stat(filename)
    except OSError:
        return False

    return stat.S_ISCHR(st.st_mode) or stat.S_ISBLK(st.st_mode)


def copylink(src, dst, force=False, hardlink=False):
    """Copy a symbolic or hardlink.
    
    :Parameters:
        `src` : str
            Filename of the source file.
        `dst` : str
            Filename of the destination file.
        `force` : bool
            Force overwriting dst, if it exists.
        `hardlink` : bool
            Create the hardlink dst for src.
            
            
    :raise shutil.Error: Raised, if copying the link fails.
    """
    
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
    
    if hardlink:
        os.link(src, dst)
    else:
        target = os.readlink(src)   
        os.symlink(target, dst)

def copyfileobj(fsrc, fdst, length=16*1024, callback=dummy):
    """Copy data from fsrc to fdst.
    
    :Parameters:
        `fsrc` : file-like object
            The source file of the data.
        `fdst` : file-like object
            The destination file of the data.
        `length` : int
            The blocksize to copy.
    
    This function is called by the copyfile function.
    """
    
    while 1:
        buf = fsrc.read(length)
        if not buf:
            break
           
        callback( len(buf) )
        fdst.write(buf)

def copyfile(src, dst, length=16*1024, resume=False, force=False, callback=dummy):
    """Copy data from src to dst.
    
    :Parameters:
        `src` : str
            The filename of the source file.
        `dst` : str
            The filename of the destination file.
        `length` : int
            The blocksize to copy (defaults to 16K). 
        `resume` : bool
            Whether or not dst is intended to be a partly copy of src.
            If True, we try to continue copying instead of recopying
            already complete data.
        `force` : bool
            Force overwriting already existing files.
        `callback` : callable
            A callback-function that is called everytime we copy a
            block of data. It should take exactly one argument: The
            number of bytes copied at that time.
    """

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

    try:
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
                    
    except IOError:
        raise Error("Can't open '%s': Permission denied" % src)

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

    :Parameters:
        `src` : str
            The name of the source file.
        `dst` : str
            The name of the destination file.
        `length` : int
            The blocksize to use in order to check whether the data
            in dst is the same as in src.
        `step` : int
            The distance between checked data blocks.

    :rtype: bool
    
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
                    return _checkpart(fsrc, fdst, dstsize - length,
                                length=length)
                                
                if not _checkpart(fsrc, fdst, offset, length=length):
                    return False
                
                offset += step

