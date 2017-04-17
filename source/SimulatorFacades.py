#!/usr/bin/python
# -*- coding: utf-8 -*-

class SimulationObjectData:
    def __init__(self, simulator):
        self.genericSimulator = GenericSimulatorFacade(simulator)
        
    def _selectSimulatorAddMethod(self, func):
        self.func = func
        
    def tuple(self):
        pass
    
    def loadToSimulator(self):
        self.func(self.genericSimulator, *self.tuple())

class ContainerData(SimulationObjectData):
    def __init__(self, simulator):
        SimulationObjectData.__init__(self, simulator)
        self.maxWaterLevel = None
        self.area = None
        self.baseHeight = None # TODO : Ez jelenleg nincs figyelembe véve
        self.staticContainer = None
        self._selectSimulatorAddMethod(GenericSimulatorFacade.addContainer)
    
    def tuple(self):
        return (self.maxWaterLevel, self.area, self.staticContainer)

class ActiveElementData(SimulationObjectData):
    def __init__(self, simulator):
        SimulationObjectData.__init__(self, simulator)
        self.ID1 = None
        self.ID2 = None
        self.length = None
        self.height = None
    
class PipeData(ActiveElementData):
    def __init__(self, simulator):
        ActiveElementData.__init__(self, simulator)
        self.radius = None
        self._selectSimulatorAddMethod(GenericSimulatorFacade.addPipe)
    
    def tuple(self):
        return (self.ID1, self.ID2, self.radius, self.length, self.height)
        
class PumpData(PipeData):
    def __init__(self, simulator):
        PipeData.__init__(self, simulator)
        self.maxPressure = None
        self._selectSimulatorAddMethod(GenericSimulatorFacade.addPump)
        
    def tuple(self):    
        return (self.ID1, self.ID2, self.radius, self.length, self.height, self.maxPressure,)
        
class ValveData(ActiveElementData):
    def __init__(self, simulator):
        ActiveElementData.__init__(self, simulator)
        self.minRadius = None
        self.maxRadius = None
        self._selectSimulatorAddMethod(GenericSimulatorFacade.addValve)
    
    def tuple(self):
        return (self.ID1, self.ID2, self.minRadius, self.maxRadius, self.length, self.height)

class AbstractSimulatorFacade(object):
    """ This is the parent of all Simulator facades. It only defines the functions. """
    def addContainer(self, maxWaterLevel, area, static): raise NotImplementedError()
    def addPipe(self, ID1, ID2, radius, length, height): raise NotImplementedError()
    def addValve(self, ID1, ID2, minRadius, maxRadius, length, height): raise NotImplementedError()
    def addPump(self, ID1, ID2, radius, length, height, maxPressure): raise NotImplementedError()
    def setValveState(self, activeElementID, percent): raise NotImplementedError()
    def openValve(self, activeElementID, percentPoint): raise NotImplementedError()
    def closeValve(self, activeElementID, percentPoint): raise NotImplementedError()
    def setPumpPerformance(self, activeElementID, percent): raise NotImplementedError()
    def incPumpPerformance(self, activeElementID, percentPoint): raise NotImplementedError()
    def decPumpPerformance(self, activeElementID, percentPoint): raise NotImplementedError()
    def getFluidsimObjectDescription(self, objectID): raise NotImplementedError()
    def setContainerState(self, containerID, fluidTemperature, fluidLevel): raise NotImplementedError()
    def run(self, deltaT, repeat=1): raise NotImplementedError()
    def getListOfIds(self): raise NotImplementedError()
    def getContainersOfActiveElement(self, activeElementId): raise NotImplementedError()
    def serialize(self): raise NotImplementedError()
    def deserialize(self, serial): raise NotImplementedError()
    def deleteFluidsimObject(self, objectID): raise NotImplementedError()
    def setRampingParams(self, objectID, rampParams): raise NotImplementedError()

class GenericSimulatorFacade(AbstractSimulatorFacade):
    """
    This is a generic simulator facade.
    It can use other simulator facades.
    It can used by objects which need some basic knowledge about the structure
    of the simulator facades but they will get the concrete object from somewhere else.
    """
    def __init__(self, simulatorImplementation):
        self.sim = simulatorImplementation

    def addContainer(self, maxWaterLevel, area, static):
        return self.sim.addContainer(maxWaterLevel, area, static)
        
    def addPipe(self, ID1, ID2, radius, length, height):
        return self.sim.addPipe(ID1, ID2, radius, length, height)
    
    def addValve(self, ID1, ID2, minRadius, maxRadius, length, height):
        return self.sim.addValve(ID1, ID2, minRadius, maxRadius, length, height)
    
    def addPump(self, ID1, ID2, radius, length, height, maxPressure):
        return self.sim.addPump(ID1, ID2, radius, length, height, maxPressure)
        
    def setValveState(self, activeElementID, percent):
        return self.sim.setValveState(activeElementID, percent)
    
    def openValve(self, activeElementID, percentPoint):
        return self.sim.openValve(activeElementID, percentPoint)
    
    def closeValve(self, activeElementID, percentPoint):
        return self.sim.closeValve(activeElementID, percentPoint)
    
    def setPumpPerformance(self, activeElementID, percent):
        return self.sim.setPumpPerformance(activeElementID, percent)
    
    def incPumpPerformance(self, activeElementID, percentPoint):
        return self.sim.incPumpPerformance(activeElementID, percentPoint)
    
    def decPumpPerformance(self, activeElementID, percentPoint):
        return self.sim.decPumpPerformance(self, activeElementID, percentPoint)
    
    def getFluidsimObjectDescription(self, objectID):
        return self.sim.getFluidsimObjectDescription(objectID)
    
    def setContainerState(self, containerID, fluidTemperature, fluidLevel):
        return self.sim.setContainerState(containerID, fluidTemperature, fluidLevel)
    
    def run(self, deltaT, repeat=1):
        return self.sim.run(deltaT, repeat)

    def getListOfIds(self):
        return self.sim.getListOfIds()
        
    def getContainersOfActiveElement(self, activeElementId):
        return self.sim.getContainersOfActiveElement(activeElementId)
        
    def serialize(self):
        return self.sim.serialize()
        
    def deserialize(self, serial):
        return self.sim.deserialize(serial)
        
    def deleteFluidsimObject(self, objectID):
        return self.sim.deleteFluidsimObject(objectID)
        
    def setRampingParams(self, objectID, rampParams):
        return self.sim.setRampingParams(objectID, rampParams)    
