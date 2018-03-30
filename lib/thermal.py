#!/usr/local/bin/python3
from math import pi, sqrt, pow, cos, sin, acos, atan

# Important constants
T_SUN = 5780 # blackbody T of the Sun
T_EARTH = 255 # blackbody T of the Earth
R_sun = 6.95E8
R_earth = 6.371E6
D_earth = 1.471E11
A_earth = 0.34 #albedo
SB_CONST = 5.6703E-8
DEFAULT_VIEW_ANGLE = 0

def degree_to_radians(value):
    return (pi*value/180)

def display_in_celcius(value):
    return (value-273.15)

def power_blackbody(r, t):
    power = 4*pi*pow(r,2)*SB_CONST*pow(t,4)
    return power

def power_radiation(t):
    power = SB_CONST*pow(t,4)
    return power

def power_per_area_at_distance(p,r):
    a = 4*pi*pow(r,2)
    return p/a

def power_albedo(r,p_specific,albedo):
    area = pi*pow(r,2)
    return area*p_specific*albedo

def albedo_irradiance(p,r):
    a = pi*pow(r,2)
    return p/a

# given a 3d shape and angle between the plane,
# get an are project on that plane
def get_projected_area(object_geometry, view_angle):
    for x in object_geometry:

def get_surface_area(object_geometry, view_angle):
    surface_area = 0.0
    if object_geometry["type"] == "plate2D":
        a = object_geometry["dimensions"]["a"]
        b = object_geometry["dimensions"]["b"]
        surface_area = a*b
        if view_angle != DEFAULT_VIEW_ANGLE:
            surface_area = surface_area*cos(degree_to_radians(view_angle))
    if object_geometry["type"] == "box":
        a = object_geometry["dimensions"]["a"]
        b = object_geometry["dimensions"]["b"]
        c = object_geometry["dimensions"]["c"]
        surface_area = 2*a*b+2*a*c+2*b*c
    if object_geometry["type"] == "sphere":
        r = object_geometry["dimensions"]["r"]
        surface_area = 4*pi*pow(r,2)

    return surface_area

def heat_flux_in(orbital_attitude, in_eclipse=False):
    P_sun = power_blackbody(R_sun,T_SUN)
    P_earth = power_blackbody(R_earth, T_EARTH)
    solar_irradiation = power_per_area_at_distance(P_sun,D_earth)
    earth_irradiation = power_per_area_at_distance(P_earth,R_earth)
    P_albedo = power_albedo(R_earth,solar_irradiation,A_earth)
    albedo_irradiation = albedo_irradiance(P_albedo,R_earth)
    albedo_flux = albedo_irradiation*(1-sqrt(1-pow(R_earth,2)/pow(R_earth+orbital_attitude,2)))
    ir_flux = earth_irradiation*(1-sqrt(1-pow(R_earth,2)/pow(R_earth+orbital_attitude,2)))
    visible_flux = solar_irradiation
    if not in_eclipse:
        return { "solar_flux":solar_irradiation, "albedo_flux":albedo_flux, "ir_flux":ir_flux }
    else:
        return { "solar_flux":0.0, "albedo_flux":0.0, "ir_flux":ir_flux }

# calculate thermal equilibrium of given shape:
# get equilibrium temperatur and radiated power
def solve_thermal_balance(heat_flux, model, view_angle=0):
    absorbing_surface_area = get_surface_area(model,view_angle)
    heat_ir = heat_flux["ir_flux"]*model["ir"]["absorptivity"]
    heat_visible = (heat_flux["albedo_flux"] + heat_flux["solar_flux"])*model["visible"]["absorptivity"]
    total_heat_in = (heat_ir + heat_visible) * absorbing_surface_area + model["heat_dissipation"]
    dissipating_surface_area = get_surface_area(model,0)
    if model["class"] == "shell":
        total_heat_out = 2*dissipating_surface_area * model["ir"]["emissivity"] * SB_CONST
        result_temp = pow(total_heat_in/total_heat_out,0.25)
        reradiated_ir = power_radiation(result_temp)
    if model["class"] == "solid":
        total_heat_out = dissipating_surface_area * model["ir"]["emissivity"] * SB_CONST
        result_temp = pow(total_heat_in/total_heat_out,0.25)
        reradiated_ir = 0.0
    reradiated_flux = {
        "ir_flux":reradiated_ir,
        "albedo_flux":0.0,
        "solar_flux":0.0
    }
    return {"result_temp":result_temp, "reradiated_flux":reradiated_flux}

# initialize data
# how it should be:
# input: geometry + materials + radiation sources
# output: equilibrium temperature or heating/cooling required
# geometry example - non-uniform illumination and non-uniform properties
def main():
    orbital_altitude1 = 3.6E7 # geosynchronous orbit
    orbital_altitude2 = 2.5E5 # low-earth orbit
    plate2D = {
        "heat_dissipation":2300.0,
        "type":"plate2D",
        "class":"shell",
        "dimensions":{
            "a" : 2.2,
            "b" : 3.5
        },
        "ir":{
            "absorptivity":0.9,
            "emissivity":0.9
        },
        "visible":
        {
            "absorptivity":0.9,
            "emissivity":0.9
        }
    }

    smu = {
        "type":"box",
        "class":"solid",
        "heat_dissipation":0.0,
        "ir":
        {
            "absorptivity":0.9,
            "emissivity":0.9
        },
        "visible":{
            "absorptivity":0.9,
            "emissivity":0.9
        },
        "dimensions":{
            "a":0.42,
            "b":0.27,
            "c":0.276,
        }
    }
    # satellite1 = load_satellite_geometry()
    # hot case
    # print ("Calculating hot case...")
    # module_list = load_module_list()
    # get_detailed_thermal_balance(orbital_altitude2, satellite1, module_list)
    # satellite1["heat_dissipation"] = 3000
    # print ("Calculating cold case...")
    # get_detailed_thermal_balance(orbital_altitude1, satellite1, module_list, eclipse=True)
    heat_flux = heat_flux_in(orbital_altitude1)
    result = solve_thermal_balance(heat_flux,plate2D,0)
    print("Equilibrium temperature is %3.2f C" % display_in_celcius(result["result_temp"]))
    result = solve_thermal_balance(result["reradiated_flux"],smu)
    print("Equilibrium temperature is %3.2f C" % display_in_celcius(result["result_temp"]))
    #print("Reradiated power is %3.2f W/m^2" % result["reradiated_flux"])

main()
