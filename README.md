# 🚀 Instalación y Ejecución del Proyecto

Este documento describe los pasos necesarios para configurar el entorno, instalar las dependencias y ejecutar el sistema de optimización de rutas basado en TSP y aprendizaje por refuerzo (RL).

---

## 📦 1. Creación del entorno de trabajo

Se recomienda el uso de un entorno virtual para evitar conflictos de dependencias.

```bash
conda create -n rl_tfm python=3.10 -y
conda activate rl_tfm
```

**Explicación:**
Se crea un entorno aislado con Python 3.10, asegurando compatibilidad con las librerías utilizadas (especialmente Gymnasium y Stable-Baselines3).

---

## 📚 2. Instalación de dependencias

```bash
pip install numpy gymnasium stable-baselines3 matplotlib geopy requests
```

**Explicación de librerías:**

* **numpy** → Manejo de datos numéricos y estructuras de coordenadas
* **gymnasium** → Creación del entorno de simulación para RL
* **stable-baselines3** → Implementación del algoritmo PPO
* **matplotlib** → Visualización de rutas y resultados
* **geopy** → Cálculo de distancias reales entre coordenadas geográficas
* **requests** → Consumo de la API de geocodificación (Mapbox)

---

## 🌍 3. Configuración de Mapbox

Antes de ejecutar el sistema, es necesario configurar un token de acceso a la API de Mapbox.

```python
MAPBOX_TOKEN = "TU_TOKEN_AQUI"
```

**Explicación:**
Este token permite convertir direcciones reales en coordenadas geográficas (latitud y longitud), lo cual es fundamental para trabajar con datos reales en el problema de optimización.

---

## ▶️ 4. Ejecución del programa

```bash
python tsp_rl_mejorado_mapbox.py
```

**Explicación:**
Este comando ejecuta el sistema completo, el cual realiza las siguientes acciones:

1. Obtiene coordenadas reales a partir de direcciones
2. Calcula la ruta óptima mediante TSP
3. Entrena un modelo de aprendizaje por refuerzo (PPO)
4. Genera una ruta alternativa mediante RL
5. Calcula distancias reales (en metros)
6. Estima tiempos de vuelo del dron
7. Muestra resultados comparativos
8. Genera visualizaciones gráficas de las rutas

---

## 📊 5. Resultados esperados

Al finalizar la ejecución, se obtendrán resultados similares a:

```text
===== RESULTADOS =====
TSP -> Distancia: XXXX m | Vuelo: XXXX s | Calc: XXXX s
RL  -> Distancia: XXXX m | Vuelo: XXXX s | Calc: XXXX s
```

Además, se generarán:

* Gráficas de las rutas (TSP vs RL)
* Gráfica comparativa de distancias

---

## ⚠️ 6. Consideraciones importantes

* El tiempo de cálculo corresponde al procesamiento del algoritmo, no al tiempo real de vuelo
* El tiempo de vuelo se estima en función de la distancia y una velocidad constante del dron
* El algoritmo TSP es óptimo pero no escalable
* El modelo RL es aproximado pero eficiente en tiempo de respuesta

---

## 🎯 7. Recomendaciones de uso

* Ejecutar pruebas con diferentes cantidades de puntos (5, 8, 10 nodos)
* Analizar la diferencia entre precisión (TSP) y escalabilidad (RL)
* Utilizar las gráficas generadas para el análisis en el TFM

---

## 🧠 8. Resumen técnico

El sistema implementa un enfoque híbrido que combina:

* **Optimización exacta (TSP)** para obtener soluciones óptimas
* **Inteligencia artificial (RL)** para analizar alternativas escalables

Esto permite evaluar el comportamiento de ambos métodos en escenarios reales de logística con drones.

---
