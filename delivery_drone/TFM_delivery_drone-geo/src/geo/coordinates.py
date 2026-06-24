#!/usr/bin/env python3
import math

def latlon_to_local(lat, lon, ref_lat, ref_lon):
    R = 6371000
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    ref_lat_rad = math.radians(ref_lat)
    ref_lon_rad = math.radians(ref_lon)
    dlat = lat_rad - ref_lat_rad
    dlon = lon_rad - ref_lon_rad
    x = R * dlon * math.cos(ref_lat_rad)
    y = R * dlat
    return x, y

def local_to_latlon(x, y, ref_lat, ref_lon):
    R = 6371000
    ref_lat_rad = math.radians(ref_lat)
    dlat = y / R
    dlon = x / (R * math.cos(ref_lat_rad))
    lat = math.degrees(ref_lat_rad + dlat)
    lon = math.degrees(math.radians(ref_lon) + dlon)
    return lat, lon

if __name__ == "__main__":
    ref_lat, ref_lon = 47.3977, 8.5443
    x, y = latlon_to_local(47.398, 8.545, ref_lat, ref_lon)
    print(f"x={x:.2f}, y={y:.2f}")
    lat2, lon2 = local_to_latlon(x, y, ref_lat, ref_lon)
    print(f"recuperado: {lat2:.6f}, {lon2:.6f}")
