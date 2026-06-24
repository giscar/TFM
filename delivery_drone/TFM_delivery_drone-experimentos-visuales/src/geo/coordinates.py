#!/usr/bin/env python3
"""
Módulo para manejo de coordenadas geográficas y conversiones.
"""

import math

def latlon_to_local(lat, lon, ref_lat, ref_lon):
    """
    Convierte coordenadas geográficas a coordenadas locales (x, y)
    usando una referencia.
    
    Args:
        lat, lon: Coordenadas a convertir (grados)
        ref_lat, ref_lon: Coordenadas de referencia (grados)
    
    Returns:
        x, y: Coordenadas locales en metros
    """
    # Radio de la Tierra en metros
    R = 6371000
    
    # Convertir a radianes
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    ref_lat_rad = math.radians(ref_lat)
    ref_lon_rad = math.radians(ref_lon)
    
    # Diferencias
    dlat = lat_rad - ref_lat_rad
    dlon = lon_rad - ref_lon_rad
    
    # Aproximación plana (válida para distancias pequeñas)
    x = R * dlon * math.cos(ref_lat_rad)
    y = R * dlat
    
    return x, y

def local_to_latlon(x, y, ref_lat, ref_lon):
    """
    Convierte coordenadas locales (x, y) a geográficas.
    
    Args:
        x, y: Coordenadas locales en metros
        ref_lat, ref_lon: Coordenadas de referencia (grados)
    
    Returns:
        lat, lon: Coordenadas geográficas en grados
    """
    R = 6371000
    ref_lat_rad = math.radians(ref_lat)
    
    dlat = y / R
    dlon = x / (R * math.cos(ref_lat_rad))
    
    lat = math.degrees(ref_lat_rad + dlat)
    lon = math.degrees(math.radians(ref_lon) + dlon)
    
    return lat, lon

def haversine(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia entre dos puntos geográficos usando la fórmula de Haversine.
    
    Returns:
        Distancia en metros
    """
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

if __name__ == "__main__":
    # Pruebas
    ref_lat, ref_lon = 47.3977, 8.5443  # Referencia en Zúrich
    
    # Prueba 1: convertir a locales y regresar
    x, y = latlon_to_local(ref_lat + 0.01, ref_lon + 0.01, ref_lat, ref_lon)
    lat2, lon2 = local_to_latlon(x, y, ref_lat, ref_lon)
    
    print(f"Original: ({ref_lat+0.01:.6f}, {ref_lon+0.01:.6f})")
    print(f"Locales: x={x:.2f}m, y={y:.2f}m")
    print(f"Recuperado: ({lat2:.6f}, {lon2:.6f})")
    print(f"Error: {abs(lat2-(ref_lat+0.01)):.2e} grados")
    
    # Prueba 2: distancia Haversine
    dist = haversine(ref_lat, ref_lon, ref_lat+0.01, ref_lon+0.01)
    print(f"Distancia Haversine: {dist:.2f}m")
