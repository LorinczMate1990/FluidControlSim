#!/usr/bin/python
# -*- coding: utf-8 -*-

# The goal of this simulation is to give a very basic liquid simulation for
# industrial plants. It's useless in real environment, but it's good to try
# some control loops and explain the basics of industrial control
# It has an easy-to-connect and well-documented interface, so it can connect
# with any control tools, even with real PLC-s.

# Uncovered physical phenomens
#  * Thermal expansion
#  * Delay of pipes

# while ((1)); do sleep 1; a=`pep8 fluidsim.py | grep -v "blank line contains whitespace" | grep -v "line too long" | grep -v "trailing whitespace" | head -n 1`; clear; echo $a; done

import math
import cmath
import SocketServer
import threading
from utilities import PhysConsts
from os import linesep

class TooManyContainersForOnePipe(Exception):
    pass

class LogableInterface:
    def log(self):
        return {}

class FluidsimObject(object, LogableInterface):
    def getDescription(self):
        return {}
    
    def destroy(self):
        raise NotImplementedError()
        
class Fluid(FluidsimObject):
    def __init__(self, volume, temperature):
        self._volume = volume
        self._temperature = temperature
        self._rho = 1      # Sűrűség
        self._eta = 0.003  # viszkozitás
    
    def log(self):
        return {"volume":self._volume, "temperature":self._temperature}
    
    def getDescription(self):
        return {'temperature':self._temperature, 'volume':self._volume, 'rho':self._rho, 'eta':self._eta}
        
    def eta(self):
        return self._eta

    def setTemperature(self, temperature):
        self._temperature = float(temperature)
        
    def setVolume(self, volume):
        self._volume = float(volume)

    def temperature(self):
        return self._temperature

    def volume(self):
        return self._volume

    def rho(self):
        return self._rho

    def add(self, fluid):
        # Computing the common temperature with a weighted average
        if self.volume() + fluid.volume() > 0:
            commonTemp = (self.volume()*self.temperature() + fluid.volume()*fluid.temperature()) / (self.volume() + fluid.volume())
        else:
            commonTemp = 0
        self._temperature = commonTemp
        self._volume = self._volume + fluid._volume

    def remove(self, volume):
        if self.volume() < volume:
            ret = Fluid(self.volume(), self.temperature())
            self._volume = 0
        else:
            ret = Fluid(volume, self.temperature())
            self._volume -= volume
        return ret

    def pressure(self, height):
        return self.rho() * height * PhysConsts.g

class StaticFluid(Fluid):
    """
    The level or temperature never changes.
    It can simulate a source or a sink.
    """

    def add(self, fluid):
        pass
        
    def remove(self, volume):
        return Fluid(volume, self.temperature())

class Pipe(FluidsimObject):
    """
     The active elements (Pipe, Valve, Pump) connect two containers and fluid can flow through via them
     The active elements can only be HORIZONTAL.
     The active elements have no delay
     If you want to model diagonal or delayed pipes, you have to model them with two pipes and an additional container between them
    """
    def __init__(self, radius, length, height):
        assert length>0, "Length is zero"
        self.containers = []
        self.jointHeights = []
        self.radius = radius
        self.length = length
        self.height = height
    
    def getContainer1(self):
        return self.containers[0]
    
    def getContainer2(self):
        return self.containers[1]

    def __getFluidStream(self):
        source, p0, dest, p1 = self._getSourceAndDestiny()
        q = self._getFluidQuantity(p0, p1, source, 1)
        return q
             
    def getDescription(self):
        return {'type':'activeElement', 'subtype':'pipe', 'radius':self.radius,'length':self.length,'height':self.height,'stream':self.__getFluidStream()}
        
    def log(self):
        q = self.__getFluidStream()    
        return {'stream':self.__getFluidStream()}
        
    def attach(self, container):
        self.containers.append(container)
        if len(self.containers) > 2:
            raise TooManyContainersForOnePipe()

    def destroy(self):
        for container in self.containers:
            container.removePipe(self)

    def _getFlowSpeed(self, p0, p1, source):
        # http://metal.elte.hu/aft.elte.hu/Munkatarsak/illy/fizbiol/2016tavasz/valodi_folyadekok.pdf
        # The flowspeed of the fluid is depends on the cross-section of the pipe
        #                                          the pressures measured on the ends of the pipe
        #                                          and the viscosity of the fluid
        #
        #       v(r) = (R-r)^2 * (p₁ - p₂) / (4 * eta * l)
        #             
        # Because I don't model the different flowspeed inside the pipe, I have to calculate the average flowspeed.
        # For this, I have to integrate v(r) between -R and +R, and after that, I have to divide it by 2R.
        #
        #
        return pow(self.radius, 2) * (p0 - p1) / (4 * source.eta() * self.length) / 2

    def _getFluidQuantity(self, p0, p1, source, dT):
        v = self._getFlowSpeed(p0, p1, source)
        return v*dT*pow(self.radius, 2) * math.pi

    def _getPressure0(self):
        return self.containers[0].getPressureOnPipe(self)
    
    def _getPressure1(self):
        return self.containers[1].getPressureOnPipe(self)
        
    def _getSourceAndDestiny(self):
        p0 = self._getPressure0()
        p1 = self._getPressure1()
        if (p1 < p0):
            # A 0-ból az 1-be folyik a folyadék
            source = self.containers[0].fluid
            dest = self.containers[1].fluid
        else:
            # Az 1-esből a nullásba folyik a folyadék. Ez az áramló folyadék tulajdonságai miatt fontos, ezért megcserélem
            p0, p1 = p1, p0
            source = self.containers[1].fluid
            dest = self.containers[0].fluid
        return (source, p0, dest, p1)
    
    def flow(self, dT):
        dT = float(dT)
        source, p0, dest, p1 = self._getSourceAndDestiny()
        q = self._getFluidQuantity(p0, p1, source, dT)
        fluid = source.remove(q)
        dest.add(fluid)

