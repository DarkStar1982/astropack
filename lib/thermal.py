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

MATERIAL_OSR = {
        "ir":{
            "absorptivity":0.83,
            "emissivity":0.83
        },
        "visible":
        {
            "absorptivity":0.06,
            "emissivity":0.06
        },
    }

MATERIAL_BLANKET  = {
        "ir":{
            "absorptivity":0.003,
            "emissivity":0.83
        },
        "visible":
        {
            "absorptivity":0.83,
            "emissivity":0.83
        },
    }

MATERIAL_BLACKBODY  = {
        "ir":{
            "absorptivity":0.83,
            "emissivity":0.83
        },
        "visible":
        {
            "absorptivity":0.83,
            "emissivity":0.83
        },
    }


def degree_to_radians(value):
    return (pi*value/180)

def kelvin_to_celcius(value):
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

def get_surface_area(object_geometry, view_angle=0.0, mode="total"):
    surface_area = 0.0
    if object_geometry["type"] == "plate2D":
        a = object_geometry["dimensions"]["a"]
        b = object_geometry["dimensions"]["b"]
        surface_area = a*b
        if mode == "projection":
            surface_area = surface_area*cos(degree_to_radians(view_angle))
    if object_geometry["type"] == "box":
        a = object_geometry["dimensions"]["a"]
        b = object_geometry["dimensions"]["b"]
        c = object_geometry["dimensions"]["b"]
        surface_area = 2*a*b+2*b*c+2*c*a
        if mode == "projection":
            #todo
            pass
    return surface_area

# calculate thermal equilibrium of given shape:
# get equilibrium temperatur and radiated power
# including calculate view are for Earth IR and albedo

def solve_thermal_balance(heat_flux, model,internal_heat_dissipation, view_angles, visible_shaded=False, ir_shaded=False):
    ir_absorbing_surface_area = get_surface_area(model,view_angles["ir"],"projection")
    visible_absorbing_surface_area = get_surface_area(model,view_angles["visible"],"projection")
    albedo_absorbing_surface_area = get_surface_area(model,view_angles["ir"],"projection")
    if ir_shaded:
        total_heat_ir = 0.0
    else:
        heat_ir = heat_flux["ir_flux"]*model["material"]["ir"]["absorptivity"]
        total_heat_ir = heat_ir*ir_absorbing_surface_area
    if visible_shaded:
        heat_visible = heat_flux["albedo_flux"] * model["material"]["visible"]["absorptivity"]
        total_heat_visible = heat_visible*albedo_absorbing_surface_area
    else:
        heat_visible_a = heat_flux["albedo_flux"] * model["material"]["visible"]["absorptivity"] * albedo_absorbing_surface_area
        heat_visible_b = heat_flux["solar_flux"] * model["material"]["visible"]["absorptivity"] * visible_absorbing_surface_area
        total_heat_visible = heat_visible_a + heat_visible_b
    total_heat_in = total_heat_ir + total_heat_visible + internal_heat_dissipation
    dissipating_surface_area = get_surface_area(model,"total")
    if model["class"] == "shell":
        total_heat_out = 2*dissipating_surface_area * model["material"]["ir"]["emissivity"] * SB_CONST
        result_temp = pow(total_heat_in/total_heat_out,0.25)
        reradiated_ir = power_radiation(result_temp)
    if model["class"] == "solid":
        total_heat_out = dissipating_surface_area * model["material"]["ir"]["emissivity"] * SB_CONST
        result_temp = pow(total_heat_in/total_heat_out,0.25)
        reradiated_ir = 0.0
    reradiated_flux = {
        "ir_flux":reradiated_ir,
        "albedo_flux":0.0,
        "solar_flux":0.0
    }
    return { "result_temp":result_temp, "reradiated_flux":reradiated_flux }


