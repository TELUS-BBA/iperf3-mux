#!/usr/bin/env python3

from twisted.internet import reactor
from twisted.internet.protocol import Protocol
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol


class Iperf3MuxClient(Protocol):
    def connectionMade(self):
        self.transport.write("SENDPORT\r\n")

    def dataReceived(self, data):
        print("Data received: {}".format(data))


if __name__ == "__main__":
    endpoint = TCP4ClientEndpoint(reactor, "192.168.1.101", 10000)
    connection = connectProtocol(endpoint, Iperf3MuxClient())
