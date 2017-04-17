#!/usr/bin/python
# -*- coding: utf-8 -*-

import json

# TODO : Ez az osztály két dolgot csinál, (ír a socket-re és olvas onnan) tehát külön kell venni két részre.
# A SocketHandler megmaradhat, mint olyan osztály, ami összefogja a SocketReader-t és a SocketWriter-t.
class SocketHandler(object):
    def __dictToPacketString(self, d):
        packetString = "#"
        packetString += json.dumps(d)
        packetString +="!"
        return packetString
        
    def __packetStringToDict(self, packetString):
        startIndex = packetString.find('#')
        endIndex = packetString.find('!')
        if startIndex == -1 or endIndex == -1:
            return {}
        packetString = packetString[startIndex+1:endIndex]
        d = json.loads(packetString)
        return d
    
    def __readNextPacketString(self):
        packetString = "#"
        actChar = ""
        while actChar != '#':
            actChar = self.socket.recv(1)
        while actChar != '!':
            actChar = self.socket.recv(1)
            packetString += actChar
        return packetString
        
    def __init__(self, socket):
        self.socket = socket

    def getNextPacket(self):
        packetString = self.__readNextPacketString()
        packetDict = self.__packetStringToDict(packetString)
        return packetDict
     
    def sendPacket(self,d):
        packetString = self.__dictToPacketString(d)
        self.socket.send(packetString)
        
    def sendPacketAndGetAnswer(self, d):
        self.sendPacket(d)
        return self.getNextPacket()
