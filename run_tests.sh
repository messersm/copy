#!/bin/sh

# Copyright notice:

# Some of the tests in the 'tests'-directory are from the
# busybox (v1.21.1) testsuite. As busybox is released under the GPL,
# these tests are released under the GPL as well.

OLD_PWD="$PWD"

if [ ! -e ".git" -o ! -e 'copy' ]; then
	echo "Please run this file from the git root."
	exit 1
else
	# Add copy to PATH - making sure we
	# use the development version
	PATH="$PWD:$PATH"
fi

logfile="$(mktemp)"

for test in $(find $PWD/tests -type f); do
	tmpdir="$(mktemp -d)"
	
	cd $tmpdir || exit

	echo -n ">>> ${test##**/}"
	sh $test 2>$logfile
	
	if [ "$?" -eq 0 ]; then
		echo " - OK"
		cat $logfile || exit 1
	else
		echo " - FAIL"
		cat $logfile || exit 1
	fi

	cd "$OLD_PWD" || exit 1
	rm -rf $tmpdir || exit 1
	
done

rm $logfile || exit 1
