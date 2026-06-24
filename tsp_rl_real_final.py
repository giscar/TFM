import numpy as np
import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import PPO
import requests
import matplotlib.pyplot as plt
import time
import os
from itertools import permutations
from geopy.distance import geodesic

# =========================
# CONFIG MAPBOX
# =========================

MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN", "").strip()

def geocode(address):
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{address}.json"
    params = {"access_token": MAPBOX_TOKEN, "limit": 1}
    response = requests.get(url, params=params)
    data = response.json()
    coords = data["features"][0]["geometry"]["coordinates"]
    return coords  # [lon, lat]

# =========================
# DIRECCIONES REALES
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

print("Obteniendo coordenadas...")
points = np.array([geocode(addr) for addr in addresses])

# =========================
# DISTANCIA REAL (METROS)
# =========================

def distance_real(p1, p2):
    return geodesic((p1[1], p1[0]), (p2[1], p2[0])).meters

def total_distance_real(route, points):
    dist = 0
    for i in range(len(route) - 1):
        dist += distance_real(points[route[i]], points[route[i+1]])
    return dist

# =========================
# ENTORNO RL
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
            return self.state, -10, False, False, {}

        prev = self.current
        self.current = action
        self.visited.append(action)

        dist = distance_real(self.points[prev], self.points[action])
        reward = -dist

        self.state[action] = 1
        terminated = len(self.visited) == self.n

        return self.state, reward, terminated, False, {}

# =========================
# TSP FUERZA BRUTA
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
# EJECUTAR TSP
# =========================

start = time.time()
tsp_route, tsp_distance = tsp_bruteforce(points)
tsp_time = time.time() - start

# =========================
# ENTRENAR RL
# =========================

env = TSPEnv(points)
model = PPO("MlpPolicy", env, verbose=0)

print("Entrenando RL...")
model.learn(total_timesteps=15000)

# =========================
# EJECUTAR RL
# =========================

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
# TIEMPO DE VUELO REAL
# =========================

velocidad = 10  # m/s

tsp_flight_time = tsp_distance / velocidad
rl_flight_time = rl_distance / velocidad

# =========================
# RESULTADOS
# =========================

print("\n===== RESULTADOS REALES =====")
print(f"TSP -> Distancia: {tsp_distance:.2f} m | Tiempo vuelo: {tsp_flight_time:.2f} s | Tiempo cálculo: {tsp_time:.4f}s")
print(f"RL  -> Distancia: {rl_distance:.2f} m | Tiempo vuelo: {rl_flight_time:.2f} s | Tiempo cálculo: {rl_time:.4f}s")

# =========================
# GRAFICAS
# =========================

plot_route(points, tsp_route, "Ruta TSP")
plot_route(points, route, "Ruta RL")

# Comparación
methods = ["TSP", "RL"]
distances = [tsp_distance, rl_distance]

plt.bar(methods, distances)
plt.title("Comparación de Distancia (m)")
plt.ylabel("Distancia (m)")
plt.show()
