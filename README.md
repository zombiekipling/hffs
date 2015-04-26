# hffs
Hash Filter File System

A simple file system to filter out files with known hash values.

Usage:
python hffs.py mountpoint -o rootDir=PATH -o hashFile=FILE

Hash file is in hash<whitespace>filepath format, e.g. as produced by sha256sum.

Currently only supports SHA256 and full path comparison (i.e. both the hash and the full path need to match).
