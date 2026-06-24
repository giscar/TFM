from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from tsp_env import TSPEnv
import numpy as np
import os

np.random.seed(42)
points = np.random.rand(10, 2)

env = make_vec_env(lambda: TSPEnv(points), n_envs=4)
model = PPO('MlpPolicy', env, verbose=1)
model.learn(total_timesteps=50000)

os.makedirs('models', exist_ok=True)
model.save('models/ppo_tsp_10nodes')
print("Modelo guardado en models/ppo_tsp_10nodes.zip")
