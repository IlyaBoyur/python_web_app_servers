"""
Key feature: server sets sockets in non blocking mode (setblocking(False))
             only in event loop "sel.select(timeout=None)"
"""

import logging
import selectors
import socket
import sys

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))


def new_connection(selector: selectors.BaseSelector, sock: socket.socket) -> None:
    new_conn, address = sock.accept()
    logger.info("accepted new_conn from %s", address)
    new_conn.setblocking(False)
    selector.register(new_conn, selectors.EVENT_READ, read_callback)


def read_callback(selector: selectors.BaseSelector, sock: socket.socket) -> None:
    data = sock.recv(1024)
    if data:
        sock.send(data)
    else:
        logger.info("closing connection %s", sock)
        selector.unregister(sock)
        sock.close()


def run_iteration(selector: selectors.BaseSelector) -> None:
    events = selector.select(timeout=None)
    for key, mask in events:
        callback = key.data
        callback(selector, key.fileobj)


def serve_forever(host: str, port: int) -> None:
    """
    Метод запускает сервер на постоянное прослушивание новых сообщений.
    """
    with selectors.SelectSelector() as selector:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
            server_socket.bind((host, port))
            server_socket.listen()
            server_socket.setblocking(False)
            logger.info("Server started on port %s", port)
            selector.register(server_socket, selectors.EVENT_READ, new_connection)
            while True:
                run_iteration(selector)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <host> <port>")
        sys.exit(1)
    host, port = sys.argv[1], int(sys.argv[2])
    serve_forever(host, port)
