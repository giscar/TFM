#!/usr/bin/env python3
import requests
import os

class MapboxGeocoder:
    def __init__(self, token=None):
        self.token = token or os.environ.get("MAPBOX_TOKEN")
        if not self.token:
            raise ValueError("No se encontró token de Mapbox. Proporciónalo o define la variable MAPBOX_TOKEN.")
        self.base_url = "https://api.mapbox.com/geocoding/v5/mapbox.places/"

    def geocode(self, address, limit=1):
        url = f"{self.base_url}{address}.json"
        params = {
            "access_token": self.token,
            "limit": limit,
            "language": "es"
        }
        try:
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("features"):
                    lon, lat = data["features"][0]["geometry"]["coordinates"]
                    return lat, lon
            else:
                print(f"Error en geocodificación: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Excepción: {e}")
        return None

    def reverse_geocode(self, lat, lon, limit=1):
        url = f"{self.base_url}{lon},{lat}.json"
        params = {
            "access_token": self.token,
            "limit": limit,
            "language": "es"
        }
        try:
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("features"):
                    return data["features"][0]["place_name"]
            else:
                print(f"Error en reverse geocode: {response.status_code}")
        except Exception as e:
            print(f"Excepción: {e}")
        return None

if __name__ == "__main__":
    g = MapboxGeocoder()
    coords = g.geocode("Madrid")
    print(coords)
