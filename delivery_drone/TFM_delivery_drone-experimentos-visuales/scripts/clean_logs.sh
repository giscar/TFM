#!/bin/bash
echo "🧹 Limpiando logs viejos de PX4..."
find ~/drone_project -name "*.ulg" -mtime +1 -size +10M -exec rm -v {} \;
find /var/lib/docker -name "*.ulg" -mtime +1 -size +10M -sudo exec rm -v {} \; 2>/dev/null
echo "✅ Limpieza completada"
