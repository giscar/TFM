import numpy as np
import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import PPO
import matplotlib.pyplot as plt
import time
from itertools import permutations
from geopy.distance import geodesic
import requests
import os
from urllib.parse import quote

# =========================
# CONFIG
# =========================

MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN", "").strip()
SHOW_PLOTS = os.getenv("SHOW_PLOTS", "1") != "0"
REFINE_TIMESTEPS = int(os.getenv("RL_REFINE_TIMESTEPS", "0"))
TOTAL_START = time.perf_counter()

FALLBACK_COORDS = {
    "Lima Peru": [-77.0428, -12.0464],
    "Miraflores Lima": [-77.0305, -12.1211],
    "San Isidro Lima": [-77.0365, -12.0975],
    "Surco Lima": [-76.9919, -12.1469],
    "Callao Peru": [-77.1181, -12.0508],
    "La Molina Lima": [-76.9420, -12.0875],
    "Barranco Lima": [-77.0215, -12.1492],
    "San Borja Lima": [-76.9968, -12.1072],
    "Los Olivos Lima": [-77.0740, -11.9583],
    "Comas Lima": [-77.0500, -11.9320],
}

# =========================
# GEOCODING
# =========================

def geocode(address):
    fallback = FALLBACK_COORDS.get(address)

    if not MAPBOX_TOKEN:
        if fallback is not None:
            print(f"📍 Sin MAPBOX_TOKEN. Usando coordenada local: {address}")
            return fallback
        raise ValueError(f"No hay MAPBOX_TOKEN ni coordenada local para: {address}")

    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{quote(address)}.json"
    params = {"access_token": MAPBOX_TOKEN, "limit": 1}

    try:
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
    except requests.RequestException as exc:
        if fallback is not None:
            print(f"📍 Mapbox no respondió para {address}. Usando coordenada local.")
            return fallback
        raise ValueError(f"No se pudo geocodificar {address}: {exc}") from exc

    if response.status_code != 200 or "features" not in data or len(data["features"]) == 0:
        message = data.get("message", f"HTTP {response.status_code}")
        if fallback is not None:
            print(f"📍 Mapbox no geocodificó {address} ({message}). Usando coordenada local.")
            return fallback
        print(f"⚠️ Error con dirección: {address} ({message})")
        raise ValueError("No se pudo geocodificar")

    return data["features"][0]["geometry"]["coordinates"]

# =========================
# DIRECCIONES
# =========================

addresses = [
    "Lima Peru",
    "Miraflores Lima",
    "San Isidro Lima",
    "Surco Lima",
    "Callao Peru",
    "La Molina Lima",
    "Barranco Lima",
    "San Borja Lima",
    "Los Olivos Lima",
    "Comas Lima"
]

print("🌍 Obteniendo coordenadas...")
start = time.perf_counter()
points = np.array([geocode(addr) for addr in addresses])
geocode_time = time.perf_counter() - start
print(f"⏱️ Geocodificación completada en {geocode_time:.4f}s")

# 🔥 AHORA SÍ ES CORRECTO
MODEL_PATH = f"modelo_rl_{len(points)}"

# =========================
# DISTANCIA REAL
# =========================

def distance_real(p1, p2):
    return geodesic((p1[1], p1[0]), (p2[1], p2[0])).meters

def build_distance_matrix(points):
    n = len(points)
    matrix = np.zeros((n, n), dtype=np.float64)

    for i in range(n):
        for j in range(i + 1, n):
            dist = distance_real(points[i], points[j])
            matrix[i, j] = dist
            matrix[j, i] = dist

    return matrix

def total_distance_real(route, points=None, distance_matrix=None):
    if distance_matrix is not None:
        return sum(
            distance_matrix[route[i], route[i+1]]
            for i in range(len(route)-1)
        )

    return sum(
        distance_real(points[route[i]], points[route[i+1]])
        for i in range(len(route)-1)
    )

print("📏 Calculando matriz de distancias...")
start = time.perf_counter()
DISTANCE_MATRIX = build_distance_matrix(points)
distance_matrix_time = time.perf_counter() - start
print(f"⏱️ Matriz de distancias completada en {distance_matrix_time:.4f}s")

# =========================
# ENTORNO RL
# =========================

class TSPEnv(gym.Env):
    def __init__(self, points, distance_matrix=None):
        super().__init__()
        self.points = points
        self.distance_matrix = distance_matrix
        self.n = len(points)

        self.action_space = spaces.Discrete(self.n)
        self.observation_space = spaces.Box(
            low=0, high=1, shape=(self.n,), dtype=np.float32
        )

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current = 0
        self.visited = [0]
        self.state = np.zeros(self.n, dtype=np.float32)
        self.state[0] = 1
        return self.state, {}

    def step(self, action):

        if action in self.visited:
            return self.state, -100, False, False, {}

        prev = self.current
        self.current = action
        self.visited.append(action)

        if self.distance_matrix is not None:
            dist = self.distance_matrix[prev, action]
        else:
            dist = distance_real(self.points[prev], self.points[action])
        dist_norm = dist / 10000

        reward = -dist_norm

        if dist > 20000:
            reward -= 0.5

        reward += 0.1 / (dist_norm + 0.001)

        if len(self.visited) == self.n:
            reward += 5

        self.state[action] = 1
        terminated = len(self.visited) == self.n

        return self.state, reward, terminated, False, {}

