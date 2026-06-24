# TFM: Sistema de Simulación y Optimización de Rutas para Drones de Reparto

## 📌 Descripción
Este repositorio contiene el desarrollo del Trabajo Fin de Máster para la Maestría en Inteligencia Artificial. Implementa un sistema completo de simulación y control autónomo para un dron de reparto utilizando **ROS 2 Jazzy**, **PX4 Autopilot**, **Gazebo Harmonic**, **Foxglove** y **aprendizaje por refuerzo (RL)**. El sistema se despliega en una máquina virtual de Oracle Cloud y se automatiza mediante scripts `tmux`.

## 🏗️ Arquitectura del Sistema
- **Infraestructura**: Oracle Cloud VM (Ubuntu 22.04, IP pública `130.61.118.51`)
- **Simulación**: PX4 SITL + Gazebo Harmonic (modelo `x500`)
- **Middleware**: ROS 2 Jazzy + Micro XRCE-DDS Agent (puerto 8888)
- **Control autónomo**: Nodo `offboard_control.py` (setpoints a 20 Hz)
- **Geolocalización**: Mapbox API (geocodificación)
- **Optimización**: TSP (exacto ≤8 puntos, greedy+2‑opt >8) y modelo RL (PPO)
- **Visualización**: Foxglove Desktop (panel 3D y mapa satelital) + dashboard web (puerto 8080)
- **Automatización**: Script `start_all.sh` (tmux, 6 ventanas)

## 📂 Estructura de Ramas
| Rama | Propósito |
|------|-----------|
| `main` | Rama estable, documentación, script de inicio, Dockerfile |
| `add-control` | Nodo de control OFFBOARD y algoritmo TSP |
| `geo` | Módulos de geocodificación y conversión de coordenadas |
| `optimizacion` | Optimizador de rutas (TSP exacto y heurístico) |
| `mision` | Scripts de misión, generación de órdenes, menú interactivo |
| `experimentos-visuales` | Dashboard web y resultados CSV |

## 🚀 Inicio rápido
```bash
# Clonar repositorio con submódulos
git clone --recursive https://github.com/perezsandram22/TFM_delivery_drone.git
cd TFM_delivery_drone

# Construir imagen Docker
cd docker
docker build -t drone_ros2_jazzy .
cd ..

# Crear contenedor
docker run -itd --name drone_container --restart always --network host drone_ros2_jazzy

# Copiar código fuente al contenedor (o clonar dentro)
docker cp src/ drone_container:/ros2_ws/

# Ejecutar sistema
./scripts/start_all.sh
