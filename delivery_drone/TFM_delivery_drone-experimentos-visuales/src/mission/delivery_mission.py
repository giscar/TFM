#!/usr/bin/env python3
import sys
import json
import time
import subprocess
import os
import math
import csv
import argparse
from datetime import datetime
sys.path.append('/ros2_ws/src/geo')
sys.path.append('/ros2_ws/src/optimization')
from mapbox_geocoder import MapboxGeocoder
from coordinates import latlon_to_local
from route_optimizer import RouteOptimizer

ALTITUDE = -2.5
SPEED = 5.0
BATTERY_RATE = 0.01
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

def export_results(seq_metrics, opt_metrics, improvement, optimized_order, waypoints, ref_lat, ref_lon, orders_file):
    results_dir = "/ros2_ws/src/experimentos/results"
    os.makedirs(results_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.splitext(os.path.basename(orders_file))[0]
    filename = f"{results_dir}/{base_name}_results_{timestamp}.csv"
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Fecha", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        writer.writerow(["Archivo de órdenes", orders_file])
        writer.writerow(["Referencia (lat,lon)", f"{ref_lat:.6f}, {ref_lon:.6f}"])
        writer.writerow([])
        writer.writerow(["Métrica", "Ruta secuencial", "Ruta optimizada", "Mejora (%)"])
        writer.writerow(["Distancia total (m)", f"{seq_metrics['dist']:.2f}", f"{opt_metrics['dist']:.2f}", f"{improvement:.2f}"])
        writer.writerow(["Tiempo estimado (s)", f"{seq_metrics['time']:.2f}", f"{opt_metrics['time']:.2f}", f"{((seq_metrics['time'] - opt_metrics['time']) / seq_metrics['time']) * 100:.2f}"])
        writer.writerow(["Consumo batería (%)", f"{seq_metrics['battery']:.2f}", f"{opt_metrics['battery']:.2f}", f"{((seq_metrics['battery'] - opt_metrics['battery']) / seq_metrics['battery']) * 100:.2f}"])
        writer.writerow(["Eficiencia (m/s)", f"{seq_metrics['speed']:.2f}", f"{opt_metrics['speed']:.2f}", "0.00"])
        writer.writerow([])
        writer.writerow(["Orden óptimo (IDs)"])
        for item in optimized_order:
            writer.writerow([item[0], item[1]])
        writer.writerow([])
        writer.writerow(["Waypoints locales (x,y) - Orden original"])
        for wp in waypoints:
            writer.writerow([wp[2], f"{wp[0]:.2f}", f"{wp[1]:.2f}", wp[3]])
    print(f"\n📄 Resultados exportados a {filename}")

def update_central_csv(mission_name, points, seq_dist, opt_dist, mejora, seq_time, opt_time, seq_bat, opt_bat):
    import csv
    import subprocess
    import os
    csv_path = "/home/ubuntu/dashboard/data/resumen_misiones.csv"
    # Leer filas existentes
    rows = []
    if os.path.exists(csv_path):
        with open(csv_path, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
    # Verificar si ya existe la misión (evitar duplicados)
    exists = any(row[0] == mission_name for row in rows[1:])
    if not exists:
        new_row = [mission_name, points, seq_dist, opt_dist, mejora, seq_time, opt_time, seq_bat, opt_bat]
        rows.append(new_row)
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(rows)
        print(f"📊 Resultado añadido a {csv_path}")
        # Commit y push automático
        try:
            subprocess.run(["cd", "/home/ubuntu/dashboard", "&&", "git", "add", "data/resumen_misiones.csv"], shell=True, check=False)
            subprocess.run(["cd", "/home/ubuntu/dashboard", "&&", "git", "commit", "-m", f"Actualización automática: {mission_name}"], shell=True, check=False)
            subprocess.run(["cd", "/home/ubuntu/dashboard", "&&", "git", "push"], shell=True, check=False)
            print("✅ Resultado subido a GitHub")
        except Exception as e:
            print(f"⚠️ No se pudo subir a GitHub: {e}")
    else:
        print(f"⚠️ La misión {mission_name} ya existe en el resumen. No se duplica.")

def main():
    parser = argparse.ArgumentParser(description='Misión de entrega optimizada')
    parser.add_argument('--json', type=str, required=True, help='Archivo JSON con órdenes')
    parser.add_argument('--ref-lat', type=float, required=True, help='Latitud de referencia (origen)')
    parser.add_argument('--ref-lon', type=float, required=True, help='Longitud de referencia (origen)')
    args = parser.parse_args()

    orders_file = args.json
    ref_lat = args.ref_lat
    ref_lon = args.ref_lon

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
    waypoints = []

    for order in orders:
        print(f"Geocodificando: {order['address']} ...")
        coords = geocoder.geocode(order['address'])
        if not coords:
            print(f"⚠️ No se pudo geocodificar: {order['address']}")
            continue
        lat, lon = coords
        x, y = latlon_to_local(lat, lon, ref_lat, ref_lon)
        waypoints.append((x, y, order['id'], order['address']))
        print(f"   -> ({x:.2f}, {y:.2f})")

    if len(waypoints) == 0:
        print("❌ No se obtuvo ningún waypoint válido")
        sys.exit(1)

    # Ruta secuencial
    sequential = sorted(waypoints, key=lambda w: w[2])
    seq_points = [(x, y, ALTITUDE) for (x, y, _, _) in sequential]
    start_point = (0.0, 0.0, ALTITUDE)
    opt = RouteOptimizer()
    seq_dist = opt.total_distance(seq_points, start_point)
    seq_time = seq_dist / SPEED
    seq_battery = seq_dist / 100 * BATTERY_RATE
    print_metrics(seq_points, start_point, "Ruta secuencial (por ID)", dist=seq_dist)

    # Optimización
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

    # Mapear orden optimizado
    waypoint_dict = {(round(x,2), round(y,2)): (oid, addr) for (x,y,oid,addr) in waypoints}
    optimized_order = []
    for point in optimized_route:
        key = (round(point[0],2), round(point[1],2))
        if key in waypoint_dict:
            oid, addr = waypoint_dict[key]
            optimized_order.append((oid, addr))
        else:
            optimized_order.append((None, f"Waypoint ({point[0]:.2f}, {point[1]:.2f})"))

    print("\n🗺️ Orden óptimo:")
    for i, (oid, addr) in enumerate(optimized_order):
        print(f"   {i+1}. Orden {oid}: {addr}")

    # Exportar resultado local
    seq_metrics = {"dist": seq_dist, "time": seq_time, "battery": seq_battery, "speed": SPEED}
    opt_metrics = {"dist": opt_dist, "time": opt_time, "battery": opt_battery, "speed": SPEED}
    export_results(seq_metrics, opt_metrics, improvement, optimized_order, waypoints, ref_lat, ref_lon, orders_file)

    # Guardar en CSV central y subir a GitHub
    mission_name = os.path.basename(orders_file).replace('.json', '')
    update_central_csv(mission_name, len(waypoints), seq_dist, opt_dist, improvement, seq_time, opt_time, seq_battery, opt_battery)

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
        x, y = next((x, y) for (x,y,wid,_) in waypoints if wid == oid)
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
