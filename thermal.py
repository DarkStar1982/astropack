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

# geometry example - uniform illumination and uniform properties
module1 = {
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

# how it should be:
# input: geometry + materials + radiation sources
# output: equilibrium temperature or heating/cooling required
# geometry example - non-uniform illumination and non-uniform properties
satellite1 = {
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

# this assumes zero thermal capacity
def get_equilibrium_t(absorptivity_visible,
                      emissivity_ir,
                      flux_visible,
                      flux_albedo,
                      flux_ir,
                      area_absorbing_visible,
                      area_absorbing_albedo,
                      area_absorbing_ir,
                      area_emitting_ir,
                      internal_heat):

    absorptivity_ir = emissivity_ir
    heat_in = area_absorbing_visible*absorptivity_visible*flux_visible
    heat_in = heat_in + area_absorbing_albedo*absorptivity_visible*flux_albedo
    heat_in = heat_in + area_absorbing_ir*absorptivity_ir*flux_ir + internal_heat
    heat_out = area_emitting_ir*emissivity_ir*SB_CONST
    # there should be a heat equation solver instead of instantenous temperature
    result = pow(heat_in/heat_out,0.25)
    return result

def calculate_heat_balance(orbital_altitude, model, eclipse=False):
    heat_inflow = heat_flux_in(orbital_altitude,eclipse)
    temp = get_equilibrium_temperature(satellite1,heat_inflow)
    reradiated = power_radiation(temp)
    # wavelength from T
    print("Equilibrium temperatute is %3.2f C" % display_in_celcius(temp))
    print ('Re-radiated power is %3.2f W/m^2' % reradiated)

def main():
    #initialize data
    total_area = 2.2*1.9*2+2.2*3.5*2+1.9*3.5*2
    satellite1["area_visible"]["area"] = total_area/2.0
    satellite1["area_albedo"]["area"] = total_area/2.0
    satellite1["area_ir"]["area"] = total_area/2.0
    satellite1["area_dissipation"]["area"] = total_area
    satellite1["heat_dissipation"] = 3000
    # hot case
    calculate_heat_balance(orbital_altitude2, satellite1)
    # cold case
    calculate_heat_balance(orbital_altitude1, satellite1, eclipse=True)
    # ====old====
    # hot case
    heat_inflow = heat_flux_in(orbital_altitude1)

    visible_flux = heat_inflow["solar_flux"]
    albedo_flux = heat_inflow["albedo_flux"]
    ir_flux = heat_inflow["ir_flux"]
    #print('Solar flux is %3.2f W/m^2' % visible_flux)
    #print('Albedo flux is %3.2f W/m^2' % albedo_flux)
    #print('IR flux is %3.2f W/m^2' % ir_flux)
    area_sun = total_area/2.0
    area_albedo = total_area/2.0
    area_ir = total_area/2.0
    area_dissipation = total_area
    internal_heat_dissipation = 3000 # 4612
    absorbtivity_visible = 0.21
    emissivity_ir = 0.9
    t1 = get_equilibrium_t(absorbtivity_visible,
                       emissivity_ir,
                       visible_flux,
                       albedo_flux,
                       ir_flux,
                       area_sun,
                       area_albedo,
                       area_ir,
                       area_dissipation,
                       internal_heat_dissipation)
    # cold case
    t2 = get_equilibrium_t(absorbtivity_visible,
                       emissivity_ir,
                       0,
                       0,
                       ir_flux,
                       area_sun,
                       area_albedo,
                       area_ir,
                       area_dissipation,
                       internal_heat_dissipation)

    print('Equilibrium temperature %3.2f C' % (t1-273.15))
    print('Eclipse temperature %3.2f C' % (t2-273.15))
    x = power_radiation(t1)
    # wavelength from T
    #print ('Re-radiated power is %3.2f W/m^2' % x)

    # heat flux example
    heat_in1 = {
        "solar_flux":0.0,
        "albedo_flux":0.0,
        "ir_flux":x
    }

    result = get_equilibrium_temperature(module1, heat_in1)
    # print("Equlibrium temperature is %3.2f C" % (result-273.15))
    desired_t = 273
    internal_heat = get_internal_heating(module1, heat_in1, result)
    # print("Required internal heating for equilibirum T of %3.2f C is %3.2f W" % ((result-273.15), internal_heat))
main()
