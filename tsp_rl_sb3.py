import numpy as np
import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import PPO

# =========================
# ENTORNO TSP PERSONALIZADO
# =========================

class TSPEnv(gym.Env):
    def __init__(self, points):
        super(TSPEnv, self).__init__()

        self.points = points
        self.n = len(points)

        # Acción: elegir siguiente nodo
        self.action_space = spaces.Discrete(self.n)

        # Estado: nodos visitados (vector binario)
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
        terminated = False
        truncated = False

        # Penalización por repetir nodo
        if action in self.visited:
            return self.state, -10, False, False, {}

        prev = self.current
        self.current = action
        self.visited.append(action)

        # Distancia euclidiana
        dist = np.linalg.norm(self.points[prev] - self.points[action])

        # Reward negativo → minimizar distancia
        reward = -dist

        self.state[action] = 1

        # Finalizar si visitó todos los nodos
        if len(self.visited) == self.n:
            terminated = True

        return self.state, reward, terminated, truncated, {}

# =========================
# DATOS (PUEDES CAMBIARLOS)
# =========================

points = np.array([
    [0, 0],
    [1, 5],
    [5, 2],
    [6, 6],
    [8, 3]
])

# =========================
# ENTRENAMIENTO
# =========================

env = TSPEnv(points)

model = PPO(
    "MlpPolicy",
    env,
    verbose=1,
    learning_rate=0.001,
    n_steps=2048,
    batch_size=64
)

print("\nEntrenando modelo RL...")
model.learn(total_timesteps=15000)

# =========================
# OBTENER RUTA
# =========================

obs, _ = env.reset()
route = [0]

terminated = False

while not terminated:
    action, _ = model.predict(obs)
    obs, reward, terminated, truncated, _ = env.step(action)

    if action not in route:
        route.append(action)

print("\nRuta RL:", route)

# =========================
# DISTANCIA TOTAL
# =========================

def total_distance(route, points):
    dist = 0
    for i in range(len(route) - 1):
        dist += np.linalg.norm(points[route[i]] - points[route[i+1]])
    return dist

rl_distance = total_distance(route, points)

print("Distancia total RL:", rl_distance)