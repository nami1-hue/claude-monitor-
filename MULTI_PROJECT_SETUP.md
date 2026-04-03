# 🎮 Claude Monitor - Múltiples Proyectos Setup

## Descripción General

El sistema ahora soporta múltiples proyectos, permitiendo que diferentes daemons de Claude Code se ejecuten en paralelo, cada uno en su propio directorio de trabajo, todos monitoreados desde una única interfaz web.

## Arquitectura

```
┌─────────────────────────────────────┐
│     Servidor Railway (server.py)    │
│   - Maneja múltiples proyectos      │
│   - Almacena mensajes por proyecto  │
│   - Cola de comandos por proyecto   │
└─────────────────────────────────────┘
           ↑                   ↓
    ┌──────┴──────┬──────┬──────┴──────┐
    ↓             ↓      ↓             ↓
┌────────┐  ┌─────────┐ ┌──────┐  ┌─────────┐
│ Daemon │  │  Daemon │ │ Daemon│ │  Daemon │
│ PhD   │  │  HC-ACOP│ │ Other│ │ Project4│
│Research│  │  Debug  │ │      │  │         │
└────────┘  └─────────┘ └──────┘  └─────────┘
  Project    Project    Project    Project
    #1         #2         #3         #4
```

## Configuración en Railway

### Paso 1: Definir proyectos en variable de entorno

En el dashboard de Railway, agrega la variable de entorno `PROJECTS` con el siguiente formato JSON:

```json
{
  "phd-research": {
    "name": "PhD Research - 3D Unwrapping",
    "path": "~/phd-research"
  },
  "hc-acop": {
    "name": "HC ACOP Lambda Debug",
    "path": "~/hc-acop-debug"
  },
  "claude-monitor": {
    "name": "Claude Monitor Project",
    "path": "~/claude-monitor-railway"
  }
}
```

**Cómo agregar en Railway:**
1. Ve a tu proyecto en Railway
2. Ve a "Variables" o "Environment"
3. Agrega nueva variable: `PROJECTS`
4. Pega el JSON anterior
5. Deploy

### Paso 2: Instalar múltiples daemons

Para cada proyecto, instala y configura un daemon con su `PROJECT_ID`:

#### Opción A: Usando variable de entorno (Recomendado)

```bash
# En la máquina local del proyecto
export PROJECT_ID=phd-research
export CLAUDE_MONITOR_URL=https://eloquent-quietude-production.up.railway.app
python3 ~/claude-monitor-railway/cc-daemon-v3.py --dir ~/phd-research
```

#### Opción B: Usando argumentos CLI

```bash
python3 ~/claude-monitor-railway/cc-daemon-v3.py \
  --project-id phd-research \
  --dir ~/phd-research
```

#### Opción C: Instalado como servicio systemd

Crea `/etc/systemd/system/cc-daemon-phd.service`:

