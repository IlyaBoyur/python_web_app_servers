#!/usr/bin/env python3
"""
Simplest web app server ever: it blocks everywhere - in s.accept(), conn.recv(), conn.sendall()
"""
import socket


# Standard loopback interface address (localhost)
HOST = "127.0.0.1"
# Port to listen on (non-privileged ports are > 1023)
PORT = 65432  

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept()
    with conn:
        print(f"Connected by {addr}")
        while True:
            data = conn.recv(1024)
            if not data:
                break
            conn.sendall(data)
