#!/usr/bin/env python3

import iperf3
from twisted.internet import reactor
from twisted.internet.protocol import Protocol
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol


class Iperf3MuxClient(Protocol):

    def __init__(self, host):
        self.test_host = host

    def connectionMade(self):
        self.transport.write("SENDPORT\r\n".encode())

    def dataReceived(self, data):
        self.test_port = int(data.decode())
        print("Port received: {}".format(self.test_port))
        try:
            result = self.run_test()
            print("Test result: {}".format(result.sent_Mbps))
            self.transport.loseConnection()
        except:
            self.transport.write("SENDPORT\r\n".encode())
            return

    def run_test(self):
        test_client = iperf3.Client()
        test_client.server_hostname = self.test_host
        test_client.port = self.test_port
        result = test_client.run()
        return result


def run_client(host, port):
    endpoint = TCP4ClientEndpoint(reactor, host, port)
    connection = connectProtocol(endpoint, Iperf3MuxClient(host))
    reactor.run()


if __name__ == "__main__":
    run_client("192.168.1.101", 10000)
