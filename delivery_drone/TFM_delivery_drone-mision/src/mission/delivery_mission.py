#!/usr/bin/env python3
import sys
import json
import time
import subprocess
import os
import math
import csv
from datetime import datetime
sys.path.append('/ros2_ws/src/geo')
sys.path.append('/ros2_ws/src/optimization')
from mapbox_geocoder import MapboxGeocoder
from coordinates import latlon_to_local
from route_optimizer import RouteOptimizer

# Configuración
REF_LAT = 35.9000          # Valletta Ferry Terminal (Malta)
REF_LON = 14.5200
ALTITUDE = -2.5            # metros (negativo = arriba)
SPEED = 5.0                # m/s (supuesto)
BATTERY_RATE = 0.01        # % por cada 100 metros (ejemplo)

DURATION_TAKEOFF = 5
DURATION_WAYPOINT = 10
DURATION_RETURN = 10
DURATION_LAND = 5

def publish_setpoint(x, y, z, duration):
    cmd = [
        "ros2", "topic", "pub", "--rate", "20", "/fmu/in/trajectory_setpoint",
        "px4_msgs/msg/TrajectorySetpoint",
        f"{{position: [{x}, {y}, {z}], yaw: 0.0}}"
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(duration)
    proc.terminate()
    proc.wait()

def wait_countdown(seconds, message):
    print(f"{message} ", end="", flush=True)
    for i in range(seconds, 0, -1):
        print(f"{i}... ", end="", flush=True)
        time.sleep(1)
    print("¡YA!\n")

def get_current_z():
    try:
        result = subprocess.run(
            ["ros2", "topic", "echo", "/fmu/out/vehicle_local_position_v1", "--once"],
            capture_output=True, text=True, timeout=2
        )
        for line in result.stdout.split('\n'):
            if line.startswith('z:'):
                parts = line.split()
                if len(parts) > 1:
                    val_str = parts[1]
                    if val_str not in ('.inf', 'inf', '-inf'):
                        return float(val_str)
        return None
    except Exception:
        return None

def force_arm_and_takeoff():
    subprocess.run([
        "ros2", "topic", "pub", "--once", "/fmu/in/vehicle_command",
        "px4_msgs/msg/VehicleCommand",
        "{command: 400, param1: 1.0, target_system: 1, target_component: 1, source_system: 1, source_component: 1, from_external: true}"
    ], stdout=subprocess.DEVNULL)
    time.sleep(2)
    subprocess.run([
        "ros2", "topic", "pub", "--once", "/fmu/in/vehicle_command",
        "px4_msgs/msg/VehicleCommand",
        "{command: 22, param7: 2.5, target_system: 1, target_component: 1, source_system: 1, source_component: 1, from_external: true}"
    ], stdout=subprocess.DEVNULL)

def print_metrics(route, start_point, description, dist=None):
    if dist is None:
        opt = RouteOptimizer()
        dist = opt.total_distance(route, start_point)
    tiempo = dist / SPEED
    bateria = dist / 100 * BATTERY_RATE
    print(f"\n📊 {description}:")
    print(f"   Distancia total: {dist:.2f} m")
    print(f"   Tiempo estimado: {tiempo:.2f} s")
    print(f"   Consumo batería: {bateria:.2f} %")
    print(f"   Eficiencia (m/s): {SPEED:.2f} (constante)")
    return dist, tiempo, bateria

def export_results(seq_metrics, opt_metrics, improvement, optimized_order, waypoints):
    """Exporta los resultados a un archivo CSV con timestamp en la carpeta experimentos/results."""
    results_dir = "/ros2_ws/src/experimentos/results"
    os.makedirs(results_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{results_dir}/mission_results_{timestamp}.csv"
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Fecha", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        writer.writerow([])
        writer.writerow(["Métrica", "Ruta secuencial", "Ruta optimizada", "Mejora (%)"])
        writer.writerow(["Distancia total (m)", f"{seq_metrics['dist']:.2f}", f"{opt_metrics['dist']:.2f}", f"{improvement:.2f}"])
        writer.writerow(["Tiempo estimado (s)", f"{seq_metrics['time']:.2f}", f"{opt_metrics['time']:.2f}", f"{((seq_metrics['time'] - opt_metrics['time']) / seq_metrics['time']) * 100:.2f}"])
        writer.writerow(["Consumo batería (%)", f"{seq_metrics['battery']:.2f}", f"{opt_metrics['battery']:.2f}", f"{((seq_metrics['battery'] - opt_metrics['battery']) / seq_metrics['battery']) * 100:.2f}"])
        writer.writerow(["Eficiencia (m/s)", f"{seq_metrics['speed']:.2f}", f"{opt_metrics['speed']:.2f}", "0.00"])
        writer.writerow([])
        writer.writerow(["Orden óptimo (IDs)"])
        for item in optimized_order:
            writer.writerow([item[0], item[1]])  # ID, dirección
        writer.writerow([])
        writer.writerow(["Waypoints locales (x,y) - Orden original"])
        for wp in waypoints:
            writer.writerow([wp[2], wp[0], wp[1], wp[3]])  # ID, x, y, dirección
    print(f"\n📄 Resultados exportados a {filename}")
    return filename

def main():
    orders_file = "/ros2_ws/src/mission/orders.json"
    if not os.path.exists(orders_file):
        print(f"❌ Archivo {orders_file} no encontrado")
        sys.exit(1)

    with open(orders_file) as f:
        orders = json.load(f)
    print(f"📦 Órdenes cargadas: {len(orders)}")
    for o in orders:
        print(f"   {o['id']}: {o['address']}")

    token = os.environ.get("MAPBOX_TOKEN")
    if not token:
        print("❌ Variable MAPBOX_TOKEN no definida")
        sys.exit(1)

    geocoder = MapboxGeocoder(token)
    waypoints = []  # (x, y, id, address)

    for order in orders:
        print(f"Geocodificando: {order['address']} ...")
        coords = geocoder.geocode(order['address'])
        if not coords:
            print(f"⚠️ No se pudo geocodificar: {order['address']}")
            continue
        lat, lon = coords
        x, y = latlon_to_local(lat, lon, REF_LAT, REF_LON)
        waypoints.append((x, y, order['id'], order['address']))
        print(f"   -> ({x:.2f}, {y:.2f})")

    if len(waypoints) == 0:
        print("❌ No se obtuvo ningún waypoint válido")
        sys.exit(1)

    # Ruta secuencial (por ID)
    sequential = sorted(waypoints, key=lambda w: w[2])
    seq_points = [(x, y, ALTITUDE) for (x, y, _, _) in sequential]
    start_point = (0.0, 0.0, ALTITUDE)
    opt = RouteOptimizer()
    seq_dist = opt.total_distance(seq_points, start_point)
    seq_time = seq_dist / SPEED
    seq_battery = seq_dist / 100 * BATTERY_RATE
    print_metrics(seq_points, start_point, "Ruta secuencial (por ID)", dist=seq_dist)

    # Ruta optimizada
    print("\n🧠 Optimizando ruta...")
    opt = RouteOptimizer()
    for (x, y, _, _) in waypoints:
        opt.add_waypoint(x, y, ALTITUDE)
    optimized_route, opt_dist = opt.optimize_tsp(start_point)
    opt_time = opt_dist / SPEED
    opt_battery = opt_dist / 100 * BATTERY_RATE
    print_metrics(optimized_route, start_point, "Ruta optimizada", dist=opt_dist)

    improvement = ((seq_dist - opt_dist) / seq_dist) * 100 if seq_dist > 0 else 0
    print(f"\n✅ Mejora respecto a la ruta secuencial: {improvement:.2f}%")

    # Mapear orden optimizado a IDs y direcciones
    waypoint_dict = {}
    for (x, y, oid, addr) in waypoints:
        key = (round(x, 2), round(y, 2))
        waypoint_dict[key] = (oid, addr)

    optimized_order = []
    for point in optimized_route:
        key = (round(point[0], 2), round(point[1], 2))
        if key in waypoint_dict:
            oid, addr = waypoint_dict[key]
            optimized_order.append((oid, addr))
        else:
            optimized_order.append((None, f"Waypoint ({point[0]:.2f}, {point[1]:.2f})"))

    print("\n🗺️ Orden óptimo:")
    for i, (oid, addr) in enumerate(optimized_order):
        print(f"   {i+1}. Orden {oid}: {addr}")

    # Exportar resultados
    seq_metrics = {"dist": seq_dist, "time": seq_time, "battery": seq_battery, "speed": SPEED}
    opt_metrics = {"dist": opt_dist, "time": opt_time, "battery": opt_battery, "speed": SPEED}
    filename = export_results(seq_metrics, opt_metrics, improvement, optimized_order, waypoints)

    # Ejecutar misión
    print("\n🚀 INICIANDO MISIÓN")
    offboard_proc = subprocess.Popen(
        ["ros2", "topic", "pub", "--rate", "20", "/fmu/in/offboard_control_mode",
         "px4_msgs/msg/OffboardControlMode", "{position: true}"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    time.sleep(2)

    print("1️⃣ Despegando...")
    publish_setpoint(0.0, 0.0, ALTITUDE, DURATION_TAKEOFF)
    z = get_current_z()
    if z is None or z > -0.2:
        print("⚠️ Despegue automático fallido. Forzando armado y despegue...")
        force_arm_and_takeoff()
        publish_setpoint(0.0, 0.0, ALTITUDE, 5)
    else:
        print(f"✅ Despegue detectado (z={z:.2f})")

    for idx, (oid, addr) in enumerate(optimized_order):
        x, y = None, None
        for (wx, wy, wid, _) in waypoints:
            if wid == oid:
                x, y = wx, wy
                break
        if x is None:
            x, y = optimized_route[idx][0], optimized_route[idx][1]
        print(f"{idx+2}️⃣ Visitando: {addr} (ID {oid}) -> coordenadas ({x:.2f}, {y:.2f})")
        publish_setpoint(x, y, ALTITUDE, DURATION_WAYPOINT)

    print("📌 Regresando al origen...")
    publish_setpoint(0.0, 0.0, ALTITUDE, DURATION_RETURN)

    print("🛬 Aterrizando...")
    publish_setpoint(0.0, 0.0, 0.0, DURATION_LAND)

    offboard_proc.terminate()
    offboard_proc.wait()
    print("\n✅ MISIÓN COMPLETADA")

if __name__ == "__main__":
    main()
