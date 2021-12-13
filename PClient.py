import hashlib
import os
import time
from queue import SimpleQueue
from threading import Thread

from Proxy import Proxy
from torrentData import torrentData
from torrentPacket import torrentPacket


class PClient:
    def __init__(self, tracker_addr: (str, int), proxy=None, port=None, upload_rate=0, download_rate=0):
        if proxy:
            self.proxy = proxy
        else:
            self.proxy = Proxy(upload_rate, download_rate, port)  # Do not modify this line!
        self.tracker = tracker_addr
        self.myState = torrentData()
        self.id = -1
        self.rev_tracker_queue = SimpleQueue()
        self.rev_pclient_queue = SimpleQueue()
        Thread(target=self.__recv_thread__).start()
        self.__send__(
            torrentPacket.create_info(self.id, self.myState, upload_rate, download_rate).get_tcp_data(),
            tracker_addr)
        data, address = self.rev_tracker_queue.get()
        data = torrentPacket.parse_tcp_data(data)
        self.id = data.id
        self.myState = data.info
        """
        Start your additional code below!
        """

    def __recv_thread__(self):
        while True:
            if not self.proxy.recv_queue.empty():
                data, address = self.__recv__()
                Data = torrentPacket.parse_tcp_data(data)
                if Data.type == 0:
                    self.rev_tracker_queue.put((data, address))
                elif Data.type == 2:

                    fid = list(Data.info.fileDict.keys())[0]
                    filename = Data.info.fileDict[fid]["filename"]
                    chunk = 0
                    for c in Data.info.fileDict[fid]["chunkDict"].keys():
                        if len(Data.info.fileDict[fid]["chunkDict"][c]) > 0:
                            chunk = c
                            break
                    # print("Recieved req for " + filename + " " + str(c))
                    # send chunk from filename
                    f = open(filename, "rb")
                    f.seek(chunk * torrentData.CHUNK_SIZE)
                    chars = f.read(torrentData.CHUNK_SIZE)
                    f.close()
                    toSend = torrentPacket.create_data(self.id, fid, filename, chunk, chars, self.proxy.upload_rate,
                                                       self.proxy.download_rate).get_tcp_data()
                    # print(toSend)
                    self.__send__(toSend,
                                  (str(self.myState.peerDict[Data.id][0]), int(self.myState.peerDict[Data.id][1])))
                else:
                    self.rev_pclient_queue.put((data, address))
            else:
                time.sleep(0.000001)

    def __send__(self, data: bytes, dst: (str, int)):
        """
        Do not modify this function!!!
        You must send all your packet by this function!!!
        :param data: The data to be send
        :param dst: The address of the destination
        """
        self.proxy.sendto(data, dst)

    def __recv__(self, timeout=None) -> (bytes, (str, int)):
        """
        Do not modify this function!!!
        You must receive all data from this function!!!
        :param timeout: if its value has been set, it can raise a TimeoutError;
                        else it will keep waiting until receive a packet from others
        :return: a tuple x with packet data in x[0] and the source address(ip, port) in x[1]
        """
        return self.proxy.recvfrom(timeout)

    def register(self, file_path: str):
        """
        Share a file in P2P network
        :param file_path: The path to be shared, such as "./alice.txt"
        :return: fid, which is a unique identification of the shared file and can be used by other PClients to
                 download this file, such as a hash code of it
        """
        fid = None
        """
        Start your code below!
        """
        with open(file_path, 'rb') as file:
            hash = hashlib.md5()
            while True:
                data = file.read(1024)
                if not data:
                    break
                hash.update(data)
            fid = hash.hexdigest()
        self.myState.addFile(fid, file_path, os.stat(file_path).st_size)
        self.myState.peerAquireWholeFile(self.id, fid)
        self.update()
        """
        End of your code
        """
        return fid

    def download(self, fid) -> bytes:
        """
        Download a file from P2P network using its unique identification
        :param fid: the unique identification of the expected file, should be the same type of the return value of share()
        :return: the whole received file in bytes
        """
        data = None
        """
        Start your code below!
        """
        self.update()
        for c in self.myState.fileDict[fid]["chunkDict"]:
            if self.id not in self.myState.fileDict[fid]["chunkDict"][c]:
                for p in self.myState.fileDict[fid]["chunkDict"][c]:
                    if p in self.myState.peerDict.keys():
                        self.__send__(
                            torrentPacket.create_req(self.id, fid, self.myState.fileDict[fid]['filename'], c,
                                                     self.proxy.upload_rate,
                                                     self.proxy.download_rate).get_tcp_data(),
                            (str(self.myState.peerDict[p][0]), int(self.myState.peerDict[p][1])))

                        download_data, address = self.rev_pclient_queue.get()
                        data = torrentPacket.parse_tcp_data(download_data)
                        fd = open(self.myState.fileDict[fid]['filename'], "r+b")
                        fd.seek(c * torrentData.CHUNK_SIZE)
                        fd.write(data.data)
                        fd.close()

                        self.myState.peerAquireFileChunk(self.id, fid, c)

                        break

        self.update()
        """
        End of your code
        """
        return data

    def cancel(self, fid):
        """
        Stop sharing a specific file, others should be unable to get this file from this client any more
        :param fid: the unique identification of the file to be canceled register on the Tracker
        :return: You can design as your need
        """
        for c in self.myState.fileDict[fid]["chunkDict"]:
            if self.id in self.myState.fileDict[fid]["chunkDict"][c]:
                self.myState.fileDict[fid]["chunkDict"][c].remove(self.id)

        self.update()
        """
        End of your code
        """

    def close(self):
        """
        Completely stop the client, this client will be unable to share or download files any more
        :return: You can design as your need
        """
        self.__send__(
            torrentPacket.create_eot(self.id, 1).get_tcp_data(),
            self.tracker)
        """
        End of your code
        """
        self.proxy.close()

    def update(self):
        self.__send__(
            torrentPacket.create_info(self.id, self.myState, self.proxy.upload_rate,
                                      self.proxy.download_rate).get_tcp_data(),
            self.tracker)
        data, address = self.rev_tracker_queue.get()
        data = torrentPacket.parse_tcp_data(data)
        self.myState = data.info

if __name__ == '__main__':
    pass
