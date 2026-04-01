# Claude Code Monitor - Railway Deployment

Monitor y controla Claude Code desde cualquier red usando una interfaz web pública.

## 🚀 Deploy en Railway (5 minutos)

### Opción A: Deploy con GitHub (Recomendado)

#### 1. Crear repositorio en GitHub

```bash
cd ~/claude-monitor-railway

# Inicializar git
git init
git add .
git commit -m "Initial commit - Claude Code Monitor"

# Crear repo en GitHub (puedes hacerlo desde github.com/new)
# Luego conectarlo:
git remote add origin https://github.com/TU-USUARIO/claude-monitor.git
git branch -M main
git push -u origin main
```

#### 2. Deploy en Railway

1. Ve a: https://railway.app/
2. Haz login con GitHub
3. Click en "New Project"
4. Click en "Deploy from GitHub repo"
5. Selecciona tu repositorio `claude-monitor`
6. Railway lo detectará automáticamente y empezará el deploy
7. Espera 2-3 minutos

#### 3. Obtener la URL

1. En Railway, click en tu proyecto
2. Ve a "Settings" → "Domains"
3. Click en "Generate Domain"
4. Copia la URL (ej: `https://claude-monitor-production.up.railway.app`)

---

### Opción B: Deploy directo (Sin GitHub)

#### 1. Instalar Railway CLI

```bash
npm install -g @railway/cli
# o
curl -fsSL https://railway.app/install.sh | sh
```

#### 2. Login y Deploy

```bash
cd ~/claude-monitor-railway

# Login
railway login

# Crear proyecto
railway init

# Deploy
railway up

# Ver URL
railway domain
```

---

## 📱 Usar el Monitor

### 1. Configurar la URL en tu laptop

Una vez que tengas la URL de Railway (ej: `https://tu-app.up.railway.app`):

```bash
# Agregar al .bashrc para que sea permanente
echo 'export CLAUDE_MONITOR_URL="https://tu-app.up.railway.app"' >> ~/.bashrc
source ~/.bashrc
```

### 2. Instalar el cliente ccmon

```bash
# Copiar ccmon.py a tu PATH
cp ~/claude-monitor-railway/ccmon.py ~/.local/bin/ccmon
chmod +x ~/.local/bin/ccmon
```

### 3. Usar Claude Code con monitoreo

```bash
# Desde tu laptop (red Bosch)
ccmon

# O con un prompt
ccmon "ayúdame con mi código"
```

### 4. Acceder desde tu celular

1. Abre el navegador en tu celular
2. Ve a: `https://tu-app.up.railway.app`
3. ¡Listo! Verás todo en tiempo real

---

## 🎯 Cómo funciona

```
┌──────────────┐          HTTPS           ┌──────────────┐
│   Laptop     │ ─────────────────────────▶│   Railway    │
│ (Red Bosch)  │  ccmon envía mensajes     │   (Cloud)    │
└──────────────┘                           └──────────────┘
                                                   │
                                                   │ HTTPS
                                                   │
                                                   ▼
                                            ┌──────────────┐
                                            │   Celular    │
                                            │ (Red móvil)  │
                                            └──────────────┘
```

## ⚙️ Configuración

### Variables de entorno en Railway (opcional)

En Railway → Settings → Variables:

- `SECRET_KEY`: Clave secreta para Flask (se genera automática)
- `PORT`: Puerto (Railway lo asigna automático)

### Variables en tu laptop

```bash
# Obligatorio: URL del servidor Railway
export CLAUDE_MONITOR_URL="https://tu-app.up.railway.app"
```

---

## 🛠️ Troubleshooting

### El servidor no inicia en Railway

1. Ve a Railway → Logs
2. Busca errores en el deploy
3. Verifica que `requirements.txt` esté completo

### ccmon dice "Cannot connect to server"

```bash
# Verifica que la URL esté configurada
echo $CLAUDE_MONITOR_URL

# Prueba la conexión
curl https://tu-app.up.railway.app/health
```

### No veo mensajes en la web

1. Verifica que ccmon esté corriendo
2. Abre la consola del navegador (F12)
3. Busca errores de WebSocket

---

## 💰 Costos

**Railway Plan Gratuito:**
- $5 USD de crédito mensual gratis
- Suficiente para uso personal
- ~500 horas de uptime
- Más que suficiente para este proyecto

Si se agota, puedes:
- Hacer sleep del servicio cuando no lo uses
- Upgradear a plan Hobby ($5/mes)
- Usar Render.com (también gratis)

---

## 📁 Estructura

```
claude-monitor-railway/
├── server.py           # Servidor Flask + SocketIO
├── ccmon.py           # Cliente para laptop
├── templates/
│   └── monitor.html   # Interfaz web
├── requirements.txt   # Dependencias Python
├── Procfile          # Comando de inicio
├── railway.json      # Configuración Railway
└── README.md         # Este archivo
```

---

## 🔐 Seguridad

- ✅ Todo sobre HTTPS
- ✅ CORS configurado
- ⚠️ **IMPORTANTE**: Este servidor es público. Cualquiera con la URL puede ver tus mensajes.

**Para producción seria:**
- Agrega autenticación (usuario/password)
- Usa tokens de acceso
- Limita CORS a dominios específicos

Para uso personal/testing, está bien así.

---

## 🎉 ¡Listo!

Ahora puedes:
- Dejar la laptop trabajando
- Ver desde tu celular lo que Claude hace
- Aprobar/rechazar acciones desde cualquier lugar
