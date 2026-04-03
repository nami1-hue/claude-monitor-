#!/bin/bash
# ═══════════════════════════════════════════════════════════
# Claude Monitor - Setup Verification Script
# Verifica que todo está configurado correctamente
# ═══════════════════════════════════════════════════════════

set -e

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

MONITOR_URL="${CLAUDE_MONITOR_URL:-https://eloquent-quietude-production.up.railway.app}"

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Claude Monitor - Setup Verification${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

FAILED=0
PASSED=0

# Test 1: Conectividad
echo -e "${YELLOW}Test 1: Conectividad con servidor...${NC}"
if curl -s --max-time 5 "$MONITOR_URL" > /dev/null; then
    echo -e "${GREEN}✅ Servidor accesible${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ Servidor no accesible${NC}"
    ((FAILED++))
fi
echo ""

# Test 2: Health check
echo -e "${YELLOW}Test 2: Health check...${NC}"
HEALTH=$(curl -s --max-time 5 "$MONITOR_URL/health" 2>/dev/null || echo "{}")
if echo "$HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}✅ Servidor healthy${NC}"
    echo "   $HEALTH" | head -c 100
    echo ""
    ((PASSED++))
else
    echo -e "${RED}❌ Health check falló${NC}"
    ((FAILED++))
fi
echo ""

# Test 3: Listar proyectos
echo -e "${YELLOW}Test 3: Listar proyectos...${NC}"
PROJECTS=$(curl -s --max-time 5 "$MONITOR_URL/api/projects" 2>/dev/null || echo "[]")
PROJECT_COUNT=$(echo "$PROJECTS" | grep -o '"id"' | wc -l)
if [ "$PROJECT_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ Proyectos encontrados: $PROJECT_COUNT${NC}"
    echo "$PROJECTS" | grep -o '"name":"[^"]*"' | head -3
    ((PASSED++))
else
    echo -e "${RED}❌ No se encontraron proyectos${NC}"
    echo "   Response: $PROJECTS"
    ((FAILED++))
fi
echo ""

# Test 4: Python dependencies
echo -e "${YELLOW}Test 4: Dependencias Python...${NC}"
python3 -c "
import flask, flask_socketio, flask_cors, requests, pexpect
print('  ✓ flask')
print('  ✓ flask_socketio')
print('  ✓ flask_cors')
print('  ✓ requests')
print('  ✓ pexpect')
" 2>/dev/null && {
    echo -e "${GREEN}✅ Todas las dependencias OK${NC}"
    ((PASSED++))
} || {
    echo -e "${RED}❌ Faltan dependencias${NC}"
    echo "   Instala con: pip install flask flask-socketio flask-cors requests pexpect"
    ((FAILED++))
}
echo ""

# Test 5: Archivo de daemon
echo -e "${YELLOW}Test 5: Daemon script...${NC}"
if [ -f ~/claude-monitor-railway/cc-daemon-v3.py ]; then
    echo -e "${GREEN}✅ Daemon encontrado${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ Daemon no encontrado${NC}"
    ((FAILED++))
fi
echo ""

# Test 6: Monitor template
echo -e "${YELLOW}Test 6: Monitor template...${NC}"
if [ -f ~/claude-monitor-railway/templates/monitor.html ]; then
    MULTI_PROJECT=$(grep -c "projectSelect\|switchProject" ~/claude-monitor-railway/templates/monitor.html || echo 0)
    if [ "$MULTI_PROJECT" -gt 0 ]; then
        echo -e "${GREEN}✅ Template con soporte multi-proyecto${NC}"
        ((PASSED++))
    else
        echo -e "${YELLOW}⚠️  Template no tiene soporte multi-proyecto${NC}"
        ((FAILED++))
    fi
else
    echo -e "${RED}❌ Template no encontrado${NC}"
    ((FAILED++))
fi
echo ""

# Test 7: Enviar mensaje de prueba
echo -e "${YELLOW}Test 7: Enviar mensaje de prueba...${NC}"
TEST_MSG=$(curl -s --max-time 5 -X POST "$MONITOR_URL/api/message" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "default",
    "type": "test",
    "content": "Mensaje de prueba",
    "is_approval": false
  }' 2>/dev/null || echo "{}")

if echo "$TEST_MSG" | grep -q "ok"; then
    echo -e "${GREEN}✅ Mensaje de prueba enviado${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ Error al enviar mensaje de prueba${NC}"
    echo "   Response: $TEST_MSG"
    ((FAILED++))
fi
echo ""

# Resumen
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Resumen:${NC}"
echo -e "  ${GREEN}✅ Pasadas: $PASSED${NC}"
echo -e "  ${RED}❌ Fallidas: $FAILED${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ¡Setup completo! Todo funciona correctamente.${NC}"
    echo ""
    echo "Próximos pasos:"
    echo "  1. Abre el monitor en el navegador:"
    echo "     $MONITOR_URL"
    echo ""
    echo "  2. Instala daemons para tus proyectos:"
    echo "     $HOME/claude-monitor-railway/install-daemon.sh phd-research ~/phd-research"
    echo ""
    exit 0
else
    echo -e "${RED}❌ Hay problemas a resolver${NC}"
    exit 1
fi
