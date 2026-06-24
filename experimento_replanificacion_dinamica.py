import argparse
import csv
import os
import time
from dataclasses import dataclass
from itertools import permutations
from pathlib import Path
from urllib.parse import quote

import gymnasium as gym
import matplotlib.pyplot as plt
import numpy as np
import requests
from geopy.distance import geodesic
from gymnasium import spaces
from stable_baselines3 import PPO


MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN", "").strip()

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
    "Chorrillos Lima": [-77.0247, -12.1724],
    "Jesus Maria Lima": [-77.0450, -12.0750],
}

BASE_ADDRESSES = [
    "Lima Peru",
    "Miraflores Lima",
    "San Isidro Lima",
    "Surco Lima",
    "Callao Peru",
    "La Molina Lima",
    "Barranco Lima",
    "San Borja Lima",
    "Los Olivos Lima",
    "Comas Lima",
]


@dataclass
class RouteResult:
    scenario: str
    event: str
    algorithm: str
    nodes: int
    route: list[int]
    distance_m: float
    flight_time_s: float
    calc_time_s: float
    model_prep_time_s: float = 0.0
    error_relative_pct: float | None = None
    speedup_vs_tsp: float | None = None


def geocode(address: str) -> list[float]:
    fallback = FALLBACK_COORDS.get(address)
    if not MAPBOX_TOKEN:
        if fallback is None:
            raise ValueError(f"No existe coordenada local para: {address}")
        return fallback

    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{quote(address)}.json"
    params = {"access_token": MAPBOX_TOKEN, "limit": 1}

    try:
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
    except requests.RequestException:
        if fallback is not None:
            return fallback
        raise

    if response.status_code != 200 or not data.get("features"):
        if fallback is not None:
            return fallback
        raise ValueError(f"No se pudo geocodificar: {address}")

    return data["features"][0]["geometry"]["coordinates"]


def distance_real(p1: np.ndarray, p2: np.ndarray) -> float:
    return geodesic((p1[1], p1[0]), (p2[1], p2[0])).meters


def build_distance_matrix(points: np.ndarray) -> np.ndarray:
    n = len(points)
    matrix = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        for j in range(i + 1, n):
            dist = distance_real(points[i], points[j])
            matrix[i, j] = dist
            matrix[j, i] = dist
    return matrix


def route_distance(route: list[int], distance_matrix: np.ndarray) -> float:
    return sum(distance_matrix[route[i], route[i + 1]] for i in range(len(route) - 1))


def tsp_exact(distance_matrix: np.ndarray, forced_first: int | None = None) -> tuple[list[int], float]:
    n = len(distance_matrix)
    if forced_first is None:
        fixed_prefix = [0]
        candidates = [idx for idx in range(1, n)]
    else:
        fixed_prefix = [0, forced_first]
        candidates = [idx for idx in range(1, n) if idx != forced_first]

    best_route = None
    best_distance = float("inf")
    for perm in permutations(candidates):
        route = fixed_prefix + list(perm)
        dist = route_distance(route, distance_matrix)
        if dist < best_distance:
            best_route = route
            best_distance = dist

    return best_route or [0], best_distance


def greedy_route(distance_matrix: np.ndarray, forced_first: int | None = None) -> list[int]:
    n = len(distance_matrix)
    route = [0]
    unvisited = set(range(1, n))

    if forced_first is not None and forced_first in unvisited:
        route.append(forced_first)
        unvisited.remove(forced_first)

    while unvisited:
        current = route[-1]
        next_node = min(unvisited, key=lambda idx: distance_matrix[current, idx])
        route.append(next_node)
        unvisited.remove(next_node)

    return route


def two_opt(route: list[int], distance_matrix: np.ndarray, fixed_prefix_len: int = 1) -> list[int]:
    best_route = route[:]
    best_distance = route_distance(best_route, distance_matrix)
    improved = True

    while improved:
        improved = False
        for i in range(fixed_prefix_len, len(best_route) - 2):
            for j in range(i + 1, len(best_route) - 1):
                candidate = best_route[:i] + best_route[i : j + 1][::-1] + best_route[j + 1 :]
                candidate_distance = route_distance(candidate, distance_matrix)
                if candidate_distance < best_distance:
                    best_route = candidate
                    best_distance = candidate_distance
                    improved = True
                    break
            if improved:
                break

    return best_route


def greedy_two_opt(distance_matrix: np.ndarray, forced_first: int | None = None) -> tuple[list[int], float]:
    route = greedy_route(distance_matrix, forced_first=forced_first)
    fixed_prefix_len = 2 if forced_first is not None else 1
    route = two_opt(route, distance_matrix, fixed_prefix_len=fixed_prefix_len)
    return route, route_distance(route, distance_matrix)


