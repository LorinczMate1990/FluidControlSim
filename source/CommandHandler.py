#!/usr/bin/python
# -*- coding: utf-8 -*-

from Commands import *

class CommandHandler:
    def __getSpecificPacketInstance(self, packageDict):
        packageTypes = { 
            "add_pipe": AddPipeCommand,
            "add_valve": AddValveCommand,
            "add_pump": AddPumpCommand,
            "add_container": AddContainerCommand,
            "run_next_step": RunNextStepCommand,
            "control_valve": ControlValveCommand,
            "control_pump": ControlPumpCommand,
            "get_state": GetStateCommand,
            "set_container": SetContainerStateCommand,
            "quit":QuitCommand,
            "get_id_list":GetListOfIdsCommand,
            "get_containers_list":GetContainersOfActiveElementCommand,
            "serialize":SerializeCommand,
            "deserialize":DeserializeCommand,
            "delete_object":DeleteObjectCommand,
            "set_ramping_params":SetRampingParamsCommand
        }
        if "command" in packageDict:            
            command = packageDict['command'].lower()
            packageConstructor = packageTypes.get(command, InvalidCommand)
            return packageConstructor(packageDict, self.simulator)
        else:
            return InvalidCommand("No command specified", packageDict)        
    
    def __init__(self, simulator):
        self.sendInvalidCommands = False
        self.simulator = simulator
        self.response = None
        self.action = None
        
    def processPacket(self, packetDict):
        packet = self.__getSpecificPacketInstance(packetDict)
        self.action = packet.execute()
        self.response = None
        if packet.isValid() or self.sendInvalidCommands:
            self.response = packet.generateResponse()

    def getLastAction(self):
        return self.action
    
    def getLastResponse(self):
        return self.response
