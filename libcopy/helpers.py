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


def dummy(*args, **kwargs):
	pass
