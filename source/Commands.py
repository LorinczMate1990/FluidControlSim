#!/usr/bin/python
# -*- coding: utf-8 -*-

from SimulatorFacades import GenericSimulatorFacade
from utilities import str2bool, bool2str

class Command(object):
    def __copyKeysIfOnlyFirstHas(self, dict1, dict2, keys):
        for key in keys:
            if key in dict1 and key not in dict2:
                dict2[key] = dict1[key]

    def __init__(self, packageDict, simulator):
        self.simulator = GenericSimulatorFacade(simulator)
        self.valid = True        
        self.packageDict = packageDict
        self.resp = {}
    
    def isValid(self):
        return self.valid
    
    def generateResponse(self):
        resp = self.resp
        self.__copyKeysIfOnlyFirstHas(self.packageDict, resp, ["id", "command"])
        return resp
    
    def execute(self):
        raise NotImplementedError()

class DeleteObjectCommand(Command):
    @staticmethod
    def buildDict(objectID):
        return {'command':'delete_object', 'objectid':objectID}
    
    def __init__(self, packageDict, simulator):
        super(DeleteObjectCommand, self).__init__(packageDict, simulator)
        self.id = packageDict['objectid']
    
    def execute(self):
        removedIndexes = self.simulator.deleteFluidsimObject(self.id)
        self.resp['removed'] = removedIndexes

class AddContainerCommand(Command):
    @staticmethod
    def buildDict(maxVolume, area, static):
        return {'command':'add_container', 'area':area, 'maxvolume':maxVolume, 'static':bool2str(static)}
    
    def __init__(self, packageDict, simulator):
        super(AddContainerCommand, self).__init__(packageDict, simulator)
        self.maxVolume = float(packageDict['maxvolume'])
        self.area = float(packageDict['area'])
        self.static = ('static' in packageDict) and str2bool(packageDict['static'])

    def execute(self):
        containerId = self.simulator.addContainer(self.maxVolume, self.area, self.static)
        self.resp['containerid'] = containerId

class GetStateCommand(Command):
    @staticmethod
    def buildDict(objectID):
        return {'command':'get_state', 'objectid':objectID}
    
    def __init__(self, packageDict, simulator):
        super(GetStateCommand, self).__init__(packageDict, simulator)
        self.id = packageDict['objectid']
    
    def execute(self):
        self.resp['descriptor'] = self.simulator.getFluidsimObjectDescription(self.id)

class GetListOfIdsCommand(Command):
    @staticmethod
    def buildDict():
        return {'command':'get_id_list'}
    
    def __init__(self, packageDict, simulator):
        super(GetListOfIdsCommand, self).__init__(packageDict, simulator)
    
    def execute(self):
        self.resp['idlist'] = self.simulator.getListOfIds()

class GetContainersOfActiveElementCommand(Command):
    @staticmethod
    def buildDict(activeElementID):
        return {'command':'get_containers_list', 'activeelementid':activeElementID}
    
    def __init__(self, packageDict, simulator):
        self.activeElementID = packageDict['activeelementid']
        super(GetContainersOfActiveElementCommand, self).__init__(packageDict, simulator)
    
    def execute(self):
        self.resp['containers'] = self.simulator.getContainersOfActiveElement(self.activeElementID)
        
class AddActuatorCommand(Command):
    @staticmethod
    def buildDict(actuator, ID1, ID2, length, height):
        return {'command':'add_'+actuator, 'from':ID1, 'to':ID2, 'length':length, 'height':height}

    def __init__(self, packageDict, simulator):
        super(AddActuatorCommand, self).__init__(packageDict, simulator)
        self.id1 = int(packageDict['from'])
        self.id2 = int(packageDict['to'])
        self.length = float(packageDict['length'])
        assert self.length>0, "The incoming length is zero for an actuator."
        self.height = float(packageDict['height'])
        self.parameters = None
        self.simulatorFunction = None
        
    def execute(self):
        assert isinstance(self.parameters, tuple), "self.parameters is uninitialized"
        assert isinstance(self.simulatorFunction, type(AddActuatorCommand.execute)), "self.simulatorFunction is uninitialized"
        assert self.length > 0, "Itt a baj"+str(self.parameters)
        
        try:
            actuatorId = self.simulatorFunction(self.simulator, *(self.parameters))
        except IndexError:
            self.resp['error'] = "Wrong container id"
        else:
            self.resp['actuatorid'] = actuatorId


