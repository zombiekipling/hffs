#!/usr/bin/env python

import sys
import os
import string
import hashlib
import errno

import fuse
from fuse import Fuse

fuse.fuse_python_api = (0, 2)
fuse.feature_assert('has_init')

class HFFS(Fuse):

    def __init__(self, *args, **kw):
        Fuse.__init__(self, *args, **kw)
        self.rootDir = ""
        self.hashFile= ""
        self.hashList = {}
        self.fileRecords = {}

    def main(self, *a, **kw):
        if self.fuse_args.mount_expected():
            print "rootDir = " + self.rootDir
            self.rootDir = os.path.abspath(self.rootDir)
            print "rootDir = " + self.rootDir
            for line in open(self.hashFile):
                words = string.split(line)
                self.hashList[words[0]] = words[1]
        return Fuse.main(self, *a, **kw)

    def generateHash(self, path):
        blockSize = 32 * 1024 * 1024
        hashFunc = hashlib.sha256()
        with open(path, "rb") as f:
            dataBuffer = f.read(blockSize)
            while len(dataBuffer) > 0:
                hashFunc.update(dataBuffer)
                dataBuffer = f.read(blockSize)
        return hashFunc.hexdigest()

    def matches(self, path):
        try:
            rootPath = self.rootDir + path
            match = False
            if os.path.isfile(rootPath):
                if path in self.fileRecords:
                    print("Seen path " + path + " before:")
                    print(self.fileRecords[path])
                    match = self.fileRecords[path][1]
                else:
                    print("Not seen path " + path + " before:")
                    fileHash = self.generateHash(rootPath)
                    if fileHash in self.hashList:
                        print("hashList value = " + self.hashList[fileHash])
                        print("rootPath = " + rootPath)
                    if fileHash in self.hashList and self.hashList[fileHash] == rootPath:
                        match=True
                    self.fileRecords[path] = (fileHash, match)
                    print(self.fileRecords[path])
            return match
        except IOError as e:
            if e.errno == errno.EACCES:
                return False
            raise

    def getattr(self, path):
        if self.matches(path):
            return -errno.ENOENT
        else:
            return os.lstat(self.rootDir + path)

    def open(self, path, flags):
        print("open: " + path)
        if self.matches(path):
            return -errno.ENOENT
        else:
            return os.open(self.rootDir + path, flags)

    def read(self, path, size, offset):
        if self.matches(path):
            return -errno.ENOENT
        else:
            return os.read(self.rootDir + path, size, offset)

    def readdir(self, path, offset):
        print("readdir: " + path)
        if path[-1:] != "/":
            path = path + "/"
        for fileName in os.listdir(self.rootDir + path):
            if self.matches(path + fileName) == False:
                yield fuse.Direntry(fileName)

    def readlink(self, path):
        return os.readlink(self.rootDir + path)
    
    # All writes fail
    def chmod(self, path, mode):
        return -errno.EROFS
    
    def chown(self, path, user, group):
        return -errno.EROFS
    
    def link(self, source, linkName):
        return -errno.EROFS
    
    def mkdir(self, path, mode):
        return -errno.EROFS
    
    def rename(self, src, dst):
        return -errno.EROFS
    
    def rmdir(self, path):
        return -errno.EROFS
    
    def symlink(self, source, linkName):
        return -errno.EROFS
    
    def unlink(self, path):
        return -errno.EROFS
    
def main():
    usage = "Hash Filter File System\n" + Fuse.fusage
    filesystem = HFFS(version="%prog " + fuse.__version__,
                 usage=usage,
                 dash_s_do='setsingle')
    filesystem.multithreaded = False
    filesystem.parser.add_option(mountopt="rootDir", metavar="PATH", default="/",
                             help="Filter filesystem from PATH [default: %default]")
    filesystem.parser.add_option(mountopt="hashFile", metavar="FILE", default="hashFile.txt",
                             help="Hash list file containing files to filter out in hash<whitespace>path format [default: %default]")
    filesystem.parse(values=filesystem, errex=1)

    filesystem.main()

if __name__ == '__main__':
    main()
