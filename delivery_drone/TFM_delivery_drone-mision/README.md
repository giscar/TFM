
### 5. `mision/README.md`

```markdown
# Rama mision: Scripts de Misión, Generación de Órdenes y Menú Interactivo

## 🎯 Propósito
Proporciona scripts para ejecutar misiones de entrega, generar órdenes aleatorias, y un menú interactivo para seleccionar misiones predefinidas o aleatorias.

## 📁 Archivos Clave
- `src/mission/delivery_mission.py`: Script principal que integra geocodificación, optimización, ejecución de misión y guardado de resultados.
- `src/mission/run_mission_menu.sh`: Menú interactivo en bash para seleccionar misión fija o aleatoria.
- `src/mission/generate_random_orders.py`: Genera archivos JSON con direcciones aleatorias de un país dado.
- `src/mission/airports.csv`: Coordenadas de aeropuertos (origen) por país.
- `src/mission/orders_*.json`: Archivos JSON con órdenes predefinidas (Malta, Bogotá, Villavicencio).

## 🚀 Uso del Menú
```bash
cd /ros2_ws
source install/setup.bash
export MAPBOX_TOKEN="sk.eyJ1..."
./src/mission/run_mission_menu.sh
