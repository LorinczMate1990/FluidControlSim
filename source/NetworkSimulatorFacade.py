#!/usr/bin/python
# -*- coding: utf-8 -*-

from Commands import *

from SocketHandler import SocketHandler
from SimulatorFacades import AbstractSimulatorFacade

class NetworkSimulatorFacade(AbstractSimulatorFacade):
    def __init__(self, socket):
        self.socketHandler = SocketHandler(socket)

    def __sendPacketWithReturn(self, returnLabel, commandClass, argsOfBuildDict):
        packet = commandClass.buildDict(*argsOfBuildDict)
        response = self.socketHandler.sendPacketAndGetAnswer(packet)
        if returnLabel is not None:
            return response[returnLabel]
        
    def __sendPacket(self, commandClass, argsOfBuildDict):
        self.__sendPacketWithReturn(None, commandClass, argsOfBuildDict)

    def addContainer(self, maxWaterLevel, area, static):
        containerId = self.__sendPacketWithReturn('containerid', AddContainerCommand, (maxWaterLevel, area, static))
        return containerId

    def addPipe(self, ID1, ID2, radius, length, height):
        return self.__sendPacketWithReturn('actuatorid', AddPipeCommand, (ID1, ID2, radius, length, height))
    
    def addValve(self, ID1, ID2, minRadius, maxRadius, length, height):
        return self.__sendPacketWithReturn('actuatorid', AddValveCommand, (ID1, ID2, minRadius, maxRadius, length, height))
    
    def addPump(self, ID1, ID2, radius, length, height, maxPressure):
        return self.__sendPacketWithReturn('actuatorid', AddPumpCommand, (ID1, ID2, radius, length, height, maxPressure))
    
    def setValveState(self, actuatorId, percent):
        self.__sendPacket(ControlValveCommand, (actuatorId, ControlValveCommand.SET_ACTION, percent))
    
    def openValve(self, actuatorId, percentPoint):
        self.__sendPacket(ControlValveCommand, (actuatorId, ControlValveCommand.OPEN_ACTION, percentPoint))
    
    def closeValve(self, actuatorId, percentPoint):
        self.__sendPacket(ControlValveCommand, (actuatorId, ControlValveCommand.CLOSE_ACTION, percentPoint))
    
    def setPumpPerformance(self, actuatorId, percent):
        self.__sendPacket(ControlPumpCommand, (actuatorId, ControlPumpCommand.SET_ACTION, percent))

    def incPumpPerformance(self, actuatorId, percentPoint):
        self.__sendPacket(ControlPumpCommand, (actuatorId, ControlPumpCommand.INC_ACTION, percentPoint))
    
    def decPumpPerformance(self, actuatorId, percentPoint):
        self.__sendPacket(ControlPumpCommand, (actuatorId, ControlPumpCommand.DEC_ACTION, percentPoint))

    def getFluidsimObjectDescription(self, objectID):
        return self.__sendPacketWithReturn('descriptor', GetStateCommand, (objectID,))

    def setContainerState(self, containerID, fluidTemperature, fluidLevel):
        self.__sendPacket(SetContainerStateCommand, (containerID, fluidTemperature, fluidLevel))

    def run(self, deltaT, repeat=1):
        self.__sendPacket(RunNextStepCommand, (deltaT, repeat))
    
    def getListOfIds(self):
        return self.__sendPacketWithReturn('idlist', GetListOfIdsCommand, ())
        
    def getContainersOfActiveElement(self, activeElementID):
        return self.__sendPacketWithReturn('containers', GetContainersOfActiveElementCommand, (activeElementID,))
    
    def deleteFluidsimObject(self, objectID):
        return self.__sendPacketWithReturn('removed', DeleteObjectCommand, (objectID,))

    def setRampingParams(self, objectID, rampParams):
        self.__sendPacket(SetRampingParamsCommand, (rampParams,))
    
    def serialize(self): raise NotImplementedError()
    
    def deserialize(self, serial): raise NotImplementedError()
    
