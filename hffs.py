#!/usr/bin/env python

from sys import argv
import os
import string
import hashlib
import errno

from fuse import FUSE, FuseOSError, Operations

class HFFS(Operations):
    '''
    There are two name-hash mappings:
    1. The cached actual files and hashes ("cache")
    2. The inputted hash list ("hash list")
    
    We want to check the status of the actual files in the cache and return the result (in/out) if found.
    Otherwise, hash the file and attempt to match the file name/path if the hash is in the hash list.
    
    The cache is an actual file path to filter status mapping. File paths are unique, so this can be a straight mapping.
    The hash list is a hash to file path mapping. Hashes aren't necessarily unique, so we'll need the file paths in a list.
    '''
    def __init__(self, rootDir, hashFile, matchType):
        self.rootDir = os.path.abspath(rootDir)
        self.hashFile = hashFile
        self.hashList = {}
        self.cache = {}
        self.matchType = matchType
        
        for line in open(self.hashFile):
            words = string.split(line)
            fileHash = words[0]
            filePath = words[1]
            
            while filePath[0:1] == "./":
                filePath = filePath[2:]
            
            if filePath[0] != "/":
                filePath = "/" + filePath
            
            if fileHash in self.hashList:
                pathList = self.hashList[fileHash]
                pathList.append(filePath)
                self.hashList[fileHash] = pathList
            else:
                self.hashList[fileHash] = [filePath]

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
                if path in self.cache:
                    match = self.cache[path]
                    print("Seen path " + path + " before. Match:")
                    print(match)
                else:
                    print("Not checked " + path + " before. Match:")
                    fileHash = self.generateHash(rootPath)
                    if fileHash in self.hashList:
                        print("Hash in hash list")
                        pathList = self.hashList[fileHash]
                        for hashListPath in pathList:
                            print("Compare against: " + hashListPath)
                            if self.pathStringMatches(path, hashListPath):
                                match = True
                                break
                    self.cache[path] = match
                    print(match)
            return match
        except IOError as e:
            if e.errno == errno.EACCES:
                print("Access denied")
                return False
            raise FuseOSError(e.errno)

    def getattr(self, path, fh=None):
        print("getattr: " + path)
        if self.matches(path):
            raise FuseOSError(ENOENT)
        else:
            stats = os.lstat(self.rootDir + path)
            return dict((key, getattr(stats, key)) for key in ('st_atime', 'st_ctime', 'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))

    def open(self, path, flags):
        print("open: " + path)
        if self.matches(path):
            raise FuseOSError(ENOENT)
        else:
            return os.open(self.rootDir + path, flags)

    def read(self, path, length, offset, fh):
        print("read: " + path)
        if self.matches(path):
            raise FuseOSError(ENOENT)
        else:
            os.lseek(fh, offset, os.SEEK_SET)
            return os.read(fh, length)

    def readdir(self, path, fh):
        print("readdir: " + path)
        if path[-1:] != "/":
            path = path + "/"
        for fileName in os.listdir(self.rootDir + path):
            if self.matches(path + fileName) == False:
                yield fileName

    def readlink(self, path):
        return os.readlink(self.rootDir + path)
    
    def release(self, path, fh):
        print("release: " + path)
        return os.close(fh)
    
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

if __name__ == '__main__':
    if len(argv) != 5:
        print("usage: %s <rootDir> <hashFile> <matchType[none|file|fullPath]> <mountpoint>" % argv[0])
        exit(1)
    fuse = FUSE(HFFS(argv[1], argv[2], argv[3]), argv[4], foreground=True, nothreads=True)

