#!/usr/bin/python
# -*- coding: utf-8 -*-

# http://effbot.org/tkinterbook/grid.htm

import Tkinter as tk
import socket
import itertools
from threading import Thread
import pickle
import collections
import ast
import sys

from utilities import *
from NetworkSimulatorFacade import NetworkSimulatorFacade
from DirectSyncronizedSimulatorFacade import DirectSyncronizedSimulatorFacade
from SimulatorFacades import *

import fluidsim_server

# Graph

class MessageWindow(tk.Toplevel):
    def __init__(self, parent, text):
        tk.Toplevel.__init__(self, parent)
        tk.Label(self, text=text).grid(row=0, column=0, pady=2)
        tk.Button(self, text="Ok", command=self.destroy).grid(row=1, column=0, pady=2)

class EntryList(object):
    def __init__(self, graphContainer, listOfKeyLabelPairs, firstRow=1):
        self.entries = {}
        
        for row, (key, text) in enumerate(listOfKeyLabelPairs):
            entry = tk.Entry(graphContainer)
            self.entries[key] = entry
            entry.grid(row=firstRow+row, column=1)
            tk.Label(graphContainer, text=text).grid(row=firstRow+row, column=0, sticky=tk.W, pady=2)
    
    def getEntryList(self):
        return self.entries.keys()
    
    def __getitem__(self, key):
        if key in self.entries:
            return self.entries[key].get()
        else:
            raise AttributeError()

    def __setitem__(self, key, val):
        if key in self.entries:
            self.entries[key].delete(0, tk.END)
            self.entries[key].insert(0, val)
        else:
            raise AttributeError()

class DataEntry(object):
    def __init__(self, simulator):
        self.simulator = simulator
    
    def uploadToSimulator(self, data):
        raise NotImplementedError()
    
    def saveData(self):
        try:
            data = self.generateData()
        except ValueError:
            MessageWindow(self, "Wrong formatted values")
        else:
            self.uploadToSimulator(data)
            self.destroy()
        
    def generateData(self):
        raise NotImplementedError()

class OptionsWindow(tk.Toplevel, DataEntry):
    def __init__(self, parent, objectID, simulator):
        tk.Toplevel.__init__(self, parent)
        DataEntry.__init__(self, simulator)
        self.objectID = objectID
        tk.Label(self, text="ID: "+str(objectID)).grid(row=0, column=0, columnspan=2, pady=2)
        self.entries = EntryList(self, self.getEntriesDescriptor())
        tk.Button(self, text="Save", command=self.saveData).grid(row=10, column=0, columnspan=2, pady=2)
        self.downloadFromSimulator()
    
    def downloadFromSimulator(self):
        descriptor = self.simulator.getFluidsimObjectDescription(self.objectID)
        for key in self.entries.getEntryList():
            self.entries[key]=str(descriptor[key])

    def getEntriesDescriptor(self):
        raise NotImplementedError()
            
    def uploadToSimulator(self, data):
        raise NotImplementedError()
        
    def generateData(self):
        raise NotImplementedError()
    

class ContainerOptionsWindow(OptionsWindow):
    def __init__(self, parent, objectID, simulator):
        OptionsWindow.__init__(self, parent, objectID, simulator)
    
    def getEntriesDescriptor(self):
        return [('waterlevel', 'Water level: '), ('temperature', 'Water temperature: ')]
    
    def uploadToSimulator(self, data):
        self.simulator.setContainerState(self.objectID, *data)
        
    def generateData(self):
        return (float(self.entries['temperature']), float(self.entries['waterlevel']))

class ValveOptionsWindow(OptionsWindow):
    def __init__(self, parent, objectID, simulator):
        OptionsWindow.__init__(self, parent, objectID, simulator)
    
    def getEntriesDescriptor(self):
        return [('minradius', "Minimum radius: "), ('maxradius', "Minimum radius: "), ('permeability', 'Permeability (%): '), ('rampparams', 'Ramping parameters: ')]
    
    def uploadToSimulator(self, data):
        permeability = data[0]
        rampParams = data[1]    
        self.simulator.setValveState(self.objectID, permeability)
        self.simulator.setRampingParams(self.objectID, rampParams)
        
    def generateData(self):
        rampparams = ast.literal_eval(self.entries['rampparams'])
        return [float(self.entries['permeability']), rampparams]
        
