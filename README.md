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
pip install -r requirements.txt
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

Para usar geocodificación real con Mapbox, configura un token de acceso como variable de entorno:

```bash
export MAPBOX_TOKEN="TU_TOKEN_AQUI"
```

**Explicación:**
Este token permite convertir direcciones reales en coordenadas geográficas (latitud y longitud), lo cual es fundamental para trabajar con datos reales en el problema de optimización.

Si no configuras `MAPBOX_TOKEN`, `tsp_rl_persistente_mapbox.py` usa coordenadas locales de Lima para poder ejecutar el agente sin depender de la API.

---

## ▶️ 4. Ejecución del programa

```bash
python tsp_rl_persistente_mapbox.py
```

Para ejecutar sin abrir ventanas gráficas y guardar las imágenes directamente:

```bash
SHOW_PLOTS=0 MPLBACKEND=Agg python tsp_rl_persistente_mapbox.py
```

**Explicación:**
Este comando ejecuta el sistema completo, el cual realiza las siguientes acciones:

1. Obtiene coordenadas reales a partir de direcciones
2. Calcula la ruta óptima mediante TSP
3. Carga el modelo persistente si ya existe o entrena uno nuevo
4. Genera una ruta alternativa mediante RL
5. Calcula distancias reales (en metros)
6. Estima tiempos de vuelo del dron
7. Muestra resultados comparativos
8. Genera visualizaciones gráficas de las rutas

Si quieres refinar el modelo existente antes de generar la ruta RL:

```bash
RL_REFINE_TIMESTEPS=20000 python tsp_rl_persistente_mapbox.py
```

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

## 🔄 9. Experimento de replanificación dinámica

Además del script principal, el proyecto incluye un experimento específico para evaluar cómo responde el sistema ante cambios operativos propios de un servicio de delivery con drones. Este experimento se encuentra en:

```bash
experimento_replanificacion_dinamica.py
```

El objetivo es comparar tres enfoques de planificación:

* **TSP exacto** → referencia de optimalidad.
* **Greedy + 2-opt** → heurística rápida como línea base intermedia.
* **RL con PPO** → agente aprendido con modelo persistente.

El experimento simula cuatro eventos:

* **baseline** → ruta inicial sin cambios.
* **add** → incorporación de un nuevo pedido.
* **cancel** → cancelación de una entrega.
* **priority** → cambio de prioridad de un punto de entrega.

### 9.1. Prueba rápida

Sirve para verificar que el código ejecuta correctamente y genera CSV y gráficas:

```bash
MPLBACKEND=Agg /opt/anaconda3/envs/rl_tfm/bin/python experimento_replanificacion_dinamica.py \
  --nodes 5 \
  --events baseline add cancel priority \
  --timesteps 512 \
  --output-dir graficas/test_replanificacion
```

### 9.2. Ejecución recomendada para el TFM

Esta ejecución parte de 9 nodos y, con el evento `add`, llega a 10 nodos. De esta forma se conserva una comparación viable con TSP exacto:

```bash
MPLBACKEND=Agg /opt/anaconda3/envs/rl_tfm/bin/python experimento_replanificacion_dinamica.py \
  --nodes 9 \
  --events all \
  --timesteps 50000 \
  --output-dir graficas/replanificacion_tesis_9_10
```

### 9.3. Archivos generados

El experimento genera un archivo CSV con las métricas:

```bash
open graficas/replanificacion_tesis_9_10/resultados_replanificacion.csv
```

También genera gráficas comparativas por evento:

```bash
open graficas/replanificacion_tesis_9_10
```

Y rutas individuales por evento y algoritmo:

```bash
open graficas/replanificacion_tesis_9_10/rutas
```

Los modelos RL entrenados o reutilizados se guardan en:

```bash
modelos_replanificacion/
```

### 9.4. Métricas interpretadas

El CSV incluye las siguientes columnas:

* **event** → tipo de evento operativo evaluado.
* **algorithm** → algoritmo utilizado: TSP, Greedy+2opt o RL.
* **nodes** → número de nodos del escenario.
* **route** → orden de visita calculado.
* **distance_m** → distancia total de la ruta en metros.
* **flight_time_s** → tiempo estimado de vuelo, usando velocidad constante.
* **calc_time_s** → tiempo real de cálculo o inferencia de la ruta.
* **model_prep_time_s** → tiempo de carga, entrenamiento o refinamiento del modelo RL.
* **error_relative_pct** → diferencia relativa respecto al TSP exacto.
* **speedup_vs_tsp** → aceleración del método respecto al tiempo de cálculo del TSP.

Para el análisis del TFM, la columna más importante en términos de respuesta dinámica es `calc_time_s`, ya que representa la latencia de replanificación una vez que el sistema recibe un cambio operativo.

---

## 🧪 10. Experimento de ablación de función de recompensa

El proyecto incluye un experimento adicional orientado a analizar el impacto del diseño de la recompensa sobre el comportamiento del agente de aprendizaje por refuerzo. Este punto es relevante porque, en RL, la función de recompensa determina qué comportamientos aprende el agente y cómo equilibra distancia, penalizaciones y finalización de ruta.

El archivo del experimento es:

```bash
experimento_ablation_reward.py
```

Se comparan tres modos de recompensa:

* **distance_only** → penaliza únicamente la distancia recorrida.
* **distance_penalty** → penaliza distancia y agrega penalización por saltos largos.
* **full** → usa la recompensa completa: distancia, saltos largos, incentivo por cercanía y bonus por completar ruta.

### 10.1. Prueba rápida

```bash
MPLBACKEND=Agg /opt/anaconda3/envs/rl_tfm/bin/python experimento_ablation_reward.py \
  --nodes 5 \
  --timesteps 512 \
  --fresh \
  --output-dir graficas/test_ablation_reward
```

### 10.2. Ejecución recomendada para el TFM

```bash
MPLBACKEND=Agg /opt/anaconda3/envs/rl_tfm/bin/python experimento_ablation_reward.py \
  --nodes 9 \
  --timesteps 20000 \
  --fresh \
  --output-dir graficas/ablation_reward_tesis_9
```

### 10.3. Archivos generados

CSV principal:

```bash
open graficas/ablation_reward_tesis_9/resultados_ablation_reward.csv
```

Líneas base TSP y Greedy + 2-opt:

```bash
open graficas/ablation_reward_tesis_9/lineas_base.csv
```

Gráficas:

```bash
open graficas/ablation_reward_tesis_9
```

Rutas por modo de recompensa:

```bash
open graficas/ablation_reward_tesis_9/rutas
```

Modelos entrenados:

```bash
modelos_ablation_reward/
```

### 10.4. Interpretación

El experimento registra:

* **reward_mode** → modo de recompensa evaluado.
* **distance_m** → distancia obtenida por el agente RL.
* **inference_time_s** → tiempo de inferencia de la política entrenada.
* **model_prep_time_s** → tiempo de entrenamiento o carga del modelo.
* **error_relative_pct** → error relativo frente al TSP exacto.
* **repeated_actions** → acciones repetidas corregidas durante la inferencia.

En la ejecución documentada para el TFM con 9 nodos y 20.000 timesteps, `distance_penalty` obtuvo la menor distancia entre las variantes RL evaluadas. Este resultado muestra que una recompensa más compleja no siempre garantiza mejores rutas si sus componentes no están calibrados adecuadamente o si el presupuesto de entrenamiento es limitado.
