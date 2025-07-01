#!/usr/bin/env python3
import logging
import selectors
import socket
import sys

import libserver

sel = selectors.DefaultSelector()
logger = logging.getLogger(__name__)


def new_connection(selector: selectors.BaseSelector, sock: socket.socket) -> None:
    # Should be ready to read
    new_conn, address = sock.accept()
    logger.info("accepted new connection from %s", address)
    new_conn.setblocking(False)
    message = libserver.Message(selector, new_conn, address)
    selector.register(new_conn, selectors.EVENT_READ, data=message)


def run_iteration(selector: selectors.BaseSelector) -> None:
    """Прочитать текущие события и обработать."""
    events = selector.select(timeout=None)
    
    for key, mask in events:
        if key.data is None:
            new_connection(selector, key.fileobj)
        else:
            message = key.data
            try:
                message.process_events(mask)
            except Exception:
                logger.exception(f"Exception for {message.addr}")
                message.close()
    

def serve_forever(host: str, port: int) -> None:
    """
    Запустить сервер на постоянное прослушивание новых сообщений.
    """
    try:
        with selectors.SelectSelector() as selector:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
                # Avoid bind() exception: "OSError: [Errno 48] Address already in use"
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
                server_socket.bind((host, port))
                server_socket.listen()
                server_socket.setblocking(False)
                logger.info("Server started on port %s", port)
                selector.register(server_socket, selectors.EVENT_READ, data=None)
                while True:
                    run_iteration(selector)
    except KeyboardInterrupt:
        logger.info("Caught keyboard interrupt, exiting")
    finally:
        selector.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <host> <port>")
        sys.exit(1)
    host, port = sys.argv[1], int(sys.argv[2])
    serve_forever(host, port)