class DynamicTSPEnv(gym.Env):
    def __init__(self, distance_matrix: np.ndarray, reward_mode: str = "full"):
        super().__init__()
        self.distance_matrix = distance_matrix
        self.n = len(distance_matrix)
        self.reward_mode = reward_mode
        self.action_space = spaces.Discrete(self.n)
        self.observation_space = spaces.Box(low=0, high=1, shape=(self.n,), dtype=np.float32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current = 0
        self.visited = [0]
        self.state = np.zeros(self.n, dtype=np.float32)
        self.state[0] = 1
        return self.state, {}

    def _reward(self, dist: float, repeated: bool, completed: bool) -> float:
        if repeated:
            return -100.0

        dist_norm = dist / 10000
        reward = -dist_norm

        if self.reward_mode in {"distance_penalty", "full"} and dist > 20000:
            reward -= 0.5

        if self.reward_mode == "full":
            reward += 0.1 / (dist_norm + 0.001)
            if completed:
                reward += 5.0

        return float(reward)

    def step(self, action):
        action = int(action)
        if action in self.visited:
            return self.state, self._reward(0, repeated=True, completed=False), False, False, {}

        prev = self.current
        self.current = action
        self.visited.append(action)
        self.state[action] = 1

        completed = len(self.visited) == self.n
        dist = self.distance_matrix[prev, action]
        return self.state, self._reward(dist, repeated=False, completed=completed), completed, False, {}


def train_or_load_rl(
    distance_matrix: np.ndarray,
    model_dir: Path,
    reward_mode: str,
    timesteps: int,
    refine_timesteps: int,
    seed: int,
) -> PPO:
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / f"modelo_rl_dynamic_{len(distance_matrix)}_{reward_mode}.zip"
    env = DynamicTSPEnv(distance_matrix, reward_mode=reward_mode)

    if model_path.exists():
        model = PPO.load(model_path, env=env)
        if refine_timesteps > 0:
            model.learn(total_timesteps=refine_timesteps)
            model.save(model_path)
        return model

    model = PPO("MlpPolicy", env, verbose=0, seed=seed)
    model.learn(total_timesteps=timesteps)
    model.save(model_path)
    return model


def run_rl_route(
    distance_matrix: np.ndarray,
    model: PPO,
    reward_mode: str,
    forced_first: int | None = None,
) -> tuple[list[int], float]:
    env = DynamicTSPEnv(distance_matrix, reward_mode=reward_mode)
    obs, _ = env.reset()
    route = [0]

    if forced_first is not None:
        obs, _, done, _, _ = env.step(forced_first)
        route.append(forced_first)
        if done:
            return route, route_distance(route, distance_matrix)

    done = False
    while not done:
        action, _ = model.predict(obs, deterministic=True)
        action = int(action)

        if action in route:
            unvisited = [idx for idx in range(len(distance_matrix)) if idx not in route]
            if not unvisited:
                break
            action = min(unvisited, key=lambda idx: distance_matrix[env.current, idx])

        obs, _, done, _, _ = env.step(action)
        if action not in route:
            route.append(action)

    return route, route_distance(route, distance_matrix)


def evaluate_algorithm(
    scenario: str,
    event: str,
    algorithm: str,
    points: np.ndarray,
    distance_matrix: np.ndarray,
    speed_m_s: float,
    max_exact_nodes: int,
    model_dir: Path,
    reward_mode: str,
    timesteps: int,
    refine_timesteps: int,
    seed: int,
    forced_first: int | None = None,
) -> RouteResult | None:
    model_prep_time = 0.0

    if algorithm == "TSP":
        if len(points) > max_exact_nodes:
            return None
        start = time.perf_counter()
        route, dist = tsp_exact(distance_matrix, forced_first=forced_first)
    elif algorithm == "Greedy+2opt":
        start = time.perf_counter()
        route, dist = greedy_two_opt(distance_matrix, forced_first=forced_first)
    elif algorithm == "RL":
        model_start = time.perf_counter()
        model = train_or_load_rl(
            distance_matrix,
            model_dir=model_dir,
            reward_mode=reward_mode,
            timesteps=timesteps,
            refine_timesteps=refine_timesteps,
            seed=seed,
        )
        model_prep_time = time.perf_counter() - model_start
        start = time.perf_counter()
        route, dist = run_rl_route(distance_matrix, model, reward_mode=reward_mode, forced_first=forced_first)
    else:
        raise ValueError(f"Algoritmo no soportado: {algorithm}")

    calc_time = time.perf_counter() - start
    return RouteResult(
        scenario=scenario,
        event=event,
        algorithm=algorithm,
        nodes=len(points),
        route=route,
        distance_m=dist,
        flight_time_s=dist / speed_m_s,
        calc_time_s=calc_time,
        model_prep_time_s=model_prep_time,
    )


def apply_event(
    points: np.ndarray,
    labels: list[str],
    event: str,
    new_address: str,
    cancel_index: int,
    priority_index: int,
) -> tuple[np.ndarray, list[str], int | None, str]:
    if event == "baseline":
        return points.copy(), labels[:], None, "Ruta inicial sin evento operativo."

    if event == "add":
        new_point = np.array([geocode(new_address)], dtype=np.float64)
        new_points = np.vstack([points, new_point])
        return new_points, labels + [new_address], None, f"Pedido agregado: {new_address}."

    if event == "cancel":
        if cancel_index <= 0 or cancel_index >= len(points):
            raise ValueError("cancel_index debe estar entre 1 y n-1 para conservar el origen.")
        new_points = np.delete(points, cancel_index, axis=0)
        new_labels = [label for idx, label in enumerate(labels) if idx != cancel_index]
        return new_points, new_labels, None, f"Pedido cancelado: {labels[cancel_index]}."

    if event == "priority":
        if priority_index <= 0 or priority_index >= len(points):
            raise ValueError("priority_index debe estar entre 1 y n-1 para conservar el origen.")
        return points.copy(), labels[:], priority_index, f"Prioridad operativa para: {labels[priority_index]}."

    raise ValueError(f"Evento no soportado: {event}")


def enrich_relative_metrics(results: list[RouteResult]) -> None:
    tsp_by_key = {
        (r.scenario, r.event): r
        for r in results
        if r.algorithm == "TSP"
    }
    for result in results:
        baseline = tsp_by_key.get((result.scenario, result.event))
        if not baseline or baseline.distance_m == 0 or result.algorithm == "TSP":
            result.error_relative_pct = 0.0 if result.algorithm == "TSP" else None
            result.speedup_vs_tsp = 1.0 if result.algorithm == "TSP" else None
            continue
        result.error_relative_pct = ((result.distance_m - baseline.distance_m) / baseline.distance_m) * 100
        result.speedup_vs_tsp = baseline.calc_time_s / result.calc_time_s if result.calc_time_s > 0 else None


def write_results_csv(results: list[RouteResult], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "scenario",
            "event",
            "algorithm",
            "nodes",
            "route",
            "distance_m",
            "flight_time_s",
            "calc_time_s",
            "model_prep_time_s",
            "error_relative_pct",
            "speedup_vs_tsp",
        ])
        for result in results:
            writer.writerow([
                result.scenario,
                result.event,
                result.algorithm,
                result.nodes,
                "-".join(map(str, result.route)),
                f"{result.distance_m:.4f}",
                f"{result.flight_time_s:.4f}",
                f"{result.calc_time_s:.6f}",
                f"{result.model_prep_time_s:.6f}",
                "" if result.error_relative_pct is None else f"{result.error_relative_pct:.4f}",
                "" if result.speedup_vs_tsp is None else f"{result.speedup_vs_tsp:.4f}",
            ])


