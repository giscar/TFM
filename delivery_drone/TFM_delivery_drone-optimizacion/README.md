
### 4. `optimizacion/README.md`

```markdown
# Rama optimizacion: Algoritmos de Optimización de Rutas (TSP)

## 🎯 Propósito
Contiene el algoritmo de optimización de rutas basado en el Problema del Viajante (TSP), utilizado como referencia para comparar con el modelo de aprendizaje por refuerzo (RL).

## 📁 Archivos Clave
- `src/optimization/route_optimizer.py`: Implementación del TSP exacto (fuerza bruta) y heurístico (greedy + 2‑opt).

## 🧠 Descripción del Algoritmo
- **Fuerza bruta**: Evalúa todas las permutaciones, garantiza solución óptima para n ≤ 8.
- **Greedy**: Construye ruta eligiendo el vecino más cercano en cada paso.
- **2‑opt**: Mejora local invirtiendo segmentos de la ruta para eliminar cruces.

## 📈 Complejidad
- Fuerza bruta: O(n!)
- Greedy + 2‑opt: O(n²)

## 📊 Resultados de Escalabilidad
| Nodos | TSP Tiempo (s) | Error RL (%) |
|-------|----------------|--------------|
| 5 | 0.019 | 59.30% |
| 8 | 4.78 | 81.76% |
| 10 | 493.55 | 75.56% |

## 🚀 Uso
```python
from route_optimizer import RouteOptimizer

opt = RouteOptimizer()
opt.add_waypoint(5, 0, -2.5)
opt.add_waypoint(0, 5, -2.5)
route, dist = opt.optimize_tsp((0, 0, -2.5))
print(f"Óptimo: {route}, Distancia: {dist:.2f} m")

## 🤖 Aprendizaje por Refuerzo (RL)
Además del algoritmo TSP clásico, esta rama incluye un agente basado en **Proximal Policy Optimization (PPO)** para resolver el TSP de forma aproximada pero muy rápida. Los detalles se encuentran en la carpeta `optimization/rl/`.

**Resultados comparativos (10 nodos)**
| Método | Distancia (m) | Tiempo (s) |
|--------|---------------|------------|
| TSP exacto | 122,085.68 | 493.55 |
| RL (PPO) | 214,333.46 | 0.0099 |

El RL es ~50,000 veces más rápido, adecuado para entornos dinámicos.

## 🤖 Aprendizaje por Refuerzo (RL)
Además del algoritmo TSP clásico, esta rama incluye un agente basado en **Proximal Policy Optimization (PPO)** para resolver el TSP de forma aproximada pero muy rápida. Los detalles se encuentran en la carpeta `optimization/rl/`.

**Resultados comparativos (10 nodos)**
| Método | Distancia (m) | Tiempo (s) |
|--------|---------------|------------|
| TSP exacto | 122,085.68 | 493.55 |
| RL (PPO) | 214,333.46 | 0.0099 |

El RL es ~50,000 veces más rápido, adecuado para entornos dinámicos.
