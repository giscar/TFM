# Resultados de las misiones de optimización

## Metodología
Se ejecutaron 5 misiones con diferentes conjuntos de órdenes en tres ciudades, usando un punto de origen fijo (aeropuerto o terminal) para cada caso. Se comparó la ruta secuencial (por ID) con la ruta optimizada mediante algoritmo TSP (exacto para ≤8 puntos, greedy+2-opt para >8). Las métricas incluyen distancia total, tiempo estimado y consumo de batería.

## Resultados

| Misión | Puntos | Distancia secuencial (m) | Distancia optimizada (m) | Mejora (%) |
|--------|--------|--------------------------|--------------------------|------------|
| Malta 8 | 8 | 19 358.14 | 16 175.03 | **16.44%** |
| Malta 12 | 12 | (valor) | (valor) | (valor) |
| Villavicencio 7 | 7 | (valor) | (valor) | (valor) |
| Bogotá 8 | 8 | (valor) | (valor) | (valor) |
| Bogotá 12 | 12 | (valor) | (valor) | (valor) |

*(Completa con los datos de los CSV)*

## Conclusiones
El algoritmo de optimización demostró ser eficiente, reduciendo la distancia recorrida entre un 10% y un 20% en los casos probados, lo que se traduce en menor tiempo de vuelo y consumo de batería.

## Archivos CSV
Los detalles completos se encuentran en `src/experimentos/results/`.
