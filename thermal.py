#!/usr/local/bin/python3
from math import pi, sqrt, pow, cos, sin, acos, atan

T_SUN = 5780 # blackbody T of the Sun
T_EARTH = 255 # blackbody T of the Earth
R_sun = 6.95E8
R_earth = 6.371E6
D_earth = 1.471E11
A_earth = 0.34 #albedo
SB_CONST = 5.6703E-8

orbital_altitude1 = 3.6E7 # geosynchronous orbit
orbital_altitude2 = 2.5E5 # low-earth orbit

# geometry example
module1 = {
    "type":"shell",
    "heat_dissipation":0.0,
    "emissivity":{
        "ir": 0.9,
        "visible": 0.9
    },
    "absorptivity":{
        "ir":0.9,
        "visible:":0.9
    },
    "dimensions":{
        "a":1.536,
        "b":0.39,
        "c":0.25,
    },
}

# heat flux example
heat_in = {
    "visible":0.0,
    "ir":0.0
}


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
    if object_geometry["type"] == "shell":
        a = object_geometry["dimensions"]["a"]
        b = object_geometry["dimensions"]["b"]
        c = object_geometry["dimensions"]["c"]
        surface_area = 2*a*b+2*a*c+2*b*c
    return surface_area

#uniform illumination and radiation
def get_equilibrium_temperature(module, heat_flux):
    surface_area = get_surface_area(module)
    heat_in = heat_flux["ir"]*module["absorptivity"]["ir"]

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

def heat_flux_in(orbital_attitude):
    P_sun = power_blackbody(R_sun,T_SUN)
    P_earth = power_blackbody(R_earth, T_EARTH)
    solar_irradiation = power_per_area_at_distance(P_sun,D_earth)
    earth_irradiation = power_per_area_at_distance(P_earth,R_earth)
    P_albedo = power_albedo(R_earth,solar_irradiation,A_earth)
    albedo_irradiation = albedo_irradiance(P_albedo,R_earth)

    albedo_flux = albedo_irradiation*(1-sqrt(1-pow(R_earth,2)/pow(R_earth+orbital_attitude,2)))
    ir_flux = earth_irradiation*(1-sqrt(1-pow(R_earth,2)/pow(R_earth+orbital_attitude,2)))
    visible_flux = solar_irradiation
    return {"solar_flux":solar_irradiation, "albedo_flux":albedo_flux, "ir_flux":ir_flux, }

def main():
    heat_inflow = heat_flux_in(orbital_altitude1)

    visible_flux = heat_inflow["solar_flux"]
    albedo_flux = heat_inflow["albedo_flux"]
    ir_flux = heat_inflow["ir_flux"]

    print('Solar flux is %3.2f W/m^2' % visible_flux)
    print('Albedo flux is %3.2f W/m^2' % albedo_flux)
    print('IR flux is %3.2f W/m^2' % ir_flux)

    internal_heat_dissipation = 0 # 4612
    total_area = 2.2*1.9*2+2.2*3.5*2+1.9*3.5*2
    area_sun = total_area/2.0
    area_albedo = total_area/2.0
    area_ir = total_area/2.0
    area_dissipation = total_area

    absorbtivity_visible = 0.21
    emissivity_ir = 0.9

    #eclipse
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
    # eclipse case
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
    x = power_radiation(t2)
    # wavelength from T
    print ('Re-radiated power is %3.2f W/m^2' % x)

    ir_flux = x
    area_module_1 =get_surface_area(module1)
    # module example
    #t3 = get_equilibrium_t(absorbtivity_visible,
    #                   emissivity_ir,
    #                   0,
    #                   0,
    #                   ir_flux,
    #                   0,
    #                   0,
    #                   area_ir,
    #                   area_dissipation,
    #                   20)
    #print("Module temperature is %3.2f C" % (t3-273.15))

main()
