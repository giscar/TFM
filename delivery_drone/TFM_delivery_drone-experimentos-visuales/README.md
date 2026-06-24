
### 6. `experimentos-visuales/README.md`

```markdown
# Rama experimentos-visuales: Dashboard y Resultados

## 🎯 Propósito
Almacena el dashboard web interactivo, los resultados de las misiones (CSV) y gráficos consolidados para el análisis de la optimización de rutas.

## 📁 Archivos Clave
- `dashboard/index.html`: Página web con gráficos (Chart.js) y tabla comparativa.
- `dashboard/data/resumen_misiones.csv`: CSV central con todas las métricas de las misiones ejecutadas.
- `src/experimentos/results/`: Carpeta con CSV detallados de cada misión.

## 📊 Dashboard
- Accesible en `http://130.61.118.51:8080`.
- Muestra:
  - Tabla comparativa (distancia, tiempo, batería, mejora).
  - Gráficos de barras por misión.
  - Gráficos consolidados: mejora promedio, distancia total, batería promedio, distribución por país.
- Actualización automática cada 60 segundos (lee el CSV central).

## 📈 Resultados Destacados (ejemplo)
| Misión | Puntos | Dist. Secuencial (km) | Dist. Optimizada (km) | Mejora |
|--------|--------|----------------------|----------------------|--------|
| Malta 8 | 8 | 27.55 | 19.69 | 28.54% |
| Bogotá 12 | 12 | 58,950.04 | 37,958.15 | 35.61% |

## 🚀 Cómo Actualizar el Dashboard
Tras ejecutar una misión, el CSV central se actualiza automáticamente y se sube a GitHub. Para reflejar cambios manualmente:
```bash
docker cp drone_container:/home/ubuntu/dashboard/data/resumen_misiones.csv ~/dashboard/data/
