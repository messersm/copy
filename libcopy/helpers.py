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


_FILESIZES = [	(1024**4, "T"),
				(1024**3, "G"),
				(1024**2, "M"),
				(1024**1, "K")
			]

def readable_filesize(filesize):
	"""Returns a human readable string from an integer filesize."""
	for size, ext in _FILESIZES:
		if filesize >= size:
			return "%.1f%s" % (float(filesize) / size, ext)
	
	return "%d" % filesize


def shortname(name, length=8):
	"""Returns name with length length, shortening or appending if needed."""
	s_len = len(name)
	
	if s_len <= length:
		return name + ' ' * (length - s_len )
		
	dots = '.' * (2 + length % 2)
	part = (length - length % 2 - 2) // 2
	
	return name[:part] + dots + name[-part:]

def dummy(*args, **kwargs):
	pass
