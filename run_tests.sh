#!/bin/sh

# we use the busybox testsuite to test copy
BUSYBOX_VERSION="1.21.1"
BUSYBOX_DIR="busybox-$BUSYBOX_VERSION"
BUSYBOX_FILE="$BUSYBOX_DIR.tar.bz2"
BUSYBOX_URL="http://www.busybox.net/downloads/$BUSYBOX_FILE"
BUSYBOX_SHA512="b1dd626e1c111214ebd9b933ce2465c943fd8a0a515b6962a31f3a76276ff7992c21b7f96eeb9baeb861a5e734689054e6df5dd6414c753c37084e2d705810e1"

OLD_PWD="$PWD"

if [ ! -e ".git" -o ! -e 'copy' ]; then
	echo "Please run this file from the git root."
	exit 1
else
	# Add copy to PATH - making sure we
	# use the development version
	PATH="$PWD:$PATH"
fi

# Download
if [ ! -e "tmp/$BUSYBOX_FILE" ]; then
	WGET="$(which wget)"
	CURL="$(which curl)"

	mkdir -p tmp || exit 1
	cd tmp || exit 1
	if [ "$WGET" ]; then
		wget $BUSYBOX_URL || exit 1
	elif [ "$CURL" ]; then
		curl $BUSYBOX_URL > $BUSYBOX_FILE || exit 1
	else
		echo "Don't know how to donwload busybox."
		exit 1
	fi
else
	cd tmp
fi

# Checksum and extract
if [ ! -d "$BUSYBOX_DIR" ]; then
	chksum="$(sha512sum $BUSYBOX_FILE)"
	if [ "$chksum" = "$BUSYBOX_SHA512  $BUSYBOX_FILE" ]; then
		tar -jxf "$BUSYBOX_FILE" || exit 1
	else
		echo "Bad checksum for $BUSYBOX_FILE."
		exit 1
	fi
fi

# patch files
if [ ! -e "$BUSYBOX_DIR/.copy_file_patched" ]; then
	for f in $(find $BUSYBOX_DIR/testsuite/cp -type f); do
		
		sed 's/busybox cp/copy/' $f > $f.new || exit 1
		mv -f $f.new $f
	done
	
	touch $BUSYBOX_DIR/.copy_file_patched || exit 1
fi

cd "$OLD_PWD" || exit 1

mkdir -p tmp/test_run || exit 1
cd tmp/test_run || exit 1

logfile="$(mktemp)"

for test in $(find ../$BUSYBOX_DIR/testsuite/cp -type f); do
	echo -n ">>> ${test##**/}"
	sh $test 2>$logfile
	
	if [ "$?" -eq 0 ]; then
		echo " - OK"
		cat $logfile || exit 1
	else
		echo " - FAIL"
		cat $logfile || exit 1
	fi
	
	if [ "$(find . -type f)" ]; then
		rm -r * || exit 1
	fi
done

rm $logfile || exit 1
