#!/usr/bin/env python3
import math
from itertools import permutations

class RouteOptimizer:
    def __init__(self):
        self.waypoints = []

    def add_waypoint(self, x, y, z):
        self.waypoints.append((x, y, z))

    def distance(self, p1, p2):
        return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2 + (p1[2]-p2[2])**2)

    def total_distance(self, route, start_point):
        if not route:
            return 0.0
        total = self.distance(start_point, route[0])
        for i in range(len(route)-1):
            total += self.distance(route[i], route[i+1])
        total += self.distance(route[-1], start_point)
        return total

    def optimize_tsp(self, start_point):
        """Exacto (≤8) o greedy + 2-opt (>8)"""
        if len(self.waypoints) <= 8:
            best_route = None
            best_dist = float('inf')
            for perm in permutations(self.waypoints):
                dist = self.total_distance(perm, start_point)
                if dist < best_dist:
                    best_dist = dist
                    best_route = perm
            return best_route, best_dist
        else:
            route = self.greedy_route(start_point)
            route = self.two_opt(route, start_point)
            dist = self.total_distance(route, start_point)
            return route, dist

    def greedy_route(self, start_point):
        unvisited = self.waypoints[:]
        route = []
        current = start_point
        while unvisited:
            next_wp = min(unvisited, key=lambda wp: self.distance(current, wp))
            route.append(next_wp)
            current = next_wp
            unvisited.remove(next_wp)
        return route

    def two_opt(self, route, start_point):
        best = route[:]
        best_dist = self.total_distance(best, start_point)
        improved = True
        while improved:
            improved = False
            for i in range(1, len(best)-2):
                for j in range(i+1, len(best)-1):
                    new_route = best[:i] + best[i:j+1][::-1] + best[j+1:]
                    new_dist = self.total_distance(new_route, start_point)
                    if new_dist < best_dist:
                        best = new_route
                        best_dist = new_dist
                        improved = True
                        break
                if improved:
                    break
        return best

if __name__ == "__main__":
    # Prueba rápida
    opt = RouteOptimizer()
    opt.add_waypoint(5,0,-2.5)
    opt.add_waypoint(0,5,-2.5)
    opt.add_waypoint(3,3,-2.5)
    start = (0,0,-2.5)
    route, dist = opt.optimize_tsp(start)
    print("Ruta optimizada:", route)
    print("Distancia:", dist)