class PumpOptionsWindow(OptionsWindow):
    def __init__(self, parent, objectID, simulator):
        OptionsWindow.__init__(self, parent, objectID, simulator)
    
    def getEntriesDescriptor(self):
        return [('maxpressure', 'Maximum pressure: '), ('performance', 'Performance (+/- %): '), ('rampparams', 'Ramping parameters: ')]
    
    def uploadToSimulator(self, data):
        performance = data[0]
        rampParams = data[1]
        self.simulator.setPumpPerformance(self.objectID, performance)
        self.simulator.setRampingParams(self.objectID, rampParams)
        
    def generateData(self):
        rampparams = ast.literal_eval(self.entries['rampparams'])
        return [float(self.entries['performance']), rampparams]
        


class AddContainerWindow(tk.Toplevel, DataEntry):
    def uploadToSimulator(self, data):
        data.loadToSimulator()

    def __init__(self, parent, simulator):
        tk.Toplevel.__init__(self, parent)
        DataEntry.__init__(self, simulator)

        self.wm_title("Adding a new container")

        self.staticContainercBool = tk.BooleanVar()
        staticContainerCheckbutton = tk.Checkbutton(self, text="Static container", variable=self.staticContainercBool, onvalue=True, offvalue=False)
        
        entriesDescriptor = [('maxWaterLevel', 'Max. water level: '), ('area', 'Area: '), ('baseHeight', 'Baseheight: ')]
        self.entries = EntryList(self, entriesDescriptor)
        
        staticContainerCheckbutton.grid(row=4, column=1, columnspan=2, sticky=tk.W, pady=2)
        
        tk.Button(self, text="Save", command=self.saveData).grid(row=5, column=0, columnspan=2, pady=2)
   
    def generateData(self):
        container = ContainerData(self.simulator)
        container.maxWaterLevel = float(self.entries['maxWaterLevel'])
        container.area = float(self.entries['area'])            
        container.baseHeight = float(self.entries['baseHeight'])
        container.staticContainer = self.staticContainercBool.get()
        return container

class AddActiveElementWindow(tk.Toplevel, DataEntry):
    def uploadToSimulator(self, data):
        data.loadToSimulator()

    def __init__(self, parent, mainWindow, simulator, rowOfSaveButton):
        tk.Toplevel.__init__(self, parent)
        DataEntry.__init__(self, simulator)
        self.mainWindow = mainWindow
        self.simulator = simulator

        self.mainWindow.prepareForActiveElementCreation()
        
        self.wm_title("Adding a new pipe")

        self.fromIdLabel = tk.Label(self)
        self.toIdLabel = tk.Label(self)
        self.saveButton = tk.Button(self, text="Save", command=self.saveData, state=tk.DISABLED)
        
        tk.Label(self, text="From: ").grid(row=0, column=0, sticky=tk.W, pady=2)
        tk.Label(self, text="To: ").grid(row=1, column=0, sticky=tk.W, pady=2)
        tk.Button(self, text="Refresh", command=self.refreshFromAndToId).grid(row=2, column=0, columnspan=2, pady=2)
        
        self.fromIdLabel.grid(row=0, column=1)
        self.toIdLabel.grid(row=1, column=1)
        self.saveButton.grid(row=rowOfSaveButton, column=1, columnspan=2, pady=2)
        
    def refreshFromAndToId(self):
        selectedObjects = self.mainWindow.getSelectedObjectsOnScene()
        if len(selectedObjects) != 2:
            MessageWindow(self, "Please select two objects!")
        else:
            fromObject = selectedObjects[0]
            toObject = selectedObjects[1]
            self.fromID = fromObject.getID()
            self.toID = toObject.getID()
            
            self.fromIdLabel.config(text=str(self.fromID))
            self.toIdLabel.config(text=str(self.toID))
            self.saveButton.config(state=tk.NORMAL)
        
