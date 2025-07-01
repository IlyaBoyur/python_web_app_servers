#!/usr/bin/env python3
"""
This web app server can handle multiple client connections at once.

Key feature: server blocks only in event loop "sel.select(timeout=None)"

The client keeps track of the number of bytes it`s received
from the server so that it can close its side of the connection.
When the server detects this, it closes its side of the connection too.

By doing this, the server depends on the client being well-behaved:
the server expects the client to close its side of the connection
when it`s done sending messages. If the client doesn`t close,
the server will leave the connection open. In a real application,
you may want to guard against this in your server by implementing
a timeout to prevent client connections from accumulating
if they don`t send a request after a certain amount of time.
"""
import sys
import socket
import selectors
import types
from selectors import SelectorKey

sel = selectors.DefaultSelector()


def accept_wrapper(sock) -> None:
    # Socket should be ready to accept
    conn, addr = sock.accept()  
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)


def service_connection(key: SelectorKey, mask: int) -> None:
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        # Socket should be ready to recieve
        recv_data = sock.recv(1024)
        if recv_data:
            data.outb += recv_data
        else:
            print(f"Closing connection to {data.addr}")
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            print(f"Echoing {data.outb!r} to {data.addr}")
            # Socket should be ready to write
            sent = sock.send(data.outb)
            data.outb = data.outb[sent:]


def serve_forever(host: str, port: int) -> None:
    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lsock.bind((host, port))
    lsock.listen()
    print(f"Listening on {(host, port)}")
    lsock.setblocking(False)
    sel.register(lsock, selectors.EVENT_READ, data=None)

    # Event Loop
    try:
        while True:
            events = sel.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    accept_wrapper(key.fileobj)
                else:
                    service_connection(key, mask)
    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting")
    finally:
        sel.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: python {__file__} <host> <port>")
        sys.exit(1)
    host, port = sys.argv[1], int(sys.argv[2])
    serve_forever(host, port)
