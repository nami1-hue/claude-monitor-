# Claude Monitor - Quick Start Guide

## 🚀 Setup en 5 minutos

### 1️⃣ Configurar variable de entorno en Railway

1. Ve a tu proyecto en Railway
2. Variables → Agrega `PROJECTS`
3. Pega esto (ajusta rutas según tus proyectos):

```json
{
  "phd-research": {
    "name": "PhD Research - 3D Unwrapping",
    "path": "~/phd-research"
  }
}
```

### 2️⃣ Instalar daemon localmente

```bash
cd ~/claude-monitor-railway

# Dale permiso de ejecución
chmod +x install-daemon.sh

# Instala daemon para tu proyecto
./install-daemon.sh phd-research ~/phd-research
```

### 3️⃣ Abrir monitor en navegador

```
https://eloquent-quietude-production.up.railway.app
```

Ingresa tu contraseña (configurada en `MONITOR_PASSWORD` en Railway).

### 4️⃣ Verificar conexión

- Debe aparecer el selector de proyecto
- El daemon debe mostrar 🟢 Conectado
- Haz un test: escribe un comando y envía

---

## 📋 Comandos comunes

### Instalar múltiples daemons

```bash
./install-daemon.sh phd-research ~/phd-research
./install-daemon.sh hc-acop ~/hc-acop-debug
./install-daemon.sh claude-monitor ~/claude-monitor-railway
```

### Verificar setup

```bash
./test-setup.sh
```

### Ver logs del daemon

```bash
# Si está corriendo en terminal:
# Ctrl+C para detener

# Si está como servicio systemd:
sudo systemctl status cc-daemon-phd-research
journalctl -u cc-daemon-phd-research -f

# O archivo de log directo:
tail -f /tmp/cc-daemon-v3-phd-research.log
```

### Detener daemon

```bash
# Manual (Ctrl+C en terminal)

# O si es servicio:
sudo systemctl stop cc-daemon-phd-research
```

### Reiniciar daemon

```bash
# Servicio:
sudo systemctl restart cc-daemon-phd-research

# O manual: Ctrl+C y reiniciar
```

---

## 🔧 Variables de entorno necesarias

### En Railway (server.py)

```bash
PROJECTS={"phd-research":{"name":"PhD","path":"~/phd-research"}}
MONITOR_PASSWORD=TuPasswordAqui123!
```

### En tu máquina (daemon)

```bash
export PROJECT_ID=phd-research
export CLAUDE_MONITOR_URL=https://eloquent-quietude-production.up.railway.app
# El daemon hereda del script cc aux variables AWS/Bedrock
```

---

## 🐛 Troubleshooting rápido

### "Proyecto no encontrado"
```bash
# Verifica que PROJECT_ID coincide con lo configurado en Railway
echo $PROJECT_ID

# Verifica que está en el JSON de PROJECTS
# Debe ser exactamente igual (minúsculas, sin espacios)
```

### Daemon no conecta
```bash
# Verifica URL
echo $CLAUDE_MONITOR_URL

# Testa conectividad
curl -I https://eloquent-quietude-production.up.railway.app

# Verifica logs
tail -f /tmp/cc-daemon-v3-${PROJECT_ID}.log
```

### Selector vacío en web
```bash
# Verifica que PROJECTS está bien configurado en Railway
# JSON debe ser válido

# Testa endpoint:
curl https://eloquent-quietude-production.up.railway.app/api/projects
```

### Comando no se ejecuta
1. Verifica que seleccionaste el proyecto correcto
2. Verifica que el daemon está 🟢 Conectado
3. Mira los logs: `journalctl -u cc-daemon-* -f`

---

## 📊 Flujo típico de uso

```
1. Abre monitor en navegador
   ↓
2. Selecciona proyecto del dropdown
   ↓
3. Ves mensajes del proyecto
   ↓
4. Escribes comando
   ↓
5. Presionas Enter o click "Enviar"
   ↓
6. Daemon lo recibe (via /api/poll_command)
   ↓
7. Daemon ejecuta en Claude Code
   ↓
8. Respuesta aparece en feed
   ↓
9. Cambias a otro proyecto (step 2)
```

---

## 💡 Tips

- **Múltiples terminales:** Corre cada daemon en su propia terminal
- **Servicios systemd:** Para que los daemons corran automáticamente
- **Monitoreo remoto:** Accede desde celular usando la URL de Railway
- **Logs:** Los logs del daemon están en `/tmp/cc-daemon-v3-{project_id}.log`

---

## 📚 Documentación completa

- `MULTI_PROJECT_SETUP.md` - Setup detallado
- `README.md` - Overview del proyecto
- `SECURITY_SETUP.md` - Seguridad y autenticación
- `CHANGELOG.md` - Historial de cambios

---

**¿Problemas?** Revisa los logs y verifica que:
1. ✅ Servidor Railway está running
2. ✅ Variable `PROJECTS` está bien configurada
3. ✅ Daemon tiene `PROJECT_ID` correcto
4. ✅ `MONITOR_PASSWORD` está configurado