class AddPipeWindow(AddActiveElementWindow):
    def __init__(self, parent, mainWindow, simulator):
        AddActiveElementWindow.__init__(self, parent, mainWindow, simulator, 6)
        entriesDescriptor = [('length', 'Length: '), ('height', 'Height: '), ('radius', 'Radius: ')]
        self.entries = EntryList(self, entriesDescriptor, 3)
    
    def generateData(self):
        pipe = PipeData(self.simulator)
        pipe.radius = float(self.entries['radius'])
        pipe.length = float(self.entries['length'])            
        pipe.height = float(self.entries['height'])
        pipe.ID1 = self.fromID
        pipe.ID2 = self.toID
        return pipe
                
class AddPumpWindow(AddActiveElementWindow):
    def __init__(self, parent, mainWindow, simulator):
        AddActiveElementWindow.__init__(self, parent, mainWindow, simulator, 7)
        entriesDescriptor = [('length', 'Length: '), ('height', 'Height: '), ('radius', 'Radius: '), ('maxPressure', 'Max pressure: ')]
        self.entries = EntryList(self, entriesDescriptor, 3)
       
    def generateData(self):
        pump = PumpData(self.simulator)
        pump.maxPressure = float(self.entries['maxPressure'])
        pump.radius = float(self.entries['radius'])
        pump.length = float(self.entries['length'])            
        pump.height = float(self.entries['height'])
        pump.ID1 = self.fromID
        pump.ID2 = self.toID
        return pump

class AddValveWindow(AddActiveElementWindow):
    def __init__(self, parent, mainWindow, simulator):
        AddActiveElementWindow.__init__(self, parent, mainWindow, simulator, 7)
        entriesDescriptor = [('length', 'Length: '), ('height', 'Height: '), ('minRadius', 'Min radius: '), ('maxRadius', 'Max radius: ')]
        self.entries = EntryList(self, entriesDescriptor, 3)
       
    def generateData(self):
        valve = ValveData(self.simulator)
        valve.minRadius = float(self.entries['minRadius'])
        valve.maxRadius = float(self.entries['maxRadius'])
        valve.length = float(self.entries['length'])            
        valve.height = float(self.entries['height'])
        valve.ID1 = self.fromID
        valve.ID2 = self.toID
        return valve




















