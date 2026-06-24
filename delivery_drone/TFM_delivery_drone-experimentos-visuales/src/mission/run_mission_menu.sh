#!/bin/bash
# Menú para seleccionar misión de optimización (incluye generación aleatoria)

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Misiones predefinidas (fijas)
MISSIONS=(
    "Malta 8 puntos|/ros2_ws/src/mission/orders_8_Malta.json|35.9000|14.5200"
    "Malta 12 puntos|/ros2_ws/src/mission/orders_12_Malta.json|35.9000|14.5200"
    "Villavicencio 7 puntos|/ros2_ws/src/mission/orders_7_Villavicencio.json|4.1614|-73.2389"
    "Bogotá 8 puntos|/ros2_ws/src/mission/orders_8_Bogota.json|4.7016|-74.1469"
    "Bogotá 12 puntos|/ros2_ws/src/mission/orders_12_Bogota.json|4.7016|-74.1469"
)

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}   MENÚ DE MISIONES DE OPTIMIZACIÓN${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""

# Mostrar opciones fijas
i=1
valid_options=()
for mission in "${MISSIONS[@]}"; do
    name=$(echo "$mission" | cut -d'|' -f1)
    file=$(echo "$mission" | cut -d'|' -f2)
    if [ -f "$file" ]; then
        echo "$i) $name"
        valid_options+=("$mission")
        ((i++))
    fi
done

# Opción de misión aleatoria
echo "$i) 🎲 Misión aleatoria (genera nueva)"
((i++))

read -p "Selecciona una misión (1-${#valid_options[@]} o $((i-1)) para aleatoria): " choice

if [[ "$choice" == "$((i-1))" ]]; then
    # Generar misión aleatoria
    echo ""
    echo -e "${YELLOW}🌍 Selecciona el país:${NC}"
    echo "1) Malta"
    echo "2) Bogotá"
    echo "3) Villavicencio"
    read -p "Opción: " country_opt
    case $country_opt in
        1) COUNTRY="Malta" ;;
        2) COUNTRY="Bogotá" ;;
        3) COUNTRY="Villavicencio" ;;
        *) echo "Opción no válida"; exit 1 ;;
    esac
    read -p "Número de órdenes (máx 12): " NUM_ORDERS
    if [ -z "$NUM_ORDERS" ] || [ "$NUM_ORDERS" -lt 1 ] || [ "$NUM_ORDERS" -gt 12 ]; then
        echo "Número no válido. Usando 8 por defecto."
        NUM_ORDERS=8
    fi

    echo -e "${YELLOW}🎲 Generando órdenes aleatorias...${NC}"
    RANDOM_OUTPUT=$(python3 /ros2_ws/src/mission/generate_random_orders.py "$COUNTRY" "$NUM_ORDERS")
    JSON_FILE=$(echo "$RANDOM_OUTPUT" | grep "✅ Archivo generado:" | awk '{print $3}')
    REF_LAT=$(echo "$RANDOM_OUTPUT" | grep "📌 Referencia:" | awk '{print $4}' | cut -d',' -f1)
    REF_LON=$(echo "$RANDOM_OUTPUT" | grep "📌 Referencia:" | awk '{print $5}')
    if [ -z "$JSON_FILE" ] || [ ! -f "$JSON_FILE" ]; then
        echo -e "${RED}Error al generar el archivo JSON.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Archivo generado: $JSON_FILE${NC}"
    echo "Referencia: lat=$REF_LAT, lon=$REF_LON"
    echo ""
    python3 /ros2_ws/src/mission/delivery_mission.py --json "$JSON_FILE" --ref-lat "$REF_LAT" --ref-lon "$REF_LON"
    exit 0
fi

# Validar elección de misión fija
if ! [[ "$choice" =~ ^[0-9]+$ ]] || [ "$choice" -lt 1 ] || [ "$choice" -gt ${#valid_options[@]} ]; then
    echo -e "${RED}Opción no válida.${NC}"
    exit 1
fi

selected="${valid_options[$((choice-1))]}"
name=$(echo "$selected" | cut -d'|' -f1)
json_file=$(echo "$selected" | cut -d'|' -f2)
ref_lat=$(echo "$selected" | cut -d'|' -f3)
ref_lon=$(echo "$selected" | cut -d'|' -f4)

echo -e "\n${GREEN}Ejecutando misión: $name${NC}"
echo "Archivo JSON: $json_file"
echo "Referencia: lat=$ref_lat, lon=$ref_lon"
echo ""

python3 /ros2_ws/src/mission/delivery_mission.py --json "$json_file" --ref-lat "$ref_lat" --ref-lon "$ref_lon"
