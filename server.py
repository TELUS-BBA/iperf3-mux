#!/usr/bin/env python3

import iperf3
import multiprocessing
import random
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet.protocol import Factory, ProcessProtocol
from twisted.internet.error import ProcessExitedAlready
from twisted.protocols.basic import LineOnlyReceiver
from twisted.internet import reactor


class Iperf3ServerProcessProtocol(ProcessProtocol):

    def connectionMade(self):
        self.transport.closeStdin()


class Iperf3MuxServer(LineOnlyReceiver):
    """Responsible for managing two things: a single server process, and a client connection"""

    def __init__(self, factory):
        self.factory = factory
        self.server_process = None

    def connectionMade(self):
        self.factory.addConnection(self)
        self.client_host = self.transport.getPeer().host
        self.client_port = self.transport.getPeer().port
        print("{}:{} : connected".format(self.client_host, self.client_port))

    def connectionLost(self, reason):
        print("{}:{} : disconnected".format(self.client_host, self.client_port))
        self.clear_server()
        self.factory.removeConnection()
        
    def lineReceived(self, line):
        if line.decode() == "SENDPORT":
            print("{}:{} : SENDPORT received".format(self.client_host, self.client_port))
            self.clear_server()
            port = random.randrange(10001, 20001)
            self.run_server(port)
            self.sendLine(str(port).encode())
        else:
            print("error: invalid message {} received".format(line.decode()))
            # log error
            self.transport.loseConnection()

    def run_server(self, port):
        process = Iperf3ServerProcessProtocol()
        cmd = ["iperf3", "-s", "-p", str(port), "-1"]
        self.server_process = reactor.spawnProcess(process, cmd[0], cmd)

    def clear_server(self):
        """puts self.server_process into a known state"""
        if self.server_process is not None:
            try:
                self.server_process.signalProcess('KILL')
            except ProcessExitedAlready:
                # log error
                pass
            self.server_process = None


class Iperf3MuxServerFactory(Factory):
    
    def __init__(self, max_connections):
        # ensure max_connections >= 1
        self.max_connections = max_connections
        self.num_connections = 0

    def buildProtocol(self, addr):
        if self.num_connections + 1 > self.max_connections:
            # log this
            print("too many connections!")
            return None
        return Iperf3MuxServer(self)

    def addConnection(self, protocol):
        self.num_connections = self.num_connections + 1
        print("Factory: {} connections active".format(self.num_connections))

    def removeConnection(self):
        if self.num_connections <= 0:
            # log this, this is an error
            print("too few connections!")
            pass
        else:
            self.num_connections = self.num_connections - 1
            print("Factory: {} connections active".format(self.num_connections))


if __name__ == "__main__":
    endpoint = TCP4ServerEndpoint(reactor, 10000)
    endpoint.listen(Iperf3MuxServerFactory(3))
    reactor.run()