# =========================
# TSP
# =========================

def tsp_bruteforce(points, distance_matrix):
    n = len(points)
    min_route = None
    min_dist = float("inf")

    for perm in permutations(range(1, n)):
        route = [0] + list(perm)
        dist = total_distance_real(route, distance_matrix=distance_matrix)

        if dist < min_dist:
            min_dist = dist
            min_route = route

    return min_route, min_dist

# =========================
# GRAFICAR
# =========================

def plot_route(points, route, title, output_path=None):
    plt.figure(figsize=(6,6))
    plt.scatter(points[:,0], points[:,1])

    for i in range(len(route)-1):
        p1 = points[route[i]]
        p2 = points[route[i+1]]
        plt.plot([p1[0], p2[0]], [p1[1], p2[1]], 'r-')

    for i, (x, y) in enumerate(points):
        plt.text(x, y, str(i))

    plt.title(title)
    plt.grid()
    if output_path:
        plt.savefig(output_path, dpi=160, bbox_inches="tight")
    if SHOW_PLOTS:
        plt.show()
    plt.close()

# =========================
# EJECUCIÓN TSP
# =========================

print("🚀 Ejecutando modelo TSP...")
start = time.perf_counter()
tsp_route, tsp_distance = tsp_bruteforce(points, DISTANCE_MATRIX)
tsp_time = time.perf_counter() - start
print(f"⏱️ Modelo TSP ejecutado en {tsp_time:.4f}s")

# =========================
# RL PERSISTENTE
# =========================

env = TSPEnv(points, DISTANCE_MATRIX)

if os.path.exists(MODEL_PATH + ".zip"):
    start = time.perf_counter()
    print("🔁 Cargando modelo existente...")
    model = PPO.load(MODEL_PATH, env=env)
    model_load_time = time.perf_counter() - start
    print(f"⏱️ Modelo RL cargado en {model_load_time:.4f}s")

    if REFINE_TIMESTEPS > 0:
        start = time.perf_counter()
        print(f"📈 Refinando modelo ({REFINE_TIMESTEPS} timesteps)...")
        model.learn(total_timesteps=REFINE_TIMESTEPS)
        refine_time = time.perf_counter() - start
        print(f"⏱️ Refinamiento RL completado en {refine_time:.4f}s")

else:
    start = time.perf_counter()
    print("🧠 Entrenando modelo desde cero...")
    model = PPO("MlpPolicy", env, verbose=0)
    model.learn(total_timesteps=50000)
    train_time = time.perf_counter() - start
    print(f"⏱️ Entrenamiento RL completado en {train_time:.4f}s")

# 💾 GUARDAR SIEMPRE
model.save(MODEL_PATH)
print("💾 Modelo guardado")

# =========================
# EJECUTAR RL
# =========================

print("🚀 Ejecutando modelo RL...")
start = time.perf_counter()

obs, _ = env.reset()
route = [0]
done = False

while not done:
    action, _ = model.predict(obs)
    action = int(action)

    if action in route:
        unvisited = [i for i in range(len(points)) if i not in route]
        if not unvisited:
            break
        action = min(unvisited, key=lambda idx: DISTANCE_MATRIX[env.current, idx])

    obs, reward, done, truncated, _ = env.step(action)

    if action not in route:
        route.append(action)

rl_time = time.perf_counter() - start
rl_distance = total_distance_real(route, distance_matrix=DISTANCE_MATRIX)
print(f"⏱️ Modelo RL ejecutado en {rl_time:.4f}s")

# =========================
# TIEMPO DE VUELO
# =========================

velocidad = 10

tsp_flight = tsp_distance / velocidad
rl_flight = rl_distance / velocidad

# =========================
# RESULTADOS
# =========================

print("\n===== RESULTADOS =====")
print(f"TSP -> {tsp_distance:.2f} m | Vuelo: {tsp_flight:.2f}s | Calc: {tsp_time:.4f}s")
print(f"RL  -> {rl_distance:.2f} m | Vuelo: {rl_flight:.2f}s | Calc: {rl_time:.4f}s")

# =========================
# GRÁFICAS
# =========================

OUTPUT_DIR = os.path.join("graficas", f"ejecucion_{time.strftime('%Y%m%d_%H%M%S')}")
os.makedirs(OUTPUT_DIR, exist_ok=True)

start = time.perf_counter()
plot_route(points, tsp_route, "Ruta TSP", os.path.join(OUTPUT_DIR, "ruta_tsp.png"))
plot_route(points, route, "Ruta RL", os.path.join(OUTPUT_DIR, "ruta_rl.png"))

plt.figure(figsize=(6,4))
plt.bar(["TSP", "RL"], [tsp_distance, rl_distance])
plt.title("Comparación de Distancia")
plt.ylabel("Metros")
plt.savefig(os.path.join(OUTPUT_DIR, "comparacion_distancia.png"), dpi=160, bbox_inches="tight")
if SHOW_PLOTS:
    plt.show()
plt.close()
plots_time = time.perf_counter() - start

print(f"📊 Gráficas guardadas en: {OUTPUT_DIR}")
print(f"⏱️ Gráficas generadas en {plots_time:.4f}s")
print(f"⏱️ Tiempo total de ejecución: {time.perf_counter() - TOTAL_START:.4f}s")
