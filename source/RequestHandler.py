#!/usr/bin/python
# -*- coding: utf-8 -*-

import SocketServer
from SocketHandler import SocketHandler

from CommandHandler import CommandHandler


def buildRequestHandler(simulator):
    class RequestHandler(SocketServer.BaseRequestHandler):
        shutdownServer = False

        def setup(self):
            self.keepRunning = True
            self.simulator = simulator # TODO : Ez biztos, hogy azt csinálja, amit akarok?
        
        def handle(self):
            socketHandler = SocketHandler(self.request)
            commandHandler = CommandHandler(self.simulator)
            print "Új partner csatlakozott."
            
            while self.keepRunning and not RequestHandler.shutdownServer:
                nextPacket = socketHandler.getNextPacket()
                commandHandler.processPacket(nextPacket)
                action = commandHandler.getLastAction()
                response = commandHandler.getLastResponse()
                
                if response is not None:
                    socketHandler.sendPacket(response)            
                
                if action is not None:
                    if action == "QUIT":
                        self.keepRunning = False
                    elif action == "KILL":
                        self.keepRunning = False
                        RequestHandler.shutdownServer = True
                        self.server.shutdown()
                        
    return RequestHandler
