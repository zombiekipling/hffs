# hffs
Hash Filter File System
=======================

A simple file system to filter out files with known hash values.

Dependencies
------------

* python
* FUSE
* [fusepy](https://github.com/terencehonles/fusepy)

Usage
-----
`python hffs.py rootDir hashFile matchType mountpoint`

`rootDir` is directory to be filtered.

`hashFile` is in hash(whitespace)filepath format, e.g. as produced by sha256sum. (Currently only SHA256 is supported.)

`matchType` controls how the file names/paths are compared:

* `none`: Don't consider the file name/path at all, i.e. only the hash.
* `file`: Only compare the file's name, not the path.
* `fullPath`: Compare the file's full path within `rootDir` to the full string in the hash file.

`mountpoint` is the filtered output mount point.
