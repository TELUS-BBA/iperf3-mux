#!/usr/bin/env python3

import iperf3
import threading
import random
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineOnlyReceiver
from twisted.internet import reactor


class Iperf3MuxServer(LineOnlyReceiver):

    def __init__(self, factory):
        self.factory = factory
        self.server_thread = None
        self.server_port = None

    def connectionMade(self):
        pass

    def connectionLost(self, reason):
        if (self.server_port is not None) or (self.server_thread is not None):
            self.stop_server()
        
    def lineReceived(self, line):
        if self.server_port is None:
            if line == "SENDPORT":
                self.server_port = random.randrange(10001, 20001)
                self.run_server(self.server_port)
                self.sendLine(self.server_port)
            else:
                pass
                # log error
                self.transport.loseConnection()
        else:
            if line == "SENDPORT":
                self.stop_server()
                self.server_port = random.randrange(10001, 20001)
                self.run_server(self.server_port)
                self.sendLine(self.server_port)
            else:
                pass
                # log error
                self.transport.loseConnection()

    def run_server(self, port):
        server = iperf3.Server()
        server.bind_address = '0.0.0.0'
        server.port = port
        self.server_thread = threading.Thread(target=server.run, args=[])
        self.server_thread.start()

    def stop_server(self):
        if self.server_thread is not None:
            if self.server_thread.is_alive():
                self.server_thread.join()
            self.server_thread = None
        if self.server_port is not None:
            self.server_port = None


if __name__ == "__main__":
    endpoint = TCP4ServerEndpoint(reactor, 10000)
    endpoint.listen(Factory.forProtocol(Iperf3MuxServer))
    #reactor.listenTCP(10000, Factory.forProtocol(Iperf3MuxServer))
    reactor.run()
