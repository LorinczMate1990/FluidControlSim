#!/usr/bin/python
# -*- coding: utf-8 -*-

import fluidsim_server
from NetworkSimulatorFacade import NetworkSimulatorFacade
from DirectSyncronizedSimulatorFacade import DirectSyncronizedSimulatorFacade
import thread
import random
from socket import socket
import time
import itertools
import sys

def checkWaterLevelsAndTemperatures():
    global idCont1_1Description, idCont1_2Description, idCont2Description, idCont3Description, idCont4Description

    print "Check water levels and temperatures before simulation"
    idCont1_1Description = simulator.getFluidsimObjectDescription(idCont1_1)
    print "  --- Description of", idCont1_1, ": ", idCont1_1Description
    idCont1_2Description = simulator.getFluidsimObjectDescription(idCont1_2)
    print "  --- Description of", idCont1_2, ": ", idCont1_2Description
    idCont2Description = simulator.getFluidsimObjectDescription(idCont2)
    print "  --- Description of", idCont2, ": ", idCont2Description
    idCont3Description = simulator.getFluidsimObjectDescription(idCont3)
    print "  --- Description of", idCont3, ": ", idCont3Description
    idCont4Description = simulator.getFluidsimObjectDescription(idCont4)
    print "  --- Description of", idCont4, ": ", idCont4Description

def equalList(a,b):
    return set(a).intersection(b) == set(a) == set(b)

port = random.randint(8000,10000)
testViaServer = False


passedOnTest = True

maxWaterVolume = 5000
startingWaterVolume = 5000
baseArea = 100.0
startingWaterTemperatureH = 30
startingWaterTemperatureL = 0

serverStarted = False

both = (False, True)
false = (False,)
true = (True,)
def generateTestCases(testingServerClient, testStaticScenarios):
    return itertools.product(testingServerClient, testStaticScenarios)

serverStarted = False
listOfIds = []