class AbstractRamp(FluidsimObject):
    def __init__(self, initialValue):
        self.setpoint = initialValue
        self.actValue = initialValue
    
    def setSetpoint(self, value):
        self.setpoint = value
    
    def getSetpoint(self):
        return self.setpoint
    
    def getActValue(self):
        return self.actValue
        
    def getDescription(self):
        return {'rampparams':self.getParams()}

    def setParams(self, params):
        raise NotImplementedError
    
    def getParams(self):
        raise NotImplementedError

    def recalc(self, dT):
        raise NotImplementedError
    

class LinearRamp(AbstractRamp):
    def __init__(self, initialValue, delta):
        AbstractRamp.__init__(self, initialValue)
        self.delta = delta
    
    def setParams(self, params):
        self.delta = params[0]
    
    def getParams(self):
        return (self.delta,)
        
    def setSetpoint(self, value):
        self.setpoint = value
    
    def getSetpoint(self):
        return self.setpoint
    
    def getActValue(self):
        return self.actValue
    
    def recalc(self, dT):
        difference = self.delta * dT
        if self.actValue < self.setpoint:
            self.actValue = min(self.actValue + difference, self.setpoint)
        else:
            self.actValue = max(self.actValue - difference, self.setpoint)

class SecondOrderDiffRamp(AbstractRamp):
    """
    The class solves symbolicly the following diff eqution:
        y + alpha*y' + beta*y'' = setpoint
    """
    
    def __init__(self, initialValue, alpha, beta):
        AbstractRamp.__init__(self, initialValue)
        self.alpha = alpha
        self.beta = beta
        
        self.Y = lambda t: initialValue
        self.dY = lambda t: 0
        self.actTime = 0
    
    def setParams(self, params):
        self.alpha = params[0]
        self.beta = params[1]
        self.__refreshSolution()
    
    def getParams(self):
        return (self.alpha, self.beta)

    def setSetpoint(self, value):
        self.setpoint = value
        self.__refreshSolution()
    
    def getSetpoint(self):
        return self.setpoint

    def getActValue(self):
        return self.actValue
    
    def recalc(self, dT):
        self.actTime += dT
        self.actValue = self.Y(self.actTime)
        
    def __refreshSolution(self):
        alpha = self.alpha
        beta = self.beta    
        D = math.pow(alpha, 2) - 4*beta

        if beta == 0:
            self.__generateFirstOrderDiffEq()
        elif D == 0:
            self.__generateSecOrderDiffEqWithIdenticalRoots()
        else:
            self.__generateSecOrderDiffEqWithDifferentRoots(D)
        
        self.actTime = 0           
            
    def __generateFirstOrderDiffEq(self):
        alpha = self.alpha
        Sp = self.setpoint
        y_0 = self.Y(self.actTime)
        
        c = y_0-Sp
        
        print alpha, Sp, y_0, c
        
        self.Y = lambda t: c*math.exp(-1./alpha * t) + Sp
        self.dY = lambda t: -1./alpha*c*math.exp(-1./alpha * t)
    
    def __generateSecOrderDiffEqWithIdenticalRoots(self):
        y_0 = self.Y(self.actTime)
        dY_0 = self.dY(self.actTime)
        Sp = self.setpoint
        alpha = self.alpha
        beta = self.beta    
        
        l = -alpha / (2. * beta)
        c1 = y_0 - Sp
        c2 = dY_0 - c1*Sp
        
        self.Y = lambda t: c1*math.exp(l*t) + c2*t*math.exp(l*t) + Sp
        self.dY = lambda t: l*c1*math.exp(l*t) + l*c2*t*math.exp(l*t)
    
    def __generateSecOrderDiffEqWithDifferentRoots(self, D):
        y_0 = self.Y(self.actTime)
        dY_0 = self.dY(self.actTime)
        Sp = self.setpoint
        alpha = self.alpha
        beta = self.beta    
        
        l1 = -(alpha + cmath.sqrt(D))/(2.*beta)
        l2 = -(alpha - cmath.sqrt(D))/(2.*beta)
        
        c2 = (dY_0 - l1*(y_0-Sp))/(l2-l1)
        c1 = y_0 - Sp - c2
        self.Y = lambda t: (c1*cmath.exp(l1*t) + c2*cmath.exp(l2*t) + Sp).real
        self.dY = lambda t: (l1*c1*cmath.exp(l1*t) + l2*c2*cmath.exp(l2*t)).real

