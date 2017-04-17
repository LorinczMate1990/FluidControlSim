#!/usr/bin/python
# -*- coding: utf-8 -*-

import SocketServer
from RequestHandler import buildRequestHandler
from DirectSyncronizedSimulatorFacade import DirectSyncronizedSimulatorFacade


class Server:
    def __init__(self, ip, port, simulator):
        self.ip = ip
        self.port = port
        self.simulator = simulator
        
    def start(self):
        RequestHandler = buildRequestHandler(self.simulator)
        self.server = SocketServer.ThreadingTCPServer((self.ip, self.port), RequestHandler)
        self.server.serve_forever()
        self.server.server_close()
        
    def stop(self):
        self.server.server_close()

if __name__ == "__main__":
    simulator = DirectSyncronizedSimulatorFacade()
    server = Server("localhost", 8883, simulator)
    server.start()