for testViaServer, testWithStaticContainers in generateTestCases(true, both):
    if testViaServer:
        if not serverStarted:
            listOfIds = []
            print "Starting server..."
            thread.start_new_thread( fluidsim_server.serverLife, ('localhost', port))
            time.sleep(0.1)
            print "Server started"
            serverStarted = True
        print ""
        print ""
        print "Creating and connecting with socket"
        s = socket()
        s.connect(("localhost", port))
        time.sleep(0.1)
        print "Connected"
        print ""
        print ""
        print "Creating NetworkSimulatorFacade"
        simulator = NetworkSimulatorFacade(s)
    else:
        print "Creating DirectSyncronizedSimulatorFacade()"
        listOfIds = []
        simulator = DirectSyncronizedSimulatorFacade() 

    print "Creating containers"
    maxWaterLevel = float(maxWaterVolume)/baseArea
    idCont1_1 = simulator.addContainer(maxWaterLevel, baseArea, testWithStaticContainers)
    idCont1_2 = simulator.addContainer(maxWaterLevel, baseArea, testWithStaticContainers)

    idCont2 = simulator.addContainer(maxWaterLevel, baseArea, False)
    idCont3 = simulator.addContainer(maxWaterLevel, 10, False)
    idCont4 = simulator.addContainer(maxWaterLevel, 10, False)
    print "  --- IDs : ", idCont1_1, idCont1_2, idCont2, idCont3, idCont4
    listOfIds=listOfIds+[idCont1_1, idCont1_2, idCont2, idCont3, idCont4]        

    print "Setting water level"
    simulator.setContainerState(idCont1_1, 30, startingWaterVolume/baseArea)
    simulator.setContainerState(idCont1_2, 0, startingWaterVolume/baseArea)
    simulator.setContainerState(idCont4, 30, 0)

    print "Creating pipes"
    pipe1 = simulator.addPipe(idCont1_1, idCont2, 0.05, 5, 0)
    pipe2 = simulator.addPipe(idCont1_2, idCont2, 0.1, 5, 0)

    print "Creating valve"
    valve1 = simulator.addValve(idCont2, idCont3, 0, 0.5, 5, 0)
    print "Set valve"
    simulator.setValveState(valve1, 0)

    print "Add pump"
    pump1 = simulator.addPump(idCont3, idCont4, 0.1, 5, 0, 0.5)
    
    print ""
    print ""
    print ""
    print "Testing neighbour queries"
    pipe1Con = simulator.getContainersOfActiveElement(pipe1)
    pipe2Con = simulator.getContainersOfActiveElement(pipe2)
    valve1Con = simulator.getContainersOfActiveElement(valve1)
    pump1Con = simulator.getContainersOfActiveElement(pump1)            
    
    connectionRequestIsCorrect = equalList(pipe1Con, [idCont1_1, idCont2]) and \
                                 equalList(pipe2Con, [idCont1_2, idCont2]) and \
                                 equalList(valve1Con, [idCont2, idCont3]) and \
                                 equalList(pump1Con, [idCont3, idCont4])

    assert connectionRequestIsCorrect, "The requested connections are wrong."

    listOfIds=listOfIds+[pipe1, pipe2, valve1, pump1]

    checkWaterLevelsAndTemperatures()

    assert idCont1_1Description['temperature'] == startingWaterTemperatureH, "First container water level"
    assert idCont1_2Description['temperature'] == startingWaterTemperatureL, "Sec first container water level"
    assert idCont1_1Description['volume'] == startingWaterVolume, "First container water volume ("+str(startingWaterVolume * baseArea)+")"
    assert idCont1_2Description['volume'] == startingWaterVolume, "Sec first container water volume ("+str(startingWaterVolume * baseArea)+")"
    assert idCont2Description['volume'] == 0, "Sec container volume is not zero"
    assert idCont3Description['volume'] == 0, "3th container volume is not zero"
    assert idCont4Description['volume'] == 0, "4th container volume is not zero"
        
    print ""
    print ""
    print ""

    print "Starting dynamic testing. Simulate 10 sec simulation time"

    simulator.run(0.01, 1000)

    print ""
    print ""
    print ""
    
    checkWaterLevelsAndTemperatures()

    if testWithStaticContainers:
        assert idCont1_1Description['volume'] == startingWaterVolume, "The 1st static container lost water."
        assert idCont1_2Description['volume'] == startingWaterVolume, "The 2nd static container lost water."
        
        assert idCont2Description['volume'] != 0, "Sec container volume is zero"
        assert idCont3Description['volume'] == 0, "3th container volume is not zero"
        assert idCont4Description['volume'] == 0, "4th container volume is not zero"
        assert idCont2Description['temperature'] > startingWaterTemperatureL and idCont2Description['temperature'] < startingWaterTemperatureH, "The common temperature is impossible."
        print "System with nonstatic containers is correct"
    else:
        assert idCont1_1Description['volume'] > idCont1_2Description['volume'], "Sec container has more water than first"
        assert abs(idCont1_1Description['volume'] + idCont1_2Description['volume'] + idCont2Description['volume'] - 2*startingWaterVolume) < 0.00001, "The amount of water changed on the system: "+str(idCont1_1Description['volume'] + idCont1_2Description['volume'] + idCont2Description['volume'] - 2*startingWaterVolume)
        assert idCont2Description['volume'] != 0, "Sec container volume is zero"
        assert idCont3Description['volume'] == 0, "3th container volume is not zero"
        assert idCont4Description['volume'] == 0, "4th container volume is not zero"
        assert idCont2Description['temperature'] > startingWaterTemperatureL and idCont2Description['temperature'] < startingWaterTemperatureH, "The common temperature is impossible."
        print "System with nonstatic containers is correct"

    print ""
    print ""
    print ""
    print "Opening the valve"
    
    simulator.setValveState(valve1, 100)
    print "Simulating 2 minutes"    
    simulator.run(0.01, 12000)
    print "Simulation completed"
    checkWaterLevelsAndTemperatures()
    
    assert idCont3Description['volume'] != 0, "3th container volume is still zero"
    assert idCont4Description['volume'] != 0, "4th container volume is still zero" 
    assert idCont3Description['volume'] > idCont4Description['volume'], "4th container has more fluid than 3th."
    
    sumOfWaterAfterTheValve = idCont3Description['volume'] + idCont4Description['volume']
    print "Closing valve"
    simulator.setValveState(valve1, 0)    
    
    print "Simulating 2 minutes"    
    simulator.run(0.01, 12000)
    print "Simulation completed"
    
    checkWaterLevelsAndTemperatures()

    assert abs(idCont3Description['volume'] + idCont4Description['volume'] - sumOfWaterAfterTheValve)<0.0000001, "Water changed after valve closed. Error: "+str(abs(idCont3Description['volume'] + idCont4Description['volume'] - sumOfWaterAfterTheValve))
    
    print ""
    print ""
    print ""
    print "Testing for 20 minutes"
    simulator.run(0.1, 12000)
    print "Simulation completed"
    checkWaterLevelsAndTemperatures()
    assert abs(idCont3Description['volume'] - idCont4Description['volume'])<0.1, "Water level didn't equalized"

    print ""
    print ""
    print ""
    print "Testing for 20 minutes"
    simulator.run(0.1, 12000)
    print "Simulation completed"
    checkWaterLevelsAndTemperatures()
    assert abs(idCont3Description['volume'] - idCont4Description['volume'])<0.1, "Water level didn't equalized"
    
    print "Turn pump on."
    simulator.setPumpPerformance(pump1, 100)
    
    print ""
    print ""
    print ""
    print "Testing for 20 minutes"
    simulator.run(0.1, 12000)
    print "Simulation completed"
    checkWaterLevelsAndTemperatures()
    assert idCont3Description['volume']-idCont4Description['volume']<-0.4, "Pump doesn't work"
    
    assert idCont3Description['volume']-idCont4Description['volume']>-0.6, "Pump is too strong"

    print ""
    print ""
    print ""
    print "Testing for 10 minutes"
    simulator.run(0.1, 6000)
    print "Simulation completed"
    checkWaterLevelsAndTemperatures()
    assert idCont3Description['volume']-idCont4Description['volume']<-0.4, "Pump doesn't work"
    assert idCont3Description['volume']-idCont4Description['volume']>-0.6, "Pump is too strong"

    print "Invert pump on."
    simulator.setPumpPerformance(pump1, -100)
    
    print ""
    print ""
    print ""
    print "Testing for 20 minutes"
    simulator.run(0.1, 12000)
    print "Simulation completed"
    checkWaterLevelsAndTemperatures()
    assert idCont3Description['volume']-idCont4Description['volume']>0.4, "Pump doesn't work"
    
    assert idCont3Description['volume']-idCont4Description['volume']<0.6, "Pump is too strong"

    print ""
    print ""
    print ""
    print "Testing for 10 minutes"
    simulator.run(0.1, 6000)
    print "Simulation completed"
    checkWaterLevelsAndTemperatures()
    assert idCont3Description['volume']-idCont4Description['volume']>0.4, "Pump doesn't work"
    assert idCont3Description['volume']-idCont4Description['volume']<0.6, "Pump is too strong"

    print ""
    print ""
    print ""
    print "Testing get ID list"
    print "Locally stored ID list: ", listOfIds
    remoteListOfIds = simulator.getListOfIds()
    print "Remotely stored ID list: ", remoteListOfIds
    assert equalList(remoteListOfIds, listOfIds), "The locally and remotly stored ID list is not equal."

    if testViaServer:
        s.close()
        
print ""
print ""
print ""
print ""
print ""
print ""

print "        !!!!!!!!!!!!!!!!!!    The test was succesful    !!!!!!!!!!!!!!!!!!"
