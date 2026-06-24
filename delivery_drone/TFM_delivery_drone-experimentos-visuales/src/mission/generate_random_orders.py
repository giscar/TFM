#!/usr/bin/env python3
import json
import random
import sys
import csv
from datetime import datetime

# Listas de direcciones reales por país (máximo 12 direcciones válidas por país)
addresses = {
    "Malta": [
        "Sliema, Malta",
        "St Julians, Malta",
        "Naxxar, Malta",
        "Msida, Malta",
        "San Gwann, Malta",
        "Attard, Malta",
        "Swieqi, Malta",
        "Gzira, Malta",
        "Birkirkara, Malta",
        "St. Paul's Bay, Malta",
        "Mdina, Malta",
        "Luqa, Malta"
    ],
    "Bogotá": [
        "Carrera 32 #22B - 66, Bogotá, Colombia",
        "Calle 154a #96 - 40 Apto 102, Bogotá, Colombia",
        "Transversal 6 N° 27-10 Oficina 701, Bogotá, Colombia",
        "Cra. 91 N° 147-55 Lcs 11, Bogotá, Colombia",
        "Calle 153 #96-42 Suba, Bogotá, Colombia",
        "Transversal 70 D Bis A # 68-75 Sur Torre 5 Apto 503, Bogotá, Colombia",
        "Carrera 97F # 26-71 Sur Casa 293, Bogotá, Colombia",
        "Carrera 2 # 12C-61, Bogotá, Colombia",
        "Calle 65 A Sur # 11 A Este 56, Bogotá, Colombia",
        "Calle 45C # 1A - 14, Bogotá, Colombia",
        "Calle 34 Bis Sur # 95A - 70 Interior 8 Casa 20, Bogotá, Colombia",
        "Carrera 8 # 1-66 Sur, Bogotá, Colombia"
    ],
    "Villavicencio": [
        "Calle 10B No. 31A - 27 B. Panorama, Acacias, Meta, Colombia",
        "Calle 24A #13C - 55, Acacias, Meta, Colombia",
        "Calle 13 #24 - 65, Acacias, Meta, Colombia",
        "Calle 11 #12 - 110 B. Estero, Villavicencio, Meta, Colombia",
        "Calle 45 38 74, Villavicencio, Meta, Colombia",
        "Cra 12 #20 - 12, Villavicencio, Meta, Colombia",
        "Calle 10 #3A - 50, Villavicencio, Meta, Colombia"
    ]
}

def load_airport_coords():
    """Lee el archivo airports.csv y devuelve un diccionario {país: (lat, lon)}"""
    coords = {}
    with open('/ros2_ws/src/mission/airports.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            coords[row['País']] = (float(row['Latitud']), float(row['Longitud']))
    return coords

def generate_orders(country, num_orders):
    if country not in addresses:
        print(f"❌ País '{country}' no soportado. Usa: {list(addresses.keys())}")
        sys.exit(1)

    available = addresses[country]
    if num_orders > len(available):
        print(f"⚠️ Solo hay {len(available)} direcciones disponibles para {country}. Se usarán {len(available)}.")
        num_orders = len(available)

    # Seleccionar aleatoriamente sin repetición
    selected = random.sample(available, num_orders)
    orders = [{"id": i+1, "address": addr} for i, addr in enumerate(selected)]

    # Obtener coordenadas del aeropuerto
    airports = load_airport_coords()
    if country not in airports:
        print(f"❌ No se encontraron coordenadas de aeropuerto para {country}")
        sys.exit(1)
    ref_lat, ref_lon = airports[country]

    # Nombre del archivo con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"/ros2_ws/src/mission/random_{country}_{num_orders}_{timestamp}.json"

    with open(filename, "w") as f:
        json.dump(orders, f, indent=2)

    print(f"✅ Archivo generado: {filename}")
    print(f"📌 Referencia: lat={ref_lat}, lon={ref_lon}")
    return filename, ref_lat, ref_lon

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: generate_random_orders.py <país> <num_órdenes>")
        sys.exit(1)
    country = sys.argv[1]
    num_orders = int(sys.argv[2])
    generate_orders(country, num_orders)
