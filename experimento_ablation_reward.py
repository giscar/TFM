import argparse
import csv
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from stable_baselines3 import PPO

from experimento_replanificacion_dinamica import (
    BASE_ADDRESSES,
    DynamicTSPEnv,
    build_distance_matrix,
    geocode,
    greedy_two_opt,
    route_distance,
    tsp_exact,
)


REWARD_MODES = ["distance_only", "distance_penalty", "full"]


def model_path(model_dir: Path, nodes: int, reward_mode: str, seed: int, timesteps: int) -> Path:
    return model_dir / f"ablation_rl_{nodes}_{reward_mode}_seed{seed}_ts{timesteps}.zip"


def train_model(
    distance_matrix: np.ndarray,
    reward_mode: str,
    seed: int,
    timesteps: int,
    model_dir: Path,
    fresh: bool,
) -> tuple[PPO, float, Path]:
    model_dir.mkdir(parents=True, exist_ok=True)
    path = model_path(model_dir, len(distance_matrix), reward_mode, seed, timesteps)

    if fresh and path.exists():
        path.unlink()

    env = DynamicTSPEnv(distance_matrix, reward_mode=reward_mode)
    start = time.perf_counter()

    if path.exists():
        model = PPO.load(path, env=env)
    else:
        model = PPO("MlpPolicy", env, verbose=0, seed=seed)
        model.learn(total_timesteps=timesteps)
        model.save(path)

    prep_time = time.perf_counter() - start
    return model, prep_time, path


def run_policy(distance_matrix: np.ndarray, model: PPO, reward_mode: str) -> tuple[list[int], float, int]:
    env = DynamicTSPEnv(distance_matrix, reward_mode=reward_mode)
    obs, _ = env.reset()
    route = [0]
    repeated_actions = 0
    done = False

    while not done:
        action, _ = model.predict(obs, deterministic=True)
        action = int(action)

        if action in route:
            repeated_actions += 1
            unvisited = [idx for idx in range(len(distance_matrix)) if idx not in route]
            if not unvisited:
                break
            action = min(unvisited, key=lambda idx: distance_matrix[env.current, idx])

        obs, _, done, _, _ = env.step(action)
        if action not in route:
            route.append(action)

    return route, route_distance(route, distance_matrix), repeated_actions


def evaluate_reward_mode(
    points: np.ndarray,
    reward_mode: str,
    seed: int,
    timesteps: int,
    model_dir: Path,
    fresh: bool,
    tsp_distance: float,
    speed_m_s: float,
) -> dict:
    distance_matrix = build_distance_matrix(points)
    model, prep_time, path = train_model(
        distance_matrix=distance_matrix,
        reward_mode=reward_mode,
        seed=seed,
        timesteps=timesteps,
        model_dir=model_dir,
        fresh=fresh,
    )

    start = time.perf_counter()
    route, distance_m, repeated_actions = run_policy(distance_matrix, model, reward_mode)
    inference_time = time.perf_counter() - start

    return {
        "reward_mode": reward_mode,
        "seed": seed,
        "timesteps": timesteps,
        "nodes": len(points),
        "route": "-".join(map(str, route)),
        "distance_m": distance_m,
        "flight_time_s": distance_m / speed_m_s,
        "inference_time_s": inference_time,
        "model_prep_time_s": prep_time,
        "error_relative_pct": ((distance_m - tsp_distance) / tsp_distance) * 100,
        "repeated_actions": repeated_actions,
        "model_path": str(path),
    }


