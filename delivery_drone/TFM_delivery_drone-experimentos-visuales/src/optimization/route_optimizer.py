#!/usr/bin/env python3
"""
Módulo para optimización de rutas de entrega.
Implementa algoritmos para encontrar la ruta más eficiente.
"""

import math
from itertools import permutations

class RouteOptimizer:
    def __init__(self):
        self.waypoints = []
        
    def add_waypoint(self, x, y, z):
        """Añade un punto de paso a la misión."""
        self.waypoints.append((x, y, z))
        
    def distance(self, p1, p2):
        """Calcula distancia euclidiana entre dos puntos 3D."""
        return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2 + (p1[2]-p2[2])**2)
    
    def optimize_tsp(self, start_point):
        """
        Optimiza ruta usando algoritmo de fuerza bruta para TSP.
        Para N pequeños (N <= 8). Para N grandes, usar heurísticas.
        
        Args:
            start_point: (x, y, z) punto de inicio y fin
            
        Returns:
            best_route: tupla con el orden óptimo de waypoints
            best_distance: distancia total optimizada
        """
        if len(self.waypoints) > 8:
            print("⚠️ Demasiados puntos para fuerza bruta, usando heurística greedy")
            return self.optimize_greedy(start_point)
            
        best_route = None
        best_distance = float('inf')
        
        for perm in permutations(self.waypoints):
            current = start_point
            total_dist = 0
            visited = []
            
            for wp in perm:
                total_dist += self.distance(current, wp)
                visited.append(wp)
                current = wp
                
            # Regresar al inicio
            total_dist += self.distance(current, start_point)
            
            if total_dist < best_distance:
                best_distance = total_dist
                best_route = perm
                
        return best_route, best_distance
    
    def optimize_greedy(self, start_point):
        """Heurística greedy para muchos puntos."""
        unvisited = list(self.waypoints)
        route = []
        current = start_point
        total_dist = 0
        
        while unvisited:
            # Encontrar el punto no visitado más cercano
            next_wp = min(unvisited, key=lambda wp: self.distance(current, wp))
            route.append(next_wp)
            total_dist += self.distance(current, next_wp)
            current = next_wp
            unvisited.remove(next_wp)
            
        # Regresar al inicio
        total_dist += self.distance(current, start_point)
        
        return route, total_dist
    
    def optimize_2opt(self, route):
        """
        Mejora una ruta usando algoritmo 2-opt.
        """
        improved = True
        best_route = list(route)
        best_distance = self.calculate_route_distance(best_route)
        
        while improved:
            improved = False
            for i in range(1, len(best_route)-2):
                for j in range(i+1, len(best_route)-1):
                    # Crear nueva ruta intercambiando segmento
                    new_route = best_route[:i] + best_route[i:j+1][::-1] + best_route[j+1:]
                    new_distance = self.calculate_route_distance(new_route)
                    
                    if new_distance < best_distance:
                        best_route = new_route
                        best_distance = new_distance
                        improved = True
                        break
                if improved:
                    break
                    
        return best_route, best_distance
    
    def calculate_route_distance(self, route):
        """Calcula distancia total de una ruta."""
        if not route:
            return 0
            
        total = 0
        for i in range(len(route)-1):
            total += self.distance(route[i], route[i+1])
        return total

if __name__ == "__main__":
    # Prueba con 5 puntos
    opt = RouteOptimizer()
    opt.add_waypoint(5, 0, -2.5)
    opt.add_waypoint(8, 3, -2.5)
    opt.add_waypoint(3, 5, -2.5)
    opt.add_waypoint(0, 2, -2.5)
    opt.add_waypoint(2, -2, -2.5)
    
    start = (0, 0, -2.5)
    
    print("=== OPTIMIZACIÓN DE RUTA ===")
    print(f"Waypoints: {opt.waypoints}")
    
    route, dist = opt.optimize_tsp(start)
    print(f"\n📊 Ruta optimizada ({len(route)} puntos):")
    for i, wp in enumerate(route):
        print(f"  {i+1}. {wp}")
    print(f"Distancia total: {dist:.2f}m")
