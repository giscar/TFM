
### 3. `geo/README.md`

```markdown
# Rama geo: Geocodificación y Conversión de Coordenadas

## 🎯 Propósito
Proporciona módulos para convertir direcciones reales en coordenadas geográficas (lat/lon) y transformarlas a coordenadas locales (x, y) utilizables por el dron.

## 📁 Archivos Clave
- `src/geo/mapbox_geocoder.py`: Cliente de la API de Mapbox para geocodificación (conversión dirección → lat/lon).
- `src/geo/coordinates.py`: Funciones de conversión entre coordenadas geográficas y locales (lat/lon ↔ x, y) usando una referencia fija (punto de origen).

## 🧭 Conversión de Coordenadas
- `latlon_to_local(lat, lon, ref_lat, ref_lon)`: Proyección plana (R ≈ 6371 km) para distancias cortas.
- `local_to_latlon(x, y, ref_lat, ref_lon)`: Inversa.

## 🌍 Puntos de Origen (Aeropuertos)
| Ciudad | Latitud | Longitud |
|--------|---------|----------|
| Malta (Valletta) | 35.9000 | 14.5200 |
| Bogotá (El Dorado) | 4.7016 | -74.1469 |
| Villavicencio (Vanguardia) | 4.1614 | -73.2389 |

## 🚀 Ejemplo
```python
from mapbox_geocoder import MapboxGeocoder
from coordinates import latlon_to_local

geocoder = MapboxGeocoder()
lat, lon = geocoder.geocode("Sliema, Malta")
x, y = latlon_to_local(lat, lon, ref_lat=35.9, ref_lon=14.52)
print(f"Waypoint local: ({x:.2f}, {y:.2f})")