def plot_event_results(results: list[RouteResult], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    grouped: dict[tuple[str, str], list[RouteResult]] = {}
    for result in results:
        grouped.setdefault((result.scenario, result.event), []).append(result)

    for (scenario, event), items in grouped.items():
        labels = [r.algorithm for r in items]
        distances = [r.distance_m for r in items]
        times = [r.calc_time_s for r in items]

        fig, axes = plt.subplots(1, 2, figsize=(11, 4))
        axes[0].bar(labels, distances, color=["#2f80ed", "#27ae60", "#f2994a"][: len(labels)])
        axes[0].set_title(f"Distancia - {event}")
        axes[0].set_ylabel("Metros")
        axes[0].tick_params(axis="x", rotation=15)

        axes[1].bar(labels, times, color=["#2f80ed", "#27ae60", "#f2994a"][: len(labels)])
        axes[1].set_title(f"Tiempo de cálculo - {event}")
        axes[1].set_ylabel("Segundos")
        axes[1].tick_params(axis="x", rotation=15)

        fig.suptitle(scenario)
        fig.tight_layout()
        fig.savefig(output_dir / f"comparacion_{event}.png", dpi=160, bbox_inches="tight")
        plt.close(fig)


def plot_routes(points: np.ndarray, labels: list[str], results: list[RouteResult], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for result in results:
        plt.figure(figsize=(6, 6))
        plt.scatter(points[:, 0], points[:, 1], color="#2f80ed")
        for idx, (x, y) in enumerate(points):
            label = f"{idx}"
            if idx == 0:
                label += " origen"
            plt.text(x, y, label, fontsize=9)

        for i in range(len(result.route) - 1):
            p1 = points[result.route[i]]
            p2 = points[result.route[i + 1]]
            plt.plot([p1[0], p2[0]], [p1[1], p2[1]], "r-", linewidth=1.8)

        plt.title(f"{result.algorithm} - {result.event} - {result.distance_m:.0f} m")
        plt.grid(True)
        plt.savefig(output_dir / f"ruta_{result.event}_{result.algorithm.lower().replace('+', '_')}.png", dpi=160, bbox_inches="tight")
        plt.close()


def print_results(results: list[RouteResult]) -> None:
    print("\n===== RESULTADOS DE REPLANIFICACION DINAMICA =====")
    for r in results:
        error = "NA" if r.error_relative_pct is None else f"{r.error_relative_pct:.2f}%"
        speedup = "NA" if r.speedup_vs_tsp is None else f"{r.speedup_vs_tsp:.2f}x"
        print(
            f"{r.event:8s} | {r.algorithm:11s} | nodos={r.nodes:2d} | "
            f"dist={r.distance_m:10.2f} m | calc={r.calc_time_s:9.6f}s | "
            f"prep={r.model_prep_time_s:8.4f}s | error={error:>8s} | "
            f"speedup={speedup:>10s} | ruta={r.route}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Experimento de replanificacion dinamica para rutas de drones con TSP, Greedy+2opt y RL."
    )
    parser.add_argument("--nodes", type=int, default=9, help="Nodos iniciales. Use 9 para que add llegue a 10 con TSP exacto.")
    parser.add_argument("--events", nargs="+", default=["baseline", "add", "cancel", "priority"], choices=["baseline", "add", "cancel", "priority", "all"])
    parser.add_argument("--new-address", default="Chorrillos Lima", help="Direccion usada para el evento add.")
    parser.add_argument("--cancel-index", type=int, default=3, help="Indice de nodo cancelado. Debe ser mayor que 0.")
    parser.add_argument("--priority-index", type=int, default=4, help="Indice de nodo priorizado. Debe ser mayor que 0.")
    parser.add_argument("--max-exact-nodes", type=int, default=10, help="Maximo de nodos para ejecutar TSP exacto.")
    parser.add_argument("--timesteps", type=int, default=20000, help="Timesteps iniciales para entrenar RL si no existe modelo.")
    parser.add_argument("--refine-timesteps", type=int, default=0, help="Timesteps para refinar modelos RL existentes.")
    parser.add_argument("--reward-mode", default="full", choices=["distance_only", "distance_penalty", "full"])
    parser.add_argument("--speed", type=float, default=10.0, help="Velocidad asumida del dron en m/s.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()

    if args.nodes < 3 or args.nodes > len(BASE_ADDRESSES):
        raise ValueError(f"--nodes debe estar entre 3 y {len(BASE_ADDRESSES)}")

    events = ["baseline", "add", "cancel", "priority"] if "all" in args.events else args.events
    labels = BASE_ADDRESSES[: args.nodes]
    points = np.array([geocode(address) for address in labels], dtype=np.float64)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_dir = Path(args.output_dir or f"graficas/replanificacion_{timestamp}")
    model_dir = Path("modelos_replanificacion")

    all_results: list[RouteResult] = []
    event_points: dict[str, tuple[np.ndarray, list[str]]] = {}

    for event in events:
        current_points, current_labels, forced_first, description = apply_event(
            points,
            labels,
            event=event,
            new_address=args.new_address,
            cancel_index=args.cancel_index,
            priority_index=args.priority_index,
        )
        event_points[event] = (current_points, current_labels)
        distance_matrix = build_distance_matrix(current_points)

        print(f"\nEvento: {event} | {description} | nodos={len(current_points)}")
        for algorithm in ["TSP", "Greedy+2opt", "RL"]:
            result = evaluate_algorithm(
                scenario="dynamic_replanning",
                event=event,
                algorithm=algorithm,
                points=current_points,
                distance_matrix=distance_matrix,
                speed_m_s=args.speed,
                max_exact_nodes=args.max_exact_nodes,
                model_dir=model_dir,
                reward_mode=args.reward_mode,
                timesteps=args.timesteps,
                refine_timesteps=args.refine_timesteps,
                seed=args.seed,
                forced_first=forced_first,
            )
            if result is None:
                print(f"  {algorithm}: omitido por superar max_exact_nodes={args.max_exact_nodes}")
                continue
            all_results.append(result)

    enrich_relative_metrics(all_results)
    write_results_csv(all_results, output_dir / "resultados_replanificacion.csv")
    plot_event_results(all_results, output_dir)

    for event, (current_points, current_labels) in event_points.items():
        plot_routes(
            current_points,
            current_labels,
            [r for r in all_results if r.event == event],
            output_dir / "rutas",
        )

    print_results(all_results)
    print(f"\nCSV: {output_dir / 'resultados_replanificacion.csv'}")
    print(f"Graficas: {output_dir}")
    print(f"Modelos RL: {model_dir}")


if __name__ == "__main__":
    main()
