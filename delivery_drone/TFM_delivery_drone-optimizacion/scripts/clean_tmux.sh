#!/bin/bash
echo "🧹 LIMPIEZA COMPLETA DEL SISTEMA"
echo "================================"

# Matar todas las sesiones tmux
echo "Matando sesiones tmux..."
tmux kill-server 2>/dev/null
sleep 1

# Matar procesos específicos
echo "Matando procesos..."
pkill -f MicroXRCEAgent 2>/dev/null
pkill -f px4 2>/dev/null
pkill -f gz 2>/dev/null
pkill -f foxglove 2>/dev/null
pkill -f ros2 2>/dev/null
sleep 2

# Verificar que no quedan procesos
echo "Procesos restantes:"
ps aux | grep -E "MicroXRCEAgent|px4|gz|foxglove|ros2" | grep -v grep || echo "✅ Ninguno"

echo ""
echo "✅ Sistema completamente limpio"
echo "Ahora puedes ejecutar: ./start_all.sh"
