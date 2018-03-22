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

    def __init__(self):
        self.server_process = None

    def connectionMade(self):
        print("connectionMade")

    def connectionLost(self, reason):
        print("Connection lost")
        self.clear_server()
        
    def lineReceived(self, line):
        if line.decode() == "SENDPORT":
            print("SENDPORT received")
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
    
    def __init__(self):
        print("init method of Iperf3MuxServerFactory")

    def buildProtocol(self, addr):
        return Iperf3MuxServer()


if __name__ == "__main__":
    endpoint = TCP4ServerEndpoint(reactor, 10000)
    endpoint.listen(Iperf3MuxServerFactory())
    print("ready")
    reactor.run()
