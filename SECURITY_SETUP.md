# 🔒 Configuración de Seguridad - Claude Code Monitor

## ⚠️ IMPORTANTE: Configurar contraseña ANTES de usar

El sistema incluye autenticación con contraseña para proteger tu acceso.

---

## 📋 Configuración en Railway

### 1. Configurar Variable de Entorno

1. Ve a tu proyecto en Railway: https://railway.app
2. Selecciona tu servicio "claude-monitor"
3. Ve a la pestaña **"Variables"**
4. Agrega una nueva variable:
   - **Nombre:** `MONITOR_PASSWORD`
   - **Valor:** Tu contraseña segura (ejemplo: `miClaudeSeguro2026!`)
5. Click en **"Add"**
6. Railway reiniciará automáticamente el servicio

### 2. Contraseña Predeterminada (CAMBIAR INMEDIATAMENTE)

Si NO configuras `MONITOR_PASSWORD`, el sistema usa:
```
changeme123
```

**⚠️ ESTO ES INSEGURO** - Cámbiala INMEDIATAMENTE

---

## 🔐 Recomendaciones de Contraseña

✅ **Buenas contraseñas:**
- `MiProyecto2026!Seguro`
- `SecureAccess*2026`
- `Claude_Monitor_Xyz789!`

❌ **Malas contraseñas:**
- `123456`
- `password`
- `admin`

**Características:**
- Mínimo 12 caracteres
- Mezcla de mayúsculas, minúsculas, números y símbolos
- No uses información personal

---

## 🚀 Uso del Sistema

### Login
1. Abre: https://tu-app.up.railway.app
2. Ingresa la contraseña configurada
3. Click "Acceder"

### Logout
- Los botones de logout aún no están implementados
- Para cerrar sesión: Cierra el navegador o borra cookies

---

## 🛡️ Seguridad Adicional (Opcional)

### Whitelist de IPs en Railway

1. Ve a Settings → Networking
2. Configura "Allowed IPs"
3. Agrega solo tus IPs confiables

### HTTPS

Railway proporciona HTTPS automáticamente en todas las URLs `.up.railway.app`

---

## 🔄 Rotar Contraseña

Para cambiar la contraseña:

1. Railway → Variables → `MONITOR_PASSWORD`
2. Click en el valor actual
3. Ingresa nueva contraseña
4. Save (Railway reiniciará automáticamente)

---

## 📝 Notas Importantes

- **Sesiones:** Se mantienen por 24 horas o hasta cerrar navegador
- **Daemon local:** NO requiere autenticación (corre en tu WSL)
- **Solo web:** La autenticación protege solo la interfaz web

---

## ❓ Problemas Comunes

**"Contraseña incorrecta"**
- Verifica que configuraste `MONITOR_PASSWORD` en Railway
- Asegúrate de no tener espacios extras al inicio/fin
- La contraseña es case-sensitive (mayúsculas/minúsculas importan)

**"No puedo acceder después de configurar"**
- Espera 30 segundos después de cambiar la variable
- Railway tarda en reiniciar el servicio
- Refresca la página

---

**Fecha:** 2026-04-02
**Versión:** 1.0
