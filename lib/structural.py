#!/usr/local/bin/python3
from math import sqrt
import numpy as np

#part description
sat_body = {
    "type":"box",
    "mass":1500,
    "dimensions":{
        "a":1.9,
        "b":2.2,
        "c":3.5,
    },
    "offset":{
        "dx":0.0,
        "dy":0.0,
        "dz":0.0
    }
}

solar_panel_A = {
    "type":"box",
    "mass":100,
    "dimensions":{
        "a":2.0,
        "b":2.0,
        "c":0.3,
    },
    "offset":{
        "dx":1.1,
        "dy":0.0,
        "dz":-0.75
    }
}

solar_panel_B = {
    "type":"box",
    "mass":100,
    "dimensions":{
        "a":2.0,
        "b":2.0,
        "c":0.3,
    },
    "offset":{
        "dx":-1.1,
        "dy":0.0,
        "dz":-0.75
    }
}

solar_panel_1 = {
    "type":"thin_rect",
    "mass":100,
    "dimensions":{
        "a":2.0,
        "b":12.885,
    },
    "offset":{
        "dx":7.4,
        "dy":0.0,
        "dz":-0.75
    }
}

solar_panel_2 = {
    "type":"thin_rect",
    "mass":100,
    "dimensions":{
        "a":2.0,
        "b":12.885,
    },
    "offset":{
        "dx":-7.4,
        "dy":0.0,
        "dz":-0.75
    }
}

antenna_module = {
    "type":"cylinder",
    "mass":46,
    "dimensions":{
        "d":0.6,
        "h":1.83,
    },
    "offset":{
        "dx":0.0,
        "dy":1.25,
        "dz":-0.835
    }
}

antenna_boom_A = {
    "type": "rod",
    "mass":14,
    "dimensions":{
        "d":0.3,
        "l":5.0
    },
    "offset":{
        "dx":0.0,
        "dy":2.868,
        "dz":-3.518
    }
}

antenna_boom_B = {
    "type": "rod",
    "mass":14,
    "dimensions":{
        "d":0.3,
        "l":4.0
    },
    "offset":{
        "dx":0.0,
        "dy":4.635,
        "dz":-7.285
    }
}

reflector = {
    "type": "disk",
    "mass":18,
    "dimensions":{
        "d":8.0,
        "h":0.01
    },
    "offset":{
        "dx":0.0,
        "dy":0.635,
        "dz":-9.285
    }
}

#composite structure
satellite_stowed = [sat_body,solar_panel_A,solar_panel_B,antenna_module]
satellite_partially_deployed = [sat_body,solar_panel_1,solar_panel_2,antenna_module]
satellite_fully_deployed = [sat_body,solar_panel_1,solar_panel_2,antenna_boom_A,antenna_boom_B,reflector]


def moments_of_inertia(shape):
    r_n = sqrt(shape["offset"]["dx"]**2+shape["offset"]["dy"]**2+shape["offset"]["dz"]**2)
    m = shape["mass"]
    dx = shape["offset"]["dx"]
    dy = shape["offset"]["dy"]
    dz = shape["offset"]["dz"]
    if shape["type"] == "box":
        a = shape["dimensions"]["a"]
        b = shape["dimensions"]["b"]
        c = shape["dimensions"]["c"]
        Ixx = (m/12.0)*(a**2+c**2) + m*(r_n**2)
        Iyy = (m/12.0)*(b**2+c**2) + m*(r_n**2)
        Izz = (m/12.0)*(a**2+b**2) + m*(r_n**2)
    if shape["type"] == "thin_rect":
        a = shape["dimensions"]["a"]
        b = shape["dimensions"]["b"]
        Ixx = (m/12.0)*(b**2) + m*(r_n**2)
        Iyy = (m/12.0)*(a**2) + m*(r_n**2)
        Izz = (m/12.0)*(a**2+b**2) + m*(r_n**2)
    if shape["type"] == "rod":
        l = shape["dimensions"]["l"]
        Ixx  = (m/12.0)*l**2 +  m*(r_n**2)
        Iyy = 0 +  m*(r_n**2)
        Izz =  (m/12.0)*l**2 +  m*(r_n**2)
    if shape["type"] == "disk":
        r = shape["dimensions"]["d"]/2.0
        Ixx = (m*r**2)/4 +  m*(r_n**2)
        Iyy = Ixx
        Izz = (m*r**2)/2 + m*(r_n**2)
    if shape["type"] == "cylinder":
        r = shape["dimensions"]["d"]/2.0
        h = shape["dimensions"]["h"]
        Ixx = (m/12.0)*(3*r**2+h**2) + m*(r_n**2)
        Iyy = (m/12.0)*(3*r**2+h**2) + m*(r_n**2)
        Izz = (m/2.0)*(r**2) + m*(r_n**2)
    Ixy = m*dx*dy
    Ixz = m*dx*dz
    Iyz = m*dy*dz
    Iyx = Ixy
    Izx = Ixz
    Izy = Iyz
    return [[Ixx, -Ixy, -Ixz],[-Iyx, Iyy, -Iyz], [-Izx, -Izy, Izz]]

def print_matrix(matrix):
    for item in matrix:
        print(["%3.2f" % x for x in item])

def add_matrices(a,b):
    x = np.matrix(a)
    y = np.matrix(b)
    z = np.add(x,y)
    return z.tolist()

def ret_jordan(x):
    j = np.matrix(x)
    w, v = np.linalg.eig(j)
    t = w.tolist()
    t = sorted(t)
    r = [t[0],0,0],[0,t[1],0],[0,0,t[2]]
    return r

def calculate_inertia_tensor(structure):
    result = [[0,0,0],[0,0,0],[0,0,0]]
    for part in structure:
        part_result = moments_of_inertia(part)
        result = add_matrices(result,part_result)
    inertia_matrix = ret_jordan(result)
    print_matrix(inertia_matrix)

def main():
    calculate_inertia_tensor(satellite_stowed)
    print('\n')
    calculate_inertia_tensor(satellite_partially_deployed)
    print('\n')
    calculate_inertia_tensor(satellite_fully_deployed)
    print('\n')
main()
