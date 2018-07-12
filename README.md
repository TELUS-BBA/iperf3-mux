# iperf3-mux

iperf3 servers do not support multiple simultaneous tests.
I have solved this problem by wrapping it in some python scripts that
manage multiple iperf3 servers as subprocesses.
It is a hack, but it works.
A typical test looks like:

1.  The main server listens on a fixed TCP port defined by the constant `SERVER_PORT` in `server.py`.

1.  A client connects to this port (the "management connection") 
    and uses it to send a UTF-8 formatted message "SENDPORT\r\n".

1.  Upon receiving this message (and only this message) the server picks a random
    port between `IPERF3_SERVER_PORT_MIN` and `IPERF3_SERVER_PORT_MAX` inclusive
    and starts an iperf3 server subprocess that occupies the port.

1.  The server sends the port back to the client over the management connection,
    encoded once again as UTF-8.

1.  The client can now use that port to perform an iperf3 test as usual.

Important Notes:

- The client must maintain the management connection for the duration of the test -
  when this connection is broken the server assumes that the client is done with the test
  and kills the iperf3 server subprocess.

- Each iperf3 server is good for only one test.
  If you want to perform multiple tests you must make a management connection
  and send "SENDPORT\r\n" etc. once for each test.

- If any exceptions occur on the server side then the server closes the connection.

- In the rare case that the port the server randomly chooses is occupied,
  the server might still send out that port.
  In this case an exception will be raised on the client side -
  it is up to the client to recognize this
  and close the connection. See `example_client.py` for example code.

- A limit must be placed on the maximum number of iperf3 server subprocesses,
  since test results can be affected if the server's network connection
  is not fast enough to serve all of the connected clients.
  For example, if I have a server with a 10 Gbit/s uplink and my clients are
  capable of 1 Gbit/s, I should set my `IPERF3_MAX_CONCURRENT_TESTS` to 9
  (10 is max capability, subtract one to be safe).

- Since it was a pain to get a systemd service for this running,
  I've included a file that works (at least, for me) - see iperf3-server.service.


## Installation

You need `iperf3` and the python's `twisted`.
