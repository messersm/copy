copy
====
Advanced command line copy tool

Website
-------
https://sourceforge.net/projects/python-copy/

Installation
------------
tar -zxf copy-VERSION.tar.gz
cd copy-VERSION
python setup.py install

Tests
-----
You can run 'sh run_tests.sh' to test copy.
For now we use the busybox testsuite for cp, so this script will
download the busybox source first. Any options not supported by copy
will fail (like '--parents').
