#!/usr/bin/env python3

import iperf3
import multiprocessing
import random
import sys
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet.protocol import Factory, ProcessProtocol
from twisted.internet.error import ProcessExitedAlready
from twisted.protocols.basic import LineOnlyReceiver
from twisted.logger import Logger, FileLogObserver, formatEventAsClassicLogText, globalLogPublisher
from twisted.internet import reactor


LOG_FILE = "log.txt"
log_file = open(LOG_FILE, "a")


class Iperf3ServerProcessProtocol(ProcessProtocol):

    def connectionMade(self):
        self.transport.closeStdin()


class Iperf3MuxServer(LineOnlyReceiver):
    """Responsible for managing two things: a single server process, and a client connection"""

    log = Logger()

    def __init__(self, factory):
        self.factory = factory
        self.server_process = None

    def connectionMade(self):
        self.factory.addConnection(self)
        self.client_host = self.transport.getPeer().host
        self.client_port = self.transport.getPeer().port
        self.log.info("{log_source.client_host}:{log_source.client_port} => connected")

    def connectionLost(self, reason):
        self.log.info("{log_source.client_host}:{log_source.client_port} => disconnected")
        self.clear_server()
        self.factory.removeConnection()
        
    def lineReceived(self, line):
        if line.decode() == "SENDPORT":
            self.log.info("{log_source.client_host}:{log_source.client_port} => SENDPORT received")
            self.clear_server()
            port = random.randrange(10001, 20001)
            self.run_server(port)
            self.sendLine(str(port).encode())
        else:
            self.log.warn(
                "{log_source.client_host}:{log_source.client_port} => invalid message {line} received",
                line=line.decode()
            )
            self.transport.loseConnection()

    def run_server(self, port):
        process = Iperf3ServerProcessProtocol()
        cmd = ["iperf3", "-s", "-p", str(port), "-1"]
        self.server_process = reactor.spawnProcess(process, cmd[0], cmd)

    def clear_server(self):
        """puts self.server_process into original state"""
        if self.server_process is not None:
            try:
                self.server_process.signalProcess('KILL')
            except ProcessExitedAlready:
                pass
            self.server_process = None


class Iperf3MuxServerFactory(Factory):

    log = Logger()
    
    def __init__(self, max_connections):
        # ensure max_connections >= 1
        self.max_connections = max_connections
        self.num_connections = 0

    def buildProtocol(self, addr):
        if self.num_connections + 1 > self.max_connections:
            self.log.error("connection rejected; server at maximum of {log_source.max_connections} connections")
            return None
        return Iperf3MuxServer(self)

    def addConnection(self, protocol):
        self.num_connections = self.num_connections + 1
        self.log.info("{log_source.num_connections} active connections")

    def removeConnection(self):
        if self.num_connections <= 0:
            self.log.error("attempted to decrement num_connections when it was already <= 0")
        else:
            self.num_connections = self.num_connections - 1
            self.log.info("{log_source.num_connections} active connections")


if __name__ == "__main__":
    log_file = sys.stdout # can be changed to whatever file descriptor you want
    globalLogPublisher.addObserver(FileLogObserver(log_file, formatEventAsClassicLogText))
    endpoint = TCP4ServerEndpoint(reactor, 10000)
    endpoint.listen(Iperf3MuxServerFactory(3))
    reactor.run()
