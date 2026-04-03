#!/bin/bash
# ═══════════════════════════════════════════════════════════
# Claude Monitor - Daemon Installation Script
# Instala un daemon para un proyecto específico
# ═══════════════════════════════════════════════════════════

set -e

PROJECT_ID="${1:-}"
PROJECT_PATH="${2:-}"
MONITOR_URL="${CLAUDE_MONITOR_URL:-https://eloquent-quietude-production.up.railway.app}"

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Claude Monitor - Daemon Installation${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Validar argumentos
if [ -z "$PROJECT_ID" ] || [ -z "$PROJECT_PATH" ]; then
    echo -e "${RED}❌ Uso: $0 <PROJECT_ID> <PROJECT_PATH>${NC}"
    echo ""
    echo "Ejemplos:"
    echo "  $0 phd-research ~/phd-research"
    echo "  $0 hc-acop ~/hc-acop-debug"
    echo ""
    exit 1
fi

# Expandir ~ a home
PROJECT_PATH="${PROJECT_PATH/#\~/$HOME}"

# Validar que el path existe
if [ ! -d "$PROJECT_PATH" ]; then
    echo -e "${RED}❌ Directorio no existe: $PROJECT_PATH${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 Configuración:${NC}"
echo "  Project ID:     $PROJECT_ID"
echo "  Project Path:   $PROJECT_PATH"
echo "  Monitor URL:    $MONITOR_URL"
echo ""

# Opción 1: Modo manual (run in terminal)
echo -e "${YELLOW}¿Cómo quieres ejecutar el daemon?${NC}"
echo "  1) Manual (correr en terminal)"
echo "  2) Servicio systemd (automático)"
echo ""
read -p "Selecciona opción (1 o 2): " OPTION

if [ "$OPTION" = "1" ]; then
    echo ""
    echo -e "${GREEN}✅ Ejecutando daemon manualmente...${NC}"
    echo ""
    echo "Comando a ejecutar:"
    echo ""
    echo -e "${BLUE}export PROJECT_ID=$PROJECT_ID${NC}"
    echo -e "${BLUE}export CLAUDE_MONITOR_URL=$MONITOR_URL${NC}"
    echo -e "${BLUE}cd $PROJECT_PATH${NC}"
    echo -e "${BLUE}python3 ~/claude-monitor-railway/cc-daemon-v3.py --dir $PROJECT_PATH${NC}"
    echo ""
    echo -e "${YELLOW}Presiona Enter para ejecutar o Ctrl+C para cancelar...${NC}"
    read

    export PROJECT_ID="$PROJECT_ID"
    export CLAUDE_MONITOR_URL="$MONITOR_URL"
    cd "$PROJECT_PATH"
    python3 ~/claude-monitor-railway/cc-daemon-v3.py --dir "$PROJECT_PATH"

elif [ "$OPTION" = "2" ]; then
    echo ""
    echo -e "${YELLOW}⚙️  Instalando como servicio systemd...${NC}"

    SERVICE_NAME="cc-daemon-${PROJECT_ID}"
    SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

    echo -e "${YELLOW}📝 Creando archivo de servicio...${NC}"

    # Crear archivo temporal
    TEMP_SERVICE="/tmp/${SERVICE_NAME}.service"

    cat > "$TEMP_SERVICE" << EOF
[Unit]
Description=Claude Monitor Daemon - $PROJECT_ID
After=network.target

[Service]
Type=simple
User=$USER
Environment="PROJECT_ID=$PROJECT_ID"
Environment="CLAUDE_MONITOR_URL=$MONITOR_URL"
Environment="ANTHROPIC_MODEL_PROVIDER=bedrock"
Environment="ANTHROPIC_MODEL=us.anthropic.claude-sonnet-4-5-20250929-v1:0"
Environment="AWS_PROFILE=hc-qa-admin"
Environment="AWS_REGION=us-east-1"
WorkingDirectory=$PROJECT_PATH
ExecStart=/usr/bin/python3 $HOME/claude-monitor-railway/cc-daemon-v3.py --dir $PROJECT_PATH
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    echo -e "${BLUE}Contenido del servicio:${NC}"
    cat "$TEMP_SERVICE"
    echo ""

    echo -e "${YELLOW}Necesitas permisos sudo para instalar el servicio.${NC}"
    read -p "¿Continuar con instalación? (s/n): " CONFIRM

    if [ "$CONFIRM" = "s" ] || [ "$CONFIRM" = "y" ]; then
        sudo cp "$TEMP_SERVICE" "$SERVICE_FILE"
        sudo chmod 644 "$SERVICE_FILE"

        echo ""
        echo -e "${GREEN}✅ Servicio instalado${NC}"
        echo ""

        read -p "¿Iniciar servicio ahora? (s/n): " START_SERVICE

        if [ "$START_SERVICE" = "s" ] || [ "$START_SERVICE" = "y" ]; then
            sudo systemctl daemon-reload
            sudo systemctl enable "$SERVICE_NAME"
            sudo systemctl start "$SERVICE_NAME"

            echo ""
            echo -e "${GREEN}✅ Servicio iniciado${NC}"
            echo ""
            echo -e "${YELLOW}Comandos útiles:${NC}"
            echo "  Ver estado:     sudo systemctl status $SERVICE_NAME"
            echo "  Ver logs:       journalctl -u $SERVICE_NAME -f"
            echo "  Detener:        sudo systemctl stop $SERVICE_NAME"
            echo "  Reiniciar:      sudo systemctl restart $SERVICE_NAME"
        else
            echo ""
            echo -e "${YELLOW}Para iniciar después:${NC}"
            echo "  sudo systemctl start $SERVICE_NAME"
        fi

        rm "$TEMP_SERVICE"
    else
        echo -e "${YELLOW}Instalación cancelada${NC}"
        echo "Archivo de servicio guardado en: $TEMP_SERVICE"
        exit 1
    fi
else
    echo -e "${RED}❌ Opción inválida${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ ¡Daemon configurado!${NC}"
echo ""
echo -e "${BLUE}Próximos pasos:${NC}"
echo "  1. Abre el monitor: $MONITOR_URL"
echo "  2. Selecciona proyecto: $PROJECT_ID"
echo "  3. Verifica conexión (debe mostrar 🟢 conectado)"
echo ""