class Valve(Pipe):
    def __init__(self, minRadius, maxRadius, length, height):   
        # Here, the self.radius is the current radius. (Like in the other two ActiveElements)
        super(Valve, self).__init__(maxRadius, length, height)
        self.minRadius = minRadius
        self.maxRadius = maxRadius
        self.ramp = SecondOrderDiffRamp(100, 10, 0)
    
    def flow(self, dT):
        self.ramp.recalc(dT)
        self._recalcRadius()
        Pipe.flow(self, dT)
    
    def log(self):
        l = Pipe.log(self)
        l.update({"permeability":self.ramp.getActValue()})
        return l

    def getDescription(self):
        ret = super(Valve, self).getDescription()
        ret.update({'type':'activeElement', 'subtype':'valve',"minradius":self.minRadius, "maxradius":self.maxRadius, "permeability":self.ramp.getActValue(), "setpoint":self.ramp.getSetpoint()})
        ret.update(self.ramp.getDescription())
        return ret
    
    def getPermeability(self):
        return self.ramp.getActValue()

    def close(self, percentPoint):
        self.setPermeability(self.ramp.getActValue()-percentPoint)
    
    def open(self, percentPoint):
        self.setPermeability(self.ramp.getActValue()+percentPoint)
    
    def _recalcRadius(self):
        self.radius = (self.maxRadius - self.minRadius)/100.0*self.ramp.getActValue() + self.minRadius
        
    def setPermeability(self, percent):
        if percent < 0:
            percent = 0
        if percent > 100:
            percent = 100
        self.ramp.setSetpoint(percent)


class Pump(Pipe):
    def __init__(self, radius, length, height, maxPressure):
        super(Pump, self).__init__(radius, length, height)
        self.maxPressure = maxPressure
        self.performance = 0
        self.ramp = SecondOrderDiffRamp(0, 10, 0)

    def flow(self, dT):
        self.ramp.recalc(dT)
        Pipe.flow(self, dT)

    def log(self):
        l = Pipe.log(self)
        l.update({"performance":self.ramp.getActValue()})
        return l
    
    def getDescription(self):
        ret = super(Pump, self).getDescription()
        ret.update({'type':'activeElement', 'subtype':'pump', "maxpressure":self.maxPressure, "performance":self.ramp.getActValue(), "setpoint":self.ramp.getSetpoint()})
        ret.update(self.ramp.getDescription())
        return ret
    
    def actPressure(self):
        return self.maxPressure * self.ramp.getActValue() / 100.0
    
    def setPerformance(self, percent):
        if percent > 100:
            percent = 100
        if percent < -100:
            percent = -100
        self.ramp.setSetpoint(percent)

    def getPerformance(self):
        return self.ramp.getActValue()
    
    def increasePerformance(self, percentPoint):
        self.setPerformance(self.ramp.getActValue()+percentPoint)
    
    def decreasePerformance(self, percentPoint):
        self.setPerformance(self.ramp.getActValue()-percentPoint)
    
    def _getPressure0(self):
        return super(Pump, self)._getPressure0()+self.actPressure()


