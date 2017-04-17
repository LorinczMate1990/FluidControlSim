#!/usr/bin/python
# -*- coding: utf-8 -*-

import math

class PhysConsts:
    g = 10

def syncronize(func):
    def ret(self, *arg):
        with self.lock:
            return func(self, *arg)
    return ret

def str2bool(string):
    trueStrings = ['true', '1', 't', 'y', 'yes']
    return string in trueStrings
    
def bool2str(boolean):
    return 'true' if boolean else 'false'
    

def coordTransform(arrayOfCoords, funcForX, funcForY):
    retArray = []
    for x,y in arrayOfCoords:   
        nX = funcForX(x,y)
        nY = funcForY(x,y)
        retArray.append((nX, nY))
    return retArray

def rotate(arrayOfCoords, alpha):
    funcForX = lambda x, y: x*math.cos(alpha) - y*math.sin(alpha)
    funcForY = lambda x, y: x*math.sin(alpha) + y*math.cos(alpha)
    return coordTransform(arrayOfCoords, funcForX, funcForY)
    
def translate(arrayOfCoords, newCenter):
    funcForX = lambda x, y: x+newCenter[0]
    funcForY = lambda x, y: y+newCenter[1]
    return coordTransform(arrayOfCoords, funcForX, funcForY)
   
def calculateElevationInRadian(point1, point2):
    dX = point2[0]-point1[0]
    dY = point2[1]-point1[1]

    if dX == 0: 
        return math.pi/2 if dY > 0 else -math.pi/2
    
    alpha = math.atan(float(dY)/float(dX))
    
    if dX>0:
        return alpha
    else:
        return math.pi+alpha
    
def limit(value, minimum, maximum):
    if value < minimum:
        return minimum
    elif maximum < value:
        return maximum
    else:
        return value
        
def rescale(value, oldMin, oldMax, newMin, newMax):
    return float(value-oldMin)/float(oldMax-oldMin)*float(newMax-newMin)+newMin
