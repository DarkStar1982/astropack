#!/usr/local/bin/python3
from math import pi,sqrt,pow,cos,sin, acos, atan

# Important constants
T_SUN = 5780 # blackbody T of the Sun
T_EARTH = 255 # blackbody T of the Earth
R_sun = 6.95E8
R_earth = 6.371E6
D_earth = 1.471E11
A_earth = 0.34 #albedo
SB_CONST = 5.6703E-8

orbital_altitude1 = 3.6E7 # geosynchronous orbit
orbital_altitude2 = 2.5E5 # low-earth orbit

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

def get_surface_area(object_geometry):
    surface_area = 0.0
    if object_geometry["type"] == "box":
        a = object_geometry["dimensions"]["a"]
        b = object_geometry["dimensions"]["b"]
        c = object_geometry["dimensions"]["c"]
        surface_area = 2*a*b+2*a*c+2*b*c
    if object_geometry["type"] == "sphere":
        r = object_geometry["dimensions"]["a"]
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

#uniform illumination and radiation
def get_internal_heating(module, heat_flux, temperature):
    surface_area = get_surface_area(module)
    total_heat_out = surface_area*module["emissivity"]["ir"]*SB_CONST
    total_heat_in = total_heat_out*pow(temperature, 4)
    heat_ir = heat_flux["ir_flux"]*module["absorptivity"]["ir"]
    heat_visible = (heat_flux["albedo_flux"] + heat_flux["solar_flux"])*module["absorptivity"]["visible"]
    internal_heat = total_heat_in - (heat_ir+heat_visible)*surface_area
    return internal_heat

#uniform illumination and radiation
def get_equilibrium_temperature(model, heat_flux):
    result = 0.0
    if model["class"] == "uniform":
        # black bodies of variable shapes, but uniform properties
        surface_area = get_surface_area(model)
        heat_ir = heat_flux["ir_flux"]*model["absorptivity"]["ir"]
        heat_visible = (heat_flux["albedo_flux"] + heat_flux["solar_flux"])*model["absorptivity"]["visible"]
        total_heat_in = (heat_ir + heat_visible) * surface_area + model["heat_dissipation"]
        total_heat_out = surface_area * model["emissivity"]["ir"] * SB_CONST
        result = pow(total_heat_in/total_heat_out,0.25)
    if model["class"] == "variable":
        #for a non-uniform body
        internal_heat = model["heat_dissipation"]
        heat_visible = model["area_visible"]["area"] * model["area_visible"]["a_visible"] * heat_flux["solar_flux"]
        heat_albedo = model["area_albedo"]["area"]* model["area_albedo"]["a_visible"]* heat_flux["albedo_flux"]
        heat_ir = model["area_ir"]["area"] * model["area_ir"]["a_ir"] * heat_flux["ir_flux"] + internal_heat
        total_heat_in = heat_visible + heat_albedo + heat_ir
        total_heat_out = model["area_dissipation"]["area"]*model["area_dissipation"]["e_ir"]*SB_CONST
        # there should be a heat equation solver instead of instantenous temperature
        result = pow(total_heat_in/total_heat_out,0.25)
    return result

def calculate_heat_balance(orbital_altitude, model, eclipse=False):
    heat_inflow = heat_flux_in(orbital_altitude,eclipse)
    temp = get_equilibrium_temperature(model,heat_inflow)
    reradiated = power_radiation(temp)
    return {"temp":temp, "reradiated":reradiated}

def get_detailed_thermal_balance(orbit, satellite, module_list, eclipse=False):
    case = calculate_heat_balance(orbit, satellite, eclipse)
    print ("Equilibrium temperatute is %3.2f C" % display_in_celcius(case["temp"]))
    print ('Re-radiated power internally is %3.2f W/m^2' % case["reradiated"])
    heat_flux = {
        "ir_flux":case["reradiated"],
        "albedo_flux":0.0,
        "solar_flux":0.0
    }
    for x in module_list:
        t = get_equilibrium_temperature(x, heat_flux)
        print("Equilibrium temperature for module: %s is %3.2f C" %(x["id"],display_in_celcius(t)))

# initialize data
# how it should be:
# input: geometry + materials + radiation sources
# output: equilibrium temperature or heating/cooling required
# geometry example - non-uniform illumination and non-uniform properties
def load_satellite_geometry():
    satellite = {
        "heat_dissipation":0.0,
        "class":"variable",
        "area_visible" :
        {
            "area":1.0,
            "e_ir":0.9,
            "a_ir":0.9,
            "a_visible":0.21
        },
        "area_albedo":
        {
            "area":1.0,
            "e_ir":0.9,
            "a_ir":0.9,
            "a_visible":0.21
        },
        "area_ir":
        {
            "area":1.0,
            "e_ir":0.9,
            "a_ir":0.9,
            "a_visible":0.21
        },
        "area_dissipation":
        {
            "area":1.0,
            "e_ir":0.9,
            "a_ir":0.9,
            "a_visible":0.21
        }
    }
    total_area = 2.2*1.9*2+2.2*3.5*2+1.9*3.5*2
    satellite["area_visible"]["area"] = total_area/2.0
    satellite["area_albedo"]["area"] = total_area/2.0
    satellite["area_ir"]["area"] = total_area/2.0
    satellite["area_dissipation"]["area"] = total_area
    satellite["heat_dissipation"] = 3000
    return satellite

def load_module_list():
    # geometry example - uniform illumination and uniform properties
    module1 = {
        "id":"test",
        "class":"uniform",
        "type":"box",
        "heat_dissipation":30.0,
        "emissivity":{
            "ir": 0.9,
            "visible":0.9
        },
        "absorptivity":{
            "ir":0.9,
            "visible":0.9
        },
        "dimensions":{
            "a":0.42,
            "b":0.27,
            "c":0.276,
        }
    }
    return [module1]

def main():
    satellite1 = load_satellite_geometry()
    # hot case
    print ("Calculating hot case...")
    module_list = load_module_list()
    get_detailed_thermal_balance(orbital_altitude2, satellite1, module_list)
    # cold case
    print ("Calculating cold case...")
    get_detailed_thermal_balance(orbital_altitude1, satellite1, module_list, eclipse=True)

main()