def write_csv(rows: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    headers = [
        "reward_mode",
        "seed",
        "timesteps",
        "nodes",
        "route",
        "distance_m",
        "flight_time_s",
        "inference_time_s",
        "model_prep_time_s",
        "error_relative_pct",
        "repeated_actions",
        "model_path",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            formatted = row.copy()
            for key in [
                "distance_m",
                "flight_time_s",
                "inference_time_s",
                "model_prep_time_s",
                "error_relative_pct",
            ]:
                formatted[key] = f"{row[key]:.6f}"
            writer.writerow(formatted)


def plot_summary(rows: list[dict], tsp_distance: float, greedy_distance: float, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    modes = [row["reward_mode"] for row in rows]
    distances = [row["distance_m"] / 1000 for row in rows]
    errors = [row["error_relative_pct"] for row in rows]
    inference = [row["inference_time_s"] for row in rows]
    repeated = [row["repeated_actions"] for row in rows]

    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    colors = ["#2f80ed", "#27ae60", "#f2994a"]

    axes[0, 0].bar(modes, distances, color=colors)
    axes[0, 0].axhline(tsp_distance / 1000, color="#333333", linestyle="--", label="TSP")
    axes[0, 0].axhline(greedy_distance / 1000, color="#7f8c8d", linestyle=":", label="Greedy+2opt")
    axes[0, 0].set_title("Distancia RL por modo de recompensa")
    axes[0, 0].set_ylabel("Kilometros")
    axes[0, 0].tick_params(axis="x", rotation=15)
    axes[0, 0].legend()
    axes[0, 0].grid(axis="y", alpha=0.25)

    axes[0, 1].bar(modes, errors, color=colors)
    axes[0, 1].set_title("Error relativo frente a TSP")
    axes[0, 1].set_ylabel("Porcentaje")
    axes[0, 1].tick_params(axis="x", rotation=15)
    axes[0, 1].grid(axis="y", alpha=0.25)

    axes[1, 0].bar(modes, inference, color=colors)
    axes[1, 0].set_title("Tiempo de inferencia")
    axes[1, 0].set_ylabel("Segundos")
    axes[1, 0].tick_params(axis="x", rotation=15)
    axes[1, 0].grid(axis="y", alpha=0.25)

    axes[1, 1].bar(modes, repeated, color=colors)
    axes[1, 1].set_title("Acciones repetidas corregidas")
    axes[1, 1].set_ylabel("Cantidad")
    axes[1, 1].tick_params(axis="x", rotation=15)
    axes[1, 1].grid(axis="y", alpha=0.25)

    fig.suptitle("Ablacion de funcion de recompensa en RL", fontsize=15)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(output_dir / "ablation_reward_resumen.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_routes(points: np.ndarray, rows: list[dict], output_dir: Path) -> None:
    route_dir = output_dir / "rutas"
    route_dir.mkdir(parents=True, exist_ok=True)

    for row in rows:
        route = [int(value) for value in row["route"].split("-")]
        plt.figure(figsize=(6, 6))
        plt.scatter(points[:, 0], points[:, 1], color="#2f80ed")
        for idx, (x, y) in enumerate(points):
            label = f"{idx}"
            if idx == 0:
                label += " origen"
            plt.text(x, y, label, fontsize=9)

        for i in range(len(route) - 1):
            p1 = points[route[i]]
            p2 = points[route[i + 1]]
            plt.plot([p1[0], p2[0]], [p1[1], p2[1]], "r-", linewidth=1.8)

        plt.title(f"{row['reward_mode']} - {row['distance_m']:.0f} m")
        plt.grid(True)
        plt.savefig(route_dir / f"ruta_{row['reward_mode']}.png", dpi=160, bbox_inches="tight")
        plt.close()


def print_results(rows: list[dict], tsp_distance: float, greedy_distance: float) -> None:
    print("\n===== ABLACION DE FUNCION DE RECOMPENSA =====")
    print(f"TSP exacto      : {tsp_distance:.2f} m")
    print(f"Greedy + 2-opt : {greedy_distance:.2f} m")
    for row in rows:
        print(
            f"{row['reward_mode']:16s} | dist={row['distance_m']:10.2f} m | "
            f"infer={row['inference_time_s']:.6f}s | prep={row['model_prep_time_s']:.3f}s | "
            f"error={row['error_relative_pct']:.2f}% | repetidas={row['repeated_actions']} | "
            f"ruta={row['route']}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Experimento de ablacion para evaluar el impacto de la funcion de recompensa en RL."
    )
    parser.add_argument("--nodes", type=int, default=9)
    parser.add_argument("--timesteps", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--speed", type=float, default=10.0)
    parser.add_argument("--fresh", action="store_true", help="Entrena modelos desde cero para esta configuracion.")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--model-dir", default="modelos_ablation_reward")
    args = parser.parse_args()

    if args.nodes < 3 or args.nodes > len(BASE_ADDRESSES):
        raise ValueError(f"--nodes debe estar entre 3 y {len(BASE_ADDRESSES)}")

    labels = BASE_ADDRESSES[: args.nodes]
    points = np.array([geocode(address) for address in labels], dtype=np.float64)
    distance_matrix = build_distance_matrix(points)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_dir = Path(args.output_dir or f"graficas/ablation_reward_{timestamp}")
    model_dir = Path(args.model_dir)

    start = time.perf_counter()
    tsp_route, tsp_distance = tsp_exact(distance_matrix)
    tsp_time = time.perf_counter() - start

    start = time.perf_counter()
    greedy_route, greedy_distance = greedy_two_opt(distance_matrix)
    greedy_time = time.perf_counter() - start

    rows = []
    for mode in REWARD_MODES:
        rows.append(
            evaluate_reward_mode(
                points=points,
                reward_mode=mode,
                seed=args.seed,
                timesteps=args.timesteps,
                model_dir=model_dir,
                fresh=args.fresh,
                tsp_distance=tsp_distance,
                speed_m_s=args.speed,
            )
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(rows, output_dir / "resultados_ablation_reward.csv")
    plot_summary(rows, tsp_distance, greedy_distance, output_dir)
    plot_routes(points, rows, output_dir)

    with (output_dir / "lineas_base.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["algorithm", "route", "distance_m", "calc_time_s"])
        writer.writerow(["TSP", "-".join(map(str, tsp_route)), f"{tsp_distance:.6f}", f"{tsp_time:.6f}"])
        writer.writerow(["Greedy+2opt", "-".join(map(str, greedy_route)), f"{greedy_distance:.6f}", f"{greedy_time:.6f}"])

    print_results(rows, tsp_distance, greedy_distance)
    print(f"\nCSV: {output_dir / 'resultados_ablation_reward.csv'}")
    print(f"Lineas base: {output_dir / 'lineas_base.csv'}")
    print(f"Graficas: {output_dir}")
    print(f"Modelos RL: {model_dir}")


if __name__ == "__main__":
    main()
