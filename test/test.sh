#!/bin/bash
# For testing hffs.py.

TESTSFILE="tests.txt"

TESTDIR=$(mktemp -d)
echo "Test directory: ${TESTDIR}"

echo "Creating hash list file"
HASHLISTFILE="${TESTDIR}/hashlist"
HASHLISTDIR="${TESTDIR}/forhashing"
mkdir "${HASHLISTDIR}"
mkdir "${HASHLISTDIR}/dirA"
mkdir "${HASHLISTDIR}/dirB"
echo "ryu" > "${HASHLISTDIR}/dirA/file1"
echo "ryu" > "${HASHLISTDIR}/dirB/file2"
pushd "${HASHLISTDIR}"
find * -type f | xargs sha256sum > "${HASHLISTFILE}"
popd

echo "Creating test root directory"
ROOTDIR="${TESTDIR}/rootdir"
mkdir "${ROOTDIR}"
mkdir "${ROOTDIR}/dirA"
mkdir "${ROOTDIR}/dirB"
mkdir "${ROOTDIR}/dirC"
mkdir "${ROOTDIR}/dirD"
FILEPATHhdf="dirC/file3"
FILEPATHhdF="dirC/file1"
FILEPATHhDf="dirA/file3"
FILEPATHhDF="dirA/file1"
FILEPATHHdf="dirD/file4"
FILEPATHHdF="dirD/file2"
FILEPATHHDf="dirB/file4"
FILEPATHHDF="dirB/file2"
echo "ken" > "${ROOTDIR}/${FILEPATHhdf}"
echo "ken" > "${ROOTDIR}/${FILEPATHhdF}"
echo "ken" > "${ROOTDIR}/${FILEPATHhDf}"
echo "ken" > "${ROOTDIR}/${FILEPATHhDF}"
echo "ryu" > "${ROOTDIR}/${FILEPATHHdf}"
echo "ryu" > "${ROOTDIR}/${FILEPATHHdF}"
echo "ryu" > "${ROOTDIR}/${FILEPATHHDf}"
echo "ryu" > "${ROOTDIR}/${FILEPATHHDF}"

MOUNTDIR="${TESTDIR}/mountdir"
mkdir "${MOUNTDIR}"
FAILSTRING="Failed cases:"
FAILURES=0
for MATCHTYPE in none file fullPath; do
	echo "Starting match type ${MATCHTYPE}"
	python ../hffs.py "${ROOTDIR}" "${HASHLISTFILE}" "${MATCHTYPE}" "${MOUNTDIR}"
	
	SUBTESTSFILE=$(mktemp)
	grep "${MATCHTYPE}" "${TESTSFILE}" > "${SUBTESTSFILE}"
	
	while read TESTCASE MATCHTYPE2 HASHMATCH FILENAMEMATCH DIRMATCH RESULT; do
		if [ "${TESTCASE:0:1}" != "#" -a "${TESTCASE}" != "" -a "${MATCHTYPE}" == "${MATCHTYPE2}" ]; then
			echo "Starting test case ${TESTCASE}"
		
			FILEPATHVAR="FILEPATH"
			if [ "${HASHMATCH}" = "true" ]; then
				FILEPATHVAR="${FILEPATHVAR}H"
			else
				FILEPATHVAR="${FILEPATHVAR}h"
			fi
			if [ "${DIRMATCH}" = "true" ]; then
				FILEPATHVAR="${FILEPATHVAR}D"
			else
				FILEPATHVAR="${FILEPATHVAR}d"
			fi
			if [ "${FILENAMEMATCH}" = "true" ]; then
				FILEPATHVAR="${FILEPATHVAR}F"
			else
				FILEPATHVAR="${FILEPATHVAR}f"
			fi
			
			FILEPATH=$(eval echo \$\{${FILEPATHVAR}\})
			FILEPATH="${MOUNTDIR}/${FILEPATH}"
			if [ -f "${FILEPATH}" ]; then
				if [ "${RESULT}" == "not" ]; then
					echo "Pass - file correctly not filtered"
				else
					echo "Fail - file incorrectly not filtered"
					FAILSTRING="${FAILSTRING} ${TESTCASE}"
					FAILURES=1
				fi
			else
				if [ "${RESULT}" == "not" ]; then
					echo "Fail - file incorrectly filtered"
					FAILSTRING="${FAILSTRING} ${TESTCASE}"
					FAILURES=1
				else
					echo "Pass - file correctly filtered"
				fi
			fi
		fi
	done < "${SUBTESTSFILE}"
	
	fusermount -u "${MOUNTDIR}"
done

if [ -d "${TESTDIR}" ]; then
	rm -rf "${TESTDIR}"
fi

if [ "${FAILURES}" == 1 ]; then
	echo "${FAILSTRING}"
	exit 1
else
	echo "All passed"
	exit 0
fi
