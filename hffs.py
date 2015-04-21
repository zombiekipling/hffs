#!/usr/bin/env python

from fuse import FUSE

class HFFS():

    def __init__(self, root, hashList):
        self.root = root
        self.hashList = hashList
        self.fileHashes = {}

    def open(self, path, flags):
        exclude = false
        if path in self.hashTable:
            exclude = self.fileHashes[path][1]
        else:
            hash = hashFile(root + path)
            exclude = hash in hashList
            self.fileHashes[path] = (hash, exclude)
        
        if ! exclude:
            os.open(root + path)

if __name__ == '__main__':
    fuse = FUSE(HFFS(), argv[1], foreground=True)
