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
    '''
    There are two name-hash mappings:
    1. The cached actual files and hashes ("cache")
    2. The inputted hash list ("hash list")
    
    We want to check the status of the actual files in the cache and return the result (in/out) if found.
    Otherwise, hash the file and attempt to match the file name/path if the hash is in the hash list.
    
    The cache is an actual file path to filter status mapping. File paths are unique, so this can be a straight mapping.
    The hash list is a hash to file path mapping. Hashes are necessarily unique, so we'll need the file paths in a list.
    '''
    def __init__(self, *args, **kw):
        Fuse.__init__(self, *args, **kw)
        self.rootDir = ""
        self.hashFile= ""
        self.hashList = {}
        self.cache = {}
        self.matchType = "file"

    def main(self, *a, **kw):
        if self.fuse_args.mount_expected():
            self.rootDir = os.path.abspath(self.rootDir)
            for line in open(self.hashFile):
                words = string.split(line)
                fileHash = words[0]
                filePath = words[1]
                if fileHash in self.hashList:
                    pathList = self.hashList[fileHash]
                    pathList.append(filePath)
                    self.hashList[fileHash] = pathList
                else:
                    self.hashList[fileHash] = [filePath]
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
    
    def pathStringMatches(self, cachePath, hashListPath):
        if self.matchType == "none":
            return True
        elif self.matchType == "fullPath":
            if cachePath == hashListPath:
                return True
            else:
                return False
        else:
            # "file"
            if os.path.basename(cachePath) == os.path.basename(hashListPath):
                return True
            else:
                return False

    def matches(self, path):
        try:
            rootPath = self.rootDir + path
            match = False
            if os.path.isfile(rootPath):
                if rootPath in self.cache:
                    match = self.cache[rootPath]
                    print("Seen path " + path + " before:")
                    print(match)
                else:
                    print("Not checked " + path + " before:")
                    fileHash = self.generateHash(rootPath)
                    if fileHash in self.hashList:
                        print("Hash in hash list")
                        pathList = self.hashList[fileHash]
                        for hashListPath in pathList:
                            print("Compare against: " + hashListPath)
                            if self.pathStringMatches(rootPath, hashListPath):
                                match = True
                                break
                    self.cache[rootPath] = match
                    print(match)
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
    filesystem.parser.add_option(mountopt="matchType", metavar="TYPE", default="file",
        help="Matching mode for path component (""none"", ""file"" or ""fullPath"")")
    filesystem.parse(values=filesystem, errex=1)

    filesystem.main()

if __name__ == '__main__':
    main()
