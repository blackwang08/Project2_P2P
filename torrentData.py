# defines a listing of peers and files available in the network

class torrentData:
    CHUNK_SIZE = 512

    def __init__(self):

        self.peerDict = {
            # ID : [IP, PORT, UPLOAD, DOWNLOAD]
        }
        self.fileDict = {
            # "FILE HASH": { "filename" : FILE_NAME , "filesize" : FILESIZE(bytes), "totalchunks" : NUM_CHUNKS,
            # "chunkDict" : {0 : [ID, ID, ...], 1 : [ID, ID, ...]}}
        }

    # adds file with no owned chunks
    def addFile(self, hashname, filename , size):
        if hashname in self.fileDict.keys():
            return False

        numChunks = -(-size // self.CHUNK_SIZE)
        self.fileDict[hashname] = { "filename" : filename ,"filesize": size, "totalchunks": numChunks, "chunkDict": {}}
        for i in range(0, self.fileDict[hashname]["totalchunks"]):
            self.fileDict[hashname]["chunkDict"][i] = []
        return True

    # use fileDict.pop("filename") if ever needed

    # adds to known peers, but does not inform on owned chunks
    def addPeer(self, pid, ip, port, upload, download):
        if pid in self.peerDict.keys():
            return False  # no duplicate
        self.peerDict[pid] = [ip, port, upload, download]
        return True

    # removes from peerDict and removes from chunkDicts
    def removePeer(self, pid):
        if pid not in self.peerDict.keys():
            return False

        for f in self.fileDict.keys():
            for c in self.fileDict[f]["chunkDict"].keys():
                self.fileDict[f]["chunkDict"][c].remove(pid)

        self.peerDict.pop(pid)
        return True

    # peer obtains single chunk of file
    def peerAquireFileChunk(self, pid, hashname, chunk):
        if pid not in self.peerDict.keys():
            return False  # pid not registered
        if hashname not in self.fileDict.keys():
            return False  # non existance file to own
        if chunk >= self.fileDict[hashname]["totalchunks"]:
            return False  # non-existant chunk
        # chunk has been registered
        if chunk in self.fileDict[hashname]["chunkDict"]:
            if pid in self.fileDict[hashname]["chunkDict"][chunk]:
                return False  # already owns

        self.fileDict[hashname]["chunkDict"][chunk].append(pid)
        return True

    # peer obtains all chunks of file (when they first connect)
    def peerAquireWholeFile(self, pid, hashname):
        if pid not in self.peerDict.keys():
            return False
        if hashname not in self.fileDict.keys():
            return False
        for c in range(0, self.fileDict[hashname]["totalchunks"]):
            self.peerAquireFileChunk(pid, hashname, c)
        return True