class DragTracking(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def mouseInNewPos(self, x, y):
        dX = x-self.x
        dY = y-self.y
        self.x = x
        self.y = y
        return (dX, dY)

class Selectable:
    def select(self):
        self.__isSelected = True
        self.onSelect()
        
    def unselect(self):
        self.__isSelected = False
        self.onUnselect()
        
    def isSelected(self):
        try:
            return self.__isSelected
        except AttributeError:
            return False

    def onSelect(self):
        pass
    
    def onUnselect(self):
        pass

class Selector:
    def __init__(self):
        self.maxSelection = 1
        self.selectList = []
    
    def __throwOldest(self):
        unselected = self.selectList.pop(0)
        unselected.unselect()        
    
    def setSelectionNumber(self, n):
        while n<len(self.selectList):
            self.__throwOldest() 
        self.maxSelection = n
    
    def __removeFromList(self, val):
        self.selectList.remove(val)
        val.unselect()
        
    def __addToList(self, val):
        self.selectList.append(val)
        val.select()
        if len(self.selectList)>self.maxSelection:
            self.__throwOldest()
    
    def select(self, val):
        if val in self.selectList:
            self.__removeFromList(val)
        else:
            self.__addToList(val)

    def unselectAll(self):
        for i in range(0,len(self.selectList)):
            self.__throwOldest()

    def getSelection(self):
        return [i for i in self.selectList]

class EventListenerInterface:
    def notify(self, event):
        raise NotImplementedError()    

class Event(object):
    def __init__(self):
        self.eventListeners = set()
    
    def subscribe(self, listener):
        self.eventListeners.add(listener)
    
    def notify(self):
        for listener in self.eventListeners:
            listener.notify(self)

class SimulationObject(object):
    def __init__(self, ID, simulator):
        self.ID = ID
        self.simulator = simulator
    
    def getID(self):
        return self.ID
    
    def getDataFromSimulator(self):
        descriptor = self.simulator.getFluidsimObjectDescription(self.ID)
        self.parseDescriptor(descriptor)
        
    def parseDescriptor(self, descriptor):
        raise NotImplementedError()

class GraphSimulationObject(SimulationObject, Selectable):
    tagCounter = 1
    @staticmethod
    def generateTagGroup():
        DragableGraphSimulationObject.tagCounter+=1
        return "DRAGGROUP"+str(DragableGraphSimulationObject.tagCounter)

    def __init__(self, ID, simulationScene, simulator):
        SimulationObject.__init__(self, ID, simulator)
        self.tagGroup = GraphSimulationObject.generateTagGroup()  
        self.simulationScene = simulationScene
        self.canvas = simulationScene.getCanvas()
        self.redrawEvent = Event()
    
    def subscribeForRedrawing(self, listener):
        self.redrawEvent.subscribe(listener)

    def draw(self):
        self.generateGraph()
        self.canvas.tag_bind(self.tagGroup, "<Double-Button-1>", self.b1DoubleClick)
        self.canvas.tag_bind(self.tagGroup, "<Triple-Button-1>", self.b1TripleClick)
        self.canvas.tag_bind(self.tagGroup, "<Button-1>", self.b1MouseDown)
        self.canvas.tag_bind(self.tagGroup, "<B1-Motion>", self.b1MouseMove)
        self.redrawEvent.notify()

    def b1TripleClick(self, event):
        pass

    def b1DoubleClick(self, event):
        self.openOptions()
        
    def b1MouseMove(self, event):
        dX, dY = self.dragTracking.mouseInNewPos(event.x, event.y)
        self.drag(dX, dY)
        
    def b1MouseDown(self, event):
        self.dragTracking = DragTracking(event.x, event.y)
        self.simulationScene.selectObject(self)
        
    def generateGraph(self):
        raise NotImplementedError()
    
    def openOptions(self):
        raise NotImplementedError()
        
    def drag(self, dX, dY):
        pass
        
    def invalidateGraph(self):
        self.refreshDrawing()
        self.redrawEvent.notify()        
                
    def refreshDrawing(self):
        raise NotImplementedError()                

class DragableGraphSimulationObject(GraphSimulationObject):
    def __init__(self, *args):
        GraphSimulationObject.__init__(self, *args)
        self.x = 0
        self.y = 0

    def getPos(self):
        return (self.x, self.y)
        
    def setPos(self, pos):
        self.x, self.y = pos

    def drag(self, dX, dY):
        self.x += dX
        self.y += dY
        self.invalidateGraph()

class ContainerObject(DragableGraphSimulationObject):
    minTemperature = 0
    maxTemperature = 100
    containerReferenceAreaFor100PixelWidth = 100.0
    containerReferenceMaxLevelFor100PixelHeight = 100.0

    @staticmethod
    def thisObject(descriptor):
        return descriptor['type']=='container'
    
    def __init__(self, *args):
        DragableGraphSimulationObject.__init__(self, *args)
        self.positionModificationEvent = Event()
        self.minWidth = 100
        self.minHeight = 150
        self.width = self.minWidth
        self.height = self.minHeight
        self.pad = 10
        
    def subscribeForPositionModification(self, obj):
        self.positionModificationEvent.subscribe(obj)
    
    def parseDescriptor(self, descriptor):    
        self.maxVolume = descriptor['maxvolume']
        self.baseLine = descriptor['baseline']
        self.temperature = descriptor['temperature']
        self.volume = descriptor['volume']
        self.maxWaterLevel = descriptor['maxwaterlevel']
        self.waterLevel = descriptor['waterlevel']
        self.rho = descriptor['rho']
        self.eta = descriptor['eta']
        self.area = descriptor['area']

    def __getFullness(self):
        return limit(self.waterLevel / self.maxWaterLevel, 0.0, 1.0)

    def __getFluidColor(self):
        low = ContainerObject.minTemperature
        high = ContainerObject.maxTemperature
        temperature = limit(self.temperature, low, high)
        
        redComponent = rescale(temperature, ContainerObject.minTemperature, ContainerObject.maxTemperature, 0, 255)
        blueComponent = rescale(temperature, ContainerObject.minTemperature, ContainerObject.maxTemperature, 255, 0)
        redComponent, blueComponent = int(redComponent), int(blueComponent)
        
        fluidColor = '#%02x%02x%02x' % (redComponent, 0, blueComponent)
        return fluidColor

    def __getContainerUpperRectangle(self):
        return (self.x, self.y, self.width+self.x, (1-self.__getFullness())*self.height+self.y)        
    
    def __getContainerLowerRectangle(self):
        return (self.x, (1-self.__getFullness())*self.height+self.y, self.width+self.x, self.height+self.y)

    def __getCenter(self):
        return (self.x+self.width/2, self.y+self.height/2)

    def getJointPoint(self):
        return self.__getCenter()

    def __getTextPosition(self):
        return (self.x+self.pad/2, self.y+self.pad/2)
        
    def __generateContainerCaption(self):
        text = "ID: {:d}\n".format(self.ID)
        text += "\n"
        text += "Vol.: {:0.2f}\n".format(self.volume)
        text += "Temp.: {:0.2f}\n".format(self.temperature)
        text += "\n"
        text += "Act. level: {:0.2f}\n".format(self.waterLevel)
        text += "Max. level: {:0.2f}".format(self.maxWaterLevel)
        return text
        
    def __refreshWidthAndHeight(self, textId):
        self.width = int(self.area / ContainerObject.containerReferenceAreaFor100PixelWidth * 100)
        self.height = int(self.maxWaterLevel / ContainerObject.containerReferenceMaxLevelFor100PixelHeight * 100)
    
    def generateGraph(self):
        self.textId = self.canvas.create_text(self.__getTextPosition(), text=self.__generateContainerCaption(), tags=self.tagGroup, anchor=tk.NW)
        self.__refreshWidthAndHeight(self.textId)
        outlineColor = 'red' if self.isSelected() else 'black'
        
        self.lowerRectangleId = self.canvas.create_rectangle(self.__getContainerLowerRectangle(), tags=self.tagGroup, fill=self.__getFluidColor(), outline=outlineColor)
        self.upperRectangleId = self.canvas.create_rectangle(self.__getContainerUpperRectangle(), tags=self.tagGroup, fill="SpringGreen4", outline=outlineColor)
        
        self.canvas.tag_raise(self.textId)
        
    def refreshDrawing(self):
        self.canvas.coords(self.lowerRectangleId, self.__getContainerLowerRectangle())
        self.canvas.coords(self.upperRectangleId, self.__getContainerUpperRectangle())        
        self.canvas.coords(self.textId, self.__getTextPosition())
        self.positionModificationEvent.notify()
    
    def onSelect(self):
        self.canvas.itemconfig(self.lowerRectangleId, outline='red') 
        self.canvas.itemconfig(self.upperRectangleId, outline='red') 
        
    def onUnselect(self):
        self.canvas.itemconfig(self.lowerRectangleId, outline='black')
        self.canvas.itemconfig(self.upperRectangleId, outline='black')
    
    def openOptions(self):
        ContainerOptionsWindow(self.simulationScene, self.ID, self.simulator)
    
class PipeObject(GraphSimulationObject, EventListenerInterface):
    @staticmethod
    def thisObject(descriptor):
        return descriptor['type']=='activeElement' and descriptor['subtype']=='pipe' 
    
    def __init__(self, *args):
        GraphSimulationObject.__init__(self, *args)
    
    def getDataFromSimulator(self):
        fromID, toID = self.simulator.getContainersOfActiveElement(self.ID)
        
        self.fromContainer = self.simulationScene.getObjectByID(fromID)
        self.fromContainer.subscribeForPositionModification(self)
        
        self.toContainer = self.simulationScene.getObjectByID(toID)
        self.toContainer.subscribeForPositionModification(self)
        
        GraphSimulationObject.getDataFromSimulator(self)
        
    def parseDescriptor(self, descriptor):
        self.radius = descriptor['radius']
        self.length = descriptor['length']
        self.height = descriptor['height']
        self.stream = descriptor['stream']
    
    def __getLinePoints(self):
        return self.fromContainer.getJointPoint() + self.toContainer.getJointPoint()
    
    def _getEndPoints(self):
        return self.fromContainer.getJointPoint(), self.toContainer.getJointPoint()
    
    def _getPipeCenter(self):
        start, end = self._getEndPoints()
        x = (start[0]+end[0])/2
        y = (start[1]+end[1])/2
        
        return (x, y)

    def generateGraph(self):
        self.line = self.canvas.create_line(*self.__getLinePoints(), width=5, tags=self.tagGroup, fill="SpringGreen4")

    def refreshDrawing(self):
        self.canvas.coords(self.line, self.__getLinePoints())

    def notify(self, e):
        self.refreshDrawing()
        
    def openOptions(self):
        print "Option window of a pipe opened"

    def _transformPointsIntoCenterOfPipe(self, points):
        alpha = calculateElevationInRadian(*self._getEndPoints())
        points = rotate(points, alpha)
        points = translate(points, (self._getPipeCenter()))
        return tuple(itertools.chain(*points))

class PumpObject(PipeObject):
    @staticmethod
    def thisObject(descriptor):
        return descriptor['type']=='activeElement' and descriptor['subtype']=='pump' 
    
    def __init__(self, *args):
        PipeObject.__init__(self, *args)
        self.r = 15

    def __getPumpSymbol(self):
        points = [(0, self.r), (self.r, 0), (0, -self.r)]
        return self._transformPointsIntoCenterOfPipe(points)
    
    def __getCircleBoundingBox(self):
        topLeftCorner = [i-self.r for i in self._getPipeCenter()]
        bottomRightCorner = [i+self.r for i in self._getPipeCenter()]
        return tuple(topLeftCorner + bottomRightCorner)    
    
    def __generateCaption(self):
        text = "{:0.0f}\n".format(self.performance)
        text += "{:0.0f}".format(self.setpoint)
        return text
        
    def __getTextPosition(self):
        center = self._getPipeCenter()
        return (center[0], center[1])
    
    def parseDescriptor(self, descriptor):
        PipeObject.parseDescriptor(self, descriptor)
        self.maxPressure = descriptor['maxpressure']
        self.performance = descriptor['performance']
        self.setpoint = descriptor['setpoint']
    
    def __getSymbolColor(self):
        if self.performance > 0.1:
            return "green"
        else:
            return "red"    
    
    def generateGraph(self):
        PipeObject.generateGraph(self)
        cX, cY = self._getPipeCenter()
        self.circle = self.canvas.create_oval(self.__getCircleBoundingBox(), fill="gray", tags=self.tagGroup)
        self.polygon = self.canvas.create_polygon(self.__getPumpSymbol(), tags=self.tagGroup, fill=self.__getSymbolColor())
        self.textId = self.canvas.create_text(self.__getTextPosition(), text=self.__generateCaption(), tags=self.tagGroup, anchor=tk.CENTER)

    def refreshDrawing(self):
        PipeObject.refreshDrawing(self)
        self.canvas.coords(self.circle, self.__getCircleBoundingBox())
        self.canvas.coords(self.polygon, self.__getPumpSymbol())
        self.canvas.coords(self.textId, self.__getTextPosition())
        
    def openOptions(self):
        PumpOptionsWindow(self.simulationScene, self.ID, self.simulator)

class ValveObject(PipeObject):
    @staticmethod
    def thisObject(descriptor):
        return descriptor['type']=='activeElement' and descriptor['subtype']=='valve' 
    
    def __init__(self, *args):
        PipeObject.__init__(self, *args)
        
    def parseDescriptor(self, descriptor):
        PipeObject.parseDescriptor(self, descriptor)
        self.minRadius = descriptor['minradius']
        self.maxRadius = descriptor['maxradius']
        self.permeability = descriptor['permeability']
        self.setpoint = descriptor['setpoint']
        
    def __getValveSymbol(self):
        x = 15
        y = 10
        points = [(-x, -y), (+x, +y), (+x, -y), (-x, +y)]
        return self._transformPointsIntoCenterOfPipe(points)
    
    def __getSymbolColor(self):
        if self.permeability > 0.1:
            return 'green'
        else:
            return 'red'

    def __generateCaption(self):
        text = "{:0.0f}\n".format(self.permeability)
        text += "{:0.0f}".format(self.setpoint)
        return text
        
    def __getTextPosition(self):
        center = self._getPipeCenter()
        return (center[0], center[1])
    
    def generateGraph(self):
        PipeObject.generateGraph(self)
        self.polygon = self.canvas.create_polygon(self.__getValveSymbol(), tags=self.tagGroup, fill=self.__getSymbolColor())
        self.textId = self.canvas.create_text(self.__getTextPosition(), text=self.__generateCaption(), tags=self.tagGroup, anchor=tk.CENTER)

    def refreshDrawing(self):
        PipeObject.refreshDrawing(self)
        self.canvas.coords(self.polygon, self.__getValveSymbol())
        self.canvas.coords(self.textId, self.__getTextPosition())

    def openOptions(self):
        ValveOptionsWindow(self.simulationScene, self.ID, self.simulator)

def SimulationObjectFactory(ID, simulationScene, simulator):
    possibleObjectTypes = [PipeObject, PumpObject, ValveObject, ContainerObject]
    descriptor = simulator.getFluidsimObjectDescription(ID)
    for objectType in possibleObjectTypes:
        if objectType.thisObject(descriptor):
            return objectType(ID, simulationScene, simulator)
    # TODO: Maybe, I should raise an Exception because I couldn't identify the descriptor 

class SimulationScene(tk.Frame):
    def __init__(self, simulator, root):
        tk.Frame.__init__(self, root)
        self.simulator = simulator
        self.objects = {}
        self.canvas = tk.Canvas(self, width=500, height=500)
        self.canvas.pack()
        self.objectSelector = Selector()
    
    def __dropObjectByID(self, objectID):
        self.objects.pop(objectID, False)
    
    def dropObjectsByID(self, objectIDs):
        if isinstance(objectIDs, collections.Iterable):
            for ID in objectIDs:
                self.__dropObjectByID(ID)
        else:
            self.__dropObjectByID(objectIDs)
        self.objectSelector.unselectAll()
    
    def getCanvas(self):
        return self.canvas
        
    def getObjectByID(self, ID):
        return self.objects[ID]
        
    def getContainersPos(self):
        posDict = {obj.ID:obj.getPos() for obj in self.objects.values() if isinstance(obj, ContainerObject)}
        return posDict
    
    def setContainersPos(self, posDict):
        self.refresh()
        for ID, pos in posDict.iteritems():
            if ID in self.objects:
                self.objects[ID].setPos(pos)
        self.draw()
            
    def selectObject(self, simulationObject):
        self.objectSelector.select(simulationObject)
    
    def getSelectedObjects(self):
        return self.objectSelector.getSelection()
        
    def setMaximumNumberOfSelectedObjects(self, n):
        self.objectSelector.setSelectionNumber(n)
                
    def refresh(self):
        # TODO: It can't remove objects. This is true for the whole simulation
        idList = self.simulator.getListOfIds()
        for ID in idList:
            if ID not in self.objects:
                simulationObject = SimulationObjectFactory(ID, self, self.simulator)
                self.objects[ID]=simulationObject
        for simulationObject in self.objects.values():
            simulationObject.getDataFromSimulator()
        self.draw() # TODO : It would be enough to draw only the new objects
            
    def draw(self):
        self.canvas.delete("all")
        for simulationObject in self.objects.values():
            simulationObject.draw()

class TopMenu(tk.Frame):
    def __init__(self, simulator, root):
        tk.Frame.__init__(self, root)
        self.simulator = simulator
        self.root = root
        addPipeButton = tk.Button(self, text="New pipe", command=self.addPipe)
        addValveButton = tk.Button(self, text="New valve", command=self.addValve)
        addPumpButton = tk.Button(self, text="New pump", command=self.addPump)
        addContainerButton = tk.Button(self, text="New container", command=self.addContainer)
        deleteSelectedItemButton = tk.Button(self, text="Delete item", command=self.deleteSelectedItem)
        refreshButton = tk.Button(self, text="Refresh", command=root.refreshSimulation)
        saveButton = tk.Button(self, text="Save", command=root.save)
        loadButton = tk.Button(self, text="Load", command=root.load)

        self.simulateBool = tk.BooleanVar()
        simulateCheckbutton = tk.Checkbutton(self, text="Simulation", variable=self.simulateBool, onvalue=True, offvalue=False)
        
        self.refreshBool = tk.BooleanVar()
        refreshCheckbutton = tk.Checkbutton(self, text="Refresh", variable=self.refreshBool, onvalue=True, offvalue=False)
        
        addPipeButton.grid(row=0, column=0)
        addValveButton.grid(row=0, column=1)
        addPumpButton.grid(row=0, column=2)
        addContainerButton.grid(row=0, column=3)
        deleteSelectedItemButton.grid(row=0, column=4)
        refreshButton.grid(row=0, column=5)
        simulateCheckbutton.grid(row=0, column=6)
        refreshCheckbutton.grid(row=0, column=7)
        saveButton.grid(row=0, column=8)
        loadButton.grid(row=0, column=9)
    
    def deleteSelectedItem(self):
        selectedObjects = self.root.getSelectedObjectsOnScene()
        selectedIDs = [selectedObject.ID for selectedObject in selectedObjects]
        for ID in selectedIDs:
            removedIDs = simulator.deleteFluidsimObject(ID)
            self.root.dropObjectsByIDOnScene(removedIDs)
    
    def addPipe(self):
        AddPipeWindow(self, self.root, self.simulator)
        
    def addValve(self):
        AddValveWindow(self, self.root, self.simulator)
        
    def addPump(self):
        AddPumpWindow(self, self.root, self.simulator)
        
    def addContainer(self):
        AddContainerWindow(self, self.simulator)
        
    def isSimulationOn(self):
        return self.simulateBool.get()
    
    def isRefreshOn(self):
        return self.refreshBool.get()
        
class MainWindow(tk.Frame):
    def __init__(self, simulator, root):
        tk.Frame.__init__(self, root)
        self.root = root
        self.simulator = simulator
        self.topMenu = TopMenu(simulator, self)
        self.topMenu.grid(row=0, column=0)
        self.simulationScene = SimulationScene(simulator, self)
        self.simulationScene.grid(row=1, column=0)
    
    def getSelectedObjectsOnScene(self):
        return self.simulationScene.getSelectedObjects()
    
    def dropObjectsByIDOnScene(self, objectIDs):
        self.simulationScene.dropObjectsByID(objectIDs)
    
    def prepareForActiveElementCreation(self):
        self.simulationScene.setMaximumNumberOfSelectedObjects(2)
    
    def save(self):
        cont={'simulator':self.simulator.serialize(), 'simulationScene':self.simulationScene.getContainersPos()}
        with open('dump.txt', 'w') as f:
            pickle.dump(cont, f)
        
    def load(self):
        with open('dump.txt', 'r') as f:
            cont = pickle.load(f)
        self.simulator.deserialize(cont['simulator'])
        self.simulationScene.setContainersPos(cont['simulationScene'])
    
    def refreshSimulation(self):
        if self.topMenu.isSimulationOn():
            self.simulator.run(0.01, 25)
        if self.topMenu.isRefreshOn() or self.topMenu.isSimulationOn():
            self.root.after(250, self.refreshSimulation)
        self.simulationScene.refresh()

if __name__ == "__main__":
    autoLoad = False

    if len(sys.argv) > 1:
        autoLoad = (sys.argv[1] == "load")
            
    root = tk.Tk()
    simulator = DirectSyncronizedSimulatorFacade()
    server = fluidsim_server.Server("localhost", 8883, simulator)
    main = MainWindow(simulator, root)
    if autoLoad:
        main.load()
        
    main.pack(side="top", fill="both", expand=True)
    serverThread = Thread(target=server.start)
    serverThread.start()
    root.mainloop()
    server.stop()