def calculate_thermal_case(satellite_geometry, heat_flux):
    net_area = 0.0
    net_reradiated = 0.0
    for x in satellite_geometry:
        surface_area = get_surface_area(x[0])
        net_area = net_area + surface_area
        result = solve_thermal_balance(heat_flux,x[0],x[1],x[2],x[3],x[4])
        print("Equilibrium temperature is %3.2f C" % kelvin_to_celcius(result["result_temp"]))
        print("Reradiated power is %3.2f W/m^2" % result["reradiated_flux"]["ir_flux"])
        #print("Surface_area is %3.2f m^2" % surface_area)
        total_reradiated = surface_area*result["reradiated_flux"]["ir_flux"]
        net_reradiated = net_reradiated + total_reradiated
    internal_ir_level = net_reradiated/net_area
    internal_flux = {
        "ir_flux":internal_ir_level,
        "albedo_flux":0.0,
        "solar_flux":0.0
    }
    return internal_flux

# initialize data
# how it should be:
# input: geometry + materials + radiation sources
# output: equilibrium temperature or heating/cooling required
# geometry example - non-uniform illumination and non-uniform properties
def main():
    orbital_altitude1 = 2.5E5 # low-earth orbit
    orbital_altitude2 = 3.6E7 # geosynchronous orbit
    # illumination angle - direct
    view_angles_a = {
        "ir": 0.0,
        "visible": 0.0
    }
    # illumination angle - oblique
    view_angles_b = {
        "ir": 45.0,
        "visible": 45.0
    }

    # radiator plate - dissipating
    plate2D_osr = {
        "type":"plate2D",
        "class":"shell",
        "dimensions":{
            "a" : 2.2,
            "b" : 2.5
        },
        "material": MATERIAL_OSR
    }

    # non-radiator plate - absorbing
    plate2D_blanket_long = {
        "type":"plate2D",
        "class":"shell",
        "dimensions":{
            "a" : 1.9,
            "b" : 2.5
        },
        "material": MATERIAL_BLANKET
    }

    plate2D_blanket_short = {
        "type":"plate2D",
        "class":"shell",
        "dimensions":{
            "a" : 1.9,
            "b" : 2.2
        },
        "material": MATERIAL_BLANKET
    }

    # list of modules
    # as uniform blackbodies
    smu = {
        "type":"box",
        "class":"solid",
        "material": MATERIAL_BLACKBODY,
        "dimensions":{
            "a":0.42,
            "b":0.27,
            "c":0.276,
        }
    }

    print ("Calculating hot case...")
    satellite_geometry = [
        (plate2D_blanket_long, 0, view_angles_a, True, False), # bottom plate
        (plate2D_blanket_short, 0, view_angles_b, False, False), # forward plate
        (plate2D_blanket_short, 0, view_angles_b, False, False), # back plate
        (plate2D_blanket_long, 0, view_angles_a, False, True), # top plate
        (plate2D_osr, 2300, view_angles_b, False, False), # radiator 1
        (plate2D_osr, 2300, view_angles_b, False, False), # radiator 2
    ]

    heat_flux = heat_flux_in(orbital_altitude1)
    internal_flux = calculate_thermal_case(satellite_geometry, heat_flux)
    result = solve_thermal_balance(internal_flux, smu, 0.0, view_angles_a)
    print("Equilibrium module temperature is %3.2f C" % kelvin_to_celcius(result["result_temp"]))

    print ("Calculating cold case...")
    heat_flux = heat_flux_in(orbital_altitude2, True)
    satellite_geometry = [
        (plate2D_blanket_long, 0, view_angles_a, True, False), # bottom plate
        (plate2D_blanket_short, 0, view_angles_b, False, False), # forward plate
        (plate2D_blanket_short, 0,  view_angles_b, False, False), # back plate
        (plate2D_blanket_long, 0, view_angles_a, False, True), # top plate
        (plate2D_osr, 1400, view_angles_b, False, False), # radiator 1
        (plate2D_osr, 1400, view_angles_b, False, False), # radiator 2
        ]
    internal_flux = calculate_thermal_case(satellite_geometry, heat_flux)
    result = solve_thermal_balance(internal_flux, smu, 130.0, view_angles_a)
    print("Equilibrium module temperature is %3.2f C" % kelvin_to_celcius(result["result_temp"]))

main()
