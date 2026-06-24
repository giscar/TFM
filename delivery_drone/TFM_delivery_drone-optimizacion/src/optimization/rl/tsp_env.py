import gymnasium as gym
from gymnasium import spaces
import numpy as np

class TSPEnv(gym.Env):
    def __init__(self, points, max_steps=None):
        super().__init__()
        self.points = np.array(points)
        self.n = len(points)
        self.max_steps = max_steps or self.n
        self.action_space = spaces.Discrete(self.n)
        self.observation_space = spaces.Box(low=0, high=1, shape=(self.n,), dtype=np.uint8)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.visited = np.zeros(self.n, dtype=np.uint8)
        self.current = np.random.randint(self.n)
        self.visited[self.current] = 1
        self.steps = 1
        self.total_distance = 0.0
        return self._get_obs(), {}

    def _get_obs(self):
        return self.visited.copy()

    def step(self, action):
        if self.visited[action] == 1:
            reward = -100.0
            terminated = True
            truncated = False
            return self._get_obs(), reward, terminated, truncated, {}
        dist = np.linalg.norm(self.points[self.current] - self.points[action])
        self.total_distance += dist
        self.visited[action] = 1
        self.current = action
        self.steps += 1
        reward = -dist / 10000.0
        if self.steps == self.n:
            dist_back = np.linalg.norm(self.points[self.current] - self.points[0])
            self.total_distance += dist_back
            reward = -dist_back / 10000.0 + 5.0
            terminated = True
        else:
            terminated = False
        return self._get_obs(), reward, terminated, False, {}
