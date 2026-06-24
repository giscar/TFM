
### 2. `add-control/README.md`

```markdown
# Rama add-control: Control OFFBOARD y Optimización TSP

## 🎯 Propósito
Esta rama contiene el nodo de control autónomo para el dron (`offboard_control.py`) y la implementación del algoritmo de optimización de rutas basado en el Problema del Viajante (TSP) con mejora 2‑opt.

## 📁 Archivos Clave
- `src/control/offboard_control.py`: Nodo ROS 2 que publica setpoints de posición a 20 Hz, gestiona el modo OFFBOARD e incluye un fallback de armado/despegue.
- `src/optimization/route_optimizer.py`: Algoritmo TSP exacto (fuerza bruta) para ≤8 puntos y heurística greedy + 2‑opt para más puntos.

## 🧠 Algoritmo TSP
- **Exacto**: Permutaciones, complejidad O(n!) – usado para n ≤ 8.
- **Heurístico**: Greedy (vecino más cercano) + mejora 2‑opt, complejidad O(n²).

## 📊 Evaluación
| Nodos | TSP Distancia (m) | TSP Tiempo (s) |
|-------|-------------------|----------------|
| 5 | 96,915.91 | 0.019 |
| 8 | 101,992.90 | 4.78 |
| 10 | 122,085.68 | 493.55 |

## 🚀 Uso
```bash
# Ejecutar nodo de control (dentro del contenedor)
ros2 run offboard_pkg offboard_control

# Ejecutar optimizador TSP desde script de misión
python3 src/mission/delivery_mission.py --json <ruta_json> --ref-lat <lat> --ref-lon <lon>
