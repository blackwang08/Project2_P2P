from torrentPacket import torrentPacket
from Proxy import Proxy
from torrentData import torrentData

ID_COUNT = 1
netState = torrentData()


class Tracker:
    def __init__(self, upload_rate=10000, download_rate=10000, port=None):
        self.proxy = Proxy(upload_rate, download_rate, port)

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

    def start(self):
        global ID_COUNT
        while True:
            msg, frm = self.__recv__()
            msg = msg.decode()
            pkt = torrentPacket.parse_tcp_data(msg)

            if pkt.type == 0:
                if pkt.id == -1:
                    netState.addPeer(ID_COUNT, frm[0], frm[1])
                    for f in pkt.info.fileDict.keys():
                        netState.addFile(f, pkt.info.fileDict[f]["filesize"])
                        netState.peerAquireWholeFile(ID_COUNT, f)
                    pkt.id = ID_COUNT
                    ID_COUNT = ID_COUNT + 1
                else:
                    for f in pkt.info.fileDict.keys():
                        netState.addFile(f, pkt.info.fileDict[f]["filesize"])

                self.proxy.socket.sendall(torrentPacket.create_info(pkt.id, netState).get_tcp_data())
            elif pkt.type == 1:
                netState.removePeer(pkt.id)

    def response(self, data: str, address: (str, int)):
        self.__send__(data.encode(), address)


if __name__ == '__main__':
    tracker = Tracker(port=10086)
    tracker.start()
