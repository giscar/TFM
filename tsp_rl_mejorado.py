import numpy as np
import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import PPO
import matplotlib.pyplot as plt
import time
from itertools import permutations
from geopy.distance import geodesic

# =========================
# COORDENADAS REALES (LIMA)
# =========================
# (Evita fallos de API y es válido para tu TFM)

points = np.array([
    [-77.0428, -12.0464],  # Lima
    [-77.0300, -12.1210],  # Miraflores
    [-77.0365, -12.0972],  # San Isidro
    [-76.9910, -12.1400],  # Surco
    [-77.1180, -12.0620],  # Callao
])

# =========================
# DISTANCIA REAL (METROS)
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

        # ❌ penalización fuerte por repetir nodo
        if action in self.visited:
            return self.state, -100, False, False, {}

        prev = self.current
        self.current = action
        self.visited.append(action)

        dist = distance_real(self.points[prev], self.points[action])

        # 🔥 NORMALIZACIÓN (estabilidad)
        dist_norm = dist / 10000

        # 🔥 REWARD BASE
        reward = -dist_norm

        # 🔥 penalización por saltos largos
        if dist > 20000:
            reward -= 0.5

        # 🔥 incentivo por cercanía
        reward += 0.1 / (dist_norm + 0.001)

        # 🔥 bonus por completar
        if len(self.visited) == self.n:
            reward += 5

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
    plt.scatter(points[:,0], points[:,1], color='blue')

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

model = PPO(
    "MlpPolicy",
    env,
    verbose=0,
    learning_rate=0.001
)

print("Entrenando RL...")
model.learn(total_timesteps=50000)

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
# TIEMPO DE VUELO
# =========================

velocidad = 10  # m/s

tsp_flight = tsp_distance / velocidad
rl_flight = rl_distance / velocidad

# =========================
# RESULTADOS
# =========================

print("\n===== RESULTADOS MEJORADOS =====")
print(f"TSP -> Distancia: {tsp_distance:.2f} m | Tiempo vuelo: {tsp_flight:.2f} s | Cálculo: {tsp_time:.4f}s")
print(f"RL  -> Distancia: {rl_distance:.2f} m | Tiempo vuelo: {rl_flight:.2f} s | Cálculo: {rl_time:.4f}s")

# =========================
# GRAFICAS
# =========================

plot_route(points, tsp_route, "Ruta TSP")
plot_route(points, route, "Ruta RL")

# Comparación
methods = ["TSP", "RL"]
distances = [tsp_distance, rl_distance]

plt.bar(methods, distances)
plt.title("Comparación de Distancia")
plt.ylabel("Metros")
plt.show()