```ini
[Unit]
Description=Claude Code Daemon - PhD Research
After=network.target

[Service]
Type=simple
User=nmi1mx
Environment="PROJECT_ID=phd-research"
Environment="CLAUDE_MONITOR_URL=https://eloquent-quietude-production.up.railway.app"
Environment="ANTHROPIC_MODEL_PROVIDER=bedrock"
Environment="ANTHROPIC_MODEL=us.anthropic.claude-sonnet-4-5-20250929-v1:0"
Environment="AWS_PROFILE=hc-qa-admin"
WorkingDirectory=/home/nmi1mx/phd-research
ExecStart=/usr/bin/python3 /home/nmi1mx/claude-monitor-railway/cc-daemon-v3.py --dir /home/nmi1mx/phd-research
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Luego:
```bash
sudo systemctl enable cc-daemon-phd
sudo systemctl start cc-daemon-phd
sudo systemctl status cc-daemon-phd
```

## Interfaz Web - Selector de Proyectos

### Uso

1. **Accede al monitor:**
   ```
   https://eloquent-quietude-production.up.railway.app
   ```

2. **Ingresa contraseña** (configurada en `MONITOR_PASSWORD`)

3. **Selector de proyectos** en el header:
   - Dropdown con lista de proyectos
   - Muestra: nombre, cantidad de mensajes, estado (🟢 conectado / 🔴 desconectado)

4. **Cambiar proyecto:**
   - Click en dropdown
   - Selecciona proyecto
   - Se cargan automáticamente los mensajes del proyecto

5. **Enviar comandos:**
   - Escribe comando en input
   - Click "Enviar" o presiona Enter
   - El comando se envía **automáticamente al proyecto seleccionado**

### Ejemplo de flujo

```
1. Abres el monitor
2. Ves selector con: "PhD Research", "HC ACOP", "Claude Monitor"
3. Seleccionas "PhD Research"
4. Se cargan los últimos 200 mensajes de ese proyecto
5. Escribes: ask "¿Cómo está el algoritmo?"
6. El daemon del proyecto PhD-Research lo recibe y ejecuta
7. Respuesta aparece en el feed
8. Cambias a "HC ACOP"
9. Ves conversación diferente del otro proyecto
```

## API Endpoints (actualizado para multi-proyecto)

Todos los endpoints ahora soportan `project_id`:

### GET /api/projects
**Retorna:** Lista de proyectos configurados

```json
[
  {
    "id": "phd-research",
    "name": "PhD Research - 3D Unwrapping",
    "path": "~/phd-research",
    "connected": true,
    "messages": 45
  },
  {
    "id": "hc-acop",
    "name": "HC ACOP Lambda Debug",
    "path": "~/hc-acop-debug",
    "connected": false,
    "messages": 12
  }
]
```

### GET /api/messages?project=PROJECT_ID
**Parámetros:** `project` (proyecto_id, default: "default")
**Retorna:** Últimos 200 mensajes del proyecto

### POST /api/message
**Daemon envía mensajes**

```json
{
  "project_id": "phd-research",
  "type": "claude",
  "content": "Respuesta del daemon...",
  "is_approval": false
}
```

### POST /api/send_command
**Web envía comandos al daemon**

```json
{
  "project_id": "phd-research",
  "command": "ask '¿Qué es X?'"
}
```

### GET /api/poll_command?project_id=PROJECT_ID
**Daemon obtiene comandos pendientes**

Retorna:
```json
{
  "status": "ok",
  "command": {
    "id": 1,
    "command": "ask '¿Qué es X?'",
    "timestamp": "2026-04-02T12:34:56",
    "status": "executing",
    "project_id": "phd-research"
  }
}
```

## Variables de Entorno - Referencia Completa

### Servidor (Railway)

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `PROJECTS` | JSON con proyectos configurados | Ver arriba |
| `MONITOR_PASSWORD` | Contraseña para acceder al web | `secure123` |
| `SECRET_KEY` | Secret para sesiones Flask | Auto-generado |
| `PORT` | Puerto para servidor | `8080` |

### Daemon (Local)

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `PROJECT_ID` | ID del proyecto que maneja este daemon | `phd-research` |
| `CLAUDE_MONITOR_URL` | URL del servidor Railway | `https://...up.railway.app` |
| `ANTHROPIC_MODEL_PROVIDER` | Proveedor de modelo (bedrock) | `bedrock` |
| `ANTHROPIC_MODEL` | Modelo a usar | `us.anthropic.claude-sonnet-4-5-20250929-v1:0` |
| `AWS_PROFILE` | Perfil AWS | `hc-qa-admin` |
| `AWS_REGION` | Región AWS | `us-east-1` |

## Troubleshooting

### ❌ "Proyecto no encontrado"
**Causa:** El `PROJECT_ID` del daemon no coincide con los configurados en Railway

**Solución:**
```bash
# Verifica PROJECT_ID
echo $PROJECT_ID

# Verifica que está en PROJECTS de Railway
# Debe estar exactamente igual (minúsculas, sin espacios)
```

### ❌ Daemon no envía mensajes
**Causa:** El servidor no puede recibir los mensajes

**Solución:**
```bash
# Verifica que el daemon está corriendo
ps aux | grep cc-daemon-v3

# Verifica logs
tail -f /tmp/cc-daemon-v3-phd-research.log

# Testa conectividad
curl https://eloquent-quietude-production.up.railway.app/health
```

### ❌ Selector vacío en web
**Causa:** Variable `PROJECTS` no está configurada o JSON inválido

**Solución:**
```bash
# En Railway, verifica que PROJECTS está bien formado
# JSON debe ser válido (sin comas extra, comillas balanceadas)

# Testa manualmente:
curl https://eloquent-quietude-production.up.railway.app/api/projects
```

### ❌ Comando enviado pero daemon no lo ejecuta
**Causa:** `project_id` en comando no coincide con `PROJECT_ID` del daemon

**Solución:**
- Verifica que seleccionaste el proyecto correcto en el dropdown
- Verifica que el `PROJECT_ID` del daemon matches el que ves en el dropdown

## Testing del Setup

### Test 1: Verificar servidor
```bash
curl https://eloquent-quietude-production.up.railway.app/health
# Debe retornar: {"status": "healthy", ...}
```

### Test 2: Listar proyectos
```bash
curl https://eloquent-quietude-production.up.railway.app/api/projects
# Debe retornar JSON con proyectos
```

### Test 3: Enviar mensaje desde daemon
```bash
curl -X POST https://eloquent-quietude-production.up.railway.app/api/message \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "phd-research",
    "type": "test",
    "content": "Mensaje de prueba",
    "is_approval": false
  }'
```

### Test 4: Obtener mensajes
```bash
curl https://eloquent-quietude-production.up.railway.app/api/messages?project=phd-research
```

## Próximos Pasos

1. ✅ Configure `PROJECTS` en Railway
2. ✅ Instale daemons para cada proyecto
3. ✅ Abra monitor en navegador
4. ✅ Seleccione proyecto y pruebe
5. ✅ Configure servicios systemd si lo desea

## Soporte

Si tienes problemas:
1. Revisa los logs: `/tmp/cc-daemon-v3-*.log`
2. Verifica logs de Railway: Dashboard → Logs
3. Testa endpoints manualmente con curl
4. Verifica que las contraseñas y URLs sean correctas

---

**Última actualización:** 2026-04-02
**Versión:** Multi-Project v1.0
