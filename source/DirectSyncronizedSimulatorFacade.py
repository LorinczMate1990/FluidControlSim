#!/usr/bin/python
# -*- coding: utf-8 -*-

import threading
import dill # For pickling lambda functions.
import pickle 

from SimulatorFacades import AbstractSimulatorFacade
from utilities import syncronize 
from fluidsim_core import *

class DirectSyncronizedSimulatorFacade(AbstractSimulatorFacade):
    """
    The interface for the simulation
    The Simulator object has a method for every possibly function in the simulation
    This fallows the "Facade pattern". 
    """
    
    def __isActiveElementID(self, ID):
        return ID % 2 == 0
    
    def __i2ae(self, index):  # This converts an index to an Active Element ID
        return index*2
    
    def __ae2i(self, ID):
        return int(ID)/2  # This converts an Active Element ID to index
        
    def __i2c(self, index):  # This converts an index to Container ID
        return index*2+1
    
    def __c2i(self, ID):  # This converts a container ID to index
        return int(ID)/2
    
    def __getObject(self, ID):
        ID = int(ID)
        if self.__isActiveElementID(ID):
            return self.activeElements[ID/2]
        else:
            return self.containers[ID/2]

    def __getFirstFreeIndex(self, array):
        try:
            return array.index(None)
        except ValueError:
            newIndex = len(array)
            array.append(None)
            return newIndex
    
    def __getFirstFreeContainerIndex(self):
        return self.__getFirstFreeIndex(self.containers)

    def __getFirstFreeActiveElementIndex(self):
        return self.__getFirstFreeIndex(self.activeElements)

    def serialize(self):
        return pickle.dumps(self.pickablePart)
        
    def deserialize(self, serial):
        self.pickablePart = pickle.loads(serial)
        self.containers = self.pickablePart['containers']
        self.activeElements = self.pickablePart['activeElements']
    
    def __init__(self):
        self.containers = []
        self.activeElements = []
        self.pickablePart = {'containers':self.containers, 'activeElements':self.activeElements}
        self.lock = threading.RLock()
        self.logManager = LogManager([FileLogHandler])
        self.simulationTime = 0
    
    def __newActiveElement(self, element):
        index = self.activeElements.push_back(element)
        return self.__i2ae(index)
    
    @syncronize
    def addContainer(self, maxWaterLevel, area, static):
        pressureCalculator = StandardPressureCalculator(area, maxWaterLevel)
        index = self.__getFirstFreeContainerIndex()
        
        if static:
            container = Container(pressureCalculator, StaticFluid(0,0))
        else:
            container = Container(pressureCalculator)
        self.containers[index] = container
        self.logManager.monitor(self.__i2c(index), container)
        return self.__i2c(index)

    def __addActiveElement(self, ID1, ID2, element):
        index = self.__getFirstFreeActiveElementIndex()
        cont1 = self.__getObject(ID1)
        cont2 = self.__getObject(ID2)        
        cont1.attachPipe(element)
        cont2.attachPipe(element)
        self.activeElements[index] = element
        self.logManager.monitor(str(self.__i2ae(index))+"_"+str(ID1)+"-"+str(ID2), element)    
        return self.__i2ae(index)
    
    @syncronize
    def addPipe(self, ID1, ID2, radius, length, height):
        pipe = Pipe(radius, length, height)
        return self.__addActiveElement(ID1, ID2, pipe)
    
    @syncronize   
    def addValve(self, ID1, ID2, minRadius, maxRadius, length, height):
        valve = Valve(minRadius, maxRadius, length, height)
        return self.__addActiveElement(ID1, ID2, valve)
    
    @syncronize
    def addPump(self, ID1, ID2, radius, length, height, maxPressure):
        pump = Pump(radius, length, height, maxPressure)
        return self.__addActiveElement(ID1, ID2, pump)
    
    @syncronize
    def setValveState(self, activeElementID, percent):
        valve = self.__getObject(activeElementID)
        valve.setPermeability(percent)
    
    @syncronize
    def openValve(self, activeElementID, percentPoint):
        valve = self.__getObject(activeElementID)
        valve.open(percentPoint)
    
    @syncronize
    def closeValve(self, activeElementID, percentPoint):
        valve = self.__getObject(activeElementID)
        valve.close(percentPoint)
    
    @syncronize
    def setPumpPerformance(self, activeElementID, percent):
        pump = self.__getObject(activeElementID)
        pump.setPerformance(percent)

    @syncronize
    def incPumpPerformance(self, activeElementID, percentPoint):
        pump = self.__getObject(activeElemendID)
        pump.increasePerformance(percent)    
    
    @syncronize
    def decPumpPerformance(self, activeElementID, percentPoint):
        pump = self.__getObject(activeElemendID)
        pump.decreasePerformance(percent)    

    @syncronize    
    def getFluidsimObjectDescription(self, objectID):
        obj = self.__getObject(objectID)
        return obj.getDescription()

    @syncronize    
    def setContainerState(self, containerID, fluidTemperature, fluidLevel):
        container = self.__getObject(containerID)
        container.fluid.setTemperature(fluidTemperature)
        container.setLevel(fluidLevel)
    
    @syncronize    
    def run(self, deltaT, repeat=1):
        for i in range(0, repeat):
            for element in self.activeElements:
                element.flow(deltaT)
            self.simulationTime+=deltaT
            self.logManager.createLog(self.simulationTime)

    @syncronize    
    def getListOfIds(self):
        listOfActiveElementsId = [self.__i2ae(index) for index in range(0,len(self.activeElements)) if self.activeElements[index] is not None]
        listOfContainersId = [self.__i2c(index) for index in range(0,len(self.containers)) if self.containers[index] is not None]
        return listOfActiveElementsId + listOfContainersId
        
    @syncronize
    def getContainersOfActiveElement(self, activeElementID):
        index = self.__ae2i(activeElementID)
        activeElement = self.activeElements[index]
        a = activeElement.getContainer1()
        b = activeElement.getContainer2()
        indexOfA = self.containers.index(a)
        indexOfB = self.containers.index(b)
        idOfA = self.__i2c(indexOfA)
        idOfB = self.__i2c(indexOfB)
        return [idOfA, idOfB]
    
    @syncronize
    def deleteFluidsimObject(self, objectID):
        obj = self.__getObject(objectID)
        if self.__isActiveElementID(objectID):
            obj.destroy()
            self.activeElements[self.__ae2i(objectID)] = None
            return [objectID]
        else:
            affectedPipes = obj.destroy()
            self.containers[self.__c2i(objectID)] = None
            affectedPipeIDs = []
            for pipe in affectedPipes:
                pipe.destroy()
                pipeIndex = self.activeElements.index(pipe)
                affectedPipeIDs.append(self.__i2ae(pipeIndex))
                self.activeElements[pipeIndex] = None
            return [objectID] + affectedPipeIDs
            
    @syncronize
    def setRampingParams(self, objectID, rampParams):
        rampableId = self.__getObject(objectID)
        rampableId.ramp.setParams(rampParams)
