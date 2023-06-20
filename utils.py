import select
import socket
from socket import *
from schema import *

import time


class Log:
    def __init__(self, tag: str):
        self.tag = tag

    def log(self, level: int, message: str):
        levelStr = "INFO"
        if level == 0:
            levelStr = "INFO"
        elif level == 1:
            levelStr = "WARNING"
        elif level == 2:
            levelStr = "ERROR"
        print(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}\t{levelStr}\t[{self.tag}]: {message}")

    def i(self, message: str):
        self.log(0, message)

    def w(self, message: str):
        self.log(1, message)

    def e(self, message: str):
        self.log(2, message)


timeout_in_seconds = 0.5


def clearSocketBuffer(conn: socket):
    while True:
        ready = select.select([conn], [], [], timeout_in_seconds)
        if ready[0]:
            data = conn.recv(4)
        else:
            return


class SocketHelper:
    retransmit_count = 0

    def __init__(self, soc: socket):
        self.soc = soc
        soc.settimeout(3)

    def sendto(self, dist: tuple, resp: Response, need_response: bool = True):
        error_msg = f"No response from {dist}"
        if not need_response:
            self.soc.sendto(resp.to_json().encode(), dist)
            return
        while self.retransmit_count < 3:
            try:
                self.soc.sendto(resp.to_json().encode(), dist)
                # self.soc.setblocking(False)
                # clearSocketBuffer(self.soc)
                self.soc.setblocking(True)
                resp = Response(code=1,
                                message=self.soc.recv(1024).decode())
                return resp
            except error as e:
                error_msg = e
                self.retransmit_count = self.retransmit_count + 1
        self.retransmit_count = 0
        return Response(code=0, message=error_msg)

    def sendall(self, message: str, need_response: bool = True):
        if not need_response:
            self.soc.sendall(message)
            return
        error_msg = "No response"
        while self.retransmit_count < 3:
            try:
                self.soc.sendall(message)
                self.soc.setblocking(False)
                time.sleep(0.1)
                self.soc.setblocking(True)
                resp = json2Response(self.soc.recv(1024).decode())
                return resp
            except error as e:
                error_msg = e
                self.retransmit_count = self.retransmit_count + 1
        self.retransmit_count = 0
        return Response(code=0, message=error_msg)
