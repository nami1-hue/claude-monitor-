# Changelog - Claude Monitor

## [2.0.0] - 2026-04-02 - Multi-Project Support

### ✨ Nuevas Características

#### Backend (server.py)
- ✅ Soporte para múltiples proyectos
- ✅ Variable de entorno `PROJECTS` con configuración JSON
- ✅ Almacenamiento separado de mensajes por proyecto
- ✅ Cola de comandos independiente por proyecto
- ✅ Endpoint `/api/projects` para listar proyectos
- ✅ Todos los endpoints soportan `project_id`

#### Daemon (cc-daemon-v3.py)
- ✅ Variable de entorno `PROJECT_ID` para identificarse
- ✅ Argumento CLI `--project-id` para override
- ✅ Envío de `project_id` en todos los mensajes
- ✅ Polling de comandos específicos del proyecto
- ✅ Logs separados por proyecto (`cc-daemon-v3-{project_id}.log`)

#### Frontend (monitor.html)
- ✅ Selector de proyecto en el header
- ✅ Carga dinámica de proyectos desde `/api/projects`
- ✅ Indicador de estado de conexión (🟢 conectado/🔴 desconectado)
- ✅ Contador de mensajes por proyecto
- ✅ Cambio de proyecto con carga automática de mensajes
- ✅ Filtrado de mensajes por proyecto activo
- ✅ Envío automático de comandos al proyecto seleccionado

### 📄 Documentación Agregada

- `MULTI_PROJECT_SETUP.md` - Guía completa de setup (instalación, configuración, troubleshooting)
- `PROJECTS_EXAMPLE.json` - Ejemplo de configuración de proyectos
- `CHANGELOG.md` - Este archivo
- Scripts de utilidad:
  - `install-daemon.sh` - Instalador interactivo de daemons
  - `test-setup.sh` - Script de verificación del setup

### 🔧 Cambios técnicos

#### Estructura de datos
```python
# Anterior (single project)
message_history = []
pending_commands = []

# Nuevo (multi-project)
projects_data = {
    'phd-research': {
        'config': {...},
        'message_history': [],
        'pending_commands': [],
        'connected_daemon': None
    },
    'hc-acop': {...}
}
```

#### API Changes

**Nuevos parámetros:**
- GET `/api/messages?project=PROJECT_ID`
- GET `/api/poll_command?project_id=PROJECT_ID`
- POST `/api/send_command` requiere `project_id` en JSON

**Nuevos campos en JSON:**
- Todos los mensajes incluyen `project_id`
- Todos los comandos incluyen `project_id`

### 🚀 Mejoras de rendimiento

- Isolamiento de datos por proyecto evita contaminar históricos
- Daemons pueden trabajar en paralelo sin interferir
- Interface web mantiene solo los datos del proyecto actual en memoria

### 🔐 Seguridad

- Validación de `project_id` en todos los endpoints
- 404 si el proyecto no existe
- Aislamiento total de autenticación por usuario (sigue siendo single-user)

### 📊 Compatibilidad

- ✅ Retrocompatible con cliente único (PROJECT_ID="default")
- ✅ Servidor soporta ambos modos
- ✅ No requiere cambios en clientes existentes

### 🐛 Bugfixes

- N/A (esto es primera versión multi-proyecto)

### ⚠️ Notas de ruptura

**Para usuarios existentes:**
1. Agrega `PROJECTS` variable en Railway (o deja que use default)
2. Reinstala daemons con `PROJECT_ID`
3. Interface web ahora requiere seleccionar proyecto

### 📝 Migration Guide

Si tenías un setup anterior (single project):

1. **No necesitas cambiar nada** - funcionará con PROJECT_ID="default"
2. **Si quieres múltiples proyectos:**
   - Define `PROJECTS` en Railway
   - Ejecuta `./install-daemon.sh` para cada proyecto

### 🙏 Gracias

Implementación completa en 4 pasos pequeños siguiendo arquitectura limpia.

---

## [1.0.0] - 2026-04-01 - Initial Release

### ✨ Características

- ✅ Interfaz web para monitorear Claude Code
- ✅ Autenticación con contraseña
- ✅ Histórico de mensajes
- ✅ Aprobación de acciones desde web
- ✅ Deploy en Railway con auto-redeploy desde GitHub
- ✅ Daemon persistente con sesión de Claude Code
- ✅ Conexión segura HTTPS

### 🔐 Seguridad

- ✅ Autenticación por contraseña
- ✅ HTTPS en Railway (auto-configurado)
- ✅ Validación de CORS
- ✅ Sin expo sición de credenciales AWS en cliente

---

**Versión actual:** 2.0.0
**Última actualización:** 2026-04-02