class AddPipeCommand(AddActuatorCommand):
    @staticmethod
    def buildDict(ID1, ID2, radius, length, height):
        d = AddActuatorCommand.buildDict('pipe', ID1, ID2, length, height)
        d.update({'radius':radius})
        return d
    
    def __init__(self, packageDict, simulator):
        super(AddPipeCommand, self).__init__(packageDict, simulator)
        self.radius = float(packageDict['radius'])
        self.simulatorFunction = GenericSimulatorFacade.addPipe
        self.parameters = (self.id1, self.id2, self.radius, self.length, self.height)


class AddValveCommand(AddActuatorCommand):
    @staticmethod
    def buildDict(ID1, ID2, minRadius, maxRadius, length, height):
        d = AddActuatorCommand.buildDict('valve', ID1, ID2, length, height)
        d.update({'minradius':minRadius, 'maxradius':maxRadius})
        return d
    
    def __init__(self, packageDict, simulator):
        super(AddValveCommand, self).__init__(packageDict, simulator)
        self.minRadius = float(packageDict['minradius'])
        self.maxRadius = float(packageDict['maxradius'])
        self.simulatorFunction = GenericSimulatorFacade.addValve
        self.parameters = (self.id1, self.id2, self.minRadius, self.maxRadius, self.length, self.height)


class AddPumpCommand(AddActuatorCommand):
    @staticmethod
    def buildDict(ID1, ID2, radius, length, height, maxPressure):
        d = AddActuatorCommand.buildDict('pump', ID1, ID2, length, height)
        d.update({'maxpressure':maxPressure, 'radius':radius})
        return d
    
    def __init__(self, packageDict, simulator):
        super(AddPumpCommand, self).__init__(packageDict, simulator)
        self.radius = float(packageDict['radius'])
        self.maxPressure = float(packageDict['maxpressure'])
        self.simulatorFunction = GenericSimulatorFacade.addPump
        self.parameters = (self.id1, self.id2, self.radius, self.length, self.height, self.maxPressure)
        

class ActuatorCommand(Command):
    ACTION_MAP = {}

    @staticmethod
    def buildDict(actuatorId, actuator, action, percentpoint):
        return {'command':'control_'+actuator, 'actuatorid':actuatorId, 'action':action, 'percentpoint':percentpoint}

    def __init__(self, packetDict, defaultAction, simulator):
        super(ActuatorCommand, self).__init__(packetDict, simulator)
        self.defaultAction = defaultAction
        
        self.actuatorId = int(packetDict['actuatorid'])
        if "action" in packetDict:
            self.action = packetDict["action"]
        else:
            self.action = defaultAction
        self.percentPoint = packetDict["percentpoint"]
    
    def execute(self):
        if self.action in self.ACTION_MAP:
            try:
                self.ACTION_MAP[self.action](self.simulator, self.actuatorId, self.percentPoint)
            except IndexError:
                self.resp['error'] = "Wrong actuator id"
        else:
            self.resp['error'] = "Given '"+self.action+"' is invalid action. Possible actions are: "+str(ACTION_MAP.keys())


class ControlValveCommand(ActuatorCommand):
    OPEN_ACTION = "open"
    CLOSE_ACTION = "close"
    SET_ACTION = "set"
    ACTION_MAP = {OPEN_ACTION: GenericSimulatorFacade.openValve,
                  CLOSE_ACTION: GenericSimulatorFacade.closeValve,
                  SET_ACTION: GenericSimulatorFacade.setValveState}

    @staticmethod
    def buildDict(actuatorId, action, percentpoint):
        return ActuatorCommand.buildDict(actuatorId, 'valve', action, percentpoint)

    def __init__(self, packageDict, simulator):
        super(ControlValveCommand, self).__init__(packageDict, ControlValveCommand.SET_ACTION, simulator)