class StandardPressureCalculator(FluidsimObject):
    def __init__(self, area, maxWaterLevel):
        self.area = float(area)
        self.fluid = 0
        self.maxVolume = float(maxWaterLevel) * self.area
    
    def setFluid(self, fluid):
        self.fluid = fluid
    
    def getWaterLevelFor(self, volume):
        return float(volume)/float(self.area)
    
    def getVolumeFor(self, level):
        return self.area*level
    
    def getWaterLevel(self):
        return self.getWaterLevelFor(self.fluid.volume())
    
    def setLevel(self, level):
        self.fluid.setVolume(self.getVolumeFor(level))
    
    def getPressureAt(self, height):
        fluidHeight = self.fluid.volume()/self.area
        fluidHeight = self.getWaterLevelFor(self.fluid.volume())
        return self.fluid.pressure(fluidHeight-height)

    def log(self):
        return {"waterlevel":self.getWaterLevel()}

    def getDescription(self):
        return {'maxvolume':self.maxVolume, 'waterlevel':self.getWaterLevel(), 'maxwaterlevel':self.getWaterLevelFor(self.maxVolume), 'area':self.area}

class Container(FluidsimObject):
    def __init__(self, pressureCalculator, fluid=None):
        # pressureFunc : descendant of StandardPressureCalculator
        self.fluid = fluid if fluid is not None else Fluid(0,0)
        self.pressureCalculator = pressureCalculator
        self.pressureCalculator.setFluid(self.fluid)
        self.joins = {}
        self.baseLine = 0  # The distance between the container's bottom and the ground

    def log(self):
        ret = {}
        fluidLog = self.fluid.log()
        pressureLog = self.pressureCalculator.log()
        ret.update(fluidLog)
        ret.update(pressureLog)
        return ret

    def getDescription(self):
        ret = {'type':'container', "baseline":self.baseLine}
        ret.update(self.fluid.getDescription())
        ret.update(self.pressureCalculator.getDescription())
        return ret
    
    def setLevel(self, level):
        self.pressureCalculator.setLevel(level)
    
    def attachPipe(self, pipe):
        self.joins[pipe] = pipe.height-self.baseLine
        pipe.attach(self)
    
    def removePipe(self, pipe):
        return self.joins.pop(pipe, False)
    
    def destroy(self):
        attachedPipes = self.joins.keys() # the pipe.destroy will modify the self.joins dictionary, need copy from the keys
        for pipe in attachedPipes:
            pipe.destroy()
        return attachedPipes
    
    def getPressureOnPipe(self, pipe):
        return self.pressureCalculator.getPressureAt(self.joins[pipe])

class FileLogHandler:
    def __init__(self, prefix, logID, fluidSimObject):
        self.filename = str(prefix)+str(logID)+".log"
        self.fluidSimObject = fluidSimObject
        with open(self.filename, 'w') as f:
            firstLog = fluidSimObject.log()
            self.keys = firstLog.keys()
            f.write("timestamp")
            for key in self.keys:
                f.write(","+str(key))
            f.write(linesep)
    
    def createLog(self, timestamp):
        actLog = self.fluidSimObject.log()
        with open(self.filename, 'a') as f:
            f.write(str(timestamp))
            for key in self.keys:
                f.write(","+str(actLog[key]))
            f.write(linesep)
        
class LogManager:
    def __init__(self, logHandlerTypeList):
        self.logHandlerTypes = logHandlerTypeList
        self.logHandlers = []
        self.prefix = "logs/" 
        self.logPeriod = 1.0
        self.prevLogTimestamp = 0
    
    def monitor(self, ID, fluidSimObject):
        for LogHandler in self.logHandlerTypes:
            self.logHandlers.append(LogHandler(self.prefix, ID, fluidSimObject))
        
    def createLog(self, timestamp):
        if timestamp >= self.prevLogTimestamp + self.logPeriod:
            self.prevLogTimestamp = timestamp
            for logHandler in self.logHandlers:
                logHandler.createLog(timestamp)       
