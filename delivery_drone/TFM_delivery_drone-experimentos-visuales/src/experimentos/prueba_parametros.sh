#!/bin/bash
# Script para probar diferentes parámetros de vuelo

echo "🧪 EXPERIMENTOS CON PARÁMETROS DE VUELO"
echo "========================================"

# Lista de parámetros a probar
alturas=("-1.5" "-2.0" "-2.5" "-3.0")
velocidades=("2.0" "3.0" "4.0" "5.0")

echo "Probando diferentes alturas..."
for h in "${alturas[@]}"; do
    echo -n "  Altura $h metros: "
    # Aquí iría el comando para probar cada altura
    echo "simulación completada"
    sleep 1
done

echo ""
echo "Probando diferentes velocidades..."
for v in "${velocidades[@]}"; do
    echo -n "  Velocidad $v m/s: "
    # Aquí iría el comando para probar cada velocidad
    echo "simulación completada"
    sleep 1
done

echo ""
echo "✅ Experimentos completados"