class ControlPumpCommand(ActuatorCommand):
    INC_ACTION = "inc"
    DEC_ACTION = "dec"
    SET_ACTION = "set"
    ACTION_MAP = {INC_ACTION: GenericSimulatorFacade.incPumpPerformance,
                  DEC_ACTION: GenericSimulatorFacade.decPumpPerformance,
                  SET_ACTION: GenericSimulatorFacade.setPumpPerformance}

    @staticmethod
    def buildDict(actuatorId, action, percentpoint):
        return ActuatorCommand.buildDict(actuatorId, 'pump', action, percentpoint)

    def __init__(self, packageDict, simulator):
        super(ControlPumpCommand, self).__init__(packageDict, ControlPumpCommand.SET_ACTION, simulator)

class RunNextStepCommand(Command):
    @staticmethod
    def buildDict(delta, repeat):
        return {'command':'run_next_step', 'delta':delta, 'repeat':repeat}

    def __init__(self, packageDict, simulator):
        super(RunNextStepCommand, self).__init__(packageDict, simulator)
        self.delta = float(packageDict['delta'])
        self.repeat = int(packageDict['repeat']) if 'repeat' in packageDict else 1
        
    def execute(self):
        self.simulator.run(self.delta, self.repeat)

class SetContainerStateCommand(Command):
    @staticmethod
    def buildDict(containerId, temperature, level):
        return {'command':'set_container', 'containerid':containerId, 'temperature':temperature, 'level':level}
    
    def __init__(self, packageDict, simulator):
        super(SetContainerStateCommand, self).__init__(packageDict, simulator)
        self.containerID = packageDict['containerid']
        self.temperature = packageDict['temperature']
        self.level = packageDict['level']

    def execute(self):
        self.simulator.setContainerState(self.containerID, self.temperature, self.level)

class SetRampingParamsCommand(Command):
    @staticmethod
    def buildDict(rampingId, params):
        return {'command':'set_ramping_params', 'rampingid':rampingId, 'params':params}
    
    def __init__(self, packageDict, simulator):
        super(SetContainerStateCommand, self).__init__(packageDict, simulator)
        self.rampingId = packageDict['rampingid']
        self.params = packageDict['params']

    def execute(self):
        self.simulator.setRampingParams(self.rampingId, self.params)

class QuitCommand(Command):
    @staticmethod
    def buildDict(forAll):
        return {'command':'quit', 'global':bool2str(forAll)}
    
    def __init__(self, packageDict, simulator):
        super(QuitCommand, self).__init__(packageDict, simulator)
        self.globalAction = ('global' in packageDict) and str2bool(packageDict['global'])
    
    def execute(self):
        if self.globalAction:
            return "KILL"
        else:
            return "QUIT"

class SerializeCommand(Command):
    @staticmethod
    def buildDict():
        return {'command':'serialize'}
        
    def __init__(self, packageDict, simulator):
        super(SerializeCommand, self).__init__(packageDict, simulator)
    
    def execute(self):
        resp['serial'] = self.simulator.serialize()
        
class DeserializeCommand(Command):
    @staticmethod
    def buildDict(serial):
        return {'command':'deserialize', 'serial':serial}
        
    def __init__(self, packageDict, simulator):
        super(SerializeCommand, self).__init__(packageDict, simulator)
    
    def execute(self):
        self.simulator.deserialize(packageDict['serial'])
        
        

class InvalidCommand(Command):
    def __initByExplicitProblem(self, problem, packageDict):
        self.problem = problem    
        self.packageDict = packageDict        

    def __initByDefaultProblem(self, packageDict):
        self.problem = "Invalid command"
        self.packageDict = packageDict
            
    def __init__(self, problemOrPackageDict, defaultDict={}):
        if isinstance(problemOrPackageDict, dict):
            self.__initByDefaultProblem(problemOrPackageDict)
        elif isinstance(problemOrPackageDict, str):
            self.__initByExplicitProblem(problemOrPackageDict, defaultDict)
        else:
            raise Exception()  # I have no idea, how can I go at this point
        self.resp = {"command": "invalid", "problem": self.problem}
        self.valid = False
            
    def execute(self):
        print self.problem


