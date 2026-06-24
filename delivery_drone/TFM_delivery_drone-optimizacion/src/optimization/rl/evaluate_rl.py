from stable_baselines3 import PPO
from tsp_env import TSPEnv
import numpy as np
import time
from itertools import permutations

def exact_tsp(points):
    best_dist = np.inf
    best_route = None
    start = points[0]
    others = points[1:]
    for perm in permutations(others):
        route = [start] + list(perm)
        dist = sum(np.linalg.norm(route[i] - route[i+1]) for i in range(len(route)-1))
        dist += np.linalg.norm(route[-1] - start)
        if dist < best_dist:
            best_dist = dist
            best_route = route
    return best_route, best_dist

def evaluate_rl(model, env, episodes=10):
    total_dist = 0.0
    for _ in range(episodes):
        obs, _ = env.reset()
        done = False
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, _, _ = env.step(action)
        total_dist += env.total_distance
    return total_dist / episodes

if __name__ == "__main__":
    np.random.seed(42)
    points = np.random.rand(10, 2)

    start_time = time.time()
    exact_route, exact_dist = exact_tsp(points)
    exact_time = time.time() - start_time

    env = TSPEnv(points)
    model = PPO.load('models/ppo_tsp_10nodes')
    start_time = time.time()
    avg_rl_dist = evaluate_rl(model, env, episodes=10)
    rl_time = time.time() - start_time

    print(f"TSP exacto: Distancia = {exact_dist:.2f}, Tiempo = {exact_time:.4f}s")
    print(f"RL (PPO): Distancia promedio = {avg_rl_dist:.2f}, Tiempo inferencia = {rl_time:.4f}s")
    print(f"Error relativo RL: {(avg_rl_dist - exact_dist)/exact_dist*100:.2f}%")

    import csv
    with open('results/rl_comparison.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Metodo', 'Distancia', 'Tiempo (s)', 'Error (%)'])
        writer.writerow(['TSP exacto', exact_dist, exact_time, 0])
        writer.writerow(['RL (PPO)', avg_rl_dist, rl_time, (avg_rl_dist - exact_dist)/exact_dist*100])
