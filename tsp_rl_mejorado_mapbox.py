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

# =========================
# CONFIG MAPBOX
# =========================

MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN", "").strip()

def geocode(address):
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{address}.json"
    params = {
        "access_token": MAPBOX_TOKEN,
        "limit": 1
    }

    response = requests.get(url, params=params)
    data = response.json()

    # Manejo seguro de errores
    if "features" not in data or len(data["features"]) == 0:
        print(f"⚠️ Error con dirección: {address}")
        raise ValueError("No se pudo geocodificar")

    coords = data["features"][0]["geometry"]["coordinates"]
    return coords  # [lon, lat]

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
    "San Borja Lima"
]

print("Obteniendo coordenadas...")
points = np.array([geocode(addr) for addr in addresses])

# =========================
# DISTANCIA REAL
# =========================

def distance_real(p1, p2):
    return geodesic((p1[1], p1[0]), (p2[1], p2[0])).meters

def total_distance_real(route, points):
    return sum(
        distance_real(points[route[i]], points[route[i+1]])
        for i in range(len(route)-1)
    )

# =========================
# ENTORNO RL MEJORADO
# =========================

class TSPEnv(gym.Env):
    def __init__(self, points):
        super().__init__()
        self.points = points
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

def tsp_bruteforce(points):
    n = len(points)
    min_route = None
    min_dist = float("inf")

    for perm in permutations(range(1, n)):
        route = [0] + list(perm)
        dist = total_distance_real(route, points)

        if dist < min_dist:
            min_dist = dist
            min_route = route

    return min_route, min_dist

# =========================
# GRAFICAR
# =========================

def plot_route(points, route, title):
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
    plt.show()

# =========================
# EJECUCIÓN
# =========================

# TSP
start = time.time()
tsp_route, tsp_distance = tsp_bruteforce(points)
tsp_time = time.time() - start

# RL
env = TSPEnv(points)

model = PPO("MlpPolicy", env, verbose=0)
print("Entrenando RL...")
model.learn(total_timesteps=50000)

start = time.time()

obs, _ = env.reset()
route = [0]
done = False

while not done:
    action, _ = model.predict(obs)
    obs, reward, done, truncated, _ = env.step(action)
    if action not in route:
        route.append(action)

rl_time = time.time() - start
rl_distance = total_distance_real(route, points)

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

plot_route(points, tsp_route, "Ruta TSP")
plot_route(points, route, "Ruta RL")

plt.bar(["TSP", "RL"], [tsp_distance, rl_distance])
plt.title("Comparación de Distancia")
plt.ylabel("Metros")
plt.show()
